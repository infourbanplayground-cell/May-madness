# -*- coding: utf-8 -*-
"""The Blackout palette board — what each colour is for, and what it is not for.

Reads blackout-season.json, so the board cannot show a colour the app does not
have. Contrast ratios are computed, not asserted: the board states where a
colour may carry type and where it may not, and the number is on the board so
nobody has to take it on trust.

  python3 build-blackout-palette.py && node render-blackout-palette.mjs
"""
import base64, json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
SP = "/tmp/claude-0/-home-user-May-madness/0e44f0ad-a683-5f0d-9de6-9459ae328963/scratchpad"
FONTS = os.path.join(SP, "video", "fonts")
BRAND = os.path.join(HERE, "brand", "blackout")

W, H = 1500, 1180


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


def lum(hexs):
    r, g, b = (int(hexs[i:i + 2], 16) / 255 for i in (1, 3, 5))

    def c(u):
        return u / 12.92 if u <= 0.04045 else ((u + 0.055) / 1.055) ** 2.4

    r, g, b = c(r), c(g), c(b)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def ratio(a, b):
    la, lb = lum(a), lum(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def main():
    cfg = json.load(open(os.path.join(HERE, "blackout-season.json")))
    P = cfg["palette"]
    BG = P["bg"]

    # name, hex, what it is for, may it carry small type on the ground
    SWATCHES = [
        ("LIME", P["lime"], "Primary · live · a night in progress"),
        ("LIME PALE", P["limePale"], "Highlights · type on lime fills"),
        ("LIME DEEP", P["limeDeep"], "Fills and tints under type"),
        ("MAGENTA", P["magenta"], "The rare one · double points · the aperture"),
        ("UV", P["uv"], "Structure · waitlist · the night grid"),
        ("UV DEEP", P["uvDeep"], "Plates behind UV · never type"),
        ("INK", P["ink"], "Primary text"),
        ("MUTED", P["muted"], "Done · archived · inactive"),
    ]

    cards = []
    for name, hexv, use in SWATCHES:
        r = ratio(hexv, BG)
        verdict = ("type ok" if r >= 4.5 else
                   "large type only" if r >= 3.0 else "fills only")
        warn = "" if r >= 4.5 else (" warn" if r >= 3.0 else " bad")
        cards.append(
            f'<div class="card">'
            f'<div class="chip" style="background:{hexv}"></div>'
            f'<div class="nm">{name}</div>'
            f'<div class="hx">{hexv.upper()}</div>'
            f'<div class="use">{use}</div>'
            f'<div class="ratio{warn}">{r:.1f}:1 on black &middot; {verdict}</div>'
            f'</div>')

    # The night ramp: nine chips, lime deepening into the season and the
    # double-points nights taking magenta. Colour that is earned by the
    # schedule rather than chosen for decoration.
    n = cfg["sessions"]
    dbl = cfg["doubleFromSession"]
    chips = []
    for i in range(1, n + 1):
        if i >= dbl:
            bg, fg, bd = "rgba(255,46,136,.16)", P["magenta"], P["magenta"]
        else:
            t = (i - 1) / max(1, dbl - 2)
            bg = f"rgba(198,255,0,{0.05 + 0.13 * t:.3f})"
            fg = P["limePale"] if t > 0.5 else P["lime"]
            bd = f"rgba(198,255,0,{0.25 + 0.5 * t:.2f})"
        chips.append(f'<div class="night" style="background:{bg};border-color:{bd};'
                     f'color:{fg}"><span>N{i}</span></div>')

    html = f"""<!doctype html><html><head><meta charset="utf-8"><style>
{faces()}
*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{width:{W}px;height:{H}px;background:{BG};color:{P['ink']};
  font-family:'Archivo',sans-serif;-webkit-font-smoothing:antialiased;overflow:hidden}}
.wash{{position:absolute;inset:0;pointer-events:none;
  background:radial-gradient(circle at 88% 8%, rgba(123,43,255,.22), transparent 46%),
             radial-gradient(circle at 6% 94%, rgba(198,255,0,.10), transparent 44%)}}
.pad{{position:relative;padding:54px 60px}}
.d{{font-style:italic;font-variation-settings:'wdth' 125,'wght' 900;line-height:.9}}
.k{{font-family:'JetBrains Mono',monospace;font-weight:700;letter-spacing:.26em}}
.grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:22px;margin-top:34px}}
.card{{border:3px solid rgba(242,242,242,.10);padding:18px}}
.chip{{height:104px}}
.nm{{font-family:'JetBrains Mono',monospace;font-weight:700;font-size:17px;
  letter-spacing:.18em;margin-top:16px}}
.hx{{font-family:'JetBrains Mono',monospace;font-size:15px;color:{P['muted']};margin-top:5px}}
.use{{font-size:17px;color:{P['ink2']};margin-top:11px;min-height:48px}}
.ratio{{font-family:'JetBrains Mono',monospace;font-size:13px;letter-spacing:.06em;
  color:{P['limePale']};margin-top:8px}}
.ratio.warn{{color:{P['magenta']}}}
.ratio.bad{{color:{P['muted']}}}
.rule{{height:3px;background:rgba(242,242,242,.10);margin:34px 0 26px}}
.nights{{display:flex;gap:14px;margin-top:18px}}
.night{{width:96px;height:78px;border:3px solid;display:flex;align-items:center;
  justify-content:center;font-style:italic;
  font-variation-settings:'wdth' 118,'wght' 900;font-size:30px}}
</style></head><body><div class="wash"></div><div class="pad">

<div class="k" style="font-size:17px;color:{P['uv']}">URBAN SOCIAL SERIES &middot; {cfg['volume']}</div>
<div class="d" style="font-size:66px;margin-top:12px">THE BLACKOUT PALETTE</div>
<div style="font-size:21px;color:{P['ink2']};margin-top:14px;max-width:1000px">
  Lights out plus UV is the room this volume is named after &mdash; and neon
  yellow-green and neon pink are what highlighter pigments do under one.
  Violet is the lamp, not a third neon picked for contrast.</div>

<div class="grid">{''.join(cards)}</div>

<div class="rule"></div>
<div class="k" style="font-size:15px;color:{P['muted']}">THE NIGHT RAMP &mdash; COLOUR EARNED BY THE SCHEDULE</div>
<div class="nights">{''.join(chips)}</div>
<div style="font-size:18px;color:{P['muted']};margin-top:16px">
  Lime deepens across the season; nights {dbl} and {n} take magenta, because
  they are the double-points nights. Nothing here is decorative.</div>
</div></body></html>"""

    out = os.path.join(BRAND, "blackout-palette.html")
    with open(out, "w") as f:
        f.write(html)
    print(f"built blackout-palette.html  {W}x{H}")
    for name, hexv, _ in SWATCHES:
        print(f"  {name:<10} {hexv.upper():<9} {ratio(hexv, BG):5.1f}:1 on {BG}")
    print("\nnow render:  node render-blackout-palette.mjs")


if __name__ == "__main__":
    main()
