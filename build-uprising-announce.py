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

# Local, not Google. Chromium in this container does not trust the agent
# proxy's CA, so a link to fonts.googleapis.com fails — and a webfont that
# fails to load is a silent fallback, not an error: the whole story series
# rendered in Times once with every assertion passing. See ops/vendor-fonts.py.
FONTS = os.environ.get("UP_FONTS", "../../fonts/fonts.css")

CUR = S["currency"]
# The champion's prize is a club voucher, not cash, and the posts say so in
# every place the figure appears. "Champion takes 15 OMR" reads as cash, and a
# player who turns up expecting notes and is handed a voucher has been misled
# by our own poster — the one place the club cannot afford to be vague.
KIND = S.get("championPrizeKind", "")
CHAMP = f"{S['championPrize']} {CUR}"
CHAMP_FULL = f"{CHAMP} {KIND}".strip()
# "8 for a win on Court 1, 6 on Court 2, …" — generated from the shipped points
# table rather than typed, so it stays right if the ladder ever gets a fifth
# court or the table is re-weighted.
PAYS = ", ".join(
    (f"{F['win'][str(c)]} for a win on Court {c}" if c == 1 else f"{F['win'][str(c)]} on Court {c}")
    for c in range(1, F["courts"] + 1))
# On night one THE CLIMB cannot be awarded — see uprising-social.json. The post
# must advertise the prize that will actually be handed out.
FIRST = bool(S.get("firstNight"))
# One prize, or two. With SECOND off, the prize cards carry a single CHAMPION
# block and no caption mentions a runner-up — a second prize that is advertised
# and then not handed out is worse than never having offered it.
SECOND = bool(S.get("secondPrize"))
# The last round only doubles when NOBODY rests — whoever is sitting it out
# could not win it. With 16 on 3 courts, 4 rest, so every line that promises a
# double finish has to vanish with it rather than being quietly wrong on the
# night. Same for "matches each": 13 ROUNDS is 9 matches each once 4 of 16 are
# off court, and the two are the same number only when nobody rests.
DBL = bool(F.get("doubleFinal"))
RESTS = int(F.get("resting") or 0)
EACH = int(F.get("matches") or 0)


def plural(n, word):
    """1 player / 2 players / 1 match / 2 matches."""
    return f"{n} {word}" + ("" if n == 1 else ("es" if word[-1] in "sxz" or word[-2:] in ("ch", "sh") else "s"))
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
    <div class="step"><span class="n mono">03</span><b>{"Last round doubles" if DBL else plural(RESTS, "player") + " rests a round"}</b>
      <i>{"Highest total wins. One night in three is decided in the final round." if DBL else f"{F['onCourt']} play at once, so {RESTS} sit out — on a rota drawn before the first serve, so everyone rests the same number of times."}</i></div>
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
    <h2 class="disp">{"Two ways<br>to <em>take it</em>" if SECOND else "One night.<br>One <em>winner</em>."}</h2>
    <p class="lede">{"One prize for the best player on the night. One for the best against <b>themselves</b> — so a first-timer can win on their first night." if SECOND else "No groups, no knockout, no final. <b>Every point you win all night goes on one table</b>, and the name at the top of it takes the voucher."}</p>
  </div>
  <div>
    <div class="prize win">
      <div class="pl"><span class="t disp">Champion</span>
        <span class="d">Most points once the last round is played.</span></div>
      <span class="v disp">{CHAMP}<em>{KIND}</em></span>
    </div>
    {f'''<div class="prize climb">
      <div class="pl"><span class="t disp">{SECOND_NAME}</span>
        <span class="d">{SECOND_RULE}</span></div>
      <span class="v disp small">{S['climbPrize']}</span>
    </div>''' if SECOND else ""}
    <p class="note">{("One prize only ever goes to the best player in the room, and three of them would take 70% of the nights. This one is open to everybody — on the first night it is whoever finishes strongest, and from next month it becomes THE CLIMB: most points above <b>your own</b> average." if FIRST else "Measured over 200 simulated seasons: a single scratch prize sends <b>70%</b> of nights to the same three players. The handicap prize is <b>21%</b> — and it self-corrects, because winning it raises your own bar.") if SECOND else f"There is no score to reach and no last-match shoot-out. A win on Court 1 is worth {F['win']['1']} and a win on Court {F['courts']} is worth {F['win'][str(F['courts'])]}, so the table rewards <b>climbing and staying up there</b>.{' The last round counts double, which is why one night in three is still open when it starts.' if DBL else ''}"}</p>
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
  .prize .v em{display:block;font-family:'Archivo',sans-serif;font-style:normal;
    font-variation-settings:normal;font-weight:800;font-size:15px;letter-spacing:.24em;
    color:var(--muted2);margin-top:6px;}
  .prize .v.small{font-size:24px;max-width:300px;white-space:normal;line-height:1.2;color:var(--uv);}
  .note{font-size:17px;line-height:1.5;color:var(--muted2);margin-top:22px;}
  .note b{color:var(--cream);}
  .fact b{font-size:38px;} .fact i{font-size:11px;}
  .host{font-size:14px;text-align:right;white-space:nowrap;} .host small{font-size:12px;}
""")

# ── the story series ───────────────────────────────────────────────────────
# Five 1080x1920 cards, posted in order. A story is watched one frame at a
# time and most people see only one of them, so each card carries the name,
# the date and the host — none of them depends on the one before it.
#
# The padding is deliberately deep: Instagram draws its own chrome over the
# top ~170px and the reply bar over the bottom ~200px of a story, and a card
# laid out to the full 1920 puts its date under the reply box on a phone.
STORY_PAD = "180px 64px 210px"
STORY_CSS = LADDER_CSS + """
  .top{justify-content:space-between;}
  .top .sub{margin-left:0;font-size:13px;}
  .top .nm{font-size:34px;}
  .kick{font-size:14px;font-weight:700;letter-spacing:.3em;text-transform:uppercase;color:var(--uv);}
  h1.wordmark{white-space:nowrap;font-size:176px;line-height:.84;color:var(--volt);
    text-shadow:0 0 70px rgba(var(--volt-rgb),.45);letter-spacing:-.005em;}
  /* 84, not 96: at 96 the longest line a story headline carries ("CLIMB A
     COURT") takes a third line, and a two-line headline with an orphan under
     it reads as a mistake. Checked by counting rendered lines, not by eye. */
  h2{font-size:84px;line-height:.9;}
  h2 em{font-style:italic;color:var(--volt);text-shadow:0 0 48px rgba(var(--volt-rgb),.45);}
  .strap{font-size:46px;line-height:1;margin-top:18px;color:var(--cream);}
  .lede{font-size:26px;margin-top:26px;}
  .when{border-top:1px solid var(--line);border-bottom:1px solid var(--line);padding:34px 0;}
  .day{font-size:104px;line-height:.9;color:var(--volt);text-shadow:0 0 44px rgba(var(--volt-rgb),.4);}
  .dl{font-family:'JetBrains Mono',monospace;font-size:24px;font-weight:700;
    letter-spacing:.1em;color:var(--cream);margin-top:16px;}
  .rung{padding:28px 26px;} .rung .cn{width:200px;font-size:22px;} .rung .pts{font-size:32px;}
  .rung .note{font-size:19px;}
  .lhead{font-size:13px;}
  .mid span{font-size:16px;}
  .hostline{text-align:center;}
  .host{font-size:17px;} .host small{font-size:13px;margin-top:8px;}
  .swipe{text-align:center;font-family:'JetBrains Mono',monospace;font-size:19px;font-weight:700;
    letter-spacing:.2em;color:var(--volt);}
"""


def story(name, body, extra=""):
    return page(name, 1080, 1920, STORY_PAD, body, STORY_CSS + extra)


# 1 — the name, the date, and nothing else to read
story("story-1-name.html", f"""
  <div class="top">{MARK}<span class="sub">Urban Playground</span></div>
  <div>
    <div class="kick mono">New · {S['cadenceLine']}</div>
    <h1 class="disp wordmark" data-fit style="margin-top:26px">{S['name']}</h1>
    <div class="strap">{S['tagline']}</div>
    <p class="lede">A new padel social. <b>Come on your own</b> — four courts, one ladder,
       and a different partner almost every round.</p>
  </div>
  <div class="when">
    <div class="day disp">{WHEN}</div>
    <div class="dl">{DATE_SHORT} &nbsp;·&nbsp; NO PARTNER NEEDED</div>
  </div>
  <div class="hostline"><span class="host">{S['host'].upper()}<small>{S['promise'].upper()}</small></span></div>
""", """
  .strap{font-size:52px;}
  .lede{font-size:28px;max-width:900px;}
""")

# 2 — the ladder, which is the whole idea
story("story-2-ladder.html", f"""
  {header("How it works")}
  <div>
    <h2 class="disp">Win a match,<br>climb a <em>court</em></h2>
    <p class="lede">Lose one and you drop a court. Where you are standing <b>is</b> your
       position — and the higher it is, the more a win there pays.</p>
  </div>
  {ladder()}
  <div class="hostline"><span class="host">{DATE_SHORT} &nbsp;·&nbsp; {S['host'].upper()}</span></div>
""")

# 3 — the one thing everybody asks
story("story-3-match.html", f"""
  {header("How a match works")}
  <div>
    <h2 class="disp big">First to<br><em>{F['target']}</em></h2>
    <p class="lede">Every rally you win is a point. <b>No 15-30-40, no deuce, no games,
       no sets.</b> First pair to {F['target']} wins and the match stops there.</p>
  </div>
  <div class="scoreline">
    <div class="sl"><span class="n">{F['target']}</span><span class="dash">&#8211;</span><span class="n o">7</span></div>
    <div class="cap">A score always looks like this. Then you walk to your next court.</div>
  </div>
  <div class="two">
    <div class="tr"><span class="lab">In the match</span><span class="val">0&#8211;{F['target']}</span>
      <span class="exp">Rallies. Decides <b>this match</b>.</span></div>
    <div class="tr hi"><span class="lab">On the table</span>
      <span class="val">{F['lose'][str(F['courts'])]}&#8211;{F['win']['1']}</span>
      <span class="exp">What the court pays. Decides <b>the night</b>.</span></div>
  </div>
  <div class="hostline"><span class="host">{DATE_SHORT} &nbsp;·&nbsp; {S['host'].upper()}</span></div>
""", """
  /* The number IS the headline on this card — at the same size as the words
     above it, "11" reads as an orphan line rather than the answer. */
  h2.big em{font-size:1.9em;line-height:.85;display:inline-block;}
  .scoreline{border:1px solid var(--neon);background:rgba(var(--volt-rgb),.08);
    box-shadow:0 0 36px rgba(var(--volt-rgb),.18);padding:36px;text-align:center;}
  .sl{font-family:'JetBrains Mono',monospace;font-weight:700;line-height:1;}
  .sl .n{font-size:112px;color:var(--volt);} .sl .n.o{color:var(--cream);}
  .sl .dash{font-size:70px;color:var(--muted2);margin:0 30px;vertical-align:16px;}
  .cap{font-size:19px;color:var(--muted2);margin-top:20px;}
  .tr{display:flex;align-items:center;gap:22px;border:1px solid var(--line);
    padding:24px 26px;margin-bottom:10px;background:rgba(var(--cream-rgb),.025);}
  .tr.hi{border-color:rgba(var(--uv-rgb),.5);background:rgba(var(--uv-rgb),.08);}
  .tr .lab{font-family:'Archivo';font-style:italic;font-variation-settings:'wdth' 125,'wght' 900;
    text-transform:uppercase;font-size:23px;width:270px;flex:0 0 auto;}
  .tr.hi .lab{color:var(--uv);}
  .tr .val{font-family:'JetBrains Mono',monospace;font-size:30px;font-weight:700;
    width:100px;flex:0 0 auto;}
  .tr .exp{flex:1;font-size:19px;color:var(--muted2);} .tr .exp b{color:var(--cream);}
""")

# 4 — what is on the table
story("story-4-prizes.html", f"""
  {header("What you win")}
  <div>
    <h2 class="disp">{"Two ways<br>to <em>take it</em>" if SECOND else "One night.<br>One <em>winner</em>."}</h2>
    <p class="lede">{"One for the best player on the night. One for the best against <b>themselves</b> — so a first-timer can win on their first night." if SECOND else "No groups, no knockout, no final. <b>Every point you win all night goes on one table</b> — and the name at the top takes it."}</p>
  </div>
  <div>
    <div class="prize win">
      <div class="pl"><span class="t disp">Champion</span>
        <span class="d">Most points once the last round is played.</span></div>
      <span class="v disp">{CHAMP}<em>{KIND}</em></span>
    </div>
    {f'''<div class="prize climb">
      <div class="pl"><span class="t disp">{SECOND_NAME}</span>
        <span class="d">{SECOND_RULE}</span></div>
      <span class="v disp small">{S['climbPrize']}</span>
    </div>''' if SECOND else f'''<div class="prize note">
      <div class="pl"><span class="t disp">{"Last round doubles" if DBL else "Every round counts"}</span>
        <span class="d">{"Worth twice the points, so the night is not over until it is. One in three is decided there." if DBL else f"There is no score to reach and no final — you accumulate over {plural(EACH, 'match')}, and the table is live all night."}</span></div>
    </div>'''}
  </div>
  <div class="hostline"><span class="host">{S['entry']} {CUR} TO PLAY &nbsp;·&nbsp; {DATE_SHORT}</span></div>
""", """
  .prize{display:flex;align-items:center;gap:30px;border:1px solid var(--line);
    padding:38px 34px;margin-bottom:16px;background:rgba(var(--cream-rgb),.025);}
  .prize.win{border-color:var(--neon);background:rgba(var(--volt-rgb),.10);
    box-shadow:0 0 36px rgba(var(--volt-rgb),.22);}
  .prize.climb{border-color:rgba(var(--uv-rgb),.5);background:rgba(var(--uv-rgb),.08);}
  .prize.note{border-color:rgba(var(--uv-rgb),.5);background:rgba(var(--uv-rgb),.08);}
  .pl{flex:1;}
  .prize .t{display:block;font-size:42px;}
  .prize.win .t{color:var(--volt);}
  .prize.climb .t, .prize.note .t{color:var(--uv);}
  .prize .d{display:block;font-size:19px;color:var(--muted2);margin-top:10px;line-height:1.4;}
  .prize .v{font-size:56px;white-space:nowrap;text-align:right;}
  .prize .v em{display:block;font-family:'Archivo',sans-serif;font-style:normal;
    font-variation-settings:normal;font-weight:800;font-size:16px;letter-spacing:.24em;
    color:var(--muted2);margin-top:8px;}
  .prize .v.small{font-size:26px;max-width:320px;white-space:normal;line-height:1.25;color:var(--uv);}
""")

# 5 — the ask. The only card with a verb in the headline.
story("story-5-claim.html", f"""
  {header("Claim a place")}
  <div>
    <h2 class="disp">Reply to<br>take a <em>place</em></h2>
    <p class="lede">{S['signupVia']}. First come, first on — after {S['cap']} it is a
       waitlist, and places go faster than they come back.</p>
  </div>
  <div class="card">
    <div class="row"><span class="k">When</span><span class="v">{WHEN} · {DATE_SHORT}</span></div>
    <div class="row"><span class="k">Entry</span><span class="v">{S['entry']} {CUR}</span></div>
    <div class="row"><span class="k">Places</span><span class="v">Up to {S['cap']}</span></div>
    <div class="row"><span class="k">Partner</span><span class="v">Not needed</span></div>
    <div class="row hi"><span class="k">Champion</span><span class="v">{CHAMP_FULL}</span></div>
  </div>
  <div class="swipe">&#8593; &nbsp; {S['host'].upper()}</div>
""", """
  .lede{font-size:27px;max-width:920px;}
  .card{border:1px solid var(--line);background:rgba(var(--cream-rgb),.025);}
  .row{display:flex;align-items:baseline;justify-content:space-between;gap:24px;
    padding:30px 34px;border-bottom:1px solid var(--line);}
  .row:last-child{border-bottom:0;}
  .row.hi{background:rgba(var(--volt-rgb),.09);border-top:1px solid var(--neon);}
  .row .k{font-size:15px;font-weight:800;letter-spacing:.24em;text-transform:uppercase;
    color:var(--muted2);}
  .row .v{font-family:'Archivo';font-style:italic;font-variation-settings:'wdth' 125,'wght' 900;
    text-transform:uppercase;font-size:34px;text-align:right;}
  .row.hi .v{color:var(--volt);}
""")

# ── the link preview ───────────────────────────────────────────────────────
# 1200x630, the one size WhatsApp, iMessage and every other unfurler agrees on.
#
# This is the card that does the explaining now: the sign-up post is a header
# and a numbered list, and the link under it is what tells somebody who has
# never heard of UPRISING what they would be turning up to. It gets ONE glance
# at thumbnail size in a chat, so it carries the name, the one-line rule and
# the three numbers that decide whether you reply — and nothing else.
page("og-card.html", 1200, 630, "54px 60px", f"""
  <div class="top">{MARK}<span class="nm disp">{S['name']}</span>
    <span class="sub">Urban Playground</span></div>
  <div>
    <h2 class="disp">Climb to <em>Court One</em></h2>
    <p class="lede">Come alone. <b>{F['courts']} courts, one ladder</b> — win your match
       and you go up a court, lose it and you go down. Every match is first to {F['target']}.</p>
  </div>
  <div class="foot">
    <div style="display:flex;gap:38px;align-items:flex-end">
      <span class="fact"><b class="disp">{DT.day} {DT.strftime("%b").upper()}</b><i>{DAY}</i></span>
      <span class="fact"><b class="disp">{S['entry']} {CUR}</b><i>To play</i></span>
      <span class="fact"><b class="disp"><u>Up to</u>{S['cap']}</b><i>Places</i></span>
      <span class="fact"><b class="disp">0</b><i>Partners needed</i></span>
    </div>
    <span class="host">{S['host'].upper()}</span>
  </div>
""", """
  .top .nm{font-size:26px;} .top .sub{font-size:11px;}
  h2{font-size:62px;line-height:.92;margin-top:4px;}
  h2 em{font-style:italic;color:var(--volt);text-shadow:0 0 40px rgba(var(--volt-rgb),.45);}
  .lede{font-size:21px;margin-top:16px;max-width:1010px;}
  .foot{padding-top:22px;}
  .fact b{font-size:34px;} .fact i{font-size:10px;}
  .host{font-size:13px;text-align:right;white-space:nowrap;}
""")

# ── the meta tags on the app ───────────────────────────────────────────────
# Spliced into americano-index.html between markers, the same way the engine
# is spliced in by build-americano-app.py. They live there rather than being
# hand-written because the description carries the DATE: typed once it is right
# for a month and quietly wrong after that, on the one surface nobody re-reads.
APP = os.path.join(HERE, "americano-index.html")
OG_START = "<meta property=\"og:type\" content=\"website\" />"
OG_END = "<!-- ═══ END UPRISING LINK PREVIEW"

# WhatsApp truncates a description at roughly 150 characters and shows the rest
# to nobody, so the sentence that explains the format comes first and the three
# figures that decide whether somebody replies come second.
OG_DESC = (f"Come alone, no partner needed. {F['courts']} courts, one ladder: win and "
           f"you go up a court, lose and you go down. {DATE_SHORT.title()} · "
           f"{S['entry']} {CUR} · up to {S['cap']} places.")
OG = "\n".join([
    OG_START,
    '<meta property="og:site_name" content="Urban Playground" />',
    f'<meta property="og:url" content="https://{S["host"]}/" />',
    f'<meta property="og:title" content="{S["name"]} — {S["tagline"].rstrip(".")}" />',
    f'<meta property="og:description" content="{OG_DESC}" />',
    f'<meta property="og:image" content="https://{S["host"]}/og-card.jpg" />',
    '<meta property="og:image:width" content="1200" />',
    '<meta property="og:image:height" content="630" />',
    f'<meta property="og:image:alt" content="{S["name"]} — {S["tagline"].lower()} '
    f'{F["courts"]} courts, one ladder." />',
    '<meta name="twitter:card" content="summary_large_image" />',
    f'<meta name="description" content="{S["name"]} — a {S["cadence"]} padel social at '
    f'Urban Playground. {F["courts"]} courts, one ladder: win and you climb, lose and '
    f'you drop. Come on your own." />',
    "",
])
_app = open(APP).read()
_i, _j = _app.find(OG_START), _app.find(OG_END)
if _i < 0 or _j < 0 or _j < _i:
    sys.exit("!! americano-index.html has no UPRISING LINK PREVIEW block — the "
             "markers were renamed or removed; see the head of that file")
_new = _app[:_i] + OG + _app[_j:]
if _new != _app:
    open(APP, "w").write(_new)
    print("  rewrote the link-preview tags in americano-index.html"
          " — rebuild and deploy the app for them to go live")

if len(OG_DESC) > 150:
    print(f"  !! og:description is {len(OG_DESC)} chars — WhatsApp will cut it at ~150")

# ── the app's home screen ──────────────────────────────────────────────────
# The same splice again, for the facts the HOME screen prints. Only what the
# engine cannot know goes in: when, how much, what you win. The court count,
# the target and the points table are read from the inlined engine by the
# component itself, exactly as the RULES screen reads them — two sources for
# one number is how a rules page ends up disagreeing with the scoring.
NEXT_START = "const UP_NEXT = {"
NEXT_END = "// ═══ END UPRISING NEXT NIGHT"
NEXT = ("const UP_NEXT = {\n"
        f'  date: "{S["date"]}",\n'
        f'  dateLabel: "{DATE_SHORT.title()}",\n'
        f'  entry: "{S["entry"]} {CUR}",\n'
        f'  cap: {S["cap"]},\n'
        f'  champion: "{CHAMP_FULL}",\n'
        f'  signupVia: "{S["signupVia"]}",\n'
        f'  cadence: "{S["cadenceLine"]}"\n'
        "};\n")
_app = open(APP).read()
_i, _j = _app.find(NEXT_START), _app.find(NEXT_END)
if _i < 0 or _j < 0 or _j < _i:
    sys.exit("!! americano-index.html has no UPRISING NEXT NIGHT block — the "
             "markers were renamed or removed; see the Home component")
_new = _app[:_i] + NEXT + _app[_j:]
if _new != _app:
    open(APP, "w").write(_new)
    print("  rewrote UP_NEXT in americano-index.html"
          " — rebuild and deploy the app for it to go live")

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
WHATSAPP 1 — the announcement (paste with post-1-hero.png)
{HR}

🏆 *{S['name']}* — a brand new padel night. *{WHEN.title()}, {DATE_LONG}.*

Come on your own. No partner needed. You will play with a different
partner almost every round.

*{F['courts']} courts, one ladder.* Win your match and you move UP a court.
Lose it and you move DOWN. The court you are standing on is your
position — and everyone can see it from the car park.

*How a match works:* every rally you win is a point. No 15-30-40, no
games, no sets. First pair to {F['target']} wins and you move on — so a score
always looks like {F['target']}-7.

*How the night is won:* the {F['target']} decides the match and then goes nowhere
near the table. What you BANK is what the COURT pays — {F['win']['1']} points for a
win on Court 1, down to {F['win'][str(F['courts'])]} on Court {F['courts']}. So a loss at the top is worth
a win in the middle, and there is nothing to gain from camping at the
bottom. Highest total at the end takes the night. 👑

• Up to {F['matches']} matches each — not three
• First to {F['target']}, straight rallies
• {S['entry']} {CUR} · up to {S['cap']} places, then a waitlist
• 👑 Champion takes a *{CHAMP_FULL}*{f'''
• ⚡ {"STRONGEST FINISH — biggest second half of the night — plays the next one FREE" if FIRST else "THE CLIMB — most points above your own average — plays the next one FREE"}''' if SECOND else ""}
{"• 🔥 Last round is worth DOUBLE" if DBL else "• 🪜 " + plural(F["courts"], "court") + ", one ladder, " + plural(EACH, "match") + " each"}

Round one is the shuffle: it decides which court you start on and scores
nothing, so nobody is placed by a draw. You earn where you stand.

*Reply with a 👍 to claim a place.* Monthly from here.
{S['host']}

{HR}
WHATSAPP 2 — the short one (for busy groups, or a forward)
{HR}

🏆 *{S['name']}* — {WHEN.lower()}, {DATE_SHORT.title()}.

{F['courts']} courts, one ladder. Win and you climb a court, lose and you drop
one. Up to {F['matches']} matches, a new partner almost every round, come on your
own. First to {F['target']} — straight rallies, no games, no sets.

{S['entry']} {CUR} · up to {S['cap']} places · champion takes a {CHAMP_FULL}
{"Last round counts double, so it is not over until it is over." if DBL else "The table is live all night — highest total at the end takes it."}

👍 to claim a place → {S['host']}

{HR}
WHATSAPP 3 — the reminder, a few hours before
{HR}

(Send this on the day itself, not the night before — hence "today".)

⏳ *{S['name']} is today* — a few places left.

Come alone, we sort the pairs. Win a match, climb a court; lose one, drop
a court. {S['entry']} {CUR}, up to {F['matches']} matches, a {CHAMP_FULL} to the champion.

Last call — 👍 and you are in.

{HR}
WHATSAPP 4 — the answer to "what even is it?"
{HR}

It is not an Americano and it is not a league. 🪜

Four courts ranked 1 to 4. You win your match, you move up a court. You
lose it, you move down. Every round you get a new partner on whatever
court you landed on.

A match is first to {F['target']} rallies — that is just how the match ends.
What goes on the leaderboard is what the COURT pays:
{PAYS}.

So the whole night is one question: how high can you climb, and can you
stay there. Highest total wins.

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
Champion takes a {CHAMP_FULL}.{f' {"Strongest finisher" if FIRST else "Biggest climb above your own average"} plays next month free.' if SECOND else (" Last round counts double." if DBL else " Highest total at the end takes it.")}

Link in bio to the live ladder.

#urbanplayground #padeloman #padelmuscat #uprising

{HR}
INSTAGRAM STORIES — five cards, post in this order
{HR}

Each card stands on its own — most people see one frame, not five — so the
date and the name are on every one of them. Put the link sticker on every
card, not just the last.

  story-1-name.png     THE HOOK — the name, the date, nothing to read
                       Sticker: link → {S['host']}
                       Overlay (optional): "{S['promise']}"

  story-2-ladder.png   THE IDEA — win and you go up a court
                       Sticker: a poll — "Which court do you finish on?"
                       with COURT 1 / COURT 4 as the two answers

  story-3-match.png    THE QUESTION EVERYONE ASKS — first to {F['target']}
                       Sticker: "Ask me anything" so the replies come to you

  story-4-prizes.png   THE STAKES — {CHAMP_FULL} to the champion
                       Sticker: countdown to {DATE_SHORT.title()}

  story-5-claim.png    THE ASK — reply and you are in
                       Sticker: link → {S['host']}, plus "DM to claim a place"

Posting them one a day in the week before works better than five at once.
On the day, re-post story-5 on its own with the countdown sticker.

{HR}
THE ONE-LINER, if you only get a sentence
{HR}

"{F['courts']} courts, one ladder — win and you climb, lose and you drop.
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
  for a social — but do not sell it as a ranking tournament.{"" if SECOND else '''
· Not a second prize, a runner-up prize or a free entry. There is ONE prize
  this night and the cards say so. If one is added later, set secondPrize in
  uprising-social.json and re-render rather than promising it in a message.'''}
· Not a finals night, a season table or a league. This is one night, monthly.
· Not "{S['championPrize']} {CUR}" on its own — it is a {KIND or "prize"}, and every line above
  says so. Somebody turning up expecting cash and being handed a {KIND or "prize"} was
  misled by our own poster.
· Not a start time, until the court is confirmed. The posts carry the date and
  nothing on the clock on purpose; a poster reshot because the time moved is
  worse than one that never claimed it.
""")

N_PAGES = len([x for x in os.listdir(OUT) if x.endswith(".html")])
print(f"UPRISING announcement — {DATE_LONG}, {S['start']}–{END}")
print(f"  {F['players']} players · {F['courts']} courts · {F['matches']} matches "
      f"({F['scoring']} scoring + the shuffle) · first to {F['target']} · {F['minutes']} min")
print(f"  {S['entry']} {CUR} in · champion {CHAMP_FULL} · "
      + (f"{SECOND_NAME.lower()}: {S['climbPrize'].lower()}" if SECOND
         else "no second prize advertised"))
print(f"  wrote {N_PAGES} pages + CAPTIONS.txt to {OUT}")
