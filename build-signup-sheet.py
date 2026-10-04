# -*- coding: utf-8 -*-
"""The printable sign-up sheet — A4, for the clipboard at the courts.

The WhatsApp sheet (ops/signup-post.py) is where most people put their name;
this is the one on the wall for whoever turns up without having read the group.
Same numbers, same source, so the two cannot disagree.

  python3 build-signup-sheet.py 1
  node render-signup-sheet.mjs
"""
import base64, datetime, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SP = "/tmp/claude-0/-home-user-May-madness/0e44f0ad-a683-5f0d-9de6-9459ae328963/scratchpad"
FONTS = os.path.join(SP, "video", "fonts")
BRAND = os.path.join(HERE, "brand", "blackout")
OUT = os.path.join(BRAND, "posts")

LIGHT = os.environ.get("LIGHT") == "1"
if LIGHT:
    BG, LIME, MAGENTA, INK, MUTED = "#FFFFFF", "#6E8F00", "#C4005E", "#0A0A0A", "#6E6E6E"
    RULE, WLRULE = "rgba(10,10,10,.38)", "rgba(196,0,94,.5)"
else:
    BG, LIME, MAGENTA, INK, MUTED = "#050505", "#C6FF00", "#FF2E88", "#F2F2F2", "#9A9A9A"
    RULE, WLRULE = "rgba(242,242,242,.30)", "rgba(255,46,136,.55)"
MAX_TEAMS, WL_SIZE = 16, 5


def b64(p):
    with open(p, "rb") as f:
        return base64.b64encode(f.read()).decode()


def faces():
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


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    cfg = json.load(open(os.path.join(HERE, "blackout-season.json")))
    nights = cfg["nights"]
    if not 1 <= n <= len(nights):
        sys.exit(f"night {n} — this volume has {len(nights)}")
    d = datetime.date.fromisoformat(nights[n - 1])
    dbl = n >= cfg["doubleFromSession"]
    # The mark is a lime block carrying black bars and a magenta square, so
    # brightness(0) does not darken it for a white sheet — it floods the whole
    # block black and swallows the bars that make it the mark. It goes on
    # unfiltered; lime on white is a strong enough block to read.
    mark_style = ''
    mark = base64.b64encode(
        open(os.path.join(BRAND, "blackout-mark.svg")).read().encode()).decode()

    rows = "".join(
        f'<div class="row"><span class="num">{i}</span>'
        f'<span class="line"></span><span class="line"></span></div>'
        for i in range(1, MAX_TEAMS + 1))
    wl = "".join(
        f'<div class="row wl"><span class="num">W{i}</span>'
        f'<span class="line"></span><span class="line"></span></div>'
        for i in range(1, WL_SIZE + 1))

    html = f"""<!doctype html><html><head><meta charset="utf-8"><style>
{faces()}
@page {{ size: A4; margin: 0; }}
*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{width:210mm;height:297mm;background:{BG};color:{INK};
  font-family:'Archivo',sans-serif;-webkit-print-color-adjust:exact;print-color-adjust:exact}}
.pad{{padding:10mm 13mm}}
.top{{display:flex;align-items:center;gap:6mm;border-bottom:1.2mm solid {LIME};
  padding-bottom:4mm}}
.top img{{width:16mm;display:block}}
.d{{font-style:italic;font-variation-settings:'wdth' 125,'wght' 900;line-height:.9}}
.k{{font-family:'JetBrains Mono',monospace;font-weight:700;letter-spacing:.22em}}
.meta{{display:flex;gap:8mm;margin:4mm 0 3.5mm}}
.meta div span{{display:block}}
.hdr{{display:flex;gap:4mm;margin-bottom:2mm}}
.hdr span:first-child{{width:12mm}}
.hdr span{{flex:1}}
.row{{display:flex;gap:4mm;align-items:flex-end;margin-bottom:2.6mm}}
.num{{width:12mm;font-family:'JetBrains Mono',monospace;font-weight:700;
  font-size:4.4mm;color:{MUTED};padding-bottom:1mm}}
.line{{flex:1;border-bottom:.4mm solid {RULE};height:6.4mm}}
.row.wl .num{{color:{MAGENTA}}}
.row.wl .line{{border-bottom-color:{WLRULE}}}
.wlhdr{{margin:4mm 0 2.2mm;display:flex;align-items:center;gap:3mm}}
.foot{{position:absolute;left:13mm;right:13mm;bottom:10mm;display:flex;
  justify-content:space-between;align-items:flex-end}}
</style></head><body><div class="pad">

<div class="top">
  <img src="data:image/svg+xml;base64,{mark}" style="{mark_style}">
  <div>
    <div class="k" style="font-size:3mm;color:{LIME}">URBAN SOCIAL SERIES &middot; {cfg['volume']}</div>
    <div class="d" style="font-size:13mm;margin-top:1.5mm">{cfg['name']}</div>
  </div>
  <div style="margin-left:auto;text-align:right">
    <div class="d" style="font-size:9.4mm;color:{LIME};white-space:nowrap">SESSION {n}</div>
    <div class="k" style="font-size:3.4mm;color:{MUTED};margin-top:1.5mm">
      {d.strftime('%a %-d %B').upper()} &middot; 5:30 PM</div>
  </div>
</div>

<div class="meta">
  <div><span class="k" style="font-size:2.6mm;color:{MUTED}">ENTRY</span>
       <span class="d" style="font-size:7mm;margin-top:1mm">{cfg['entry']} OMR</span></div>
  <div><span class="k" style="font-size:2.6mm;color:{MUTED}">EACH WINNER</span>
       <span class="d" style="font-size:7mm;color:{LIME};margin-top:1mm">{cfg['voucher']} OMR</span></div>
  <div><span class="k" style="font-size:2.6mm;color:{MUTED}">TEAMS</span>
       <span class="d" style="font-size:7mm;margin-top:1mm">{MAX_TEAMS} MAX</span></div>
  {'<div><span class="k" style="font-size:2.6mm;color:' + MAGENTA + '">TONIGHT</span>'
   '<span class="d" style="font-size:7mm;color:' + MAGENTA + ';margin-top:1mm">DOUBLE POINTS</span></div>'
   if dbl else ''}
</div>

<div class="hdr k" style="font-size:2.8mm;color:{MUTED}">
  <span>#</span><span>PLAYER</span><span>PARTNER</span></div>
{rows}

<div class="wlhdr">
  <span class="k" style="font-size:3mm;color:{MAGENTA}">WAITLIST</span>
  <span style="flex:1;height:.3mm;background:rgba(255,46,136,.3)"></span>
</div>
{wl}

<div class="foot">
  <div class="k" style="font-size:2.8mm;color:{MUTED}">
    FIRST COME, FIRST SERVED &middot; {cfg['host'].upper()}</div>
  <div class="d" style="font-size:5mm;color:{LIME}">LIGHTS OUT.</div>
</div>
</div></body></html>"""

    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, f"signup-sheet-{n}{'-light' if LIGHT else ''}.html")
    with open(path, "w") as f:
        f.write(html)
    print(f"built {os.path.basename(path)}  "
          f"{d.strftime('%a %-d %b')}, {'double points' if dbl else 'normal'}, "
          f"{MAX_TEAMS} teams + {WL_SIZE} waitlist")
    print("now render:  node render-signup-sheet.mjs")


if __name__ == "__main__":
    main()
