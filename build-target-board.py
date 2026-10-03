# -*- coding: utf-8 -*-
"""DEAD EYE — Urban Playground target-challenge board, 1200 x 2000mm.

One hole, dead centre, inside a printed bullseye. The ball has to pass through
to score, so nothing is judged by eye and nobody argues.

House branding, not a volume's: the Urban Playground emblem, dark ground, one
accent. No volume lockup and no wordmark — the board is a fixture that outlives
any one season, and anything season-specific would date it the moment the volume
turns over.

The ACCENT is the exception, and it is deliberate. The first board was cyan,
which was September Surge's colour, and the moment Vol.7 was archived the fixture
was wearing a retired volume's livery. So the palette is a named livery now
(LIVERY=blackout, the default, or LIVERY=house for the original cyan): the rings
pick up whatever is on court, and nothing else about the board changes.

Three outputs, because a fabricator needs three different things:

  deadeye-board.pdf      the artwork, 1:1 at 1200 x 2000mm, vector
  deadeye-cutfile.pdf    the same sheet with ONLY the cut circle, magenta
                         hairline, plus corner registration marks
  deadeye-board.png      a raster preview for sharing

The hole is sized against the ball, not chosen because it looks right. A padel
ball is 63.5-67.7mm (FIP), so the aperture is specified as a clearance ratio
against the largest legal ball.

  python3 build-target-board.py
  node render-target-board.mjs
"""
import base64, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SP = "/tmp/claude-0/-home-user-May-madness/0e44f0ad-a683-5f0d-9de6-9459ae328963/scratchpad"
FONTS = os.path.join(SP, "video", "fonts")
FONT_BUNDLE = "/tmp/certs/fonts/bundle.css"      # the original location, if it survives
OUT = os.path.join(HERE, "brand", "target-board")

W, H = 1200.0, 2000.0            # mm
BALL_MAX = 67.7                  # mm, largest legal padel ball

# Liveries. Only the accent, the grounds and which emblem file is used change —
# the geometry, the type and the wording are identical, because the board is the
# same fixture whichever volume is running.
LIVERIES = {
    "house": dict(
        accent="#00E5FF", ink="#0A0F14", void="#050709", lift="#121B23",
        chalk="#F4F9FA", muted="#5C6B78",
        emblem=os.path.join("brand", "september-surge", "up-logo-cyan-2x.png"),
    ),
    "blackout": dict(
        accent="#C6FF00", ink="#050505", void="#000000", lift="#121212",
        chalk="#F2F2F2", muted="#6E6E6E",
        emblem=os.path.join("brand", "blackout", "up-logo-tight.png"),
    ),
}
LIVERY = os.environ.get("LIVERY", "blackout")
if LIVERY not in LIVERIES:
    sys.exit(f"unknown livery {LIVERY!r} — one of {', '.join(LIVERIES)}")
L = LIVERIES[LIVERY]

INK          = L["ink"]
VOID         = L["void"]
CYAN         = L["accent"]       # the accent, whatever this livery calls it
CHALK        = L["chalk"]
DEEP_STEEL   = L["muted"]
CUT          = "#FF00FF"         # the fabricator's cut colour, never printed

_ew, _eh = __import__("PIL.Image", fromlist=["Image"]).open(
    os.path.join(HERE, L["emblem"])).size
EMBLEM_RATIO = _eh / _ew

HOLE_D = 120.0                   # 1.77x ball — 52mm of clearance
CX, CY = 600.0, 1160.0           # 840mm off the floor with the board standing

# Bullseye bands, outermost first: (outer radius, cyan tint).
# Alternating tints are what make it read as a target rather than as a set of
# concentric circles — the eye needs filled area, not just outlines.
# Tints are pushed harder than they need to be on a screen: this is read from
# the far baseline, ten-odd metres away, where low-contrast bands merge into
# one grey disc and stop helping anyone aim.
BANDS = [(430, 0.09), (350, 0.00), (280, 0.17), (210, 0.00), (140, 0.30)]


def b64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()


def faces():
    """The font faces, inlined.

    The original build read a bundle from /tmp, which does not survive a new
    container — a print file that cannot be rebuilt is a print file you cannot
    correct. Falls back to the repo-side fonts the rest of the art uses.
    """
    if os.path.exists(FONT_BUNDLE):
        css = open(FONT_BUNDLE).read()
        if "url(data:" in css:
            return css
    css = open(os.path.join(FONTS, "fonts.css")).read()
    seen = {}

    def sub(m):
        n = m.group(1)
        if n not in seen:
            seen[n] = b64(os.path.join(FONTS, n))
        return "url(data:font/woff2;base64,%s) format('woff2')" % seen[n]

    css = re.sub(r"url\(([0-9a-f]+\.woff2)\)\s*format\('woff2'\)", sub, css)
    assert ".woff2)" not in css, "a font file was left as an external reference"
    return css


def bullseye():
    p = []
    # Filled bands, largest first so each paints over the one outside it.
    for r, tint in BANDS:
        fill = (f'fill="{CYAN}" fill-opacity="{tint:.2f}"' if tint
                else f'fill="{VOID}"')
        p.append(f'<circle cx="{CX}" cy="{CY}" r="{r}" {fill}/>')
    # A crisp line on every boundary, so the rings hold their edge at distance
    # even where two bands sit close in tone.
    for r, _ in BANDS:
        p.append(f'<circle cx="{CX}" cy="{CY}" r="{r}" fill="none" '
                 f'stroke="{CYAN}" stroke-opacity=".55" stroke-width="3"/>')
    # Crosshair ticks outside the rim, at the quarters
    outer = BANDS[0][0]
    for dx, dy in ((0, -1), (0, 1), (-1, 0), (1, 0)):
        x1, y1 = CX + dx * (outer + 16), CY + dy * (outer + 16)
        x2, y2 = CX + dx * (outer + 68), CY + dy * (outer + 68)
        p.append(f'<line x1="{x1:.0f}" y1="{y1:.0f}" x2="{x2:.0f}" y2="{y2:.0f}" '
                 f'stroke="{CYAN}" stroke-opacity=".7" stroke-width="5"/>')
    # The aperture: a void with a bright lip, which is what makes it legible
    # from the far baseline.
    r = HOLE_D / 2
    p.append(f'<circle cx="{CX}" cy="{CY}" r="{r}" fill="{VOID}" '
             f'stroke="{CYAN}" stroke-width="9"/>')
    p.append(f'<circle cx="{CX}" cy="{CY}" r="{r-11:.1f}" fill="none" '
             f'stroke="{CYAN}" stroke-opacity=".35" stroke-width="2"/>')
    return "".join(p)


def board_svg(emblem_b64, cut_only=False):
    p = []
    if cut_only:
        p.append(f'<rect width="{W}" height="{H}" fill="#FFFFFF"/>')
        p.append(f'<rect x="0" y="0" width="{W}" height="{H}" fill="none" '
                 f'stroke="{CUT}" stroke-width="1"/>')
        r = HOLE_D / 2
        p.append(f'<circle cx="{CX}" cy="{CY}" r="{r}" fill="none" '
                 f'stroke="{CUT}" stroke-width="1"/>')
        p.append(f'<line x1="{CX-r-40}" y1="{CY}" x2="{CX+r+40}" y2="{CY}" '
                 f'stroke="{CUT}" stroke-width="0.6"/>')
        p.append(f'<line x1="{CX}" y1="{CY-r-40}" x2="{CX}" y2="{CY+r+40}" '
                 f'stroke="{CUT}" stroke-width="0.6"/>')
        p.append(f'<text x="{CX}" y="{CY-r-58:.0f}" text-anchor="middle" '
                 f'font-family="JetBrains Mono, monospace" font-size="26" '
                 f'fill="{CUT}">ø{HOLE_D:.0f}mm</text>')
        p.append(f'<text x="{CX}" y="{CY+r+86:.0f}" text-anchor="middle" '
                 f'font-family="JetBrains Mono, monospace" font-size="20" '
                 f'fill="{CUT}">CENTRE {CX:.0f}, {CY:.0f} · '
                 f'{H-CY:.0f}mm OFF THE FLOOR</text>')
        for x, y in ((0, 0), (W, 0), (0, H), (W, H)):
            p.append(f'<path d="M {x-40} {y} H {x+40} M {x} {y-40} V {y+40}" '
                     f'stroke="{CUT}" stroke-width="1" fill="none"/>')
        p.append(f'<text x="{W/2}" y="{H-40}" text-anchor="middle" '
                 f'font-family="JetBrains Mono, monospace" font-size="26" fill="{CUT}">'
                 f'DEAD EYE · CUT FILE · {W:.0f} x {H:.0f}mm · '
                 f'1 HOLE · MAGENTA = CUT, DO NOT PRINT</text>')
        return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
                f'width="{W}mm" height="{H}mm">' + "".join(p) + '</svg>')

    # ── artwork ───────────────────────────────────────────────────────────
    p.append(f'<defs><radialGradient id="g" cx="50%" cy="57%" r="64%">'
             f'<stop offset="0%" stop-color="{L["lift"]}"/>'
             f'<stop offset="100%" stop-color="{INK}"/></radialGradient></defs>')
    p.append(f'<rect width="{W}" height="{H}" fill="url(#g)"/>')

    p.append(f'<rect x="26" y="26" width="{W-52}" height="{H-52}" fill="none" '
             f'stroke="{CHALK}" stroke-opacity=".14" stroke-width="3"/>')
    p.append(f'<rect x="26" y="26" width="{W-52}" height="14" fill="{CYAN}"/>')
    p.append(f'<rect x="26" y="{H-40}" width="{W-52}" height="8" fill="{CYAN}"/>')

    # ── header: the house mark, then the game ─────────────────────────────
    # The ratio is read off the file. It used to be hard-coded to the cyan
    # emblem's 768x1130, which silently stretches any other emblem — the house
    # one is 324x505, a different shape.
    ew = 130.0
    eh = ew * EMBLEM_RATIO
    p.append(f'<image href="data:image/png;base64,{emblem_b64}" '
             f'x="{(W-ew)/2:.0f}" y="86" width="{ew:.0f}" height="{eh:.0f}" '
             f'preserveAspectRatio="xMidYMid meet"/>')
    p.append(f'<text x="{W/2}" y="490" text-anchor="middle" font-family="Archivo" '
             f'font-style="italic" font-size="176" '
             f'font-variation-settings="\'wdth\' 125,\'wght\' 900" fill="{CHALK}" '
             f'stroke="{CHALK}" stroke-width="7" paint-order="stroke fill">DEAD EYE</text>')
    p.append(f'<text x="{W/2}" y="544" text-anchor="middle" '
             f'font-family="JetBrains Mono, monospace" font-weight="700" font-size="30" '
             f'letter-spacing="14" fill="{CYAN}">TARGET CHALLENGE</text>')
    p.append(f'<line x1="330" y1="592" x2="870" y2="592" stroke="{CYAN}" '
             f'stroke-opacity=".45" stroke-width="3"/>')

    # ── the bullseye ──────────────────────────────────────────────────────
    p.append(bullseye())

    # ── footer ────────────────────────────────────────────────────────────
    p.append(f'<rect x="0" y="1706" width="{W}" height="{H-1706}" fill="{VOID}" fill-opacity=".5"/>')
    p.append(f'<text x="{W/2}" y="1778" text-anchor="middle" '
             f'font-family="JetBrains Mono, monospace" font-weight="700" font-size="28" '
             f'letter-spacing="11" fill="{CYAN}">FIVE BALLS</text>')
    p.append(f'<text x="{W/2}" y="1852" text-anchor="middle" font-family="Archivo" '
             f'font-weight="800" font-size="48" fill="{CHALK}">'
             f'Through the hole, or it doesn’t count.</text>')
    p.append(f'<text x="{W/2}" y="1924" text-anchor="middle" '
             f'font-family="JetBrains Mono, monospace" font-size="24" letter-spacing="10" '
             f'fill="{DEEP_STEEL}">URBAN PLAYGROUND · MUSCAT</text>')

    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
            f'width="{W}mm" height="{H}mm">' + "".join(p) + '</svg>')


def build_html(emblem_b64, cut_only):
    bg = "#FFFFFF" if cut_only else INK
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
{faces()}
@page {{ size: {W}mm {H}mm; margin: 0; }}
*{{margin:0;padding:0;}}
html,body{{width:{W}mm;height:{H}mm;background:{bg};overflow:hidden;
  -webkit-print-color-adjust:exact;print-color-adjust:exact;}}
svg{{display:block;}}
</style></head><body>
{board_svg(emblem_b64, cut_only)}
</body></html>"""


def main():
    os.makedirs(OUT, exist_ok=True)
    emblem = b64(os.path.join(HERE, L["emblem"]))
    for cut_only, name in ((False, "deadeye-board"), (True, "deadeye-cutfile")):
        with open(os.path.join(OUT, name + ".html"), "w") as f:
            f.write(build_html(emblem, cut_only))
        print(f"built {name}.html")
    print(f"\nboard {W:.0f} x {H:.0f}mm, 1 hole   livery {LIVERY} ({L['accent']})")
    print(f"  ø{HOLE_D:.0f}mm at ({CX:.0f},{CY:.0f})  {H-CY:.0f}mm off the floor  "
          f"{HOLE_D/BALL_MAX:.2f}x ball  ({HOLE_D-BALL_MAX:.1f}mm clearance)")
    print(f"  bullseye outer ø{BANDS[0][0]*2:.0f}mm")
    print("\nnow render:  node render-target-board.mjs")


if __name__ == "__main__":
    main()
