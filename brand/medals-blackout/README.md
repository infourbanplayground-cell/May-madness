# Blackout Series · Vol.8 — Medal cut-outs, 1st to 3rd

Circular inserts in two sizes, because medal inserts come in two: **50mm (2in)**
and **25mm (1in)**. They are not one artwork scaled — arc text that reads at
50mm turns to mush at half the diameter, so 25mm is a separate cut with the arc
dropped.

| | 50mm | 25mm |
|---|---|---|
| Lime ring + hairline | yes | yes |
| Blackout mark | yes | yes |
| `BLACKOUT · VOL.8` arc | yes | — |
| Squares at 3 and 9 o'clock | yes | — |
| Numeral | 0.74 × radius | 0.80 × radius |

## Files

| Pattern | What it is |
|---|---|
| `bo-medals-{size}mm-1-to-3.pdf` | all three as one job — **give this to the printer** |
| `bo-medal-{size}mm-{place}-bleed.pdf` | one placement, exact physical size |
| `*-disc.png` | **the cut-out** — trimmed to the circle, transparent outside it |
| `*-bleed.png` | square artboard, trim + 3mm bleed, black to the edge |
| `PROOF.png` | all six composited on black, white, cream and a mid-tone |

The `-disc.png` files are the ones to drop onto a photo of the winner or onto a
medal blank. The `-bleed.png` files are the printer's: the bleed ground is the
same black as the disc, so a die that wanders half a millimetre cuts into more
of the same colour rather than into a visible seam.

## Rebuilding

```bash
python3 build-blackout-medals.py          # or --sizes 50 --places 1 2 3
node render-blackout-medals.mjs           # -> 300 DPI PNG
node ops/check-blackout-medals.mjs        # -> centring report + PROOF.png
python3.13 pack-blackout-medal-pdfs.py    # -> print-ready PDF
```

`img2pdf` is installed on **python3.13** in this container, not on the default
`python3` (3.11).

## Design notes

**All three are lime.** The numeral already says which placement a cut-out is,
and lime leads this volume, so one colour throughout reads as a series rather
than as three separate awards. **There is no gold / silver / bronze** — it is
not in this palette and the app's own medal chips do not use it. Two other
colourways are one flag away:

```bash
python3 build-blackout-medals.py --way lime     # default
python3 build-blackout-medals.py --way ladder   # lime / pale / deep
python3 build-blackout-medals.py --way metal    # gold / silver / bronze
```

`--way metal` exists only for if these ever have to sit beside conventional
ribbons.

**The mark, not the lockup.** The horizontal Blackout lockup carries a sub-line
of small type that is under a millimetre tall at 50mm and prints as grey fuzz,
so the square mark rides above the numeral instead and the one arc carries what
the mark does not: the series and the volume.

**Squares, not diamonds.** Vol.7 set the 3- and 9-o'clock markers as rotated
diamonds. This volume has radius 0 and no rotated geometry anywhere, so they sit
square.

**No soft glows.** `build-blackout-brand.py` records why: Chromium tiles big
blurred shadows and the seams print as hard-edged rectangles. The disc is the
one deliberate circle, and everything on it is a hard edge — including the
tactical grid inside it, which is clipped to the hairline ring so it can never
print across the cut line.

### Making the numerals bolder

Archivo's weight axis stops at 900 and its width axis at 125, so the numerals
are already as bold as the face goes. `BOLD_STROKE` (0.055em) strokes each one
in its own colour with `paint-order="stroke fill"`, which fattens the glyph
evenly on every edge while leaving the counters open. Much past 0.08 and the
`1`'s spur and the `3`'s bowls start to close up.

### Centring the numeral

The placement numeral is the mark, so it sits dead centre — and centre here is
**measured, not eyeballed**. `text-anchor="middle"` centres the numeral *and*
its ordinal suffix together, which leaves the numeral itself well left of
centre; correcting that with a hand-tuned nudge per digit was still 2–6% out in
Vol.7, because the right factor depends on the glyph, the size and the font's
real advance widths. So the two are separate elements and the page measures the
numeral's box once the font has loaded, then puts the numeral on the centre and
hangs the suffix off its right edge.

**The renderer must wait for that pass.** It screenshots only once the page sets
`svg[data-centred="1"]`, and fails the cut-out if it never appears. Screenshot
any earlier and every one ships with the mark off-centre — the exact bug the
pass exists to prevent. `ops/check-blackout-medals.mjs` reports the offset for
all six; it should read 0.00 units.

### The bottom arc

The arc path must start at the **left** point with sweep-flag 0
(`M cx-r,cy A r,r 0 0 0 cx+r,cy`), which is the construction the certificate
seal uses. Starting from the right point sends the text back over the top and
sets it mirrored.

## What the renderer checks

- **The alpha is real.** Corners clear, not wholly transparent, under 90%
  opaque, and the ink covering ~78.5% of the square — which is what a disc
  inscribed in one covers. An opaque square looks perfect on a dark slide and
  ruins a white one, with nothing on screen to tell you which you have.
- **The bleed artboard is solid to its edge**, which is the opposite test.
- **Archivo was really drawn**, measured against the same stack falling back.
  Mono is checked for being embedded rather than width-probed, because JetBrains
  Mono is installed system-wide in this container — see the certificates README.
  It is only required on the 50mm cut; at 25mm the arc is deliberately dropped,
  so the face never loads there.
- 300 DPI at both sizes.

Proved by sabotage:

```bash
SABOTAGE=opaque ONLY=50mm-1-disc node render-blackout-medals.mjs
SABOTAGE=nofont ONLY=50mm-1      node render-blackout-medals.mjs
```

Sabotaged pages write to `*-sabotage.png` so they can never overwrite artwork.
