# -*- coding: utf-8 -*-
"""AUGUST ATTACK — the report as an animated Instagram story (1080x1920).

Six scenes over 18s. Every scene's visibility is driven by ONE animation that
spans the whole timeline, with keyframe percentages marking its window — that
makes the whole thing seekable to an exact millisecond, so frame capture is
deterministic rather than dependent on how fast screenshots come back.

Content is laid out inside Instagram's safe area (250px top and bottom).
Same figures and the same photos as the printed report.
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
OLD= json.load(open(f'{SC}/news_stats.json'))
T, TOP = OLD['totals'], D['top'][:5]
C1, C2 = D['champions'][0], D['champions'][1]
LEFT = 9 - len(OLD['sessions'])

RED, ICE, CHALK, STEEL, COURT, GREEN = '#FF2E43','#3DE1FF','#F4F6FA','#8B95A7','#0A0C12','#27E08A'
DUR = 18000
# scene windows in ms
W = [(0,2900),(2900,6100),(6100,9400),(9400,12300),(12300,15400),(15400,18000)]
pct = lambda ms: round(ms / DUR * 100, 3)

def av(pid, size, accent=RED):
    src = PH.get(pid)
    if not src: return f'<span class="av ph" style="width:{size}px;height:{size}px"></span>'
    return (f'<span class="av" style="width:{size}px;height:{size}px;'
            f'background-image:url({src});box-shadow:inset 0 -4px 0 {accent}"></span>')

def scene_kf(i):
    """One animation per scene spanning the full timeline: hidden, rise in,
    hold, fall out, hidden. Percentages come from the window table."""
    a, b = W[i]
    ei, eo = 520, 420                      # enter / exit
    p0, p1, p2, p3 = pct(a), pct(a+ei), pct(b-eo), pct(b)
    return f"""@keyframes sc{i}{{
  0%,{p0}%{{opacity:0;transform:translateY(26px);visibility:hidden}}
  {p0+.001}%{{visibility:visible}}
  {p1}%{{opacity:1;transform:none}}
  {p2}%{{opacity:1;transform:none}}
  {p3}%{{opacity:0;transform:translateY(-18px);visibility:hidden}}
  100%{{opacity:0;visibility:hidden}}
}}"""

CSS = f"""
@font-face{{font-family:'Anton';src:url(data:font/woff2;base64,{anton}) format('woff2');font-display:block}}
@font-face{{font-family:'Mono';font-weight:700;src:url(data:font/woff2;base64,{mono}) format('woff2')}}
@font-face{{font-family:'Archivo';font-weight:800;src:url(data:font/woff2;base64,{arch8}) format('woff2')}}
@font-face{{font-family:'Archivo';font-weight:600;src:url(data:font/woff2;base64,{arch6}) format('woff2')}}
@property --n1 {{ syntax:'<integer>'; initial-value:0; inherits:false }}
@property --n2 {{ syntax:'<integer>'; initial-value:0; inherits:false }}
@property --n3 {{ syntax:'<integer>'; initial-value:0; inherits:false }}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{width:1080px;height:1920px;overflow:hidden;position:relative;color:{CHALK};
  font-family:Archivo,sans-serif;background:
  radial-gradient(ellipse 92% 30% at 50% 2%, rgba(255,46,67,.30), transparent 62%),
  radial-gradient(ellipse 62% 24% at 8% 70%, rgba(61,225,255,.11), transparent 64%),
  linear-gradient(180deg,#08090D 0%,{COURT} 50%,#06070B 100%)}}
.grid{{position:absolute;inset:0;opacity:.5;
  background-image:linear-gradient(rgba(255,46,67,.055) 1px,transparent 1px),
   linear-gradient(90deg,rgba(255,46,67,.055) 1px,transparent 1px);background-size:46px 46px;
  -webkit-mask-image:radial-gradient(120% 60% at 50% 26%,#000,transparent 88%)}}
.tk{{position:absolute;width:70px;height:70px;z-index:6}}
.tl{{top:250px;left:52px;border-top:5px solid {ICE};border-left:5px solid {ICE}}}
.br{{bottom:250px;right:52px;border-bottom:5px solid {RED};border-right:5px solid {RED}}}

/* every scene occupies the same safe box; only one is visible at a time */
.sc{{position:absolute;left:0;right:0;top:250px;bottom:250px;padding:0 84px;
  display:flex;flex-direction:column;align-items:center;justify-content:center;
  text-align:center;opacity:0;visibility:hidden;
  animation-duration:{DUR}ms;animation-timing-function:cubic-bezier(.23,1,.32,1);
  animation-fill-mode:none;animation-iteration-count:1}}
{''.join(f'.sc{i}{{animation-name:sc{i}}}' for i in range(6))}
{''.join(scene_kf(i) for i in range(6))}

.av{{display:inline-block;flex:none;background-size:cover;background-position:center 22%;
  background-color:#141826}}
.av.ph{{background:rgba(244,246,250,.06);box-shadow:inset 0 -4px 0 {STEEL}}}

.kick{{display:inline-flex;align-items:center;gap:14px;font-weight:800;font-size:19px;
  letter-spacing:.34em;color:{STEEL};text-transform:uppercase}}
.kick i{{width:5px;height:19px;background:{RED};box-shadow:0 0 10px {RED};display:block}}
.word{{width:660px;margin:30px 0 26px;filter:drop-shadow(0 0 34px rgba(255,46,67,.45))}}
.title{{font-family:Anton;font-size:96px;line-height:.98;letter-spacing:.02em;
  text-shadow:-3px 0 {RED},3px 0 {ICE}}}
.sub{{margin-top:22px;font-family:Mono;font-weight:700;font-size:22px;letter-spacing:.22em;color:{ICE}}}

.h{{font-family:Mono;font-weight:700;font-size:19px;letter-spacing:.3em;color:{RED};
  margin-bottom:40px}}

.nums{{display:flex;flex-wrap:wrap;gap:20px;width:100%;justify-content:center}}
.num{{width:calc(50% - 10px);background:rgba(16,20,32,.92);padding:34px 10px 28px;
  box-shadow:inset 0 4px 0 {RED}}}
.num.i{{box-shadow:inset 0 4px 0 {ICE}}}
.num b{{display:block;font-family:Anton;font-size:104px;line-height:.9;font-variant-numeric:tabular-nums}}
.num.i b{{color:{ICE}}}
.num span{{display:block;margin-top:14px;font-family:Mono;font-weight:700;font-size:16px;
  letter-spacing:.16em;color:{STEEL}}}
/* counter-reset must sit on the element carrying the animated custom
   property: @property ... inherits:false means ::after never sees it */
.n1{{counter-reset:n var(--n1)}} .n1::after{{content:counter(n)}}
.n2{{counter-reset:n var(--n2)}} .n2::after{{content:counter(n)}}
.n3{{counter-reset:n var(--n3)}} .n3::after{{content:counter(n)}}
.sc1 .n1{{animation:c1 1100ms {W[1][0]+400}ms cubic-bezier(.23,1,.32,1) both}}
.sc1 .n2{{animation:c2 1100ms {W[1][0]+560}ms cubic-bezier(.23,1,.32,1) both}}
.sc1 .n3{{animation:c3 1100ms {W[1][0]+720}ms cubic-bezier(.23,1,.32,1) both}}
@keyframes c1{{to{{--n1:{T['matches']}}}}}
@keyframes c2{{to{{--n2:{T['ranked']}}}}}
@keyframes c3{{to{{--n3:{D['debutants']}}}}}

.hero{{display:flex;align-items:center;gap:34px;width:100%;text-align:left;
  background:rgba(16,20,32,.94);padding:34px 36px;margin-bottom:22px;
  background-image:linear-gradient({RED},{RED}),linear-gradient({RED},{RED});
  background-size:30px 4px,4px 30px;background-position:0 0,0 0;background-repeat:no-repeat}}
.hero.i{{background-image:linear-gradient({ICE},{ICE}),linear-gradient({ICE},{ICE})}}
.hero .k{{font-family:Mono;font-weight:700;font-size:16px;letter-spacing:.22em;color:{RED}}}
.hero.i .k{{color:{ICE}}}
.hero .n{{font-family:Anton;font-size:52px;line-height:1.05;margin-top:8px}}
.hero .d{{font-weight:600;font-size:23px;color:{STEEL};margin-top:8px;line-height:1.4}}
.hero .d em{{font-style:normal;color:{CHALK};font-weight:800}}

.row{{display:flex;align-items:center;gap:22px;width:100%;padding:20px 26px;
  background:rgba(16,20,32,.92);margin-bottom:14px;text-align:left}}
.row.p1{{box-shadow:inset 5px 0 0 {RED}}}
.row .rk{{font-family:Anton;font-size:40px;width:56px;color:{STEEL};flex:none;text-align:center}}
.row.p1 .rk{{color:{RED}}}
.row .nm{{flex:1;font-family:Anton;font-size:38px;white-space:nowrap;overflow:hidden;
  text-overflow:ellipsis}}
.row .pt{{font-family:Anton;font-size:44px;flex:none;font-variant-numeric:tabular-nums}}
.row.p1 .pt{{color:{RED}}}

.big{{font-family:Anton;font-size:118px;line-height:.95;color:{RED};
  text-shadow:0 0 50px rgba(255,46,67,.8)}}
.out{{font-weight:600;font-size:28px;line-height:1.55;color:#C9CFDA;max-width:820px;margin-top:20px}}
.out b{{color:{ICE};font-weight:800}}
.url{{margin-top:38px;font-family:Anton;font-size:44px;letter-spacing:.03em}}
.url em{{font-style:normal;color:{RED}}}
.emb{{width:132px;margin-top:30px;filter:drop-shadow(0 0 20px rgba(255,46,67,.55))}}
"""

def duo(c, size=120):
    return f'<div style="display:flex;gap:16px;justify-content:center">{av(c["p1"],size)}{av(c["p2"],size)}</div>'

rows = ''.join(f'''<div class="row {'p1' if e['rank']==1 else ''}">
  <span class="rk">{e['rank']}</span>{av(e['id'],64, RED if e['rank']==1 else STEEL)}
  <span class="nm">{e['name']}</span><span class="pt">{e['pts']}</span></div>''' for e in TOP)

HTML = f"""<!doctype html><meta charset="utf-8"><style>{CSS}</style>
<div class="grid"></div><div class="tk tl"></div><div class="tk br"></div>

<div class="sc sc0">
  <span class="kick"><i></i>Urban Playground &middot; Vol.6</span>
  <img class="word" src="data:image/png;base64,{word}" alt="August Attack">
  <div class="title">THE REPORT</div>
  <div class="sub">AFTER TWO NIGHTS</div>
</div>

<div class="sc sc1">
  <div class="h">THE NUMBERS</div>
  <div class="nums">
    <div class="num"><b class="n1"></b><span>MATCHES PLAYED</span></div>
    <div class="num i"><b class="n2"></b><span>PLAYERS RANKED</span></div>
    <div class="num"><b class="n3"></b><span>SERIES DEBUTANTS</span></div>
    <div class="num i"><b>{LEFT}</b><span>NIGHTS LEFT</span></div>
  </div>
</div>

<div class="sc sc2">
  <div class="h">HIGHLIGHTS</div>
  <div class="hero">{av(D['leader']['id'],118)}
    <div><div class="k">SERIES LEADER</div><div class="n">{D['leader']['name']}</div>
    <div class="d">MVP night one, champion night two &mdash; <em>{D['leader']['pts']} pts</em></div></div></div>
  <div class="hero i">{av(D['topClimber']['id'],118,ICE)}
    <div><div class="k">BIGGEST CLIMBER</div><div class="n">{D['topClimber']['name']}</div>
    <div class="d">Up <em>{D['topClimber']['delta']} places</em> after the night-two title</div></div></div>
</div>

<div class="sc sc3">
  <div class="h">CHAMPIONS ON DEBUT</div>
  {duo(C1,150)}
  <div style="font-family:Anton;font-size:56px;margin-top:26px;line-height:1.1">{C1['label']}</div>
  <div class="out">Won the opening night on their <b>first ever</b> Urban Playground appearance.</div>
  <div style="margin-top:44px;font-family:Mono;font-weight:700;font-size:18px;letter-spacing:.22em;color:{STEEL}">
    NIGHT TWO &middot; <span style="color:{CHALK}">{C2['label']}</span></div>
</div>

<div class="sc sc4">
  <div class="h">STANDINGS &middot; TOP 5</div>
  {rows}
</div>

<div class="sc sc5">
  <div class="big">{LEFT} NIGHTS<br>TO GO</div>
  <div class="out">Mon &amp; Wed &middot; 5:30 PM &middot; all August.
    <b>Nights 8 &amp; 9 pay double</b> &mdash; the table can still flip on the last ball.
    Miss the first two? You have not missed the series.</div>
  <div class="url">ATTACK<em>.</em>URBANPADEL<em>.</em>OM</div>
  <img class="emb" src="data:image/png;base64,{emblem}" alt="Urban Playground">
</div>"""

open(f'{SC}/story-report.html', 'w').write(HTML)
print(f'built story-report.html — {DUR/1000:.0f}s, {len(W)} scenes')
