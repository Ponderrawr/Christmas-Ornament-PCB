# 6. Lessons learned (bring-up log)

| Symptom | Root cause | Fix |
|---|---|---|
| Uploading to "every COM port" failed, and one USB port stopped working | The programmer isn't a serial device. ATtiny ISP programmers talk over raw USB | Identified the programmer type in Zadig (it was a **FabISP**, USBtiny protocol). A reboot restored the port |
| `could not find USB device vid=0x16c0 pid=0x5dc` | `platformio.ini` was set to `usbasp` | `upload_protocol = usbtiny` + libusb-win32 driver |
| `'m_hi' was not declared` | Arrays defined below their first use after a partial edit | Keep lookup tables above the functions that use them. Replace whole files rather than pasting fragments |
| Every animation ran at a snail's pace | Per-bit shifts in the charlieplex inner loop at 1 MHz made each frame ~15 ms instead of the planned 5-8 ms | Precomputed bitmasks, shorter hold time, retuned animation rates |
| Button did nothing, but touching the pin changed modes | Firmware expected an active-high press, while the switch actually pulls PB3 **to GND**. With no pullup the pin floated, so a fingertip acted as an antenna | Enabled the internal pullup and switched to active-low detection with a noise re-check |
| First twinkle mode looked frantic | Spark-and-decay design was too fast and too sparse | Redesigned as a shimmer: all LEDs lit, each drifting to random levels |
| Acrylic quote far over budget | UV printing has a per-design setup fee | Switched to 3D-printed translucent plates |
| Ice-blue plate planned with red LEDs | Colored filament absorbs off-color light | Natural/white filament for red LEDs |

## What I'd change in rev B
- Draw the button to VCC with a pulldown, or label it clearly as active-low, so schematic and firmware match
- Add a 6-pin ISP header or pogo pads for programming in-circuit
- Silkscreen polarity marks next to every LED footprint
- Add a test point for measuring battery current
