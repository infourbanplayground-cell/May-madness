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
    """The club's profile picture: the emblem in lime, inside a magenta ring.

    Chosen by the owner from twelve. It is the mono treatment — the mark itself
    in the season's colour rather than a device drawn around a white mark — with
    the ring added, so lime leads and magenta frames. That is the reverse of
    every other avatar in this file, and it is why this one does not look like a
    dark circle with a logo in it.

    This is the URBAN PLAYGROUND emblem, not the BO mark: it goes on the club's
    own accounts, which are not a volume's. The season shows in the palette, so
    the next volume is a colour change rather than a new logo.

    The ring sits at r=468 of a 512 radius, inside where a platform draws its own
    border, because every account that matters crops to a circle.
    """
    return avatar_variant2("mono-ring16")


# A touch of pink in the ground, on every avatar.
#
# Two layers, not one: a single radial reads as a smudge in one corner, while a
# strong one opposite a faint one reads as light falling across the thing. The
# magenta sits top-right and the lime answers it bottom-left, which is the same
# arrangement the app and the posts use, so the accounts and the app look lit by
# the same lamp.
#
# It goes UNDER everything a variant draws, so a ring or a court still sits on
# top of it rather than being tinted by it.
PINK_DARK = (
    '<div style="position:absolute;inset:0;background:'
    'radial-gradient(circle at 76% 12%, rgba(255,46,136,.26) 0%, '
    'rgba(255,46,136,.07) 34%, transparent 56%),'
    'radial-gradient(circle at 14% 92%, rgba(198,255,0,.11) 0%, transparent 48%)'
    '"></div>')

# On a lime ground the same idea has to be subtracted rather than added: pink at
# 40% over lime is a muddy olive, so this is a low-alpha wash that warms the
# corner instead of colouring it.
PINK_LIME = (
    '<div style="position:absolute;inset:0;background:'
    'radial-gradient(circle at 82% 90%, rgba(255,46,136,.22) 0%, transparent 54%),'
    'radial-gradient(circle at 18% 10%, rgba(255,255,255,.10) 0%, transparent 44%)'
    '"></div>')


def avatar_variant(style):
    """Alternatives to the club avatar, same rules as the one above.

    All of them are circle-safe, all of them carry the emblem at the same size
    so the set can be judged on treatment rather than on scale, and none of them
    names the volume — the palette does that, so next volume is a colour change
    rather than a new logo.

    On the lime grounds the emblem is driven to solid black with brightness(0)
    rather than swapped for a black file, because no black file exists and a
    second emblem asset is a second thing to keep in step. It takes the orange
    ball with it, which at 48px is a feature: the mark reads as one silhouette.
    """
    w = 1024
    ew = 462.0
    eh = ew * UP_RATIO
    ex, ey = (w - ew) / 2, (w - eh) / 2
    emblem = (f'<div style="position:absolute;left:{ex:.0f}px;top:{ey:.0f}px;'
              f'width:{ew:.0f}px;height:{eh:.0f}px" data-circle="1">'
              f'<img src="data:image/png;base64,{UP_B64}" '
              f'style="width:100%;display:block;%FILTER%"></div>')
    ink = emblem.replace("%FILTER%", "filter:brightness(0)")
    emblem = emblem.replace("%FILTER%", "")

    if style == "solid":
        # Lime ground, emblem punched out in black. The loudest of the set and
        # the one that survives being 24px in a notification.
        body = (f'<div style="position:absolute;inset:0;background:{LIME}"></div>'
                + PINK_LIME +
                f'<div style="position:absolute;left:50%;top:50%;width:916px;height:916px;'
                f'margin:-458px 0 0 -458px;border:5px solid rgba(5,5,5,.30);'
                f'border-radius:50%"></div>'
                + ink +
                f'<div style="position:absolute;left:770px;top:206px;width:46px;height:46px;'
                f'background:{MAGENTA}"></div>')
    elif style == "bars":
        # The Blackout mark's own bars, behind the emblem. The circle crops them
        # into chords, which is what makes it read as Blackout and not as a
        # generic dark avatar.
        bars = "".join(
            f'<div style="position:absolute;left:0;right:0;top:{t}px;height:{h}px;'
            f'background:{LIME};opacity:.92"></div>'
            for t, h in ((812, 18), (862, 30), (926, 46), (992, 32)))
        body = (f'<div style="position:absolute;inset:0;background:{BG}"></div>'
                + PINK_DARK + bars + emblem)
    elif style == "arc":
        # An open ring. The gap gives the mark a direction, which a closed ring
        # cannot, and the magenta cap sits in the gap.
        body = (f'<div style="position:absolute;inset:0;'
                f'background:radial-gradient(circle at 50% 42%, #12140C 0%, {BG} 62%)"></div>'
                + PINK_DARK +
                # Drawn as a dashed SVG circle, not a rotated bordered div: a
                # rotated 936px square has a 1324px diagonal, so its bounding
                # box leaves the canvas and the overflow check fails it even
                # though no ink is anywhere near the edge.
                f'<svg viewBox="0 0 1024 1024" style="position:absolute;inset:0;'
                f'width:1024px;height:1024px">'
                f'<circle cx="512" cy="512" r="461" fill="none" stroke="{LIME}" '
                f'stroke-width="14" stroke-dasharray="2171 724" '
                f'transform="rotate(-118 512 512)"/></svg>'
                + emblem +
                f'<div style="position:absolute;left:836px;top:488px;width:48px;height:48px;'
                f'background:{MAGENTA}"></div>')
    elif style == "duo":
        # Two rings, the club's colour outside and the volume's inside, so the
        # avatar carries the season without carrying its name.
        body = (f'<div style="position:absolute;inset:0;'
                f'background:radial-gradient(circle at 50% 42%, #12140C 0%, {BG} 62%)"></div>'
                + PINK_DARK +
                f'<div style="position:absolute;left:50%;top:50%;width:964px;height:964px;'
                f'margin:-482px 0 0 -482px;border:10px solid {MAGENTA};'
                f'border-radius:50%;opacity:.85"></div>'
                f'<div style="position:absolute;left:50%;top:50%;width:900px;height:900px;'
                f'margin:-450px 0 0 -450px;border:16px solid {LIME};border-radius:50%"></div>'
                + emblem)
    elif style == "band":
        # Half and half. The emblem sits on the dark side; the lime is weight
        # rather than decoration, which is what carries at thumbnail size.
        bw = 372.0
        bh = bw * UP_RATIO
        body = (f'<div style="position:absolute;inset:0;background:{BG}"></div>'
                + PINK_DARK +
                f'<div style="position:absolute;left:0;right:0;top:760px;bottom:0;'
                f'background:{LIME}"></div>'
                f'<div style="position:absolute;left:0;right:0;top:748px;height:8px;'
                f'background:{MAGENTA}"></div>'
                f'<div style="position:absolute;left:{(w-bw)/2:.0f}px;top:148px;'
                f'width:{bw:.0f}px;height:{bh:.0f}px" data-circle="1">'
                f'<img src="data:image/png;base64,{UP_B64}" '
                f'style="width:100%;display:block"></div>')
    else:
        raise ValueError(style)

    return head(w, w) + body + '</body></html>'


def avatar_variant2(style):
    """A second set, pushing past "emblem plus a frame device".

    The first six were all the same idea wearing different jewellery: a mark in
    the middle, something drawn around it. These change what is BEHIND the mark,
    or the mark itself.

    Recolouring uses a CSS mask over a flat fill rather than a filter chain. The
    emblem is white artwork on transparency, so masking by its alpha gives the
    exact brand hex; a filter stack can only ever arrive near it, and 'near the
    brand lime' is not a colour this club has.
    """
    w = 1024
    ew = 462.0
    eh = ew * UP_RATIO
    ex, ey = (w - ew) / 2, (w - eh) / 2
    box = (f'position:absolute;left:{ex:.0f}px;top:{ey:.0f}px;'
           f'width:{ew:.0f}px;height:{eh:.0f}px')
    plain = (f'<div style="{box}" data-circle="1">'
             f'<img src="data:image/png;base64,{UP_B64}" style="width:100%;display:block">'
             f'</div>')

    def masked(colour):
        url = f"url(data:image/png;base64,{UP_B64})"
        return (f'<div style="{box};background:{colour};'
                f'-webkit-mask:{url} center/contain no-repeat;'
                f'mask:{url} center/contain no-repeat" data-circle="1"></div>')

    dark = (f'<div style="position:absolute;inset:0;'
            f'background:radial-gradient(circle at 50% 42%, #12140C 0%, {BG} 62%)"></div>'
            + PINK_DARK)

    if style == "mono":
        # The mark itself in the season's colour. The only one of the set where
        # the logo changes rather than its surroundings — and the orange goes
        # with it, since an alpha mask does not know the artwork had colours.
        body = dark + masked(LIME)
    elif style.startswith("mono-ring"):
        # mono, with the magenta ring the owner asked for. The weight is in the
        # name (mono-ring10 / 16 / 24) because the only real question is how
        # heavy it should be, and that is answered by looking at the three.
        #
        # The ring is the second colour and the mark is the first, which is the
        # opposite of every other avatar here: lime leads, magenta frames. The
        # ring sits at r=468 of a 512 radius so a platform's own border does not
        # eat it, same as everywhere else in this set.
        px = int(style[len("mono-ring"):] or 16)
        d = 936
        body = (dark + masked(LIME) +
                f'<div style="position:absolute;left:50%;top:50%;'
                f'width:{d}px;height:{d}px;margin:{-d//2}px 0 0 {-d//2}px;'
                f'border:{px}px solid {MAGENTA};border-radius:50%"></div>')
    elif style == "halo":
        # Light behind the mark instead of a line around it. Blackout bans soft
        # glows in PRINT, where Chromium tiles them and the seams show; on
        # screen there is no such constraint.
        body = (f'<div style="position:absolute;inset:0;background:{BG}"></div>'
                + PINK_DARK +
                f'<div style="position:absolute;left:50%;top:50%;width:760px;height:760px;'
                f'margin:-380px 0 0 -380px;border-radius:50%;'
                f'background:radial-gradient(circle, rgba(198,255,0,.42) 0%, '
                f'rgba(198,255,0,.10) 48%, transparent 70%)"></div>'
                + plain)
    elif style == "grid":
        # The app's own scanline language, turned into a field.
        body = (f'<div style="position:absolute;inset:0;background:{BG}"></div>'
                + PINK_DARK +
                f'<div style="position:absolute;inset:0;background:'
                f'repeating-linear-gradient(0deg, rgba(198,255,0,.10) 0 2px, transparent 2px 64px),'
                f'repeating-linear-gradient(90deg, rgba(198,255,0,.10) 0 2px, transparent 2px 64px)'
                f'"></div>'
                f'<div style="position:absolute;left:50%;top:50%;width:936px;height:936px;'
                f'margin:-468px 0 0 -468px;border:10px solid {LIME};border-radius:50%"></div>'
                + plain)
    elif style == "court":
        # A padel court, from above, behind the mark. 20x10m at 2:1, with the
        # net and the service lines where they actually are — a club's avatar
        # may as well be about the game.
        cw, chh = 880, 440
        cx0, cy0 = (w - cw) / 2, (w - chh) / 2
        svc = cw * 0.31          # service line, 3.0m from the back of a 10m half
        body = (dark +
                f'<svg viewBox="0 0 {w} {w}" style="position:absolute;inset:0;'
                f'width:{w}px;height:{w}px" opacity=".8">'
                f'<rect x="{cx0:.0f}" y="{cy0:.0f}" width="{cw}" height="{chh}" '
                f'fill="none" stroke="{LIME}" stroke-width="5"/>'
                f'<line x1="{w/2}" y1="{cy0:.0f}" x2="{w/2}" y2="{cy0+chh:.0f}" '
                f'stroke="{MAGENTA}" stroke-width="5"/>'
                f'<line x1="{cx0+svc:.0f}" y1="{cy0:.0f}" x2="{cx0+svc:.0f}" y2="{cy0+chh:.0f}" '
                f'stroke="{LIME}" stroke-width="3"/>'
                f'<line x1="{cx0+cw-svc:.0f}" y1="{cy0:.0f}" x2="{cx0+cw-svc:.0f}" '
                f'y2="{cy0+chh:.0f}" stroke="{LIME}" stroke-width="3"/>'
                f'<line x1="{cx0+svc:.0f}" y1="{w/2}" x2="{cx0+cw-svc:.0f}" y2="{w/2}" '
                f'stroke="{LIME}" stroke-width="3"/>'
                f'</svg>'
                + plain)
    elif style == "wedge":
        # A hard diagonal. The only asymmetric one in either set, which is what
        # makes it findable in a list of round club logos.
        body = (f'<div style="position:absolute;inset:0;background:{BG}"></div>'
                + PINK_DARK +
                f'<div style="position:absolute;inset:0;background:{LIME};'
                f'clip-path:polygon(0 100%, 100% 100%, 100% 64%)"></div>'
                f'<div style="position:absolute;inset:0;background:{MAGENTA};'
                f'clip-path:polygon(0 100%, 100% 62%, 100% 66%, 0 104%)"></div>'
                + plain)
    elif style == "disc":
        # Lime where the mark is, black where it is not: the colour sits behind
        # the artwork rather than around it, so the mark keeps its own weight.
        body = (f'<div style="position:absolute;inset:0;background:{BG}"></div>'
                + PINK_DARK +
                # 840, not 700: a 700px disc cannot carry a 720px-tall mark,
                # and the top of URBAN and the foot of PLAYGROUND fell off it
                # into the black ground and simply vanished.
                f'<div style="position:absolute;left:50%;top:50%;width:840px;height:840px;'
                f'margin:-420px 0 0 -420px;border-radius:50%;background:{LIME}"></div>'
                f'<div style="position:absolute;left:770px;top:206px;width:46px;height:46px;'
                f'background:{MAGENTA}"></div>'
                + masked(BG))
    else:
        raise ValueError(style)

    return head(w, w) + body + '</body></html>'


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
        **{f"blackout-avatar-{v}": avatar_variant(v)
           for v in ("solid", "bars", "arc", "duo", "band")},
        **{f"blackout-avatar-{v}": avatar_variant2(v)
           for v in ("mono", "halo", "grid", "court", "wedge", "disc",
                     "mono-ring10", "mono-ring16", "mono-ring24")},
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
