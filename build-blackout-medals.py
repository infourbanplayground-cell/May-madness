# -*- coding: utf-8 -*-
"""Blackout Series (Vol.8) medal cut-outs — circular inserts, 1st to 3rd.

THE LOGO IS THE MARK AND THE PLACEMENT IS A GHOST BEHIND IT. The numeral fills
the field at 20% opacity, clipped to just inside the hairline ring, with the
Blackout mark dead centre on top of it at full strength. `--layout numeral`
flips that round — the placement centred and solid, the logo small above it.

Two sizes, because medal inserts come in two: 50mm (2in) and 25mm (1in). They
are not the same artwork scaled — arc text that reads at 50mm turns to mush at
half the diameter, so the numeral cut drops the arc at 25mm. The LOGO cut
cannot: the ghost is decorative, so the arc is the only thing on the cut-out
that states the placement in words, and one whose only claim to "1st" is a
20%-opacity shape is not one anybody can sort at the prize table.

Each is produced two ways:

  *-disc.png    THE CUT-OUT: trimmed to the circle, transparent outside it, for
                dropping onto a photo or a medal blank
  *-bleed.png   square, trim + 3mm bleed, black to the edge — give this to the
                printer for die-cut stickers, and it packs to a PDF at exact
                physical size

NO GOLD/SILVER/BRONZE by default. It is not in this palette, and the app's own
medal chips do not use it. The placement is carried by the numeral; the default
colourway is lime throughout, so a set of three reads as one series rather than
as three unrelated awards. `--way metal` is one flag away if these ever have to
sit beside conventional gold/silver/bronze ribbons.

NO SOFT GLOWS. build-blackout-brand.py records why: Chromium tiles big blurred
shadows and the seams print as hard-edged rectangles. Everything here is a hard
edge. The disc itself is the one deliberate circle, the same exception the
certificate's seal takes.

  python3 build-blackout-medals.py
  python3 build-blackout-medals.py --way metal
  python3 build-blackout-medals.py --sizes 50
"""
import argparse, base64, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "ops"))
from font_bundle import bundle as font_bundle          # noqa: E402

BRAND = os.path.join(HERE, "brand", "blackout")
OUT = os.path.join(HERE, "brand", "medals-blackout")
SEASON = os.path.join(HERE, "blackout-season.json")

_S = json.load(open(SEASON))
PAL = _S["palette"]
BG       = PAL["bg"]
LIME     = PAL["lime"]
LIMEPALE = PAL["limePale"]
LIMEDEEP = PAL["limeDeep"]
INK      = PAL["ink"]
VOLUME   = _S["volume"]

SERIES = {1: dict(ord_="1", suf="ST"),
          2: dict(ord_="2", suf="ND"),
          3: dict(ord_="3", suf="RD")}

WAYS = {
    "lime":   {1: LIME, 2: LIME,     3: LIME},
    "ladder": {1: LIME, 2: LIMEPALE, 3: LIMEDEEP},
    "metal":  {1: "#E3B341", 2: "#C9CDD2", 3: "#C3813F"},
}

BLEED_MM = 3.0

# Archivo's variable weight axis tops out at 900 and the width axis at 125, so
# the numerals are already as bold as the face goes. To get heavier without
# leaving the volume's typeface, each numeral is stroked in its own colour with
# paint-order putting the stroke behind the fill: the glyph fattens evenly on
# every edge and the counters stay open. 0.055em is about a weight-step; much
# past 0.08 and the "1"'s spur and the "3"'s bowls start to close up.
BOLD_STROKE = 0.055


def b64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()


def bold(colour, font_size):
    """Stroke attributes that fatten a glyph without changing its shape."""
    return (f' stroke="{colour}" stroke-width="{font_size*BOLD_STROKE:.2f}"'
            f' stroke-linejoin="round" paint-order="stroke fill"')


def cap_centre(c, font_size):
    """Baseline that puts a run of capitals' optical centre on the disc's centre.

    The placement numeral is the mark, so it belongs dead centre. Caps sit
    roughly from baseline-0.72em to the baseline, so their middle is about
    0.35em above it; the baseline therefore goes 0.35em below centre.
    """
    return c + font_size * 0.35


def svg(place, size_mm, accent, mark_b64, bleed=True, layout="logo"):
    """One cut-out. Units are 0.1mm, so a 50mm disc is 500 units across."""
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

    parts = []
    # Full-bleed ground, on the bleed artboard only. The disc is the same black,
    # so a die that wanders half a millimetre cuts into more of the same colour
    # rather than into a visible seam.
    parts.append(f'<rect width="{U}" height="{U}" fill="{BG}"/>')
    parts.append(f'<circle cx="{c}" cy="{c}" r="{R}" fill="{BG}"/>')

    # Vol.8's page texture, as a field inside the disc: the app's tactical grid,
    # hard-edged. Clipped to the disc so it cannot print across the cut line.
    pitch = R * 0.20
    parts.append(
        f'<defs><clipPath id="fld{place}{int(size_mm)}">'
        f'<circle cx="{c}" cy="{c}" r="{r_hair:.1f}"/></clipPath>'
        f'<pattern id="grd{place}{int(size_mm)}" width="{pitch:.1f}" height="{pitch:.1f}" '
        f'patternUnits="userSpaceOnUse">'
        f'<path d="M0 0 H{pitch:.1f} M0 0 V{pitch:.1f}" stroke="{accent}" '
        f'stroke-opacity=".16" stroke-width="{R*0.010:.2f}"/></pattern></defs>'
        f'<rect x="0" y="0" width="{U}" height="{U}" fill="url(#grd{place}{int(size_mm)})" '
        f'clip-path="url(#fld{place}{int(size_mm)})"/>')

    parts.append(f'<circle cx="{c}" cy="{c}" r="{r_ring:.1f}" fill="none" '
                 f'stroke="{accent}" stroke-width="{R*0.052:.1f}"/>')
    parts.append(f'<circle cx="{c}" cy="{c}" r="{r_hair:.1f}" fill="none" '
                 f'stroke="{INK}" stroke-opacity=".26" stroke-width="{R*0.010:.1f}"/>')

    # The one arc, at the foot. The path takes sweep 0 from the LEFT point,
    # which traces the lower arc left to right. Starting from the right point
    # instead sends the words back over the top and sets them mirrored.
    def arc(text, size_f, track_f):
        return (
            f'<defs><path id="bot{place}{int(size_mm)}" '
            f'd="M {c-r_text:.1f} {c} A {r_text:.1f} {r_text:.1f} 0 0 0 {c+r_text:.1f} {c}"/>'
            f'</defs>'
            f'<text font-family="JetBrains Mono, monospace" font-weight="700" '
            f'font-size="{R*size_f:.1f}" letter-spacing="{R*track_f:.2f}" fill="{accent}">'
            f'<textPath href="#bot{place}{int(size_mm)}" startOffset="50%" '
            f'text-anchor="middle">{text}</textPath></text>')

    # Squares at 3 and 9 o'clock, closing the arc. Vol.7 set these as diamonds;
    # this volume has radius 0 and no rotated geometry anywhere, so they sit
    # square. Only at 50mm — at 25mm they crowd an arc that is already tight.
    def stops():
        out = []
        for sx in (-1, 1):
            x = c + sx * r_text
            out.append(f'<rect x="{x - R*0.024:.1f}" y="{c - R*0.024:.1f}" '
                       f'width="{R*0.048:.1f}" height="{R*0.048:.1f}" fill="{accent}"/>')
        return out

    if layout == "logo":
        # THE PLACEMENT IS A GHOST AND THE LOGO IS THE MARK. The numeral fills
        # the field behind at low opacity, big enough to read as a motif rather
        # than as a number somebody forgot to finish.
        #
        # It is CLIPPED to just inside the hairline ring. Unclipped it runs off
        # the disc into the bleed, so the crop reads as an accident — and on the
        # square artboard you can read "1ST" sitting outside its own sticker.
        #
        # The opacity goes on the GROUP, not on fill and stroke separately: at
        # 20% each they composite to ~36% where they overlap, so the glyph gets
        # a lighter rim and reads as outlined rather than as bolder.
        ghost = R * (1.02 if big else 1.12)
        parts.append(
            f'<defs><clipPath id="gh{place}{int(size_mm)}">'
            f'<circle cx="{c}" cy="{c}" r="{r_hair - R*0.012:.1f}"/></clipPath></defs>'
            f'<g clip-path="url(#gh{place}{int(size_mm)})" opacity="0.20">'
            f'<text id="ghost" x="{c:.1f}" y="{cap_centre(c, ghost):.1f}" text-anchor="middle" '
            f'font-family="Archivo" font-style="italic" font-size="{ghost:.1f}" '
            f'font-variation-settings="\'wdth\' 125, \'wght\' 900" fill="{accent}"'
            f'{bold(accent, ghost)}>{p["ord_"]}{p["suf"]}</text></g>')

        # The logo, dead centre, at full strength: the mark with BLACKOUT set
        # under it, the same order and the same two inks as the real lockup
        # (BLACK in ink, OUT in the accent). The horizontal lockup PNG is not
        # used because it carries a sub-line of small type that is under a
        # millimetre tall at 50mm and prints as grey fuzz; the word is set as
        # live type instead so it can be fitted to the disc at either size.
        #
        # The pair is treated as one stacked lockup and centred on the disc as
        # a whole, so the mark sits above centre and the word below it.
        mw = R * (0.40 if big else 0.40)
        ws = R * (0.26 if big else 0.30)
        cap = ws * 0.72                     # cap height of a run of capitals
        gap = R * 0.095
        top = c - (mw + gap + cap) / 2
        # The two are wrapped so the page can centre the PAIR vertically once
        # the font has loaded. `cap` above is an estimate of a capital's height
        # (0.72em); the real ink box differs by a few per cent, which left the
        # lockup 3% of the radius low at 25mm. Estimate to lay it out, measure
        # to place it — the same rule as everything else here.
        parts.append(f'<g id="lockup">'
                     f'<image href="data:image/png;base64,{mark_b64}" '
                     f'x="{c-mw/2:.1f}" y="{top:.1f}" '
                     f'width="{mw:.1f}" height="{mw:.1f}" '
                     f'preserveAspectRatio="xMidYMid meet"/>')
        wy = top + mw + gap + cap
        parts.append(
            f'<text id="word" x="{c:.1f}" y="{wy:.1f}" text-anchor="middle" '
            f'font-family="Archivo" font-style="italic" font-size="{ws:.1f}" '
            f'font-variation-settings="\'wdth\' 125, \'wght\' 900" '
            f'letter-spacing="{-ws*0.012:.2f}" '
            f'data-yoff="{wy - c - cap/2:.2f}" data-rlimit="{r_hair - R*0.012:.2f}" '
            f'data-fs0="{ws:.1f}">'
            f'<tspan fill="{INK}">BLACK</tspan>'
            f'<tspan fill="{accent}">OUT</tspan></text></g>')

        # BECAUSE THE GHOST IS DECORATIVE, THE ARC HAS TO CARRY THE PLACEMENT IN
        # WORDS — at BOTH sizes. A cut-out whose only statement of "1st" is a
        # 20%-opacity shape is not one anybody can sort at the prize table, and
        # that is the whole job of a medal insert. The volume is dropped at 25mm
        # so the remaining words can be set larger.
        parts.append(arc(f'{p["ord_"]}{p["suf"]} PLACE' + (f' · {VOLUME}' if big else ''),
                         0.098 if big else 0.116, 0.036 if big else 0.042))
        if big:
            parts += stops()
    else:
        # The placement at full strength, centred, with the logo above it.
        # Louder about which medal this is, quieter about the series.
        mw = R * (0.30 if big else 0.34)
        parts.append(f'<image href="data:image/png;base64,{mark_b64}" '
                     f'x="{c-mw/2:.1f}" y="{c - R*(0.66 if big else 0.70):.1f}" '
                     f'width="{mw:.1f}" height="{mw:.1f}" '
                     f'preserveAspectRatio="xMidYMid meet"/>')
        if big:
            parts.append(arc(f'BLACKOUT · {VOLUME}', 0.098, 0.036))
            parts += stops()
            num_size, suf_size = R * 0.74, R * 0.25
        else:
            num_size, suf_size = R * 0.80, R * 0.27
        num_y = cap_centre(c + R * 0.08, num_size)

        # The numeral, with the ordinal riding high beside it so the pair reads
        # as one mark.
        #
        # "Centre" is MEASURED, not guessed. Anchoring numeral+suffix together
        # leaves the numeral itself well left of centre (the suffix drags the
        # anchor), and correcting that with a hand-tuned nudge per digit was
        # still 2-6% out, because the right factor depends on the glyph, the
        # size and the font's real advance widths. So the two are separate
        # elements and the page measures the numeral's box once the font has
        # loaded, then places both.
        parts.append(
            f'<text id="num" x="{c:.1f}" y="{num_y:.1f}" text-anchor="middle" '
            f'font-family="Archivo" font-style="italic" font-size="{num_size:.1f}" '
            f'font-variation-settings="\'wdth\' 125, \'wght\' 900" fill="{accent}"'
            f'{bold(accent, num_size)}>{p["ord_"]}</text>')
        parts.append(
            f'<text id="suf" x="{c:.1f}" y="{num_y - num_size*0.42:.1f}" text-anchor="start" '
            f'font-family="Archivo" font-style="italic" font-size="{suf_size:.1f}" '
            f'font-variation-settings="\'wdth\' 125, \'wght\' 900" fill="{accent}"'
            f'{bold(accent, suf_size)}>{p["suf"]}</text>')

    clip = ""
    g_open = "<g>"
    if not bleed:
        clip = (f'<defs><clipPath id="disc{place}{int(size_mm)}">'
                f'<circle cx="{c}" cy="{c}" r="{R}"/></clipPath></defs>')
        g_open = f'<g clip-path="url(#disc{place}{int(size_mm)})">'
        parts[0] = ""    # drop the bleed ground; transparency outside the disc

    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {U} {U}" '
            f'width="{art}mm" height="{art}mm">{clip}' + g_open
            + "".join(parts) + "</g></svg>")


def build_html(place, size_mm, accent, mark_b64, bleed, layout="logo"):
    art = size_mm + (2 * BLEED_MM if bleed else 0)
    c_units = art * 10 / 2
    gap = size_mm * 10 / 2 * 0.03
    faces = font_bundle()
    body_bg = BG if bleed else "transparent"
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
{faces}
@page {{ size: {art}mm {art}mm; margin: 0; }}
*{{margin:0;padding:0;}}
html,body{{width:{art}mm;height:{art}mm;background:{body_bg};overflow:hidden;
  -webkit-print-color-adjust:exact;print-color-adjust:exact;}}
svg{{display:block;}}
</style></head><body>
{svg(place, size_mm, accent, mark_b64, bleed, layout)}
<script>
// Centre the numeral on the disc and hang the ordinal off its right edge.
// Done here rather than in the SVG because it needs the font's real advance
// width, which only exists once the face has loaded. The renderer blocks on
// the flag below — screenshot before this lands and every cut-out ships with
// its mark off-centre, which is exactly the bug this pass exists to fix.
document.fonts.ready.then(() => {{
  const num = document.getElementById('num');
  const suf = document.getElementById('suf');
  const svg = document.querySelector('svg');
  const C = {c_units};
  // The logo layout has no solid numeral — the placement is one ghost string
  // sitting behind the logo. text-anchor="middle" centres on the ADVANCE
  // width, and an italic glyph's ink does not sit centred inside its advance:
  // "1ST" measured 1.4% of the disc off to the right, because the 1 carries a
  // wide left side bearing. Same measure-then-place pass as the numeral.
  const ghost = document.getElementById('ghost');
  if (ghost) {{
    const gb = ghost.getBBox();
    ghost.setAttribute('x',
      (Number(ghost.getAttribute('x')) + (C - (gb.x + gb.width / 2))).toFixed(2));
  }}

  // BLACKOUT is shrunk to the chord of the disc at its own height, not to the
  // disc's width: the word does not sit on the diameter, so the space it has
  // is narrower than the field is wide, and sizing it against the field is how
  // a wordmark ends up touching the ring. Measured after the font loads — the
  // fallback face is nothing like Archivo at wdth 125, so a fit computed any
  // earlier is a fit against the wrong letters.
  const word = document.getElementById('word');
  if (word) {{
    const y = Number(word.dataset.yoff), rl = Number(word.dataset.rlimit);
    const max = 2 * Math.sqrt(Math.max(0, rl * rl - y * y)) * 0.92;
    let fs = Number(word.getAttribute('font-size'));
    for (let i = 0; i < 60 && word.getBBox().width > max; i++) {{
      fs *= 0.97;
      word.setAttribute('font-size', fs.toFixed(3));
    }}
    const wb = word.getBBox();
    word.setAttribute('x',
      (Number(word.getAttribute('x')) + (C - (wb.x + wb.width / 2))).toFixed(2));
    svg.dataset.wordFit = (fs / Number(word.dataset.fs0 || fs)).toFixed(3);

    // Now centre the mark and the word as ONE pair on the disc.
    const lock = document.getElementById('lockup');
    const lb = lock.getBBox();
    lock.setAttribute('transform',
      `translate(0 ${{(C - (lb.y + lb.height / 2)).toFixed(2)}})`);
  }}
  if (!num || !suf) {{ svg.dataset.centred = '1'; return; }}
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
    ap.add_argument("--layout", choices=("logo", "numeral"), default="logo",
                    help="logo: the logo centred, the placement a ghost motif "
                         "behind it (default). numeral: the placement centred "
                         "at full strength, the logo above it.")
    ap.add_argument("--way", choices=sorted(WAYS), default="lime",
                    help="Colourway: lime (all three, default), "
                         "ladder (lime/pale/deep), metal (gold/silver/bronze)")
    a = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    mark = b64(os.path.join(BRAND, "blackout-mark-transparent.png"))

    for size in a.sizes:
        for place in a.places:
            accent = WAYS[a.way][place]
            for bleed in (True, False):
                tag = "bleed" if bleed else "disc"
                h = os.path.join(OUT, f"bo-medal-{int(size)}mm-{place}-{tag}.html")
                with open(h, "w") as f:
                    f.write(build_html(place, size, accent, mark, bleed, a.layout))
            print(f"built {int(size)}mm · {place} · {a.layout} · {a.way} · {accent}")
    print("\nnow render:  node render-blackout-medals.mjs")


if __name__ == "__main__":
    main()
