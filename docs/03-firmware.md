# 3. Firmware

Bare-metal AVR C (avr-libc, no Arduino core), built with PlatformIO. Source: [`firmware/src/main.cpp`](../firmware/src/main.cpp).

## Architecture
```
main loop
 ├─ mode handler   → updates bright[0..5]   (one animation step)
 ├─ pwmScan()      → one software-PWM frame (32 levels, one LED lit at a time)
 └─ checkButton()  → debounced mode change, EEPROM save
PCINT0 ISR         → sets btnFlag on button press (also wakes from sleep)
```

### Software PWM over charlieplexing
Each frame steps a threshold from 0 to 127 in 32 steps. At each step, every LED whose brightness is above the threshold gets lit briefly (15 µs) and then turned off. Only one LED conducts at a time, so peak battery current stays at a single LED's current.

### Charlieplex drive
Pin states are precomputed bitmasks, so lighting an LED takes two register writes. The first version used per-bit shifts in the inner loop. At 1 MHz that made the frame about 2-3x slower than planned and every animation crawled (see [lessons learned](06-lessons-learned.md)).

## Modes
| # | Name | Behavior |
|---|---|---|
| 0 | All on | All LEDs at ~78% |
| 1 | Organic fade | Each LED follows a half-sine "breath" at its own rate and phase, so 2-3 are lit at once and the pattern drifts and never repeats exactly |
| 2 | Wreath shimmer | Every LED stays lit and glides toward a new random target brightness, so the whole wreath shimmers independently |
| 3 | Off | `SLEEP_MODE_PWR_DOWN`; the button pin-change interrupt wakes it into mode 0 |

The last *lit* mode is saved to EEPROM, so a fresh battery never starts in "off."

## Power measures
- Clock prescaler forced to ÷8 (1 MHz)
- ADC, USI, Timer0 and Timer1 powered down
- All charlieplex pins left Hi-Z between PWM slots
- Power-down sleep in off mode

## Tuning knobs
| Constant | Effect |
|---|---|
| `fadeRate[]` | Breath speed per LED (bigger = faster) |
| `SH_MIN` / `SH_MAX` | Shimmer depth (lower `SH_MIN` = more visible shimmer) |
| `shStep` | Shimmer speed |
| `bright[i] = 100` in all-on | Overall brightness and current |
