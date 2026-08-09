# -*- coding: utf-8 -*-
"""AUGUST ATTACK — session night Instagram story.

1080x1920. Frame is 170 top / 244 bottom, not Instagram's blanket 250/250:
the top overlay is only the profile row, while the bottom reply bar really
is that tall. Type is set for a phone first and content cut to suit.

  python3 build_session_story.py --session 3 --date "MON 10 AUG" --time "5:30 PM"

The chasing pack is read from news_stats2.json, which stats2.cjs produces by
running the app's OWN engine over live state -- so the poster can never
disagree with the RANK tab.

Field state (--full / --spots N) changes the call to action. A story that
says "drop your name" when all 16 rows are taken sends people to a closed
list; a story that says FULL sells the waitlist instead, which is the more
honest and the more urgent message.
"""
import argparse, base64, json, os

SC = os.path.dirname(os.path.abspath(__file__))
b64f = lambda f: base64.b64encode(open(f'{SC}/{f}', 'rb').read()).decode()

ap = argparse.ArgumentParser()
ap.add_argument('--session', default='3')
ap.add_argument('--date',    default='MON 10 AUG')
ap.add_argument('--time',    default='5:30 PM')
ap.add_argument('--fee',     default='7')
ap.add_argument('--voucher', default='14')
ap.add_argument('--left',    default='7', help='sessions remaining, including this one')
ap.add_argument('--full',    action='store_true', help='16 teams already in')
ap.add_argument('--partners', default=None, help='e.g. "4" — teams still needing a partner')
ap.add_argument('--out',     default='session-story')
A = ap.parse_args()

anton = b64f('anton.woff2');      mono  = b64f('jbmono700.woff2')
arch8 = b64f('archivo800.woff2'); arch6 = b64f('archivo600.woff2')
word  = b64f('aa-wordmark-clean.png')

RED, ICE, CHALK, STEEL, COURT = '#FF2E43', '#3DE1FF', '#F4F6FA', '#8B95A7', '#0A0C12'

TOP = json.load(open(f'{SC}/news_stats2.json'))['top'][:3]

chase = ''.join(
    f'''<div class="cr"><span class="crk">{e['rank']}</span>
      <span class="cnm">{e['name']}</span><span class="cpt">{e['pts']}</span></div>'''
    for e in TOP)

if A.full:
    cta_h, cta_p = 'THE LIST IS <em>FULL</em>', 'Waitlist is open &mdash; drop your name, teams drop out every week.'
else:
    cta_h, cta_p = 'GET YOUR <em>NAME</em> DOWN', 'Sixteen teams max, first come first served.'

partners = (f'<div class="pn">{A.partners} teams still need a partner &mdash; '
            f'say the word and we pair you up.</div>') if A.partners else ''

CSS = f"""
@font-face{{font-family:'Anton';src:url(data:font/woff2;base64,{anton}) format('woff2');font-display:block}}
@font-face{{font-family:'Mono';font-weight:700;src:url(data:font/woff2;base64,{mono}) format('woff2')}}
@font-face{{font-family:'Archivo';font-weight:800;src:url(data:font/woff2;base64,{arch8}) format('woff2')}}
@font-face{{font-family:'Archivo';font-weight:600;src:url(data:font/woff2;base64,{arch6}) format('woff2')}}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{width:1080px;height:1920px;overflow:hidden;position:relative;color:{CHALK};
  font-family:Archivo,sans-serif;background:
  radial-gradient(ellipse 92% 30% at 50% 0%, rgba(255,46,67,.30), transparent 62%),
  radial-gradient(ellipse 60% 24% at 6% 74%, rgba(61,225,255,.10), transparent 64%),
  linear-gradient(180deg,#08090D 0%,{COURT} 42%,#06070B 100%)}}
.grid{{position:absolute;inset:0;z-index:0;opacity:.5;
  background-image:linear-gradient(rgba(255,46,67,.055) 1px,transparent 1px),
   linear-gradient(90deg,rgba(255,46,67,.055) 1px,transparent 1px);background-size:48px 48px;
  -webkit-mask-image:radial-gradient(120% 60% at 50% 16%,#000,transparent 88%)}}
.tk{{position:absolute;width:66px;height:66px;z-index:5}}
.tk.tl{{top:184px;left:44px;border-top:6px solid {ICE};border-left:6px solid {ICE}}}
.tk.br{{bottom:258px;right:44px;border-bottom:6px solid {RED};border-right:6px solid {RED}}}
.z{{position:relative;z-index:4;min-height:1920px;padding:170px 68px 244px;
  display:flex;flex-direction:column;align-items:center;justify-content:center}}

.word{{width:430px;filter:drop-shadow(0 0 34px rgba(255,46,67,.45))}}

.kick{{margin-top:22px;padding:13px 30px 11px;background:{RED};
  box-shadow:0 0 54px rgba(255,46,67,.55)}}
.kick b{{font-family:Anton;font-size:44px;letter-spacing:.08em;color:#fff}}

.sn{{margin-top:26px;text-align:center;line-height:.82}}
.sn span{{display:block;font-family:Mono;font-weight:700;font-size:22px;letter-spacing:.34em;
  color:{STEEL};margin-left:.34em}}
.sn b{{display:block;margin-top:14px;font-family:Anton;font-size:210px;color:{CHALK};
  text-shadow:0 0 60px rgba(255,46,67,.5);font-variant-numeric:tabular-nums}}

.when{{margin-top:22px;text-align:center;font-family:Anton;font-size:64px;letter-spacing:.02em;
  line-height:1.06}}
.when em{{font-style:normal;color:{ICE}}}
.where{{margin-top:12px;font-family:Mono;font-weight:700;font-size:22px;letter-spacing:.2em;
  color:{STEEL}}}

.tiles{{display:flex;gap:14px;width:100%;margin-top:30px}}
.tile{{flex:1;text-align:center;background:rgba(16,20,32,.92);padding:22px 6px 18px;
  box-shadow:inset 0 4px 0 {RED}}}
.tile.i{{box-shadow:inset 0 4px 0 {ICE}}}
.tile b{{display:block;font-family:Anton;font-size:62px;line-height:1;
  font-variant-numeric:tabular-nums}}
.tile.i b{{color:{ICE}}}
.tile span{{display:block;margin-top:9px;font-family:Mono;font-weight:700;font-size:16px;
  letter-spacing:.14em;color:{STEEL}}}

.sec{{display:flex;align-items:center;gap:14px;width:100%;margin:28px 0 10px}}
.sec b{{font-family:Mono;font-weight:700;font-size:17px;letter-spacing:.28em;color:{RED};
  white-space:nowrap}}
.sec i{{flex:1;height:1px;background:rgba(244,246,250,.14)}}

.chase{{width:100%;background:rgba(16,20,32,.92);padding:4px 26px 8px}}
.cr{{display:flex;align-items:center;gap:22px;padding:13px 0;
  border-bottom:1px solid rgba(244,246,250,.07)}}
.cr:last-child{{border-bottom:none}}
.crk{{flex:none;width:44px;font-family:Anton;font-size:38px;color:{STEEL};text-align:center}}
.cr:first-child .crk{{color:{RED}}}
.cnm{{flex:1;font-family:Anton;font-size:44px;letter-spacing:.02em;white-space:nowrap;
  overflow:hidden;text-overflow:ellipsis}}
.cpt{{flex:none;width:110px;text-align:right;font-family:Anton;font-size:50px;
  font-variant-numeric:tabular-nums}}
.cr:first-child .cpt{{color:{RED}}}

.cta{{width:100%;margin-top:26px;background:rgba(16,20,32,.94);padding:26px 30px 24px;
  background-image:linear-gradient({ICE},{ICE}),linear-gradient({ICE},{ICE}),
    linear-gradient({RED},{RED}),linear-gradient({RED},{RED});
  background-size:28px 4px,4px 28px,28px 4px,4px 28px;
  background-position:0 0,0 0,100% 100%,100% 100%;background-repeat:no-repeat}}
.cta h4{{font-family:Anton;font-size:56px;line-height:1.05}}
.cta h4 em{{font-style:normal;color:{RED}}}
.cta p{{margin-top:12px;font-weight:600;font-size:25px;line-height:1.38;color:#C9CFDA}}
.pn{{margin-top:12px;font-weight:600;font-size:23px;line-height:1.35;color:{ICE}}}

.foot{{margin-top:26px;width:100%;text-align:center;font-family:Anton;font-size:40px;
  letter-spacing:.04em}}
.foot em{{font-style:normal;color:{RED}}}
"""

HTML = f"""<!doctype html><meta charset="utf-8"><style>{CSS}</style>
<div class="grid"></div><div class="tk tl"></div><div class="tk br"></div>
<div class="z">
  <img class="word" src="data:image/png;base64,{word}" alt="August Attack">
  <div class="kick"><b>TOMORROW</b></div>

  <div class="sn"><span>SESSION</span><b>{int(A.session):02d}</b></div>
  <div class="when">{A.date} &middot; <em>{A.time}</em></div>
  <div class="where">URBAN PLAYGROUND &middot; OMAN</div>

  <div class="tiles">
    <div class="tile"><b>{A.fee}</b><span>OMR TO PLAY</span></div>
    <div class="tile i"><b>{A.voucher}</b><span>OMR IF YOU WIN</span></div>
    <div class="tile"><b>{A.left}</b><span>NIGHTS LEFT</span></div>
  </div>

  <div class="sec"><b>CATCH THEM IF YOU CAN</b><i></i></div>
  <div class="chase">{chase}</div>

  <div class="cta">
    <h4>{cta_h}</h4>
    <p>{cta_p}</p>
    {partners}
  </div>

  <div class="foot">ATTACK<em>.</em>URBANPADEL<em>.</em>OM</div>
</div>"""

open(f'{SC}/{A.out}.html', 'w').write(HTML)
print(f'built {A.out}.html  session {A.session}  full={A.full}')
