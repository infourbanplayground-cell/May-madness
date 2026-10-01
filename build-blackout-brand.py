# -*- coding: utf-8 -*-
"""Blackout Series (Vol.8) brand art.

Four files the app and the posts need, all built from the same lockup so they
cannot drift apart:

  blackout-lockup.png   BLACK/OUT wordmark + mark, for the app header and splash
  blackout-icon.png     512px app icon, lime ground
  blackout-og.png       1200x630 link preview
  blackout-mark.png     the mark alone, raster, for places SVG is awkward

The wordmark is Archivo italic at 'wdth' 125 / 'wght' 900 — the handoff's display
style. It must be a VARIABLE instance: a static one silently ignores the width
axis and the lockup comes out ~20% too narrow, which is how an earlier volume's
art shipped wrong.

Square corners everywhere. Blackout has no radius except the app icon, which the
OS rounds anyway.

  python3 build-blackout-brand.py && node render-blackout-brand.mjs
"""
import base64, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
SP = "/tmp/claude-0/-home-user-May-madness/0e44f0ad-a683-5f0d-9de6-9459ae328963/scratchpad"
FONTS = os.path.join(SP, "video", "fonts")
BRAND = os.path.join(HERE, "brand", "blackout")
OUT = BRAND

BG = "#050505"
LIME = "#C6FF00"
MAGENTA = "#FF2E88"
INK = "#F2F2F2"
MUTED = "#9A9A9A"


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


MARK = open(os.path.join(BRAND, "blackout-mark.svg")).read()
MARK_B64 = base64.b64encode(MARK.encode()).decode()


def head(w, h, bg=BG):
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
{faces()}
*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{width:{w}px;height:{h}px;background:{bg};overflow:hidden;
  font-family:'Archivo',sans-serif;-webkit-font-smoothing:antialiased}}
.scan{{position:absolute;inset:0;pointer-events:none;
  background:repeating-linear-gradient(0deg, rgba(198,255,0,.045) 0 1px, transparent 1px 5px)}}
.glow{{position:absolute;inset:0;pointer-events:none;
  background:radial-gradient(circle at 100% 18%, rgba(255,46,136,.16), transparent 42%),
             radial-gradient(circle at 0% 92%, rgba(198,255,0,.08), transparent 40%)}}
.d{{font-style:italic;font-variation-settings:'wdth' 125,'wght' 900;line-height:.84;
  letter-spacing:-.5px}}
.k{{font-weight:800;text-transform:uppercase;letter-spacing:.28em;color:{MUTED}}}
</style></head><body><div class="glow"></div><div class="scan"></div>"""


def lockup():
    """Horizontal lockup: mark, hairline, BLACK/OUT stacked, series line."""
    w, h = 1550, 420
    return head(w, h) + f"""
<div style="position:absolute;inset:0;display:flex;align-items:center;gap:52px;padding:0 70px">
  <img src="data:image/svg+xml;base64,{MARK_B64}" style="width:188px;height:188px;display:block">
  <div style="width:2px;height:206px;background:rgba(255,255,255,.14)"></div>
  <div>
    <div class="d" style="font-size:152px;color:{INK}">BLACK<span style="color:{LIME}">OUT</span></div>
    <div class="k" style="font-size:25px;margin-top:20px">SERIES &middot; URBAN SOCIAL SERIES &middot; VOL.8</div>
  </div>
</div></body></html>"""


def icon():
    """App icon: lime ground, the mark's bars, BO set solid black."""
    w = 512
    return head(w, w, LIME) + f"""
<div style="position:absolute;inset:0;background:{LIME}"></div>
<div style="position:absolute;left:0;right:0;top:238px;height:14px;background:{BG}"></div>
<div style="position:absolute;left:0;right:0;top:300px;height:26px;background:{BG}"></div>
<div style="position:absolute;left:0;right:0;top:370px;height:42px;background:{BG}"></div>
<div style="position:absolute;left:0;right:0;top:454px;height:58px;background:{BG}"></div>
<div style="position:absolute;right:62px;top:62px;width:58px;height:58px;background:{MAGENTA}"></div>
<div class="d" style="position:absolute;left:54px;top:74px;font-size:150px;color:{BG}">BO</div>
</body></html>"""


def og():
    w, h = 1200, 630
    return head(w, h) + f"""
<div style="position:absolute;left:0;right:0;top:0;height:7px;background:{LIME}"></div>
<div style="position:absolute;left:64px;top:92px;display:flex;align-items:center;gap:22px">
  <img src="data:image/svg+xml;base64,{MARK_B64}" style="width:62px;height:62px;display:block">
  <div class="k" style="font-size:17px">URBAN SOCIAL SERIES &middot; VOL.8</div>
</div>
<div class="d" style="position:absolute;left:64px;top:206px;font-size:136px;color:{INK}">LIGHTS</div>
<div class="d" style="position:absolute;left:64px;top:330px;font-size:136px;color:{LIME}">OUT.</div>
<div style="position:absolute;left:64px;top:492px;display:flex;gap:46px;align-items:flex-end">
  <div><div class="k" style="font-size:12px">PRIZE POOL</div>
    <div class="d" style="font-size:52px;color:{LIME};margin-top:8px">__POOL__ OMR</div></div>
  <div><div class="k" style="font-size:12px">NIGHTS</div>
    <div class="d" style="font-size:52px;color:{INK};margin-top:8px">9</div></div>
  <div><div class="k" style="font-size:12px">WHEN</div>
    <div class="d" style="font-size:52px;color:{MAGENTA};margin-top:8px">ALL OCTOBER</div></div>
</div>
</body></html>"""


def mark_png():
    return head(512, 512, "#00000000") + f"""
<img src="data:image/svg+xml;base64,{MARK_B64}" style="width:512px;height:512px;display:block">
</body></html>"""


def main():
    os.makedirs(OUT, exist_ok=True)
    # The pool is derived the same way the app derives it, so the art can never
    # advertise a number the app contradicts.
    import json
    cfg = json.load(open(os.path.join(HERE, "blackout-season.json")))
    pool = cfg["voucher"] * 2 * cfg["sessions"] + sum(cfg["seasonPrizes"])
    pages = {
        "blackout-lockup": lockup(),
        "blackout-icon": icon(),
        "blackout-og": og().replace("__POOL__", str(pool)),
        "blackout-mark": mark_png(),
    }
    for name, html in pages.items():
        with open(os.path.join(OUT, name + ".html"), "w") as f:
            f.write(html)
        print(f"built {name}.html")
    print(f"\npool advertised: {pool} OMR  "
          f"({cfg['voucher']} x 2 x {cfg['sessions']} nights + {sum(cfg['seasonPrizes'])} season)")
    print("now render:  node render-blackout-brand.mjs")


if __name__ == "__main__":
    main()
