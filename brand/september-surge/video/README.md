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

Voices are a kick, a trailer impact (sub drop + noise crack + tail), a noise
riser, a sub-bass, a detuned saw stab and a pad — all in D minor. Everything the
picture marks as a beat also ducks the bed by up to 30%, so the impacts read
through the pulse. Peak lands at -1 dBFS; Instagram normalises anyway.

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
