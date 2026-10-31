# 1. Design decisions

## Goals
- A fun, ~10-minute solder build for students, with the satisfying payoff of LEDs lighting up when they finish
- One PCB that supports several themes, including non-holiday ones
- A long, quiet twinkle on a single coin cell (no sound)
- As few student-soldered SMD parts as possible

## Analog vs. microcontroller
I started out wanting a fully analog circuit: a fast 555 as a PWM carrier, with slow per-LED RC networks biasing a transistor on each LED to make independent fades. I rejected it because:

| | Analog (555 + RC per LED) | ATtiny85 |
|---|---|---|
| Parts per LED | ~5 (NPN, 2R, C, LED) | 1 LED (plus 1 shared R per pin) |
| Idle current | 555 always running, ~100-300 µA | Power-down sleep ~0.1 µA |
| Effects | Fixed by component values | Any pattern, changeable in firmware |
| Off mode | Needs a switch | Sleep on a button press |

The ATtiny85 wins on part count, battery life, and flexibility. Students never see the MCU; they solder LEDs and a button.

## Charlieplexing on 3 pins
3 pins give 3 × 2 = **6 independently addressable LEDs**. Each address has **two footprints** on the PCB, one in each design region, which is how one board supports multiple plates. Students populate only the 6 for their design, and an empty footprint is just an open circuit, so the firmware doesn't need to know which design is fitted.

Considered and rejected: 4 pins (12 LEDs, which would need a 4th pin and blur together on an 80 mm ornament) and a CD4017 counter (incompatible with fast PWM fading).

That leaves PB3 for the mode button, and PB4 and PB5 (RESET) free.

## Current limiting
Every charlieplex path is HIGH pin → R → LED → R → LOW pin, so the resistance is split evenly with one resistor per pin.

Design calculation (red LED, Vf ≈ 1.8 V, 3.0 V cell, 5 mA target):

```
R_total = (3.0 - 1.8) / 5 mA = 240 Ω  →  ~120 Ω per pin
```

As the cell sags toward ~2.2 V, the current falls but red LEDs keep glowing. Blue and white LEDs (Vf ≈ 3 V) would go dark, which is why this design uses red LEDs.

> **TODO:** record the resistor values actually fitted.

## Power budget
- MCU active at 1 MHz: roughly 0.3-0.5 mA (estimate)
- LEDs: only one is ever on at a time, at ~5 mA peak. The average depends on mode and brightness, and is roughly 2-4 mA in all-on mode (estimate)
- Off mode: ~0.1 µA, so shelf life is effectively the battery's own shelf life

**Honest result:** the original goal of 30 days of continuous twinkle isn't realistic with LED current in the milliamps. With a CR2032 (~225 mAh), continuous all-on runtime is estimated at a few days. The off mode makes this a non-issue for an ornament that gets switched on in the evenings.

> **TODO:** measure average current in each mode with a meter in series with the cell, and replace the estimates above.
