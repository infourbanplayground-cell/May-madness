# -*- coding: utf-8 -*-
"""September Surge (Vol.7) medal stickers — circular inserts, 1st to 3rd.

Two sizes, because medal inserts come in two: 50mm (2in) and 25mm (1in). They
are not the same artwork scaled — 25mm is a separate cut of the design, because
arc text that reads at 50mm turns to mush at half the diameter.

  50mm  outer ring, both arcs, the emblem, ripple, and the numeral
  25mm  the numeral and one arc, nothing else

Each is produced three ways:

  *-bleed.png   square, trim + 3mm bleed, dark to the edge — give this to the
                printer for die-cut stickers
  *.png         trimmed to the circle with transparency outside, for digital use
                and for anyone placing it onto artwork themselves
  *.pdf         the bleed artboard at exact physical size

Placement colours follow the series ladder — cyan, light steel, steel — not
gold/silver/bronze. DESIGN.md is explicit that gold is out of this palette and
the app's medal chips already use this ladder. `--metal` overrides it if these
have to sit next to conventional gold/silver/bronze medal ribbons.

  python3 build-surge-medal-stickers.py
  python3 build-surge-medal-stickers.py --metal
"""
import argparse, base64, os

HERE = os.path.dirname(os.path.abspath(__file__))
FONT_BUNDLE = "/tmp/certs/fonts/bundle.css"
BRAND = os.path.join(HERE, "brand", "september-surge")
OUT = os.path.join(HERE, "brand", "medal-stickers")

DEEP_CURRENT = "#0A0F14"
VOID         = "#050709"
SURGE_CYAN   = "#00E5FF"
VOLTAGE      = "#F4F9FA"
LIGHT_STEEL  = "#C3D0D8"
STEEL_TX     = "#8A9BA8"

SERIES = {
    1: dict(ord_="1", suf="ST", accent=SURGE_CYAN),
    2: dict(ord_="2", suf="ND", accent=LIGHT_STEEL),
    3: dict(ord_="3", suf="RD", accent=STEEL_TX),
}
# Only if these have to sit beside conventional medal ribbons.
METAL = {1: "#E3B341", 2: "#C9CDD2", 3: "#C08457"}

BLEED_MM = 3.0


def b64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()


def svg(place, size_mm, accent, emblem_b64, bleed=True):
    """One sticker. Units are 0.1mm, so a 50mm disc is 500 units across."""
    b = BLEED_MM if bleed else 0.0
    art = size_mm + 2 * b          # artboard edge in mm
    U = art * 10                   # viewBox units
    c = U / 2                      # centre
    R = size_mm * 10 / 2           # trim radius

    p = SERIES[place]
    big = size_mm >= 40

    # Ring geometry, as fractions of the trim radius so both sizes stay in tune.
    r_ring = R * 0.945             # the accent ring
    r_hair = R * 0.876             # hairline inside it
    r_text = R * 0.775             # arc text baseline
    r_inner = R * 0.700            # the field the numeral sits on

    parts = []
    # Full-bleed ground. The disc is darker than the bleed so the cut edge has
    # something to sit against if the die wanders half a millimetre.
    parts.append(f'<rect width="{U}" height="{U}" fill="{VOID}"/>')
    parts.append(f'<circle cx="{c}" cy="{c}" r="{R}" fill="{DEEP_CURRENT}"/>')

    # Vol.7's ripple, faint, behind everything
    for i, rr in enumerate((r_inner * 0.42, r_inner * 0.66, r_inner * 0.90)):
        parts.append(f'<circle cx="{c}" cy="{c}" r="{rr:.1f}" fill="none" '
                     f'stroke="{accent}" stroke-opacity="{0.16 - i*0.04:.2f}" '
                     f'stroke-width="{R*0.012:.1f}"/>')

    parts.append(f'<circle cx="{c}" cy="{c}" r="{r_ring:.1f}" fill="none" '
                 f'stroke="{accent}" stroke-width="{R*0.052:.1f}"/>')
    parts.append(f'<circle cx="{c}" cy="{c}" r="{r_hair:.1f}" fill="none" '
                 f'stroke="{VOLTAGE}" stroke-opacity=".26" stroke-width="{R*0.010:.1f}"/>')

    # Arc text. The bottom arc is drawn right-to-left so it reads the right way up.
    parts.append(
        f'<defs>'
        f'<path id="top{place}" d="M {c-r_text:.1f} {c} A {r_text:.1f} {r_text:.1f} 0 0 1 {c+r_text:.1f} {c}"/>'
        # sweep 0, left point to right point, traces the LOWER arc — the same
        # construction the certificate seal uses. Starting from the right point
        # instead sends the text back over the top, on to the upper arc.
        f'<path id="bot{place}" d="M {c-r_text:.1f} {c} A {r_text:.1f} {r_text:.1f} 0 0 0 {c+r_text:.1f} {c}"/>'
        f'</defs>')

    if big:
        parts.append(
            f'<text font-family="JetBrains Mono, monospace" font-weight="700" '
            f'font-size="{R*0.108:.1f}" letter-spacing="{R*0.044:.2f}" fill="{VOLTAGE}" '
            f'fill-opacity=".92"><textPath href="#top{place}" startOffset="50%" '
            f'text-anchor="middle">URBAN PLAYGROUND</textPath></text>')
        parts.append(
            f'<text font-family="JetBrains Mono, monospace" font-weight="700" '
            f'font-size="{R*0.098:.1f}" letter-spacing="{R*0.036:.2f}" fill="{accent}" '
            f'><textPath href="#bot{place}" startOffset="50%" '
            f'text-anchor="middle">SEPTEMBER SURGE · VOL.7</textPath></text>')
        # diamonds at 3 and 9 o'clock, separating the two arcs
        for sx in (-1, 1):
            x = c + sx * r_text
            parts.append(f'<rect x="{x - R*0.026:.1f}" y="{c - R*0.026:.1f}" '
                         f'width="{R*0.052:.1f}" height="{R*0.052:.1f}" fill="{accent}" '
                         f'transform="rotate(45 {x:.1f} {c:.1f})"/>')
        # the emblem above the numeral
        ew, eh = R * 0.30, R * 0.44
        parts.append(f'<image href="data:image/png;base64,{emblem_b64}" '
                     f'x="{c-ew/2:.1f}" y="{c - R*0.62:.1f}" width="{ew:.1f}" height="{eh:.1f}" '
                     f'preserveAspectRatio="xMidYMid meet"/>')
        num_y, num_size, suf_size = c + R * 0.44, R * 0.80, R * 0.26
    else:
        # 25mm: one arc only, and the numeral carries the disc.
        parts.append(
            f'<text font-family="JetBrains Mono, monospace" font-weight="700" '
            f'font-size="{R*0.125:.1f}" letter-spacing="{R*0.050:.2f}" fill="{accent}" '
            f'><textPath href="#bot{place}" startOffset="50%" '
            f'text-anchor="middle">SEPTEMBER SURGE</textPath></text>')
        num_y, num_size, suf_size = c + R * 0.34, R * 1.00, R * 0.32

    # The numeral, in Vol.7's display face. The ordinal suffix rides high beside
    # it rather than sitting on the baseline, so "1ST" reads as one mark.
    #
    # Optical centring: text-anchor centres numeral+suffix together, which puts
    # the numeral — the thing the eye actually reads as the middle — left of the
    # disc's centre. Nudging right by a fraction of the suffix width corrects it.
    # "1" needs more of that correction than "2" or "3" because it is so much
    # narrower, so the mark's centre of mass sits further from the numeral.
    dx = suf_size * (0.55 if p["ord_"] == "1" else 0.18)
    parts.append(
        f'<text x="{c + dx:.1f}" y="{num_y:.1f}" text-anchor="middle" '
        f'font-family="Archivo" font-style="italic" font-size="{num_size:.1f}" '
        f'font-variation-settings="\'wdth\' 125, \'wght\' 900" fill="{accent}">'
        f'{p["ord_"]}<tspan font-size="{suf_size:.1f}" dy="{-num_size*0.42:.1f}">{p["suf"]}</tspan>'
        f'</text>')

    # Cut guide, drawn only on the bleed artboard.
    if bleed:
        parts.append(f'<circle cx="{c}" cy="{c}" r="{R}" fill="none" '
                     f'stroke="#FF00FF" stroke-opacity=".0" stroke-width="2"/>')

    clip = ''
    if not bleed:
        clip = (f'<defs><clipPath id="disc{place}">'
                f'<circle cx="{c}" cy="{c}" r="{R}"/></clipPath></defs>')
        parts[0] = ''    # drop the bleed ground; transparency outside the disc

    g_open = '<g>' if bleed else f'<g clip-path="url(#disc{place})">'
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {U} {U}" '
            f'width="{art}mm" height="{art}mm">{clip}' + g_open
            + "".join(parts) + '</g></svg>')


def build_html(place, size_mm, accent, emblem_b64, bleed):
    art = size_mm + (2 * BLEED_MM if bleed else 0)
    faces = open(FONT_BUNDLE).read()
    body_bg = VOID if bleed else "transparent"
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
{faces}
@page {{ size: {art}mm {art}mm; margin: 0; }}
*{{margin:0;padding:0;}}
html,body{{width:{art}mm;height:{art}mm;background:{body_bg};overflow:hidden;
  -webkit-print-color-adjust:exact;print-color-adjust:exact;}}
svg{{display:block;}}
</style></head><body>
{svg(place, size_mm, accent, emblem_b64, bleed)}
</body></html>"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--places", nargs="*", type=int, default=[1, 2, 3])
    ap.add_argument("--sizes", nargs="*", type=float, default=[50.0, 25.0])
    ap.add_argument("--metal", action="store_true",
                    help="Use gold/silver/bronze instead of the series ladder")
    a = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    emblem = b64(os.path.join(BRAND, "up-logo-cyan-2x.png"))

    for size in a.sizes:
        for place in a.places:
            accent = METAL[place] if a.metal else SERIES[place]["accent"]
            for bleed in (True, False):
                tag = "bleed" if bleed else "disc"
                h = os.path.join(OUT, f"ss-medal-{int(size)}mm-{place}-{tag}.html")
                with open(h, "w") as f:
                    f.write(build_html(place, size, accent, emblem, bleed))
            print(f"built {int(size)}mm · {place} · {accent}")
    print("\nnow render:  node render-surge-medal-stickers.mjs")


if __name__ == "__main__":
    main()
