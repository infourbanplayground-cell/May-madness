# Blackout Series · Vol.8 — Certificates of Achievement, 1st to 5th

A4 landscape (297 x 210mm), 300 DPI, full bleed. Five placements.

| File | What it is |
|---|---|
| `bo-certificates-1-to-5.pdf` | all five as one job — **give this to the print shop** |
| `bo-certificate-N.pdf` | one placement per file |
| `bo-certificate-N.png` | 3510 x 2481 preview / for sending as an image |
| `bo-certificate-N.html` | the artboard, self-contained (fonts and marks inlined) |

## Rebuilding

```bash
# blank name lines — print these BEFORE the last night and write names in
python3 build-blackout-certificates.py
node render-blackout-certificates.mjs
python3.13 pack-blackout-certificate-pdfs.py
```

With the names and figures read off the live app:

```bash
ssh urbanpadel 'curl -s localhost:3009/state' > $SP/bo.json
node ops/blackout-standings.mjs $SP/bo.json $SP/bo-standings.json
python3 build-blackout-certificates.py --standings $SP/bo-standings.json
node render-blackout-certificates.mjs && python3.13 pack-blackout-certificate-pdfs.py
```

`img2pdf` and Pillow are installed on **python3.13** in this container, not on
the default `python3` (3.11).

## The names are read, never typed

Every name and every figure on these sheets comes from
`ops/blackout-standings.mjs`, which lifts the app's own scoring engine out of
`blackout-index.html` and runs it over the live state. A certificate cannot
award a placement or print a total that the leaderboard contradicts.

**It refuses to print a name while a night is still to play.** The top five is
not a fact until the season is over — on 30 October 1st to 4th were covered by
38 points with a double-points night left. `--provisional` overrides it, and
then the sheet *says so*: the kicker reads `PROVISIONAL · THE SEASON IS NOT
FINISHED` and the top rule turns magenta, so a provisional sheet cannot be
mistaken for a final one at arm's length. The imprint line carries it too.

Run with no `--standings` at all and you get blank name lines and no figures —
which claims nothing, and is the right thing to print in advance.

## Design notes

This is Vol.7's certificate re-cut for Vol.8 rather than a new design, the same
way the app inherits its markup volume to volume.

- **Palette** — Deep Current to true black `#050505`, Surge Cyan to lime
  `#C6FF00`. Lime leads. **Magenta is the rare one** and appears on the
  champion's sheet only, because it is the colour of the thing that scores.
  Violet (`uv`) is a *structure* colour: it is the label caps, a ring in the
  seal and a wash under the foot, and it is **never set as type** — 3.1:1 on
  `#050505` fails at body size.
- **Geometry** — radius 0 everywhere, the one exception being the seal, which is
  a deliberate circle. Vol.7's soft accent rules become hard bars, and the
  frame's single rising bar becomes the app's own four corner ticks.
- **Texture** — Vol.7's horizontal surge trace gives way to Vol.8's tactical
  grid and scanline field, which is what the app draws.
- **Figures** — Vol.7's sheet carried none, which made it a template somebody
  had filled in rather than a record. This one carries POINTS / NIGHTS / NIGHTS
  WON, straight off the engine's own table.

**No soft glows, anywhere.** Vol.7's placement numeral hung a 4mm and an 18mm
shadow off itself. `build-blackout-brand.py` already records why that is wrong
here: Chromium tiles big blurred shadows and the seams print as hard-edged
rectangles. The placement is carried by size and colour alone.

**Placement is carried by the numeral and the label, not by fading** — the
lesson Vol.7 recorded after stepping 4th and 5th down to a dimmer accent and
watching it print washed out, which is the wrong thing for something somebody
keeps. All five sheets lead lime. There is **no gold / silver / bronze**: it is
not in this palette.

## The writable plate

The sheet is near-black, so a black pen on it is invisible. The name field
therefore sits on its own light plate (`#EFEFEA`, not pure white, so it does not
glare against the black field), with a lime cap bar along its top edge so it
reads as a labelled field belonging to the frame rather than as a white box
dropped on the sheet. 15mm is enough to write a name in without taking the eye
off the placement.

**Both modes use the same plate.** A typed name prints in `#0A0A0A` on the plate
rather than on the dark ground, so a pre-printed certificate and a handwritten
one are structurally identical.

The date is printed, not ruled — the season's finals date comes from
`blackout-season.json`, and `--date` overrides it.

## What the renderer checks

- **The face was really drawn.** Archivo is measured against the same stack
  falling back; `getComputedStyle` reports the family in the stylesheet whether
  or not it loaded, and `document.fonts.check()` answers *true* with zero faces
  loaded. Mono cannot be width-probed here — JetBrains Mono is installed
  system-wide in this container, so the stack resolves to the system copy with
  the bundle stripped and the probe passes with nothing embedded, which is
  exactly how an HTML artboard reaches a print shop that does not have the face.
  It is checked for being in `document.fonts` and loaded instead.
- **Every run of type sits inside the printed frame, and no two overlap.** The
  page is `overflow:hidden` at a fixed mm size, so `scrollHeight` can never
  exceed `clientHeight` — Vol.7's overflow assertion was vacuous and would have
  passed a sheet whose body copy had run under the seal.
- **Nothing is clipped inside its own container**, which is the long-name case.
- 300 DPI, and the PDF packer re-checks the A4 aspect before it writes a page.

Proved by sabotage, which is the only way to know an assertion can fail:

```bash
SABOTAGE=nofont node render-blackout-certificates.mjs 1   # face + a collision
SABOTAGE=long   node render-blackout-certificates.mjs 1   # a clipped name
```

Sabotaged pages write to `*-sabotage.png` so they can never overwrite artwork.
