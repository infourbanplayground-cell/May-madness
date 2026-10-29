# -*- coding: utf-8 -*-
"""Blackout Vol.8 — the 15-second INSTAGRAM STORY cut for the final night.

Longer than the 7-second slam, and doing a different job. That one is a
reminder: one fact, one date. This is the sell, and it ends on two asks —

  0.00  TOMORROW — the last night
  2.40  where the season stands
  5.40  the fact: the gap at the top
  7.60  the last night is a double
  9.80  PLAY   — the cap, the entry, how to get a name in
 12.20  WATCH  — the time, the place, the address

Fifteen seconds because that is one story card. Longer and Instagram splits it,
and a cut split across two cards loses the half nobody taps through to.

EVERY FIGURE IS DERIVED. Points and gaps come from `ops/blackout-standings.mjs`
(the app's own engine over the live state), entry and voucher from
`blackout-season.json`, the team cap from `ops/signup-post.py`, and the start
time is parsed out of the season file's own schedule line rather than typed —
the night-9 signup sheet already went out carrying it, and two assets quoting
different times is the fault worth engineering against.

It does NOT say "every point counts twice", which the WhatsApp sheet does: 2X
applies to everything except the streak bonus, so the sentence is very nearly
true and still wrong. DOUBLE POINTS on its own is exactly true.

  ssh urbanpadel 'curl -s localhost:3009/state' > $SP/bo.json
  node ops/blackout-standings.mjs $SP/bo.json $SP/bo-standings.json
  python3 build-story-video.py && python3.13 build-story-audio.py
  node record-story-video.mjs
"""
import base64, datetime, json, os, re, sys
from importlib.machinery import SourceFileLoader

HERE = os.path.dirname(os.path.abspath(__file__))
SP = "/tmp/claude-0/-home-user-May-madness/0e44f0ad-a683-5f0d-9de6-9459ae328963/scratchpad"
FONTS = os.path.join(HERE, "brand", "fonts")
DATA = os.path.join(SP, "bo-standings.json")
SEASON = os.path.join(HERE, "blackout-season.json")
OUT = os.path.join(SP, "story.html")

W, H = 1080, 1920
DUR = 15.00
SCENES = [0.00, 2.40, 5.40, 7.60, 9.80, 12.20]
BEATS = [0.00, 1.20, 2.40, 3.60, 4.50, 5.40, 6.50, 7.60,
         8.70, 9.80, 11.00, 12.20, 13.40, 14.30]
HERO = [0.00, 5.40, 7.60, 9.80, 12.20]

LIME = "#C6FF00"
MAGENTA = "#FF2E88"
INK = "#F2F2F2"
MUTED = "#9A9A9A"
DIM = "#6E6E6E"

DAYS = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]
MONS = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN",
        "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]


def faces():
    css = open(os.path.join(FONTS, "fonts.css")).read()
    seen = {}

    def sub(m):
        n = m.group(1)
        if n not in seen:
            with open(os.path.join(FONTS, n), "rb") as f:
                seen[n] = base64.b64encode(f.read()).decode()
        return "url(data:font/woff2;base64,%s) format('woff2')" % seen[n]

    css = re.sub(r"url\(\./([A-Za-z0-9._-]+\.woff2)\)\s*format\('woff2'\)", sub, css)
    assert ".woff2)" not in css, "a font file was left as an external reference"
    return css


MARK = base64.b64encode(
    open(os.path.join(HERE, "brand", "blackout", "blackout-mark.svg")).read().encode()).decode()


def page(d):
    rows = "\n".join(
        f'<div class="r" id="r{i}" style="top:{i * 136}px">'
        f'<span class="rp" style="color:{LIME if i == 0 else MUTED}">{i + 1}</span>'
        f'<span class="rn fitcell">{r["name"].upper()}</span>'
        f'<span class="rv" id="v{i}" data-to="{r["pts"]}"'
        f' style="color:{LIME if i == 0 else INK}">0</span>'
        f'</div>'
        for i, r in enumerate(d["table"][:4]))

    cfg = json.dumps(dict(scenes=SCENES, beats=BEATS, hero=HERO, dur=DUR))

    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
{faces()}
*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{width:{W}px;height:{H}px;background:#050505;overflow:hidden;
  font-family:'Archivo',sans-serif;color:{INK};-webkit-font-smoothing:antialiased}}
#bg{{position:absolute;inset:0;z-index:1}}
.vig{{position:absolute;inset:0;z-index:3;pointer-events:none;
  background:radial-gradient(ellipse 74% 56% at 50% 46%, transparent 40%, rgba(5,5,5,.88) 100%)}}
/* The sweep is a bright band travelling down the frame, locked to the bar.
   It sits under the type so it lights the picture, not the words. */
#sweep{{position:absolute;left:0;right:0;height:300px;z-index:4;pointer-events:none;
  background:linear-gradient(180deg,transparent,rgba(198,255,0,.16),transparent)}}
.scene{{position:absolute;inset:0;z-index:6;will-change:opacity}}
/* Letterbox bars snap in on a cut and relax. They are the cheapest way to make
   a still frame feel cut rather than faded. */
.lb{{position:absolute;left:0;right:0;background:#050505;z-index:8;pointer-events:none}}
#lbt{{top:0}} #lbb{{bottom:0}}
#flash{{position:absolute;inset:0;z-index:7;pointer-events:none;background:{LIME};opacity:0}}
.d{{font-style:italic;font-variation-settings:'wdth' 125,'wght' 900;line-height:.86;
   letter-spacing:-.5px}}
.k{{font-family:'JetBrains Mono',monospace;font-weight:700;text-transform:uppercase;
   letter-spacing:.3em}}
.ctr{{position:absolute;left:0;right:0;text-align:center}}

.r{{position:absolute;left:84px;right:84px;display:flex;align-items:center;gap:26px;
   height:124px;border-bottom:3px solid rgba(242,242,242,.10)}}
.r .rp{{font-family:'JetBrains Mono',monospace;font-weight:700;font-size:34px;
   width:50px;flex:0 0 50px}}
.r .rn{{flex:1;min-width:0;font-style:italic;
   font-variation-settings:'wdth' 100,'wght' 900;font-size:58px;white-space:nowrap}}
.r .rv{{font-style:italic;font-variation-settings:'wdth' 112,'wght' 900;
   font-size:78px;line-height:1;flex:0 0 auto;font-variant-numeric:tabular-nums}}

.pill{{position:absolute;display:flex;align-items:center;justify-content:center;
   border:5px solid {MAGENTA};background:rgba(255,46,136,.10)}}
.stat{{position:absolute;left:0;right:0;display:flex}}
.stat>div{{flex:1;text-align:center}}
.stat .sv{{font-style:italic;font-variation-settings:'wdth' 118,'wght' 900;font-size:104px;
   line-height:1}}
.stat .sl{{font-family:'JetBrains Mono',monospace;font-weight:700;font-size:22px;
   letter-spacing:.2em;color:{MUTED};margin-top:14px}}
</style></head><body>
<canvas id="bg" width="{W}" height="{H}"></canvas>
<div class="vig"></div>
<div id="sweep"></div>

<div class="scene" id="s1">
  <div style="position:absolute;left:50%;top:560px;width:120px;height:120px;margin-left:-60px">
    <img id="s1m" src="data:image/svg+xml;base64,{MARK}" style="width:100%;display:block">
  </div>
  <div class="k ctr" id="s1k" style="top:736px;font-size:28px;color:{LIME}">BLACKOUT &middot; VOL.8</div>
  <div class="d ctr fit" id="s1h" style="top:800px;font-size:230px">TOMORROW</div>
  <div class="k ctr" id="s1s" style="top:1082px;font-size:30px;color:{INK}">THE LAST NIGHT OF THE SEASON</div>
</div>

<div class="scene" id="s2">
  <div class="k ctr" id="s2k" style="top:596px;font-size:26px;color:{MUTED}">
    AFTER {d['played']} OF {d['sessionsTotal']} NIGHTS</div>
  <div id="s2rows" style="position:absolute;left:0;right:0;top:692px">{rows}</div>
</div>

<div class="scene" id="s3">
  <div class="d ctr fit" id="s3n" style="top:666px;font-size:330px;color:{MAGENTA}">{d['hook']}</div>
  <div class="k ctr" id="s3s" style="top:1078px;font-size:30px;color:{INK}">{d['hookSub']}</div>
</div>

<div class="scene" id="s4">
  <div class="pill" id="s4p" style="left:84px;right:84px;top:756px;height:300px">
    <div class="d" id="s4h" style="font-size:132px;color:{MAGENTA};text-align:center">DOUBLE<br>POINTS</div>
  </div>
  <div class="k ctr" id="s4s" style="top:1110px;font-size:28px;color:{INK}">NIGHT {d['sessionsTotal']} OF {d['sessionsTotal']}</div>
</div>

<div class="scene" id="s5">
  <div class="k ctr" id="s5k" style="top:584px;font-size:28px;color:{LIME}">GET IN IT</div>
  <div class="d ctr fit" id="s5h" style="top:646px;font-size:250px">PLAY</div>
  <div class="stat" id="s5st" style="top:944px">
    <div><div class="sv" style="color:{LIME}">{d['maxTeams']}</div><div class="sl">TEAMS ONLY</div></div>
    <div><div class="sv">{d['entry']}</div><div class="sl">OMR A NIGHT</div></div>
    <div><div class="sv" style="color:{LIME}">{d['voucher']}</div><div class="sl">OMR EACH WINNER</div></div>
  </div>
  <div class="k ctr" id="s5s" style="top:1180px;font-size:27px;color:{INK}">DROP YOUR NAME IN THE GROUP</div>
</div>

<div class="scene" id="s6">
  <div class="k ctr" id="s6k" style="top:556px;font-size:28px;color:{LIME}">OR JUST TURN UP</div>
  <div class="d ctr fit" id="s6h" style="top:618px;font-size:210px">COME WATCH</div>
  <div class="d ctr fit" id="s6d" style="top:884px;font-size:112px;color:{MAGENTA}">{d['when']} &middot; {d['time']}</div>
  <div class="k ctr" id="s6v" style="top:1040px;font-size:30px;color:{INK}">{d['venue'].upper()}</div>
  <div class="k ctr fit" id="s6u" style="top:1124px;font-size:30px;color:{LIME}">{d['host'].upper()}</div>
</div>

<div class="lb" id="lbt"></div>
<div class="lb" id="lbb"></div>
<div id="flash"></div>

<script>
const D={cfg};
const W={W}, H={H};
const g=document.getElementById('bg').getContext('2d');
const clamp=(x,a=0,b=1)=>Math.min(b,Math.max(a,x));
const inv=(t,a,b)=>clamp((t-a)/(b-a));
const outQuint=x=>1-Math.pow(1-x,5);
const outExpo =x=>x>=1?1:1-Math.pow(2,-10*x);
const outBack =x=>{{const c1=1.9,c3=c1+1;return 1+c3*Math.pow(x-1,3)+c1*Math.pow(x-1,2);}};
const HERO=new Set(D.hero);

function set(el,o,tr,fl){{
  if(!el) return;
  el.style.opacity=o.toFixed(3);
  if(tr!==undefined) el.style.transform=tr;
  if(fl!==undefined) el.style.filter=fl;
}}
// Chromatic split, done with text-shadow rather than three stacked copies of
// the element: duplicates would be three more leaf text nodes sitting exactly
// on top of each other, which is precisely what the recorder's overlap check
// exists to catch.
function split(el,amt){{
  if(!el) return;
  if(amt<0.4){{ el.style.textShadow='none'; return; }}
  const a=amt.toFixed(1);
  el.style.textShadow=`-${{a}}px 0 rgba(255,46,136,.85), ${{a}}px 0 rgba(0,229,255,.70)`;
}}
function widen(el,t,t0,d,w0=66,w1=125,blur=16){{
  if(!el) return;
  const p=outExpo(inv(t,t0,t0+d)), o=inv(t,t0,t0+d*0.26);
  el.style.fontVariationSettings=`'wdth' ${{(w0+(w1-w0)*p).toFixed(1)}},'wght' 900`;
  set(el,o,`scale(${{(1+0.06*(1-p)).toFixed(4)}})`,`blur(${{(blur*(1-p)).toFixed(2)}}px)`);
  split(el,18*(1-p));
}}
function rise(el,t,t0,d,px){{
  if(!el) return;
  set(el, inv(t,t0,t0+d*0.5),
      `translateY(${{(px*(1-outQuint(inv(t,t0,t0+d)))).toFixed(1)}}px)`);
}}
// A row arrives as a wipe plus a slide. The wipe is what makes it read as a
// board filling in rather than a list fading up.
function wipe(el,t,t0,d){{
  if(!el) return;
  const p=outQuint(inv(t,t0,t0+d));
  el.style.clipPath=`inset(0 ${{(100*(1-p)).toFixed(1)}}% 0 0)`;
  set(el, inv(t,t0,t0+d*0.3), `translateX(${{(-38*(1-p)).toFixed(1)}}px)`);
}}
function pop(el,t,t0,d){{
  if(!el) return;
  const p=outBack(inv(t,t0,t0+d));
  set(el, inv(t,t0,t0+d*0.3), `scale(${{(0.86+0.14*p).toFixed(4)}})`);
}}

let fitted=false;
function fitOnce(){{
  if(fitted || !document.fonts.check("italic 900 40px Archivo")) return;
  const hidden=[...document.querySelectorAll('.scene')].map(s=>[s,s.style.display]);
  hidden.forEach(([s])=>{{s.style.display='block';}});
  const MAX=W-110;
  for(const el of document.querySelectorAll('.fit')){{
    if(!el.firstElementChild || !el.firstElementChild.classList.contains('fitspan'))
      el.innerHTML=`<span class="fitspan" style="display:inline-block;white-space:nowrap">${{el.textContent.trim()}}</span>`;
    const base=parseFloat(getComputedStyle(el).fontSize);
    const keep=el.style.fontVariationSettings;
    el.style.fontVariationSettings="'wdth' 125,'wght' 900";
    const w=el.firstElementChild.getBoundingClientRect().width;
    el.style.fontVariationSettings=keep;
    if(w>MAX) el.style.fontSize=(base*MAX/w).toFixed(2)+'px';
  }}
  // A flex:1 cell is the leftover space at any font size, so the frame-width
  // pass above cannot bound it — it has to be measured against its own box.
  for(const el of document.querySelectorAll('.fitcell')){{
    if(!el.firstElementChild || !el.firstElementChild.classList.contains('fitspan'))
      el.innerHTML=`<span class="fitspan" style="display:inline-block;white-space:nowrap">${{el.textContent.trim()}}</span>`;
    const box=el.clientWidth-6;
    let fs=parseFloat(getComputedStyle(el).fontSize), guard=0;
    while(el.firstElementChild.getBoundingClientRect().width>box && fs>10 && guard++<400){{
      fs-=1; el.style.fontSize=fs+'px';
    }}
  }}
  hidden.forEach(([s,d])=>{{s.style.display=d;}});
  fitted=true; document.body.dataset.fitted='1';
}}

function energy(t){{
  let e=0,h=0;
  for(const b of D.beats){{
    if(t<b-0.02||t>b+0.44) continue;
    const u=(t-b)/0.44, v=clamp(Math.pow(1-u,3));
    e=Math.max(e,v); if(HERO.has(b)) h=Math.max(h,v);
  }}
  return [e,h];
}}

// Seeded off the frame index, never Math.random(): a backdrop that re-rolls
// per call cannot be scrubbed twice to the same picture, and every frame is
// scrubbed more than once by the checks that run before capture.
function backdrop(t,e,h){{
  g.fillStyle='#050505'; g.fillRect(0,0,W,H);
  const vy=H*0.46, drift=(t*104)%120;
  g.lineWidth=2;
  g.strokeStyle=`rgba(198,255,0,${{(0.06+0.17*e).toFixed(3)}})`;
  for(let i=-14;i<=14;i++){{
    const x=W/2+i*118;
    g.beginPath(); g.moveTo(W/2+(x-W/2)*0.12,vy); g.lineTo(x*2.3-W*0.65,H+40); g.stroke();
  }}
  for(let i=0;i<13;i++){{
    const y=vy+Math.pow(i+(drift/120),2.05)*10.5;
    if(y>H+40) break;
    g.strokeStyle=`rgba(198,255,0,${{(0.05+0.14*e).toFixed(3)}})`;
    g.beginPath(); g.moveTo(0,y); g.lineTo(W,y); g.stroke();
  }}
  // Speed lines out of the vanishing point on a hit.
  if(e>0.02){{
    const seed=Math.floor(t*30);
    g.lineWidth=3;
    for(let i=0;i<26;i++){{
      const a=((i*137.5+seed*11)%360)*Math.PI/180;
      const r0=160+((i*53)%220), r1=r0+e*(300+((i*97)%260));
      g.strokeStyle=`rgba(198,255,0,${{(e*0.30).toFixed(3)}})`;
      g.beginPath();
      g.moveTo(W/2+Math.cos(a)*r0, vy+Math.sin(a)*r0);
      g.lineTo(W/2+Math.cos(a)*r1, vy+Math.sin(a)*r1);
      g.stroke();
    }}
  }}
  if(h>0.01){{
    const seed=Math.floor(t*4);
    for(let i=0;i<3;i++){{
      const r=Math.max(1,(1-h)*(600+i*200)+90);
      g.strokeStyle=`rgba(255,46,136,${{(h*(0.32-i*0.09)).toFixed(3)}})`;
      g.lineWidth=6-i;
      g.beginPath(); g.arc(W/2,vy+((seed*37)%9)-4,r,0,Math.PI*2); g.stroke();
    }}
  }}
  const grd=g.createRadialGradient(W/2,vy,0,W/2,vy,W*0.95);
  grd.addColorStop(0,`rgba(198,255,0,${{(0.05+0.12*e).toFixed(3)}})`);
  grd.addColorStop(1,'rgba(198,255,0,0)');
  g.fillStyle=grd; g.fillRect(0,0,W,H);
}}

const S=D.scenes, END=[...S.slice(1), D.dur];
function sceneAt(t){{ let i=0; for(let k=0;k<S.length;k++) if(t>=S[k]-0.001) i=k; return i; }}

function seek(t){{
  t=clamp(t,0,D.dur);
  fitOnce();
  const [e,h]=energy(t);
  backdrop(t,e,h);

  const i=sceneAt(t), t0=S[i];

  // Flash frame on the hero cuts — two frames at a third, under the bars.
  // Above them and at half opacity it washed the whole frame and read as a
  // strobe rather than as a cut.
  const fl=document.getElementById('flash');
  fl.style.opacity=(HERO.has(t0)?0.34*clamp(1-(t-t0)/0.07):0).toFixed(3);
  fl.style.background=(i>=4?'{LIME}':'{MAGENTA}');

  // Letterbox: punches to 120px on the cut, relaxes to 34px over 0.5s.
  const lb=34+86*(1-outQuint(inv(t,t0,t0+0.5)));
  document.getElementById('lbt').style.height=lb.toFixed(1)+'px';
  document.getElementById('lbb').style.height=lb.toFixed(1)+'px';

  // The sweep runs the length of the scene it is in.
  const sw=document.getElementById('sweep');
  const p=inv(t,t0,END[i]);
  sw.style.top=(-300+p*(H+300)).toFixed(0)+'px';
  sw.style.opacity=(0.30+0.5*e).toFixed(3);

  for(let k=0;k<S.length;k++){{
    const el=document.getElementById('s'+(k+1));
    el.style.display=(t>=S[k]-0.001 && t<END[k]+0.001)?'block':'none';
  }}

  // 1 — tomorrow
  pop(document.getElementById('s1m'),t,S[0]+0.00,0.42);
  rise(document.getElementById('s1k'),t,S[0]+0.10,0.34,-16);
  widen(document.getElementById('s1h'),t,S[0]+0.16,0.60);
  rise(document.getElementById('s1s'),t,S[0]+0.52,0.40,20);

  // 2 — the table, a row every sixth of a second, numbers counting up
  rise(document.getElementById('s2k'),t,S[1]+0.00,0.28,-12);
  for(let k=0;k<4;k++){{
    wipe(document.getElementById('r'+k),t,S[1]+0.10+k*0.17,0.40);
    const v=document.getElementById('v'+k);
    if(v){{
      const to=+v.dataset.to;
      const q=outQuint(inv(t,S[1]+0.16+k*0.17,S[1]+0.16+k*0.17+0.70));
      v.textContent=Math.round(to*q);
    }}
  }}

  // 3 — the fact
  widen(document.getElementById('s3n'),t,S[2]+0.02,0.52,54,125,20);
  rise(document.getElementById('s3s'),t,S[2]+0.34,0.36,22);

  // 4 — the double
  pop(document.getElementById('s4p'),t,S[3]+0.00,0.44);
  widen(document.getElementById('s4h'),t,S[3]+0.10,0.46,78,125,10);
  rise(document.getElementById('s4s'),t,S[3]+0.40,0.36,18);

  // 5 — play
  rise(document.getElementById('s5k'),t,S[4]+0.00,0.30,-14);
  widen(document.getElementById('s5h'),t,S[4]+0.10,0.52);
  rise(document.getElementById('s5st'),t,S[4]+0.42,0.42,26);
  rise(document.getElementById('s5s'),t,S[4]+0.74,0.40,20);

  // 6 — watch
  rise(document.getElementById('s6k'),t,S[5]+0.00,0.30,-14);
  widen(document.getElementById('s6h'),t,S[5]+0.10,0.54);
  widen(document.getElementById('s6d'),t,S[5]+0.52,0.46,84,125,8);
  rise(document.getElementById('s6v'),t,S[5]+0.86,0.38,18);
  rise(document.getElementById('s6u'),t,S[5]+1.10,0.42,16);
}}
window.__seek=seek; window.__dur=D.dur; window.__outro=S[5];
document.fonts.ready.then(()=>{{fitted=false;fitOnce();seek(0);}});
seek(0);
</script></body></html>"""


def main():
    if not os.path.exists(DATA):
        sys.exit(f"missing {DATA}\n"
                 f"  ssh urbanpadel 'curl -s localhost:3009/state' > {SP}/bo.json\n"
                 f"  node ops/blackout-standings.mjs {SP}/bo.json {DATA}")
    d = json.load(open(DATA))
    cfg = json.load(open(SEASON))

    if len(d["remaining"]) != 1:
        sys.exit(f"refusing: {len(d['remaining'])} nights remain, and this cut "
                 f"says TOMORROW and THE LAST NIGHT")
    last = d["remaining"][0]
    if last not in d["doubleNights"]:
        sys.exit("refusing: the cut carries a DOUBLE POINTS card and the season "
                 "file does not have the last night as a double")

    x = datetime.date.fromisoformat(last)
    today = datetime.date.today()
    if (x - today).days != 1:
        sys.exit(f"refusing: the cut opens on TOMORROW and the last night is "
                 f"{(x - today).days} day(s) away ({last})")

    # The start time is the one the night-9 signup sheet already went out with.
    # Parsed from the season file's own schedule line rather than typed here,
    # so the two cannot drift apart.
    m = re.search(r"(\d{1,2}:\d{2}\s*(?:AM|PM))", cfg.get("schedule", ""), re.I)
    if not m:
        sys.exit("refusing: no start time in blackout-season.json's schedule line, "
                 "and this cut puts one on screen")
    d["time"] = m.group(1).upper().replace(" ", " ")

    # The cap belongs to the signup sheet; importing it is how the video and
    # the sheet stay in agreement about how many teams the venue can run.
    sp = SourceFileLoader("signup_post", os.path.join(HERE, "ops", "signup-post.py")).load_module()
    d["maxTeams"] = sp.MAX_TEAMS

    t = d["table"]
    if len(t) < 4:
        sys.exit("refusing: fewer than four players in the series")
    g23, g12 = t[1]["pts"] - t[2]["pts"], t[0]["pts"] - t[1]["pts"]
    if g23 <= g12:
        hook, sub = str(g23), ("POINT BETWEEN 2ND AND 3RD" if g23 == 1
                               else "POINTS BETWEEN 2ND AND 3RD")
    else:
        hook, sub = str(g12), ("POINT OFF THE LEAD" if g12 == 1
                               else "POINTS OFF THE LEAD")
    d["hook"], d["hookSub"] = hook, sub
    d["when"] = f"{DAYS[x.weekday()]} {x.day} {MONS[x.month - 1]}"
    d["venue"] = "Urban Playground"

    os.makedirs(SP, exist_ok=True)
    with open(OUT, "w") as f:
        f.write(page(d))

    print(f"built {OUT}  {W}x{H}  {DUR}s  ({len(SCENES)} scenes)")
    print(f"  after {d['played']} of {d['sessionsTotal']}  ·  "
          f"{d['when']} {d['time']} at {d['venue']}")
    for i, r in enumerate(t[:4]):
        print(f"   {i+1}. {r['name']:<20} {r['pts']}")
    print(f"  hook: {hook} {sub}")
    print(f"  play: {d['maxTeams']} teams · {d['entry']} OMR · {d['voucher']} OMR a winner")
    print("\nnow:  python3.13 build-story-audio.py && node record-story-video.mjs")


if __name__ == "__main__":
    main()
