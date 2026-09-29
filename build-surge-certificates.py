# -*- coding: utf-8 -*-
"""September Surge (Vol.7) placement certificates, 1st through 5th.

A4 landscape, print-ready: a 300 DPI PNG for preview and sharing, packed into a
PDF page at exactly 297 x 210mm for the print shop.

This is the Vol.6 certificate re-cut for Vol.7 rather than a new design, the
same way the app inherits its markup volume to volume. What changes is what
DESIGN.md says changes between the two:

  - Palette. Court Black -> Deep Current, Attack Red -> Surge Cyan. Cyan leads;
    Strike Amber is urgency-only and so appears nowhere on a certificate.
  - Display face. Vol.6 stood Anton up tall; Vol.7 is Archivo italic at
    wdth 125 / wght 900, which is what the app and the reels use.
  - Texture. The Vol.6 tactical grid and scanlines give way to Vol.7's
    horizontal surge trace.
  - Motif. The attack burst behind the placement becomes concentric ripple
    rings -- Vol.6's boot was a glitch, a signal cut; Vol.7's is a pulse and
    ripple, a signal sent.

Placement colours use the series ladder (cyan -> light steel -> steel), NOT
gold/silver/bronze. DESIGN.md is explicit that gold is not in this palette, and
the app's medal chips already use this ladder.

Fonts and both brand marks are embedded as base64, so the file renders
identically anywhere with no network and no font substitution at the print shop.

  python3 build-surge-certificates.py                     # all five, blank name line
  python3 build-surge-certificates.py --places 1 2 3
  python3 build-surge-certificates.py --names "Hamed Amri" "Munther Rahbi" ...
"""
import argparse, base64, os

HERE = os.path.dirname(os.path.abspath(__file__))
FONT_BUNDLE = "/tmp/certs/fonts/bundle.css"
BRAND = os.path.join(HERE, "brand", "september-surge")
OUT = os.path.join(HERE, "brand", "certificates-surge")
# Vol.7 closes on session 8. The certificates are dated the night they are
# awarded, not the day they happen to be generated.
FINALE_DATE = "30 September 2026"

# ── Palette (DESIGN.md, Vol.7) ────────────────────────────────────────────
DEEP_CURRENT = "#0A0F14"
VOID         = "#050709"
SURGE_CYAN   = "#00E5FF"
VOLTAGE      = "#F4F9FA"
STEEL_TX     = "#8A9BA8"
DEEP_STEEL   = "#5C6B78"
LIGHT_STEEL  = "#C3D0D8"
# Every field that gets filled in by hand sits on a light plate, because
# black pen on Deep Current is invisible. Not pure white: a hair of warmth
# stops it glaring against the dark field and reads as a label stock.
PLATE        = "#EEF2F4"
PLATE_EDGE   = "#B9C6CE"
INK          = "#0A0F14"

# The ladder: cyan, light steel, steel. 3rd through 5th all sit on the same
# steel and lean on the numeral rather than inventing two more colours the
# series does not have — stepping down to Deep Steel for 4th and 5th was tried
# and printed washed out, which is the wrong thing for a certificate somebody
# keeps. Placement is carried by the numeral and the label, not by fading. The
# sub-label names the honour instead of restating the number, which would just
# read as "3RD PLACE / THIRD PLACE".
PLACES = {
    1: dict(ord_="1ST", word="FIRST",  accent=SURGE_CYAN,  label="SERIES CHAMPION"),
    2: dict(ord_="2ND", word="SECOND", accent=LIGHT_STEEL, label="RUNNER-UP"),
    3: dict(ord_="3RD", word="THIRD",  accent=STEEL_TX,    label="PODIUM FINISH"),
    4: dict(ord_="4TH", word="FOURTH", accent=STEEL_TX,    label="TOP FIVE"),
    5: dict(ord_="5TH", word="FIFTH",  accent=STEEL_TX,    label="TOP FIVE"),
}


def b64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()


def ripple(accent, rings=7, r0=120, step=52):
    """Concentric rings behind the placement — Vol.7's pulse-and-ripple motif.

    Vol.6 put a spiked attack burst here. DESIGN.md changes the boot from a
    glitch (a signal cut) to a pulse (a signal sent), so the certificate echoes
    that: even rings, fading outward, with a brighter inner pair so the numeral
    still sits on something solid.
    """
    parts = []
    for i in range(rings):
        r = r0 + i * step
        o = round(max(0.05, 0.62 - i * 0.085), 3)
        w = 3.2 if i < 2 else 1.6
        parts.append(
            f'<circle cx="500" cy="500" r="{r}" fill="none" '
            f'stroke="{accent}" stroke-opacity="{o}" stroke-width="{w}"/>')
    # a few radial ticks on the outer ring so it reads as a dial, not a target
    for deg in range(0, 360, 30):
        parts.append(
            f'<line x1="500" y1="500" x2="500" y2="{500 - r0 - rings * step}" '
            f'stroke="{accent}" stroke-opacity=".14" stroke-width="1.4" '
            f'transform="rotate({deg} 500 500)"/>')
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 1000" '
            'width="1000" height="1000">' + "".join(parts) + "</svg>")


def seal(accent, emblem_b64):
    return f"""<svg class="sealsvg" viewBox="0 0 400 400" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <path id="arcTop" d="M 60 200 A 140 140 0 0 1 340 200"/>
    <path id="arcBot" d="M 62 200 A 138 138 0 0 0 338 200"/>
  </defs>
  <circle cx="200" cy="200" r="176" fill="none" stroke="{accent}" stroke-width="2.5" opacity=".85"/>
  <circle cx="200" cy="200" r="166" fill="none" stroke="rgba(244,249,250,.30)" stroke-width="1"/>
  <circle cx="200" cy="200" r="124" fill="none" stroke="rgba(244,249,250,.14)" stroke-width="1"/>
  <text font-family="'JetBrains Mono', monospace" font-size="21" font-weight="700"
        letter-spacing="4.4" fill="{VOLTAGE}" opacity=".92">
    <textPath href="#arcTop" startOffset="50%" text-anchor="middle">URBAN PLAYGROUND</textPath>
  </text>
  <text font-family="'JetBrains Mono', monospace" font-size="17" font-weight="700"
        letter-spacing="3.4" fill="{accent}" opacity=".95">
    <textPath href="#arcBot" startOffset="50%" text-anchor="middle">SEPTEMBER SURGE · VOL.7</textPath>
  </text>
  <image href="data:image/png;base64,{emblem_b64}" x="152" y="126" width="96" height="148"
         preserveAspectRatio="xMidYMid meet"/>
</svg>"""


def build_html(place, name=None, date_str=FINALE_DATE):
    p = PLACES[place]
    acc = p["accent"]
    faces = open(FONT_BUNDLE).read()
    wordmark = b64(os.path.join(BRAND, "surge-lockup@1600.png"))
    emblem = b64(os.path.join(BRAND, "up-logo-cyan-2x.png"))
    rings = base64.b64encode(ripple(acc).encode()).decode()

    # A typed name replaces the ruled line; otherwise the line stays blank so
    # the organiser can write it in. Both are deliberate states, not a fallback.
    if name:
        nameblock = ('<div class="plate nameplate">'
                     f'<div class="typed">{name}</div></div>\n'
                     '  <div class="namehint">Name</div>')
    else:
        nameblock = ('<div class="plate nameplate"></div>\n'
                     '  <div class="namehint">Name</div>')

    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
{faces}
@page {{ size: A4 landscape; margin: 0; }}
*{{margin:0;padding:0;box-sizing:border-box;}}
html,body{{width:297mm;height:210mm;overflow:hidden;}}
body{{
  background:
    radial-gradient(ellipse 150mm 92mm at 50% 31%, #111A22 0%, {DEEP_CURRENT} 62%),
    {DEEP_CURRENT};
  font-family:'Archivo',system-ui,sans-serif;
  color:{VOLTAGE};
  -webkit-print-color-adjust:exact; print-color-adjust:exact;
  position:relative; overflow:hidden;
}}
.layer{{position:absolute;inset:0;pointer-events:none;}}

/* Vol.7's page texture: a horizontal surge trace, not Vol.6's tactical grid.
   0.9mm pitch reads as a woven field in print rather than as stripes. */
.trace{{background:repeating-linear-gradient(to bottom,
    rgba(0,229,255,.055) 0 .22mm, transparent .22mm .9mm);}}
/* Three brighter lines, as if one pulse were passing through the field */
.pulse{{background:
   linear-gradient(to bottom, transparent 27.0%, rgba(0,229,255,.10) 27.2%, transparent 27.5%),
   linear-gradient(to bottom, transparent 52.0%, rgba(244,249,250,.05) 52.2%, transparent 52.4%),
   linear-gradient(to bottom, transparent 73.0%, rgba(0,229,255,.08) 73.2%, transparent 73.5%);}}
.floor{{top:auto;height:78mm;background:linear-gradient(to bottom, rgba(5,7,9,0), {VOID});}}
.vign{{background:radial-gradient(ellipse 175mm 120mm at 50% 45%, transparent 42%, rgba(5,7,9,.58) 100%);}}

/* The ripple sits behind the placement */
.rings{{position:absolute;width:118mm;height:118mm;left:50%;top:11mm;
  transform:translateX(-50%);opacity:.20;}}

/* Double frame: hairline outer, fainter inner */
.edge{{position:absolute;inset:6mm;border:.6pt solid rgba(244,249,250,.13);}}
.edge2{{position:absolute;inset:8.6mm;border:.5pt solid rgba(244,249,250,.09);}}
.rule{{position:absolute;top:6mm;left:6mm;right:6mm;height:2.4mm;
  background:linear-gradient(90deg, {acc} 0%, {acc} 62%, rgba(244,249,250,.25) 100%);}}
.rulebot{{position:absolute;bottom:6mm;left:6mm;right:6mm;height:.9mm;
  background:linear-gradient(90deg, rgba(244,249,250,.18) 0%, {acc} 46%, {acc} 100%);}}
/* Vol.7's card marker is a single rising bar rather than Vol.6's four ticks */
.riser{{position:absolute;left:6mm;top:6mm;bottom:6mm;width:1.1mm;
  background:linear-gradient(to top, rgba(0,229,255,0), {acc});}}

.wrap{{position:relative;height:100%;display:flex;flex-direction:column;
  align-items:center;justify-content:flex-start;padding:15mm 26mm 46mm;text-align:center;}}

.wordmark{{height:26mm;}}
.vol{{font-family:'JetBrains Mono',monospace;font-weight:700;font-size:8pt;
  letter-spacing:.36em;color:{STEEL_TX};text-transform:uppercase;margin-top:1.5mm;}}

.kickwrap{{display:flex;align-items:center;gap:5mm;margin-top:6.5mm;}}
.kickwrap .ln{{width:26mm;height:.5pt;background:linear-gradient(90deg,transparent,{acc});}}
.kickwrap .ln:last-child{{background:linear-gradient(90deg,{acc},transparent);}}
.kicker{{font-family:'JetBrains Mono',monospace;font-weight:700;font-size:7.6pt;
  letter-spacing:.44em;color:{acc};white-space:nowrap;}}

/* Vol.7's display face — Archivo italic, widened, not Anton */
.place{{font-family:'Archivo',sans-serif;font-style:italic;
  font-variation-settings:'wdth' 125,'wght' 900;
  letter-spacing:.005em;line-height:.92;
  font-size:62pt;color:{acc};margin-top:2mm;
  text-shadow:0 0 4mm {acc}44, 0 0 18mm {acc}26;}}

.labelrow{{display:flex;align-items:center;gap:4mm;margin-top:2.5mm;}}
.chev{{color:{acc};font-size:9pt;opacity:.8;letter-spacing:-.1em;}}
.label{{font-family:'Archivo',sans-serif;font-weight:900;font-size:11.5pt;
  letter-spacing:.32em;color:{VOLTAGE};text-transform:uppercase;
  padding:2.2mm 7mm;border:.6pt solid rgba(244,249,250,.22);
  background:rgba(244,249,250,.045);}}

.awarded{{font-size:9.5pt;color:{STEEL_TX};margin-top:7mm;letter-spacing:.04em;}}

.plate{{position:relative;background:{PLATE};border:.6pt solid {PLATE_EDGE};}}
/* A cap bar in the placement colour along the top edge. Corner ticks were tried
   first and read as glitches against a light field; a cap makes the plate look
   like a labelled field that belongs to the frame. */
.plate::before{{content:"";position:absolute;left:0;right:0;top:0;height:.9mm;
  background:{acc};}}

/* Sized to be written in, not to dominate: a 16mm band takes a signature
   comfortably while leaving the placement the largest thing on the sheet. */
.nameplate{{width:172mm;height:16mm;margin:5mm auto 0;}}
.namehint{{font-family:'JetBrains Mono',monospace;font-size:6.4pt;letter-spacing:.32em;
  color:rgba(138,155,168,.75);margin-top:2.4mm;text-transform:uppercase;}}

/* A typed name gets the display face at a size that holds a long name on one
   line, with the same ruled underline so printed and handwritten match. */
.nameplate .typed{{position:absolute;inset:0;display:flex;align-items:center;
  justify-content:center;font-style:italic;
  font-variation-settings:'wdth' 112,'wght' 900;
  font-size:21pt;line-height:1;color:{INK};white-space:nowrap;}}

.body{{font-size:9.2pt;color:{STEEL_TX};margin-top:6mm;max-width:164mm;line-height:1.7;}}
.body b{{color:{VOLTAGE};font-weight:800;}}

/* The foot was a date plate and a director plate flanking the seal, and the
   three crowded each other — the director plate ran almost to the frame. The
   date is known, so it is printed; the director box is gone. What is left is a
   single centred stack: seal, then the award date, then the imprint. */
.sealsvg{{position:absolute;left:50%;bottom:28mm;transform:translateX(-50%);
  width:32mm;height:32mm;}}
.issued{{position:absolute;left:0;right:0;bottom:16mm;text-align:center;
  font-family:'JetBrains Mono',monospace;font-weight:700;font-size:7.4pt;
  letter-spacing:.30em;color:{VOLTAGE};text-transform:uppercase;}}
.issued span{{color:{acc};}}

.serial{{position:absolute;left:0;right:0;bottom:9.4mm;text-align:center;
  font-family:'JetBrains Mono',monospace;font-size:6pt;letter-spacing:.3em;
  color:rgba(138,155,168,.55);text-transform:uppercase;}}
</style></head><body>
<div class="layer trace"></div>
<div class="layer pulse"></div>
<img class="rings" src="data:image/svg+xml;base64,{rings}" alt="">
<div class="layer vign"></div>
<div class="layer floor"></div>
<div class="edge"></div><div class="edge2"></div>
<div class="rule"></div><div class="rulebot"></div><div class="riser"></div>

<div class="wrap">
  <img class="wordmark" src="data:image/png;base64,{wordmark}" alt="September Surge">
  <div class="vol">Urban Playground · Vol.7 · Muscat</div>

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
  {nameblock}

  <div class="body">
    for finishing <b>{p['word']}</b> in the <b>September Surge</b> series at Urban Playground —
    earned across eight sessions of group play and knockouts.
  </div>
</div>

{seal(acc, emblem)}
<div class="issued">Awarded <span>{date_str}</span></div>
<div class="serial">September Surge · Vol.7 · Urban Playground · Muscat, Oman</div>
</body></html>"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--places", nargs="*", type=int, default=[1, 2, 3, 4, 5])
    ap.add_argument("--names", nargs="*", default=[],
                    help="Winner names in placement order. Omit for blank name lines.")
    ap.add_argument("--date", default=FINALE_DATE,
                    help=f"Award date printed on the sheet (default: {FINALE_DATE})")
    a = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    for i, place in enumerate(a.places):
        name = a.names[i] if i < len(a.names) else None
        html = build_html(place, name, a.date)
        h = os.path.join(OUT, f"ss-certificate-{place}.html")
        with open(h, "w") as f:
            f.write(html)
        print(f"built {os.path.basename(h)}  ({len(html)/1024:.0f}KB)  {a.date}"
              + (f"  — {name}" if name else "  — blank name line"))
    print("\nnow render:  node render-surge-certificates.mjs")


if __name__ == "__main__":
    main()
