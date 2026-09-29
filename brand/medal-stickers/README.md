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

**All three are cyan.** The numeral already says which placement a sticker is,
and `DESIGN.md` has cyan leading the volume, so one colour throughout reads as a
series rather than as three separate awards.

Two metal colourways are kept one flag away, for if these ever have to sit
beside conventional ribbons:

```bash
python3 build-surge-medal-stickers.py --way cyan     # default: all cyan
python3 build-surge-medal-stickers.py --way ladder   # cyan / silver / bronze
python3 build-surge-medal-stickers.py --way metal    # gold / silver / bronze
```

Bronze `#C3813F` appears only in those two. It is a deliberate exception to
`DESIGN.md`, which reserves warm accents for urgency — it is cooler and darker
than Strike Amber, so the two cannot be confused elsewhere in the system.

The lockup stays its own colour on all three. A brand mark does not restyle
itself per placement; the ring, the numeral and the arc carry that.

The centre is Vol.7's ripple, faint, behind the numeral — the same pulse motif
the certificates use.

### Centring the numeral

The placement numeral is the mark, so it sits dead centre — and centre here is
measured, not eyeballed. `verify-medal-centring.mjs` reports the offset for
every sticker; it should read 0.00 units on all six.

`text-anchor="middle"` centres the numeral *and* its ordinal suffix together,
which leaves the numeral itself well left of centre. Correcting that with a
hand-tuned nudge per digit was still 2–6% out, because the right factor depends
on the glyph, the size and the font's real advance widths — and tuning it by eye
made one placement worse while fixing another. So the numeral and suffix are
separate elements, and the page measures the numeral's box once the font has
loaded, then puts the numeral on the centre and hangs the suffix off its right
edge.

**The renderer must wait for that pass.** It screenshots only once the page sets
`svg[data-centred="1"]`, and fails the sticker if it never appears. Screenshot
any earlier and every sticker ships with the mark off-centre — the exact bug the
pass exists to prevent.

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
