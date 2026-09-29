# September Surge · Vol.7 — Medal stickers, 1st to 3rd

Circular inserts in two sizes, because medal inserts come in two: **50mm (2in)**
and **25mm (1in)**. They are not one artwork scaled — 25mm is a separate cut,
because arc text that reads at 50mm turns to mush at half the diameter.

| | 50mm | 25mm |
|---|---|---|
| Outer ring | yes | yes |
| September Surge lockup | yes | yes |
| `URBAN PLAYGROUND · VOL.7` arc | yes | — |
| Numeral | 0.72 × radius | 0.86 × radius |

The **lockup is the mark**, not the bare emblem. Because it already reads
SEPTEMBER SURGE, the top arc that used to repeat it is gone — the lockup fills
that space, and the one remaining arc carries what the lockup does not: the club
and the volume. At 25mm there is no arc at all: mono text on a 25mm disc is
under a millimetre tall and prints as grey fuzz.

## Files

| Pattern | What it is |
|---|---|
| `ss-medals-{size}mm-1-to-3.pdf` | all three as one job — **give this to the printer** |
| `ss-medal-{size}mm-{place}.pdf` | one placement, exact physical size |
| `*-bleed.png` | square artboard, trim + 3mm bleed, dark to the edge |
| `*-disc.png` | trimmed to the circle, transparent outside — for digital use |

The disc is a shade lighter than the bleed ground, so if the die wanders half a
millimetre the cut edge still has something to sit against.

## Rebuilding

```bash
python3 build-surge-medal-stickers.py      # or --sizes 38 --places 1 2 3
node render-surge-medal-stickers.mjs       # -> 300 DPI PNG
python3 pack-surge-medal-pdfs.py           # -> print-ready PDF
```

## Design notes

**Cyan, light steel, bronze.** First keeps the series' own colour, which is what
a player sees next to their name in the table; second reads as silver; third is
bronze `#C3813F`.

Bronze is a deliberate exception to `DESIGN.md`, which reserves warm accents for
urgency. These go onto physical medals, where third place is bronze by
convention and steel would read as a mistake. It is a metal, not the series'
Strike Amber — cooler and darker, so it cannot be confused with a live-now
marker anywhere else in the system. `--metal` switches first and second to gold
and silver too, if they have to match rather than lead with cyan.

The lockup stays its own colour on all three. A brand mark does not restyle
itself per placement; the ring, the numeral and the arc carry that.

The centre is Vol.7's ripple, faint, behind the numeral — the same pulse motif
the certificates use.

### Two things that bit, worth knowing

- **The bottom arc must start at the LEFT point with sweep-flag 0**
  (`M cx-r,cy A r,r 0 0 0 cx+r,cy`), which is the construction the certificate
  seal uses. Starting from the right point sends the text back over the top and
  it lands on the upper arc, upside down and colliding with it.
- **Optical centring.** `text-anchor="middle"` centres numeral *and* suffix
  together, which leaves the numeral — the thing the eye reads as the middle —
  sitting left of the disc's centre. The mark is nudged right by a fraction of
  the suffix width, and `1` needs three times the correction `2` and `3` do
  because it is so much narrower.
