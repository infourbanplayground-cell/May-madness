# -*- coding: utf-8 -*-
"""AUGUST ATTACK — Instagram launch creative.

Emits two formats from one set of facts:
  feed  1080x1350 (4:5)
  story 1080x1920 (9:16), laid out inside the safe area — Instagram
        covers roughly the top 250px and bottom 250px with its own UI,
        so nothing that must be read goes there.

Every fact on this poster was read out of the live app or its state, not
written from memory:
  tagline / subtitle  -> aa_state.json  seasonTagline, seasonSubtitle
  MON & WED · 5:30 PM -> jh-mock-caption in august-attack-index.html
  7 OMR               -> the session-announcement text builder in the app
  238 ranked          -> len(state.players), all 238 carrying prev points
  5 series before it  -> state.prevSeriesNames

Design language per DESIGN.md §2: court black, Attack Red dominant with cyan
as the second voice, Anton display, JetBrains Mono for data, corner ticks
instead of borders, no rounded corners.
"""
import base64, json

SC = '/tmp/claude-0/-home-user-May-madness/0e44f0ad-a683-5f0d-9de6-9459ae328963/scratchpad'
b64f = lambda f: base64.b64encode(open(f'{SC}/{f}', 'rb').read()).decode()

anton   = b64f('anton.woff2')
mono    = b64f('jbmono700.woff2')
arch8   = b64f('archivo800.woff2')
arch6   = b64f('archivo600.woff2')
word    = b64f('aa-wordmark-clean.png')
emblem  = b64f('aa-emblem.png')

st = json.load(open(f'{SC}/aa_state.json'))
RANKED   = len(st['players'])
PREV     = len(st.get('prevSeriesNames') or [])
TAGLINE  = st.get('seasonTagline', 'Serve First. Strike Hard.')
SUBTITLE = st.get('seasonSubtitle', 'URBAN SOCIAL SERIES · VOL. 6')
LINEAGE  = ' · '.join((st.get('prevSeriesNames') or []))
# Prize figures come from the prize panel the live app already renders on the
# August dashboard — "402 OMR / PRIZE POOL UP FOR GRABS" + the 2X chip. Already
# public, so the post can't contradict the site.
# What the thing actually is, for anyone who's never come to one. The feed
# post is tight on space, so it gets the short read; the story has room for
# the fuller one.
ABOUT = [
 "A <b>social</b> padel series &mdash; not a closed league.",
 "New partners every session, so you meet the whole community.",
 "Everyone gets ranked, first night or fiftieth. Real competition, no egos.",
]

POOL     = '402'
BONUS    = 'SESSIONS 8 &amp; 9 PAY DOUBLE'

# H = canvas height, PAD = (top, bottom) padding that keeps content clear of
# Instagram's chrome, WORD = wordmark width, TAG = tagline size, BIG = the
# MON & WED size, STAT = stat number size
FORMATS = {
    'feed':  dict(H=1350, PAD=(84, 84), WORD=560, TAG=41, BIG=47, STAT=37, LIN=1,
                  GAP=17, URL=34, EMB=104, POOLSZ=98, ABOUT=19, LINE=1.62,
                  out='august-attack-launch'),
    'story': dict(H=1920, PAD=(250, 250), WORD=676, TAG=52, BIG=64, STAT=50, LIN=0,
                  GAP=26, URL=38, EMB=116, POOLSZ=126, ABOUT=22, LINE=1.55,
                  out='august-attack-story'),
}

RED   = '#FF2E43'
ICE   = '#3DE1FF'
CHALK = '#F4F6FA'
STEEL = '#8B95A7'
COURT = '#0A0C12'

def build(fmt, anim=False):
  F = FORMATS[fmt]
  LINEAGE_HTML = (f'<div class="lineage"><div class="ln"><em>VOL.{PREV+1}</em>'
                  f'&nbsp;&middot;&nbsp; {LINEAGE.upper().replace(" · ", " &middot; ")}'
                  f'</div></div>') if F["LIN"] else ''
  H, (PT, PB) = F["H"], F["PAD"]
  CSS = f"""
@font-face{{font-family:'Anton';src:url(data:font/woff2;base64,{anton}) format('woff2');font-display:block}}
@font-face{{font-family:'Mono';font-weight:700;src:url(data:font/woff2;base64,{mono}) format('woff2')}}
@font-face{{font-family:'Archivo';font-weight:800;src:url(data:font/woff2;base64,{arch8}) format('woff2')}}
@font-face{{font-family:'Archivo';font-weight:600;src:url(data:font/woff2;base64,{arch6}) format('woff2')}}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{width:1080px;height:{H}px;overflow:hidden;position:relative;background:
  radial-gradient(ellipse 92% 46% at 50% 4%, rgba(255,46,67,.26), transparent 62%),
  radial-gradient(ellipse 62% 34% at 6% 66%, rgba(61,225,255,.11), transparent 64%),
  linear-gradient(180deg,#08090D 0%,{COURT} 52%,#06070B 100%);
  font-family:Archivo,sans-serif;color:{CHALK}}}

/* tactical grid — DESIGN.md motif, 46px cell */
.grid{{position:absolute;inset:0;z-index:0;opacity:.55;
  background-image:linear-gradient(rgba(255,46,67,.055) 1px,transparent 1px),
    linear-gradient(90deg,rgba(255,46,67,.055) 1px,transparent 1px);
  background-size:46px 46px;
  -webkit-mask-image:radial-gradient(118% 76% at 50% 26%,#000,transparent 86%)}}
.scan{{position:absolute;inset:-6px 0;z-index:6;pointer-events:none;
  background:repeating-linear-gradient(0deg,rgba(0,0,0,.17) 0 1px,transparent 1px 3px)}}

/* corner ticks frame the canvas: cyan opens, red closes */
.tk{{position:absolute;width:74px;height:74px;z-index:5}}
.tk.tl{{top:44px;left:44px;border-top:5px solid {ICE};border-left:5px solid {ICE}}}
.tk.tr{{top:44px;right:44px;border-top:5px solid {RED};border-right:5px solid {RED}}}
.tk.bl{{bottom:44px;left:44px;border-bottom:5px solid {RED};border-left:5px solid {ICE}}}
.tk.br{{bottom:44px;right:44px;border-bottom:5px solid {RED};border-right:5px solid {RED}}}

.z{{position:relative;z-index:4;height:100%;display:flex;flex-direction:column;
  align-items:center;padding:{PT}px 84px {PB}px}}

.kick{{display:inline-flex;align-items:center;gap:13px;font-weight:800;font-size:17px;
  letter-spacing:.34em;color:{STEEL};text-transform:uppercase}}
.kick i{{display:block;width:4px;height:17px;background:{RED};box-shadow:0 0 9px {RED}}}

.word{{width:{F["WORD"]}px;margin-top:26px;filter:drop-shadow(0 0 34px rgba(255,46,67,.42))}}

.rule{{width:100%;height:2px;margin:24px 0 0;
  background:linear-gradient(90deg,transparent,{RED} 18%,{RED} 46%,{ICE} 54%,{ICE} 82%,transparent)}}

/* chromatic split: red left, cyan right — the glitch signature */
.tag{{margin-top:{F["GAP"]}px;font-family:Anton;font-size:{F["TAG"]}px;letter-spacing:.035em;line-height:1;
  text-align:center;text-shadow:-3px 0 {RED},3px 0 {ICE},0 0 40px rgba(255,46,67,.4)}}
.tag b{{color:{RED};font-weight:400;text-shadow:0 0 26px rgba(255,46,67,.75)}}

/* the explainer — plain language, deliberately the quietest type on the
   poster: it's for the person who hasn't been before, and it shouldn't
   compete with the wordmark or the pool */
.about{{margin-top:{F["GAP"]}px;margin-bottom:auto;max-width:940px;text-align:center;
  font-family:Archivo;font-weight:600;font-size:{F["ABOUT"]}px;line-height:{F["LINE"]};
  text-wrap:balance;
  letter-spacing:.005em;color:{STEEL}}}
.about b{{color:{CHALK};font-weight:800}}

/* series lineage — five volumes of receipts, and the name to beat */
.lineage{{margin-top:{F["GAP"]}px;width:100%;text-align:center}}
.lineage .ln{{font-family:Mono;font-weight:700;font-size:13px;letter-spacing:.09em;
  white-space:nowrap;
  color:{STEEL};line-height:1.85}}
.lineage .ln em{{font-style:normal;color:{ICE}}}
/* prize hero — after the wordmark, this is the loudest thing on the poster */
.prize{{display:flex;align-items:center;justify-content:center;gap:30px;width:100%;
  margin-top:{F['GAP']}px;margin-bottom:16px;padding:22px 30px 20px;background:rgba(16,20,32,.94);
  background-image:
    linear-gradient({ICE},{ICE}),linear-gradient({ICE},{ICE}),
    linear-gradient({RED},{RED}),linear-gradient({RED},{RED});
  background-size:34px 3px,3px 34px,34px 3px,3px 34px;
  background-position:0 0,0 0,100% 100%,100% 100%;background-repeat:no-repeat;
  box-shadow:0 0 62px rgba(255,46,67,.24)}}
.prize .amt{{font-family:Anton;font-size:{F["POOLSZ"]}px;line-height:.84;color:{RED};
  letter-spacing:.01em;text-shadow:0 0 46px rgba(255,46,67,.85)}}
.prize .amt sub{{display:block;font-size:.27em;letter-spacing:.22em;color:{CHALK};
  vertical-align:baseline;margin-top:9px;text-shadow:none}}
.prize .txt{{text-align:left}}
.prize .txt .t{{font-family:Anton;font-size:{int(F["POOLSZ"]*.35)}px;line-height:1.02;
  letter-spacing:.02em;color:{CHALK}}}
.prize .txt .c{{display:inline-block;margin-top:12px;padding:8px 14px 7px;
  font-family:Mono;font-weight:700;font-size:{int(F["POOLSZ"]*.115)}px;letter-spacing:.16em;
  color:{ICE};background:rgba(61,225,255,.10);box-shadow:inset 0 0 0 1px rgba(61,225,255,.45)}}

.when{{margin-top:auto;width:100%;position:relative;padding:26px 30px 26px;
  background:rgba(16,20,32,.92);
  background-image:
    linear-gradient({RED},{RED}),linear-gradient({RED},{RED}),
    linear-gradient({RED},{RED}),linear-gradient({RED},{RED});
  background-size:30px 3px,3px 30px,30px 3px,3px 30px;
  background-position:0 0,0 0,100% 100%,100% 100%;
  background-repeat:no-repeat;text-align:center}}
.when .lbl{{font-family:Mono;font-weight:700;font-size:16px;letter-spacing:.3em;color:{ICE}}}
.when .big{{font-family:Anton;font-size:{F["BIG"]}px;letter-spacing:.02em;line-height:1.06;margin-top:15px}}
.when .big em{{font-style:normal;color:{RED}}}

.stats{{display:flex;gap:14px;width:100%;margin-top:14px}}
.stat{{flex:1;background:rgba(16,20,32,.92);padding:18px 8px 15px;text-align:center;
  box-shadow:inset 0 3px 0 {RED}}}
.stat.i{{box-shadow:inset 0 3px 0 {ICE}}}
.stat b{{display:block;font-family:Anton;font-size:{F["STAT"]}px;line-height:1;letter-spacing:.01em}}
.stat.i b{{color:{ICE}}}
.stat span{{display:block;margin-top:9px;font-family:Mono;font-weight:700;font-size:13px;
  letter-spacing:.19em;color:{STEEL}}}

.foot{{display:flex;align-items:center;justify-content:space-between;width:100%;margin-top:{F["GAP"]}px}}
.foot .url{{font-family:Anton;font-size:{F["URL"]}px;letter-spacing:.03em;color:{CHALK}}}
.foot .url span{{color:{RED}}}
.foot .sub{{font-family:Mono;font-weight:700;font-size:14px;letter-spacing:.2em;
  color:{STEEL};margin-top:7px}}
.foot img{{height:{F["EMB"]}px;filter:drop-shadow(0 0 20px rgba(255,46,67,.5))}}
"""


  if anim:
   # ── TIMELINE ──────────────────────────────────────────────────────────
  # 6s. Enters are ease-out and short; the pool is the one moment allowed
  # to be loud, because you see this once, not fifty times a day. The last
  # second holds so the frame is readable when the loop wraps.
   CSS += f"""
@property --n {{ syntax:'<integer>'; initial-value:0; inherits:false }}
.kick,.word,.rule,.tag,.about>div,.lineage,.prize,.when,.stats>div,.foot{{
  animation-fill-mode:both !important; animation-timing-function:cubic-bezier(.23,1,.32,1) !important}}

.kick{{animation:aIn 460ms 240ms}}
.word{{animation:aBoot 760ms 60ms}}
.rule{{animation:aWipe 520ms 720ms}}
.tag{{animation:aTag 620ms 900ms}}
.about>div:nth-child(1){{animation:aIn 460ms 1380ms}}
.about>div:nth-child(2){{animation:aIn 460ms 1500ms}}
.about>div:nth-child(3){{animation:aIn 460ms 1620ms}}
.lineage{{animation:aIn 460ms 1760ms}}
.prize{{animation:aSlam 620ms 2050ms}}
.prize .num{{animation:aCount 900ms 2250ms cubic-bezier(.23,1,.32,1) both;
  counter-reset:n var(--n)}}
.prize .num::after{{content:counter(n)}}
.prize .c{{animation:aIn 420ms 2900ms both}}
.when{{animation:aRise 560ms 3150ms}}
.stats>div:nth-child(1){{animation:aRise 480ms 3600ms}}
.stats>div:nth-child(2){{animation:aRise 480ms 3700ms}}
.stats>div:nth-child(3){{animation:aRise 480ms 3800ms}}
.foot{{animation:aIn 520ms 4020ms}}

@keyframes aIn{{from{{opacity:0;transform:translateY(14px)}}to{{opacity:1;transform:none}}}}
@keyframes aRise{{from{{opacity:0;transform:translateY(24px)}}to{{opacity:1;transform:none}}}}
@keyframes aWipe{{from{{opacity:0;transform:scaleX(.2)}}to{{opacity:1;transform:none}}}}
/* the wordmark arrives as a glitch: torn bands, chromatic fringe, then settles */
@keyframes aBoot{{
  0%{{opacity:0;transform:translateX(-26px) skewX(7deg) scale(1.06);
      filter:drop-shadow(16px 0 rgba(255,46,67,.9)) drop-shadow(-16px 0 rgba(61,225,255,.9));
      clip-path:inset(42% 0 42% 0)}}
  22%{{opacity:1;transform:translateX(18px) skewX(-4deg) scale(1.03);clip-path:inset(0 0 58% 0)}}
  42%{{transform:translateX(-11px) skewX(2deg);clip-path:inset(8% 0 0 0)}}
  62%{{transform:translateX(6px);clip-path:inset(0 0 0 0);
      filter:drop-shadow(5px 0 rgba(255,46,67,.6)) drop-shadow(-5px 0 rgba(61,225,255,.6))}}
  100%{{transform:none;filter:none;clip-path:inset(0 0 0 0)}}}}
@keyframes aTag{{
  0%{{opacity:0;letter-spacing:.3em;filter:blur(7px)}}
  55%{{opacity:1;letter-spacing:.06em;filter:blur(0)}}
  100%{{opacity:1;letter-spacing:.035em}}}}
@keyframes aSlam{{
  0%{{opacity:0;transform:scale(.9);box-shadow:0 0 0 rgba(255,46,67,0)}}
  58%{{opacity:1;transform:scale(1.022);box-shadow:0 0 120px rgba(255,46,67,.6)}}
  100%{{transform:none;box-shadow:0 0 62px rgba(255,46,67,.24)}}}}
@keyframes aCount{{to{{--n:{POOL}}}}}

/* ambient: the scanlines drift and the pool keeps breathing, so the hold
   at the end is still alive */
.scan{{animation:aScan 2.4s linear infinite}}
@keyframes aScan{{to{{transform:translateY(3px)}}}}
.prize .amt{{animation:aPulse 2.6s 3s ease-in-out infinite}}
@keyframes aPulse{{0%,100%{{text-shadow:0 0 46px rgba(255,46,67,.85)}}
  50%{{text-shadow:0 0 74px rgba(255,46,67,1)}}}}
"""

  HTML = f"""<!doctype html><meta charset="utf-8"><style>{CSS}</style>
<div class="grid"></div>
<div class="tk tl"></div><div class="tk tr"></div>
<div class="tk bl"></div><div class="tk br"></div>
<div class="scan"></div>

<div class="z">
  <span class="kick"><i></i>Urban Playground Presents</span>
  <img class="word" src="data:image/png;base64,{word}" alt="August Attack">
  <div class="rule"></div>
  <div class="tag">SERVE FIRST.<br><b>STRIKE HARD.</b></div>

  <div class="about">{''.join(f'<div>{l}</div>' for l in ABOUT)}</div>

  {LINEAGE_HTML}

  <div class="prize">
    <div class="amt">{'<i class="num"></i>' if anim else POOL}<sub>OMR</sub></div>
    <div class="txt">
      <div class="t">PRIZE POOL<br>UP FOR GRABS</div>
      <div class="c">{BONUS}</div>
    </div>
  </div>

  <div class="when">
    <div class="lbl">EVERY WEEK · ALL AUGUST</div>
    <div class="big">MON &amp; WED<br><em>5:30 PM</em></div>
  </div>

  <div class="stats">
    <div class="stat"><b>{RANKED}</b><span>RANKED</span></div>
    <div class="stat i"><b>7</b><span>OMR PER SESSION</span></div>
    <div class="stat"><b>{PREV}</b><span>SERIES BEFORE IT</span></div>
  </div>

  <div class="foot">
    <div>
      <div class="url">ATTACK<span>.</span>URBANPADEL<span>.</span>OM</div>
      <div class="sub">{SUBTITLE.upper()}</div>
    </div>
    <img src="data:image/png;base64,{emblem}" alt="Urban Playground">
  </div>
</div>"""

  name = F["out"] + ('-anim' if anim else '')
  open(f'{SC}/{name}.html', 'w').write(HTML)
  return name, F["H"]

for fmt in FORMATS:
    for anim in (False, True):
        name, h = build(fmt, anim)
        print(f'built {name}.html  1080x{h}  ({fmt}{", animated" if anim else ""})')
print(f'facts: {RANKED} ranked, vol.{PREV + 1}, pool {POOL} OMR')
