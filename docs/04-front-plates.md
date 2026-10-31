# 4. Front plates

The PCB has no artwork of its own. A screw-on front plate gives each design its look.

## Options evaluated
| Option | Verdict |
|---|---|
| Laser-cut + UV-printed acrylic (e.g. Pololu) | Best look, but about $50 setup per unique print layout plus per-part cost, too expensive for 30 plates |
| Second PCB as a plate (silkscreen art) | Cheap, but no light diffusion and limited color |
| Cardstock / transparency film | Near zero cost, but looks low-end |
| **3D-printed translucent plate** | **Chosen:** cheap, diffuses light, fast to iterate |

## Light-transmission design
Translucent filament dims roughly exponentially with thickness, so the plate is designed like a lithophane:

| Region | Thickness | Purpose |
|---|---|---|
| Background field | 1.6 mm | Even, soft glow |
| Over each LED (back-side pocket, 6 mm × 0.8 mm deep) | 0.8 mm shell | Bright halo around the berries; also clears the LED dome |
| 3 × Ø1.5 mm through-holes per LED | open | Direct light reads as bright "berries" |
| Needles, holly, bow, pinecone | 2.5-4.5 mm | Darker silhouette when lit, relief in daylight |

Use `plates/Thickness_Test_Coupon.stl` (0.4-3.2 mm steps) to check real transmission in your filament before printing a batch.

### Filament and LED color
Colored translucent plastic passes its own color and absorbs the rest. **Red LEDs behind ice-blue or green filament come out dim and murky.** With red LEDs, use natural/clear translucent PLA for a warm glow, or plain white PLA if you're going the lithophane route. An option for daylight color: dry-brush the raised wreath with green acrylic paint and leave the thin field unpainted.

## Generator
`plates/generator/wreath_plate.py` builds the plate as a heightmap from simple primitives (needle capsules, holly leaves, bow loops), then writes a watertight binary STL. Two details:
- Outer edges and all holes are snapped onto exact circles, so they print round instead of stair-stepped
- Feature edges are smoothstep-blended into the base to avoid aliasing

Change the `LEDS` and `MOUNTS` lists to regenerate the plate for a different board.

**Known limitation:** fine organic detail (individual needles, holly spikes) is close to the limit of a heightmap and of a 0.4 mm nozzle. For a sellable sculpted look, the fallback is a sculpted model with the holes added as negative parts in the slicer.

## Print settings
- Face up, no supports (the back pockets print as short bridges)
- 0.12 mm layers, 2 walls, **100% infill**: sparse infill shows up as a grid pattern when backlit
