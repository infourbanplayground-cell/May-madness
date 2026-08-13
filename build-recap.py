# -*- coding: utf-8 -*-
"""AUGUST ATTACK — weekly recap video (Instagram story, 1080x1920).

Seven scenes cross-fading over 22.5s. Every element animates on a fixed delay
with `both` fill, so the page is a pure function of time and the recorder can
pause the timeline and scrub to an exact frame (see record-recap.mjs).

Nothing here is typed in. The champions come out of each session's bracket
final, the winners' route comes out of their own group and knockout matches,
and every number on the stats scenes comes from week_stats.json, which is
computed by week-stats.cjs using the app's OWN scoring engine (aa_score.cjs).
That matters: if the video and the RANK tab disagree, someone is wrong in
public, so both read the same code.

  node week-stats.cjs && python3 build_recap.py && node record-recap.mjs
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
W      = json.load(open(f'{SC}/week_stats.json'))
names  = {p['id']: p.get('name') for p in state['players']}
pid    = lambda n: next((k for k, v in names.items() if v == n), None)
photo  = lambda n: photos.get(pid(n))

WEEK = state['sessions'][2:]          # Session 3 (Mon 10) and Session 4 (Wed 12)

def team(s, tid):
    for t in s.get('teams', []):
        if t['id'] == tid:
            return t
    return None

def pair(s, tid):
    t = team(s, tid)
    return [names.get(t.get('p1Id'), '?'), names.get(t.get('p2Id'), '?')] if t else ['?', '?']

def champ(s):
    """The winning pair of a session, straight out of the bracket final."""
    f = s['bracket']['final']
    return pair(s, f['team1Id'] if f['winner'] == 'team1' else f['team2Id'])

def champ_team_id(s):
    f = s['bracket']['final']
    return f['team1Id'] if f['winner'] == 'team1' else f['team2Id']

def final_score(s):
    sc = s['bracket']['final']['score']
    return max(sc['t1'], sc['t2']), min(sc['t1'], sc['t2'])

mon, wed = WEEK[0], WEEK[1]
mon_win, wed_win = champ(mon), champ(wed)
mon_hi, mon_lo = final_score(mon)
wed_hi, wed_lo = final_score(wed)

def route(s, tid):
    """Every decided match a team played, in the order they played it."""
    legs, b = [], s.get('bracket', {})
    src = ([('GROUP', m) for m in s.get('groupMatches', [])]
           + [('QUARTER', m) for m in b.get('qf', [])]
           + [('SEMI', m) for m in b.get('sf', [])]
           + ([('FINAL', b['final'])] if b.get('final') else []))
    for label, m in src:
        if not m.get('winner') or tid not in (m.get('team1Id'), m.get('team2Id')):
            continue
        us_t1 = m['team1Id'] == tid
        opp = pair(s, m['team2Id'] if us_t1 else m['team1Id'])
        mine = m['score']['t1'] if us_t1 else m['score']['t2']
        theirs = m['score']['t2'] if us_t1 else m['score']['t1']
        legs.append((label, f'{opp[0]} &amp; {opp[1]}', f'{mine}&ndash;{theirs}',
                     mine > theirs))
    return legs

WED_ROUTE = route(wed, champ_team_id(wed))
WED_WON_ALL = all(w for *_, w in WED_ROUTE)

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
.score{{margin-top:22px;font-family:Mono;font-weight:700;font-size:26px;
  letter-spacing:.16em;color:{CHALK}}}

.flash{{font-family:Anton;font-size:88px;line-height:1.02;color:{RED};
  text-shadow:0 0 60px rgba(255,46,67,.75)}}
.route{{width:100%;margin-top:28px;background:rgba(16,20,32,.94);padding:6px 28px 8px;
  background-image:linear-gradient({ICE},{ICE}),linear-gradient({ICE},{ICE}),
    linear-gradient({RED},{RED}),linear-gradient({RED},{RED});
  background-size:30px 4px,4px 30px,30px 4px,4px 30px;
  background-position:0 0,0 0,100% 100%,100% 100%;background-repeat:no-repeat}}
.rr{{display:flex;align-items:baseline;gap:16px;padding:12px 0;
  border-bottom:1px solid rgba(244,246,250,.08);text-align:left}}
.rr:last-child{{border-bottom:none}}
.rr .r{{flex:none;width:96px;font-family:Mono;font-weight:700;font-size:18px;
  letter-spacing:.12em;color:{RED}}}
.rr .o{{flex:1;font-weight:600;font-size:25px;color:#C9CFDA;line-height:1.25;
  overflow:hidden;text-overflow:ellipsis;white-space:nowrap}}
.rr .s{{flex:none;font-family:Anton;font-size:34px;font-variant-numeric:tabular-nums}}
.tag{{margin-top:22px;font-weight:600;font-size:29px;line-height:1.4;color:#C9CFDA}}
.tag b{{color:{CHALK};font-weight:800}}

/* ---- stats scenes ---- */
.jump{{font-family:Anton;font-size:250px;line-height:.82;color:{ICE};
  font-variant-numeric:tabular-nums;text-shadow:0 0 70px rgba(61,225,255,.55)}}
.jump i{{font-style:normal;font-size:140px;vertical-align:.14em}}
.arrow{{margin-top:26px;font-family:Mono;font-weight:700;font-size:30px;
  letter-spacing:.18em;color:{STEEL}}}
.arrow b{{color:{CHALK};font-family:Anton;font-size:46px;letter-spacing:0;
  vertical-align:-.04em}}

.cards{{width:100%;display:flex;flex-direction:column;gap:16px;margin-top:40px}}
.cd{{background:rgba(16,20,32,.94);padding:24px 30px;display:flex;
  align-items:center;gap:24px;text-align:left;box-shadow:inset 4px 0 0 {RED}}}
.cd .k{{flex:1}}
.cd .k u{{display:block;text-decoration:none;font-family:Mono;font-weight:700;
  font-size:17px;letter-spacing:.16em;color:{STEEL}}}
.cd .k strong{{display:block;margin-top:7px;font-family:Anton;font-weight:400;
  font-size:44px;line-height:1.06}}
.cd .v{{flex:none;font-family:Anton;font-size:60px;line-height:1;color:{ICE};
  font-variant-numeric:tabular-nums}}
.cd.ice{{box-shadow:inset 4px 0 0 {ICE}}}
.cd.ice .v{{color:{RED}}}

.tbl{{width:100%;margin-top:40px}}
.tr{{display:flex;align-items:center;gap:24px;padding:24px 30px;
  background:rgba(16,20,32,.94);margin-bottom:14px;text-align:left}}
.tr .p{{flex:none;width:74px;font-family:Anton;font-size:56px;line-height:1;
  color:{STEEL};font-variant-numeric:tabular-nums}}
.tr .n{{flex:1;font-family:Anton;font-weight:400;font-size:52px;line-height:1.06}}
.tr .pt{{flex:none;font-family:Mono;font-weight:700;font-size:34px;
  font-variant-numeric:tabular-nums;color:{ICE}}}
.tr.one{{box-shadow:inset 0 0 0 3px {RED}}}
.tr.one .p{{color:{RED}}}

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
TOTAL = 22.5
SCENES = [(0.0, 3.0), (2.7, 6.3), (6.0, 9.0), (8.7, 13.5),
          (13.2, 16.2), (15.9, 19.5), (19.2, 22.5)]
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
for j in range(1, 4):
    CSS += anim(f'#s2 .rowstat div:nth-child({j})', 'up', .5, 3.9 + .15 * (j - 1))

CSS += anim('#s3 .day', 'up', .45, 6.3)
CSS += anim('#s3 .duo', 'up', .55, 6.55)
CSS += anim('#s3 .nm', 'up', .55, 6.8)
CSS += anim('#s3 .score', 'up', .5, 7.15)

CSS += anim('#s4 .day', 'up', .45, 9.0)
CSS += anim('#s4 .duo', 'up', .55, 9.2)
CSS += anim('#s4 .nm', 'up', .55, 9.45)
CSS += anim('#s4 .flash', 'slam', .8, 9.8, ', glow 2.4s ease-in-out 10.6s infinite')
CSS += anim('#s4 .route', 'up', .6, 10.4)
CSS += anim('#s4 .tag', 'up', .5, 11.0)

CSS += anim('#s5 .lab', 'up', .45, 13.5)
CSS += anim('#s5 .jump', 'slam', .75, 13.7)
CSS += anim('#s5 .arrow', 'up', .5, 14.4)
CSS += anim('#s5 .tag', 'up', .5, 14.7)

CSS += anim('#s6 .lab', 'up', .45, 16.2)
for j in range(1, 5):
    CSS += anim(f'#s6 .cd:nth-child({j})', 'up', .5, 16.45 + .16 * (j - 1))

CSS += anim('#s7 .lab', 'up', .45, 19.5)
for j in range(1, 4):
    CSS += anim(f'#s7 .tr:nth-child({j})', 'up', .5, 19.75 + .16 * (j - 1))
CSS += anim('#s7 .score', 'up', .5, 20.4)
CSS += anim('.foot', 'up', .5, 20.8)

cl, big, mw, br = W['topClimber'], W['biggest'], W['mostWins'], W['bestRate']

CARDS = [
    ('MOST WINS', f"{mw['name']}", f"{mw['w']}<span style='font-size:34px'>W</span>", ''),
    ('BEST WIN RATE', f"{br['name']}", f"{br['rate']}<span style='font-size:34px'>%</span>", 'ice'),
    ('BIGGEST WIN', big['winner'], big['score'].replace('-', '&ndash;'), ''),
    ('NAIL-BITERS', 'Decided by one game', str(W['oneGameThrillers']), 'ice'),
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
  <div class="big">{W['matches']}</div>
  <div class="sub">MATCHES PLAYED</div>
  <div class="rowstat">
    <div><b>{W['teams']}</b><span>TEAMS</span></div>
    <div><b>{W['players']}</b><span>PLAYERS</span></div>
    <div><b>{W['games']}</b><span>GAMES</span></div>
  </div>
</div>

<div class="sc" id="s3">
  <div class="day">MONDAY &middot; SESSION 3</div>
  <div class="duo">{av(mon_win[0], 190)}{av(mon_win[1], 190)}</div>
  <div class="nm">{mon_win[0]}<br><em>&amp;</em> {mon_win[1]}</div>
  <div class="score">CHAMPIONS &middot; WON THE FINAL {mon_hi}&ndash;{mon_lo}</div>
</div>

<div class="sc" id="s4">
  <div class="day">WEDNESDAY &middot; SESSION 4</div>
  <div class="duo">{av(wed_win[0], 160)}{av(wed_win[1], 160)}</div>
  <div class="nm">{wed_win[0]} <em>&amp;</em> {wed_win[1].split()[0]}</div>
  <div class="flash">FIRST EVER WIN</div>
  <div class="route">
    {''.join(f'<div class="rr"><span class="r">{r}</span><span class="o">{o}</span><span class="s">{s}</span></div>' for r, o, s, _ in WED_ROUTE)}
  </div>
  <div class="tag">Four sessions, no title &mdash; then
    <b>{'won every match' if WED_WON_ALL else 'all the way to the title'}</b>. Amour is <b>14</b>.</div>
</div>

<div class="sc" id="s5">
  <div class="lab">BIGGEST CLIMB</div>
  <div class="jump"><i>&#9650;</i>{cl['delta']}</div>
  <div class="arrow">{cl['name'].upper()} &nbsp;&middot;&nbsp; UP TO <b>#{cl['rank']}</b></div>
  <div class="tag">One night moved him <b>{cl['delta']} places</b> up the series table.</div>
</div>

<div class="sc" id="s6">
  <div class="lab">THE WEEK IN NUMBERS</div>
  <div class="cards">
    {''.join(f'<div class="cd {c}"><div class="k"><u>{k}</u><strong>{n}</strong></div><div class="v">{v}</div></div>' for k, n, v, c in CARDS)}
  </div>
</div>

<div class="sc" id="s7">
  <div class="lab">SERIES TABLE &middot; TOP 3</div>
  <div class="tbl">
    {''.join(f'<div class="tr{" one" if p["rank"] == 1 else ""}"><span class="p">{p["rank"]}</span><span class="n">{p["name"]}</span><span class="pt">{p["points"]} PTS</span></div>' for p in W['top3'])}
  </div>
  <div class="score">{W['ranked']} PLAYERS RANKED &middot; SEE THE FULL TABLE</div>
</div>

<div class="foot">ATTACK<em>.</em>URBANPADEL<em>.</em>OM</div>"""

open(f'{SC}/recap.html', 'w').write(HTML)
print('built recap.html')
print(f'  monday   : {" & ".join(mon_win)}  {mon_hi}-{mon_lo}')
print(f'  wednesday: {" & ".join(wed_win)}  {wed_hi}-{wed_lo}  unbeaten={WED_WON_ALL}')
for r, o, s, w in WED_ROUTE:
    print(f'    {r:8} {o:38} {s}  {"W" if w else "L"}')
print(f'  week     : {W["matches"]} matches, {W["games"]} games, {W["players"]} players')
print(f'  climber  : {cl["name"]} +{cl["delta"]} to #{cl["rank"]}')
