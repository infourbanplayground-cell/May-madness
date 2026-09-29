# DEAD EYE — Urban Playground target challenge

A 1200 × 2000mm board with five cut-through holes. The ball has to pass through
to score, so nothing is judged by eye and nothing gets argued about.

## Files

| File | What it is |
|---|---|
| `deadeye-board.pdf` | the artwork, 1:1 at 1200 × 2000mm, vector — give this to the printer |
| `deadeye-cutfile.pdf` | the same sheet, cut circles only, magenta hairline — give this to whoever cuts |
| `deadeye-board.png` | preview, for sharing |
| `deadeye-cutfile.png` | preview of the cut geometry |

Rebuild: `python3 build-target-board.py && node render-target-board.mjs`

## The holes

Sizes are set by the ball, not by what looks tidy. A padel ball is 63.5–67.7mm
(FIP), so each hole is specified as a clearance ratio against the **largest**
legal ball.

| Target | Ø | Clearance | Centre (x, y from top-left) | Height off floor | Points |
|---|---|---|---|---|---|
| Bullseye | 100mm | 1.48× ball | 600, 680 | 1320mm | **100** |
| Mid left | 160mm | 2.36× ball | 330, 1000 | 1000mm | **50** |
| Mid right | 160mm | 2.36× ball | 870, 1000 | 1000mm | **50** |
| Outer left | 240mm | 3.55× ball | 310, 1340 | 660mm | **25** |
| Outer right | 240mm | 3.55× ball | 890, 1340 | 660mm | **25** |

The bullseye is deliberately tight — 3.2cm of total clearance means it only goes
through if the strike is clean. That is the shot people will queue to try.

Heights assume the board stands on its base on the court floor, and sit in the
band a padel player actually hits through.

## Rules

- **Five balls each.** Fed or served, same for everyone — pick one and hold to it.
- **Through the hole, or it doesn't count.** A ball that hits the rim and comes
  back scores nothing. This is the whole reason the holes are cut rather than
  printed.
- **Max 500** (five bullseyes). Realistic good score is 100–150.
- **Ties** are broken by a single ball at the bullseye, repeated until it breaks.

Suggested formats:

- **Side game** — 1 OMR for five balls, best score of the night takes the pot.
- **Session opener** — every player gets five balls before the group stage; the
  score is a tiebreaker in the standings.
- **Head to head** — two boards, two players, five balls each, straight shootout.

## Fabrication

- **Substrate:** 12mm plywood or 10mm Forex/PVC foam board. Ply survives repeated
  hits better; foam is lighter to move between courts but will dent.
- **Print:** direct to substrate, or vinyl wrap applied then holes cut through
  both layers so the vinyl does not lift at the rim.
- **Cut the holes after printing**, not before — and **radius the rims** or tape
  them. A square-cut edge in ply will fray and will also mark the balls.
- **Leave space behind the board.** The ball has to go somewhere: hang it off the
  back glass with a gap, or stand it in front of a catch net. Flat against the
  glass and nothing passes through, which defeats the design.
- **Weight the base.** A 1.2 × 2m board takes a real hit; it needs feet or
  sandbags or it will go over on the first clean strike.

## Design notes

Brand is Vol.7: Deep Current ground, Surge Cyan, Archivo italic display, the
surge trace as texture, and the ripple radiating from each hole so a target
reads as a target from the far baseline.

**Rings sit a fixed distance outside each hole (22mm and 44mm), not a multiple
of its radius.** Proportional rings gave the 240mm holes a 271mm halo that ran
straight through the row above them.

**Scores sit out in the side margin**, not under the holes — under is where the
next row of targets begins, and the first layout had the 50s and 25s landing on
top of the rings below and on the footer. The bullseye keeps its score above it,
where there is clear air.

**No soft glows anywhere.** Chromium's vector PDF writer tiles large blurred
shadows and the seams print as hard-edged rectangles — and at 2m across a court,
a glow is wasted anyway. Everything is flat shapes and crisp strokes, which is
also what keeps the PDF at 1.2MB.
