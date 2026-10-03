# -*- coding: utf-8 -*-
"""Blackout Series Vol.8 — the announcement post.

A three-card carousel at 1080x1350 (Instagram's portrait crop, the largest the
feed will show) plus a 1080x1920 story card for status:

  post-1-hero.png    the volume, the tagline, the dates in one line
  post-2-nights.png  all nine nights as a grid, the finals night lit
  post-3-money.png   what is on the table, and what Vol.7 actually paid
  post-story.png     the whole announcement on one tall card

Every figure is derived, never typed: the nights, entry, voucher and season
prizes come out of blackout-season.json, the pool is computed from its parts the
way the app computes it, and Vol.7's payout is recomputed from the archived
state by the same function the film uses. A post cannot advertise a number the
app contradicts.

  python3 build-announce-post.py
  node render-announce-post.mjs
"""
import base64, datetime, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SP = "/tmp/claude-0/-home-user-May-madness/0e44f0ad-a683-5f0d-9de6-9459ae328963/scratchpad"
FONTS = os.path.join(SP, "video", "fonts")
BRAND = os.path.join(HERE, "brand", "blackout")
OUT = os.path.join(BRAND, "posts")

BG = "#050505"
LIME = "#C6FF00"
MAGENTA = "#FF2E88"
INK = "#F2F2F2"
MUTED = "#9A9A9A"
DIM = "#6E6E6E"

DAYS = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]

# The film already knows how to read Vol.7's payout out of the archive, and two
# implementations of the same sum is how two posts end up disagreeing.
sys.path.insert(0, HERE)
from importlib.machinery import SourceFileLoader
_film = SourceFileLoader("announce_film",
                         os.path.join(HERE, "build-announce-video.py")).load_module()
surge_earnings = _film.surge_earnings


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


MARK_B64 = base64.b64encode(open(os.path.join(BRAND, "blackout-mark.svg")).read()
                            .encode()).decode()


def head(w, h):
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
{faces()}
*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{width:{w}px;height:{h}px;background:{BG};overflow:hidden;
  font-family:'Archivo',sans-serif;color:{INK};-webkit-font-smoothing:antialiased}}
.wash{{position:absolute;inset:0;pointer-events:none;
  background:radial-gradient(circle at 100% 12%, rgba(255,46,136,.16), transparent 46%),
             radial-gradient(circle at 0% 94%, rgba(198,255,0,.10), transparent 44%)}}
.scan{{position:absolute;inset:0;pointer-events:none;
  background:repeating-linear-gradient(0deg, rgba(198,255,0,.045) 0 1px, transparent 1px 5px)}}
.bar{{position:absolute;left:0;right:0;background:{LIME}}}
.d{{font-style:italic;font-variation-settings:'wdth' 125,'wght' 900;line-height:.88;
  letter-spacing:-.5px}}
.k{{font-family:'JetBrains Mono',monospace;font-weight:700;text-transform:uppercase;
  letter-spacing:.28em;color:{LIME}}}
.m{{font-family:'JetBrains Mono',monospace;font-weight:700;letter-spacing:.2em;color:{MUTED}}}
.ctr{{position:absolute;left:0;right:0;text-align:center}}
/* Square corners everywhere — Blackout has no radius. */
.chip{{border:3px solid rgba(242,242,242,.16);background:rgba(255,255,255,.03);
  display:flex;flex-direction:column;align-items:center;justify-content:center}}
.chip .cd{{font-family:'JetBrains Mono',monospace;font-weight:700;font-size:17px;
  letter-spacing:.18em;color:{MUTED}}}
.chip .cn{{font-style:italic;font-variation-settings:'wdth' 125,'wght' 900;
  font-size:56px;line-height:1;margin-top:4px}}
.chip.fin{{border-color:{LIME};background:rgba(198,255,0,.12)}}
.chip.fin .cn,.chip.fin .cd{{color:{LIME}}}
.ern{{display:flex;align-items:center;gap:20px;padding:16px 0;
  border-bottom:3px solid rgba(242,242,242,.10)}}
.ern .pos{{font-family:'JetBrains Mono',monospace;font-weight:700;font-size:26px;
  color:{MUTED};width:40px}}
.ern .who{{flex:1;min-width:0;font-style:italic;
  font-variation-settings:'wdth' 104,'wght' 900;font-size:44px;white-space:nowrap}}
.ern .amt{{font-style:italic;font-variation-settings:'wdth' 104,'wght' 900;
  font-size:48px;color:{LIME};white-space:nowrap}}
.ern .amt small{{font-family:'JetBrains Mono',monospace;font-style:normal;
  font-weight:700;font-size:20px;letter-spacing:.14em;color:{MUTED};margin-left:8px}}
.pill{{display:inline-block;border:3px solid {LIME};color:{LIME};
  font-family:'JetBrains Mono',monospace;font-weight:700;font-size:24px;
  letter-spacing:.2em;padding:14px 26px}}
</style><script>
// Shrink-to-fit: an element carrying data-fit="<px>" is stepped down until it is
// no wider than that. The renderer runs it AFTER document.fonts.ready — measured
// in the fallback face the numbers mean nothing, because the display face is
// italic at 'wdth' 125 and far wider than any substitute.
window.__fit = function () {{
  var out = {{}};
  document.querySelectorAll('[data-fit]').forEach(function (el, i) {{
    var max = parseFloat(el.dataset.fit);
    var fs = parseFloat(getComputedStyle(el).fontSize);
    var guard = 0;
    while (el.getBoundingClientRect().width > max && fs > 8 && guard++ < 500) {{
      fs -= 1;
      el.style.fontSize = fs + 'px';
    }}
    out[(el.id || el.className) + '#' + i] = Math.round(fs);
  }});
  return out;
}};
</script></head><body><div class="wash"></div><div class="scan"></div>"""


def footer(y, host=None):
    """The club, not the URL. Every card already carries the address once, in
    the place it is meant to be read; twice reads as a template."""
    return (f'<div class="m ctr" style="top:{y}px;font-size:22px;color:{DIM}">'
            f'URBAN PLAYGROUND &middot; MUSCAT</div>')


def hero(c, w, h):
    return head(w, h) + f"""
<div class="bar" style="top:0;height:9px"></div>
<div class="bar" style="bottom:0;height:5px"></div>
<div style="position:absolute;left:50%;top:118px;width:128px;height:128px;margin-left:-64px">
  <img src="data:image/svg+xml;base64,{MARK_B64}" style="width:100%;display:block">
</div>
<div class="k ctr" style="top:288px;font-size:22px">URBAN SOCIAL SERIES &middot; VOL.8</div>
<div class="ctr" style="top:348px"><span class="d" data-fit="{w-120}"
     style="display:inline-block;font-size:168px;white-space:nowrap">BLACKOUT</span></div>
<div class="d ctr" style="top:516px;font-size:84px;color:{LIME}">LIGHTS OUT.</div>
<div style="position:absolute;left:50%;top:654px;width:420px;height:5px;
     margin-left:-210px;background:{LIME}"></div>
<div class="d ctr" style="top:712px;font-size:108px">{c['sessions']} NIGHTS</div>
<div class="m ctr" style="top:846px;font-size:26px">ALL {c['monthUpper']} &middot; MON &amp; WED &middot; 5:30 PM</div>
<div class="d ctr" style="top:928px;font-size:96px;color:{LIME}">{c['pool']} OMR</div>
<div class="m ctr" style="top:1046px;font-size:24px">PRIZE POOL &middot; {c['entry']} OMR A NIGHT</div>
<div class="ctr" style="top:1136px">
  <span class="pill">SIGN UP &middot; {c['host'].upper()}</span>
</div>
<div class="m ctr" style="top:1232px;font-size:24px;color:{LIME}">FIRST NIGHT &middot; {c['first']}</div>
{footer(h-66)}
</body></html>"""


def nights_card(c, w, h):
    return head(w, h) + f"""
<div class="bar" style="top:0;height:9px"></div>
<div class="k ctr" style="top:112px;font-size:22px">THE SCHEDULE</div>
<div class="d ctr" style="top:164px;font-size:132px">{c['sessions']} NIGHTS</div>
<div class="m ctr" style="top:322px;font-size:26px">MON &amp; WED &middot; 5:30 PM &middot; ALL {c['monthUpper']}</div>
<div style="position:absolute;left:96px;right:96px;top:440px;display:flex;
     flex-wrap:wrap;gap:20px;justify-content:center">{c['chips']}</div>
<div style="position:absolute;left:50%;top:862px;width:380px;height:5px;
     margin-left:-190px;background:{MAGENTA}"></div>
<div class="d ctr" style="top:916px;font-size:72px">NO FINALS CUT.</div>
<div class="ctr" style="top:1018px;font-size:32px;color:{MUTED}">
  Night {c['sessions']} is open to everyone.</div>
<div class="ctr" style="top:1076px;font-size:32px;color:{MUTED}">
  Season top three on points take it.</div>
<div class="m ctr" style="top:1168px;font-size:24px;color:{LIME}">
  DOUBLE POINTS FROM NIGHT {c['dbl']}</div>
{footer(h-66)}
</body></html>"""


def money_card(c, w, h):
    return head(w, h) + f"""
<div class="bar" style="top:0;height:9px"></div>
<div class="k ctr" style="top:112px;font-size:22px">ON THE TABLE</div>
<div class="ctr" style="top:158px">
  <span class="d" style="font-size:188px;color:{LIME}">{c['pool']}</span>
  <span class="d" style="font-size:76px;color:{LIME}">OMR</span>
</div>
<div class="ctr" style="top:400px;font-size:34px">
  <b style="color:{LIME}">{c['voucher']} OMR</b> to each winner, every night</div>
<div class="ctr" style="top:456px;font-size:34px">
  Season top 3 &middot; <b style="color:{LIME}">{c['prizes']} OMR</b></div>
<div class="ctr" style="top:512px;font-size:34px">
  Entry <b style="color:{LIME}">{c['entry']} OMR</b> a night</div>
<div style="position:absolute;left:150px;right:150px;top:600px;height:3px;
     background:rgba(242,242,242,.14)"></div>
<div class="k ctr" style="top:646px;font-size:20px;color:{MUTED}">LAST SEASON, PAID OUT</div>
<div class="d ctr" style="top:692px;font-size:108px;color:{LIME}">{c['paid']} OMR</div>
<div class="m ctr" style="top:826px;font-size:22px">TOP THREE EARNERS</div>
<div style="position:absolute;left:110px;right:110px;top:878px">{c['earners']}</div>
<div class="ctr" style="top:1160px;font-size:30px;color:{MUTED}">
  Night vouchers plus the season prize.</div>
<div class="m ctr" style="top:1226px;font-size:24px;color:{LIME}">{c['host'].upper()}</div>
{footer(h-66)}
</body></html>"""


def story(c, w, h):
    return head(w, h) + f"""
<div class="bar" style="top:0;height:10px"></div>
<div class="bar" style="bottom:0;height:6px"></div>
<div style="position:absolute;left:50%;top:150px;width:150px;height:150px;margin-left:-75px">
  <img src="data:image/svg+xml;base64,{MARK_B64}" style="width:100%;display:block">
</div>
<div class="k ctr" style="top:346px;font-size:24px">URBAN SOCIAL SERIES &middot; VOL.8</div>
<div class="ctr" style="top:410px"><span class="d" data-fit="{w-110}"
     style="display:inline-block;font-size:196px;white-space:nowrap">BLACKOUT</span></div>
<div class="d ctr" style="top:606px;font-size:96px;color:{LIME}">LIGHTS OUT.</div>
<div style="position:absolute;left:50%;top:762px;width:460px;height:5px;
     margin-left:-230px;background:{LIME}"></div>
<div style="position:absolute;left:96px;right:96px;top:826px;display:flex;
     flex-wrap:wrap;gap:18px;justify-content:center">{c['chips']}</div>
<div class="m ctr" style="top:1300px;font-size:26px">MON &amp; WED &middot; 5:30 PM &middot; ALL {c['monthUpper']}</div>
<div class="d ctr" style="top:1372px;font-size:104px;color:{LIME}">{c['pool']} OMR</div>
<div class="m ctr" style="top:1500px;font-size:24px">PRIZE POOL &middot; {c['entry']} OMR A NIGHT</div>
<div class="ctr" style="top:1586px"><span class="pill">SIGN UP &middot; {c['host'].upper()}</span></div>
<div class="m ctr" style="top:1686px;font-size:24px;color:{LIME}">FIRST NIGHT &middot; {c['first']}</div>
{footer(h-78)}
</body></html>"""


def main():
    cfg = json.load(open(os.path.join(HERE, "blackout-season.json")))
    paid, top = surge_earnings()

    nights = [datetime.date.fromisoformat(d) for d in cfg["nights"]]
    finals = datetime.date.fromisoformat(cfg["finalsDate"])
    assert len(nights) == cfg["sessions"], "the schedule and the session count disagree"

    pool = cfg["voucher"] * 2 * cfg["sessions"] + sum(cfg["seasonPrizes"])

    chips = "".join(
        f'<div class="chip{" fin" if d == finals else ""}" '
        f'style="width:152px;height:152px">'
        f'<span class="cd">{DAYS[d.weekday()]}</span>'
        f'<span class="cn">{d.day}</span></div>'
        for d in nights)

    earners = "".join(
        f'<div class="ern"><span class="pos">{i+1}</span>'
        f'<span class="who">{e["name"].upper()}</span>'
        f'<span class="amt">{e["total"]}<small>OMR</small></span></div>'
        for i, e in enumerate(top))

    c = dict(cfg, pool=pool, paid=paid, chips=chips, earners=earners,
             prizes=" / ".join(str(p) for p in cfg["seasonPrizes"]),
             dbl=cfg["doubleFromSession"],
             first=f"{DAYS[nights[0].weekday()]} {nights[0].day} "
                   f"{cfg['monthUpper'][:3]} &middot; 5:30 PM")

    os.makedirs(OUT, exist_ok=True)
    pages = {
        "post-1-hero": hero(c, 1080, 1350),
        "post-2-nights": nights_card(c, 1080, 1350),
        "post-3-money": money_card(c, 1080, 1350),
        "post-story": story(c, 1080, 1920),
    }
    for name, html in pages.items():
        with open(os.path.join(OUT, name + ".html"), "w") as f:
            f.write(html)
        print(f"built {name}.html")

    print(f"\npool  {pool} OMR  ({cfg['voucher']} x 2 x {cfg['sessions']} "
          f"+ {sum(cfg['seasonPrizes'])})")
    print(f"paid  {paid} OMR last season — "
          + ", ".join(f"{e['name']} {e['total']}" for e in top))
    print(f"first night  {nights[0]}   finals  {finals}")
    print("\nnow render:  node render-announce-post.mjs")


if __name__ == "__main__":
    main()
