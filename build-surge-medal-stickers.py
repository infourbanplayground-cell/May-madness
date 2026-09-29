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

BRONZE = "#C3813F"

SERIES = {
    1: dict(ord_="1", suf="ST"),
    2: dict(ord_="2", suf="ND"),
    3: dict(ord_="3", suf="RD"),
}

# Three colourways. All-cyan is the default: the numeral already says which
# placement this is, and DESIGN.md has cyan leading the volume, so a set that is
# one colour throughout reads as a series rather than as three separate awards.
#
# The metal ladders are kept because they are one flag away if these ever have
# to sit next to conventional gold/silver/bronze ribbons. Bronze is the one
# warm colour in here and a deliberate exception to DESIGN.md's rule that warm
# accents mean urgency -- it is cooler and darker than Strike Amber, so the two
# cannot be confused anywhere else in the system.
WAYS = {
    "cyan":   {1: SURGE_CYAN, 2: SURGE_CYAN,  3: SURGE_CYAN},
    "ladder": {1: SURGE_CYAN, 2: LIGHT_STEEL, 3: BRONZE},
    "metal":  {1: "#E3B341", 2: "#C9CDD2",    3: BRONZE},
}

BLEED_MM = 3.0
# surge-lockup@1600.png is 1600x750; the height follows the width so the
# mark is never squashed by a change to the disc size.
LOCKUP_RATIO = 750 / 1600


def b64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()


def cap_centre(c, font_size):
    """Baseline that puts a run of capitals' optical centre on the disc's centre.

    The placement numeral is the mark, so it belongs dead centre — it used to
    hang below it, because the lockup was sized to push it down. Caps sit
    roughly from baseline-0.72em to the baseline, so their middle is about
    0.35em above it; the baseline therefore goes 0.35em below centre.
    """
    return c + font_size * 0.35


def svg(place, size_mm, accent, lockup_b64, bleed=True):
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
    # Four rings now rather than three, and a touch stronger: with the numeral
    # centred on them they read as a motif radiating from it rather than as
    # stray circles behind an off-centre mark.
    for i, rr in enumerate((r_inner * 0.34, r_inner * 0.56, r_inner * 0.78, r_inner * 1.00)):
        parts.append(f'<circle cx="{c}" cy="{c}" r="{rr:.1f}" fill="none" '
                     f'stroke="{accent}" stroke-opacity="{0.22 - i*0.045:.2f}" '
                     f'stroke-width="{R*0.013:.1f}"/>')

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
        # The September Surge lockup is the mark, not the bare emblem. It already
        # says SEPTEMBER SURGE, so the top arc that used to repeat it is gone —
        # the lockup fills that space instead, and the one remaining arc carries
        # what the lockup does not: the club and the volume.
        lw = R * 0.86
        lh = lw * LOCKUP_RATIO
        parts.append(f'<image href="data:image/png;base64,{lockup_b64}" '
                     f'x="{c-lw/2:.1f}" y="{c - R*0.76:.1f}" '
                     f'width="{lw:.1f}" height="{lh:.1f}" '
                     f'preserveAspectRatio="xMidYMid meet"/>')
        parts.append(
            f'<text font-family="JetBrains Mono, monospace" font-weight="700" '
            f'font-size="{R*0.100:.1f}" letter-spacing="{R*0.038:.2f}" fill="{accent}" '
            f'><textPath href="#bot{place}" startOffset="50%" '
            f'text-anchor="middle">URBAN PLAYGROUND · VOL.7</textPath></text>')
        # diamonds at 3 and 9 o'clock, closing the arc
        for sx in (-1, 1):
            x = c + sx * r_text
            parts.append(f'<rect x="{x - R*0.026:.1f}" y="{c - R*0.026:.1f}" '
                         f'width="{R*0.052:.1f}" height="{R*0.052:.1f}" fill="{accent}" '
                         f'transform="rotate(45 {x:.1f} {c:.1f})"/>')
        num_size = R * 0.78
        num_y, suf_size = cap_centre(c, num_size), R * 0.26
    else:
        # 25mm: the lockup and the numeral, nothing else. Arc text at this
        # diameter is under a millimetre tall and prints as grey fuzz.
        lw = R * 0.92
        lh = lw * LOCKUP_RATIO
        parts.append(f'<image href="data:image/png;base64,{lockup_b64}" '
                     f'x="{c-lw/2:.1f}" y="{c - R*0.80:.1f}" '
                     f'width="{lw:.1f}" height="{lh:.1f}" '
                     f'preserveAspectRatio="xMidYMid meet"/>')
        num_size = R * 0.86
        num_y, suf_size = cap_centre(c, num_size), R * 0.28

    # The numeral, in Vol.7's display face, with the ordinal riding high beside
    # it so the pair reads as one mark.
    #
    # The numeral is the placement logo, so it sits dead centre — and "centre"
    # is measured, not guessed. Anchoring numeral+suffix together leaves the
    # numeral itself well left of centre (the suffix drags the anchor), and
    # correcting that with a hand-tuned nudge per digit was still 2-6% out
    # because the right factor depends on the glyph, the size and the font's
    # actual advance widths. So the two are separate elements and the page
    # measures the numeral's box once the font has loaded, then places both:
    # numeral centred on the disc, suffix hugging its right edge.
    parts.append(
        f'<text id="num" x="{c:.1f}" y="{num_y:.1f}" text-anchor="middle" '
        f'font-family="Archivo" font-style="italic" font-size="{num_size:.1f}" '
        f'font-variation-settings="\'wdth\' 125, \'wght\' 900" fill="{accent}">'
        f'{p["ord_"]}</text>')
    parts.append(
        f'<text id="suf" x="{c:.1f}" y="{num_y - num_size*0.42:.1f}" text-anchor="start" '
        f'font-family="Archivo" font-style="italic" font-size="{suf_size:.1f}" '
        f'font-variation-settings="\'wdth\' 125, \'wght\' 900" fill="{accent}">'
        f'{p["suf"]}</text>')

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


def build_html(place, size_mm, accent, lockup_b64, bleed):
    art = size_mm + (2 * BLEED_MM if bleed else 0)
    c_units = art * 10 / 2
    gap = size_mm * 10 / 2 * 0.03
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
{svg(place, size_mm, accent, lockup_b64, bleed)}
<script>
// Centre the numeral on the disc and hang the ordinal off its right edge.
// Done here rather than in the SVG because it needs the font's real advance
// width, which only exists once the face has loaded.
document.fonts.ready.then(() => {{
  const num = document.getElementById('num');
  const suf = document.getElementById('suf');
  const svg = document.querySelector('svg');
  const C = {c_units};
  const nb = num.getBBox();
  num.setAttribute('x', (Number(num.getAttribute('x')) + (C - (nb.x + nb.width / 2))).toFixed(2));
  const nb2 = num.getBBox();
  suf.setAttribute('x', (nb2.x + nb2.width + {gap:.1f}).toFixed(2));
  svg.dataset.centred = '1';
}});
</script>
</body></html>"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--places", nargs="*", type=int, default=[1, 2, 3])
    ap.add_argument("--sizes", nargs="*", type=float, default=[50.0, 25.0])
    ap.add_argument("--way", choices=sorted(WAYS), default="cyan",
                    help="Colourway: cyan (all three, default), "
                         "ladder (cyan/silver/bronze), metal (gold/silver/bronze)")
    a = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    lockup = b64(os.path.join(BRAND, "surge-lockup@1600.png"))

    for size in a.sizes:
        for place in a.places:
            accent = WAYS[a.way][place]
            for bleed in (True, False):
                tag = "bleed" if bleed else "disc"
                h = os.path.join(OUT, f"ss-medal-{int(size)}mm-{place}-{tag}.html")
                with open(h, "w") as f:
                    f.write(build_html(place, size, accent, lockup, bleed))
            print(f"built {int(size)}mm · {place} · {a.way} · {accent}")
    print("\nnow render:  node render-surge-medal-stickers.mjs")


if __name__ == "__main__":
    main()
