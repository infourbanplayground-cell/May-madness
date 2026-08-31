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

## certificates-deck/

The certificates as designed in the Claude Design handoff bundle
(`Certificates Deck.dc.html`) — 1920×1080 editorial artboards, distinct from
the A4 set in `certificates/`.

Built by `build-certificates-deck.py` + `render-certificates-deck.mjs`. The
handoff sections are used verbatim (they are pure inline-styled HTML); fonts
and images are inlined as base64 so the print shop cannot substitute a face
or drop an asset.

The PDF page is **297 × 167.06mm** — full A4 landscape width at the design's
own 16:9 ratio, so it prints centred on A4 with an even top/bottom margin and
nothing is cropped or stretched.

The handoff stops at 4th place; 5th is generated from the 4th by
`make_fifth()`, which asserts every substitution so a missed swap fails the
build instead of shipping a certificate that still says "Fourth".

The name holder is a solid white plate (~182 x 19mm) to write the winner's
name on — the handoff's glowing underline looks right on screen but leaves
nothing writable on a near-black printed sheet. `--name-style rule` restores
the original. The plate keeps the placement accent as a bar along its bottom
edge; 3rd place is the exception, where the chalk accent would vanish against
the white plate and an ink bar would vanish against the dark sheet, so it uses
steel, the one value that reads against both.

PDFs are assembled from the 300 DPI raster by `pack-certificate-pdfs.py`, not
printed from the browser: Chromium's vector PDF export tiles large blurred
shadows and the seams print as hard-edged rectangular blocks around the
placement numeral's glow.

### Copy that disagrees with the live app

Defaults match the handoff exactly. Flags override:

| Handoff says | App says | Flag |
|---|---|---|
| "Eight sessions" | `sessionsTotal = 9` | `--sessions nine` |
| 3rd = 35 OMR | `season = [75, 45, 30]` | `--third-prize 30` |
| 28 August 2026 | Session 9 not yet scheduled | `--date "..."` |
