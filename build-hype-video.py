# -*- coding: utf-8 -*-
"""Blackout Vol.8 — the 18-second FINAL WEEK hype cut. ANIMATED, no photographs.

The first version of this cut was led by the session photos. They were
rejected and the reason is sound: every one of them is the same posed
four-at-the-net line-up, so nine of them in a row read as a gallery rather
than as a film. Nothing moved except a slow push on a still.

So the picture is generated instead, in the volume's own language — true
black, lime, magenta, hard geometry, radius 0 — and the one scene that was a
LIST is now a RACE: four bars growing to their real points with the numbers
counting under them, which is the same information doing some work.

Every figure still comes from ops/blackout-standings.mjs, which runs the app's
own engine over the live state.

Deterministic: no CSS animations, no requestAnimationFrame, every moving value
a pure function of t behind window.__seek(t). The canvas backdrop is redrawn
from scratch on each seek, so scrubbing to a time gives the same pixels every
run.

  python3 build-hype-audio.py
  python3 build-hype-video.py
  node record-hype-video.mjs
"""
import base64, datetime, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SP = "/tmp/claude-0/-home-user-May-madness/0e44f0ad-a683-5f0d-9de6-9459ae328963/scratchpad"
VID = os.path.join(SP, "video")
STD = os.path.join(SP, "bo-standings.json")
OUT = os.path.join(SP, "hype.html")

W, H = 1080, 1920
LIME, MAGENTA, INK, MUTED, BG = "#C6FF00", "#FF2E88", "#F2F2F2", "#9A9A9A", "#050505"
LIMEPALE, LIMEDEEP = "#E9FF86", "#8CB800"

SCENES = [0.00, 4.20, 8.60, 12.40]
DUR = 18.00
BEATS = [0.10, 4.22, 8.62, 10.50, 12.42, 14.30, 16.10]
HERO = [8.62, 12.42]

DAYS = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]


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
    x = datetime.date.fromisoformat(d)
    return f"{DAYS[x.weekday()]} {x.day}"


def main():
    if not os.path.exists(STD):
        sys.exit("missing bo-standings.json — run ops/blackout-standings.mjs first")
    d = json.load(open(STD))
    cfg = json.load(open(os.path.join(HERE, "blackout-season.json")))
    assert d["remaining"], "no nights left — this is not a final-week film"
    assert d["doubleNights"], "no doubled nights left; scene 3 would be a lie"

    top = d["table"][:4]
    bars = "".join(
        f'<div class="bar{" ld" if i == 0 else " lo" if i == len(top) - 1 else ""}" id="b{i}">'
        f'<div class="bn">{r["name"].upper()}</div>'
        f'<div class="btrack"><div class="bfill" id="bf{i}"></div></div>'
        f'<div class="bp" id="bp{i}">0</div></div>'
        for i, r in enumerate(top))

    dates = " · ".join(short(x) for x in d["remaining"])
    dbl = " & ".join(short(x) for x in d["doubleNights"])

    payload = json.dumps({
        "scenes": SCENES, "dur": DUR, "beats": BEATS, "hero": HERO,
        "pts": [r["pts"] for r in top], "max": top[0]["pts"],
        "gap": d["gap14"], "rows": len(top),
    })

    mark = open(os.path.join(HERE, "brand", "blackout", "blackout-mark.svg")).read()
    html = TEMPLATE.format(
        faces=inline_fonts(), data=payload, W=W, H=H,
        mark=base64.b64encode(mark.encode()).decode(),
        lime=LIME, magenta=MAGENTA, ink=INK, muted=MUTED, bg=BG,
        limepale=LIMEPALE, limedeep=LIMEDEEP,
        bars=bars, left=len(d["remaining"]), dates=dates, dbl=dbl,
        gap=d["gap14"], host=cfg["host"].upper(),
    )
    with open(OUT, "w") as f:
        f.write(html)
    print(f"built hype.html  {len(html.encode())/1024/1024:.1f}MB  {DUR:.1f}s  animated")
    print(f"  {d['played']}/{d['sessionsTotal']} nights · {dates} left · {dbl} double")
    print(f"  bars: " + ", ".join(f"{r['name'].split()[0]} {r['pts']}" for r in top)
          + f"   gap {d['gap14']}")
    print("\nnow:  node record-hype-video.mjs")


TEMPLATE = r"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
{faces}
*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{width:{W}px;height:{H}px;background:{bg};overflow:hidden}}
body{{font-family:'Archivo',sans-serif;color:{ink};-webkit-font-smoothing:antialiased}}
#cam{{position:absolute;inset:0;overflow:hidden;background:{bg}}}
#bg{{position:absolute;inset:0}}
.scene{{position:absolute;inset:0;z-index:5;will-change:opacity}}
.disp{{font-style:italic;font-variation-settings:'wdth' 125,'wght' 900;line-height:.88;
  letter-spacing:-.5px;white-space:pre-line}}
.kick{{font-family:'JetBrains Mono',monospace;font-weight:700;letter-spacing:.3em;color:{lime}}}
.mono{{font-family:'JetBrains Mono',monospace;font-weight:700}}
.ctr{{position:absolute;left:0;right:0;text-align:center}}
.fit{{white-space:nowrap}}
/* The bar race. Square ends, no radius — the volume has none. */
.bar{{display:flex;align-items:center;gap:16px;height:92px;will-change:opacity,transform}}
/* NO overflow:hidden. It silently cut MUNTASER HASNI to "MUNTASER HAS" and
   hid the fault from the recorder's clipping check, which is exactly the
   failure DESIGN.md records for the brand art — a box that fits while the ink
   inside it does not. Sized for the longest name the top four can produce. */
.bar .bn{{width:384px;flex:0 0 384px;font-style:italic;
  font-variation-settings:'wdth' 92,'wght' 900;font-size:31px;
  white-space:nowrap;text-align:right}}
.bar .btrack{{flex:1;height:38px;background:rgba(242,242,242,.09);position:relative}}
.bar .bfill{{position:absolute;left:0;top:0;bottom:0;width:0;background:{limedeep};
  transform-origin:0 50%}}
.bar .bp{{width:124px;flex:0 0 124px;font-style:italic;
  font-variation-settings:'wdth' 110,'wght' 900;font-size:52px;text-align:right}}
.bar.ld .bfill{{background:{lime}}}
.bar.ld .bn,.bar.ld .bp{{color:{lime}}}
.bar.lo .bfill{{background:{magenta}}}
.bar.lo .bn,.bar.lo .bp{{color:{magenta}}}
.flash{{position:absolute;inset:0;pointer-events:none;background:{lime};
  mix-blend-mode:screen;opacity:0;z-index:8}}
</style></head><body>

<div id="cam">
  <canvas id="bg" width="{W}" height="{H}"></canvas>

  <!-- 1 · the slam -->
  <div class="scene" id="s1">
    <div style="position:absolute;left:50%;top:620px;width:150px;height:150px;margin-left:-75px" id="s1m">
      <img src="data:image/svg+xml;base64,{mark}" style="width:100%;display:block">
    </div>
    <div class="kick ctr" style="top:848px;font-size:26px" id="s1k">BLACKOUT SERIES &middot; VOL.8</div>
    <div class="disp ctr fit" style="top:910px;font-size:196px" id="s1t">FINAL WEEK</div>
    <div class="disp ctr" style="top:1128px;font-size:84px;color:{lime}" id="s1g">{left} NIGHTS LEFT.</div>
  </div>

  <!-- 2 · the race -->
  <div class="scene" id="s2">
    <div class="kick ctr" style="top:596px;font-size:24px" id="s2k">SIX NIGHTS IN</div>
    <div id="s2g" style="position:absolute;left:62px;right:62px;top:664px">{bars}</div>
    <div class="ctr" style="top:1128px;font-size:44px" id="s2n">
      <b style="color:{lime}">{gap} points</b> cover the top four.</div>
  </div>

  <!-- 3 · the multiplier -->
  <div class="scene" id="s3">
    <div class="kick ctr" style="top:694px;font-size:28px;color:{magenta}" id="s3k">{dbl}</div>
    <div class="ctr" id="s3b" style="top:752px">
      <span class="disp" style="font-size:300px;color:{magenta}" id="s3x">2X</span>
    </div>
    <div class="disp ctr fit" style="top:1086px;font-size:96px" id="s3t">DOUBLE POINTS.</div>
  </div>

  <!-- 4 · the dates -->
  <div class="scene" id="s4">
    <div class="disp ctr" style="top:700px;font-size:122px" id="s4t">SEE IT OUT.</div>
    <div style="position:absolute;left:50%;top:876px;width:480px;height:5px;margin-left:-240px;background:{lime}" id="s4r"></div>
    <div class="mono ctr fit" style="top:934px;font-size:40px;letter-spacing:.14em;color:{lime}" id="s4d">{dates}</div>
    <div class="disp ctr fit" style="top:1024px;font-size:58px;color:{lime}" id="s4u">{host}</div>
    <div class="mono ctr" style="top:1124px;font-size:25px;letter-spacing:.3em;color:{muted}" id="s4e">URBAN PLAYGROUND &middot; MUSCAT</div>
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
  if(!el) return;
  el.style.opacity=o.toFixed(3);
  if(tr!==undefined) el.style.transform=tr;
  if(fl!==undefined) el.style.filter=fl;
}}
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
let fitted=false;
function fitOnce(){{
  if(fitted || !document.fonts.check("italic 900 40px Archivo")) return;
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

// ── the backdrop ───────────────────────────────────────────────────────────
// Redrawn from scratch every seek. No stored state, no rAF — scrubbing to a
// time must give the same pixels whichever order the frames are asked for.
//
// Three layers, all in the volume's own vocabulary: a court-ish perspective
// grid that drifts, speed lines that fire on the beats, and a shockwave that
// belongs to the 2X.
const CV=document.getElementById('bg'), X=CV.getContext('2d');
const LIME='{lime}', MAG='{magenta}';

function grid(t,e){{
  // A floor receding to a vanishing point above centre. The verticals fan out
  // from it and the horizontals bunch toward it, which is what makes a flat
  // canvas read as a court rather than as graph paper.
  const vy=820, drift=(t*0.055)%1;
  X.save();
  X.strokeStyle='rgba(198,255,0,'+(0.10+0.06*e).toFixed(3)+')';
  X.lineWidth=2;
  for(let i=-9;i<=9;i++){{
    X.beginPath(); X.moveTo({W}/2+i*26, vy); X.lineTo({W}/2+i*560, {H}+120); X.stroke();
  }}
  for(let k=0;k<14;k++){{
    const u=((k+drift)/14), y=vy+Math.pow(u,2.1)*({H}+140-vy);
    X.strokeStyle='rgba(198,255,0,'+(0.16*u+0.05).toFixed(3)+')';
    X.beginPath(); X.moveTo(0,y); X.lineTo({W},y); X.stroke();
  }}
  X.restore();
}}

function speedlines(t,e){{
  if(e<0.02) return;
  X.save();
  X.globalAlpha=e*0.55;
  X.strokeStyle=LIME; X.lineWidth=3;
  // Deterministic pseudo-random: seeded off the beat index, not Math.random,
  // or every re-render of the same frame would draw different lines.
  for(let i=0;i<16;i++){{
    const s=Math.sin(i*12.9898+Math.floor(t*4)*78.233)*43758.5453;
    const r=s-Math.floor(s);
    const y=r*{H}, len=120+((r*7)%1)*340, dir=i%2?1:-1;
    const x=dir>0? -60+((r*13)%1)*300 : {W}+60-((r*13)%1)*300;
    X.beginPath(); X.moveTo(x,y); X.lineTo(x+dir*len,y); X.stroke();
  }}
  X.restore();
}}

function shock(t){{
  // Rings expanding from the 2X stamp. Scene 3 only.
  const a=D.scenes[2];
  if(t<a-0.1||t>a+2.2) return;
  X.save();
  for(let k=0;k<3;k++){{
    const p=inv(t,a+k*0.16,a+k*0.16+1.5);
    if(p<=0||p>=1) continue;
    X.globalAlpha=(1-p)*0.5;
    X.strokeStyle=MAG; X.lineWidth=6*(1-p)+1;
    X.beginPath(); X.arc({W}/2, 905, 60+p*980, 0, Math.PI*2); X.stroke();
  }}
  X.restore();
}}

function glow(t,e,h){{
  const g=X.createRadialGradient({W}/2,860,40,{W}/2,860,980);
  const a=0.16+0.16*e+0.22*h;
  g.addColorStop(0,'rgba(198,255,0,'+(a*0.55).toFixed(3)+')');
  g.addColorStop(0.45,'rgba(198,255,0,'+(a*0.13).toFixed(3)+')');
  g.addColorStop(1,'rgba(5,5,5,0)');
  X.fillStyle=g; X.fillRect(0,0,{W},{H});
}}

function backdrop(t,e,h){{
  X.fillStyle='{bg}'; X.fillRect(0,0,{W},{H});
  grid(t,e);
  glow(t,e,h);
  speedlines(t,e);
  shock(t);
  // vignette, so the corners never compete with the type
  const v=X.createRadialGradient({W}/2,{H}*0.46,220,{W}/2,{H}*0.46,1180);
  v.addColorStop(0,'rgba(5,5,5,0)'); v.addColorStop(1,'rgba(5,5,5,0.92)');
  X.fillStyle=v; X.fillRect(0,0,{W},{H});
}}

const S=D.scenes, END=[...S.slice(1), DUR];
function seek(t){{
  fitOnce();
  const [e,h]=energy(t);
  backdrop(t,e,h);
  document.getElementById('flash').style.opacity=(e*0.05+h*0.10).toFixed(3);
  document.getElementById('cam').style.transform=
    `scale(${{(1+e*0.008).toFixed(4)}})`;

  for(let i=0;i<S.length;i++){{
    const o=Math.min(inv(t,S[i]-XF,S[i]+0.02), 1-inv(t,END[i],END[i]+XF));
    const el=document.getElementById('s'+(i+1));
    el.style.opacity=o.toFixed(3);
    el.style.display=o<=0.002?'none':'block';
  }}
  const g=(i)=>document.getElementById(i);

  {{ // 1 · the slam
    const u=t-S[0];
    set(g('s1m'), inv(u,0.06,0.42), `scale(${{(0.80+0.20*outBack(inv(u,0.06,0.78))).toFixed(4)}})`);
    rise(g('s1k'), u, 0.46, 0.44, 12);
    widen(g('s1t'), u, 0.62, 0.80);
    widen(g('s1g'), u, 1.24, 0.60, {{w0:86,blur:7}});
  }}

  {{ // 2 · the race. Bars grow to their real totals and the numbers count
     //     with them — the same figures the list showed, doing some work.
    const u=t-S[1];
    rise(g('s2k'), u, 0.04, 0.34, 10);
    for(let i=0;i<D.rows;i++){{
      const a=0.20+i*0.13;
      set(g('b'+i), inv(u,a,a+0.22), `translateX(${{(-26*(1-outQuint(inv(u,a,a+0.5)))).toFixed(1)}}px)`);
      const p=outCubic(inv(u,a+0.10,a+1.35));
      const frac=(D.pts[i]/D.max)*p;
      g('bf'+i).style.width=(frac*100).toFixed(2)+'%';
      g('bp'+i).textContent=Math.round(D.pts[i]*p);
    }}
    rise(g('s2n'), u, 2.10, 0.46, 14);
  }}

  {{ // 3 · the multiplier — a stamp, not a sentence
    const u=t-S[2];
    rise(g('s3k'), u, 0.04, 0.30, 10);
    const q=outBack(inv(u,0.10,0.62));
    set(g('s3b'), inv(u,0.10,0.24),
        `scale(${{(1.34-0.34*q).toFixed(4)}})`, `blur(${{(14*(1-outExpo(inv(u,0.10,0.52)))).toFixed(2)}}px)`);
    widen(g('s3t'), u, 0.74, 0.62, {{w0:74,blur:8}});
  }}

  {{ // 4 · the dates
    const u=t-S[3];
    widen(g('s4t'), u, 0.12, 0.72);
    set(g('s4r'), 1, `scaleX(${{outQuint(inv(u,0.64,1.04)).toFixed(3)}})`);
    set(g('s4d'), inv(u,0.88,1.14));
    widen(g('s4u'), u, 1.16, 0.56, {{w0:80,blur:6}});
    set(g('s4e'), inv(u,1.64,1.94));
  }}
}}
window.__seek=seek; window.__dur=DUR; window.__outro=S[3]; seek(0);
</script></body></html>"""


if __name__ == "__main__":
    main()
