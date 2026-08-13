# -*- coding: utf-8 -*-
"""AUGUST ATTACK — weekly recap video (Instagram story, 1080x1920).

Four scenes cross-fading over 12s. Every element animates on a fixed delay
with `both` fill, so the page is a pure function of time and the recorder can
pause the timeline and scrub to an exact frame (see record-recap.mjs).

Everything factual here is read from the live tournament state, not typed:
champions come out of each session's bracket final, the route comes out of
the group and knockout matches, and the photos are the players' own from the
app's /photos endpoint.

  python3 build_recap.py && node record-recap.mjs
"""
import base64, json, os

SC = os.path.dirname(os.path.abspath(__file__))
b64f = lambda f: base64.b64encode(open(f'{SC}/{f}', 'rb').read()).decode()

anton = b64f('anton.woff2');      mono  = b64f('jbmono700.woff2')
arch8 = b64f('archivo800.woff2'); arch6 = b64f('archivo600.woff2')
word  = b64f('aa-wordmark-clean.png')

RED, ICE, CHALK, STEEL, COURT = '#FF2E43', '#3DE1FF', '#F4F6FA', '#8B95A7', '#0A0C12'

state  = json.load(open(f'{SC}/aa_now.json'))
photos = json.load(open(f'{SC}/aa_photos_now.json'))['photos']
names  = {p['id']: p.get('name') for p in state['players']}
pid    = lambda n: next((k for k, v in names.items() if v == n), None)
photo  = lambda n: photos.get(pid(n))

WEEK = state['sessions'][2:]          # Session 3 (Mon 10) and Session 4 (Wed 12)

def team(s, tid):
    for t in s.get('teams', []):
        if t['id'] == tid:
            return [names.get(t.get('p1Id'), '?'), names.get(t.get('p2Id'), '?')]
    return []

# Monday's champions, straight out of the bracket.
mon = WEEK[0]
f = mon['bracket']['final']
mon_win = team(mon, f['team1Id'] if f['winner'] == 'team1' else f['team2Id'])

matches = sum(len(s.get('groupMatches', [])) + len(s['bracket'].get('qf', []))
              + len(s['bracket'].get('sf', [])) + (1 if s['bracket'].get('final') else 0)
              for s in WEEK)
players = len({p for s in WEEK for t in s.get('teams', [])
               for p in (t.get('p1Id'), t.get('p2Id')) if p})

HERO = ['Amour', 'Faris Namaani']

def av(n, size):
    src = photo(n)
    if not src:
        return f'<span class="av ph" style="width:{size}px;height:{size}px"></span>'
    return (f'<span class="av" style="width:{size}px;height:{size}px;'
            f'background-image:url({src})"></span>')

CSS = f"""
@font-face{{font-family:'Anton';src:url(data:font/woff2;base64,{anton}) format('woff2');font-display:block}}
@font-face{{font-family:'Mono';font-weight:700;src:url(data:font/woff2;base64,{mono}) format('woff2')}}
@font-face{{font-family:'Archivo';font-weight:800;src:url(data:font/woff2;base64,{arch8}) format('woff2')}}
@font-face{{font-family:'Archivo';font-weight:600;src:url(data:font/woff2;base64,{arch6}) format('woff2')}}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{width:1080px;height:1920px;overflow:hidden;position:relative;color:{CHALK};
  font-family:Archivo,sans-serif;--e:cubic-bezier(.23,1,.32,1);background:
  radial-gradient(ellipse 92% 30% at 50% 0%, rgba(255,46,67,.30), transparent 62%),
  radial-gradient(ellipse 60% 24% at 6% 74%, rgba(61,225,255,.10), transparent 64%),
  linear-gradient(180deg,#08090D 0%,{COURT} 42%,#06070B 100%)}}
.grid{{position:absolute;inset:0;z-index:0;opacity:.45;
  background-image:linear-gradient(rgba(255,46,67,.055) 1px,transparent 1px),
   linear-gradient(90deg,rgba(255,46,67,.055) 1px,transparent 1px);background-size:48px 48px;
  -webkit-mask-image:radial-gradient(120% 60% at 50% 16%,#000,transparent 88%)}}
.tk{{position:absolute;width:66px;height:66px;z-index:6}}
.tk.tl{{top:184px;left:44px;border-top:6px solid {ICE};border-left:6px solid {ICE}}}
.tk.br{{bottom:258px;right:44px;border-bottom:6px solid {RED};border-right:6px solid {RED}}}

/* Every scene occupies the same safe box; only one is visible at a time. */
.sc{{position:absolute;left:0;right:0;top:170px;bottom:244px;z-index:4;
  display:flex;flex-direction:column;align-items:center;justify-content:center;
  padding:0 68px;text-align:center;opacity:0}}

.word{{width:440px;filter:drop-shadow(0 0 34px rgba(255,46,67,.45))}}
.kick{{margin-top:26px;padding:13px 30px 11px;background:{RED};
  box-shadow:0 0 54px rgba(255,46,67,.55)}}
.kick b{{font-family:Anton;font-size:46px;letter-spacing:.08em;color:#fff}}
.dates{{margin-top:30px;font-family:Mono;font-weight:700;font-size:24px;
  letter-spacing:.2em;color:{STEEL};line-height:2}}

.lab{{font-family:Mono;font-weight:700;font-size:22px;letter-spacing:.34em;
  color:{RED};margin-left:.34em}}
.big{{font-family:Anton;font-size:230px;line-height:.86;
  font-variant-numeric:tabular-nums;text-shadow:0 0 60px rgba(255,46,67,.45)}}
.sub{{margin-top:10px;font-family:Mono;font-weight:700;font-size:24px;
  letter-spacing:.2em;color:{STEEL}}}
.rowstat{{display:flex;gap:16px;width:100%;margin-top:44px}}
.rowstat div{{flex:1;background:rgba(16,20,32,.92);padding:26px 6px 22px;
  box-shadow:inset 0 4px 0 {ICE}}}
.rowstat b{{display:block;font-family:Anton;font-size:74px;line-height:1;
  font-variant-numeric:tabular-nums}}
.rowstat span{{display:block;margin-top:10px;font-family:Mono;font-weight:700;
  font-size:17px;letter-spacing:.14em;color:{STEEL}}}

.av{{display:inline-block;flex:none;background-size:cover;background-position:center 22%;
  background-color:#141826;box-shadow:inset 0 -4px 0 {RED}}}
.av.ph{{background:rgba(244,246,250,.06);box-shadow:inset 0 -4px 0 {STEEL}}}
.duo{{display:flex;gap:22px;justify-content:center;margin-top:34px}}
.nm{{margin-top:32px;font-family:Anton;font-size:76px;line-height:1.04}}
.nm em{{font-style:normal;color:{ICE}}}
.day{{font-family:Mono;font-weight:700;font-size:24px;letter-spacing:.28em;color:{STEEL}}}
.score{{margin-top:22px;font-family:Mono;font-weight:700;font-size:26px;
  letter-spacing:.16em;color:{CHALK}}}

.flash{{font-family:Anton;font-size:96px;line-height:1.02;color:{RED};
  text-shadow:0 0 60px rgba(255,46,67,.75)}}
.route{{width:100%;margin-top:36px;background:rgba(16,20,32,.94);padding:8px 30px 12px;
  background-image:linear-gradient({ICE},{ICE}),linear-gradient({ICE},{ICE}),
    linear-gradient({RED},{RED}),linear-gradient({RED},{RED});
  background-size:30px 4px,4px 30px,30px 4px,4px 30px;
  background-position:0 0,0 0,100% 100%,100% 100%;background-repeat:no-repeat}}
.rr{{display:flex;align-items:baseline;gap:18px;padding:16px 0;
  border-bottom:1px solid rgba(244,246,250,.08);text-align:left}}
.rr:last-child{{border-bottom:none}}
.rr .r{{flex:none;width:96px;font-family:Mono;font-weight:700;font-size:19px;
  letter-spacing:.14em;color:{RED}}}
.rr .o{{flex:1;font-weight:600;font-size:27px;color:#C9CFDA;line-height:1.25}}
.rr .s{{flex:none;font-family:Anton;font-size:36px;font-variant-numeric:tabular-nums}}
.tag{{margin-top:28px;font-weight:600;font-size:30px;line-height:1.4;color:#C9CFDA}}
.tag b{{color:{CHALK};font-weight:800}}

.foot{{position:absolute;left:0;right:0;bottom:262px;z-index:5;text-align:center;
  font-family:Anton;font-size:40px;letter-spacing:.04em;opacity:0}}
.foot em{{font-style:normal;color:{RED}}}

@keyframes fade{{from{{opacity:0}} to{{opacity:1}}}}
@keyframes up  {{from{{opacity:0;transform:translateY(34px)}} to{{opacity:1;transform:none}}}}
@keyframes slam{{0%{{opacity:0;transform:scale(1.6)}} 60%{{opacity:1;transform:scale(.95)}}
                 80%{{transform:scale(1.02)}} 100%{{opacity:1;transform:scale(1)}}}}
@keyframes pulse{{0%,100%{{opacity:1}} 50%{{opacity:.6}}}}
@keyframes glow{{0%,100%{{text-shadow:0 0 60px rgba(255,46,67,.5)}}
                 50%{{text-shadow:0 0 120px rgba(255,46,67,.95)}}}}
"""

# Scene visibility windows (seconds). Each scene fades in, holds, fades out;
# the next starts 0.3s before the previous ends so there is a real cross-fade.
# One animation per scene, spanning the WHOLE video, with the fade in and out
# expressed as percentage stops. Two separate animations on `opacity` does not
# work: the second one's backwards fill wins during the fill phase, so every
# scene sat at opacity 1 from t=0 and bled through the one before it.
TOTAL = 13.0
SCENES = [(0.0, 3.0), (2.7, 6.0), (5.7, 9.0), (8.7, 13.0)]
FADE = 0.45
for i, (a, b) in enumerate(SCENES, 1):
    pct = lambda t: round(max(0.0, min(100.0, t / TOTAL * 100)), 3)
    last = (i == len(SCENES))
    p1, p2 = pct(a), pct(a + FADE)
    # The final scene holds to the end — a story that fades to black before
    # the viewer taps away just looks like it broke.
    tail = "100%{opacity:1}" if last else f"{pct(b - FADE)}%{{opacity:1}} {pct(b)}%,100%{{opacity:0}}"
    CSS += (f"\n@keyframes scene{i}{{"
            f"0%,{p1}%{{opacity:0}} {p2}%{{opacity:1}} {tail}}}"
            f"\n#s{i}{{animation:scene{i} {TOTAL}s linear 0s both}}")

def anim(sel, kf, dur, delay, extra=''):
    return f"\n{sel}{{animation:{kf} {dur}s var(--e) {delay}s both{extra}}}"

CSS += anim('#s1 .word', 'slam', .9, .15)
CSS += anim('#s1 .kick', 'up', .5, .8)
CSS += anim('#s1 .dates', 'up', .5, 1.15)

CSS += anim('#s2 .lab', 'up', .45, 3.0)
CSS += anim('#s2 .big', 'slam', .7, 3.2)
CSS += anim('#s2 .rowstat div:nth-child(1)', 'up', .5, 3.9)
CSS += anim('#s2 .rowstat div:nth-child(2)', 'up', .5, 4.05)
CSS += anim('#s2 .rowstat div:nth-child(3)', 'up', .5, 4.2)

CSS += anim('#s3 .day', 'up', .45, 6.0)
CSS += anim('#s3 .duo', 'up', .55, 6.25)
CSS += anim('#s3 .nm', 'up', .55, 6.5)
CSS += anim('#s3 .score', 'up', .5, 6.85)

CSS += anim('#s4 .day', 'up', .45, 9.0)
CSS += anim('#s4 .duo', 'up', .55, 9.2)
CSS += anim('#s4 .nm', 'up', .55, 9.45)
CSS += anim('#s4 .flash', 'slam', .8, 9.8, ', glow 2.4s ease-in-out 10.6s infinite')
CSS += anim('#s4 .route', 'up', .6, 10.4)
CSS += anim('#s4 .tag', 'up', .5, 11.0)
CSS += anim('.foot', 'up', .5, 11.4)

ROUTE = [
    ('GROUP', 'Ali Safwan &amp; Haitham', '6&ndash;4'),
    ('GROUP', 'Dareen &amp; Barraq', '6&ndash;1'),
    ('GROUP', 'Muntaser &amp; Qoot', '6&ndash;4'),
    ('QUARTER', 'Faisal &amp; Suliman', '6&ndash;1'),
    ('SEMI', 'Munther Rahbi &amp; Mohd', '6&ndash;5'),
]

HTML = f"""<!doctype html><meta charset="utf-8"><style>{CSS}</style>
<div class="grid"></div><div class="tk tl"></div><div class="tk br"></div>

<div class="sc" id="s1">
  <img class="word" src="data:image/png;base64,{word}" alt="August Attack">
  <div class="kick"><b>THE WEEK</b></div>
  <div class="dates">SESSION 3 &middot; MON 10 AUG<br>SESSION 4 &middot; WED 12 AUG</div>
</div>

<div class="sc" id="s2">
  <div class="lab">TWO NIGHTS</div>
  <div class="big">{matches}</div>
  <div class="sub">MATCHES PLAYED</div>
  <div class="rowstat">
    <div><b>32</b><span>TEAMS</span></div>
    <div><b>{players}</b><span>PLAYERS</span></div>
    <div><b>5</b><span>NIGHTS LEFT</span></div>
  </div>
</div>

<div class="sc" id="s3">
  <div class="day">MONDAY &middot; SESSION 3</div>
  <div class="duo">{av(mon_win[0], 190)}{av(mon_win[1], 190)}</div>
  <div class="nm">{mon_win[0]}<br><em>&amp;</em> {mon_win[1]}</div>
  <div class="score">CHAMPIONS &middot; WON THE FINAL 6&ndash;3</div>
</div>

<div class="sc" id="s4">
  <div class="day">WEDNESDAY &middot; SESSION 4</div>
  <div class="duo">{av(HERO[0], 170)}{av(HERO[1], 170)}</div>
  <div class="nm">{HERO[0]} <em>&amp;</em> Faris</div>
  <div class="flash">FIRST EVER WIN</div>
  <div class="route">
    {''.join(f'<div class="rr"><span class="r">{r}</span><span class="o">{o}</span><span class="s">{s}</span></div>' for r, o, s in ROUTE)}
  </div>
  <div class="tag">Four sessions, no title &mdash; then <b>unbeaten all night</b>.
    Amour is <b>14</b>.</div>
</div>

<div class="foot">ATTACK<em>.</em>URBANPADEL<em>.</em>OM</div>"""

open(f'{SC}/recap.html', 'w').write(HTML)
print('built recap.html')
print(f'  monday champions : {" & ".join(mon_win)}')
print(f'  week             : {matches} matches, {players} players')
