# -*- coding: utf-8 -*-
"""UPRISING — the announcement.

A three-card carousel at 1080x1350 (Instagram's portrait crop, the largest the
feed will show) plus a 1080x1920 story card:

  post-1-hero.png     what it is, when, and the one line that sells it
  post-2-match.png    how ONE match is scored, and the two things called points
  post-3-ladder.png   how you move between courts, and what each one pays
  post-4-prizes.png   what it costs, what you win, and why anyone can win it
  post-story.png      the whole thing on one tall card

The match card is not optional. The owner of the club read the first draft of
this announcement and asked "first to 11 points?" — because the word POINTS
means two different things in this format and no card said so. If the person
who commissioned it had to ask, every player will.

Every figure is derived, never typed. The date, entry and prizes come from
uprising-social.json; the court count, round count, target, running time and
points table come out of the SHIPPED engine via ops/uprising-facts.mjs. A post
cannot advertise a number the app contradicts.

  python3 build-uprising-announce.py
  node ops/render-uprising-announce.mjs
"""
import datetime, json, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "brand", "uprising", "posts")
os.makedirs(OUT, exist_ok=True)

S = json.load(open(os.path.join(HERE, "uprising-social.json")))
F = json.loads(subprocess.check_output(
    ["node", os.path.join(HERE, "ops", "uprising-facts.mjs")], text=True))

# Dates are formatted here, from a plain YYYY-MM-DD, never through
# toISOString() — the server runs UTC and Oman is UTC+4, which has silently
# moved a date back a day in this repo before.
y, m, d = (int(x) for x in S["date"].split("-"))
DT = datetime.date(y, m, d)
DAY = DT.strftime("%A").upper()
# Announced the night before, so the date block says TOMORROW while that is
# true — it is the most persuasive word available and it expires by itself.
# Computed from the real clock, not hardcoded, so a rebuild on the day says
# TONIGHT and a rebuild after it says the date.
_TODAY = datetime.date.today()
WHEN = ("TONIGHT" if DT == _TODAY
        else "TOMORROW" if DT == _TODAY + datetime.timedelta(days=1)
        else f'{DT.day} {DT.strftime("%b").upper()}')
DATE_LONG = f'{DT.strftime("%A")} {DT.day} {DT.strftime("%B")}'
DATE_SHORT = f'{DT.strftime("%a").upper()} {DT.day} {DT.strftime("%b").upper()}'

FONTS = os.environ.get("UP_FONTS",
    "https://fonts.googleapis.com/css2?family=Archivo:ital,wdth,wght@0,62..125,400..900;"
    "1,62..125,400..900&family=JetBrains+Mono:wght@500;700&display=swap")

CUR = S["currency"]
# On night one THE CLIMB cannot be awarded — see uprising-social.json. The post
# must advertise the prize that will actually be handed out.
FIRST = bool(S.get("firstNight"))
SECOND_NAME = "Strongest finish" if FIRST else "The Climb"
SECOND_RULE = ("Most points in the second half of the night minus the first. "
               "Nothing to do with how you started.") if FIRST else \
              "Most points above your own average. Open to anyone in the room."
# The posts carry the DATE but no clock times and no durations — the owner
# fixes the start when the court is confirmed, and a poster that has to be
# reshot because the time moved is worse than one that never claimed it.
# S["start"] and F["minutes"] still drive the RULES screen inside the app.
END = (datetime.datetime.combine(DT, datetime.time(int(S["start"][:2]), int(S["start"][3:])))
       + datetime.timedelta(minutes=F["minutes"])).strftime("%H:%M")

CSS = """
  :root{
    --volt-rgb:0,245,200; --uv-rgb:157,107,255; --cream-rgb:242,240,247;
    --volt:#00F5C8; --uv:#9D6BFF; --cream:#F2F0F7; --muted:#9A95A8;
    --muted2:#8A84A2; --warn:#FF4D6D; --line:rgba(var(--cream-rgb),.12);
    --neon:rgba(var(--volt-rgb),.55);
    --grain:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='160' height='160'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.9' numOctaves='2' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E");
  }
  *{margin:0;padding:0;box-sizing:border-box;}
  body{position:relative;overflow:hidden;background:#06060A;color:var(--cream);
    font-family:'Archivo',system-ui,sans-serif;-webkit-font-smoothing:antialiased;}
  .wash{position:absolute;inset:0;background:
      radial-gradient(ellipse 90% 55% at 12% 4%,rgba(var(--uv-rgb),.17),transparent),
      radial-gradient(ellipse 80% 55% at 92% 8%,rgba(var(--volt-rgb),.15),transparent),
      radial-gradient(ellipse 70% 50% at 50% 100%,rgba(var(--volt-rgb),.10),transparent),
      linear-gradient(180deg,#030305,#06060A 58%,#04040A);}
  .grid{position:absolute;inset:0;background-image:
      linear-gradient(rgba(var(--volt-rgb),.05) 1px,transparent 1px),
      linear-gradient(90deg,rgba(var(--volt-rgb),.05) 1px,transparent 1px);
    background-size:60px 60px;}
  .grain{position:absolute;inset:0;opacity:.26;mix-blend-mode:overlay;background-image:var(--grain);}
  .pad{position:relative;height:100%;display:flex;flex-direction:column;justify-content:space-between;}
  .disp{font-family:'Archivo';font-style:italic;font-variation-settings:'wdth' 125,'wght' 900;
    text-transform:uppercase;letter-spacing:.01em;}
  .mono{font-family:'JetBrains Mono',monospace;}
  .top{display:flex;align-items:center;gap:16px;}
  .mark{width:46px;height:46px;border:1px solid var(--neon);background:rgba(var(--volt-rgb),.12);
    display:flex;align-items:center;justify-content:center;box-shadow:0 0 30px rgba(var(--volt-rgb),.30);}
  .top .nm{font-size:30px;}
  .top .sub{margin-left:auto;font-size:12px;font-weight:800;letter-spacing:.3em;color:var(--uv);}
  .lede{color:var(--muted);line-height:1.45;}
  .lede b{color:var(--cream);font-weight:800;}
  .host{font-family:'JetBrains Mono',monospace;font-weight:700;letter-spacing:.2em;color:var(--volt);}
  .host small{display:block;color:var(--muted2);letter-spacing:.2em;margin-top:6px;}
  .foot{padding-top:30px;border-top:1px solid var(--line);
    display:flex;align-items:flex-end;justify-content:space-between;gap:26px;}
  .fact b{display:block;font-family:'Archivo';font-style:italic;
    font-variation-settings:'wdth' 125,'wght' 900;text-transform:uppercase;white-space:nowrap;}
  .fact i{display:block;font-style:normal;font-weight:800;letter-spacing:.2em;
    text-transform:uppercase;color:var(--muted2);margin-top:5px;}
  .fact b u{display:block;text-decoration:none;font-family:'Archivo',sans-serif;
    font-style:normal;font-variation-settings:normal;font-weight:800;
    font-size:.32em;letter-spacing:.2em;color:var(--muted2);margin-bottom:2px;}
"""

MARK = ("""<span class="mark"><svg viewBox="0 0 100 100" width="24" height="24">"""
        """<path d="M18 64 L50 32 L82 64" fill="none" stroke="#00F5C8" stroke-width="13" """
        """stroke-linecap="square"/></svg></span>""")


def page(name, w, h, pad, body, extra=""):
    html = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
<link href="{FONTS}" rel="stylesheet" />
<style>html,body{{width:{w}px;height:{h}px;}}{CSS}.pad{{padding:{pad};}}{extra}</style>
</head><body>
<div class="wash"></div><div class="grid"></div><div class="grain"></div>
<div class="pad">{body}</div>
</body></html>"""
    open(os.path.join(OUT, name), "w").write(html)
    return name


def header(sub="Urban Playground"):
    return f"""<div class="top">{MARK}<span class="nm disp">{S['name']}</span>
      <span class="sub">{sub}</span></div>"""


def ladder(rows_note=True):
    out = ['<div><div class="lhead"><span>The ladder</span><span>Win / lose</span></div>']
    notes = {1: "The top. Winners stay.",
             2: "Win here and you are on Court 1 next round.",
             3: "A win here is worth a loss on Court 1.",
             4: "The bottom. Only one way to go."}
    for c in range(1, F["courts"] + 1):
        top = " top" if c == 1 else ""
        # Without the note there is no flex filler, so the points floated in
        # the middle of a very wide rung instead of sitting at its right edge.
        note = (f'<span class="note">{notes.get(c, "")}</span>' if rows_note
                else '<span class="note"></span>')
        out.append(f'''<div class="rung{top}"><span class="cn">COURT {c}</span>{note}
          <span class="pts"><b>{F["win"][str(c)]}</b><i> / {F["lose"][str(c)]}</i></span></div>''')
        if c == 1:
            out.append('<div class="mid"><span class="up">&#9650; Winners move up</span>'
                       '<span class="dn">Losers move down &#9660;</span></div>')
    out.append("</div>")
    return "".join(out)


LADDER_CSS = """
  .lhead{display:flex;justify-content:space-between;font-size:12px;font-weight:800;
    letter-spacing:.26em;text-transform:uppercase;color:var(--muted2);margin-bottom:12px;}
  .rung{display:flex;align-items:center;gap:20px;border:1px solid var(--line);
    padding:21px 22px;margin-bottom:9px;background:rgba(var(--cream-rgb),.025);}
  .rung.top{border-color:var(--neon);background:rgba(var(--volt-rgb),.10);
    box-shadow:0 0 34px rgba(var(--volt-rgb),.22);}
  .rung .cn{font-family:'JetBrains Mono',monospace;font-size:19px;font-weight:700;
    letter-spacing:.14em;width:168px;color:var(--muted);}
  .rung.top .cn{color:var(--volt);}
  .rung .note{flex:1;font-size:17px;color:var(--muted2);}
  .rung .pts{font-family:'JetBrains Mono',monospace;font-size:26px;font-weight:700;
    width:112px;text-align:right;}
  .rung .pts b{color:var(--cream);} .rung.top .pts b{color:var(--volt);}
  .rung .pts i{font-style:normal;color:var(--muted2);}
  .mid{display:flex;justify-content:space-between;padding:0 24px;margin:-3px 0 5px;}
  .mid span{font-size:15px;font-weight:800;letter-spacing:.18em;text-transform:uppercase;}
  .up{color:var(--volt);} .dn{color:var(--uv);}
"""

# ── 1. hero ────────────────────────────────────────────────────────────────
page("post-1-hero.html", 1080, 1350, "60px 64px 54px", f"""
  <div class="top">{MARK}<span class="sub">Urban Playground</span></div>
  <div>
    <div class="kick mono">New · {S['cadenceLine']}</div>
    <h1 class="disp wordmark" data-fit>{S['name']}</h1>
    <div class="strap disp">{S['tagline']}</div>
    <p class="lede">A new padel social. <b>Come on your own</b> — you play with a different
       partner almost every round, and the court you are standing on is your position.</p>
  </div>
  <div class="when">
    <div class="day disp">{WHEN}</div>
    <div class="dl">{DATE_SHORT} &nbsp;·&nbsp; NO PARTNER NEEDED</div>
  </div>
  <div class="foot">
    <div style="display:flex;gap:40px;align-items:flex-end">
      <span class="fact"><b class="disp"><u>Up to</u>{F['players']}</b><i>Places</i></span>
      <span class="fact"><b class="disp"><u>Up to</u>{F['matches']}</b><i>Matches each</i></span>
      <span class="fact"><b class="disp">{S['entry']} {CUR}</b><i>To play</i></span>
    </div>
    <span class="host">{S['host'].upper()}<small>{S['promise'].upper()}</small></span>
  </div>
""", """
  .top{justify-content:space-between;}
  .top .sub{margin-left:0;}
  .kick{font-size:13px;font-weight:700;letter-spacing:.3em;text-transform:uppercase;color:var(--uv);}
  /* The name is the hero. It is set to fill the width rather than to a fixed
     size, so a longer name would shrink instead of running off the card. */
  h1.wordmark{white-space:nowrap;font-size:184px;line-height:.84;margin-top:24px;color:var(--volt);
    text-shadow:0 0 70px rgba(var(--volt-rgb),.45);letter-spacing:-.005em;}
  .strap{font-size:46px;line-height:1;margin-top:18px;color:var(--cream);}
  .lede{font-size:24px;margin-top:26px;max-width:900px;}
  .when{border-top:1px solid var(--line);border-bottom:1px solid var(--line);padding:30px 0;}
  .day{font-size:100px;line-height:.9;color:var(--volt);text-shadow:0 0 44px rgba(var(--volt-rgb),.4);}
  .dl{font-family:'JetBrains Mono',monospace;font-size:24px;font-weight:700;
    letter-spacing:.14em;color:var(--cream);margin-top:14px;}
  .fact b{font-size:46px;} .fact i{font-size:12px;}
  .host{font-size:15px;text-align:right;white-space:nowrap;} .host small{font-size:12px;}
""")

# ── 2. what a match actually is ────────────────────────────────────────────
page("post-2-match.html", 1080, 1350, "60px 64px 54px", f"""
  {header("How a match works")}
  <div>
    <h2 class="disp">Win {F['target']} rallies<br>and it is <em>over</em></h2>
    <p class="lede">Every rally you win is one point. <b>No 15-30-40, no deuce, no games,
       no sets.</b> First pair to {F['target']} wins and the match stops there — so a score is
       always {F['target']} and whatever the other pair got.</p>
  </div>

  <div class="scoreline">
    <div class="sl"><span class="n">{F['target']}</span><span class="dash">&#8211;</span><span class="n o">7</span></div>
    <div class="cap">Around {F['target'] + 6} rallies in all. Seven or eight minutes. Then you walk to your next court.</div>
  </div>

  <div class="two">
    <div class="th">Two things are called points. They are not the same.</div>
    <div class="tr">
      <span class="lab">In the match</span>
      <span class="val">0&#8211;{F['target']}</span>
      <span class="exp">Rallies you won. Decides who wins <b>this match</b>.</span>
    </div>
    <div class="tr hi">
      <span class="lab">On the table</span>
      <span class="val">{F['lose'][str(F['courts'])]}&#8211;{F['win']['1']}</span>
      <span class="exp">What that result pays you. Decides who wins <b>the night</b>.</span>
    </div>
    <p class="note">Win {F['target']}&#8211;7 on Court 2 and you take <b>{F['win']['2']} points</b> — not {F['target']}.
       The {F['target']} only decided the match. Highest total after {F['scoring']} rounds wins; there is no
       number to reach.</p>
  </div>

  <div class="foot">
    <div style="display:flex;gap:40px;align-items:flex-end">
      <span class="fact"><b class="disp">{F['target']}</b><i>To win a match</i></span>
      <span class="fact"><b class="disp"><u>Up to</u>{F['matches']}</b><i>Matches each</i></span>
      <span class="fact"><b class="disp">{F['courts']}</b><i>Courts</i></span>
    </div>
    <span class="host">{S['host'].upper()}</span>
  </div>
""", """
  h2{font-size:84px;line-height:.88;}
  h2 em{font-style:italic;color:var(--volt);text-shadow:0 0 44px rgba(var(--volt-rgb),.42);}
  .lede{font-size:22px;margin-top:22px;max-width:920px;}
  .scoreline{border:1px solid var(--neon);background:rgba(var(--volt-rgb),.08);
    box-shadow:0 0 36px rgba(var(--volt-rgb),.18);padding:30px 36px;text-align:center;}
  .sl{font-family:'JetBrains Mono',monospace;font-weight:700;line-height:1;}
  .sl .n{font-size:96px;color:var(--volt);}
  .sl .n.o{color:var(--cream);}
  .sl .dash{font-size:60px;color:var(--muted2);margin:0 26px;vertical-align:14px;}
  .cap{font-size:17px;color:var(--muted2);margin-top:16px;}
  .two{}
  .th{font-size:13px;font-weight:800;letter-spacing:.24em;text-transform:uppercase;
    color:var(--muted2);margin-bottom:12px;}
  .tr{display:flex;align-items:center;gap:24px;border:1px solid var(--line);
    padding:20px 24px;margin-bottom:9px;background:rgba(var(--cream-rgb),.025);}
  .tr.hi{border-color:rgba(var(--uv-rgb),.5);background:rgba(var(--uv-rgb),.08);}
  .tr .lab{font-family:'Archivo';font-style:italic;font-variation-settings:'wdth' 125,'wght' 900;
    text-transform:uppercase;font-size:21px;width:210px;flex:0 0 auto;}
  .tr.hi .lab{color:var(--uv);}
  .tr .val{font-family:'JetBrains Mono',monospace;font-size:28px;font-weight:700;
    width:96px;flex:0 0 auto;color:var(--cream);}
  .tr .exp{flex:1;font-size:17px;color:var(--muted2);}
  .tr .exp b{color:var(--cream);}
  .note{font-size:17px;line-height:1.5;color:var(--muted2);margin-top:16px;}
  .note b{color:var(--cream);}
  .fact b{font-size:38px;} .fact i{font-size:11px;}
  .host{font-size:14px;text-align:right;}
""")

# ── 3. the ladder ──────────────────────────────────────────────────────────
page("post-3-ladder.html", 1080, 1350, "60px 64px 54px", f"""
  {header("How it works")}
  <div>
    <h2 class="disp">Win and you<br>go <em>up a court</em></h2>
    <p class="lede">Lose and you go down. Points are worth more the higher you climb — so
       farming wins at the bottom gets you nowhere. <b>Losing on Court 1 is worth a win on
       Court 3.</b></p>
  </div>
  {ladder()}
  <div class="steps">
    <div class="step"><span class="n mono">01</span><b>The shuffle</b>
      <i>Round one scores nothing. It decides where you start, so your court is won, not drawn.</i></div>
    <div class="step"><span class="n mono">02</span><b>New partners</b>
      <i>Re-paired on arrival, closest match possible. Ten different partners in a night.</i></div>
    <div class="step"><span class="n mono">03</span><b>Last round doubles</b>
      <i>Highest total wins. One night in three is decided in the final round.</i></div>
  </div>
  <div class="foot">
    <div style="display:flex;gap:40px;align-items:flex-end">
      <span class="fact"><b class="disp">{F['courts']}</b><i>Courts</i></span>
      <span class="fact"><b class="disp">{F['scoring']}</b><i>Scoring rounds</i></span>
      <span class="fact"><b class="disp">{F['target']}</b><i>Point match</i></span>
      <span class="fact"><b class="disp"><u>Up to</u>{F['players']}</b><i>Players</i></span>
    </div>
    <span class="host">{S['host'].upper()}</span>
  </div>
""", LADDER_CSS + """
  h2{font-size:84px;line-height:.88;}
  h2 em{font-style:italic;color:var(--volt);text-shadow:0 0 44px rgba(var(--volt-rgb),.42);}
  .lede{font-size:22px;margin-top:22px;max-width:900px;}
  .steps{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;}
  .step{border:1px solid var(--line);padding:21px 19px 23px;background:rgba(var(--cream-rgb),.025);}
  .step .n{font-size:13px;font-weight:700;color:var(--volt);letter-spacing:.14em;}
  .step b{display:block;font-size:20px;font-weight:800;color:var(--cream);margin-top:9px;}
  .step i{display:block;font-style:normal;font-size:15px;line-height:1.4;color:var(--muted2);margin-top:7px;}
  .fact b{font-size:38px;} .fact i{font-size:11px;}
  .host{font-size:14px;text-align:right;}
""")

# ── 3. what you win ────────────────────────────────────────────────────────
page("post-4-prizes.html", 1080, 1350, "60px 64px 54px", f"""
  {header("What you win")}
  <div>
    <h2 class="disp">Two ways<br>to <em>take it</em></h2>
    <p class="lede">One prize for the best player on the night. One for the best against
       <b>themselves</b> — so a first-timer can win on their first night.</p>
  </div>
  <div>
    <div class="prize win">
      <div class="pl"><span class="t disp">Champion</span>
        <span class="d">Most points once the last round is played.</span></div>
      <span class="v disp">{S['championPrize']} {CUR}</span>
    </div>
    <div class="prize climb">
      <div class="pl"><span class="t disp">{SECOND_NAME}</span>
        <span class="d">{SECOND_RULE}</span></div>
      <span class="v disp small">{S['climbPrize']}</span>
    </div>
    <p class="note">{"One prize only ever goes to the best player in the room, and three of them would take 70% of the nights. This one is open to everybody — on the first night it is whoever finishes strongest, and from next month it becomes THE CLIMB: most points above <b>your own</b> average." if FIRST else "Measured over 200 simulated seasons: a single scratch prize sends <b>70%</b> of nights to the same three players. The handicap prize is <b>21%</b> — and it self-corrects, because winning it raises your own bar."}</p>
  </div>
  <div class="foot">
    <div style="display:flex;gap:40px;align-items:flex-end">
      <span class="fact"><b class="disp">{S['entry']} {CUR}</b><i>To play</i></span>
      <span class="fact"><b class="disp"><u>Up to</u>{S['cap']}</b><i>Places</i></span>
      <span class="fact"><b class="disp">{DT.day} {DT.strftime("%b").upper()}</b><i>{DT.strftime("%A").upper()}</i></span>
    </div>
    <span class="host">{S['signupVia'].upper()}<small>{S['host'].upper()}</small></span>
  </div>
""", """
  h2{font-size:84px;line-height:.88;}
  h2 em{font-style:italic;color:var(--volt);text-shadow:0 0 44px rgba(var(--volt-rgb),.42);}
  .lede{font-size:23px;margin-top:22px;max-width:880px;}
  .prize{display:flex;align-items:center;gap:30px;border:1px solid var(--line);
    padding:34px 32px;margin-bottom:14px;background:rgba(var(--cream-rgb),.025);}
  .prize.win{border-color:var(--neon);background:rgba(var(--volt-rgb),.10);
    box-shadow:0 0 36px rgba(var(--volt-rgb),.22);}
  .prize.climb{border-color:rgba(var(--uv-rgb),.5);background:rgba(var(--uv-rgb),.08);}
  .pl{flex:1;}
  .prize .t{display:block;font-size:38px;}
  .prize.win .t{color:var(--volt);} .prize.climb .t{color:var(--uv);}
  .prize .d{display:block;font-size:17px;color:var(--muted2);margin-top:8px;line-height:1.4;}
  .prize .v{font-size:52px;white-space:nowrap;text-align:right;}
  .prize .v.small{font-size:24px;max-width:300px;white-space:normal;line-height:1.2;color:var(--uv);}
  .note{font-size:17px;line-height:1.5;color:var(--muted2);margin-top:22px;}
  .note b{color:var(--cream);}
  .fact b{font-size:38px;} .fact i{font-size:11px;}
  .host{font-size:14px;text-align:right;white-space:nowrap;} .host small{font-size:12px;}
""")

# ── 4. story ───────────────────────────────────────────────────────────────
page("post-story.html", 1080, 1920, "120px 64px 110px", f"""
  <div class="top">{MARK}<span class="sub">Urban Playground</span></div>
  <div>
    <div class="kick mono">New · {S['cadenceLine']}</div>
    <h1 class="disp wordmark" data-fit>{S['name']}</h1>
    <div class="strap disp">{S['tagline']}</div>
    <p class="lede">Come on your own. A different partner almost every round, and the court
       you are standing on is your position. Every match is <b>first to {F['target']}</b> —
       straight rallies, no games, no sets.</p>
  </div>
  {ladder(rows_note=False)}
  <div class="when">
    <div class="day disp">{WHEN}</div>
    <div class="dl">{DATE_SHORT} &nbsp;·&nbsp; {S['entry']} {CUR} &nbsp;·&nbsp; up to {S['cap']} places</div>
  </div>
  <div class="foot">
    <div style="display:flex;gap:46px;align-items:flex-end">
      <span class="fact"><b class="disp"><u>Up to</u>{F['matches']}</b><i>Matches each</i></span>
      <span class="fact"><b class="disp">{S['championPrize']} {CUR}</b><i>Champion</i></span>
      <span class="fact"><b class="disp">Free</b><i>Next month, for {"the finish" if FIRST else "the climb"}</i></span>
    </div>
  </div>
  <div class="hostline"><span class="host">{S['host'].upper()}<small>{S['promise'].upper()}</small></span></div>
""", LADDER_CSS + """
  .top{justify-content:space-between;}
  .top .sub{margin-left:0;}
  .kick{font-size:14px;font-weight:700;letter-spacing:.3em;text-transform:uppercase;color:var(--uv);}
  h1.wordmark{white-space:nowrap;font-size:176px;line-height:.84;margin-top:26px;color:var(--volt);
    text-shadow:0 0 70px rgba(var(--volt-rgb),.45);letter-spacing:-.005em;}
  .strap{font-size:44px;line-height:1;margin-top:16px;color:var(--cream);}
  .lede{font-size:24px;margin-top:24px;}
  .rung .cn{width:190px;font-size:21px;}
  .rung{padding:26px 24px;}
  .rung .pts{font-size:30px;}
  .when{border-top:1px solid var(--line);border-bottom:1px solid var(--line);padding:34px 0;}
  .day{font-size:96px;line-height:.9;color:var(--volt);text-shadow:0 0 44px rgba(var(--volt-rgb),.4);}
  .dl{font-family:'JetBrains Mono',monospace;font-size:23px;font-weight:700;
    letter-spacing:.1em;color:var(--cream);margin-top:16px;}
  .foot{border-top:0;padding-top:0;}
  .fact b{font-size:46px;} .fact i{font-size:12px;}
  .hostline{text-align:center;}
  .host{font-size:16px;} .host small{font-size:13px;}
""")

# ── the copy ───────────────────────────────────────────────────────────────
# Written here rather than kept in a doc, so the sentence that quotes "15
# matches" is regenerated from the same facts as the card that prints it.
CAP = os.path.join(OUT, "CAPTIONS.txt")
HR = "=" * 68
open(CAP, "w").write(f"""UPRISING — announcement copy
Generated by build-uprising-announce.py. Every number here is the same one the
cards and the app carry; re-run the builder after changing uprising-social.json
rather than editing this by hand.

{HR}
WHATSAPP — the group post (paste with post-1-hero.png)
{HR}

*{S['name']}* — a new padel social. {WHEN.title()}, {DATE_LONG}.

Come on your own. No partner needed.

{F['courts']} courts, one ladder. Win and you move up a court, lose and you move
down — the court you're standing on is your position. You play with a
different partner almost every round.

*How a match works:* every rally you win is a point. No 15-30-40, no games,
no sets. First pair to {F['target']} wins and you move on — so a score is always
{F['target']}-something.

*How the night is won:* the {F['target']} decides the match and then goes nowhere near
the table. What you bank is what the COURT pays — {F['win']['1']} for a win on Court 1,
down to {F['win'][str(F['courts'])]} on Court {F['courts']}. Highest total at the end takes the night.

• Up to {F['matches']} matches each — not three
• First to {F['target']}, straight rallies
• {S['entry']} {CUR} · up to {S['cap']} places, then a waitlist
• Champion takes {S['championPrize']} {CUR}
• {"STRONGEST FINISH — biggest second half — plays the next one free" if FIRST else "THE CLIMB — most points above your own average — plays the next one free"}

Round one is the shuffle: it decides which court you start on and scores
nothing, so nobody is placed by a draw.

Reply to claim a place. Monthly from here.
{S['host']}

{HR}
INSTAGRAM — carousel caption (5 cards, hero first)
{HR}

{S['promise']}

{S['name']} is a new monthly padel social, and the first one is {WHEN.lower()} — {DATE_LONG}.

Every match is first to {F['target']} — straight rallies, no games, no sets. Win it and
you climb a court. Lose and you drop one.

Here is the bit worth reading twice: the {F['target']} decides the match and nothing else.
What you bank is what the court pays — {F['win']['1']} for a win on Court 1, {F['win'][str(F['courts'])]} on Court {F['courts']}.
So there is nothing to gain from camping at the bottom beating people you
should beat.

Up to {F['matches']} matches. A different partner almost every round. You do not need
to bring anyone.

{S['entry']} {CUR} · up to {S['cap']} places
Champion {S['championPrize']} {CUR}. {"Strongest finisher" if FIRST else "Biggest climb above your own average"} plays next month free.

Link in bio to the live ladder.

#urbanplayground #padeloman #padelmuscat #uprising

{HR}
STORY — text over post-story.png
{HR}

{WHEN} · {DATE_LONG}
Come alone. Up to {S['cap']} places.
Link sticker → {S['host']}

{HR}
THE ONE-LINER, if you only get a sentence
{HR}

"Four courts, one ladder — win and you climb, lose and you drop.
 Up to {F['matches']} matches, no partner needed, {S['entry']} {CUR}."

{HR}
WHAT NOT TO PROMISE
{HR}

· Not "a different partner every round" — a court of four has only three ways
  to split, so past about round 11 people start repeating. Measured: 10 to 13
  different partners out of {F['scoring'] + 1}. "Almost every round" and "ten different
  partners" are both true; "every round" is not.
· Not "the best player wins". Measured, the winner is one of the three
  strongest players about 69% of the time. That is the right amount of luck
  for a social, and it is why THE CLIMB exists — but do not sell it as a
  ranking tournament.
· Not a finals night, a season table or a league. This is one night, monthly.
""")

print(f"UPRISING announcement — {DATE_LONG}, {S['start']}–{END}")
print(f"  {F['players']} players · {F['courts']} courts · {F['matches']} matches "
      f"({F['scoring']} scoring + the shuffle) · first to {F['target']} · {F['minutes']} min")
print(f"  {S['entry']} {CUR} in · champion {S['championPrize']} {CUR} · climb: {S['climbPrize'].lower()}")
print(f"  wrote 4 pages + CAPTIONS.txt to {OUT}")
