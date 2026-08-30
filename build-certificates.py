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


def burst_rays(accent, spikes=28, r_out=500, r_in=352, width_deg=3.1, opacity=".5"):
    """The Vol.6 attack burst, rebuilt in the placement colour.

    Geometry matches assets/aa-burst.svg — alternating long/short spikes radiating
    from a common inner radius — rather than being a new motif. That file ships on
    the server but is referenced nowhere; this is the same mark, recoloured per
    placement, which is the one recolouring DESIGN.md's "never recolour" rule
    doesn't cover (it governs the logo marks, not the burst).
    """
    import math
    parts = []
    for i in range(spikes):
        a = (360 / spikes) * i
        long_ = (i % 2 == 0)
        ro = r_out if long_ else r_out * 0.74
        w = width_deg if long_ else width_deg * 0.78
        ax, ay = math.radians(a), math.radians(a - w)
        bz = math.radians(a + w)
        tip = (500 + ro * math.cos(ax), 500 + ro * math.sin(ax))
        p1 = (500 + r_in * math.cos(ay), 500 + r_in * math.sin(ay))
        p2 = (500 + r_in * math.cos(bz), 500 + r_in * math.sin(bz))
        parts.append(f'<polygon points="{tip[0]:.1f},{tip[1]:.1f} {p1[0]:.1f},{p1[1]:.1f} '
                     f'{p2[0]:.1f},{p2[1]:.1f}" fill="{accent}" opacity="{opacity}"/>')
    return ('<svg viewBox="0 0 1000 1000" xmlns="http://www.w3.org/2000/svg">'
            + "".join(parts) + '</svg>')


def seal(accent, emblem_b64):
    """Circular seal: ring rules, arc-set lettering, emblem at the centre.

    Replaces the bare emblem that previously floated between the two signature
    lines — a certificate wants a seal at the foot, and this reads as one
    without inventing any new brand element.
    """
    return f"""<svg class="sealsvg" viewBox="0 0 400 400" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <path id="arcTop" d="M 60 200 A 140 140 0 0 1 340 200"/>
    <path id="arcBot" d="M 62 200 A 138 138 0 0 0 338 200"/>
  </defs>
  <circle cx="200" cy="200" r="176" fill="none" stroke="{accent}" stroke-width="2.5" opacity=".85"/>
  <circle cx="200" cy="200" r="166" fill="none" stroke="rgba(244,246,250,.30)" stroke-width="1"/>
  <circle cx="200" cy="200" r="124" fill="none" stroke="rgba(244,246,250,.14)" stroke-width="1"/>
  <text font-family="Mono, monospace" font-size="21" font-weight="700"
        letter-spacing="4.4" fill="{CHALK}" opacity=".92">
    <textPath href="#arcTop" startOffset="50%" text-anchor="middle">URBAN PLAYGROUND</textPath>
  </text>
  <text font-family="Mono, monospace" font-size="17" font-weight="700"
        letter-spacing="3.4" fill="{accent}" opacity=".95">
    <textPath href="#arcBot" startOffset="50%" text-anchor="middle">AUGUST ATTACK · VOL.6</textPath>
  </text>
  <image href="data:image/png;base64,{emblem_b64}" x="140" y="118" width="120" height="164"
         preserveAspectRatio="xMidYMid meet"/>
</svg>"""


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
    rays = base64.b64encode(burst_rays(p["accent"]).encode()).decode()
    acc = p["accent"]

    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
{faces}
@page {{ size: A4 landscape; margin: 0; }}
*{{margin:0;padding:0;box-sizing:border-box;}}
html,body{{width:297mm;height:210mm;overflow:hidden;}}
body{{
  background:
    radial-gradient(ellipse 150mm 90mm at 50% 30%, #12161F 0%, {COURT_BLACK} 62%),
    {COURT_BLACK};
  font-family:'Archivo',system-ui,sans-serif;
  color:{CHALK};
  -webkit-print-color-adjust:exact; print-color-adjust:exact;
  position:relative; overflow:hidden;
}}
.layer{{position:absolute;inset:0;pointer-events:none;}}

/* Tactical grid — the Vol.6 motif, kept faint so it never fights the type */
.grid{{background-image:
    linear-gradient(rgba(244,246,250,.030) .5px, transparent .5px),
    linear-gradient(90deg, rgba(244,246,250,.030) .5px, transparent .5px);
  background-size:12mm 12mm;}}
/* Scanlines — Vol.6 is the glitch volume. 0.6mm pitch reads as texture in
   print rather than as stripes. */
.scan{{background:repeating-linear-gradient(to bottom,
    rgba(244,246,250,.020) 0 .18mm, transparent .18mm .6mm);}}
/* Speed streaks echoing the wordmark's swoosh, raked to the same angle */
.streaks{{background:
   linear-gradient(103deg, transparent 34%, {acc}0b 34.4%, transparent 35.0%),
   linear-gradient(103deg, transparent 61%, rgba(244,246,250,.028) 61.3%, transparent 61.8%),
   linear-gradient(103deg, transparent 68%, {acc}09 68.3%, transparent 68.9%);}}
.floor{{top:auto;height:78mm;background:linear-gradient(to bottom, rgba(6,7,11,0), {DEEP_BLACK});}}
.vign{{background:radial-gradient(ellipse 175mm 120mm at 50% 45%, transparent 42%, rgba(6,7,11,.55) 100%);}}

/* Burst rays sit behind the placement — the attack motif from aa-burst.svg */
.rays{{position:absolute;width:116mm;height:116mm;left:50%;top:13mm;
  transform:translateX(-50%);opacity:.17;}}
/* Double frame: hairline outer, accent inner, with corner ticks on the inner */
.edge{{position:absolute;inset:6mm;border:.6pt solid rgba(244,246,250,.13);}}
.edge2{{position:absolute;inset:8.6mm;border:.5pt solid rgba(244,246,250,.09);}}
.rule{{position:absolute;top:6mm;left:6mm;right:6mm;height:2.4mm;
  background:linear-gradient(90deg, {acc} 0%, {acc} 62%, rgba(244,246,250,.25) 100%);}}
.rulebot{{position:absolute;bottom:6mm;left:6mm;right:6mm;height:.9mm;
  background:linear-gradient(90deg, rgba(244,246,250,.18) 0%, {acc} 46%, {acc} 100%);}}

.tick{{position:absolute;width:10mm;height:10mm;}}
.tick::before,.tick::after{{content:"";position:absolute;background:{acc};}}
.tick::before{{width:10mm;height:.55mm;}} .tick::after{{width:.55mm;height:10mm;}}
.tl{{left:8.6mm;top:8.6mm;}} .tr{{right:8.6mm;top:8.6mm;}}
.tr::before{{right:0;}} .tr::after{{right:0;}}
.bl{{left:8.6mm;bottom:8.6mm;}} .bl::before{{bottom:0;}} .bl::after{{bottom:0;}}
.br{{right:8.6mm;bottom:8.6mm;}}
.br::before{{right:0;bottom:0;}} .br::after{{right:0;bottom:0;}}

.wrap{{position:relative;height:100%;display:flex;flex-direction:column;
  align-items:center;justify-content:flex-start;padding:17mm 26mm 46mm;text-align:center;}}

.wordmark{{height:22mm;}}
.vol{{font-family:'Mono',monospace;font-weight:700;font-size:8pt;
  letter-spacing:.36em;color:{STEEL};text-transform:uppercase;margin-top:.5mm;}}

/* Kicker flanked by rules — the classic certificate device, drawn in the
   series' own hairline weight rather than a decorative flourish. */
.kickwrap{{display:flex;align-items:center;gap:5mm;margin-top:7.5mm;}}
.kickwrap .ln{{width:26mm;height:.5pt;background:linear-gradient(90deg,transparent,{acc});}}
.kickwrap .ln:last-child{{background:linear-gradient(90deg,{acc},transparent);}}
.kicker{{font-family:'Mono',monospace;font-weight:700;font-size:7.6pt;
  letter-spacing:.44em;color:{acc};white-space:nowrap;}}

.place{{font-family:'Anton',sans-serif;letter-spacing:.045em;line-height:.92;
  font-size:{'66pt' if place == 1 else '58pt'};color:{acc};margin-top:2mm;
  text-shadow:0 0 3mm {acc}55, 0 0 16mm {acc}33;}}

/* Label sits on a plate with chevrons, so it reads as a title rather than a
   second, competing headline. */
.labelrow{{display:flex;align-items:center;gap:4mm;margin-top:2.5mm;}}
.chev{{color:{acc};font-size:9pt;opacity:.8;letter-spacing:-.1em;}}
.label{{font-family:'Archivo',sans-serif;font-weight:900;font-size:11.5pt;
  letter-spacing:.32em;color:{CHALK};text-transform:uppercase;
  padding:2.2mm 7mm;border:.6pt solid rgba(244,246,250,.22);
  background:rgba(244,246,250,.045);}}

.awarded{{font-size:9.5pt;color:{STEEL};margin-top:10.5mm;letter-spacing:.04em;}}

/* Name is left blank deliberately: the series is still running, so these are
   templates the organiser fills in — by hand on the printed card, or by
   typing into the PDF before printing. */
.nameline{{position:relative;width:158mm;margin:6mm auto 0;height:15mm;
  border-bottom:1pt solid rgba(244,246,250,.44);}}
.nameline::before,.nameline::after{{content:"";position:absolute;bottom:-1pt;
  width:.8mm;height:3.4mm;background:{acc};}}
.nameline::before{{left:0;}} .nameline::after{{right:0;}}
.namehint{{font-family:'Mono',monospace;font-size:6.4pt;letter-spacing:.32em;
  color:rgba(139,149,167,.6);margin-top:2mm;text-transform:uppercase;}}

.body{{font-size:9.2pt;color:{STEEL};margin-top:8mm;max-width:172mm;line-height:1.7;}}
.body b{{color:{CHALK};font-weight:800;}}

/* Seal centred at the foot, signatures either side of it */
.sealsvg{{position:absolute;left:50%;bottom:16mm;transform:translateX(-50%);
  width:42mm;height:42mm;}}
.foot{{position:absolute;left:26mm;right:26mm;bottom:20mm;display:flex;
  align-items:flex-end;justify-content:space-between;}}
.sig{{width:74mm;text-align:center;}}
.sigline{{border-bottom:.8pt solid rgba(244,246,250,.36);height:10mm;}}
.sigcap{{font-family:'Mono',monospace;font-size:6.4pt;letter-spacing:.28em;
  color:{STEEL};margin-top:2mm;text-transform:uppercase;}}

/* Issue line — gives the sheet the authority of a numbered document and a
   place to record which certificate went to whom. */
.serial{{position:absolute;left:0;right:0;bottom:9.2mm;text-align:center;
  font-family:'Mono',monospace;font-size:6pt;letter-spacing:.3em;
  color:rgba(139,149,167,.5);text-transform:uppercase;}}
</style></head><body>
<div class="layer grid"></div>
<div class="layer streaks"></div>
<img class="rays" src="data:image/svg+xml;base64,{rays}" alt="">
<div class="layer scan"></div>
<div class="layer vign"></div>
<div class="layer floor"></div>
<div class="edge"></div><div class="edge2"></div>
<div class="rule"></div><div class="rulebot"></div>
<div class="tick tl"></div><div class="tick tr"></div>
<div class="tick bl"></div><div class="tick br"></div>

<div class="wrap">
  <img class="wordmark" src="data:image/png;base64,{wordmark}" alt="August Attack">
  <div class="vol">Urban Playground · Vol.6 · Muscat</div>

  <div class="kickwrap">
    <span class="ln"></span>
    <span class="kicker">CERTIFICATE OF ACHIEVEMENT</span>
    <span class="ln"></span>
  </div>
  <div class="place">{p['ord_']} PLACE</div>
  <div class="labelrow">
    <span class="chev">◆</span>
    <span class="label">{p['label']}</span>
    <span class="chev">◆</span>
  </div>

  <div class="awarded">This certificate is proudly awarded to</div>
  <div class="nameline"></div>
  <div class="namehint">Name</div>

  <div class="body">
    for finishing <b>{p['word']}</b> in the <b>August Attack</b> series at Urban Playground —
    earned across nine sessions of group play and knockouts.
  </div>
</div>

<div class="foot">
  <div class="sig"><div class="sigline"></div><div class="sigcap">Date</div></div>
  <div class="sig"><div class="sigline"></div><div class="sigcap">Tournament Director</div></div>
</div>
{seal(acc, emblem)}
<div class="serial">August Attack · Vol.6 · Muscat, Oman · No. ________</div>
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
