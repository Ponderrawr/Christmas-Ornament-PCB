# 5. Build and program

## Assembly (student)
1. Pick a design and find its 6 LED footprints (labelled on the silkscreen)
2. Solder the LEDs, **long leg (anode) to the square pad**. Check the polarity marking for each position, because charlieplexed LEDs face different directions
3. Solder the tactile switch
4. Insert the coin cell (+ side up, TODO confirm for the holder used)
5. Fit the standoffs and screw on the front plate

## Flashing the ATtiny85
**Tools:** VS Code + PlatformIO extension, and a FabISP (USBtiny firmware) programmer.

1. **Driver (Windows):** run [Zadig](https://zadig.akeo.ie/), enable *Options → List All Devices*, select **FabISP**, and install **libusb-win32**
2. Open the `firmware/` folder in VS Code. PlatformIO detects `platformio.ini`
3. Wire ISP: MOSI→PB0, MISO→PB1, SCK→PB2, RST→PB5, VCC, GND
4. Click **Upload** (→). USBtiny doesn't use a COM port
5. If you get "initialization failed," uncomment `upload_flags = -B32` in `platformio.ini`

Take the coin cell out if the programmer supplies 5 V to the target. LEDs on PB0-PB2 flickering during programming is normal.
