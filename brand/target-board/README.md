# DEAD EYE — Urban Playground target challenge

A 1200 x 2000mm board with one cut-through hole at the centre of a printed
bullseye. The ball has to pass through to score, so nothing is judged by eye and
nothing gets argued about.

**House branding, not a volume's.** The Urban Playground emblem, dark ground,
one accent. No volume lockup and no wordmark — the board is a fixture that
outlives any one season, and anything season-specific would date it the moment
the volume turns over.

**The accent is the one exception, and it is a named livery.** The first board
was cyan, which was September Surge's colour; the moment Vol.7 was archived the
fixture was wearing a retired volume's livery. So the palette is selectable and
nothing else changes with it:

```bash
python3 build-target-board.py                 # blackout — lime, the default
LIVERY=house python3 build-target-board.py    # the original cyan
node render-target-board.mjs
```

Each livery carries the club's own emblem in its own finish — white with the
orange ball for blackout, the cyan mark for house. The aspect ratio is read off
the file rather than assumed: the two are different shapes (324x505 and
768x1130), and the hard-coded ratio silently stretched whichever one it was not
written for.

The **cut file is livery-independent** — it is geometry, and one hole is one
hole whatever colour the rings are.

## Files

| File | What it is |
|---|---|
| `deadeye-board.pdf` | the artwork, 1:1 at 1200 x 2000mm, vector — give this to the printer |
| `deadeye-cutfile.pdf` | the same sheet, one magenta circle — give this to whoever cuts |
| `deadeye-board.png` | preview, for sharing |
| `deadeye-cutfile.png` | preview of the cut geometry |

Rebuild: `python3 build-target-board.py && node render-target-board.mjs`
(prefix `LIVERY=house` for cyan). The fonts are inlined from the repo-side
bundle; the original build read them from `/tmp`, which does not survive a new
container, and a print file you cannot rebuild is a print file you cannot
correct.

## The hole

Sized against the ball, not chosen because it looks right. A padel ball is
63.5-67.7mm (FIP), so the aperture is specified as a clearance ratio against the
**largest** legal ball.

| | |
|---|---|
| Diameter | **120mm** |
| Clearance | 1.77x ball — 52mm of total spare |
| Centre | 600, 1160 from the top-left |
| Height off the floor | **840mm**, with the board standing on its base |
| Bullseye outer ring | 800mm across |

120mm is a real challenge and still reachable: a clean strike goes through, a
loose one hits the rings. If you want more people to score, 140mm takes it to
2.07x ball — one number in the builder (`HOLE_D`) and both files re-cut.

## Rules

- **Two balls each.** Fed or served — pick one and hold everyone to it.
- **Through the hole, or it doesn't count.** A ball that hits a ring or the rim
  and comes back scores nothing. That is the whole reason the hole is cut rather
  than printed.
- **Score is out of two.** 2/2 is a perfect round.
- **Ties** go to sudden death, one ball each, until it breaks.

**Two balls is a different game from five, and worth deciding on purpose.** One
clean strike is now half your score rather than a fifth of it, so a single lucky
hit wins rounds that five balls would have sorted out. Most rounds will be 0/2 or
1/2 and ties stop being the exception — sudden death becomes the normal way a
round ends, not a rare one, so have someone ready to run it. It is faster, which
is the point if this is a queue between matches; `BALLS` in the builder sets both
the board and the count printed on it.

The printed rings are an aiming aid and the bullseye effect, not a score. If you
would rather they counted — 25 for the inner band, 10 for the next, 5 for the
outer — that works, but it puts close calls back in the hands of whoever is
watching, which is exactly what the cut hole was chosen to avoid.

Suggested formats:

- **Side game** — 1 OMR for two balls, best round of the night takes the pot.
- **Session opener** — everyone shoots before the group stage; the round is a
  tiebreaker in the standings.
- **Head to head** — two players, five balls each, straight shootout.

## Fabrication

- **Substrate:** 12mm plywood or 10mm Forex/PVC foam board. Ply survives repeated
  hits better; foam is lighter to move between courts but will dent.
- **Print:** direct to substrate, or vinyl wrap applied then the hole cut through
  both layers so the vinyl does not lift at the rim.
- **Cut the hole after printing**, and **radius the rim** or tape it. A
  square-cut edge in ply frays and will also mark the balls.
- **Leave space behind the board.** The ball has to go somewhere: hang it off the
  back glass with a gap, or stand it in front of a catch net. Flat against the
  glass and nothing passes through, which defeats the design.
- **Weight the base.** A 1.2 x 2m board takes a real hit and will go over on the
  first clean strike without feet or sandbags.

## Design notes

**The bands are filled, not outlined.** A bullseye reads as a bullseye because
of alternating area; concentric strokes on their own just look like ripples. Each
boundary also carries a crisp line so the rings hold their edge at distance where
two bands sit close in tone.

**The tints are pushed harder than they need to be on screen** (9%, 17%, 30%).
This is read from the far baseline, ten-odd metres away, where low-contrast bands
merge into one grey disc and stop helping anyone aim.

**The aperture is the only magenta object on the board.** Everything else is the
accent. It used to wear the accent too, which made the thing that actually scores
one more lime ring among lime rings; a single object in the second colour is
unmissable at ten metres. Four spurs point in at it, because the eye follows
converging lines and that is the cheapest way to say "here" without a glow.

**The ball count is drawn, not spelled.** Two squares above the rings say how
many attempts you get before anyone has read a word, which matters for the one
number on this board most likely to change.

**Corner brackets, not a hairline frame.** The board is a 1.2 x 2m rectangle in a
space made of rectangles — glass, fence posts, the court itself — and a thin
outline dissolves into all of them at distance.

**The title carries a hard offset in magenta, never a blur** — see the glow note
below. The rule in the footer is set in display type for the same reason it is on
the board at all: at 48px under a 176px title it read as a footnote to its own
board.

**No soft glows anywhere.** Chromium's vector PDF writer tiles large blurred
shadows and the seams print as hard-edged rectangles — and at 2m across a court a
glow is wasted anyway. Everything is flat shapes and crisp strokes, which is also
what keeps the PDF at 0.3MB.
