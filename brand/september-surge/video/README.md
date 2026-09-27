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
  depends on the network mid-shoot.
- Players without a stored photo fall back to their initials in a cyan ring, so
  a missing photo still reads as finished rather than as a hole.
- Palette and motion follow `DESIGN.md`: cyan leads, amber is urgency only
  (here: DOUBLE POINTS and the leader's row), easing overshoots and settles.
