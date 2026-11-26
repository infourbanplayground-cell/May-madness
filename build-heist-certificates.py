# -*- coding: utf-8 -*-
"""Muscat Heist (Vol.10) placement certificates, 1st through 5th — the BLANK set.

A4 landscape, print-ready: a 300 DPI PNG and a PDF page at exactly 297 x 210mm.
Blackout's certificate re-cut in the Heist's poster voice (the launch posts'
voice, not the app's: owner, 26 Nov, "it shouldn't look childish"):

  - Navy ground, the owner's own logo at the head, condensed Archivo caps for
    the placement, credits in mono. The app's Bowlby/script pairing stays in
    the app.
  - The finale's painting (EP.09 The Big Score) rises out of the foot of the
    sheet, faded into the navy — the season's last night is where the
    placements are decided.
  - PLACEMENT IS CARRIED BY THE NUMERAL, THE LABEL AND THE TIER COLOUR, never
    by fading. The colours are the knockout cards' own tiers, so a certificate
    and a card mean the same thing by the same colour: 1st gold (The Score),
    2nd pink (Getaway), 3rd orange (Inside Man), 4th and 5th cream (The Job).
  - NO SOFT GLOWS in print: Chromium tiles big blurred shadows and the seams
    print as hard-edged rectangles (build-blackout-brand.py records it).

WHAT IS CHECKED IN IS THE BLANK SET: a ruled name plate on a light label stock
(pen on navy is invisible), no figures, nothing claimed — the names go on by
hand at the prize-giving on Wed 30 Dec. It never prints a name: the top five is
not a fact until the last night has been played, and a typed name is the one
thing on a certificate that can be wrong.

  python3 build-heist-certificates.py
  node render-heist-certificates.mjs && python3.13 pack-heist-certificate-pdfs.py
"""
import base64, datetime, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "ops"))
from font_bundle import bundle as font_bundle          # noqa: E402

BRAND = os.path.join(HERE, "brand", "heist")
OUT = os.path.join(HERE, "brand", "certificates-heist")
S = json.load(open(os.path.join(HERE, "heist-season.json")))

NAVY, INK, SAND, MIST, PEACH = "#0F1B2B", "#07040D", "#F6EAD3", "#C9D1DE", "#FFB36B"
PLATE, PLATE_EDGE = "#F4EEE2", "#B9B0A0"
GOLD, PINK, ORANGE = "#FFC24A", "#FF4F8B", "#FF8A4C"

PLACES = {
    1: dict(ord_="1ST", word="first",  label="SEASON CHAMPION", tier="THE SCORE",  c=GOLD),
    2: dict(ord_="2ND", word="second", label="RUNNER-UP",       tier="GETAWAY",    c=PINK),
    3: dict(ord_="3RD", word="third",  label="THIRD PLACE",     tier="INSIDE MAN", c=ORANGE),
    4: dict(ord_="4TH", word="fourth", label="TOP FIVE",        tier="THE JOB",    c=SAND),
    5: dict(ord_="5TH", word="fifth",  label="TOP FIVE",        tier="THE JOB",    c=SAND),
}


def b64(path):
    return base64.b64encode(open(path, "rb").read()).decode()


def build_html(place):
    p = PLACES[place]
    c = p["c"]
    nights = len(S["nights"])
    last = datetime.date.fromisoformat(S["finalsDate"])
    date_str = f"{last.day} {last.strftime('%B %Y')}"
    logo = b64(os.path.join(BRAND, "heist-logo.webp"))
    finale = S["episodes"][-1]
    art = b64(os.path.join(BRAND, "art", finale["art"][:-4] + "-1600.webp"))
    prize = S["seasonPrizes"][place - 1] if place <= len(S["seasonPrizes"]) else None
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
{font_bundle()}
@page {{ size: A4 landscape; margin: 0; }}
*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{width:297mm;height:210mm;overflow:hidden}}
body{{background:{NAVY};color:{SAND};font-family:'Archivo',sans-serif;position:relative;
  -webkit-print-color-adjust:exact;print-color-adjust:exact}}
.layer{{position:absolute;inset:0;pointer-events:none}}
/* the finale's painting rises out of the foot, faded into the navy */
.art{{background:url(data:image/webp;base64,{art}) center 62%/cover no-repeat;opacity:.34;
  -webkit-mask-image:linear-gradient(180deg,transparent 30%,#000 82%);mask-image:linear-gradient(180deg,transparent 30%,#000 82%)}}
.shade{{background:linear-gradient(180deg,rgba(7,4,13,.0) 40%,rgba(7,4,13,.55) 100%)}}
.edge{{position:absolute;inset:7mm;border:.6pt solid rgba(246,234,211,.22)}}
.bar{{position:absolute;left:7mm;right:7mm;top:7mm;height:2.4mm;background:{c}}}
.barb{{position:absolute;left:7mm;right:7mm;bottom:7mm;height:.9mm;background:{c}}}
.wrap{{position:relative;height:100%;display:flex;flex-direction:column;align-items:center;
  padding:14mm 26mm 0;text-align:center}}
.logo{{height:30mm;width:auto}}
.mono{{font-family:'JetBrains Mono',monospace;font-weight:700;text-transform:uppercase}}
.vol{{font-size:7.4pt;letter-spacing:.34em;color:{MIST};margin-top:3.2mm}}
.kick{{display:flex;align-items:center;gap:5mm;margin-top:6mm}}
.kick .ln{{width:22mm;height:.7pt;background:{c};opacity:.6}}
.kicker{{font-size:7.4pt;letter-spacing:.40em;color:{c};white-space:nowrap}}
.place{{font-weight:800;font-stretch:112%;font-size:60pt;line-height:.92;letter-spacing:-.005em;
  color:{c};margin-top:1.6mm;white-space:nowrap}}
.label{{margin-top:2.6mm;display:inline-block;padding:2mm 7mm;background:{c};color:{INK};
  font-weight:800;font-stretch:112%;font-size:11pt;letter-spacing:.24em}}
.tier{{font-size:6.6pt;letter-spacing:.30em;color:{MIST};margin-top:2.6mm}}
.tier b{{color:{c}}}
.awarded{{font-size:9pt;color:{MIST};margin-top:7mm;letter-spacing:.04em}}
.plate{{position:relative;width:168mm;height:18mm;margin-top:4.6mm;background:{PLATE};border:.6pt solid {PLATE_EDGE}}}
.plate::before{{content:"";position:absolute;left:0;right:0;top:0;height:.9mm;background:{c}}}
.hint{{font-size:6.2pt;letter-spacing:.30em;color:{MIST};margin-top:2.6mm}}
.body{{font-size:9pt;color:{MIST};margin-top:7mm;max-width:170mm;line-height:1.65}}
.body b{{color:{SAND};font-weight:800}}
.foot{{position:absolute;left:0;right:0;bottom:13mm;text-align:center}}
.issued{{font-size:7.4pt;letter-spacing:.28em;color:{SAND}}}
.issued span{{color:{c}}}
.serial{{font-size:5.8pt;letter-spacing:.28em;color:{MIST};margin-top:2.6mm}}
</style></head><body class="blank">
<div class="layer art"></div><div class="layer shade"></div>
<div class="edge"></div><div class="bar"></div><div class="barb"></div>
<div class="wrap">
  <img class="logo" src="data:image/webp;base64,{logo}" alt="Urban Playground Muscat Heist">
  <div class="mono vol">{S['volumeLabel']} · {S['month']} {S['year']} · {S['venue']}</div>
  <div class="kick"><span class="ln"></span><span class="mono kicker">Certificate of achievement</span><span class="ln"></span></div>
  <div class="place">{p['ord_']} PLACE</div>
  <div><span class="label">{p['label']}</span></div>
  <div class="mono tier">Tier · <b>{p['tier']}</b>{f" · {prize} OMR" if prize else ""}</div>
  <div class="awarded">This certificate is proudly awarded to</div>
  <div class="plate"></div>
  <div class="mono hint">Name</div>
  <div class="body">for finishing <b>{p['word']}</b> in <b>{S['name']}</b> at Urban Playground —
    earned across {nights} nights of group play and knockouts, from {S['episodes'][0]['title']} to {finale['title']}.</div>
</div>
<div class="foot">
  <div class="mono issued">Awarded <span>{date_str}</span></div>
  <div class="mono serial">{S['name']} · {S['volumeLabel']} · Urban Playground · Muscat, Oman</div>
</div>
</body></html>"""


def main():
    os.makedirs(OUT, exist_ok=True)
    assert S["finalsDate"] == S["nights"][-1], "finalsDate is not the last night"
    for place in PLACES:
        h = os.path.join(OUT, f"he-certificate-{place}.html")
        html = build_html(place)
        open(h, "w").write(html)
        print(f"built {os.path.basename(h)}  ({len(html)/1024:.0f}KB)  blank name line")
    print("\nnow render:  node render-heist-certificates.mjs")


if __name__ == "__main__":
    main()
