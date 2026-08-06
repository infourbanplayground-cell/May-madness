# -*- coding: utf-8 -*-
"""AUGUST ATTACK — the report after two nights.

Figures come from news_stats2.json / news_extra.json, produced by stats2.cjs
running the app's OWN scoring engine (aa_score.cjs, lifted verbatim from
august-attack-index.html) over the live API state. Cross-checked against the
app's RANK tab: 48 ranked, Munther 45, Mazin 40, climber Mazin +14.

Player photos are the real ones from the app's /photos endpoint.

Highlights deliberately name DIFFERENT people: Munther tops wins, win-rate,
streak AND top-of-group, so awarding him each of those is one fact wearing
four hats.

Re-run after any session:
  ssh urbanpadel 'curl -s http://127.0.0.1:3005/state'  > aa_live2.json
  ssh urbanpadel 'curl -s http://127.0.0.1:3005/photos' > aa_photos.json
  node stats2.cjs > news_stats2.json && python3 build_newsletter.py
"""
import base64, json

SC = '/tmp/claude-0/-home-user-May-madness/0e44f0ad-a683-5f0d-9de6-9459ae328963/scratchpad'
b64f = lambda f: base64.b64encode(open(f'{SC}/{f}', 'rb').read()).decode()

anton = b64f('anton.woff2'); mono = b64f('jbmono700.woff2')
arch8 = b64f('archivo800.woff2'); arch6 = b64f('archivo600.woff2')
word  = b64f('aa-wordmark-clean.png'); emblem = b64f('aa-emblem.png')

D  = json.load(open(f'{SC}/news_stats2.json'))
EX = json.load(open(f'{SC}/news_extra.json'))
PH = json.load(open(f'{SC}/news_photos.json'))
OLD = json.load(open(f'{SC}/news_stats.json'))          # session/match totals

import sys
STORY = '--story' in sys.argv          # 1080x1920 instead of the tall report
S1, S2 = OLD['sessions'][0], OLD['sessions'][1]
TOP, T = D['top'][:5 if STORY else 8], OLD['totals']
LEFT = 9 - len(OLD['sessions'])

RED, ICE, CHALK, STEEL, COURT, GREEN = '#FF2E43', '#3DE1FF', '#F4F6FA', '#8B95A7', '#0A0C12', '#27E08A'

STORY_CSS = '''
/* story cut: same content grammar, compressed to 1080x1920 inside the
   250px safe margins Instagram reserves top and bottom */
.mast img{width:250px} .mast .iss b{font-size:26px} .mast .iss{font-size:11px}
.sec{margin:22px 0 11px} .sec:first-of-type{margin-top:20px}
.sec b{font-size:12px}
.num{padding:14px 6px 11px} .num b{font-size:40px} .num span{font-size:10px}
.card{padding:13px 15px;gap:13px} .card .n{font-size:23px} .card .d{font-size:13px}
.card .k{font-size:10px}
.night{padding:15px 17px 14px} .night .hd h3{font-size:24px}
.night .v2{font-size:16px} .night .sub{font-size:11px;margin-top:9px}
.tbl{padding:2px 16px 8px}
.tr{padding:8px 0;gap:12px} .tr .nm{font-size:21px} .tr .pt{font-size:24px;width:70px}
.tr .rk{font-size:21px;width:30px} .tr .meta{font-size:11px;width:158px}
.note{font-size:14px;margin-top:10px}
.next{padding:17px 20px 16px} .next h4{font-size:24px;margin-bottom:7px}
.next p{font-size:15px;line-height:1.5}
.foot{margin-top:22px;padding-top:16px} .foot .u{font-size:26px}
.foot .s{font-size:10px} .foot img{height:70px}
'''

def av(pid, size=96, accent=RED):
    src = PH.get(pid)
    if not src:
        return f'<span class="av ph" style="width:{size}px;height:{size}px"></span>'
    return (f'<span class="av" style="width:{size}px;height:{size}px;'
            f'background-image:url({src});box-shadow:inset 0 -3px 0 {accent}"></span>')

def dm(iso):
    y, m, d = iso.split('-')
    return f"{int(d)} {['JAN','FEB','MAR','APR','MAY','JUN','JUL','AUG','SEP','OCT','NOV','DEC'][int(m)-1]}"

CSS = f"""

@font-face{{font-family:'Anton';src:url(data:font/woff2;base64,{anton}) format('woff2');font-display:block}}
@font-face{{font-family:'Mono';font-weight:700;src:url(data:font/woff2;base64,{mono}) format('woff2')}}
@font-face{{font-family:'Archivo';font-weight:800;src:url(data:font/woff2;base64,{arch8}) format('woff2')}}
@font-face{{font-family:'Archivo';font-weight:600;src:url(data:font/woff2;base64,{arch6}) format('woff2')}}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{width:1080px;{'height:1920px;overflow:hidden;' if STORY else ''}position:relative;color:{CHALK};font-family:Archivo,sans-serif;background:
  radial-gradient(ellipse 90% 24% at 50% 0%, rgba(255,46,67,.26), transparent 60%),
  radial-gradient(ellipse 60% 18% at 8% 50%, rgba(61,225,255,.09), transparent 62%),
  linear-gradient(180deg,#08090D 0%,{COURT} 38%,#06070B 100%)}}
.grid{{position:absolute;inset:0;z-index:0;opacity:.45;
  background-image:linear-gradient(rgba(255,46,67,.05) 1px,transparent 1px),
   linear-gradient(90deg,rgba(255,46,67,.05) 1px,transparent 1px);background-size:46px 46px;
  -webkit-mask-image:radial-gradient(120% 46% at 50% 10%,#000,transparent 88%)}}
.z{{position:relative;z-index:2;padding:{'250px 62px 250px' if STORY else '60px 68px 66px'}{';min-height:1920px;display:flex;flex-direction:column;justify-content:center' if STORY else ''}}}

.av{{display:inline-block;flex:none;background-size:cover;background-position:center 22%;
  background-color:#141826}}
.av.ph{{background:rgba(244,246,250,.06);box-shadow:inset 0 -3px 0 {STEEL}}}

.mast{{display:flex;align-items:flex-end;justify-content:space-between;
  border-bottom:3px solid {RED};padding-bottom:20px}}
.mast img{{width:310px;filter:drop-shadow(0 0 24px rgba(255,46,67,.4))}}
.mast .iss{{text-align:right;font-family:Mono;font-weight:700;font-size:13px;
  letter-spacing:.2em;color:{STEEL};line-height:1.8}}
.mast .iss b{{display:block;font-family:Anton;font-size:32px;letter-spacing:.03em;color:{CHALK}}}

.lede{{margin-top:26px;font-weight:600;font-size:22px;line-height:1.55;color:#C9CFDA;
  max-width:880px;text-wrap:pretty}}
.lede b{{color:{CHALK};font-weight:800}}

.sec{{display:flex;align-items:center;gap:14px;margin:40px 0 16px}}
.sec:first-of-type{{margin-top:34px}}
.sec b{{font-family:Mono;font-weight:700;font-size:14px;letter-spacing:.3em;color:{RED};white-space:nowrap}}
.sec i{{flex:1;height:1px;background:rgba(244,246,250,.14)}}

.nums{{display:flex;gap:12px}}
.num{{flex:1;background:rgba(16,20,32,.92);padding:20px 8px 16px;text-align:center;
  box-shadow:inset 0 3px 0 {RED}}}
.num.i{{box-shadow:inset 0 3px 0 {ICE}}}
.num b{{display:block;font-family:Anton;font-size:48px;line-height:.95;font-variant-numeric:tabular-nums}}
.num.i b{{color:{ICE}}}
.num span{{display:block;margin-top:7px;font-family:Mono;font-weight:700;font-size:11px;
  letter-spacing:.15em;color:{STEEL}}}

/* highlight cards, each about a different person */
.hl{{display:grid;grid-template-columns:1fr 1fr;gap:14px}}
.card{{display:flex;gap:16px;align-items:center;background:rgba(16,20,32,.92);padding:18px 20px;
  background-image:linear-gradient({RED},{RED}),linear-gradient({RED},{RED});
  background-size:22px 3px,3px 22px;background-position:0 0,0 0;background-repeat:no-repeat}}
.card.i{{background-image:linear-gradient({ICE},{ICE}),linear-gradient({ICE},{ICE})}}
.card .txt{{min-width:0}}
.card .k{{font-family:Mono;font-weight:700;font-size:11px;letter-spacing:.2em;color:{RED}}}
.card.i .k{{color:{ICE}}}
.card .n{{font-family:Anton;font-size:27px;line-height:1.1;margin-top:5px;
  white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
.card .d{{font-weight:600;font-size:15px;color:{STEEL};margin-top:4px;line-height:1.4}}
.card .d em{{font-style:normal;color:{CHALK};font-weight:800}}

/* nights */
.nights{{display:flex;gap:16px}}
.night{{flex:1;background:rgba(16,20,32,.92);padding:20px 22px 18px;
  background-image:linear-gradient({RED},{RED}),linear-gradient({RED},{RED});
  background-size:24px 3px,3px 24px;background-position:0 0,0 0;background-repeat:no-repeat}}
.night .hd{{display:flex;align-items:baseline;justify-content:space-between;margin-bottom:14px}}
.night .hd h3{{font-family:Anton;font-size:29px}}
.night .hd span{{font-family:Mono;font-weight:700;font-size:12px;letter-spacing:.16em;color:{ICE}}}
.night .duo{{display:flex;align-items:center;gap:12px}}
.night .duo .who{{min-width:0}}
.night .k2{{font-family:Mono;font-weight:700;font-size:10px;letter-spacing:.18em;color:{STEEL}}}
.night .v2{{font-weight:800;font-size:19px;color:{CHALK};line-height:1.3;margin-top:3px}}
.night .sub{{margin-top:12px;display:flex;justify-content:space-between;
  font-family:Mono;font-weight:700;font-size:12px;letter-spacing:.1em;color:{STEEL}}}
.night .sub em{{font-style:normal;color:{CHALK}}}

/* standings */
.tbl{{background:rgba(16,20,32,.92);padding:4px 20px 10px}}
.tr{{display:flex;align-items:center;gap:14px;padding:11px 0;
  border-bottom:1px solid rgba(244,246,250,.07)}}
.tr:last-child{{border-bottom:none}}
.tr .rk{{font-family:Anton;font-size:24px;width:36px;color:{STEEL};text-align:center;flex:none}}
.tr.p1 .rk{{color:{RED}}} .tr.p2 .rk{{color:#C9CFDA}}
.tr .nm{{flex:1;font-family:Anton;font-size:24px;letter-spacing:.02em;
  white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
.tr .meta{{font-family:Mono;font-weight:700;font-size:12px;letter-spacing:.08em;color:{STEEL};
  flex:none;width:172px;text-align:right;font-variant-numeric:tabular-nums}}
.tr .up{{color:{GREEN}}}
.tr .pt{{font-family:Anton;font-size:28px;width:80px;text-align:right;flex:none;
  font-variant-numeric:tabular-nums}}
.tr.p1 .pt{{color:{RED}}}

.note{{margin-top:13px;font-weight:600;font-size:17px;color:{STEEL};line-height:1.6}}
.note b{{color:{CHALK};font-weight:800}}

.next{{background:rgba(16,20,32,.94);padding:24px 26px 22px;
  background-image:linear-gradient({ICE},{ICE}),linear-gradient({ICE},{ICE}),
    linear-gradient({RED},{RED}),linear-gradient({RED},{RED});
  background-size:26px 3px,3px 26px,26px 3px,3px 26px;
  background-position:0 0,0 0,100% 100%,100% 100%;background-repeat:no-repeat}}
.next h4{{font-family:Anton;font-size:29px;margin-bottom:10px}}
.next p{{font-weight:600;font-size:18px;line-height:1.6;color:#C9CFDA}}
.next p b{{color:{ICE};font-weight:800}}

.foot{{display:flex;align-items:center;justify-content:space-between;
  margin-top:44px;border-top:1px solid rgba(244,246,250,.14);padding-top:24px}}
.foot .u{{font-family:Anton;font-size:32px;letter-spacing:.03em}}
.foot .u em{{font-style:normal;color:{RED}}}
.foot .s{{margin-top:5px;font-family:Mono;font-weight:700;font-size:12px;
  letter-spacing:.18em;color:{STEEL}}}
.foot img{{height:94px;filter:drop-shadow(0 0 18px rgba(255,46,67,.5))}}
{STORY_CSS if STORY else ''}
"""

def card(kicker, pid, nm, desc, cyan=False):
    return f"""<div class="card{' i' if cyan else ''}">{av(pid, 82, ICE if cyan else RED)}
      <div class="txt"><div class="k">{kicker}</div><div class="n">{nm}</div>
      <div class="d">{desc}</div></div></div>"""

C1, C2 = D['champions'][0], D['champions'][1]

def night(s, c, n):
    return f"""
  <div class="night">
    <div class="hd"><h3>NIGHT {n}</h3><span>{dm(s['date'])}</span></div>
    <div class="duo">{av(c['p1'],62)}{av(c['p2'],62)}
      <div class="who"><div class="k2">CHAMPIONS</div><div class="v2">{c['label']}</div></div>
    </div>
    <div class="sub"><span>RUNNERS-UP <em>{s['runnerUp']}</em></span></div>
    <div class="sub"><span>MVP <em>{s['mvp'] or '—'}</em></span>
      <span>{s['teams']} TEAMS &middot; {s['groupMatches']+s['koMatches']} MATCHES</span></div>
  </div>"""

rows = ''.join(
    f'''<div class="tr p{e['rank'] if e['rank']<=2 else ''}">
      <span class="rk">{e['rank']}</span>{av(e['id'],46, RED if e['rank']==1 else STEEL)}
      <span class="nm">{e['name']}</span>
      <span class="meta">{e['sess']} NIGHT{'S' if e['sess']!=1 else ''} &middot; {e['wins']}W &middot; {e['rate']}%{
        f' <span class="up">&#9650;{e["delta"]}</span>' if e.get('delta') and e['delta']>0 else ''}</span>
      <span class="pt">{e['pts']}</span>
    </div>''' for e in TOP)

HTML = f"""<!doctype html><meta charset="utf-8"><style>{CSS}</style>
<div class="grid"></div>
<div class="z">
  <div class="mast">
    <img src="data:image/png;base64,{word}" alt="August Attack">
    <div class="iss"><b>THE REPORT</b>AFTER TWO NIGHTS &middot; VOL.6</div>
  </div>

  <div class="sec"><b>THE NUMBERS</b><i></i></div>
  <div class="nums">
    <div class="num"><b>{T['matches']}</b><span>MATCHES PLAYED</span></div>
    <div class="num i"><b>{T['ranked']}</b><span>PLAYERS RANKED</span></div>
    <div class="num"><b>{D['debutants']}</b><span>SERIES DEBUTANTS</span></div>
    <div class="num i"><b>{LEFT}</b><span>NIGHTS LEFT</span></div>
  </div>

  <div class="sec"><b>HIGHLIGHTS</b><i></i></div>
  <div class="hl">
    {card('SERIES LEADER', D['leader']['id'], D['leader']['name'],
          f"MVP on night one, champion on night two. <em>{D['leader']['pts']} pts</em> from {D['leader']['wins']} wins.")}
    {card('BIGGEST CLIMBER', D['topClimber']['id'], D['topClimber']['name'],
          f"Up <em>{D['topClimber']['delta']} places</em> after taking the night-two title.", cyan=True)}
    {card('CHAMPIONS ON DEBUT', C1['p1'], ' &amp; '.join(D['champDebut']),
          "Won the opening night on their <em>first ever</em> Urban Playground appearance.")}
    {card('MOST CONSISTENT', EX['bestRateOther']['id'], EX['bestRateOther']['name'],
          f"<em>{EX['bestRateOther']['rate']}%</em> win rate across both nights without a title.", cyan=True)}
  </div>

  {'' if STORY else f'''<div class="sec"><b>THE NIGHTS</b><i></i></div>
  <div class="nights">{night(S1,C1,1)}{night(S2,C2,2)}</div>'''}

  <div class="sec"><b>STANDINGS &middot; TOP {len(TOP)}</b><i></i></div>
  <div class="tbl">{rows}</div>
  <p class="note">Only <b>{OLD['bothNights']} players</b> have played both nights.
    {OLD['oneNight']} have played once, and <b>{D['streakBonus']}</b> have already banked a
    streak bonus &mdash; one good night is worth roughly a third of the current lead, so the
    table is nowhere near settled.</p>

  <div class="sec"><b>WHAT'S NEXT</b><i></i></div>
  <div class="next">
    <h4>{LEFT} NIGHTS TO GO</h4>
    <p>Mon &amp; Wed, 5:30 PM, all August &mdash; 7 OMR a player.
    <b>Nights 8 and 9 pay double points</b>, so the table can still flip on the last ball.
    New partners every session: if you missed the first two, you have not missed the series.</p>
  </div>

  <div class="foot">
    <div>
      <div class="u">ATTACK<em>.</em>URBANPADEL<em>.</em>OM</div>
      <div class="s">URBAN SOCIAL SERIES &middot; VOL.6 &middot; LIVE TABLE &amp; FULL RULES</div>
    </div>
    <img src="data:image/png;base64,{emblem}" alt="Urban Playground">
  </div>
</div>"""

out = 'newsletter-story.html' if STORY else 'newsletter.html'
open(f'{SC}/{out}', 'w').write(HTML)
print('built', out, '(1080x1920 story cut)' if STORY else '(tall report)')
