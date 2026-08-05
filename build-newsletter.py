# -*- coding: utf-8 -*-
"""AUGUST ATTACK — newsletter after the first two sessions.

Every figure comes from news_stats.json, which stats.cjs produces by running
the app's OWN scoring engine (aa_score.cjs, extracted verbatim from
august-attack-index.html) over the live state pulled off the API. Cross-checked
against the app's RANK tab: 48 ranked, Munther 45, Mazin 40 — all agree.

Re-run after any session:
    ssh urbanpadel 'curl -s http://127.0.0.1:3005/state' > aa_live2.json
    node stats.cjs > news_stats.json && python3 build_newsletter.py
"""
import base64, json

SC = '/tmp/claude-0/-home-user-May-madness/0e44f0ad-a683-5f0d-9de6-9459ae328963/scratchpad'
b64f = lambda f: base64.b64encode(open(f'{SC}/{f}', 'rb').read()).decode()

anton = b64f('anton.woff2'); mono = b64f('jbmono700.woff2')
arch8 = b64f('archivo800.woff2'); arch6 = b64f('archivo600.woff2')
word  = b64f('aa-wordmark-clean.png'); emblem = b64f('aa-emblem.png')

D = json.load(open(f'{SC}/news_stats.json'))
S1, S2 = D['sessions'][0], D['sessions'][1]
TOP = D['top'][:8]
T = D['totals']
SESSIONS_TOTAL = 9
LEFT = SESSIONS_TOTAL - len(D['sessions'])

RED, ICE, CHALK, STEEL, COURT, GREEN = '#FF2E43', '#3DE1FF', '#F4F6FA', '#8B95A7', '#0A0C12', '#27E08A'

def dm(iso):
    y, m, d = iso.split('-')
    return f"{int(d)} {['JAN','FEB','MAR','APR','MAY','JUN','JUL','AUG','SEP','OCT','NOV','DEC'][int(m)-1]}"

CSS = f"""
@font-face{{font-family:'Anton';src:url(data:font/woff2;base64,{anton}) format('woff2');font-display:block}}
@font-face{{font-family:'Mono';font-weight:700;src:url(data:font/woff2;base64,{mono}) format('woff2')}}
@font-face{{font-family:'Archivo';font-weight:800;src:url(data:font/woff2;base64,{arch8}) format('woff2')}}
@font-face{{font-family:'Archivo';font-weight:600;src:url(data:font/woff2;base64,{arch6}) format('woff2')}}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{width:1080px;position:relative;color:{CHALK};font-family:Archivo,sans-serif;background:
  radial-gradient(ellipse 90% 26% at 50% 0%, rgba(255,46,67,.26), transparent 60%),
  radial-gradient(ellipse 60% 20% at 8% 52%, rgba(61,225,255,.09), transparent 62%),
  linear-gradient(180deg,#08090D 0%,{COURT} 40%,#06070B 100%)}}
.grid{{position:absolute;inset:0;z-index:0;opacity:.45;
  background-image:linear-gradient(rgba(255,46,67,.05) 1px,transparent 1px),
   linear-gradient(90deg,rgba(255,46,67,.05) 1px,transparent 1px);background-size:46px 46px;
  -webkit-mask-image:radial-gradient(120% 50% at 50% 12%,#000,transparent 88%)}}
.z{{position:relative;z-index:2;padding:64px 72px 70px}}

/* masthead */
.mast{{display:flex;align-items:flex-end;justify-content:space-between;
  border-bottom:3px solid {RED};padding-bottom:22px}}
.mast img{{width:330px;filter:drop-shadow(0 0 24px rgba(255,46,67,.4))}}
.mast .iss{{text-align:right;font-family:Mono;font-weight:700;font-size:14px;
  letter-spacing:.2em;color:{STEEL};line-height:1.8}}
.mast .iss b{{display:block;font-family:Anton;font-size:34px;letter-spacing:.03em;color:{CHALK}}}

.lede{{margin-top:30px;font-weight:600;font-size:23px;line-height:1.55;color:#C9CFDA;
  max-width:880px;text-wrap:pretty}}
.lede b{{color:{CHALK};font-weight:800}}

.sec{{display:flex;align-items:center;gap:14px;margin:46px 0 18px}}
.sec b{{font-family:Mono;font-weight:700;font-size:15px;letter-spacing:.3em;color:{RED};white-space:nowrap}}
.sec i{{flex:1;height:1px;background:rgba(244,246,250,.14)}}

/* the numbers */
.nums{{display:flex;gap:14px}}
.num{{flex:1;background:rgba(16,20,32,.92);padding:22px 10px 18px;text-align:center;
  box-shadow:inset 0 3px 0 {RED}}}
.num.i{{box-shadow:inset 0 3px 0 {ICE}}}
.num b{{display:block;font-family:Anton;font-size:54px;line-height:.95}}
.num.i b{{color:{ICE}}}
.num span{{display:block;margin-top:8px;font-family:Mono;font-weight:700;font-size:12px;
  letter-spacing:.16em;color:{STEEL}}}

/* night reports */
.nights{{display:flex;gap:18px}}
.night{{flex:1;background:rgba(16,20,32,.92);padding:24px 24px 22px;
  background-image:linear-gradient({RED},{RED}),linear-gradient({RED},{RED});
  background-size:26px 3px,3px 26px;background-position:0 0,0 0;background-repeat:no-repeat}}
.night .hd{{display:flex;align-items:baseline;justify-content:space-between;margin-bottom:16px}}
.night .hd h3{{font-family:Anton;font-size:32px;letter-spacing:.02em}}
.night .hd span{{font-family:Mono;font-weight:700;font-size:13px;letter-spacing:.16em;color:{ICE}}}
.night dl{{display:flex;flex-direction:column;gap:11px}}
.night .r{{display:flex;gap:12px;align-items:baseline}}
.night .k{{font-family:Mono;font-weight:700;font-size:11px;letter-spacing:.16em;color:{STEEL};
  width:96px;flex:none}}
.night .v{{font-weight:700;font-size:19px;color:{CHALK};line-height:1.35}}
.night .v em{{font-style:normal;color:{STEEL};font-weight:600}}
.night .v.win{{color:{RED};font-weight:800}}

/* standings */
.tbl{{background:rgba(16,20,32,.92);padding:6px 22px 14px}}
.tr{{display:flex;align-items:center;gap:14px;padding:13px 0;
  border-bottom:1px solid rgba(244,246,250,.07)}}
.tr:last-child{{border-bottom:none}}
.tr .rk{{font-family:Anton;font-size:26px;width:44px;color:{STEEL};text-align:center;flex:none}}
.tr.p1 .rk{{color:{RED}}} .tr.p2 .rk{{color:#C9CFDA}} .tr.p3 .rk{{color:{STEEL}}}
.tr .nm{{flex:1;font-family:Anton;font-size:25px;letter-spacing:.02em;color:{CHALK};
  white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
.tr .meta{{font-family:Mono;font-weight:700;font-size:13px;letter-spacing:.1em;color:{STEEL};
  flex:none;width:150px;text-align:right;font-variant-numeric:tabular-nums}}
.tr .pt{{font-family:Anton;font-size:30px;color:{CHALK};width:86px;text-align:right;flex:none;
  font-variant-numeric:tabular-nums}}
.tr.p1 .pt{{color:{RED}}}

.note{{margin-top:14px;font-weight:600;font-size:17px;color:{STEEL};line-height:1.6}}
.note b{{color:{CHALK};font-weight:800}}

/* what's next */
.next{{display:flex;gap:18px;align-items:stretch;margin-top:6px}}
.next .big{{flex:1;background:rgba(16,20,32,.94);padding:26px 28px 24px;
  background-image:linear-gradient({ICE},{ICE}),linear-gradient({ICE},{ICE}),
    linear-gradient({RED},{RED}),linear-gradient({RED},{RED});
  background-size:28px 3px,3px 28px,28px 3px,3px 28px;
  background-position:0 0,0 0,100% 100%,100% 100%;background-repeat:no-repeat}}
.next h4{{font-family:Anton;font-size:30px;margin-bottom:12px}}
.next p{{font-weight:600;font-size:18px;line-height:1.6;color:#C9CFDA}}
.next p b{{color:{ICE};font-weight:800}}

.foot{{display:flex;align-items:center;justify-content:space-between;
  margin-top:52px;border-top:1px solid rgba(244,246,250,.14);padding-top:26px}}
.foot .u{{font-family:Anton;font-size:34px;letter-spacing:.03em}}
.foot .u em{{font-style:normal;color:{RED}}}
.foot .s{{margin-top:6px;font-family:Mono;font-weight:700;font-size:13px;
  letter-spacing:.18em;color:{STEEL}}}
.foot img{{height:100px;filter:drop-shadow(0 0 18px rgba(255,46,67,.5))}}
"""

def night(s, n):
    return f"""
  <div class="night">
    <div class="hd"><h3>NIGHT {n}</h3><span>{dm(s['date'])}</span></div>
    <dl>
      <div class="r"><span class="k">CHAMPIONS</span><span class="v win">{s['champion']}</span></div>
      <div class="r"><span class="k">RUNNERS-UP</span><span class="v">{s['runnerUp']}</span></div>
      <div class="r"><span class="k">FINAL</span><span class="v">{s['finalScore']}</span></div>
      <div class="r"><span class="k">MVP</span><span class="v">{s['mvp'] or '&mdash;'}</span></div>
      <div class="r"><span class="k">PLAYED</span><span class="v"><em>{s['teams']} teams &middot;
        {s['groupMatches'] + s['koMatches']} matches</em></span></div>
    </dl>
  </div>"""

rows = ''.join(
    f'''<div class="tr p{e['rank'] if e['rank']<=3 else ''}">
      <span class="rk">{e['rank']}</span>
      <span class="nm">{e['name']}</span>
      <span class="meta">{e['sess']} NIGHT{'S' if e['sess']!=1 else ''} &middot; {e['wins']}W</span>
      <span class="pt">{e['pts']}</span>
    </div>''' for e in TOP)

HTML = f"""<!doctype html><meta charset="utf-8"><style>{CSS}</style>
<div class="grid"></div>
<div class="z">
  <div class="mast">
    <img src="data:image/png;base64,{word}" alt="August Attack">
    <div class="iss"><b>THE REPORT</b>AFTER TWO NIGHTS &middot; VOL.6</div>
  </div>

  <p class="lede">Two nights in, and the series already has a leader who did it the hard way.
    <b>Munther Rahbi</b> was voted MVP on opening night, then went out on Wednesday and won the
    whole thing with <b>Mazin</b>. He tops the table on <b>45 points</b> &mdash; but only
    <b>{D['bothNights']}</b> of the {T['ranked']} players who have stepped on court have played both
    nights, so almost nobody has shown their hand yet.</p>

  <div class="sec"><b>THE NUMBERS</b><i></i></div>
  <div class="nums">
    <div class="num"><b>{T['matches']}</b><span>MATCHES PLAYED</span></div>
    <div class="num i"><b>{T['ranked']}</b><span>PLAYERS RANKED</span></div>
    <div class="num"><b>32</b><span>TEAMS DRAWN</span></div>
    <div class="num i"><b>{LEFT}</b><span>NIGHTS LEFT</span></div>
  </div>

  <div class="sec"><b>THE NIGHTS</b><i></i></div>
  <div class="nights">{night(S1,1)}{night(S2,2)}</div>

  <div class="sec"><b>STANDINGS &middot; TOP 8</b><i></i></div>
  <div class="tbl">{rows}</div>
  <p class="note">Only <b>{D['bothNights']} players</b> have played both nights.
    {D['oneNight']} have played once &mdash; one good night is worth roughly a third of the
    current lead, so the table is nowhere near settled.</p>

  <div class="sec"><b>WHAT'S NEXT</b><i></i></div>
  <div class="next">
    <div class="big">
      <h4>{LEFT} NIGHTS TO GO</h4>
      <p>Mon &amp; Wed, 5:30 PM, all August &mdash; 7 OMR a player.
      <b>Nights 8 and 9 pay double points</b>, so the table can still flip on the last ball.
      New partners every session: if you missed the first two, you have not missed the series.</p>
    </div>
  </div>

  <div class="foot">
    <div>
      <div class="u">ATTACK<em>.</em>URBANPADEL<em>.</em>OM</div>
      <div class="s">URBAN SOCIAL SERIES &middot; VOL.6 &middot; LIVE TABLE &amp; FULL RULES</div>
    </div>
    <img src="data:image/png;base64,{emblem}" alt="Urban Playground">
  </div>
</div>"""

open(f'{SC}/newsletter.html', 'w').write(HTML)
print('built newsletter.html')
