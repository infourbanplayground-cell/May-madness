# -*- coding: utf-8 -*-
"""Blackout Series Vol.8 — the FINAL WEEK film. 1080x1920, ~35s.

Three nights left of nine. The film's job is to make a player who has drifted
turn up for them, so it is built out of the one thing that does that: the actual
table, and how close it is.

EVERY NUMBER IS COMPUTED, none typed — and not computed here either. It reads
ops/blackout-standings.mjs, which lifts the scoring engine out of
blackout-index.html at run time and runs it over the live state. A hype film
that disagrees with the leaderboard everyone is looking at is worse than none,
and this repo has made that mistake on a link preview already.

WHAT IT DELIBERATELY DOES NOT CLAIM. It never states what a doubled night is
worth in points. The 2X multiplier applies to everything except the streak
bonus, so "the biggest night so far was +33, doubled that is +66" is not true
in general — it is close, and close is how a film ends up contradicting the
app. It prints the biggest night actually recorded and the fact that the last
two count twice, and lets the reader do their own arithmetic.

Deterministic, like every film in this repo: no CSS animations anywhere, every
moving value a pure function of t behind window.__seek(t).

  ssh urbanpadel 'curl -s localhost:3009/state' > $SP/bo.json
  node ops/blackout-standings.mjs $SP/bo.json $SP/bo-standings.json
  python3 build-finalweek-video.py
  python3 build-finalweek-audio.py
  node record-finalweek-video.mjs
"""
import base64, datetime, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SP = "/tmp/claude-0/-home-user-May-madness/0e44f0ad-a683-5f0d-9de6-9459ae328963/scratchpad"
VID = os.path.join(SP, "video")
STD = os.path.join(SP, "bo-standings.json")
OUT = os.path.join(SP, "finalweek.html")

W, H = 1080, 1920
LIME, MAGENTA, INK, MUTED, BG = "#C6FF00", "#FF2E88", "#F2F2F2", "#9A9A9A", "#050505"
# From blackout-season.json's palette notes: uv is a STRUCTURE colour and not a
# text colour on black (3.1:1 fails at body size). It is used here only for the
# chart's also-rans, as line ink at 6px, which is not body text.
UV, LIMEPALE = "#7B2BFF", "#E9FF86"

# Scene table — shared verbatim with build-finalweek-audio.py, so the hits land
# on the cuts rather than near them.
SCENES = [0.00, 4.00, 9.40, 15.00, 19.40, 24.20, 28.00, 31.20]
DUR = 35.40
BEATS = [0.14, 1.05, 4.02, 9.42, 15.02, 16.60, 19.42, 21.00, 24.22, 25.60,
         28.02, 31.22, 32.50]
# The two moments the whole film is built around: the 2X reveal and the cut to
# the dates. Both get a drop in the score.
HERO = [19.42, 31.22]

DAYS = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]
MONS = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN",
        "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]


def b64(p):
    with open(p, "rb") as f:
        return base64.b64encode(f.read()).decode()


def inline_fonts():
    css = open(os.path.join(VID, "fonts", "fonts.css")).read()
    seen = {}

    def sub(m):
        n = m.group(1)
        if n not in seen:
            seen[n] = b64(os.path.join(VID, "fonts", n))
        return "url(data:font/woff2;base64,%s) format('woff2')" % seen[n]

    css = re.sub(r"url\(([0-9a-f]+\.woff2)\)\s*format\('woff2'\)", sub, css)
    assert ".woff2)" not in css, "a font file was left as an external reference"
    return css


def short(d):
    """MON 26 — the form the posts use. Never from an ISO string on this box:
    the server is UTC+4 and the date would be a day behind."""
    x = datetime.date.fromisoformat(d)
    return f"{DAYS[x.weekday()]} {x.day}"


def lead_changes(race):
    """How many times the top of the table actually changed hands.

    Ranked on points alone across the tracked players, and a tie counts as no
    change: whoever was leading keeps it until somebody is outright ahead. The
    chart in the same scene is the evidence for whatever this returns, so the
    copy it drives cannot be the only claim on screen.
    """
    seq, who = [], None
    for i in range(len(race[0]["pts"])):
        rank = sorted(race, key=lambda r: -r["pts"][i])
        if len(rank) > 1 and rank[0]["pts"][i] == rank[1]["pts"][i]:
            seq.append(who)
            continue
        who = rank[0]["name"]
        seq.append(who)
    return sum(1 for a, b in zip(seq, seq[1:]) if a and b and a != b), seq


def main():
    if not os.path.exists(STD):
        sys.exit("missing bo-standings.json — run:\n"
                 "  ssh urbanpadel 'curl -s localhost:3009/state' > %s/bo.json\n"
                 "  node ops/blackout-standings.mjs %s/bo.json %s" % (SP, SP, STD))
    d = json.load(open(STD))
    cfg = json.load(open(os.path.join(HERE, "blackout-season.json")))

    # Guards. Each one is a way this film could go out wrong, and every one of
    # them has an equivalent that has already bitten this repo once.
    assert d["remaining"], "no nights left — this is a recap, not a final-week film"
    assert d["finalsDate"] in d["remaining"], \
        "the finals night has already been played; the film's outro is wrong"
    assert d["doubleNights"], \
        "no doubled nights remain — scene 5 is the spine of the film and would be a lie"
    assert len(d["table"]) >= 4, "fewer than four players in the series"
    assert d["pool"] == cfg["voucher"] * 2 * cfg["sessions"] + sum(cfg["seasonPrizes"]), \
        "the pool does not reconcile with its parts"

    top = d["table"][:4]
    race = d["race"][:4]
    climber = d["climber"]
    crow = next(r for r in d["table"] if r["id"] == climber["id"])
    changes, seq = lead_changes(d["race"])

    # Scene 3's headline is derived, not chosen: with the lead having changed
    # hands the chart is a race, and without it it is a procession, and those
    # are different films.
    s3head = "THE LEAD HAS\nCHANGED HANDS." if changes else "ONE NAME\nAT THE TOP."
    s3sub = (f"{changes} TIME" + ("S" if changes != 1 else "")
             + f" IN {d['played']} NIGHTS") if changes else f"{d['played']} NIGHTS RUNNING"

    rows = "".join(
        f'<div class="std{" ld" if i == 0 else ""}{" cl" if r["id"] == climber["id"] else ""}" id="t{i}">'
        f'<span class="pos">{i+1}</span>'
        f'<span class="who">{r["name"].upper()}</span>'
        f'<span class="amt">{r["pts"]}</span></div>'
        for i, r in enumerate(top))

    legend = "".join(
        f'<div class="lg" id="l{i}"><span class="sw" style="background:{c}"></span>'
        f'<span class="ln">{r["name"].upper()}</span></div>'
        for i, (r, c) in enumerate(zip(race, (LIME, INK, MUTED, MAGENTA))))

    dbl = " & ".join(short(x) for x in d["doubleNights"])
    datesline = " · ".join(short(x) for x in d["remaining"])
    fin = datetime.date.fromisoformat(d["finalsDate"])

    payload = json.dumps({
        "scenes": SCENES, "dur": DUR, "beats": BEATS, "hero": HERO,
        "rows": len(top), "legend": len(race), "played": d["played"],
        "left": len(d["remaining"]), "gap": d["gap14"], "best": d["bestNight"],
        "climb": climber["last2"], "nights": d["sessionsTotal"],
        # The chart draws from the engine's own cumulative totals, with each
        # line starting at the night that player first appeared.
        "race": [{"name": r["name"], "pts": r["pts"], "from": r["from"],
                  "ink": c} for r, c in zip(race, (LIME, INK, MUTED, MAGENTA))],
    })

    mark = open(os.path.join(HERE, "brand", "blackout", "blackout-mark.svg")).read()
    html = TEMPLATE.format(
        faces=inline_fonts(), data=payload, W=W, H=H,
        mark=base64.b64encode(mark.encode()).decode(),
        lime=LIME, magenta=MAGENTA, ink=INK, muted=MUTED, bg=BG,
        uv=UV, limepale=LIMEPALE,
        host=cfg["host"].upper(), month=cfg["monthUpper"],
        rows=rows, legend=legend,
        left=len(d["remaining"]), nights=d["sessionsTotal"], played=d["played"],
        matches=d["matches"], playersin=d["playersIn"],
        dates=datesline, dbl=dbl,
        s3head=s3head, s3sub=s3sub,
        climber=climber["name"].upper(), climbnights=crow["nights"],
        climbtitles=crow["titles"], climbpts=crow["pts"],
        climbrank=next(i + 1 for i, r in enumerate(d["table"]) if r["id"] == climber["id"]),
        gap=d["gap14"], best=d["bestNight"],
        prizes=" / ".join(str(p) for p in cfg["seasonPrizes"]),
        voucher=cfg["voucher"], entry=cfg["entry"],
        finalsday=f"{DAYS[fin.weekday()]} {fin.day} {MONS[fin.month - 1]}",
    )
    with open(OUT, "w") as f:
        f.write(html)

    print(f"built finalweek.html  {len(html.encode())/1024/1024:.1f}MB  {DUR:.1f}s")
    print(f"  {d['played']}/{d['sessionsTotal']} nights played, {d['matches']} matches, "
          f"{d['playersIn']} players in the series")
    print(f"  left      {datesline}   (double: {dbl}, finals {d['finalsDate']})")
    print(f"  lead      changed hands {changes}x  ->  {' '.join(s or '-' for s in seq)}")
    for i, r in enumerate(top):
        print(f"    {i+1}. {r['name']:<20} {r['pts']:>4}   "
              f"{r['nights']}n {r['wins']}/{r['played']}w {r['titles']}t")
    print(f"  gap 1-4   {d['gap14']} points")
    print(f"  form      {climber['name']} +{climber['last2']} in the last two nights")
    print(f"  best      +{d['bestNight']} is the biggest night anyone has had")

    # The posts the film goes out with, written from the same figures so a
    # caption cannot contradict the thing it is captioning. Everything in them
    # that is a number came out of the engine above.
    cap = os.path.join(SP, "finalweek-captions.txt")
    t1, t4 = d["table"][0], d["table"][3]
    with open(cap, "w") as f:
        f.write(f"""WHATSAPP — the group
\u2b1b\ufe0f BLACKOUT \u2014 FINAL WEEK

{d['played']} nights down, {len(d['remaining'])} to go.

{t1['name']} leads on {t1['pts']}. {d['gap14']} points cover the top four.
{dbl} are DOUBLE POINTS \u2014 the last two nights count twice.
No finals cut: night {d['sessionsTotal']} is open to everyone.

{datesline} \u00b7 5:30 PM \u00b7 {cfg['entry']} OMR a night
{cfg['host']}


WHATSAPP — short
Final week of BLACKOUT. {datesline}, 5:30.
{d['gap14']} points cover the top four and the last two nights are double.
{cfg['host']}


INSTAGRAM
FINAL WEEK.

{d['played']} nights played, {d['matches']} matches, {d['playersIn']} players on the board \u2014 and {d['gap14']} points
between first and fourth.

{climber['name']} has taken +{climber['last2']} out of the last two nights.
{dbl} are double points.
Season top three take {' / '.join(str(p) for p in cfg['seasonPrizes'])} OMR.

{datesline} \u00b7 5:30 PM \u00b7 {cfg['host']}

#urbanplayground #padel #muscat #oman #blackoutseries
""")
    print(f"  captions  {cap}")
    print("\nnow:  python3 build-finalweek-audio.py && node record-finalweek-video.mjs")


TEMPLATE = r"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
{faces}
*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{width:{W}px;height:{H}px;background:{bg};overflow:hidden}}
body{{font-family:'Archivo',sans-serif;color:{ink};-webkit-font-smoothing:antialiased}}
#cam{{position:absolute;inset:0;transform-origin:50% 50%;background:{bg}}}
.wash{{position:absolute;inset:0;pointer-events:none;
  background:radial-gradient(circle at 100% 14%, rgba(255,46,136,.18), transparent 44%),
             radial-gradient(circle at 0% 92%, rgba(198,255,0,.10), transparent 42%)}}
.scan{{position:absolute;inset:-40px;pointer-events:none;
  background:repeating-linear-gradient(0deg, rgba(198,255,0,.05) 0 2px, transparent 2px 10px)}}
.rail{{position:absolute;left:0;right:0;height:10px;background:{lime};transform-origin:0 50%}}
/* Content sits between roughly y=380 and y=1340, which centres on 860 in a 1920
   frame — top-heavy, with a dead bottom third where a phone's UI chrome and the
   caption land. The whole layer drops rather than every `top` being re-typed. */
.scene{{position:absolute;inset:0;transform:translateY(90px);
  will-change:opacity,transform}}
.disp{{font-style:italic;font-variation-settings:'wdth' 125,'wght' 900;line-height:.88;
  letter-spacing:-.5px;white-space:pre-line}}
.kick{{font-family:'JetBrains Mono',monospace;font-weight:700;letter-spacing:.3em;color:{lime}}}
.mono{{font-family:'JetBrains Mono',monospace;font-weight:700}}
.ctr{{position:absolute;left:0;right:0;text-align:center}}
/* A .fit line is shrunk to the frame, which only works if it is allowed to
   be ONE line. Left to wrap it never overflows, the fit pass finds nothing to
   do, and the second line lands on whatever sits below it — which is how
   FINAL WEEK ended up underneath 3 NIGHTS LEFT with every check green. */
.fit{{white-space:nowrap}}
/* Standings rows: rank, name, points. The points column is right-aligned on
   its own so four different name lengths cannot make four different number
   positions. No overflow:hidden — a clipped name reads as a bug in motion, and
   the recorder fails the render if anything is clipped. */
.std{{display:flex;align-items:center;gap:22px;padding:16px 0;
  border-bottom:3px solid rgba(242,242,242,.10);will-change:transform,opacity}}
.std .pos{{font-family:'JetBrains Mono',monospace;font-weight:700;font-size:28px;
  color:{muted};width:46px}}
.std .who{{flex:1;min-width:0;font-style:italic;
  font-variation-settings:'wdth' 104,'wght' 900;font-size:48px;white-space:nowrap}}
.std .amt{{font-style:italic;font-variation-settings:'wdth' 110,'wght' 900;
  font-size:62px;color:{ink}}}
.std.ld .amt{{color:{lime}}}
.std.ld .who{{color:{lime}}}
.std.cl .amt{{color:{magenta}}}
.std.cl .who{{color:{magenta}}}
/* Chart legend: a swatch and a name, two up, so four names fit without
   shrinking the type to the point of uselessness on a phone. */
#s3lg{{display:flex;flex-wrap:wrap;gap:16px 40px}}
.lg{{display:flex;align-items:center;gap:14px;width:380px;will-change:opacity}}
.lg .sw{{width:34px;height:8px;flex:0 0 auto}}
.lg .ln{{font-family:'JetBrains Mono',monospace;font-weight:700;font-size:24px;
  letter-spacing:.1em;color:{muted};white-space:nowrap}}
/* Square corners everywhere — Blackout has no radius. */
.plate{{border:3px solid rgba(242,242,242,.14);background:rgba(255,255,255,.03)}}
.flash{{position:absolute;inset:0;pointer-events:none;background:{lime};
  mix-blend-mode:screen;opacity:0}}
</style></head><body>

<div id="cam">
  <div class="wash"></div><div class="scan" id="scan"></div>
  <div class="rail" id="rail" style="top:0"></div>

  <!-- 1 · title -->
  <div class="scene" id="s1">
    <div style="position:absolute;left:50%;top:380px;width:156px;height:156px;margin-left:-78px" id="s1m">
      <img src="data:image/svg+xml;base64,{mark}" style="width:100%;display:block">
    </div>
    <div class="kick ctr" style="top:606px;font-size:26px" id="s1k">BLACKOUT SERIES &middot; VOL.8</div>
    <div class="disp ctr fit" style="top:672px;font-size:196px" id="s1t">FINAL WEEK</div>
    <div class="disp ctr" style="top:896px;font-size:86px;color:{lime}" id="s1g">{left} NIGHTS LEFT.</div>
    <div style="position:absolute;left:50%;top:1046px;width:460px;height:5px;margin-left:-230px;background:{lime}" id="s1r"></div>
    <div class="mono ctr fit" style="top:1114px;font-size:32px;letter-spacing:.2em;color:{muted}" id="s1s">{dates} {month}</div>
  </div>

  <!-- 2 · where it stands -->
  <div class="scene" id="s2">
    <div class="kick ctr" style="top:400px;font-size:24px" id="s2k">{played} NIGHTS DOWN &middot; {matches} MATCHES</div>
    <div class="disp ctr" style="top:454px;font-size:140px" id="s2t">WHERE IT
STANDS</div>
    <div id="s2g" style="position:absolute;left:96px;right:96px;top:700px">{rows}</div>
    <div class="ctr" style="top:1172px;font-size:34px;color:{muted}" id="s2n">{playersin} players have scored this volume.</div>
  </div>

  <!-- 3 · the race -->
  <div class="scene" id="s3">
    <div class="kick ctr" style="top:300px;font-size:24px" id="s3k">{s3sub}</div>
    <div class="disp ctr" style="top:356px;font-size:98px" id="s3h">{s3head}</div>
    <canvas id="chart" width="900" height="500" style="position:absolute;left:90px;top:648px"></canvas>
    <div id="s3lg" style="position:absolute;left:96px;right:96px;top:1190px">{legend}</div>
    <div class="mono ctr" style="top:1320px;font-size:24px;letter-spacing:.2em;color:{muted}" id="s3f">SERIES POINTS AFTER EACH NIGHT</div>
  </div>

  <!-- 4 · form -->
  <div class="scene" id="s4">
    <div class="kick ctr" style="top:420px;font-size:24px;color:{magenta}" id="s4k">FORM</div>
    <div class="disp ctr fit" style="top:476px;font-size:128px;color:{magenta}" id="s4n">{climber}</div>
    <div class="ctr" id="s4b" style="top:650px">
      <span class="disp" style="font-size:216px;color:{magenta}" id="s4v">0</span>
    </div>
    <div class="disp ctr" style="top:900px;font-size:74px" id="s4t">IN THE LAST
TWO NIGHTS.</div>
    <div style="position:absolute;left:140px;right:140px;top:1086px;height:3px;background:rgba(242,242,242,.14)" id="s4r"></div>
    <div class="mono ctr" style="top:1136px;font-size:30px;letter-spacing:.18em;color:{muted}" id="s4s">{climbnights} NIGHTS PLAYED &middot; {climbtitles} WON &middot; {climbrank}TH ON {climbpts}</div>
  </div>

  <!-- 5 · the multiplier. the one scene in magenta end to end: it is the rare
       colour and this is the one thing that scores. -->
  <div class="scene" id="s5">
    <div class="kick ctr" style="top:440px;font-size:26px;color:{magenta}" id="s5k">{dbl}</div>
    <div class="ctr" id="s5b" style="top:496px">
      <span class="disp" style="font-size:300px;color:{magenta}" id="s5x">2X</span>
    </div>
    <div class="disp ctr" style="top:850px;font-size:112px" id="s5t">DOUBLE
POINTS.</div>
    <div style="position:absolute;left:50%;top:1092px;width:400px;height:5px;margin-left:-200px;background:{magenta}" id="s5r"></div>
    <div class="ctr" style="top:1152px;font-size:40px" id="s5s">The last two nights count twice.</div>
  </div>

  <!-- 6 · how close it is -->
  <div class="scene" id="s6">
    <div class="kick ctr" style="top:470px;font-size:24px" id="s6k">FIRST TO FOURTH</div>
    <div class="ctr" id="s6b" style="top:520px">
      <span class="disp" style="font-size:264px;color:{lime}" id="s6v">0</span>
    </div>
    <div class="disp ctr" style="top:812px;font-size:92px" id="s6t">POINTS APART.</div>
    <div style="position:absolute;left:140px;right:140px;top:980px;height:3px;background:rgba(242,242,242,.14)" id="s6r"></div>
    <div class="ctr" style="top:1030px;font-size:38px;color:{muted}" id="s6n">
      Biggest night anyone has had: <b style="color:{limepale}">+{best}</b></div>
    <div class="disp ctr" style="top:1120px;font-size:76px;color:{magenta}" id="s6s">ONE NIGHT
DECIDES IT.</div>
  </div>

  <!-- 7 · what is still to win -->
  <div class="scene" id="s7">
    <div class="kick ctr" style="top:420px;font-size:24px" id="s7k">STILL TO WIN</div>
    <div class="disp ctr fit" style="top:476px;font-size:148px;color:{lime}" id="s7t">{prizes}</div>
    <div class="mono ctr" style="top:672px;font-size:30px;letter-spacing:.22em;color:{muted}" id="s7s">OMR &middot; SEASON TOP THREE</div>
    <div style="position:absolute;left:140px;right:140px;top:790px;height:3px;background:rgba(242,242,242,.14)" id="s7r"></div>
    <div class="ctr" style="top:844px;font-size:40px" id="s7a">
      <b style="color:{lime}">{voucher} OMR</b> to each winner, every night</div>
    <div class="disp ctr" style="top:960px;font-size:82px" id="s7d">NO FINALS
CUT.</div>
    <div class="ctr" style="top:1156px;font-size:36px;color:{muted}" id="s7n">Night {nights} is open to everyone.</div>
  </div>

  <!-- 8 · the dates -->
  <div class="scene" id="s8">
    <div class="disp ctr" style="top:460px;font-size:126px" id="s8t">SEE IT
OUT.</div>
    <div style="position:absolute;left:50%;top:756px;width:520px;height:5px;margin-left:-260px;background:{lime}" id="s8r"></div>
    <div class="mono ctr fit" style="top:816px;font-size:38px;letter-spacing:.14em;color:{lime}" id="s8d">{dates} &middot; 5:30 PM</div>
    <div class="mono ctr" style="top:892px;font-size:26px;letter-spacing:.22em;color:{muted}" id="s8f">FINALS NIGHT &middot; {finalsday}</div>
    <div class="disp ctr fit" style="top:986px;font-size:58px;color:{lime}" id="s8u">{host}</div>
    <div class="mono ctr" style="top:1086px;font-size:28px;letter-spacing:.22em;color:{muted}" id="s8e">{entry} OMR A NIGHT</div>
    <div style="position:absolute;left:50%;top:1174px;width:124px;height:124px;margin-left:-62px" id="s8m">
      <img src="data:image/svg+xml;base64,{mark}" style="width:100%;display:block">
    </div>
    <div class="mono ctr" style="top:1360px;font-size:24px;letter-spacing:.3em;color:#6E6E6E">URBAN PLAYGROUND &middot; MUSCAT</div>
  </div>
</div>
<div class="flash" id="flash"></div>

<script>
const D = {data};
const DUR = D.dur, XF = 0.14;
const clamp=(v,a=0,b=1)=>Math.max(a,Math.min(b,v));
const inv=(t,a,b)=>clamp((t-a)/(b-a));
const outCubic=x=>1-Math.pow(1-x,3);
const outQuint=x=>1-Math.pow(1-x,5);
const outExpo =x=>x>=1?1:1-Math.pow(2,-10*x);
const outBack =x=>{{const c1=2.0,c3=c1+1;return 1+c3*Math.pow(x-1,3)+c1*Math.pow(x-1,2);}};
const HERO=new Set(D.hero);

function set(el,o,tr,fl){{
  el.style.opacity=o.toFixed(3);
  if(tr!==undefined) el.style.transform=tr;
  if(fl!==undefined) el.style.filter=fl;
}}
// The Vol.8 entrance: type arrives condensed and opens to full width. Needs a
// VARIABLE font — a static instance accepts 'wdth' and nothing moves, which is
// why the recorder measures it rather than trusting it.
function widen(el,t,t0,d,{{w0=66,w1=125,blur=12}}={{}}){{
  const p=outExpo(inv(t,t0,t0+d)), o=inv(t,t0,t0+d*0.3);
  el.style.fontVariationSettings=`'wdth' ${{(w0+(w1-w0)*p).toFixed(1)}},'wght' 900`;
  set(el,o,`scale(${{(1+0.04*(1-p)).toFixed(4)}})`,`blur(${{(blur*(1-p)).toFixed(2)}}px)`);
}}
function rise(el,t,t0,d,px){{
  set(el, inv(t,t0,t0+d*0.5),
      `translateY(${{(px*(1-outQuint(inv(t,t0,t0+d)))).toFixed(1)}}px)`);
}}
// Shrink-to-fit, once the real face is in. document.fonts.status reads "loaded"
// before any face has been requested, so gating on it measures fallback metrics
// and shrinks nothing.
let fitted=false;
function fitOnce(){{
  if(fitted || !document.fonts.check("italic 900 40px Archivo")) return;
  // Every scene must be laid out to be measured. A scene left display:none by
  // the previous seek measures 0 wide, which reads as "it fits" and ships the
  // headline overrunning the frame.
  const hidden=[...document.querySelectorAll('.scene')].map(s=>[s,s.style.display]);
  hidden.forEach(([s])=>{{s.style.display='block';}});
  const MAX={W}-110;
  for(const el of document.querySelectorAll('.fit')){{
    if(!el.firstElementChild || !el.firstElementChild.classList.contains('fitspan'))
      el.innerHTML=`<span class="fitspan" style="display:inline-block">${{el.textContent}}</span>`;
    const base=parseFloat(getComputedStyle(el).fontSize);
    const keep=el.style.fontVariationSettings;
    el.style.fontVariationSettings="'wdth' 125,'wght' 900";
    const w=el.firstElementChild.getBoundingClientRect().width;
    el.style.fontVariationSettings=keep;
    if(w>MAX) el.style.fontSize=(base*MAX/w).toFixed(2)+'px';
  }}
  hidden.forEach(([s,d])=>{{s.style.display=d;}});
  fitted=true; document.body.dataset.fitted='1';
}}

function energy(t){{
  let e=0,h=0;
  for(const b of D.beats){{
    if(t<b-0.02||t>b+0.5) continue;
    const u=(t-b)/0.5, v=Math.max(0,Math.pow(1-u,3));
    e=Math.max(e,v); if(HERO.has(b)) h=Math.max(h,v);
  }}
  return [e,h];
}}

// ── the race chart ─────────────────────────────────────────────────────────
// Drawn with flat shapes only: no canvas animation, no requestAnimationFrame.
// The reveal is a function of p, so scrubbing to a time redraws exactly the
// same pixels every run.
const CV=document.getElementById('chart'), CX=CV.getContext('2d');
const NN=D.race[0].pts.length;
const PAD={{l:92,r:30,t:24,b:52}};
const MAXP=Math.max(...D.race.flatMap(r=>r.pts));
// The y axis is scaled to a round number above the leader, so the gridlines
// land on readable values rather than on the leader's exact total.
const STEP=50, TOP=Math.ceil(MAXP/STEP)*STEP;
const px=i=>PAD.l+(CV.width-PAD.l-PAD.r)*(NN<=1?0:i/(NN-1));
const py=v=>CV.height-PAD.b-(CV.height-PAD.t-PAD.b)*(v/TOP);

function chart(p){{
  CX.clearRect(0,0,CV.width,CV.height);
  CX.font="700 20px 'JetBrains Mono', monospace";
  CX.textBaseline='middle';
  // gridlines and the points scale
  for(let v=0;v<=TOP;v+=STEP){{
    const y=py(v);
    CX.strokeStyle='rgba(242,242,242,.10)'; CX.lineWidth=2;
    CX.beginPath(); CX.moveTo(PAD.l,y); CX.lineTo(CV.width-PAD.r,y); CX.stroke();
    CX.fillStyle='#6E6E6E'; CX.textAlign='right';
    CX.fillText(String(v), PAD.l-18, y);
  }}
  // night numbers along the foot
  CX.textAlign='center'; CX.fillStyle='#9A9A9A';
  for(let i=0;i<NN;i++) CX.fillText('N'+(i+1), px(i), CV.height-PAD.b+28);

  // the lines, revealed left to right. A player who had not joined yet starts
  // where they joined: a flat line along the axis would say they played those
  // nights and scored nothing.
  const head=p*(NN-1);
  for(const r of D.race){{
    const pts=[];
    for(let i=r.from;i<NN;i++){{
      if(i>head+1e-9) break;
      pts.push([px(i), py(r.pts[i])]);
    }}
    // the partial segment, so the head of the line moves smoothly between nights
    const i0=Math.floor(head), f=head-i0;
    if(f>0 && i0+1<NN && i0>=r.from){{
      const a=r.pts[i0], b=r.pts[i0+1];
      pts.push([px(i0)+(px(i0+1)-px(i0))*f, py(a+(b-a)*f)]);
    }}
    if(pts.length<1) continue;
    CX.strokeStyle=r.ink; CX.lineWidth=6; CX.lineJoin='round'; CX.lineCap='round';
    CX.beginPath(); pts.forEach(([x,y],k)=>k?CX.lineTo(x,y):CX.moveTo(x,y)); CX.stroke();
    const [hx,hy]=pts[pts.length-1];
    CX.fillStyle=r.ink; CX.beginPath(); CX.arc(hx,hy,10,0,Math.PI*2); CX.fill();
  }}
}}

const S=D.scenes, END=[...S.slice(1), DUR];

function seek(t){{
  fitOnce();
  const [e,h]=energy(t);
  const sx=e>0.001?Math.sin(t*118)*6*e:0, sy=e>0.001?Math.cos(t*97)*4.5*e:0;
  document.getElementById('cam').style.transform=
    `translate(${{sx.toFixed(2)}}px,${{sy.toFixed(2)}}px) scale(${{(1+e*0.010).toFixed(4)}})`;
  document.getElementById('flash').style.opacity=(e*0.05+h*0.12).toFixed(3);
  const sc=document.getElementById('scan');
  sc.style.transform=`translateY(${{(t*3.2)%10}}px)`;
  sc.style.opacity=(0.9+e*1.4).toFixed(3);
  document.getElementById('rail').style.transform=
    `scaleX(${{outExpo(inv(t,0.02,0.60)).toFixed(3)}})`;

  for(let i=0;i<S.length;i++){{
    const o=Math.min(inv(t,S[i]-XF,S[i]+0.02), 1-inv(t,END[i],END[i]+XF));
    const el=document.getElementById('s'+(i+1));
    el.style.opacity=o.toFixed(3);
    el.style.display=o<=0.002?'none':'block';
  }}
  const g=(i)=>document.getElementById(i);

  {{ // 1 · title
    const u=t-S[0];
    set(g('s1m'), inv(u,0.10,0.50), `scale(${{(0.86+0.14*outBack(inv(u,0.10,0.80))).toFixed(4)}})`);
    rise(g('s1k'), u, 0.56, 0.54, 12);
    widen(g('s1t'), u, 0.72, 0.82);
    widen(g('s1g'), u, 1.28, 0.62, {{w0:86,blur:7}});
    set(g('s1r'), 1, `scaleX(${{outQuint(inv(u,1.70,2.15)).toFixed(3)}})`);
    set(g('s1s'), inv(u,2.00,2.32));
  }}

  {{ // 2 · where it stands — the four rows land in order, top first
    const u=t-S[1];
    rise(g('s2k'), u, 0.08, 0.40, 10);
    widen(g('s2t'), u, 0.18, 0.66, {{w0:72,blur:9}});
    for(let i=0;i<D.rows;i++){{
      const a=0.72+i*0.26, q=outBack(inv(u,a,a+0.46));
      set(g('t'+i), inv(u,a,a+0.18), `translateX(${{(-34*(1-q)).toFixed(1)}}px)`);
    }}
    rise(g('s2n'), u, 2.10, 0.46, 12);
  }}

  {{ // 3 · the race
    const u=t-S[2];
    rise(g('s3k'), u, 0.08, 0.40, 10);
    widen(g('s3h'), u, 0.18, 0.70, {{w0:72,blur:9}});
    // the chart draws itself across the scene, so the race happens on screen
    chart(outCubic(inv(u,0.70,3.60)));
    CV.style.opacity=inv(u,0.60,0.88).toFixed(3);
    for(let i=0;i<D.legend;i++) set(g('l'+i), inv(u,3.20+i*0.14,3.44+i*0.14));
    set(g('s3f'), inv(u,4.10,4.40));
  }}

  {{ // 4 · form — the number counts up, which is the scene's whole event
    const u=t-S[3];
    rise(g('s4k'), u, 0.06, 0.36, 10);
    widen(g('s4n'), u, 0.16, 0.66, {{w0:76,blur:9}});
    const p=outExpo(inv(u,0.74,1.70));
    set(g('s4b'), inv(u,0.74,0.94), `scale(${{(0.94+0.06*p).toFixed(4)}})`);
    g('s4v').textContent='+'+Math.round(D.climb*p);
    widen(g('s4t'), u, 1.52, 0.64, {{w0:78,blur:8}});
    set(g('s4r'), 1, `scaleX(${{outQuint(inv(u,2.10,2.50)).toFixed(3)}})`);
    set(g('s4s'), inv(u,2.34,2.62));
  }}

  {{ // 5 · the multiplier. The 2X slams in on the drop rather than widening:
     //     it is a stamp, not a sentence.
    const u=t-S[4];
    rise(g('s5k'), u, 0.06, 0.34, 10);
    const q=outBack(inv(u,0.14,0.70));
    set(g('s5b'), inv(u,0.14,0.30),
        `scale(${{(1.34-0.34*q).toFixed(4)}})`, `blur(${{(14*(1-outExpo(inv(u,0.14,0.60)))).toFixed(2)}}px)`);
    widen(g('s5t'), u, 0.86, 0.70, {{w0:72,blur:9}});
    set(g('s5r'), 1, `scaleX(${{outQuint(inv(u,1.52,1.94)).toFixed(3)}})`);
    rise(g('s5s'), u, 1.80, 0.48, 14);
  }}

  {{ // 6 · how close it is
    const u=t-S[5];
    rise(g('s6k'), u, 0.06, 0.36, 10);
    const p=outExpo(inv(u,0.18,1.10));
    set(g('s6b'), inv(u,0.18,0.38), `scale(${{(0.94+0.06*p).toFixed(4)}})`);
    g('s6v').textContent=Math.round(D.gap*p);
    widen(g('s6t'), u, 0.96, 0.62, {{w0:78,blur:8}});
    set(g('s6r'), 1, `scaleX(${{outQuint(inv(u,1.40,1.80)).toFixed(3)}})`);
    rise(g('s6n'), u, 1.64, 0.46, 14);
    widen(g('s6s'), u, 2.06, 0.64, {{w0:76,blur:8}});
  }}

  {{ // 7 · what is still to win
    const u=t-S[6];
    rise(g('s7k'), u, 0.06, 0.36, 10);
    widen(g('s7t'), u, 0.16, 0.68, {{w0:70,blur:10}});
    set(g('s7s'), inv(u,0.78,1.04));
    set(g('s7r'), 1, `scaleX(${{outQuint(inv(u,0.98,1.36)).toFixed(3)}})`);
    rise(g('s7a'), u, 1.22, 0.46, 14);
    widen(g('s7d'), u, 1.56, 0.62, {{w0:74,blur:8}});
    rise(g('s7n'), u, 2.14, 0.46, 12);
  }}

  {{ // 8 · the dates
    const u=t-S[7];
    widen(g('s8t'), u, 0.16, 0.76);
    set(g('s8r'), 1, `scaleX(${{outQuint(inv(u,0.74,1.18)).toFixed(3)}})`);
    set(g('s8d'), inv(u,0.98,1.26));
    set(g('s8f'), inv(u,1.20,1.46));
    widen(g('s8u'), u, 1.42, 0.60, {{w0:80,blur:6}});
    set(g('s8e'), inv(u,1.86,2.12));
    set(g('s8m'), inv(u,2.04,2.38), `scale(${{(0.9+0.1*outBack(inv(u,2.04,2.70))).toFixed(4)}})`);
  }}
}}
window.__seek=seek; window.__dur=DUR; seek(0);
</script></body></html>"""


if __name__ == "__main__":
    main()
