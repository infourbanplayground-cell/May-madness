# Double Points hype video — Vol.7, sessions 7 & 8

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
