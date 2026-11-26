# -*- coding: utf-8 -*-
"""Muscat Heist — the launch posts. Four 1080x1350 feed cards and a 1080x1920 story.

    python3 build-heist-post.py && node ops/render-heist-post.mjs

Written as a heist film's one-sheet rather than in the app's playful voice
(owner, 26 Nov: "it shouldn't look childish"): the owner's own paintings
full-bleed, one condensed uppercase headline in Archivo, credits in mono, and
the logo as the one piece of play on the card. The app's Bowlby/script pairing
stays in the app; a poster that shouts in it reads as a kids' party flyer.

EVERY FIGURE COMES FROM heist-season.json: the nights, the weekdays, the time,
the venue, the entry, the voucher, the season prizes, the double nights, and
the POOL, which is derived (seasonPrizes + voucher x 2 x nights) and never
typed. Episode TITLES are placeholders and are deliberately not printed; the
cards carry the episode number and the date.

Output: brand/heist/posts/*.html (+ PNGs from the renderer) and CAPTIONS.txt.
"""
import base64, datetime, html, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "ops"))
from font_bundle import bundle  # noqa: E402

S = json.load(open(os.path.join(HERE, "heist-season.json")))
OUT = os.path.join(HERE, "brand", "heist", "posts")
os.makedirs(OUT, exist_ok=True)
ART = os.path.join(HERE, "brand", "heist", "art")

NIGHTS = [datetime.date.fromisoformat(d) for d in S["nights"]]
DOUBLE = set(S["doubleNights"])
POOL = sum(S["seasonPrizes"]) + S["voucher"] * 2 * len(NIGHTS)
NIGHTLY = S["voucher"] * 2 * len(NIGHTS)
hh, mm = map(int, S["time"].split(":"))
CLOCK = datetime.time(hh, mm).strftime("%-I:%M %p")
DAYS = " & ".join(sorted({d.strftime("%a") for d in NIGHTS}, key=lambda x: ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"].index(x)))
FIRST = NIGHTS[0].strftime("%a %-d %b")
LAST = NIGHTS[-1].strftime("%a %-d %b")
WORDS = ["zero","one","two","three","four","five","six","seven","eight","nine","ten"]
assert POOL == 412, f"pool derived as {POOL}; the owner set 75/50/35 + 14 x 2 x 9 = 412 on 26 Nov — find out which part moved"


def data_url(path, mime):
    return f"data:{mime};base64," + base64.b64encode(open(path, "rb").read()).decode()


def art(name, w=1600):
    # the 1200px WebP is plenty for a 1080 card and keeps the HTML light
    stem = name[:-4]
    p = os.path.join(ART, f"{stem}-1200.webp")
    return data_url(p, "image/webp") if os.path.exists(p) else data_url(os.path.join(ART, name), "image/jpeg")


LOGO = data_url(os.path.join(HERE, "brand", "heist", "heist-logo.webp"), "image/webp")
EP = S["episodes"]
FONTS = bundle() + "\n" + bundle(os.path.join(HERE, "brand", "heist", "fonts"))

CSS = """
:root{--navy:#0F1B2B;--ink:#07040D;--sand:#F6EAD3;--peach:#FFB36B;--pink:#FF2D78;--orange:#FF7A3D;--gold:#FFC24A;--mist:#D8DEE8;
--line:rgba(246,234,211,.22)}
*{box-sizing:border-box;margin:0;padding:0}
html,body{background:var(--navy)}
.frame{position:relative;width:1080px;overflow:hidden;background:var(--navy);color:var(--sand);font-family:'Archivo',sans-serif}
.feed{height:1350px}.story{height:1920px}
.bg{position:absolute;inset:0;background-size:cover;background-position:var(--pos,center);filter:saturate(1.2) contrast(1.05)}
.shade{position:absolute;inset:0}
.grain{position:absolute;inset:0;opacity:.09;mix-blend-mode:overlay;background-image:url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='160' height='160'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='.9' numOctaves='2' stitchTiles='stitch'/></filter><rect width='160' height='160' filter='url(%23n)'/></svg>")}
.pad{position:absolute;inset:72px}
.story .pad{inset:200px 72px 230px}
.top{display:flex;justify-content:space-between;align-items:flex-start}
.logo{width:300px;height:auto;filter:drop-shadow(0 10px 24px rgba(0,0,0,.55))}
.mono{font-family:'JetBrains Mono',monospace;font-weight:500;text-transform:uppercase;letter-spacing:.16em}
.kick{font-size:24px;color:var(--peach);text-shadow:0 1px 3px rgba(7,4,13,.9),0 0 18px rgba(7,4,13,.8)}
.vol{font-size:22px;color:var(--sand);opacity:.85;text-align:right;line-height:1.6}
.h{font-weight:800;font-stretch:112%;text-transform:uppercase;line-height:.92;letter-spacing:-.005em;white-space:nowrap;color:var(--sand)}
.h em{font-style:normal;color:var(--pink)}
.fitbox{display:block;width:100%}
.rule{height:2px;background:var(--line);margin:28px 0}
.credits{font-size:24px;line-height:1.75;color:var(--mist)}
.credits b{color:var(--sand);font-weight:700}
.foot{position:absolute;left:0;right:0;bottom:0;display:flex;justify-content:space-between;align-items:flex-end}
.url{font-size:24px;color:var(--sand)}
.tag{display:inline-block;padding:8px 14px;border:2px solid var(--sand);font-size:22px;color:var(--sand)}
.tag.hot{border-color:var(--pink);color:var(--pink)}
/* nights grid */
.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}
.cell{position:relative;aspect-ratio:3/2;overflow:hidden;background:#13202F}
.cell .bg{filter:saturate(1.15) brightness(.78)}
.cell .cs{position:absolute;inset:0;background:linear-gradient(180deg,rgba(7,4,13,0) 40%,rgba(7,4,13,.85))}
.cell .lab{position:absolute;left:16px;right:16px;bottom:14px}
.cell .n{font-weight:800;font-stretch:112%;font-size:38px;line-height:1;color:var(--sand)}
.cell .d{font-size:19px;color:var(--mist);margin-top:6px}
.cell .x2{position:absolute;right:12px;top:12px;padding:4px 10px;background:var(--pink);color:var(--ink);font-size:19px;font-weight:700}
.cell.dbl{outline:3px solid var(--pink);outline-offset:-3px}
/* format */
.steps{display:grid;grid-template-columns:repeat(3,1fr);gap:18px}
.step{border-top:3px solid var(--sand);padding-top:18px}
.step .no{font-size:22px;color:var(--peach)}
.step .t{font-weight:800;font-stretch:112%;font-size:46px;line-height:1;text-transform:uppercase;margin:12px 0 10px}
.step p{font-family:'Manrope',sans-serif;font-weight:600;font-size:25px;line-height:1.35;color:var(--mist)}
.tiers{display:grid;grid-template-columns:repeat(4,1fr);gap:14px}
.tier{padding:3px}
.tier>div{background:rgba(7,4,13,.88);padding:18px 14px 16px;height:100%}
.tier .tn{font-weight:800;font-stretch:112%;font-size:30px;line-height:1;text-transform:uppercase}
.tier .tr{font-size:18px;color:var(--mist);margin-top:10px}
.t1{background:linear-gradient(150deg,#FFF6E6,#E8D6B4)}.t2{background:linear-gradient(150deg,#FFC36B,#FF7A3D 55%,#D2357E)}
.t3{background:linear-gradient(150deg,#FF4F8B,#FF2D78 45%,#B0306E)}.t4{background:linear-gradient(150deg,#FFE7A3,#FFC24A 40%,#E89A1F)}
.t1 .tn{color:var(--sand)}.t2 .tn{color:var(--peach)}.t3 .tn{color:#FF4F8B}.t4 .tn{color:var(--gold)}
/* the take */
.big{font-weight:800;font-stretch:112%;font-size:300px;line-height:.84;letter-spacing:-.02em}
.unit{font-size:30px;color:var(--peach)}
.rows{display:grid;gap:0}
.row{display:flex;justify-content:space-between;align-items:baseline;padding:22px 0;border-top:2px solid var(--line)}
.row .l{font-family:'Manrope',sans-serif;font-weight:700;font-size:32px}
.row .l small{display:block;font-weight:600;font-size:23px;color:var(--mist);margin-top:4px}
.row .v{font-weight:800;font-stretch:112%;font-size:60px;white-space:nowrap}
"""


def page(cls, body, title):
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><title>{title}</title>
<style>{FONTS}</style><style>{CSS}</style></head><body>
<div class="frame {cls}" data-card>{body}<div class="grain" aria-hidden="true"></div></div>
<script>
// shrink each headline to fill exactly its box, after the face has loaded
// (the fallback measures narrower than Archivo at width 112, so sizing before
// fonts.ready sizes against the wrong letters)
document.fonts.ready.then(() => {{
  for (const el of document.querySelectorAll('[data-fit]')) {{
    const box = el.parentElement.clientWidth; let fs = +el.dataset.fit; el.style.fontSize = fs + 'px';
    while (el.scrollWidth > box && fs > 20) {{ fs -= 1; el.style.fontSize = fs + 'px'; }}
  }}
  document.body.dataset.ready = '1';
}});
</script></body></html>"""


def head_row(kicker):
    return f"""<div class="top"><img class="logo" src="{LOGO}" alt="Urban Playground Muscat Heist">
<div class="mono vol">{html.escape(S['volumeLabel'])}<br>{html.escape(S['month'][:3].upper())} {S['year']}</div></div>
<div class="mono kick" style="margin-top:26px">{html.escape(kicker)}</div>"""


def foot(right=None):
    r = right or f'<span class="mono tag">Sign-ups open</span>'
    return f'<div class="foot"><span class="mono url">{S["host"]}</span>{r}</div>'


# ── 1 · the hero ─────────────────────────────────────────────────────────
def hero(story=False):
    e = EP[0]
    shade = ("linear-gradient(180deg,rgba(15,27,43,.78) 0%,rgba(15,27,43,.45) 16%,rgba(15,27,43,.05) 30%,rgba(15,27,43,.1) 46%,rgba(15,27,43,.88) 70%,var(--navy) 100%)")
    n = len(NIGHTS)
    body = f"""<div class="bg" style="background-image:url({art(e['art'])});--pos:{e['artPos']}"></div>
<div class="shade" style="background:{shade}"></div>
<div class="pad">{head_row(f"Urban Social Series · {n} nights")}
<div style="position:absolute;left:0;right:0;bottom:{150 if story else 110}px">
<div class="fitbox"><div class="h" data-fit="150">{WORDS[n].title()} nights.</div></div>
<div class="fitbox"><div class="h" data-fit="150"><em>One take.</em></div></div>
<div class="rule"></div>
<div class="mono credits"><b>Every {DAYS}</b> · {CLOCK}<br>{FIRST} → {LAST}<br>{html.escape(S['venue'])}</div>
</div>{foot()}</div>"""
    return page("story" if story else "feed", body, "Muscat Heist")


# ── 2 · the nine nights ──────────────────────────────────────────────────
def nights():
    cells = []
    for i, (d, e) in enumerate(zip(NIGHTS, EP), 1):
        dbl = d.isoformat() in DOUBLE
        cells.append(f"""<div class="cell{' dbl' if dbl else ''}"><div class="bg" style="background-image:url({art(e['art'])});--pos:{e['artPos']}"></div>
<div class="cs"></div>{'<span class="mono x2">2X</span>' if dbl else ''}
<div class="lab"><div class="n">EP.{i:02d}</div><div class="mono d">{d.strftime('%a %-d %b')}</div></div></div>""")
    body = f"""<div class="shade" style="background:radial-gradient(120% 70% at 50% 0%,#24164A 0%,var(--navy) 60%)"></div>
<div class="pad">{head_row("The schedule")}
<div class="fitbox" style="margin-top:18px"><div class="h" data-fit="104">{WORDS[len(NIGHTS)].title()} episodes</div></div>
<div class="grid" style="margin-top:34px">{''.join(cells)}</div>
<div class="mono credits" style="margin-top:26px">{CLOCK} · {html.escape(S['venue'])} · <span style="color:var(--pink)">2X = double points</span></div>
{foot()}</div>"""
    return page("feed", body, "Muscat Heist · the schedule")


# ── 3 · the format ───────────────────────────────────────────────────────
def fmt():
    e = EP[3]
    tiers = [("t1", "The Job", "Quarter-final"), ("t2", "Inside Man", "Semi-final"), ("t3", "Getaway", "Finalist"), ("t4", "The Score", "Champion")]
    tt = "".join(f'<div class="tier {c}"><div><div class="tn">{n}</div><div class="mono tr">{r}</div></div></div>' for c, n, r in tiers)
    body = f"""<div class="bg" style="background-image:url({art(e['art'])});--pos:{e['artPos']}"></div>
<div class="shade" style="background:linear-gradient(180deg,rgba(15,27,43,.8) 0%,rgba(15,27,43,.93) 38%,var(--navy) 70%)"></div>
<div class="pad">{head_row("How a night runs")}
<div class="fitbox" style="margin-top:18px"><div class="h" data-fit="112">Bring a partner.</div></div>
<div class="fitbox"><div class="h" data-fit="112"><em>Leave with the take.</em></div></div>
<div class="steps" style="margin-top:44px">
<div class="step"><div class="mono no">01</div><div class="t">Groups</div><p>Every pair plays its group. Wins and close losses all score.</p></div>
<div class="step"><div class="mono no">02</div><div class="t">Knockout</div><p>The best pairs go through to quarters, semis and a final.</p></div>
<div class="step"><div class="mono no">03</div><div class="t">Champions</div><p>A {S['voucher']} OMR voucher each, and the points that build the season table.</p></div>
</div>
<div class="mono kick" style="margin-top:54px">Reach the knockout · keep the card</div>
<div class="tiers" style="margin-top:18px">{tt}</div>
{foot()}</div>"""
    return page("feed", body, "Muscat Heist · the format")


# ── 4 · the take ─────────────────────────────────────────────────────────
def take():
    e = EP[8]
    p = S["seasonPrizes"]
    body = f"""<div class="bg" style="background-image:url({art(e['art'])});--pos:{e['artPos']}"></div>
<div class="shade" style="background:linear-gradient(180deg,rgba(15,27,43,.72) 0%,rgba(15,27,43,.9) 40%,var(--navy) 66%)"></div>
<div class="pad">{head_row("The take")}
<div style="margin-top:30px"><div class="big">{POOL}</div><div class="mono unit" style="margin-top:14px">OMR prize pool</div></div>
<div class="rows" style="margin-top:54px">
<div class="row"><div class="l">Season champion<small>top of the table after night {len(NIGHTS)}</small></div><div class="v">{p[0]} OMR</div></div>
<div class="row"><div class="l">Second · Third</div><div class="v">{p[1]} · {p[2]}</div></div>
<div class="row"><div class="l">Every night's champions<small>a {S['voucher']} OMR voucher each, {len(NIGHTS)} nights</small></div><div class="v">{NIGHTLY} OMR</div></div>
</div>
{foot(f'<span class="mono tag hot">{S["entry"]} OMR entry</span>')}</div>"""
    return page("feed", body, "Muscat Heist · the take")


CARDS = {"1-hero": hero(), "2-nights": nights(), "3-format": fmt(), "4-take": take(), "story-launch": hero(story=True)}
for k, v in CARDS.items():
    open(os.path.join(OUT, f"{k}.html"), "w").write(v)

p = S["seasonPrizes"]
dbl_days = " and ".join(d.strftime("%a %-d %b") for d in NIGHTS if d.isoformat() in DOUBLE)
CAP = f"""INSTAGRAM (carousel: 1-hero, 2-nights, 3-format, 4-take)
{S['name']}. {WORDS[len(NIGHTS)].title()} nights. One take.

Urban Social Series {S['volumeLabel'].title()} runs every {DAYS} at {CLOCK}, {FIRST} to {LAST}, at {S['venue']}.
Bring a partner. Play your group, make the knockout, win the night.
{S['voucher']} OMR voucher to each of the night's champions. {POOL} OMR in the pool. {S['entry']} OMR entry.
{dbl_days} are double points.

Sign-ups: {S['host']}

WHATSAPP (announcement)
*{S['name'].upper()}*
_Urban Social Series · {S['volumeLabel'].title()} · {S['month']}_

{WORDS[len(NIGHTS)].title()} nights, every {DAYS}, {CLOCK} at {S['venue']}.
First night *{FIRST}*. Last night *{LAST}*.

• Bring a partner. Groups, then a knockout to a final.
• {S['voucher']} OMR voucher to each of the night's champions
• Season top three: {' / '.join(map(str, p))} OMR
• {POOL} OMR in the pool · {S['entry']} OMR entry
• {dbl_days} are double points
• Reach the knockout and you keep a card for the night: The Job, Inside Man, Getaway, The Score

Table, cards and your rank: https://{S['host']}
Sign-up list for night one follows.

_Now loading Muscat._
"""
open(os.path.join(OUT, "CAPTIONS.txt"), "w").write(CAP)
# the claims, against the config they came from
for claim in (f"{POOL} OMR", f"{S['voucher']} OMR voucher", f"{S['entry']} OMR entry", FIRST, LAST):
    assert claim in CAP, claim
print(f"wrote {len(CARDS)} cards + CAPTIONS.txt to {os.path.relpath(OUT, HERE)}  (pool {POOL}, {DAYS} {CLOCK}, doubles {dbl_days})")
