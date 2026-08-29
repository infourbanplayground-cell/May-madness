# -*- coding: utf-8 -*-
"""August Attack (Vol.6) placement certificates, 1st through 5th.

A4 landscape, print-ready: a vector PDF for the print shop plus a 300 DPI PNG
for previewing and for anyone who just wants to send an image.

Design follows DESIGN.md rather than certificate convention:
  - Court Black full bleed. August Attack is the neon-night volume; a white
    certificate would not read as part of this series.
  - Placement colours use the series ladder (Attack Red -> light steel ->
    steel), NOT gold/silver/bronze. DESIGN.md is explicit that gold is not in
    this palette, and the medal chips in the app already use this ladder.
  - Anton for display, Archivo for body, JetBrains Mono for the data line —
    the same three faces the app loads.

Fonts are embedded as base64 so the file renders identically anywhere, with no
network and no font-substitution surprises at the print shop. Same for the two
brand marks.

  python3 build-certificates.py            # all five
  python3 build-certificates.py --places 1 2 3
"""
import argparse, base64, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = "/tmp/certs/fonts"
BRAND = os.path.join(HERE, "brand", "august-attack")
OUT = os.path.join(HERE, "brand", "certificates")

# ── Palette (DESIGN.md §2) ────────────────────────────────────────────────
COURT_BLACK = "#0A0C12"
DEEP_BLACK  = "#06070B"
ATTACK_RED  = "#FF2E43"
CHALK       = "#F4F6FA"
STEEL       = "#8B95A7"
LIGHT_STEEL = "#C9CFDA"

# Placement ladder — red, light steel, steel; 4th/5th stay steel and lean on
# the numeral rather than inventing two more colours the series doesn't have.
# The sub-label names the honour instead of restating the number, which would
# just read as "3RD PLACE / THIRD PLACE".
PLACES = {
    1: dict(ord_="1ST", word="FIRST",  accent=ATTACK_RED,  label="CHAMPIONS"),
    2: dict(ord_="2ND", word="SECOND", accent=LIGHT_STEEL, label="RUNNERS-UP"),
    3: dict(ord_="3RD", word="THIRD",  accent=STEEL,       label="PODIUM FINISH"),
    4: dict(ord_="4TH", word="FOURTH", accent=STEEL,       label="TOP FIVE"),
    5: dict(ord_="5TH", word="FIFTH",  accent=STEEL,       label="TOP FIVE"),
}


def b64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()


def font_face(family, weight, filename, style="normal"):
    return (f"@font-face{{font-family:'{family}';font-style:{style};font-weight:{weight};"
            f"font-display:block;src:url(data:font/woff2;base64,{b64(os.path.join(FONTS, filename))}) "
            f"format('woff2');}}")


def build_html(place):
    p = PLACES[place]
    faces = "".join([
        font_face("Anton", 400, "anton-400.woff2"),
        font_face("Archivo", 400, "archivo-400.woff2"),
        font_face("Archivo", 600, "archivo-600.woff2"),
        font_face("Archivo", 800, "archivo-800.woff2"),
        font_face("Archivo", 900, "archivo-900.woff2"),
        font_face("Mono", 500, "jbmono-500.woff2"),
        font_face("Mono", 700, "jbmono-700.woff2"),
    ])
    wordmark = b64(os.path.join(BRAND, "aa-wordmark-full-colour@4x.png"))
    emblem = b64(os.path.join(BRAND, "aa-emblem-full-colour@4x.png"))

    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
{faces}
@page {{ size: A4 landscape; margin: 0; }}
*{{margin:0;padding:0;box-sizing:border-box;}}
html,body{{width:297mm;height:210mm;}}
body{{
  background:{COURT_BLACK};
  font-family:'Archivo',system-ui,sans-serif;
  color:{CHALK};
  -webkit-print-color-adjust:exact; print-color-adjust:exact;
  position:relative; overflow:hidden;
}}
/* Tactical grid — the Vol.6 motif, kept faint so it never fights the type */
.grid{{position:absolute;inset:0;
  background-image:
    linear-gradient(rgba(244,246,250,.028) 1px, transparent 1px),
    linear-gradient(90deg, rgba(244,246,250,.028) 1px, transparent 1px);
  background-size:14mm 14mm;}}
.floor{{position:absolute;left:0;right:0;bottom:0;height:70mm;
  background:linear-gradient(to bottom, rgba(6,7,11,0), {DEEP_BLACK});}}
.glow{{position:absolute;width:150mm;height:150mm;border-radius:50%;
  left:50%;top:32%;transform:translate(-50%,-50%);
  background:radial-gradient(circle, {p['accent']}22 0%, transparent 62%);}}

.edge{{position:absolute;inset:7mm;border:.7pt solid rgba(244,246,250,.16);}}
.rule{{position:absolute;top:7mm;left:7mm;right:7mm;height:2.2mm;background:{p['accent']};}}

/* Corner ticks — the card marker from the app, drawn at certificate scale */
.tick{{position:absolute;width:9mm;height:9mm;}}
.tick::before,.tick::after{{content:"";position:absolute;background:{p['accent']};}}
.tick::before{{width:9mm;height:.6mm;}} .tick::after{{width:.6mm;height:9mm;}}
.tl{{left:7mm;top:7mm;}} .tr{{right:7mm;top:7mm;}}
.tr::before{{right:0;}} .tr::after{{right:0;}}
.bl{{left:7mm;bottom:7mm;}} .bl::before{{bottom:0;}} .bl::after{{bottom:0;}}
.br{{right:7mm;bottom:7mm;}}
.br::before{{right:0;bottom:0;}} .br::after{{right:0;bottom:0;}}

/* Main block is centred in the page and the footer is pinned, so the leftover
   space splits above and below the content instead of pooling in one gap. */
.wrap{{position:relative;height:100%;display:flex;flex-direction:column;
  align-items:center;justify-content:center;padding:16mm 24mm 34mm;text-align:center;}}

.wordmark{{height:23mm;margin-bottom:1mm;}}
.vol{{font-family:'Mono',monospace;font-weight:700;font-size:8.5pt;
  letter-spacing:.34em;color:{STEEL};text-transform:uppercase;}}

.kicker{{font-family:'Mono',monospace;font-weight:700;font-size:8pt;
  letter-spacing:.42em;color:{p['accent']};margin-top:9mm;}}

.place{{font-family:'Anton',sans-serif;letter-spacing:.05em;line-height:.9;
  font-size:{'62pt' if place == 1 else '56pt'};color:{p['accent']};margin-top:2.5mm;
  text-shadow:0 0 14mm {p['accent']}44;}}
.label{{font-family:'Archivo',sans-serif;font-weight:900;font-size:12.5pt;
  letter-spacing:.30em;color:{CHALK};margin-top:1.5mm;text-transform:uppercase;}}

.awarded{{font-size:10pt;color:{STEEL};margin-top:8mm;letter-spacing:.03em;}}

/* Name is left blank deliberately: the series is still running, so these are
   templates the organiser fills in — by hand on the printed card, or by
   typing into the PDF before printing. */
.nameline{{width:150mm;margin:5mm auto 0;border-bottom:1pt solid rgba(244,246,250,.42);height:15mm;}}
.namehint{{font-family:'Mono',monospace;font-size:6.5pt;letter-spacing:.3em;
  color:rgba(139,149,167,.62);margin-top:2mm;text-transform:uppercase;}}

.body{{font-size:9.5pt;color:{STEEL};margin-top:7mm;max-width:175mm;line-height:1.65;}}
.body b{{color:{CHALK};font-weight:800;}}

.foot{{position:absolute;left:24mm;right:24mm;bottom:15mm;display:flex;
  align-items:flex-end;justify-content:space-between;gap:14mm;}}
.sig{{width:70mm;text-align:center;}}
.sigline{{border-bottom:.8pt solid rgba(244,246,250,.34);height:11mm;}}
.sigcap{{font-family:'Mono',monospace;font-size:6.5pt;letter-spacing:.26em;
  color:{STEEL};margin-top:2mm;text-transform:uppercase;}}
/* Emblem sits above the signature baseline with clear space on both sides —
   DESIGN.md asks for at least 25% of its width around the mark. */
.emblem{{height:30mm;opacity:.95;margin:0 6mm 1mm;}}
</style></head><body>
<div class="grid"></div><div class="glow"></div><div class="floor"></div>
<div class="edge"></div><div class="rule"></div>
<div class="tick tl"></div><div class="tick tr"></div>
<div class="tick bl"></div><div class="tick br"></div>

<div class="wrap">
  <img class="wordmark" src="data:image/png;base64,{wordmark}" alt="August Attack">
  <div class="vol">Urban Playground · Vol.6 · Muscat</div>

  <div class="kicker">CERTIFICATE OF ACHIEVEMENT</div>
  <div class="place">{p['ord_']} PLACE</div>
  <div class="label">{p['label']}</div>

  <div class="awarded">This certificate is proudly awarded to</div>
  <div class="nameline"></div>
  <div class="namehint">Name</div>

  <div class="body">
    for finishing <b>{p['word']}</b> in the <b>August Attack</b> series at Urban Playground —
    earned across nine sessions of group play and knockouts.
  </div>

  <div class="foot">
    <div class="sig"><div class="sigline"></div><div class="sigcap">Date</div></div>
    <img class="emblem" src="data:image/png;base64,{emblem}" alt="Urban Playground">
    <div class="sig"><div class="sigline"></div><div class="sigcap">Tournament Director</div></div>
  </div>
</div>
</body></html>"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--places", nargs="*", type=int, default=[1, 2, 3, 4, 5])
    a = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    made = []
    for place in a.places:
        html = build_html(place)
        h = os.path.join(OUT, f"aa-certificate-{place}.html")
        with open(h, "w") as f:
            f.write(html)
        made.append(h)
        print(f"built {os.path.basename(h)}  ({len(html)/1024:.0f}KB)")
    print("\nnow render:  node render-certificates.mjs")


if __name__ == "__main__":
    main()
