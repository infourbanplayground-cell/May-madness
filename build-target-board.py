# -*- coding: utf-8 -*-
"""DEAD EYE — Urban Playground target-challenge board, 1200 x 2000mm.

A rigid board with cut-through holes: the ball has to pass through to score, so
nothing is judged by eye and nobody argues at the prize table.

Three outputs, because a fabricator needs three different things:

  deadeye-board.pdf      the artwork, 1:1 at 1200 x 2000mm, vector
  deadeye-cutfile.pdf    the same sheet with ONLY the cut circles, in magenta
                         hairline, plus corner registration marks
  deadeye-board.png      a raster preview for sharing and for the socials

Geometry is driven by the ball, not by the layout. A padel ball is 63.5-67.7mm
(FIP), so every hole is specified as a clearance ratio against the largest legal
ball rather than as a round number that happens to look right:

  bullseye  100mm   1.48x ball   deliberately tight — this is the shot
  mid       160mm   2.36x ball   a good strike goes through
  outer     240mm   3.55x ball   generous, so beginners still score

Heights are measured from the floor with the board standing on its base, and sit
in the band a padel player actually hits through: 580mm, 920mm, 1240mm.

  python3 build-target-board.py
  node render-target-board.mjs
"""
import base64, os

HERE = os.path.dirname(os.path.abspath(__file__))
FONT_BUNDLE = "/tmp/certs/fonts/bundle.css"
BRAND = os.path.join(HERE, "brand", "september-surge")
OUT = os.path.join(HERE, "brand", "target-board")

W, H = 1200.0, 2000.0            # mm
BALL_MAX = 67.7                  # mm, largest legal padel ball

DEEP_CURRENT = "#0A0F14"
VOID         = "#050709"
SURGE_CYAN   = "#00E5FF"
VOLTAGE      = "#F4F9FA"
STEEL_TX     = "#8A9BA8"
DEEP_STEEL   = "#5C6B78"
AMBER        = "#FF9E1B"
CUT          = "#FF00FF"         # the fabricator's cut colour, never printed

# x, y (mm from top-left), diameter, points, label
# x, y (mm from top-left), diameter, points, label, where the score sits
HOLES = [
    (600, 680, 100, 100, "BULLSEYE", "above"),
    (330, 1000, 160, 50, "", "left"),
    (870, 1000, 160, 50, "", "right"),
    (310, 1340, 240, 25, "", "left"),
    (890, 1340, 240, 25, "", "right"),
]

# Rings sit a FIXED distance outside each hole rather than a multiple of its
# radius. Proportional rings made the 240mm holes throw a 271mm halo that ran
# straight through the row above it.
RING_1, RING_2 = 22.0, 44.0


def b64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()


def rings(cx, cy, d, accent=SURGE_CYAN):
    """Vol.7's ripple, radiating from each hole so the target reads as a target."""
    out = []
    r = d / 2
    for i, off in enumerate((RING_1, RING_2)):
        out.append(f'<circle cx="{cx}" cy="{cy}" r="{r+off:.1f}" fill="none" '
                   f'stroke="{accent}" stroke-opacity="{0.44 - i*0.16:.2f}" '
                   f'stroke-width="{3.0 - i*0.9:.1f}"/>')
    return "".join(out)


def hole(cx, cy, d, pts, label, where):
    r = d / 2
    parts = [rings(cx, cy, d)]
    # The hole itself reads as a void: the board is dark, so the aperture is
    # darker still with a bright lip, which is what makes it legible from the
    # far baseline.
    parts.append(f'<circle cx="{cx}" cy="{cy}" r="{r:.1f}" fill="{VOID}" '
                 f'stroke="{SURGE_CYAN}" stroke-width="7"/>')
    parts.append(f'<circle cx="{cx}" cy="{cy}" r="{r-9:.1f}" fill="none" '
                 f'stroke="{SURGE_CYAN}" stroke-opacity=".30" stroke-width="2"/>')
    # The score never goes inside the hole — no board there to print on — and
    # never directly below it either, because that is where the next row of
    # targets begins. It goes out into the side margin the board already has,
    # except for the bullseye, which has clear air above it.
    edge = r + RING_2
    if where == "above":
        tx, ty, anchor = cx, cy - edge - 22, "middle"
    elif where == "left":
        tx, ty, anchor = cx - edge - 24, cy + 24, "end"
    else:
        tx, ty, anchor = cx + edge + 24, cy + 24, "start"
    parts.append(
        f'<text x="{tx:.1f}" y="{ty:.1f}" text-anchor="{anchor}" '
        f'font-family="Archivo" font-style="italic" font-size="72" '
        f'font-variation-settings="\'wdth\' 125,\'wght\' 900" fill="{SURGE_CYAN}" '
        f'stroke="{SURGE_CYAN}" stroke-width="4" paint-order="stroke fill">{pts}</text>')
    if label:
        parts.append(
            f'<text x="{cx}" y="{cy - edge - 74:.1f}" text-anchor="middle" '
            f'font-family="JetBrains Mono, monospace" font-weight="700" font-size="26" '
            f'letter-spacing="8" fill="{AMBER}">{label}</text>')
    return "".join(parts)


def board_svg(lockup_b64, cut_only=False):
    p = []
    if cut_only:
        # Cut file: geometry only, on white, so a CNC or a router jig reads it
        # without anything else to strip out first.
        p.append(f'<rect width="{W}" height="{H}" fill="#FFFFFF"/>')
        p.append(f'<rect x="0" y="0" width="{W}" height="{H}" fill="none" '
                 f'stroke="{CUT}" stroke-width="1"/>')
        for cx, cy, d, _, _, _ in HOLES:
            p.append(f'<circle cx="{cx}" cy="{cy}" r="{d/2:.1f}" fill="none" '
                     f'stroke="{CUT}" stroke-width="1"/>')
            p.append(f'<line x1="{cx-d/2-18}" y1="{cy}" x2="{cx-d/2-6}" y2="{cy}" '
                     f'stroke="{CUT}" stroke-width="1"/>')
            p.append(f'<line x1="{cx}" y1="{cy-d/2-18}" x2="{cx}" y2="{cy-d/2-6}" '
                     f'stroke="{CUT}" stroke-width="1"/>')
            p.append(f'<text x="{cx}" y="{cy+8}" text-anchor="middle" '
                     f'font-family="JetBrains Mono, monospace" font-size="22" '
                     f'fill="{CUT}">ø{d:.0f}</text>')
            p.append(f'<text x="{cx}" y="{cy+40}" text-anchor="middle" '
                     f'font-family="JetBrains Mono, monospace" font-size="16" '
                     f'fill="{CUT}">{cx:.0f},{cy:.0f}</text>')
        for x, y in ((0, 0), (W, 0), (0, H), (W, H)):
            p.append(f'<path d="M {x-40} {y} H {x+40} M {x} {y-40} V {y+40}" '
                     f'stroke="{CUT}" stroke-width="1" fill="none"/>')
        p.append(f'<text x="{W/2}" y="{H-40}" text-anchor="middle" '
                 f'font-family="JetBrains Mono, monospace" font-size="26" fill="{CUT}">'
                 f'DEAD EYE · CUT FILE · {W:.0f} x {H:.0f}mm · '
                 f'5 HOLES · MAGENTA = CUT, DO NOT PRINT</text>')
        return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}mm" height="{H}mm">' + "".join(p) + '</svg>'

    # ── artwork ───────────────────────────────────────────────────────────
    p.append(f'<rect width="{W}" height="{H}" fill="{DEEP_CURRENT}"/>')
    # Vol.7's surge trace. Flat bands, no blur: a 2m board is viewed from ten
    # metres, and soft shadows tile badly in Chromium's vector PDF anyway.
    for y in range(0, int(H), 14):
        p.append(f'<rect x="0" y="{y}" width="{W}" height="2.2" '
                 f'fill="{SURGE_CYAN}" fill-opacity="0.045"/>')
    p.append(f'<rect x="0" y="1640" width="{W}" height="{H-1640}" fill="{VOID}" fill-opacity=".55"/>')

    # frame
    p.append(f'<rect x="26" y="26" width="{W-52}" height="{H-52}" fill="none" '
             f'stroke="{VOLTAGE}" stroke-opacity=".14" stroke-width="3"/>')
    p.append(f'<rect x="26" y="26" width="{W-52}" height="14" fill="{SURGE_CYAN}"/>')
    p.append(f'<rect x="26" y="{H-40}" width="{W-52}" height="8" fill="{SURGE_CYAN}"/>')

    # ── header ────────────────────────────────────────────────────────────
    p.append(f'<text x="{W/2}" y="196" text-anchor="middle" font-family="Archivo" '
             f'font-style="italic" font-size="188" '
             f'font-variation-settings="\'wdth\' 125,\'wght\' 900" fill="{VOLTAGE}" '
             f'stroke="{VOLTAGE}" stroke-width="7" paint-order="stroke fill">DEAD EYE</text>')
    p.append(f'<text x="{W/2}" y="252" text-anchor="middle" '
             f'font-family="JetBrains Mono, monospace" font-weight="700" font-size="30" '
             f'letter-spacing="13" fill="{SURGE_CYAN}">TARGET CHALLENGE</text>')
    p.append(f'<line x1="300" y1="300" x2="900" y2="300" stroke="{SURGE_CYAN}" '
             f'stroke-opacity=".5" stroke-width="3"/>')

    # ── the targets ───────────────────────────────────────────────────────
    for cx, cy, d, pts, label, where in HOLES:
        p.append(hole(cx, cy, d, pts, label, where))

    # ── footer: how it is scored, then the mark ───────────────────────────
    fy = 1660
    p.append(f'<text x="{W/2}" y="{fy}" text-anchor="middle" '
             f'font-family="JetBrains Mono, monospace" font-weight="700" font-size="26" '
             f'letter-spacing="11" fill="{SURGE_CYAN}">FIVE BALLS · BEST SCORE WINS</text>')
    p.append(f'<text x="{W/2}" y="{fy+64}" text-anchor="middle" font-family="Archivo" '
             f'font-weight="800" font-size="40" fill="{STEEL_TX}">'
             f'Through the hole, or it doesn’t count.</text>')
    # The lockup already says URBAN PLAYGROUND, so the strapline that used to
    # sit beneath it is gone -- at 520mm wide the two overlapped anyway.
    lw = 360
    lh = lw * 750 / 1600
    p.append(f'<image href="data:image/png;base64,{lockup_b64}" x="{(W-lw)/2:.0f}" '
             f'y="{H-lh-56:.0f}" width="{lw}" height="{lh:.0f}" '
             f'preserveAspectRatio="xMidYMid meet"/>')

    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
            f'width="{W}mm" height="{H}mm">' + "".join(p) + '</svg>')


def build_html(lockup_b64, cut_only):
    faces = open(FONT_BUNDLE).read()
    bg = "#FFFFFF" if cut_only else DEEP_CURRENT
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
{faces}
@page {{ size: {W}mm {H}mm; margin: 0; }}
*{{margin:0;padding:0;}}
html,body{{width:{W}mm;height:{H}mm;background:{bg};overflow:hidden;
  -webkit-print-color-adjust:exact;print-color-adjust:exact;}}
svg{{display:block;}}
</style></head><body>
{board_svg(lockup_b64, cut_only)}
</body></html>"""


def main():
    os.makedirs(OUT, exist_ok=True)
    lockup = b64(os.path.join(BRAND, "surge-lockup@1600.png"))
    for cut_only, name in ((False, "deadeye-board"), (True, "deadeye-cutfile")):
        path = os.path.join(OUT, name + ".html")
        with open(path, "w") as f:
            f.write(build_html(lockup, cut_only))
        print(f"built {name}.html")
    print(f"\nboard {W:.0f} x {H:.0f}mm, {len(HOLES)} holes")
    for cx, cy, d, pts, _, _ in HOLES:
        print(f"  ø{d:3.0f}mm at ({cx:4.0f},{cy:4.0f})  "
              f"{H-cy:4.0f}mm off the floor  {d/BALL_MAX:.2f}x ball  {pts} pts")
    print("\nnow render:  node render-target-board.mjs")


if __name__ == "__main__":
    main()
