# -*- coding: utf-8 -*-
"""Blackout Vol.8 — the 7-SECOND cut for the final round.

Seven seconds is four beats and one idea. This is not a trim of the 18-second
hype cut or the 35-second final-week film: those argue a case (a race chart, a
form read, four photographs). At seven seconds there is no case to make, only a
fact to land and a date to leave behind.

  0.00  FINAL ROUND
  1.25  the top four, as they stand
  2.95  the fact — the gap between 2nd and 3rd
  4.45  the date, and that it is worth double

EVERY FIGURE COMES FROM `ops/blackout-standings.mjs`, which runs the app's own
engine over the live state, so the cut cannot claim a total the leaderboard
contradicts. It never says what a doubled night is worth in points — 2X applies
to everything except the streak bonus, so multiplying it out is close, and close
is how a film ends up contradicting the app.

Deterministic: no CSS animations anywhere, every visual state a pure function of
t behind `window.__seek(t)`. The recorder scrubs each frame to an exact time
rather than grabbing it off a running clock.

  ssh urbanpadel 'curl -s localhost:3009/state' > $SP/bo.json
  node ops/blackout-standings.mjs $SP/bo.json $SP/bo-standings.json
  python3 build-lastround-video.py && python3 build-lastround-audio.py
  node record-lastround-video.mjs
"""
import base64, datetime, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SP = "/tmp/claude-0/-home-user-May-madness/0e44f0ad-a683-5f0d-9de6-9459ae328963/scratchpad"
FONTS = os.path.join(HERE, "brand", "fonts")
DATA = os.path.join(SP, "bo-standings.json")
OUT = os.path.join(SP, "lastround.html")

W, H = 1080, 1920
DUR = 7.00
# Four hits. The cut is built on them and so is the bed, from one table.
SCENES = [0.00, 1.25, 2.95, 4.45]
BEATS = [0.00, 1.25, 2.95, 4.45, 5.60]
HERO = [0.00, 2.95, 4.45]

LIME = "#C6FF00"
MAGENTA = "#FF2E88"
INK = "#F2F2F2"
MUTED = "#9A9A9A"
DIM = "#6E6E6E"

DAYS = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]
MONS = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN",
        "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]


def faces():
    """The vendored faces, inlined. Chromium here does not trust the agent
    proxy's CA, so a link to fonts.googleapis.com fails — and a webfont that
    fails to load is not an error, it is a silent fallback into Times."""
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


def page(d):
    t = d["table"]
    rows = "\n".join(
        f'<div class="r" id="r{i}" style="top:{i * 132}px">'
        f'<span class="rp" style="color:{LIME if i == 0 else MUTED}">{i + 1}</span>'
        f'<span class="rn fitcell">{r["name"].upper()}</span>'
        f'<span class="rv" style="color:{LIME if i == 0 else INK}">{r["pts"]}</span>'
        f'</div>'
        for i, r in enumerate(t[:4]))

    cfg = json.dumps(dict(scenes=SCENES, beats=BEATS, hero=HERO, dur=DUR))

    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
{faces()}
*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{width:{W}px;height:{H}px;background:#050505;overflow:hidden;
  font-family:'Archivo',sans-serif;color:{INK};-webkit-font-smoothing:antialiased}}
#bg{{position:absolute;inset:0;z-index:1}}
.vig{{position:absolute;inset:0;z-index:3;pointer-events:none;
  background:radial-gradient(ellipse 72% 54% at 50% 46%, transparent 42%, rgba(5,5,5,.86) 100%)}}
.scene{{position:absolute;inset:0;z-index:5;will-change:opacity}}
.d{{font-style:italic;font-variation-settings:'wdth' 125,'wght' 900;line-height:.86;
   letter-spacing:-.5px}}
.k{{font-family:'JetBrains Mono',monospace;font-weight:700;text-transform:uppercase;
   letter-spacing:.3em}}
.ctr{{position:absolute;left:0;right:0;text-align:center}}

.r{{position:absolute;left:92px;right:92px;display:flex;align-items:center;gap:26px;
   height:132px;border-bottom:3px solid rgba(242,242,242,.10)}}
.r .rp{{font-family:'JetBrains Mono',monospace;font-weight:700;font-size:34px;
   width:50px;flex:0 0 50px}}
.r .rn{{flex:1;min-width:0;font-style:italic;
   font-variation-settings:'wdth' 100,'wght' 900;font-size:62px;white-space:nowrap}}
.r .rv{{font-style:italic;font-variation-settings:'wdth' 112,'wght' 900;
   font-size:82px;line-height:1;flex:0 0 auto}}
</style></head><body>
<canvas id="bg" width="{W}" height="{H}"></canvas>
<div class="vig"></div>

<div class="scene" id="s1">
  <div class="k ctr" id="s1k" style="top:742px;font-size:28px;color:{LIME}">BLACKOUT &middot; VOL.8</div>
  <div class="d ctr fit" id="s1h" style="top:800px;font-size:188px">FINAL ROUND</div>
  <div class="k ctr" id="s1s" style="top:1052px;font-size:30px;color:{INK}">ONE NIGHT LEFT</div>
</div>

<div class="scene" id="s2">
  <div class="k ctr" id="s2k" style="top:560px;font-size:26px;color:{MUTED}">
    AFTER {d['played']} OF {d['sessionsTotal']}</div>
  <div id="s2rows" style="position:absolute;left:0;right:0;top:664px">{rows}</div>
</div>

<div class="scene" id="s3">
  <div class="d ctr fit" id="s3n" style="top:690px;font-size:300px;color:{MAGENTA}">{d['hook']}</div>
  <div class="k ctr" id="s3s" style="top:1062px;font-size:30px;color:{INK}">{d['hookSub']}</div>
</div>

<div class="scene" id="s4">
  <div class="d ctr fit" id="s4d" style="top:706px;font-size:176px">{d['when']}</div>
  <div class="d ctr fit" id="s4x" style="top:912px;font-size:118px;color:{MAGENTA}">DOUBLE POINTS</div>
  <div class="k ctr fit" id="s4u" style="top:1108px;font-size:34px;color:{LIME}">{d['host'].upper()}</div>
</div>

<script>
const D={cfg};
const W={W}, H={H};
const g=document.getElementById('bg').getContext('2d');
const clamp=(x,a=0,b=1)=>Math.min(b,Math.max(a,x));
const inv=(t,a,b)=>clamp((t-a)/(b-a));
const outQuint=x=>1-Math.pow(1-x,5);
const outExpo =x=>x>=1?1:1-Math.pow(2,-10*x);
const HERO=new Set(D.hero);

function set(el,o,tr,fl){{
  if(!el) return;
  el.style.opacity=o.toFixed(3);
  if(tr!==undefined) el.style.transform=tr;
  if(fl!==undefined) el.style.filter=fl;
}}
// The width axis IS the entrance. On a static font instance this sets 'wdth'
// and nothing moves, which is why the recorder measures it rather than
// trusting it.
function widen(el,t,t0,d,w0=68,w1=125,blur=14){{
  if(!el) return;
  const p=outExpo(inv(t,t0,t0+d)), o=inv(t,t0,t0+d*0.28);
  el.style.fontVariationSettings=`'wdth' ${{(w0+(w1-w0)*p).toFixed(1)}},'wght' 900`;
  set(el,o,`scale(${{(1+0.05*(1-p)).toFixed(4)}})`,`blur(${{(blur*(1-p)).toFixed(2)}}px)`);
}}
function rise(el,t,t0,d,px){{
  if(!el) return;
  set(el, inv(t,t0,t0+d*0.5),
      `translateY(${{(px*(1-outQuint(inv(t,t0,t0+d)))).toFixed(1)}}px)`);
}}

// Shrink-to-fit, run once the display face is really there: measured in the
// fallback the numbers are of the wrong letters entirely, since Archivo at
// 'wdth' 125 is far wider than anything the browser would substitute.
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
    if(t<b-0.02||t>b+0.45) continue;
    const u=(t-b)/0.45, v=clamp(Math.pow(1-u,3));
    e=Math.max(e,v); if(HERO.has(b)) h=Math.max(h,v);
  }}
  return [e,h];
}}

// The backdrop is redrawn every seek and seeded off the frame index, never off
// Math.random(): a backdrop that re-rolls per call cannot be scrubbed twice to
// the same picture, and the recorder scrubs every frame more than once.
function backdrop(t,e,h){{
  g.fillStyle='#050505'; g.fillRect(0,0,W,H);
  const vy=H*0.46, drift=(t*96)%120;
  g.lineWidth=2;
  g.strokeStyle=`rgba(198,255,0,${{(0.07+0.16*e).toFixed(3)}})`;
  for(let i=-14;i<=14;i++){{
    const x=W/2+i*118;
    g.beginPath(); g.moveTo(W/2+(x-W/2)*0.12,vy); g.lineTo(x*2.3-W*0.65,H+40); g.stroke();
  }}
  for(let i=0;i<13;i++){{
    const y=vy+Math.pow(i+ (drift/120),2.05)*10.5;
    if(y>H+40) break;
    g.strokeStyle=`rgba(198,255,0,${{(0.05+0.13*e).toFixed(3)}})`;
    g.beginPath(); g.moveTo(0,y); g.lineTo(W,y); g.stroke();
  }}
  if(h>0.01){{
    const seed=Math.floor(t*4);
    for(let i=0;i<3;i++){{
      const r=Math.max(1,(1-h)*(560+i*190)+90);
      g.strokeStyle=`rgba(255,46,136,${{(h*(0.30-i*0.08)).toFixed(3)}})`;
      g.lineWidth=5-i;
      g.beginPath(); g.arc(W/2,vy+((seed*37)%9)-4,r,0,Math.PI*2); g.stroke();
    }}
  }}
  const grd=g.createRadialGradient(W/2,vy,0,W/2,vy,W*0.95);
  grd.addColorStop(0,`rgba(198,255,0,${{(0.05+0.10*e).toFixed(3)}})`);
  grd.addColorStop(1,'rgba(198,255,0,0)');
  g.fillStyle=grd; g.fillRect(0,0,W,H);
}}

const S=D.scenes, END=[...S.slice(1), D.dur];
function seek(t){{
  t=clamp(t,0,D.dur);
  fitOnce();
  const [e,h]=energy(t);
  backdrop(t,e,h);

  for(let i=0;i<S.length;i++){{
    const el=document.getElementById('s'+(i+1));
    el.style.display=(t>=S[i]-0.001 && t<END[i]+0.001)?'block':'none';
  }}

  // 1 — the slam
  widen(document.getElementById('s1h'),t,S[0]+0.02,0.52);
  rise(document.getElementById('s1k'),t,S[0]+0.00,0.34,-16);
  rise(document.getElementById('s1s'),t,S[0]+0.30,0.36,18);

  // 2 — the table, one row per sixth of a beat
  rise(document.getElementById('s2k'),t,S[1]+0.00,0.26,-12);
  for(let i=0;i<4;i++) rise(document.getElementById('r'+i),t,S[1]+0.06+i*0.17,0.34,26);

  // 3 — the fact
  widen(document.getElementById('s3n'),t,S[2]+0.02,0.46,60,125,18);
  rise(document.getElementById('s3s'),t,S[2]+0.26,0.34,20);

  // 4 — the date
  widen(document.getElementById('s4d'),t,S[3]+0.02,0.48);
  rise(document.getElementById('s4x'),t,S[3]+0.30,0.36,22);
  rise(document.getElementById('s4u'),t,S[3]+0.58,0.40,18);
}}
window.__seek=seek; window.__dur=D.dur; window.__outro=S[3];
document.fonts.ready.then(()=>{{fitted=false;fitOnce();seek(0);}});
seek(0);
</script></body></html>"""


def main():
    if not os.path.exists(DATA):
        sys.exit(f"missing {DATA}\n"
                 f"  ssh urbanpadel 'curl -s localhost:3009/state' > {SP}/bo.json\n"
                 f"  node ops/blackout-standings.mjs {SP}/bo.json {DATA}")
    d = json.load(open(DATA))

    # The cut says FINAL ROUND and ONE NIGHT LEFT in 188px type. If that is not
    # what the season file and the live state agree on, there is no film here.
    if len(d["remaining"]) != 1:
        sys.exit(f"refusing: {len(d['remaining'])} nights remain, and this cut "
                 f"says ONE NIGHT LEFT")
    last = d["remaining"][0]
    if last not in d["doubleNights"]:
        sys.exit("refusing: the cut says DOUBLE POINTS and the season file "
                 "does not have the last night as a double")

    t = d["table"]
    if len(t) < 4:
        sys.exit("refusing: fewer than four players in the series")

    # The hook is whichever gap near the top is the sharpest — it is read off
    # the table rather than written here, because the point of a seven-second
    # cut is the one fact, and which one that is changes every night. Second to
    # third is the one with a prize boundary on it; the lead is the headline
    # when nobody is close behind it.
    g23 = t[1]["pts"] - t[2]["pts"]
    g12 = t[0]["pts"] - t[1]["pts"]
    if g23 <= g12:
        hook, sub = str(g23), ("POINT BETWEEN 2ND AND 3RD" if g23 == 1
                               else "POINTS BETWEEN 2ND AND 3RD")
    else:
        hook, sub = str(g12), ("POINT OFF THE LEAD" if g12 == 1
                               else "POINTS OFF THE LEAD")

    x = datetime.date.fromisoformat(last)
    d["hook"], d["hookSub"] = hook, sub
    d["when"] = f"{DAYS[x.weekday()]} {x.day} {MONS[x.month - 1]}"

    os.makedirs(SP, exist_ok=True)
    with open(OUT, "w") as f:
        f.write(page(d))

    print(f"built {OUT}  {W}x{H}  {DUR}s")
    print(f"  after {d['played']} of {d['sessionsTotal']}  ·  last night {d['when']} (double)")
    for i, r in enumerate(t[:4]):
        print(f"   {i+1}. {r['name']:<20} {r['pts']}")
    print(f"  hook: {hook} {sub}")
    print("\nnow:  python3 build-lastround-audio.py && node record-lastround-video.mjs")


if __name__ == "__main__":
    main()
