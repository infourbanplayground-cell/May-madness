# Brand assets — August Attack (Vol.6)

Source marks live only on the server (`/var/www/attack.urbanpadel.om/public/assets/`).
These are derived from `aa-wordmark.png` and `aa-emblem.png` pulled from there.

## august-attack/

| File | Use |
|---|---|
| `aa-wordmark-full-colour.png` / `@4x` | The series mark. Transparent. Designed for dark backgrounds — the letterforms are white/grey with a red neon swoosh, so it disappears on white |
| `aa-emblem-full-colour.png` / `@4x` | The Urban Playground app mark. Same caveat |
| `aa-wordmark-mono.svg` / `aa-emblem-mono.svg` | **Vector, single colour — give these to engravers/embroiderers.** Auto-traced from the raster at a luminance threshold, so the neon glow is resolved to solid ink |
| `*-mono@4x.png` | Same mono artwork as raster, if a supplier can't take SVG |

The source PNGs carry a thin full-width frame rule that is part of the file
rather than the mark; the mono versions strip it (any row/column that is
~entirely ink is treated as a rule, not artwork).

Neither original is large: the wordmark is 728×278 and the emblem 432×583.
The `@4x` files are LANCZOS upscales, not new detail. For anything printed
larger than roughly A4, use the SVGs.

Per DESIGN.md: never recolour either mark — the glow is baked into the PNG and
a CSS/print filter will fight it. The mono versions are the exception, and
exist precisely because engraving cannot reproduce a glow.

## certificates/

Placement certificates 1st–5th. A4 landscape, built by `build-certificates.py`
and rendered by `render-certificates.mjs`.

- `.pdf` — print-ready, vector type, for the print shop
- `.png` — 300 DPI flat preview
- `.html` — source; fonts and images are embedded as base64 so it renders
  identically with no network

The name line is intentionally blank: the series was still running when these
were made, so they are templates to fill in.

Colour follows DESIGN.md, which is explicit that **gold is not in this
palette** — placements use the series ladder (Attack Red → light steel →
steel), the same one the medal chips use in the app, not gold/silver/bronze.

To rebuild:

```bash
python3 build-certificates.py          # fonts expected in /tmp/certs/fonts
node render-certificates.mjs
```
