/*
 * Christmas Ornament PCB - ATtiny85 firmware
 *
 * Hardware
 *   ATtiny85 @ 1 MHz internal RC, coin cell
 *   6 charlieplexed LEDs on PB0/PB1/PB2 (one series resistor per pin)
 *   Mode button on PB3: PB3 -> switch -> R0 -> GND (active LOW, internal pullup)
 *
 * Modes (button cycles, last lit mode saved to EEPROM)
 *   0  All on
 *   1  Organic fade   - each LED breathes at its own rate, 2-3 lit at once
 *   2  Wreath shimmer - all LEDs lit, each drifts to random brightness
 *   3  Off            - power-down sleep (~0.1 uA), button press wakes
 */
#include <avr/io.h>
#include <avr/interrupt.h>
#include <avr/power.h>
#include <avr/sleep.h>
#include <avr/eeprom.h>
#include <avr/pgmspace.h>
#include <util/delay.h>

#define CP0 PB0
#define CP1 PB1
#define CP2 PB2
#define BTN PB3
#define CP_MASK ((1 << CP0) | (1 << CP1) | (1 << CP2))

#define NUM_LEDS  6
#define NUM_MODES 4
#define MODE_OFF  3

// Charlieplex address table: pin driven HIGH / pin driven LOW (third pin Hi-Z)
static const uint8_t m_hi[NUM_LEDS] = {1<<CP0, 1<<CP1, 1<<CP1, 1<<CP2, 1<<CP0, 1<<CP2};
static const uint8_t m_lo[NUM_LEDS] = {1<<CP1, 1<<CP0, 1<<CP2, 1<<CP1, 1<<CP2, 1<<CP0};

volatile uint8_t mode = 0;
volatile uint8_t btnFlag = 0;
uint8_t bright[NUM_LEDS];           // 0..127 software-PWM level per LED

// ---------- Charlieplex drive ----------
static inline void ledsOff(void) {
  DDRB  &= ~CP_MASK;
  PORTB &= ~CP_MASK;
}

static inline void lightOne(uint8_t led) {
  DDRB  = (DDRB  & ~CP_MASK) | m_hi[led] | m_lo[led];
  PORTB = (PORTB & ~CP_MASK) | m_hi[led];
}

// One software-PWM frame: 32 levels, only one LED ever on at a time
static void pwmScan(void) {
  for (uint8_t tick = 0; tick < 128; tick += 4) {
    for (uint8_t i = 0; i < NUM_LEDS; i++) {
      if (bright[i] > tick) {
        lightOne(i);
        _delay_us(15);
        ledsOff();
      }
    }
  }
}

// ---------- Button ----------
ISR(PCINT0_vect) {
  if (!(PINB & (1 << BTN))) btnFlag = 1;   // pressed = LOW
}

static void initButton(void) {
  DDRB  &= ~(1 << BTN);
  PORTB |=  (1 << BTN);                    // internal pullup
  _delay_ms(5);
  GIFR  |= (1 << PCIF);
  GIMSK |= (1 << PCIE);
  PCMSK |= (1 << PCINT3);
}

static void checkButton(void) {
  if (!btnFlag) return;
  _delay_ms(50);
  if (PINB & (1 << BTN)) { btnFlag = 0; return; }   // noise
  while (!(PINB & (1 << BTN)));                      // wait for release
  _delay_ms(50);
  mode = (mode + 1) % NUM_MODES;
  if (mode != MODE_OFF) eeprom_update_byte((uint8_t*)0, mode);  // fresh battery always starts lit
  for (uint8_t i = 0; i < NUM_LEDS; i++) bright[i] = 0;
  btnFlag = 0;
}

static void loadMode(void) {
  uint8_t saved = eeprom_read_byte((uint8_t*)0);
  mode = (saved < MODE_OFF) ? saved : 0;
}

// ---------- PRNG (xorshift16) ----------
static uint16_t rngState = 0xACE1;
static uint8_t rng8(void) {
  rngState ^= rngState << 7;
  rngState ^= rngState >> 9;
  rngState ^= rngState << 8;
  return (uint8_t)rngState;
}

// ---------- Sine lookup (lit half only) ----------
static const uint8_t PROGMEM sine64[64] = {
    0,  6, 12, 19, 25, 31, 37, 44, 50, 56, 62, 68, 74, 80, 86, 92,
   98,103,109,115,120,126,131,136,142,147,152,157,162,167,171,176,
  181,185,189,193,197,201,205,209,212,216,219,222,225,228,231,234,
  236,238,241,243,244,246,248,249,251,252,253,254,254,255,255,255
};

static uint8_t sineWave(uint8_t a) {
  uint8_t idx = a & 0x3F;
  switch (a >> 6) {
    case 0:  return pgm_read_byte(&sine64[idx]);
    case 1:  return pgm_read_byte(&sine64[63 - idx]);
    default: return 0;                       // dark half
  }
}

// ---------- MODE 0: All on ----------
static void modeAllOn(void) {
  for (uint8_t i = 0; i < NUM_LEDS; i++) bright[i] = 100;
  pwmScan();
}

// ---------- MODE 1: Organic fade ----------
static uint16_t fadeAcc[NUM_LEDS];
static const uint8_t fadeRate[NUM_LEDS]  = {180, 240, 200, 255, 220, 160};  // bigger = faster
static const uint8_t fadeStart[NUM_LEDS] = {0, 42, 85, 128, 170, 213};

static void initFade(void) {
  for (uint8_t i = 0; i < NUM_LEDS; i++) fadeAcc[i] = (uint16_t)fadeStart[i] << 8;
}

static void modeFade(void) {
  for (uint8_t i = 0; i < NUM_LEDS; i++) {
    fadeAcc[i] += fadeRate[i];
    bright[i] = sineWave(fadeAcc[i] >> 8) >> 1;
  }
  pwmScan();
}

// ---------- MODE 2: Wreath shimmer ----------
#define SH_MIN 40    // dimmest a berry dips (lower = stronger shimmer)
#define SH_MAX 120   // brightest a berry gets (max 127)
static uint8_t shTarget[NUM_LEDS];
static uint8_t shStep[NUM_LEDS];

static void modeWreath(void) {
  for (uint8_t i = 0; i < NUM_LEDS; i++) {
    if (bright[i] == shTarget[i]) {
      shTarget[i] = SH_MIN + rng8() % (SH_MAX - SH_MIN + 1);
      shStep[i]   = 1 + (rng8() & 1);
    }
    uint8_t b = bright[i], t = shTarget[i], s = shStep[i];
    if (b < t) bright[i] = (t - b > s) ? b + s : t;
    else       bright[i] = (b - t > s) ? b - s : t;
  }
  pwmScan();
}

// ---------- MODE 3: Off ----------
static void modeOff(void) {
  ledsOff();
  set_sleep_mode(SLEEP_MODE_PWR_DOWN);
  sleep_enable();
  sei();
  sleep_cpu();                 // wakes on button pin-change
  sleep_disable();
}

// ---------- Power ----------
static void initPower(void) {
  clock_prescale_set(clock_div_8);   // force 1 MHz
  ADCSRA &= ~(1 << ADEN);
  power_adc_disable();
  power_usi_disable();
  power_timer0_disable();
  power_timer1_disable();
}

int main(void) {
  cli();
  initPower();
  initButton();
  loadMode();
  initFade();
  sei();

  for (;;) {
    switch (mode) {
      case 0: modeAllOn();  break;
      case 1: modeFade();   break;
      case 2: modeWreath(); break;
      case 3: modeOff();    break;
    }
    checkButton();
  }
}
