# -*- coding: utf-8 -*-
"""Blackout Series (Vol.8) brand art.

The files the app and the posts need, all built from the same lockup so they
cannot drift apart:

  blackout-lockup.png   BLACK/OUT wordmark + mark, for the app header and splash
  blackout-stack.png    the same lockup stacked, for the club's front door hero
  blackout-icon.png     512px app icon, lime ground
  blackout-og.png       1200x630 link preview
  blackout-mark.png     the mark alone, raster, for places SVG is awkward
  blackout-whatsapp.png the group photo — laid out for a CIRCULAR crop

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

# The club's own emblem. Its ratio is read off the file rather than assumed:
# the emblems in this repo are different shapes, and a hard-coded one stretches
# whichever it was not written for.
UP_PATH = os.path.join(BRAND, "up-logo-tight.png")
UP_B64 = b64(UP_PATH)
_uw, _uh = __import__("PIL.Image", fromlist=["Image"]).open(UP_PATH).size
UP_RATIO = _uh / _uw


FIT_SCRIPT = r"""<script>
// Shrink-to-fit for display type. An element carrying data-fit="<px>" is
// stepped down until it is no wider than that, so a wordmark can never run off
// its own canvas -- which is exactly how the stacked lockup first shipped with
// the B and the T sliced off.
//
// The renderer calls this AFTER document.fonts.ready rather than letting it run
// on parse: measured in the fallback face the numbers are meaningless, and the
// display face is both italic and at 'wdth' 125, so it is far wider than
// anything the browser would substitute.
window.__fit = function () {
  var out = {};
  document.querySelectorAll('[data-fit]').forEach(function (el, i) {
    var max = parseFloat(el.dataset.fit);
    var fs = parseFloat(getComputedStyle(el).fontSize);
    var guard = 0;
    while (el.getBoundingClientRect().width > max && fs > 8 && guard++ < 500) {
      fs -= 1;
      el.style.fontSize = fs + 'px';
    }
    out[el.className + '#' + i] = Math.round(fs);
  });
  return out;
};
</script>"""


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
</style>{FIT_SCRIPT}</head><body><div class="glow"></div><div class="scan"></div>"""


def lockup():
    """Horizontal lockup: mark, hairline, BLACK/OUT stacked, series line."""
    w, h = 1550, 420
    return head(w, h) + f"""
<div style="position:absolute;inset:0;display:flex;align-items:center;gap:52px;padding:0 70px">
  <img src="data:image/svg+xml;base64,{MARK_B64}" style="width:188px;height:188px;display:block">
  <div style="width:2px;height:206px;background:rgba(255,255,255,.14)"></div>
  <div>
    <div class="d" data-fit="1100" style="display:inline-block;font-size:152px;color:{INK}">BLACK<span style="color:{LIME}">OUT</span></div>
    <div class="k" data-fit="1100" style="display:inline-block;font-size:25px;margin-top:20px">SERIES &middot; URBAN SOCIAL SERIES &middot; VOL.8</div>
  </div>
</div></body></html>"""


def stack():
    """Stacked lockup for the club's front door.

    The horizontal lockup is 3.7:1. The landing page sizes the running volume's
    mark at max-width 430px inside a tall panel, where Surge's 2.1:1 lockup
    stood 202px high; the wide one would stand 117 and read as an afterthought
    in the one place it is the hero. Same parts, stacked.
    """
    w, h = 1100, 620
    return head(w, h) + f"""
<div style="position:absolute;inset:0;display:flex;flex-direction:column;
            align-items:center;justify-content:center;gap:34px">
  <img src="data:image/svg+xml;base64,{MARK_B64}" style="width:150px;height:150px;display:block">
  <div style="text-align:center">
    <div class="d" data-fit="980" style="display:inline-block;font-size:168px;color:{INK}">BLACK<span style="color:{LIME}">OUT</span></div>
    <div class="k" data-fit="980" style="display:inline-block;font-size:26px;margin-top:22px">SERIES &middot; URBAN SOCIAL SERIES &middot; VOL.8</div>
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


def club_avatar():
    """The club's profile picture, in Blackout colours.

    This is the URBAN PLAYGROUND emblem, not the BO mark: it goes on the club's
    own accounts, which are not a volume's. The season shows in the palette —
    lime ring, true black, the magenta tick — so October's accounts look like
    October without the avatar claiming to be the tournament.

    Every platform that matters crops a profile picture to a CIRCLE (Instagram,
    WhatsApp, Facebook, X, YouTube), so the ring sits at r=468 of a 512 radius
    rather than against the edge, where a platform's own border would eat it,
    and the emblem carries data-circle for the renderer to check.

    The emblem is white with the orange ball and stays that way. Recolouring it
    lime would put lime on lime, and the orange is the club's, not a volume's.
    """
    w = 1024
    ew = 462.0
    eh = ew * UP_RATIO
    return head(w, w) + f"""
<div style="position:absolute;inset:0;
     background:radial-gradient(circle at 50% 42%, #12140C 0%, {BG} 62%)"></div>
<div class="glow"></div><div class="scan"></div>
<div style="position:absolute;left:50%;top:50%;width:936px;height:936px;
     margin:-468px 0 0 -468px;border:14px solid {LIME};border-radius:50%"></div>
<div style="position:absolute;left:50%;top:50%;width:856px;height:856px;
     margin:-428px 0 0 -428px;border:3px solid rgba(198,255,0,.22);border-radius:50%"></div>
<div style="position:absolute;left:{(w-ew)/2:.0f}px;top:{(w-eh)/2:.0f}px;
     width:{ew:.0f}px;height:{eh:.0f}px" data-circle="1">
  <img src="data:image/png;base64,{UP_B64}" style="width:100%;display:block">
</div>
<div style="position:absolute;left:770px;top:206px;width:46px;height:46px;
     background:{MAGENTA}"></div>
</body></html>"""


def whatsapp():
    """The WhatsApp group photo.

    NOT the app icon. WhatsApp crops a group photo to a CIRCLE, and the app
    icon is laid out for a rounded square: its BO sits up in the top-left
    corner, which a circle inscribed in that square slices straight through
    (the B's corner is 526px from centre on a 512px radius). The accent square
    loses its corner the same way.

    So: the wordmark is centred and lives well inside the circle, carrying a
    data-circle attribute the renderer checks against the inscribed circle. The
    bars still bleed to the edges — they are meant to be cut, and the curve
    reading across them is what makes the avatar recognisable at the 40px the
    chat list actually draws it at.
    """
    w = 1024
    return head(w, w, LIME) + f"""
<div style="position:absolute;inset:0;background:{LIME}"></div>
<div style="position:absolute;left:0;right:0;top:636px;height:20px;background:{BG}"></div>
<div style="position:absolute;left:0;right:0;top:700px;height:34px;background:{BG}"></div>
<div style="position:absolute;left:0;right:0;top:778px;height:52px;background:{BG}"></div>
<div style="position:absolute;left:0;right:0;top:874px;height:76px;background:{BG}"></div>
<div style="position:absolute;left:700px;top:168px;width:76px;height:76px;background:{MAGENTA}"></div>
<div data-circle="1" class="d" data-fit="560"
     style="position:absolute;left:50%;top:300px;transform:translateX(-50%);
            display:inline-block;font-size:290px;color:{BG};white-space:nowrap">BO</div>
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
        "blackout-stack": stack(),
        "blackout-icon": icon(),
        "blackout-whatsapp": whatsapp(),
        "blackout-club-avatar": club_avatar(),
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
