# -*- coding: utf-8 -*-
"""AUGUST ATTACK — sign-up card, the image that fronts the WhatsApp post.

1080x1350. It has to survive two very different readings:
  · a thumbnail in a busy group chat — so the wordmark, SIGN-UP OPEN and the
    402 have to carry on their own
  · opened full screen — where the format and the point table have to be
    legible enough that nobody has to ask "how does it work?"

Facts are read from the app, same as the launch creative:
  points table -> the HOW TO SCORE panel in august-attack-index.html
  best-3 rule  -> GROUP_COUNTED_GAMES = 3
  7 OMR / 14 OMR voucher -> the session announcement builder
  402 = 9 sessions x 28 OMR vouchers + 75/45/30 season prizes
"""
import base64

SC = '/tmp/claude-0/-home-user-May-madness/0e44f0ad-a683-5f0d-9de6-9459ae328963/scratchpad'
b64f = lambda f: base64.b64encode(open(f'{SC}/{f}', 'rb').read()).decode()

anton  = b64f('anton.woff2')
mono   = b64f('jbmono700.woff2')
arch8  = b64f('archivo800.woff2')
arch6  = b64f('archivo600.woff2')
word   = b64f('aa-wordmark-clean.png')
emblem = b64f('aa-emblem.png')

RED, ICE, CHALK, STEEL, COURT, GREEN = '#FF2E43', '#3DE1FF', '#F4F6FA', '#8B95A7', '#0A0C12', '#27E08A'

GROUP = [('WIN', '+3'), ('TIEBREAK LOSS', '+2'), ('COMPETITIVE LOSS', '+1'), ('TOP OF GROUP', '+1')]
KO    = [('REACH QF', '+1'), ('REACH SF', '+2'), ('REACH FINAL', '+3'), ('WIN THE FINAL', '+5')]
PODIUM = [('1ST', '75'), ('2ND', '45'), ('3RD', '30')]

CSS = f"""
@font-face{{font-family:'Anton';src:url(data:font/woff2;base64,{anton}) format('woff2');font-display:block}}
@font-face{{font-family:'Mono';font-weight:700;src:url(data:font/woff2;base64,{mono}) format('woff2')}}
@font-face{{font-family:'Archivo';font-weight:800;src:url(data:font/woff2;base64,{arch8}) format('woff2')}}
@font-face{{font-family:'Archivo';font-weight:600;src:url(data:font/woff2;base64,{arch6}) format('woff2')}}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{width:1080px;height:1350px;overflow:hidden;position:relative;color:{CHALK};
  font-family:Archivo,sans-serif;background:
  radial-gradient(ellipse 90% 42% at 50% 2%, rgba(255,46,67,.28), transparent 62%),
  radial-gradient(ellipse 60% 32% at 6% 70%, rgba(61,225,255,.10), transparent 64%),
  linear-gradient(180deg,#08090D 0%,{COURT} 52%,#06070B 100%)}}
.grid{{position:absolute;inset:0;z-index:0;opacity:.5;
  background-image:linear-gradient(rgba(255,46,67,.055) 1px,transparent 1px),
    linear-gradient(90deg,rgba(255,46,67,.055) 1px,transparent 1px);background-size:46px 46px;
  -webkit-mask-image:radial-gradient(120% 76% at 50% 24%,#000,transparent 88%)}}
.scan{{position:absolute;inset:-6px 0;z-index:6;pointer-events:none;
  background:repeating-linear-gradient(0deg,rgba(0,0,0,.17) 0 1px,transparent 1px 3px)}}
.tk{{position:absolute;width:64px;height:64px;z-index:5}}
.tk.tl{{top:38px;left:38px;border-top:5px solid {ICE};border-left:5px solid {ICE}}}
.tk.br{{bottom:38px;right:38px;border-bottom:5px solid {RED};border-right:5px solid {RED}}}
.z{{position:relative;z-index:4;height:100%;display:flex;flex-direction:column;
  align-items:center;padding:74px 72px 66px}}

.word{{width:470px;filter:drop-shadow(0 0 30px rgba(255,46,67,.42))}}

/* the one line that has to survive a thumbnail */
.open{{margin-top:16px;display:inline-flex;align-items:center;gap:14px;
  padding:13px 26px 11px;background:{RED};box-shadow:0 0 46px rgba(255,46,67,.55)}}
.open b{{font-family:Anton;font-size:38px;letter-spacing:.06em;color:#fff}}
.open i{{width:11px;height:11px;background:#fff;border-radius:50%;display:block}}

.meta{{margin-top:16px;font-family:Mono;font-weight:700;font-size:19px;
  letter-spacing:.12em;color:{CHALK};text-align:center;line-height:1.65}}
.meta span{{color:{ICE}}}

/* format chips */
.chips{{display:flex;gap:12px;margin-top:22px;width:100%}}
.chip{{flex:1;text-align:center;padding:16px 8px 13px;white-space:nowrap;background:rgba(16,20,32,.92);
  box-shadow:inset 0 3px 0 {ICE}}}
.chip b{{display:block;font-family:Anton;font-size:38px;line-height:1}}
.chip span{{display:block;margin-top:6px;font-family:Mono;font-weight:700;font-size:12px;
  letter-spacing:.16em;color:{STEEL}}}

.sec{{display:flex;align-items:center;gap:12px;width:100%;margin:30px 0 13px}}
.sec b{{font-family:Mono;font-weight:700;font-size:14px;letter-spacing:.28em;color:{RED};
  white-space:nowrap}}
.sec i{{flex:1;height:1px;background:rgba(244,246,250,.14)}}

/* points: two columns, mono values so they line up */
.cols{{display:flex;gap:14px;width:100%}}
.col{{flex:1;background:rgba(16,20,32,.92);padding:16px 16px 14px;
  background-image:linear-gradient({RED},{RED}),linear-gradient({RED},{RED});
  background-size:22px 2px,2px 22px;background-position:0 0,0 0;background-repeat:no-repeat}}
.col h4{{font-family:Anton;font-size:22px;letter-spacing:.04em;color:{CHALK};margin-bottom:10px}}
.row{{display:flex;justify-content:space-between;align-items:baseline;padding:6px 0;
  border-bottom:1px solid rgba(244,246,250,.07)}}
.row:last-child{{border-bottom:none}}
.row span{{font-family:Archivo;font-weight:600;font-size:17px;color:{STEEL};letter-spacing:.01em}}
.row em{{font-style:normal;font-family:Mono;font-weight:700;font-size:19px;color:{CHALK}}}
.row.win em{{color:{GREEN}}}
.row.gold em{{color:{RED}}}
.note{{width:100%;margin-top:10px;font-family:Archivo;font-weight:600;font-size:15px;
  color:{STEEL};text-align:center;letter-spacing:.01em}}

/* prizes */
.pool{{display:flex;align-items:center;gap:24px;width:100%;margin-top:6px;
  padding:18px 24px 16px;background:rgba(16,20,32,.94);
  background-image:linear-gradient({ICE},{ICE}),linear-gradient({ICE},{ICE}),
    linear-gradient({RED},{RED}),linear-gradient({RED},{RED});
  background-size:28px 3px,3px 28px,28px 3px,3px 28px;
  background-position:0 0,0 0,100% 100%,100% 100%;background-repeat:no-repeat;
  box-shadow:0 0 54px rgba(255,46,67,.2)}}
.pool .amt{{font-family:Anton;font-size:82px;line-height:.82;color:{RED};
  text-shadow:0 0 40px rgba(255,46,67,.8)}}
.pool .amt sub{{display:block;font-size:.26em;letter-spacing:.2em;color:{CHALK};
  margin-top:7px;text-shadow:none}}
.pool .podwrap{{flex:1}}
.pool .podlab{{font-family:Mono;font-weight:700;font-size:12px;letter-spacing:.22em;
  color:{STEEL};margin-bottom:7px}}
.pool .pod{{display:flex;gap:9px}}
.pod div{{flex:1;text-align:center;padding:10px 4px 10px;background:rgba(6,7,11,.6);
  box-shadow:inset 0 2px 0 {RED}}}
.pod div:nth-child(2){{box-shadow:inset 0 2px 0 rgba(244,246,250,.5)}}
.pod div:nth-child(3){{box-shadow:inset 0 2px 0 {STEEL}}}
.pod b{{display:block;font-family:Anton;font-size:32px;line-height:1}}
.pod span{{display:block;margin-bottom:5px;font-family:Mono;font-weight:700;font-size:12px;
  letter-spacing:.16em;color:{ICE}}}
.pod u{{display:block;margin-top:3px;text-decoration:none;font-family:Mono;font-weight:700;
  font-size:11px;letter-spacing:.1em;color:{STEEL}}}

.per{{width:100%;margin-top:13px;margin-bottom:auto;text-align:center;font-family:Mono;font-weight:700;
  font-size:16px;letter-spacing:.1em;color:{CHALK}}}
.per em{{font-style:normal;color:{ICE}}}

.foot{{margin-top:26px;display:flex;align-items:center;justify-content:space-between;width:100%}}
.foot .cta{{font-family:Anton;font-size:37px;letter-spacing:.03em;line-height:1.1}}
.foot .cta em{{font-style:normal;color:{RED}}}
.foot .url{{margin-top:6px;font-family:Mono;font-weight:700;font-size:15px;
  letter-spacing:.13em;color:{STEEL}}}
.foot img{{height:104px;filter:drop-shadow(0 0 18px rgba(255,46,67,.5))}}
"""

def rows(items, cls_for=lambda k: ''):
    return ''.join(f'<div class="row {cls_for(k)}"><span>{k}</span><em>{v}</em></div>'
                   for k, v in items)

HTML = f"""<!doctype html><meta charset="utf-8"><style>{CSS}</style>
<div class="grid"></div><div class="tk tl"></div><div class="tk br"></div><div class="scan"></div>
<div class="z">
  <img class="word" src="data:image/png;base64,{word}" alt="August Attack">
  <div class="open"><i></i><b>SIGN-UP OPEN</b></div>
  <div class="meta">MON &amp; WED &middot; <span>5:30 PM</span> &middot; ALL AUGUST<br>
    URBAN PLAYGROUND &middot; <span>7 OMR</span> PER PLAYER</div>

  <div class="chips">
    <div class="chip"><b>16</b><span>TEAMS</span></div>
    <div class="chip"><b>4</b><span>GROUPS OF 4</span></div>
    <div class="chip"><b>QF&rarr;F</b><span>KNOCKOUTS</span></div>
  </div>

  <div class="sec"><b>HOW YOU SCORE</b><i></i></div>
  <div class="cols">
    <div class="col"><h4>GROUP STAGE</h4>
      {rows(GROUP, lambda k: 'win' if k == 'WIN' else '')}</div>
    <div class="col"><h4>KNOCKOUTS</h4>
      {rows(KO, lambda k: 'gold' if k == 'WIN THE FINAL' else '')}</div>
  </div>
  <div class="note">Only your best 3 group games count &mdash; a bigger group is never an advantage.</div>

  <div class="sec"><b>PRIZES</b><i></i></div>
  <div class="pool">
    <div class="amt">402<sub>OMR TOTAL</sub></div>
    <div class="podwrap">
      <div class="podlab">END OF SEASON</div>
      <div class="pod">
        {''.join(f'<div><span>{k}</span><b>{v}</b><u>OMR</u></div>' for k, v in PODIUM)}
      </div>
    </div>
  </div>
  <div class="per">EVERY SESSION: WINNERS TAKE A <em>14 OMR VOUCHER</em> EACH</div>

  <div class="foot">
    <div>
      <div class="cta">DROP YOUR NAME<br><em>+ PARTNER BELOW</em></div>
      <div class="url">ATTACK.URBANPADEL.OM</div>
    </div>
    <img src="data:image/png;base64,{emblem}" alt="Urban Playground">
  </div>
</div>"""

open(f'{SC}/signup-card.html', 'w').write(HTML)
print('built signup-card.html')
