# Double Points hype video — Vol.7, sessions 7 & 8

Two cuts from one design:

| File | Output | Where |
|---|---|---|
| `double-points-reel.html` | 1080×1350 (4:5) | Instagram feed |
| `story-reel-9x16.html` | 1080×1920 (9:16) | Stories, Reels |

`double-points-reel.html` is the source. It is a 1080×1350 stage driven by
`window.__seek(t)` — no CSS animations, so every frame is deterministic and the
render is reproducible.

## Rebuilding

1. Pull the live state and build the contender list (top 10 by series points,
   with each player's stored profile photo as a data URI) into `data.json`.
2. Substitute it for the `DATA` placeholder: `const D = DATA;`.
3. Screenshot `__seek(i/30)` for `i` in `0 .. 30*__dur`, into JPEGs.
4. `ffmpeg -framerate 30 -i f%04d.jpg -c:v libx264 -preset slow -crf 19
   -pix_fmt yuv420p -movflags +faststart out.mp4`

Playwright's bundled ffmpeg is VP8-only — Instagram needs H.264, so use a full
ffmpeg build (`apt-get install ffmpeg`), not `/opt/pw-browsers/ffmpeg-*`.

## Notes

- Fonts are inlined from Google Fonts as local woff2 so the render never
  depends on the network mid-shoot. **Request axis RANGES, not single values** —
  `Archivo:ital,wdth,wght@0,62..125,100..900;1,62..125,100..900`. A single value
  (`@1,125,900`) makes Google serve a *static instance* on which
  `font-variation-settings:'wdth' 125` is silently ignored, so the display face
  renders at normal width and looks nothing like the app. `fontcheck.js` guards
  this: wdth 62 / 100 / 125 must measure 368 / 569 / 686 px, not three equal
  numbers. The cut is built on that axis — type enters at `wdth 62` and snaps to
  125 — so a static instance kills the motion as well as the shape.
- Players without a stored photo fall back to their initials in a cyan ring, so
  a missing photo still reads as finished rather than as a hole.
- Motion is beat-driven: a timestamped impact map drives camera punch, flash
  wash and trace brightness together, so the whole frame reacts as one rather
  than each element animating on its own.
- Palette and motion follow `DESIGN.md`: cyan leads, amber is urgency only
  (here: DOUBLE POINTS and the leader's row), easing overshoots and settles.

## Music

`score.py` writes `score.wav` — an original score, synthesised from scratch with
numpy. No samples and no library music, so the track is ours: nothing to licence
and nothing for Instagram's Content ID to claim.

It is written against the same `BEATS` array the picture uses, so the hits land
on the frames that already punch rather than merely near them. The contender
countdown reveals at 0.24s intervals, which is an eighth note at 125 BPM, so the
score sits at 125 and the edit and the music share one grid.

```bash
python3 score.py                       # ~3s, writes score.wav
ffmpeg -y -i surge-hype.mp4 -i score.wav -map 0:v -map 1:a \
  -c:v copy -c:a aac -b:a 192k -ar 48000 -ac 2 \
  -shortest -movflags +faststart surge-hype-music.mp4
```

The video stream is copied, not re-encoded, so muxing costs nothing in quality
and a new score can be dropped onto the same picture in seconds.

Two layers. **The hits** — kick, trailer impact (sub drop + noise crack + tail),
riser, sub-bass — sit on the beat map. **The bed** underneath is a real backing
track: sixteenth hats, claps on 2 and 4, a driving eighth-note bass, a sixteenth
arpeggio and offbeat chord stabs, over a Dm–Bb–F–C loop, one chord per bar.

`ENERGY(t)` is the arrangement in one function, and it follows the picture: the
titles land dry, the bed enters under the dates, climbs through the countdown,
**drops to 10% for the breath before the 60**, and returns full on the drop.

Mix gains matter more than they look. The bed is written at conservative
per-voice levels so nothing clips on its own, which leaves it ~20 dB under the
impacts and effectively inaudible — the `low += bed * 3.4` / `mid += drums * 9.0`
lines are what lift it into a backing track, about 7 dB under the hits. If the
bed ever goes missing after an edit, check those two numbers before anything
else. Every mapped beat also ducks it by up to 22%, so impacts still cut
through. Peak lands at -1 dBFS; Instagram normalises anyway.

## The 9:16 cut

`story-reel-9x16.html` is the same design re-flowed for a full vertical frame,
not a crop and not a letterbox. Three differences from the 4:5 source:

- **The background fills all 1920.** Trace, band, vignette and flashes sit at
  stage level, so the frame is full-bleed; only the composition is inset.
- **The type-led scenes scale 1.2× about their centre** via a `.zoom` layer that
  sits between `.scene` (which `seek()` transforms for the blow-past) and the
  content (which `seek()` addresses by id), so nothing the script writes is
  touched. 1.2 is the ceiling: DOUBLE POINTS is the widest line at ~840px, and
  1.2 puts it at 1008 inside a 1080 frame.
- **The chase gets its own box**, `#s3{top:250px;height:1420px}`, because it is
  the one height-bound scene. Rows grow to 108/87/8 and the avatars with them.

Instagram lays its own chrome over roughly the top 250px and bottom 250px of a
story — profile row above, reply bar and action rail below. Every cut keeps its
content inside 250..1670. That is also why the composition is **not** scaled to
fill the height: the contender rows already span the full 1080 width, so any
uniform upscale crops them.

The score is unchanged between the two cuts — same beat map, same 23.2s.

## The Duel cut (finale, 9:16)

`duel-reel-9x16.html` + `score-duel.py`. A different structure from the
countdown reels: the finale's story is not a leaderboard, it is two people two
points apart, so the cut is portrait-led.

Open → **the duel** (split screen, both faces, totals counting) → **tale of the
tape** (four two-sided bars: points, match wins, win rate, session titles) →
**the swing** (what each scored on the double night) → **the chasers** → date.

Two things the data gave us for free, and both are in the cut: they are level on
**27 match wins each**, and Hamed's 60 on session 7 is the *maximum a double
night can pay* — a perfect night, which is what took the lead off Munther.

Written natively for 1080x1920; there is no 4:5 variant, because the split
screen needs the height. Beat map and `ENERGY(t)` are re-timed to these scenes.

### Two traps this cut hit, worth knowing

- `punch()` writes `transform`, so any element centred with
  `transform: translateX(-50%)` loses its centring the moment it animates. The
  VS drifted right onto a portrait. Centre with a full-width container and
  animate an inner span instead.
- Long names wrap and break the two columns' alignment — one player's total sat
  a line lower than the other's. `.fname` is `white-space:nowrap` for that reason.
