# -*- coding: utf-8 -*-
"""56 National Series Vol.9 — the announcement posts.

Four 1080x1350 feed cards and one 1080x1920 story:

  post-1-hero.png     the flag mark, the name, the tagline, the dates
  post-2-nights.png   all nine nights with their landmarks, National Day lit
  post-3-format.png   how a night works and how points are scored
  post-4-money.png    the pool broken into the parts it is made of
  post-story.png      the whole announcement on one tall card
  CAPTIONS.txt        the WhatsApp post, the Instagram caption, a sticker plan

WHY THIS IS NOT A FORK OF build-announce-post.py. Vol.8's builder reads its
fonts from a scratchpad directory that a fresh container does not have, and
imports Vol.7's payout out of build-announce-video.py. Both are fine for the
volume they were written in and neither survives a rebuild here. This reads
the repo's own vendored faces through ops/font_bundle.py and takes every
figure from national-season.json.

EVERY NUMBER IS DERIVED. The nights, the entry, the voucher, the season prizes
and the double nights come out of the season file; the pool is computed from
its parts the way the app computes it. A post cannot advertise a figure the
app contradicts — the discipline blackout-season.json established, and the one
the in-app announcement had to be rewritten to honour after it shipped two
volumes advertising the wrong season shape.

THE ART IS THE HANDOFF'S. The khanjar tile, the masar band and the four
landmark silhouettes come from ops/national_assets.py, never an approximation.

  python3 build-national-post.py
  node render-national-post.mjs
"""
import datetime
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "ops"))
from font_bundle import bundle as font_bundle          # noqa: E402
from national_assets import assets as national_assets  # noqa: E402

CFG = json.load(open(os.path.join(HERE, "national-season.json"), encoding="utf-8"))
P = CFG["palette"]
A = national_assets()
AR = {k: v for k, v in CFG["arabic"].items() if k != "_note"}
OUT = os.path.join(HERE, "brand", "national", "posts")

POOL = CFG["voucher"] * 2 * CFG["sessions"] + sum(CFG["seasonPrizes"])
TAG = CFG["tagline"]
NIGHTS = CFG["nights"]
DOUBLES = set(CFG["doubleNights"])
LANDMARKS = CFG["landmarks"]


def night_no(d):
    return NIGHTS.index(d) + 1


def landmark_for(i):
    return LANDMARKS[i % len(LANDMARKS)]


def dt(d):
    y, m, dd = (int(x) for x in d.split("-"))
    return datetime.date(y, m, dd)


def short(d):
    t = dt(d)
    return t.strftime("%a %-d").upper()


def long_date(d):
    return dt(d).strftime("%a %-d %B")


# ── the shell ────────────────────────────────────────────────────────────────
# One place, so four cards cannot drift apart — the lesson build-standings-post
# records after keeping its own copy of build-announce-post's shell.
def logo_url():
    """The club mark, inlined. The foot of every card carries it, and a post
    that fetched it would render without one in a container with no network."""
    import base64
    f = os.path.join(HERE, "brand", "national", "up-logo-national.png")
    with open(f, "rb") as fh:
        return "data:image/png;base64," + base64.b64encode(fh.read()).decode()


LOGO = logo_url()


def chrome(night=None):
    """The header and footer rows every card carries, from the owner's design.

    THE POSTS AND THE SHARE CARDS ARE ONE SET OR THEY ARE NOTHING. Before
    this they shared a palette and nothing else: the cards had a header row
    with the Arabic opposite it and a foot carrying the club mark, the volume
    and the night's landmark, and the posts had a bare `host · URBAN
    PLAYGROUND · OMAN` line. Two things posted the same evening that do not
    look related is the fault worth engineering against, so the chrome is one
    definition used by both.
    """
    lm = landmark_for(night_no(night) - 1) if night else None
    head_r = CFG["nameAr"]
    foot_ar = (lm or {}).get("nameAr", "")
    return (
        f'<div class="chead"><div class="mono chead-l">{CFG["name"]}</div>'
        f'<div class="kufi chead-r">{head_r}</div></div>',
        f'<div class="cfoot"><img class="cmark" src="{LOGO}">'
        f'<div class="cfoot-r"><div class="mono cvol">{CFG["volume"]} &middot; '
        f'{CFG["monthUpper"][:3]} {NIGHTS[0][:4]}</div>'
        + (f'<div class="kufi car">{foot_ar}</div>' if foot_ar else "")
        + '</div></div>')


def shell(w, h, body, pad=72, night=None, head=True):
    head_html, foot_html = chrome(night)
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
{font_bundle()}
*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{width:{w}px;height:{h}px;overflow:hidden;background:{P['bg']};
  font-family:'Archivo',system-ui,sans-serif;-webkit-font-smoothing:antialiased;
  color:{P['ivory']}}}
body{{position:relative}}
/* The ground: the khanjar tile at the app's own 340px, not the handoff's 132.
   A post is looked at on a phone the same way the app is, and the two must
   not drift apart. */
.tile{{position:absolute;inset:0;opacity:.15;pointer-events:none;
  background-image:url("{A['khanjar']}");background-size:340px 340px}}
/* THE MASAR BAND IS INSET AND PILLED, the same trim the share cards carry
   and the same proportions the handoff draws: 24 tall at a 14px side inset
   with a pill radius, which at this scale is 44 inset 56. Run full-bleed it
   stops being a trim and becomes a bar of its own — the mistake this file
   shipped with and CLAUDE.md already records twice elsewhere. */
.band{{position:absolute;left:56px;right:56px;height:44px;border-radius:22px;
  pointer-events:none;overflow:hidden;background-color:{P['deep']};
  background-image:url("{A['masar']}");
  background-size:79px 44px;background-repeat:repeat-x}}
.band.t{{top:40px}} .band.b{{bottom:40px;transform:scaleY(-1)}}
.pad{{position:relative;height:100%;
  /* The chrome is absolutely positioned, so the content box has to be
     told about it: the header runs to pad+64 and the footer occupies
     from pad+22 up to about pad+122 off the foot. */
  padding:{pad + 76}px {pad}px {pad + 106}px;
  display:flex;flex-direction:column}}
/* NO DROP SHADOWS. Depth is the double line and nothing else. */
/* The filled dome, for a card that wants the ivory inversion. */
.arch{{background:{P['ivory']};color:{P['ink']};
  border-radius:50% 50% 28px 28px / 34% 34% 28px 28px;
  box-shadow:0 0 0 7px {P['bg']},0 0 0 11px {P['ivory']};
  overflow:hidden;position:relative}}
/* THE OPEN ARCH — the owner's design: a door drawn as a double ivory outline
   over a deeper ground, holding the subject, with the volume's 56 as a ghost
   behind it and the night's landmark straddling the apex. The share-card
   painter draws exactly this shape; here it can be a real element. */
.archframe{{position:relative;background:{P['deep']};
  border:5px solid {P['ivory']};
  border-radius:50% 50% 30px 30px / 38% 38% 30px 30px;
  overflow:hidden}}
/* The inner line is GREEN. The green on these surfaces has to have an edge:
   as light on a photograph it reads as a smear rather than as a lamp. */
.archframe::after{{content:"";position:absolute;inset:10px;pointer-events:none;
  border:3px solid {P['green']};
  border-radius:50% 50% 22px 22px / 38% 38% 22px 22px}}
.archframe .ghost{{position:absolute;left:0;right:0;bottom:7%;text-align:center;
  font-style:italic;font-variation-settings:'wdth' 125,'wght' 900;
  font-size:360px;line-height:.8;color:rgba(26,10,12,.26);pointer-events:none}}
.archwrap{{position:relative;display:flex;flex-direction:column;flex:1;
  min-height:0}}
/* The medallion sits ON the apex, half in and half out, which is what makes
   the arch read as a door rather than as a rounded box. */
.apex{{position:absolute;top:0;left:50%;transform:translate(-50%,-50%);
  z-index:3}}
.sheet{{background:{P['deep']};border-radius:28px;
  border:1px solid rgba(247,241,230,.18)}}
/* The result plate: ivory, its own masar trim along the top edge. */
.plate{{position:relative;background:{P['ivory']};color:{P['ink']};
  border-radius:42px;overflow:hidden;padding:46px 44px 40px}}
.plate::before{{content:"";position:absolute;top:0;left:0;right:0;height:16px;
  background-color:{P['deep']};background-image:url("{A['masar']}");
  background-size:29px 16px;background-repeat:repeat-x}}
.pill{{border-radius:999px;display:inline-flex;align-items:center;
  justify-content:center}}
.disp{{font-style:italic;font-variation-settings:'wdth' 125,'wght' 900;
  line-height:.88;text-transform:uppercase}}
.mono{{font-family:'JetBrains Mono',monospace;font-weight:700;
  text-transform:uppercase}}
.kufi{{font-family:'Noto Kufi Arabic',sans-serif;font-weight:700}}
/* The flag plaque behind the 56 — the one place white and green appear. */
.flag{{display:inline-flex;align-items:center;justify-content:center;
  border-radius:10px;padding:10px 22px 10px 34px;
  background-image:
    linear-gradient(90deg,{P['flag']} 0 16px,transparent 16px),
    linear-gradient(180deg,#FFFFFF 0 34%,{P['flag']} 34% 66%,{P['green']} 66% 100%);
  box-shadow:0 0 0 3px {P['ink']}}}
.flag .n{{color:#FFFFFF;-webkit-text-stroke:3px {P['ink']};paint-order:stroke fill;
  letter-spacing:-.02em}}
/* The landmark medallion: a disc of the base red with a white silhouette. */
.med{{border-radius:50%;background-color:{P['bg']};background-repeat:no-repeat;
  background-position:center 54%;background-size:62% auto;
  box-shadow:0 0 0 5px {P['ivory']},0 0 0 9px {P['green']};flex:0 0 auto}}
.foot{{margin-top:auto;display:flex;align-items:center;justify-content:space-between;
  gap:20px}}
/* ── the shared chrome ── */
.chead{{position:absolute;left:{pad}px;right:{pad}px;top:{pad + 16}px;
  display:flex;align-items:baseline;justify-content:space-between;gap:24px}}
.chead-l{{font-size:25px;letter-spacing:.26em;color:{P['ivory']}}}
.chead-r{{font-size:30px;color:{P['ivory']}}}
.cfoot{{position:absolute;left:{pad}px;right:{pad}px;bottom:{pad + 8}px;
  display:flex;align-items:flex-end;justify-content:space-between;gap:24px}}
.cmark{{height:64px;width:auto;display:block}}
.cfoot-r{{text-align:right}}
.cvol{{font-size:26px;letter-spacing:.22em;color:{P['ivory']}}}
.car{{font-size:26px;color:{P['rose']};margin-top:8px}}
</style></head><body>
<div class="tile"></div><div class="band t"></div><div class="band b"></div>
{head_html if head else ""}
<div class="pad">{body}</div>
{foot_html}
</body></html>"""


def med(asset, size, ink="white"):
    """A landmark disc.

    THE URL IS UNQUOTED. ops/national_assets.py escapes the SVG's own double
    quotes to single ones so the data URL can live inside a double-quoted
    attribute — which means wrapping it in url('...') closes the string on the
    first attribute in the drawing, and every medallion renders as a plain red
    circle that looks entirely deliberate.
    """
    return (f'<div class="med" style="width:{size}px;height:{size}px;'
            f'background-image:url({A[asset + "@" + ink]})"></div>')


def flag56(size):
    return (f'<span class="flag" style="font-size:{size}px">'
            f'<span class="disp n">56</span></span>')


# The per-card footer is GONE: the shared chrome carries the foot now, and
# for a while both were drawn — the old row sat under the new one and the
# renderer's overlap check caught "Win the final" lying across the host
# line. One definition, used by every card and by the share cards.

# ── 1 · HERO ────────────────────────────────────────────────────────────────
def card_hero(w, h):
    """The owner's composition: the headline, then the door.

    The old hero was a filled ivory dome with everything stacked inside it,
    which is a PANEL — the arch's shape was doing no work. This is the design
    they drew: the name set large on the ground, the open arch below it
    holding the tagline and the dates, the 56 as a ghost inside it, and the
    first night's landmark straddling the apex.
    """
    a, b = [x.strip() for x in TAG.replace("?", ".").split(".") if x.strip()]
    lm = landmark_for(0)
    body = f"""
<div class="disp" style="font-size:100px">56 NATIONAL<br>SERIES</div>
<div class="kufi" style="font-size:36px;margin-top:20px;color:{P['rose']}">
  {AR['series']}</div>
<div class="archwrap" style="margin-top:72px">
  <div class="apex">{med(lm['asset'], 112)}</div>
  <div class="archframe" style="flex:1;display:flex;flex-direction:column;
       align-items:center;justify-content:space-between;gap:30px;
       padding:136px 60px 44px">
    <div class="ghost" aria-hidden="true" data-ghost="1">56</div>
    <div class="disp" style="position:relative;font-size:70px;text-align:center;
         color:{P['ivory']}">{a.upper()}<br>
      <span style="color:{P['rose']}">{b.upper()}</span></div>
    <div class="plate" style="position:relative;width:100%;text-align:center;
         padding:28px 30px 22px">
      <div class="mono" style="font-size:22px;letter-spacing:.22em;
           color:{P['muted']}">{CFG['schedule'].upper().replace(', ', ' &middot; ')}</div>
      <div class="disp" style="font-size:58px;margin-top:12px;color:{P['ink']}">
        ALL {CFG['monthUpper']}</div>
      <div class="mono" style="font-size:24px;letter-spacing:.2em;margin-top:14px;
           color:{P['flag']}">{CFG['sessions']} NIGHTS &middot; {POOL} OMR</div>
    </div>
  </div>
</div>"""
    return shell(w, h, body, night=NIGHTS[0])


# ── 2 · THE NINE NIGHTS ─────────────────────────────────────────────────────
def card_nights(w, h):
    rows = []
    for i, d in enumerate(NIGHTS):
        lm = landmark_for(i)
        nat = d == CFG["nationalDay"]
        dbl = d in DOUBLES
        # NATIONAL DAY IS THE ONLY GREEN. Spend it anywhere else and the night
        # it belongs to stops meaning anything — the handoff's rule, kept.
        bg = P["green"] if nat else P["deep"]
        chip = ""
        if nat:
            chip = (f'<span class="pill mono" style="font-size:17px;padding:6px 13px;'
                    f'letter-spacing:.14em;background:#FFFFFF;color:{P["green"]}">'
                    f'2X &middot; NATIONAL DAY</span>')
        elif dbl:
            chip = (f'<span class="pill mono" style="font-size:17px;padding:6px 13px;'
                    f'letter-spacing:.14em;background:{P["ivory"]};color:{P["bg"]}">'
                    f'2X</span>')
        rows.append(f"""
<div style="display:flex;align-items:center;gap:20px;background:{bg};
     border-radius:999px;padding:9px 22px 9px 9px">
  {med(lm['asset'], 62, 'white')}
  <div style="flex:1;min-width:0">
    <div class="mono" style="font-size:17px;letter-spacing:.14em;white-space:nowrap;
         overflow:hidden;text-overflow:ellipsis;color:{P['rose'] if not nat else '#FFFFFF'}">
      {short(d)} NOV &middot; {lm['nameEn'].upper()}</div>
    <div class="disp" style="font-size:31px;margin-top:3px">SESSION {night_no(d)}</div>
  </div>
  {chip}
</div>""")
    body = f"""
<div class="mono" style="font-size:24px;letter-spacing:.3em;color:{P['rose']}">
  {CFG['sessions']} NIGHTS &middot; {CFG['monthUpper']}</div>
<div class="disp" style="font-size:90px;margin-top:6px">THE SEASON</div>
<div style="display:flex;flex-direction:column;gap:9px;margin-top:20px">
  {''.join(rows)}
</div>"""
    return shell(w, h, body)


# ── 3 · FORMAT ──────────────────────────────────────────────────────────────
def card_format(w, h):
    def line(k, v):
        return (f'<div style="display:flex;justify-content:space-between;'
                f'align-items:baseline;gap:20px;padding:15px 0;'
                f'border-bottom:1px solid rgba(26,10,12,.14)">'
                f'<span style="font-size:29px;font-weight:700">{k}</span>'
                f'<span class="disp" style="font-size:36px;color:{P["bg"]}">{v}</span></div>')
    body = f"""
<div class="mono" style="font-size:24px;letter-spacing:.3em;color:{P['rose']}">
  HOW A NIGHT WORKS</div>
<div class="disp" style="font-size:104px;margin-top:10px">THE<br>FORMAT</div>
<div class="arch" style="margin-top:22px;padding:140px 52px 34px;flex:1">
  <div class="mono" style="font-size:22px;letter-spacing:.2em;color:{P['bg']};
       text-align:center">16 TEAMS &middot; 4 GROUPS OF 4</div>
  <div style="font-size:26px;line-height:1.38;margin-top:14px;text-align:center">
    Group stage, then quarters, semis and a final.<br>
    New partners every night — you are not locked to one player.
  </div>
  <div style="margin-top:18px">
    {line('Group win', '+3')}
    {line('Tiebreak loss', '+2')}
    {line('Competitive loss', '+1')}
    {line('Top of your group', '+1')}
    {line('Reach QF / SF / Final', '+1 / +2 / +3')}
    {line('Win the final', '+5')}
  </div>
  <div style="font-size:22px;margin-top:14px;text-align:center;color:{P['muted']}">
    Points follow <b>you</b>, not your team. Series resets to zero;
    your all-time total carries over.
  </div>
</div>"""
    return shell(w, h, body)


# ── 4 · MONEY ───────────────────────────────────────────────────────────────
def card_money(w, h):
    per_night = CFG["voucher"] * 2
    s1, s2, s3 = CFG["seasonPrizes"]
    body = f"""
<div class="mono" style="font-size:24px;letter-spacing:.3em;color:{P['rose']}">
  WHAT IS ON THE TABLE</div>
<div class="disp" style="font-size:150px;margin-top:10px">{POOL}<br>OMR</div>
<div class="mono" style="font-size:23px;letter-spacing:.2em;color:{P['rose']};
     margin-top:14px">ACROSS THE WHOLE SEASON</div>

<div class="sheet" style="margin-top:40px;padding:34px 36px">
  <div class="mono" style="font-size:21px;letter-spacing:.2em;color:{P['rose']}">
    EVERY NIGHT</div>
  <div style="font-size:33px;margin-top:12px">
    Winners take a <b>{CFG['voucher']} OMR voucher each</b></div>
  <div class="mono" style="font-size:21px;letter-spacing:.14em;color:{P['inactive']};
       margin-top:10px">
    {per_night} OMR &times; {CFG['sessions']} NIGHTS = {per_night * CFG['sessions']} OMR</div>
</div>

<div class="sheet" style="margin-top:16px;padding:34px 36px">
  <div class="mono" style="font-size:21px;letter-spacing:.2em;color:{P['rose']}">
    END OF SEASON</div>
  <div style="display:flex;gap:14px;margin-top:16px">
    {''.join(f'''<div style="flex:1;text-align:center;background:rgba(247,241,230,.09);
         border-radius:28px;padding:22px 10px">
      <div class="mono" style="font-size:20px;letter-spacing:.16em;color:{P['rose']}">{lbl}</div>
      <div class="disp" style="font-size:46px;margin-top:8px">{amt}</div>
      <div class="mono" style="font-size:18px;color:{P['inactive']}">OMR</div>
    </div>''' for lbl, amt in (("1ST", s1), ("2ND", s2), ("3RD", s3)))}
  </div>
</div>

<div class="pill" style="margin-top:16px;background:{P['ivory']};color:{P['ink']};
     padding:22px;font-size:29px;font-weight:800;text-align:center">
  {CFG['entry']} OMR per player, per night</div>
<div style="height:30px"></div>"""
    return shell(w, h, body)


# ── 5 · THE STORY ───────────────────────────────────────────────────────────
def card_story(w, h):
    a, b = [x.strip() for x in TAG.split(".") if x.strip()]
    nat = CFG["nationalDay"]
    # Instagram draws its own chrome over roughly the top 170px and the reply
    # bar over the bottom 200px, so the deep padding is not decoration.
    body = f"""
<div style="height:120px"></div>
<div style="display:flex;flex-direction:column;align-items:center;gap:26px;text-align:center">
  {flag56(96)}
  <div>
    <div class="disp" style="font-size:96px">56 NATIONAL<br>SERIES</div>
    <div class="kufi" style="font-size:32px;margin-top:14px;color:{P['rose']}">
      {AR['series']}</div>
  </div>
  <div class="disp" style="font-size:58px;color:{P['ivory']}">
    {a.upper()}.<br>{b.upper()}.</div>
</div>

<div class="arch" style="margin-top:40px;padding:168px 50px 40px;text-align:center">
  {med('mon-nizwa', 128, 'white')}
  <div class="mono" style="font-size:24px;letter-spacing:.24em;color:{P['bg']};margin-top:24px">
    {CFG['schedule'].upper().replace(', ', ' &middot; ')}</div>
  <div class="disp" style="font-size:64px;margin-top:10px">ALL {CFG['monthUpper']}</div>
  <div style="font-size:27px;margin-top:12px;color:{P['muted']}">
    {CFG['sessions']} nights &middot; {CFG['entry']} OMR a player</div>
  <div class="pill" style="margin-top:26px;background:{P['green']};color:#FFFFFF;
       padding:15px 26px;font-size:24px;font-weight:800">
    {long_date(nat).upper()} &middot; {CFG['nationalDayLabel']}</div>
</div>

<div class="sheet" style="margin-top:22px;padding:34px 38px;text-align:center">
  <div class="mono" style="font-size:22px;letter-spacing:.24em;color:{P['rose']}">
    PRIZE POOL</div>
  <div class="disp" style="font-size:104px;margin-top:8px">{POOL} OMR</div>
</div>

<div style="height:34px"></div>
<div style="height:150px"></div>"""
    return shell(w, h, body, pad=76)


CARDS = {
    "post-1-hero":   (1080, 1350, card_hero),
    "post-2-nights": (1080, 1350, card_nights),
    "post-3-format": (1080, 1350, card_format),
    "post-4-money":  (1080, 1350, card_money),
    "post-story":    (1080, 1920, card_story),
}


def captions():
    nat = CFG["nationalDay"]
    dbl = ", ".join(f"S{night_no(d)}" for d in CFG["doubleNights"])
    return f"""56 NATIONAL SERIES — CAPTIONS
Generated by build-national-post.py. Every figure comes from
national-season.json; do not retype one here.

═══════════════════════════════════════════════════════
WHATSAPP — THE ANNOUNCEMENT
(the app's SESSIONS ▸ ANNOUNCE button writes this same post from the same
 file, so paste either; they cannot disagree)
═══════════════════════════════════════════════════════

🇴🇲 *56 NATIONAL SERIES* — Urban Social Series {CFG['volume']}
_{TAG}_

{CFG['sessions']} nights, all {CFG['month']}. {CFG['schedule']}.
{CFG['entry']} OMR a player. {POOL} OMR across the season.

🏛️ Every night carries an Omani landmark — {', '.join(l['nameEn'] for l in LANDMARKS)}.
🟢 *{long_date(nat)}* is the {CFG['nationalDayLabel']}.
⚡ Double points: {dbl}.

Winners take a {CFG['voucher']} OMR voucher each, every night.
Season: {CFG['seasonPrizes'][0]} / {CFG['seasonPrizes'][1]} / {CFG['seasonPrizes'][2]} OMR.

Series points reset to zero — your all-time total carries over.

📊 https://{CFG['host']}

Drop your name + partner below 👇
⚠️ 16 teams max, first come first served.

═══════════════════════════════════════════════════════
INSTAGRAM — CAROUSEL CAPTION
═══════════════════════════════════════════════════════

{TAG} 🇴🇲

Vol.9 of the Urban Social Series opens {long_date(NIGHTS[0])}.
{CFG['sessions']} nights across {CFG['month']}, {CFG['schedule']}, {POOL} OMR on the table.

Every night carries a landmark. {long_date(nat)} is the {CFG['nationalDayLabel'].lower()} —
double points, and the one night this series wears green.

Link in bio for the live table.

#urbanplayground #padeloman #56nationalseries #oman

═══════════════════════════════════════════════════════
STORY STICKER PLAN
═══════════════════════════════════════════════════════

post-story.png
  • Countdown sticker set to {long_date(NIGHTS[0])}, placed over the arch's
    lower third — NOT over the top 170px (Instagram's own chrome) or the
    bottom 200px (the reply bar). The card already leaves both clear.
  • Link sticker to https://{CFG['host']}
  • Poll: "Playing the national day night?" over the green pill.
"""


def main():
    os.makedirs(OUT, exist_ok=True)
    # THE TAGLINE HAS TO SPLIT, the same assertion the app build makes: the
    # hero sets its two beats on two lines.
    assert len([x for x in TAG.split(".") if x.strip()]) == 2, \
        f"the tagline must be two sentences for the hero: {TAG!r}"
    assert set(CFG["doubleNights"]) <= set(NIGHTS), \
        "a doubleNights date is not in nights"
    for name, (w, h, fn) in CARDS.items():
        path = os.path.join(OUT, name + ".html")
        with open(path, "w", encoding="utf-8") as f:
            f.write(fn(w, h))
        print(f"  {name}.html  {w}x{h}")
    with open(os.path.join(OUT, "CAPTIONS.txt"), "w", encoding="utf-8") as f:
        f.write(captions())
    print(f"  CAPTIONS.txt")
    print(f"\npool {POOL} OMR · {CFG['sessions']} nights · "
          f"{len(DOUBLES)} double · tagline {TAG!r}")
    print("\nnow render:  node render-national-post.mjs")


if __name__ == "__main__":
    main()
