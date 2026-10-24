# -*- coding: utf-8 -*-
"""UPRISING — the night-before film. 1080x1920, ~33s.

Not an explainer and not a poster: a film for the day before, whose job is to
make somebody who has never played the format want tomorrow's place. It opens
on the date, teaches the one rule that makes the night different (the shuffle
sets the ladder, and you climb), and ends on the time and the link.

EVERY FORMAT NUMBER IS READ OUT OF THE ENGINE, via ops/uprising-facts.mjs —
courts, rounds, matches each, running time, the points table, and whether the
last round doubles. Nothing about the format is typed here, which is the same
discipline the cards and the link preview already follow: a post cannot
advertise a figure the app contradicts. Everything the engine cannot know —
the date, the time, the entry, the prize, the cap — comes from
uprising-social.json.

THE DOUBLE FINAL IS CONDITIONAL. `doubleFinal` is false whenever anybody rests
the last round (16 on 3 courts, for instance), and the engine switches the
doubling off with it. Scene 5 is dropped from the film in that case rather than
advertising a rule that will not apply — the same reason the cards drop their
own double-points line.

Deterministic, like every film in this repo: no CSS animations anywhere, every
moving value a pure function of t behind window.__seek(t).

  python3 build-uprising-video.py
  python3 build-uprising-audio.py
  node record-uprising-video.mjs
"""
import base64, datetime, json, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SP = "/tmp/claude-0/-home-user-May-madness/0e44f0ad-a683-5f0d-9de6-9459ae328963/scratchpad"
VID = os.path.join(SP, "video")
OUT = os.path.join(SP, "uprising.html")
OUT_SHORT = os.path.join(SP, "uprising-short.html")

W, H = 1080, 1920
# UPRISING's own palette, not Blackout's. Volt against near-black, with the
# cream for body type; dim is the only grey.
VOLT, INK, CREAM, DIM, VOID = "#00F5C8", "#0A0A10", "#F2F0F7", "#6E6B7A", "#06060A"

# Two cuts of the same film, as scene tables rather than two builders. ORDER
# names which scenes are in the cut and in what sequence; SCENES gives each
# one's start. The short cut keeps the five that carry the night and drops the
# three that explain it — a 15-second reel is a hook, not a rulebook, and the
# shuffle, the clock and the prize are what the caption and the link are for.
#
#   SHORT=1 python3 build-uprising-video.py
FULL = dict(
    order=[1, 2, 3, 4, 5, 6, 7, 8],
    scenes=[0.00, 4.00, 8.20, 12.20, 17.40, 20.80, 24.40, 28.20],
    dur=32.60,
    beats=[0.14, 1.05, 4.02, 8.22, 12.22, 14.00, 17.42, 18.90, 20.82, 24.42,
           28.22, 29.50],
    # The two moments the film is built around: the double final and the cut
    # to the time. Both get a drop in the score.
    hero=[17.42, 28.22],
)
SHORT = dict(
    order=[1, 2, 4, 5, 8],
    scenes=[0.00, 3.00, 5.80, 9.40, 11.80],
    dur=15.00,
    beats=[0.14, 1.05, 3.02, 5.82, 7.60, 9.42, 11.82, 13.10],
    hero=[9.42, 11.82],
)

DAYS = ["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY", "SUNDAY"]
MONS = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN",
        "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
WORDS = {2: "TWO", 3: "THREE", 4: "FOUR", 5: "FIVE", 6: "SIX"}


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


def facts():
    """The format, straight out of the shipped engine."""
    r = subprocess.run([ "node", os.path.join(HERE, "ops", "uprising-facts.mjs") ],
                       capture_output=True, text=True)
    if r.returncode:
        sys.exit("uprising-facts.mjs failed:\n" + r.stderr)
    return json.loads(r.stdout)


def main():
    S = json.load(open(os.path.join(HERE, "uprising-social.json")))
    F = facts()

    DT = datetime.date.fromisoformat(S["date"])
    # Local date, never an ISO slice of a UTC clock: the server is UTC+4 and
    # would call a night "today" that is already tomorrow here.
    now = datetime.datetime.now()
    today = datetime.date(now.year, now.month, now.day)
    when = ("TONIGHT" if DT == today
            else "TOMORROW" if DT == today + datetime.timedelta(days=1) else None)

    if DT < today:
        sys.exit(f"uprising-social.json still says {S['date']}, which has passed — "
                 "roll `date` forward to the next Saturday before building")

    # The kicker over the title is the urgent word when there is one, and the
    # day otherwise. Printing both gave "17 OCT · SATURDAY 17 OCTOBER" on the
    # cards once the night was more than a day out.
    urgent = when or f"{DAYS[DT.weekday()]} {DT.day} {MONS[DT.month - 1]}"
    datestamp = f"{DAYS[DT.weekday()][:3]} {DT.day} {MONS[DT.month - 1]}"

    cut = SHORT if os.environ.get("SHORT") else FULL
    order, scenes = list(cut["order"]), list(cut["scenes"])

    # Scene 5 exists only when the night actually ends on a double round. With
    # anybody resting the last round the engine switches the doubling off, and
    # a film still advertising it would be the one thing this pipeline exists
    # to prevent. Dropping it closes the gap it left rather than holding dead
    # air where it was.
    if not F["doubleFinal"] and 5 in order:
        i = order.index(5)
        gap = (scenes[i + 1] if i + 1 < len(scenes) else cut["dur"]) - scenes[i]
        order.pop(i); scenes.pop(i)
        scenes = scenes[:i] + [x - gap for x in scenes[i:]]

    ladder = "".join(
        f'<div class="crt{" top" if c == 1 else ""}" id="k{c-1}">'
        f'<span class="cn">COURT {c}</span>'
        f'<span class="cw">{F["win"][str(c)]}</span>'
        f'<span class="cl">{F["lose"][str(c)]}</span></div>'
        for c in range(1, F["courts"] + 1))

    hours = F["minutes"] / 60
    runtime = (f"{F['minutes']} MINUTES" if F["minutes"] < 90
               else f"{hours:.0f} HOURS" if abs(hours - round(hours)) < 0.05
               else f"{hours:.1f} HOURS".replace(".0", ""))

    dur = cut["dur"] - (gap if not F["doubleFinal"] and 5 in cut["order"] else 0)
    payload = json.dumps({
        "scenes": scenes, "order": order, "dur": dur,
        "beats": [b for b in cut["beats"] if b < dur],
        "hero": [h for h in cut["hero"] if h < dur],
        "courts": F["courts"], "cap": S["cap"],
        "rounds": F["rounds"], "matches": F["matches"],
    })

    html = TEMPLATE.format(
        faces=inline_fonts(), data=payload, W=W, H=H,
        volt=VOLT, ink=INK, cream=CREAM, dim=DIM, void=VOID,
        name=S["name"], tagline=S["tagline"].upper(), promise=S["promise"],
        urgent=urgent, datestamp=datestamp, cadence=S["cadenceLine"].upper(),
        courts=F["courts"], courtword=WORDS.get(F["courts"], str(F["courts"])),
        cap=S["cap"], rounds=F["rounds"], matches=F["matches"],
        target=F["target"], runtime=runtime, ladder=ladder,
        topwin=F["win"]["1"], botwin=F["win"][str(F["courts"])],
        entry=S["entry"], cur=S["currency"],
        prize=S["championPrize"], kind=S["championPrizeKind"].upper(),
        start=S["start"], doors=S["doors"], host=S["host"].upper(),
    )
    out = OUT_SHORT if os.environ.get("SHORT") else OUT
    with open(out, "w") as f:
        f.write(html)

    print(f"built {os.path.basename(out)}  {len(html.encode())/1024/1024:.1f}MB  {dur:.1f}s"
          f"  scenes {','.join(str(o) for o in order)}")
    print(f"  night     {S['date']} ({urgent.lower()}), doors {S['doors']}, start {S['start']}")
    print(f"  format    {F['courts']} courts, {F['rounds']} rounds, {F['matches']:g} matches each, "
          f"{runtime.lower()}, first to {F['target']}")
    print(f"  points    " + "  ".join(f"C{c}:{F['win'][str(c)]}/{F['lose'][str(c)]}"
                                      for c in range(1, F["courts"] + 1)))
    print(f"  double    {'yes' if F['doubleFinal'] else 'NO — scene 5 dropped'}")
    print(f"  prize     {S['championPrize']} {S['currency']} {S['championPrizeKind']}, "
          f"{S['entry']} {S['currency']} to play, {S['cap']} places")

    # The posts the film goes out with, from the same two sources.
    cap = os.path.join(SP, "uprising-captions.txt")
    dbl = (" The last round is worth double.\n" if F["doubleFinal"] else "")
    with open(cap, "w") as f:
        f.write(f"""WHATSAPP
\U0001f7e9 *{S['name']}* — {urgent.title()}.

{S['tagline']} {S['promise']}

{F['courts']} courts, one ladder. {S['cap']} players, nobody sits out.
Round one is the shuffle: it sets the ladder by your winning margin.
Win and you go up. Courts higher up are worth more.{dbl}
{F['rounds']} rounds, {F['matches']:g} matches each, about {runtime.lower()}.

Champion takes a *{S['championPrize']} {S['currency']} {S['championPrizeKind']}*.
{S['entry']} {S['currency']} to play · doors {S['doors']} · first serve {S['start']}
{S['host']}


INSTAGRAM
{S['tagline']}

{urgent.title()}. {F['courts']} courts, {S['cap']} players, one ladder — and nobody sits out.

The first round is a shuffle: your winning margin sets where you start.
After that it is simple. Win and you climb. The higher the court, the more
a win is worth — {F['win']['1']} points on Court 1 against {F['win'][str(F['courts'])]} on the bottom.{dbl}
{F['rounds']} rounds, {F['matches']:g} matches each, about {runtime.lower()}.

Champion takes a {S['championPrize']} {S['currency']} {S['championPrizeKind']}.
{S['entry']} {S['currency']} · {S['doors']} doors · {S['start']} first serve · {S['host']}

#urbanplayground #padel #muscat #oman #uprising
""")
    print(f"  captions  {cap}")
    print("\nnow:  python3 build-uprising-audio.py && node record-uprising-video.mjs")


TEMPLATE = r"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
{faces}
*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{width:{W}px;height:{H}px;background:{void};overflow:hidden}}
body{{font-family:'Archivo',sans-serif;color:{cream};-webkit-font-smoothing:antialiased}}
#cam{{position:absolute;inset:0;transform-origin:50% 50%;background:{void}}}
/* One light source, high and to the left, so the frame reads as lit rather
   than as type on black. Volt only — UPRISING has no second colour. */
.wash{{position:absolute;inset:0;pointer-events:none;
  background:radial-gradient(circle at 16% 10%, rgba(0,245,200,.16), transparent 46%),
             radial-gradient(circle at 92% 88%, rgba(0,245,200,.08), transparent 44%)}}
.scan{{position:absolute;inset:-40px;pointer-events:none;
  background:repeating-linear-gradient(0deg, rgba(0,245,200,.045) 0 2px, transparent 2px 11px)}}
.rail{{position:absolute;left:0;right:0;height:10px;background:{volt};transform-origin:0 50%}}
.scene{{position:absolute;inset:0;transform:translateY(90px);
  will-change:opacity,transform}}
.disp{{font-style:italic;font-variation-settings:'wdth' 125,'wght' 900;line-height:.88;
  letter-spacing:-.5px;white-space:pre-line}}
.kick{{font-family:'JetBrains Mono',monospace;font-weight:700;letter-spacing:.3em;color:{volt}}}
.mono{{font-family:'JetBrains Mono',monospace;font-weight:700}}
.ctr{{position:absolute;left:0;right:0;text-align:center}}
/* A .fit line is shrunk to the frame, which only works if it is allowed to be
   ONE line. Left to wrap it never overflows, the fit pass finds nothing to do,
   and the second line lands on whatever sits below it. */
.fit{{white-space:nowrap}}
/* The ladder: a row per court, its win and its loss. Square corners — the
   lockup's only curve is a deliberate one and nothing else has any. */
.crt{{display:flex;align-items:center;gap:20px;padding:20px 26px;
  border:3px solid rgba(242,240,247,.12);background:rgba(255,255,255,.025);
  margin-bottom:16px;will-change:transform,opacity}}
.crt .cn{{flex:1;font-family:'JetBrains Mono',monospace;font-weight:700;font-size:30px;
  letter-spacing:.18em;color:{dim};white-space:nowrap}}
.crt .cw{{font-style:italic;font-variation-settings:'wdth' 112,'wght' 900;
  font-size:62px;width:106px;text-align:right}}
.crt .cl{{font-family:'JetBrains Mono',monospace;font-weight:700;font-size:34px;
  width:78px;text-align:right;color:{dim}}}
/* The column header. Same flex metrics as a court row and no border, so WIN
   and LOSE sit exactly over the numbers they name. */
.hdr{{display:flex;align-items:center;gap:20px;padding:0 26px 14px;
  font-family:'JetBrains Mono',monospace;font-weight:700;font-size:24px;
  letter-spacing:.18em;color:{dim}}}
.hdr .h1{{flex:1}}
.hdr .h2{{width:106px;text-align:right}}
.hdr .h3{{width:78px;text-align:right}}
/* Court 1 is the thing the night is named after, so it is the only lit row. */
.crt.top{{border-color:{volt};background:rgba(0,245,200,.10)}}
.crt.top .cn{{color:{volt}}}
.crt.top .cw{{color:{volt}}}
.flash{{position:absolute;inset:0;pointer-events:none;background:{volt};
  mix-blend-mode:screen;opacity:0}}
</style></head><body>

<div id="cam">
  <div class="wash"></div><div class="scan" id="scan"></div>
  <div class="rail" id="rail" style="top:0"></div>

  <!-- 1 · the night -->
  <div class="scene" id="s1">
    <div class="kick ctr" style="top:534px;font-size:30px" id="s1k">{urgent}</div>
    <div class="disp ctr fit" style="top:600px;font-size:220px;color:{volt}" id="s1t">{name}</div>
    <div style="position:absolute;left:50%;top:852px;width:440px;height:5px;margin-left:-220px;background:{volt}" id="s1r"></div>
    <div class="disp ctr fit" style="top:912px;font-size:76px" id="s1g">{tagline}</div>
    <div class="mono ctr" style="top:1046px;font-size:30px;letter-spacing:.2em;color:{dim}" id="s1s">{promise}</div>
  </div>

  <!-- 2 · the shape of the night -->
  <div class="scene" id="s2">
    <div class="kick ctr" style="top:438px;font-size:24px" id="s2k">THE NIGHT</div>
    <div class="disp ctr" style="top:494px;font-size:100px" id="s2t">{courtword} COURTS.
ONE LADDER.</div>
    <div style="position:absolute;left:140px;right:140px;top:790px;height:3px;background:rgba(242,240,247,.14)" id="s2r"></div>
    <div class="ctr" style="top:842px;font-size:42px" id="s2a">
      <b style="color:{volt}">{cap} players</b> — and nobody sits out.</div>
    <div class="ctr" style="top:928px;font-size:42px;color:{dim}" id="s2b">Come alone. You are never short of a partner.</div>
  </div>

  <!-- 3 · the shuffle -->
  <div class="scene" id="s3">
    <div class="kick ctr" style="top:470px;font-size:24px" id="s3k">ROUND ONE</div>
    <div class="disp ctr" style="top:526px;font-size:128px" id="s3t">THE
SHUFFLE.</div>
    <div class="ctr" style="top:830px;font-size:42px" id="s3a">
      Your <b style="color:{volt}">winning margin</b> sets the ladder.</div>
    <div class="ctr" style="top:916px;font-size:38px;color:{dim}" id="s3b">Biggest win opens on Court 1. Nothing else decides it.</div>
  </div>

  <!-- 4 · climbing, and what a court is worth -->
  <div class="scene" id="s4">
    <div class="kick ctr" style="top:300px;font-size:24px" id="s4k">WIN AND YOU GO UP</div>
    <div class="disp ctr" style="top:356px;font-size:106px" id="s4t">THE HIGHER
THE COURT.</div>
    <div id="s4g" style="position:absolute;left:150px;right:150px;top:600px">
      <div class="hdr" id="s4s"><span class="h1"></span><span class="h2">WIN</span><span class="h3">LOSE</span></div>
      {ladder}</div>
    <div class="ctr" style="top:1186px;font-size:38px;color:{dim}" id="s4n">A win on Court 1 is worth {topwin}. On the bottom, {botwin}.</div>
  </div>

  <!-- 5 · the decider -->
  <div class="scene" id="s5">
    <div class="kick ctr" style="top:470px;font-size:26px" id="s5k">THE LAST ROUND</div>
    <div class="ctr" id="s5b" style="top:532px">
      <span class="disp" style="font-size:300px;color:{volt}" id="s5x">2X</span>
    </div>
    <div class="disp ctr" style="top:876px;font-size:108px" id="s5t">EVERYTHING
DOUBLES.</div>
    <div class="ctr" style="top:1114px;font-size:40px;color:{dim}" id="s5s">Nobody is out of it until it is over.</div>
  </div>

  <!-- 6 · the clock -->
  <div class="scene" id="s6">
    <div class="kick ctr" style="top:470px;font-size:24px" id="s6k">THE CLOCK</div>
    <div class="ctr" id="s6b" style="top:520px">
      <span class="disp" style="font-size:268px;color:{volt}" id="s6v">0</span>
    </div>
    <div class="disp ctr" style="top:810px;font-size:96px" id="s6t">ROUNDS.</div>
    <div style="position:absolute;left:150px;right:150px;top:968px;height:3px;background:rgba(242,240,247,.14)" id="s6r"></div>
    <div class="ctr" style="top:1018px;font-size:42px" id="s6n">
      <b style="color:{volt}">{matches} matches each</b>, first to {target}.</div>
    <div class="mono ctr" style="top:1108px;font-size:28px;letter-spacing:.2em;color:{dim}" id="s6s">ABOUT {runtime} OF PLAY</div>
  </div>

  <!-- 7 · the prize -->
  <div class="scene" id="s7">
    <div class="kick ctr" style="top:450px;font-size:24px" id="s7k">THE CHAMPION TAKES</div>
    <div class="disp ctr fit" style="top:506px;font-size:198px;color:{volt}" id="s7t">{prize} {cur}</div>
    <div class="mono ctr" style="top:748px;font-size:32px;letter-spacing:.24em;color:{dim}" id="s7s">{kind}</div>
    <div style="position:absolute;left:150px;right:150px;top:862px;height:3px;background:rgba(242,240,247,.14)" id="s7r"></div>
    <div class="ctr" style="top:914px;font-size:44px" id="s7a">
      <b style="color:{volt}">{entry} {cur}</b> to play</div>
    <div class="ctr" style="top:1004px;font-size:40px;color:{dim}" id="s7b">{cap} places, and they go.</div>
  </div>

  <!-- 8 · when and where -->
  <div class="scene" id="s8">
    <div class="disp ctr fit" style="top:470px;font-size:150px" id="s8t">{urgent}</div>
    <div style="position:absolute;left:50%;top:688px;width:520px;height:5px;margin-left:-260px;background:{volt}" id="s8r"></div>
    <div class="mono ctr fit" style="top:748px;font-size:40px;letter-spacing:.14em;color:{volt}" id="s8d">{datestamp} &middot; {start}</div>
    <div class="mono ctr" style="top:826px;font-size:26px;letter-spacing:.22em;color:{dim}" id="s8f">DOORS {doors}</div>
    <div class="disp ctr fit" style="top:922px;font-size:58px;color:{volt}" id="s8u">{host}</div>
    <div class="mono ctr" style="top:1026px;font-size:28px;letter-spacing:.22em;color:{dim}" id="s8e">{cadence}</div>
    <div class="mono ctr" style="top:1360px;font-size:24px;letter-spacing:.3em;color:#4A4855">URBAN PLAYGROUND &middot; MUSCAT</div>
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
// A scene that is not in this cut is removed from the page outright, not
// merely skipped: left in the DOM it would still be measured by the
// recorder's overflow and overlap checks, and could be seen in a scrub.
// AT maps a scene's NUMBER to when it starts, so the per-scene blocks below
// do not care which cut is being built or what order the scenes come in.
const AT=Object.fromEntries(D.order.map((n,i)=>[n, D.scenes[i]]));
[...document.querySelectorAll('.scene')].forEach(el=>{{
  if(AT[Number(el.id.slice(1))]===undefined) el.remove();
}});

function set(el,o,tr,fl){{
  if(!el) return;
  el.style.opacity=o.toFixed(3);
  if(tr!==undefined) el.style.transform=tr;
  if(fl!==undefined) el.style.filter=fl;
}}
// Type arrives condensed and opens to full width. Needs a VARIABLE font — a
// static instance accepts 'wdth' and nothing moves, which is why the recorder
// measures it rather than trusting it.
function widen(el,t,t0,d,{{w0=66,w1=125,blur=12}}={{}}){{
  if(!el) return;
  const p=outExpo(inv(t,t0,t0+d)), o=inv(t,t0,t0+d*0.3);
  el.style.fontVariationSettings=`'wdth' ${{(w0+(w1-w0)*p).toFixed(1)}},'wght' 900`;
  set(el,o,`scale(${{(1+0.04*(1-p)).toFixed(4)}})`,`blur(${{(blur*(1-p)).toFixed(2)}}px)`);
}}
function rise(el,t,t0,d,px){{
  if(!el) return;
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

const S=D.scenes, END=[...S.slice(1), DUR];
// The outro's start, so the recorder can probe the widening entrance without
// a time typed into it that goes stale the moment a scene table changes.
window.__outro=AT[8];

function seek(t){{
  fitOnce();
  const [e,h]=energy(t);
  const sx=e>0.001?Math.sin(t*118)*6*e:0, sy=e>0.001?Math.cos(t*97)*4.5*e:0;
  document.getElementById('cam').style.transform=
    `translate(${{sx.toFixed(2)}}px,${{sy.toFixed(2)}}px) scale(${{(1+e*0.010).toFixed(4)}})`;
  document.getElementById('flash').style.opacity=(e*0.05+h*0.12).toFixed(3);
  const sc=document.getElementById('scan');
  sc.style.transform=`translateY(${{(t*3.2)%11}}px)`;
  sc.style.opacity=(0.9+e*1.4).toFixed(3);
  document.getElementById('rail').style.transform=
    `scaleX(${{outExpo(inv(t,0.02,0.60)).toFixed(3)}})`;

  for(let i=0;i<S.length;i++){{
    const el=document.getElementById('s'+D.order[i]);
    if(!el) continue;
    const o=Math.min(inv(t,S[i]-XF,S[i]+0.02), 1-inv(t,END[i],END[i]+XF));
    el.style.opacity=o.toFixed(3);
    el.style.display=o<=0.002?'none':'block';
  }}
  const g=(i)=>document.getElementById(i);

  {{ // 1 · the night
    const u=t-AT[1];
    rise(g('s1k'), u, 0.14, 0.50, 12);
    widen(g('s1t'), u, 0.40, 0.88);
    set(g('s1r'), 1, `scaleX(${{outQuint(inv(u,1.26,1.72)).toFixed(3)}})`);
    widen(g('s1g'), u, 1.46, 0.66, {{w0:84,blur:7}});
    set(g('s1s'), inv(u,2.04,2.36));
  }}

  {{ // 2 · the shape of the night
    const u=t-AT[2];
    rise(g('s2k'), u, 0.08, 0.40, 10);
    widen(g('s2t'), u, 0.18, 0.70, {{w0:72,blur:9}});
    set(g('s2r'), 1, `scaleX(${{outQuint(inv(u,1.06,1.48)).toFixed(3)}})`);
    rise(g('s2a'), u, 1.28, 0.48, 14);
    rise(g('s2b'), u, 1.62, 0.48, 14);
  }}

  {{ // 3 · the shuffle
    const u=t-AT[3];
    rise(g('s3k'), u, 0.08, 0.40, 10);
    widen(g('s3t'), u, 0.18, 0.72, {{w0:70,blur:10}});
    rise(g('s3a'), u, 1.14, 0.48, 14);
    rise(g('s3b'), u, 1.48, 0.48, 14);
  }}

  {{ // 4 · the ladder. The courts land from the BOTTOM up, which is the
     //     direction the night is about.
    const u=t-AT[4];
    rise(g('s4k'), u, 0.08, 0.40, 10);
    widen(g('s4t'), u, 0.18, 0.68, {{w0:72,blur:9}});
    for(let i=0;i<D.courts;i++){{
      const a=0.74+(D.courts-1-i)*0.20, q=outBack(inv(u,a,a+0.46));
      set(g('k'+i), inv(u,a,a+0.18), `translateX(${{(-30*(1-q)).toFixed(1)}}px)`);
    }}
    set(g('s4s'), inv(u,0.66,0.92));
    rise(g('s4n'), u, 1.10+D.courts*0.20, 0.48, 14);
  }}

  {{ // 5 · the decider. The 2X slams in rather than widening: it is a stamp.
    const u=t-AT[5];
    rise(g('s5k'), u, 0.06, 0.34, 10);
    const q=outBack(inv(u,0.14,0.70));
    set(g('s5b'), inv(u,0.14,0.30),
        `scale(${{(1.34-0.34*q).toFixed(4)}})`, `blur(${{(14*(1-outExpo(inv(u,0.14,0.60)))).toFixed(2)}}px)`);
    widen(g('s5t'), u, 0.88, 0.68, {{w0:72,blur:9}});
    rise(g('s5s'), u, 1.58, 0.48, 14);
  }}

  {{ // 6 · the clock
    const u=t-AT[6];
    rise(g('s6k'), u, 0.06, 0.36, 10);
    const p=outExpo(inv(u,0.18,1.06));
    set(g('s6b'), inv(u,0.18,0.38), `scale(${{(0.94+0.06*p).toFixed(4)}})`);
    const n6=g('s6v'); if(n6) n6.textContent=Math.round(D.rounds*p);
    widen(g('s6t'), u, 0.94, 0.60, {{w0:78,blur:8}});
    set(g('s6r'), 1, `scaleX(${{outQuint(inv(u,1.28,1.68)).toFixed(3)}})`);
    rise(g('s6n'), u, 1.50, 0.48, 14);
    set(g('s6s'), inv(u,1.92,2.20));
  }}

  {{ // 7 · the prize
    const u=t-AT[7];
    rise(g('s7k'), u, 0.06, 0.36, 10);
    widen(g('s7t'), u, 0.16, 0.70, {{w0:68,blur:11}});
    set(g('s7s'), inv(u,0.84,1.10));
    set(g('s7r'), 1, `scaleX(${{outQuint(inv(u,1.04,1.44)).toFixed(3)}})`);
    rise(g('s7a'), u, 1.30, 0.48, 14);
    rise(g('s7b'), u, 1.64, 0.48, 14);
  }}

  {{ // 8 · when and where
    const u=t-AT[8];
    widen(g('s8t'), u, 0.16, 0.78);
    set(g('s8r'), 1, `scaleX(${{outQuint(inv(u,0.76,1.20)).toFixed(3)}})`);
    set(g('s8d'), inv(u,1.00,1.28));
    set(g('s8f'), inv(u,1.22,1.48));
    widen(g('s8u'), u, 1.44, 0.60, {{w0:80,blur:6}});
    set(g('s8e'), inv(u,1.90,2.16));
  }}
}}
window.__seek=seek; window.__dur=DUR; seek(0);
</script></body></html>"""


if __name__ == "__main__":
    main()
