# -*- coding: utf-8 -*-
"""Interim brand art for the 56 National Series (Vol.9).

THIS IS NOT THE RE-SKIN. The app still wears Vol.8's black-and-lime skin, and
the red/ivory/arch system in brand/national/handoff/ is a separate pass. What
this fixes is the one thing that could not wait: the deployed app was serving
BLACKOUT's wordmark, with VOL.8 baked into the bitmap, as the first thing a
player sees at national.urbanpadel.om.

It uses the handoff's own assets and tokens rather than inventing a stand-in —
the khanjar tile, the masar band, the flag red, the ivory, and the "56" mark
built the way the handoff specifies it (white fill, ink stroke, an ink offset
and a flag-green offset behind).

NO ARABIC YET, deliberately. The handoff sets the Arabic line in Noto Kufi
Arabic; this container has no Kufi face, and the Arabic that IS installed
(DejaVu, FreeSerif) is not a display face and would ship brand type in a
fallback. The line goes in when ops/vendor-fonts.py carries Noto Kufi, as part
of the re-skin.

  python3 build-national-brand.py && node render-national-brand.mjs
"""
import base64
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "ops"))
from font_bundle import bundle as font_bundle          # noqa: E402

CFG = json.load(open(os.path.join(HERE, "national-season.json")))
P = CFG["palette"]
OUT = os.path.join(HERE, "brand", "national")
HANDOFF = os.path.join(OUT, "handoff", "assets")

# w, h, what
PIECES = {
    "national-lockup": (3100, 840),    # the header wordmark, Vol.8's slot
    "national-mark":   (1024, 1024),   # the "56" on its own
    "national-og":     (1200, 630),    # link preview
    "national-icon":   (512, 512),     # favicon
}


def b64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()


def head(w, h):
    tile = b64(os.path.join(HANDOFF, "khanjar-tile-red.png"))
    band = b64(os.path.join(HANDOFF, "masar-band-white.svg"))
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
{font_bundle()}
*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{width:{w}px;height:{h}px;overflow:hidden;background:{P['bg']};
  font-family:'Archivo',system-ui,sans-serif;-webkit-font-smoothing:antialiased}}
body{{position:relative;display:flex;align-items:center;justify-content:center}}
/* The khanjar tile at 14%, which is the handoff's figure. Any heavier and the
   wordmark stops being the thing you see. */
.tile{{position:absolute;inset:0;opacity:.14;
  background-image:url(data:image/png;base64,{tile});background-size:132px 132px}}
/* The masar band, top and bottom, as the frame. */
.band{{position:absolute;left:0;right:0;height:{max(10, h // 42)}px;
  background:{P['deep']};
  background-image:url("data:image/svg+xml;base64,{band}");
  background-size:auto 100%;background-repeat:repeat-x}}
.band.t{{top:0}} .band.b{{bottom:0}}
.wrap{{position:relative;display:flex;align-items:center;justify-content:center;
  gap:{h // 14}px;padding:0 {h // 12}px;max-width:100%}}
/* The "56" the handoff specifies: white fill, ink stroke, an ink offset and a
   flag-green offset behind it. The green is the flag's and appears nowhere
   else in this volume except National Day. */
.mark{{font-style:italic;font-variation-settings:'wdth' 125,'wght' 900;
  color:#fff;line-height:.84;letter-spacing:-.02em;
  -webkit-text-stroke:{max(1, h // 300)}px {P['ink']};
  paint-order:stroke fill}}
.stack{{display:flex;flex-direction:column;justify-content:center}}
.name{{font-style:italic;font-variation-settings:'wdth' 125,'wght' 900;
  color:{P['ivory']};line-height:.86;text-transform:uppercase;white-space:nowrap}}
.sub{{font-family:'JetBrains Mono',monospace;font-weight:700;color:{P['rose']};
  text-transform:uppercase;white-space:nowrap}}
</style></head><body>
<div class="tile"></div><div class="band t"></div><div class="band b"></div>
"""


def shadow(h):
    """The two offsets behind the 56, scaled to the piece."""
    a = max(2, round(h * 0.0045))
    b = max(4, round(h * 0.009))
    return f"text-shadow:{a}px {a}px 0 {P['ink']},{b}px {b}px 0 {P['green']};"


def lockup(w, h):
    return head(w, h) + f"""
<div class="wrap">
  <span class="mark" style="font-size:{int(h*0.52)}px;{shadow(h)}">56</span>
  <span class="stack" style="gap:{int(h*0.055)}px">
    <span class="name" style="font-size:{int(h*0.30)}px">National Series</span>
    <span class="sub" style="font-size:{int(h*0.075)}px;letter-spacing:.2em">
      Urban Social Series &middot; {CFG['volume']}</span>
  </span>
</div></body></html>"""


def mark(w, h):
    return head(w, h) + f"""
<div class="wrap">
  <span class="mark" style="font-size:{int(h*0.56)}px;{shadow(h)}">56</span>
</div></body></html>"""


def og(w, h):
    return head(w, h) + f"""
<div class="wrap" style="flex-direction:column;gap:{int(h*0.045)}px">
  <span class="mark" style="font-size:{int(h*0.34)}px;{shadow(h)}">56</span>
  <span class="name" style="font-size:{int(h*0.155)}px">National Series</span>
  <span class="sub" style="font-size:{int(h*0.042)}px;letter-spacing:.24em">
    {CFG['monthUpper']} &middot; {CFG['schedule'].upper()} &middot; {CFG['host'].upper()}</span>
</div></body></html>"""


def icon(w, h):
    return head(w, h) + f"""
<div class="wrap">
  <span class="mark" style="font-size:{int(h*0.60)}px;{shadow(h)}">56</span>
</div></body></html>"""


BUILDERS = {"national-lockup": lockup, "national-mark": mark,
            "national-og": og, "national-icon": icon}


def main():
    os.makedirs(OUT, exist_ok=True)
    for name, (w, h) in PIECES.items():
        html = BUILDERS[name](w, h)
        path = os.path.join(OUT, name + ".html")
        with open(path, "w") as f:
            f.write(html)
        print(f"built {name}.html  {w}x{h}")
    print("\nnow render:  node render-national-brand.mjs")


if __name__ == "__main__":
    main()
