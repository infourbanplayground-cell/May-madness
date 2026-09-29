# September Surge · Vol.7 — Medal stickers, 1st to 3rd

Circular inserts in two sizes, because medal inserts come in two: **50mm (2in)**
and **25mm (1in)**. They are not one artwork scaled — 25mm is a separate cut,
because arc text that reads at 50mm turns to mush at half the diameter.

| | 50mm | 25mm |
|---|---|---|
| Outer ring | yes | yes |
| `URBAN PLAYGROUND` top arc | yes | — |
| `SEPTEMBER SURGE · VOL.7` bottom arc | yes | `SEPTEMBER SURGE` only |
| Emblem | yes | — |
| Numeral | 0.80 × radius | 1.00 × radius |

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

Colours follow the series ladder — **cyan, light steel, steel** — not
gold/silver/bronze. `DESIGN.md` is explicit that gold is out of this palette and
the app's medal chips already use this ladder, so the sticker matches what a
player sees next to their name in the table. **`--metal` switches to
gold/silver/bronze** if these have to sit beside conventional medal ribbons.

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
