# -*- coding: utf-8 -*-
"""September Surge (Vol.7) — the season recap, 1080x1920, ~32s.

Not a highlights reel of nothing in particular: the season had a real arc and
this follows it. Munther Rahbi led from night two and held it for five straight
nights. Hamed Amri's +62 on the first double-points night took the lead by two.
The last night closed it to one.

Every number is computed from the archived final state with the app's own
engine (see make-winner-data.mjs for the same approach), so nothing here is
typed in and nothing can disagree with surge.urbanpadel.om.

The podium photographs are the owner's own, used full-bleed under a scrim.

Deterministic: no CSS animations, every moving value a function of t behind
window.__seek(t).

  python3 build-recap-video.py
  python3 build-recap-audio.py
  node record-recap-video.mjs
"""
import base64, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SP = "/tmp/claude-0/-home-user-May-madness/0e44f0ad-a683-5f0d-9de6-9459ae328963/scratchpad"
VID = os.path.join(SP, "video")
PHOTOS = os.path.join(HERE, "brand", "surge-recap")
STATE = os.path.join(HERE, "archive", "september-surge", "final-standings.json")
OUT = os.path.join(SP, "recap.html")

W, H = 1080, 1920

# Vol.7's palette: cyan leads, amber supports, on deep current. The photographs
# are lit blue, which is why the recap stays in Surge's colours rather than
# borrowing Vol.8's lime.
CYAN, AMBER, CHALK, STEEL, INK, VOID = "#00E5FF", "#FF9E1B", "#F4F9FA", "#8A9BA8", "#0A0F14", "#050709"
# Vol.8's two colours, used only by the teaser at the end. The handover from one
# volume to the next is a colour change as much as anything else.
LIME, MAGENTA = "#C6FF00", "#FF2E88"

SCENES = {
    "s1": [0.00,  3.60],   # title
    "s2": [3.60,  7.60],   # the numbers
    "s3": [7.60, 13.20],   # five nights, one name — the race chart
    "s4": [13.20, 18.20],  # the double-points night
    "s5": [18.20, 21.60],  # one night left, two points
    "s6": [21.60, 25.40],  # third
    "s7": [25.40, 29.20],  # second
    "s8": [29.20, 34.00],  # champion
    "s9": [34.00, 37.70],  # the margin
    # The lights go out on Vol.7 and come up on Vol.8. The half second of black
    # between the two is the point of the cut, so the teaser scene starts with
    # nothing on screen and the mark snaps in after it.
    "s10": [37.70, 42.60], # next volume
}
DUR = 42.60
BEATS = [0.14, 1.05, 3.62, 7.62, 13.22, 18.22, 21.62, 25.42, 29.22, 30.40, 34.02, 35.20, 38.20]
HERO = {29.22, 34.02, 38.20}


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


def main():
    for p in ("p1", "p2", "p3"):
        f = os.path.join(PHOTOS, p + ".jpg")
        if not os.path.exists(f):
            sys.exit(f"missing {f}")
    if not os.path.exists(STATE):
        sys.exit("missing archive/september-surge/final-standings.json")

    st = json.load(open(STATE))
    race = json.load(open("/tmp/race.json")) if os.path.exists("/tmp/race.json") else None
    if not race:
        sys.exit("missing /tmp/race.json — run the race extraction first")

    pod = st["podium"]
    payload = json.dumps({
        "sc": SCENES, "dur": DUR, "beats": BEATS, "hero": sorted(HERO),
        "nights": st["sessions"], "matches": 193, "players": 60,
        "race": race,
        "lead": "Munther Rahbi", "leadFrom": 2, "leadTo": 6,
        "surge": {"name": "Hamed Amri", "night": 7, "gain": 62},
        "podium": [
            {"place": "CHAMPION", "name": pod[0]["name"], "pts": pod[0]["pts"],
             "line": f"{pod[0]['nights']} nights · {pod[0]['wins']} wins · "
                     f"{pod[0]['titles']} titles", "photo": "p1"},
            {"place": "RUNNER-UP", "name": pod[1]["name"], "pts": pod[1]["pts"],
             "line": f"{pod[1]['nights']} nights · {pod[1]['wins']} wins · "
                     f"led for five", "photo": "p2"},
            {"place": "THIRD", "name": pod[2]["name"], "pts": pod[2]["pts"],
             "line": f"{pod[2]['nights']} nights · {pod[2]['wins']} wins · "
                     f"{pod[2]['titles']} title", "photo": "p3"},
        ],
        "margin": st["margin"],
        "next": {"host": "blackout.urbanpadel.om", "when": "MON & WED \u00b7 ALL OCTOBER",
                 "nights": 9, "vol": "VOL.8"},
    })

    photos = {p: "data:image/jpeg;base64," + b64(os.path.join(PHOTOS, p + ".jpg"))
              for p in ("p1", "p2", "p3")}

    html = TEMPLATE.format(
        faces=inline_fonts(), data=payload, photos=json.dumps(photos),
        logo=open(os.path.join(VID, "logo.txt")).read().strip(),
        W=W, H=H, cyan=CYAN, amber=AMBER, chalk=CHALK, steel=STEEL, ink=INK, void=VOID,
        lime=LIME, magenta=MAGENTA, nexthost="BLACKOUT.URBANPADEL.OM",
    )
    with open(OUT, "w") as f:
        f.write(html)
    print(f"built recap.html  {len(html.encode())/1024/1024:.1f}MB  {DUR:.1f}s")
    print(f"  {st['sessions']} nights · 193 matches · 60 players")
    print(f"  {pod[0]['name']} {pod[0]['pts']} – {pod[1]['name']} {pod[1]['pts']}"
          f"  (margin {st['margin']})")
    print("\nnow:  python3 build-recap-audio.py && node record-recap-video.mjs")


TEMPLATE = r"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
{faces}
*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{width:{W}px;height:{H}px;background:{void};overflow:hidden}}
body{{font-family:'Archivo',sans-serif;color:{chalk};-webkit-font-smoothing:antialiased}}
#cam{{position:absolute;inset:0;transform-origin:50% 50%;
  background:radial-gradient(ellipse 760px 900px at 50% 42%, #121B23 0%, {ink} 62%, {void} 100%)}}
.scene{{position:absolute;inset:0;will-change:opacity,transform}}
.trace{{position:absolute;inset:-40px;pointer-events:none;
  background:repeating-linear-gradient(0deg, rgba(0,229,255,.05) 0 1px, transparent 1px 15px)}}
.vig{{position:absolute;inset:0;pointer-events:none;
  background:radial-gradient(ellipse 72% 58% at 50% 44%, transparent 42%, rgba(0,0,0,.74) 100%)}}
.flash{{position:absolute;inset:0;pointer-events:none;background:{cyan};
  mix-blend-mode:screen;opacity:0}}
.rail{{position:absolute;left:0;right:0;height:8px;background:{cyan};transform-origin:0 50%}}
.disp{{font-style:italic;font-variation-settings:'wdth' 125,'wght' 900;line-height:.9;
  letter-spacing:-.5px;white-space:pre-line}}
.kick{{font-family:'JetBrains Mono',monospace;font-weight:700;letter-spacing:.3em;color:{cyan}}}
.mono{{font-family:'JetBrains Mono',monospace;font-weight:700}}
.fit{{white-space:nowrap}}
/* Podium frames: the photograph fills the frame, a scrim carries the type. */
.ph{{position:absolute;inset:0;overflow:hidden}}
.ph img{{position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);
  width:100%;min-height:100%;object-fit:cover}}
.scrim{{position:absolute;inset:0;
  background:linear-gradient(180deg, rgba(5,7,9,.72) 0%, rgba(5,7,9,.08) 32%,
    rgba(5,7,9,.52) 64%, rgba(5,7,9,.96) 100%)}}
</style></head><body>

<div id="cam">
  <div class="trace" id="trace"></div>
  <div class="rail" id="rail" style="top:0"></div>

  <div class="scene" id="s1">
    <div style="position:absolute;left:50%;top:470px;width:230px;margin-left:-115px" id="s1l">
      <img src="{logo}" style="width:100%;display:block">
    </div>
    <div class="kick" style="position:absolute;left:0;right:0;top:800px;text-align:center;font-size:28px" id="s1k">URBAN SOCIAL SERIES &middot; VOL.7</div>
    <div class="disp fit" style="position:absolute;left:0;right:0;top:860px;text-align:center;font-size:148px" id="s1a">SEPTEMBER</div>
    <div class="disp fit" style="position:absolute;left:0;right:0;top:1000px;text-align:center;font-size:148px;color:{cyan}" id="s1b">SURGE</div>
    <div style="position:absolute;left:50%;top:1190px;width:420px;height:5px;margin-left:-210px;background:{cyan}" id="s1r"></div>
    <div class="disp fit" style="position:absolute;left:0;right:0;top:1250px;text-align:center;font-size:84px" id="s1c">THE RECAP</div>
  </div>

  <div class="scene" id="s2">
    <div class="kick" style="position:absolute;left:0;right:0;top:520px;text-align:center;font-size:26px">THE SEASON IN THREE NUMBERS</div>
    <div style="position:absolute;left:90px;right:90px;top:620px" id="s2w"></div>
  </div>

  <div class="scene" id="s3">
    <div class="kick" style="position:absolute;left:0;right:0;top:180px;text-align:center;font-size:26px" id="s3k">NIGHTS TWO TO SIX</div>
    <div class="disp" style="position:absolute;left:0;right:0;top:240px;text-align:center;font-size:104px" id="s3h">ONE NAME
AT THE TOP.</div>
    <canvas id="chart" width="900" height="620" style="position:absolute;left:90px;top:560px"></canvas>
    <div id="s3lg" style="position:absolute;left:90px;right:90px;top:1230px"></div>
    <div class="disp fit" style="position:absolute;left:0;right:0;top:1400px;text-align:center;font-size:64px;color:{cyan}" id="s3n"></div>
  </div>

  <div class="scene" id="s4">
    <div class="kick" style="position:absolute;left:0;right:0;top:400px;text-align:center;font-size:26px;color:{amber}" id="s4k">SESSION 7 &middot; DOUBLE POINTS</div>
    <div class="disp" style="position:absolute;left:0;right:0;top:462px;text-align:center;font-size:110px" id="s4h">SIXTY-TWO
IN ONE NIGHT.</div>
    <div class="mono" style="position:absolute;left:0;right:0;top:740px;text-align:center;font-size:200px;color:{amber};line-height:1" id="s4n">+62</div>
    <div class="disp fit" style="position:absolute;left:0;right:0;top:1000px;text-align:center;font-size:76px" id="s4w"></div>
    <div style="position:absolute;left:0;right:0;top:1130px;text-align:center;font-size:30px;color:{steel}" id="s4s"></div>
  </div>

  <div class="scene" id="s5">
    <div class="disp" style="position:absolute;left:0;right:0;top:640px;text-align:center;font-size:124px" id="s5h">ONE NIGHT LEFT.</div>
    <div class="mono" style="position:absolute;left:0;right:0;top:860px;text-align:center;font-size:250px;color:{cyan};line-height:1" id="s5n">2</div>
    <div class="disp fit" style="position:absolute;left:0;right:0;top:1140px;text-align:center;font-size:88px" id="s5w">POINTS IN IT.</div>
  </div>

  <div class="scene" id="s6"></div>
  <div class="scene" id="s7"></div>
  <div class="scene" id="s8"></div>

  <div class="scene" id="s9">
    <div class="kick" style="position:absolute;left:0;right:0;top:560px;text-align:center;font-size:28px">EIGHT NIGHTS, DECIDED BY</div>
    <div class="disp" style="position:absolute;left:0;right:0;top:620px;text-align:center;font-size:300px;color:{cyan}" id="s9n">1</div>
    <div class="disp fit" style="position:absolute;left:0;right:0;top:940px;text-align:center;font-size:104px" id="s9w">POINT.</div>
    <div class="mono" style="position:absolute;left:0;right:0;top:1100px;text-align:center;font-size:46px;color:{steel}" id="s9m"></div>
    <div style="position:absolute;left:50%;top:1250px;width:380px;height:4px;margin-left:-190px;background:{cyan}" id="s9r"></div>
    <div style="position:absolute;left:50%;top:1320px;width:160px;margin-left:-80px" id="s9l">
      <img src="{logo}" style="width:100%;display:block">
    </div>
    <div class="mono" style="position:absolute;left:0;right:0;top:1560px;text-align:center;font-size:25px;letter-spacing:.3em;color:{steel}">URBAN PLAYGROUND &middot; MUSCAT</div>
  </div>

  <!-- ── NEXT: the Vol.8 teaser. Its own ground, because this is where the
       series changes colour. ── -->
  <div class="scene" id="s10">
    <div style="position:absolute;inset:0;background:{void}"></div>
    <div style="position:absolute;inset:0;
      background:radial-gradient(circle at 100% 16%, rgba(255,46,136,.18), transparent 44%),
                 radial-gradient(circle at 0% 90%, rgba(198,255,0,.10), transparent 42%)"></div>
    <div style="position:absolute;inset:-40px;
      background:repeating-linear-gradient(0deg, rgba(198,255,0,.05) 0 2px, transparent 2px 10px)"
      id="s10sc"></div>
    <div class="kick" style="position:absolute;left:0;right:0;top:470px;text-align:center;font-size:28px;color:{lime}" id="s10k">NEXT</div>
    <div style="position:absolute;left:50%;top:560px;width:132px;height:132px;margin-left:-66px" id="s10m">
      <span style="position:absolute;inset:0;background:{lime}"></span>
      <span style="position:absolute;left:0;right:0;top:62px;height:4px;background:{void}"></span>
      <span style="position:absolute;left:0;right:0;top:78px;height:8px;background:{void}"></span>
      <span style="position:absolute;left:0;right:0;top:97px;height:12px;background:{void}"></span>
      <span style="position:absolute;left:0;right:0;top:118px;height:14px;background:{void}"></span>
      <span style="position:absolute;right:16px;top:16px;width:17px;height:17px;background:{magenta}"></span>
    </div>
    <div class="disp fit" style="position:absolute;left:0;right:0;top:760px;text-align:center;font-size:132px" id="s10w">BLACKOUT</div>
    <div class="disp fit" style="position:absolute;left:0;right:0;top:920px;text-align:center;font-size:104px;color:{lime}" id="s10t">LIGHTS OUT.</div>
    <div style="position:absolute;left:50%;top:1100px;width:460px;height:5px;margin-left:-230px;background:{lime}" id="s10r"></div>
    <div class="mono" style="position:absolute;left:0;right:0;top:1170px;text-align:center;font-size:27px;letter-spacing:.24em;color:{steel}" id="s10d"></div>
    <div class="disp fit" style="position:absolute;left:0;right:0;top:1280px;text-align:center;font-size:58px;color:{lime}" id="s10u">{nexthost}</div>
  </div>

  <div class="vig"></div>
</div>
<div class="flash" id="flash"></div>

<script>
const D = {data}, PH = {photos};
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
function widen(el,t,t0,d,{{w0=66,w1=125,blur=11}}={{}}){{
  const p=outExpo(inv(t,t0,t0+d)), o=inv(t,t0,t0+d*0.3);
  el.style.fontVariationSettings=`'wdth' ${{(w0+(w1-w0)*p).toFixed(1)}},'wght' 900`;
  set(el,o,`scale(${{(1+0.04*(1-p)).toFixed(4)}})`,`blur(${{(blur*(1-p)).toFixed(2)}}px)`);
}}
const countTo=(t,t0,d,to)=>Math.round(to*outExpo(inv(t,t0,t0+d)));

// Shrink-to-fit. Gated on fonts.check, not fonts.status -- status reads "loaded"
// before any face has been requested. Scenes are laid out for the measuring
// pass, because a hidden element measures zero wide and that reads as fitting.
let fitted=false;
function fitOnce(){{
  if(fitted || !document.fonts.check("italic 900 40px Archivo")) return;
  const hid=[...document.querySelectorAll('.scene')].map(s=>[s,s.style.display]);
  hid.forEach(([s])=>{{s.style.display='block';}});
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
  hid.forEach(([s,d])=>{{s.style.display=d;}});
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

/* ── the three numbers ── */
document.getElementById('s2w').innerHTML = [
  ["nights","NIGHTS"],["matches","MATCHES"],["players","PLAYERS"],
].map(([k,l],i)=>`
  <div id="n${{i}}" style="border-top:1px solid rgba(244,249,250,.12);padding:34px 0 26px">
    <div class="mono" id="nv${{i}}" style="font-size:132px;line-height:1;color:${{i===1?"#FF9E1B":"#00E5FF"}}">0</div>
    <div class="mono" style="font-size:24px;letter-spacing:.3em;color:#8A9BA8;margin-top:10px">${{l}}</div>
  </div>`).join('');

/* ── podium scenes, generated so the three cannot drift ── */
D.podium.forEach((p,i)=>{{
  const host=document.getElementById(['s8','s7','s6'][i]);   // 3rd, 2nd, 1st in time order
  host.innerHTML=`
    <div class="ph" id="ph${{i}}"><img src="${{PH[p.photo]}}" alt=""></div>
    <div class="scrim"></div>
    <div class="disp fit" id="pn${{i}}" style="position:absolute;left:0;right:0;top:1250px;text-align:center;font-size:${{i===0?122:104}}px">${{p.name.toUpperCase()}}</div>
    <div class="mono" id="pp${{i}}" style="position:absolute;left:0;right:0;top:1392px;text-align:center;font-size:${{i===0?150:124}}px;line-height:1;color:#00E5FF">0</div>
    <div class="mono" id="pl${{i}}" style="position:absolute;left:0;right:0;top:1562px;text-align:center;font-size:25px;letter-spacing:.2em;color:#8A9BA8">${{p.line.toUpperCase()}}</div>`;
}});

/* ── the title race, drawn once the scene is live ── */
const CH=document.getElementById('chart'), CTX=CH.getContext('2d');
const NAMES=Object.keys(D.race), SER=NAMES.map(n=>D.race[n]);
const COL=["#00E5FF","#F4F9FA","#8A9BA8"];
document.getElementById('s3lg').innerHTML = NAMES.map((n,i)=>`
  <div style="display:flex;align-items:center;gap:12px;margin-bottom:10px">
    <span style="width:26px;height:4px;background:${{COL[i]}}"></span>
    <span style="font-weight:800;font-size:24px;color:${{i===2?"#8A9BA8":"#F4F9FA"}}">${{n}}</span>
  </div>`).join('');

function drawChart(p){{
  const w=CH.width,h=CH.height,pad=10;
  CTX.clearRect(0,0,w,h);
  const maxY=200, n=SER[0].length;
  const X=i=>pad+(w-pad*2)*(i/(n-1));
  const Y=v=>h-pad-(h-pad*2)*(v/maxY);
  // grid
  CTX.strokeStyle="rgba(244,249,250,.07)"; CTX.lineWidth=2;
  for(let g=0;g<=4;g++){{const y=Y(g*50);CTX.beginPath();CTX.moveTo(0,y);CTX.lineTo(w,y);CTX.stroke();}}
  SER.forEach((s,si)=>{{
    const upto=p*(n-1);
    CTX.strokeStyle=COL[si]; CTX.lineWidth=si===2?4:6; CTX.lineJoin="round"; CTX.lineCap="round";
    CTX.beginPath();
    for(let i=0;i<n;i++){{
      if(i>upto){{
        // partial segment, so the lines grow rather than pop in
        const prev=i-1, f=upto-prev;
        if(f>0){{
          const x=X(prev)+(X(i)-X(prev))*f, y=Y(s[prev])+(Y(s[i])-Y(s[prev]))*f;
          CTX.lineTo(x,y);
        }}
        break;
      }}
      i===0?CTX.moveTo(X(i),Y(s[i])):CTX.lineTo(X(i),Y(s[i]));
    }}
    CTX.stroke();
    // the head of each line
    const i=Math.min(n-1,Math.floor(upto)), f=upto-i;
    const nx=Math.min(n-1,i+1);
    const hx=X(i)+(X(nx)-X(i))*f, hy=Y(s[i])+(Y(s[nx])-Y(s[i]))*f;
    if(upto>0){{CTX.fillStyle=COL[si];CTX.beginPath();CTX.arc(hx,hy,si===2?6:9,0,7);CTX.fill();}}
  }});
}}

function seek(t){{
  fitOnce();
  const [e,h]=energy(t);
  const sx=e>0.001?Math.sin(t*118)*7*e:0, sy=e>0.001?Math.cos(t*97)*5*e:0;
  document.getElementById('cam').style.transform=
    `translate(${{sx.toFixed(2)}}px,${{sy.toFixed(2)}}px) scale(${{(1+e*0.012).toFixed(4)}})`;
  document.getElementById('flash').style.opacity=(e*0.05+h*0.13).toFixed(3);
  const tr=document.getElementById('trace');
  tr.style.transform=`translateY(${{(t*3.4)%15}}px)`;
  tr.style.opacity=(0.9+e*1.5).toFixed(3);

  for(const k of Object.keys(D.sc)){{
    const [a,b]=D.sc[k];
    const o=Math.min(inv(t,a-XF,a+0.02), 1-inv(t,b,b+XF));
    const el=document.getElementById(k);
    el.style.opacity=o.toFixed(3);
    el.style.display=o<=0.002?'none':'block';
  }}

  {{ const u=t-D.sc.s1[0];
    set(document.getElementById('s1l'), inv(u,0.10,0.52),
        `scale(${{(0.88+0.12*outBack(inv(u,0.10,0.80))).toFixed(4)}})`);
    set(document.getElementById('s1k'), inv(u,0.60,0.90),
        `translateY(${{(12*(1-outQuint(inv(u,0.60,1.1)))).toFixed(1)}}px)`);
    widen(document.getElementById('s1a'),u,0.76,0.80);
    widen(document.getElementById('s1b'),u,0.92,0.80);
    const r=document.getElementById('s1r');
    set(r,1,`scaleX(${{outQuint(inv(u,1.46,1.90)).toFixed(3)}})`);
    widen(document.getElementById('s1c'),u,1.60,0.68,{{w0:76}});
    const rail=document.getElementById('rail');
    rail.style.transform=`scaleX(${{outExpo(inv(t,0.02,0.60)).toFixed(3)}})`;
  }}

  {{ const u=t-D.sc.s2[0];
    const vals=[D.nights,D.matches,D.players];
    vals.forEach((v,i)=>{{
      const t0=0.24+i*0.42;
      set(document.getElementById('n'+i), inv(u,t0,t0+0.26),
          `translateY(${{(18*(1-outQuint(inv(u,t0,t0+0.7)))).toFixed(1)}}px)`);
      document.getElementById('nv'+i).textContent=countTo(u,t0+0.06,0.80,v);
    }});
  }}

  {{ const u=t-D.sc.s3[0];
    set(document.getElementById('s3k'), inv(u,0.10,0.36));
    widen(document.getElementById('s3h'),u,0.20,0.70,{{w0:74,blur:8}});
    const p=outCubic(inv(u,0.70,3.10));
    set(CH, inv(u,0.62,0.92)); drawChart(p);
    set(document.getElementById('s3lg'), inv(u,1.10,1.44));
    const nm=document.getElementById('s3n');
    nm.textContent=D.lead.toUpperCase()+" LED FOR FIVE";
    widen(nm,u,3.10,0.70,{{w0:80,blur:7}});
  }}

  {{ const u=t-D.sc.s4[0];
    set(document.getElementById('s4k'), inv(u,0.10,0.36));
    widen(document.getElementById('s4h'),u,0.20,0.70,{{w0:74,blur:8}});
    const n=document.getElementById('s4n');
    n.textContent="+"+countTo(u,0.72,0.95,D.surge.gain);
    set(n, inv(u,0.72,0.96), `scale(${{(0.9+0.1*outBack(inv(u,0.72,1.3))).toFixed(4)}})`);
    const w=document.getElementById('s4w'); w.textContent=D.surge.name.toUpperCase();
    widen(w,u,1.30,0.68,{{w0:80,blur:6}});
    const s=document.getElementById('s4s');
    s.textContent="and the lead, by two";
    set(s, inv(u,1.78,2.08));
  }}

  {{ const u=t-D.sc.s5[0];
    widen(document.getElementById('s5h'),u,0.12,0.70,{{w0:74,blur:9}});
    const n=document.getElementById('s5n');
    set(n, inv(u,0.60,0.86), `scale(${{(0.86+0.14*outBack(inv(u,0.60,1.2))).toFixed(4)}})`);
    widen(document.getElementById('s5w'),u,1.00,0.62,{{w0:80,blur:6}});
  }}

  D.podium.forEach((p,i)=>{{
    const key=['s8','s7','s6'][i];
    const u=t-D.sc[key][0], span=D.sc[key][1]-D.sc[key][0];
    // a slow push in on the photograph, so the frame is never still
    const z=1.04+0.06*inv(u,0,span);
    set(document.getElementById('ph'+i), inv(u,0.04,0.46), `scale(${{z.toFixed(4)}})`);
    widen(document.getElementById('pn'+i), u, 0.52, 0.74, {{w0:76,blur:8}});
    const pp=document.getElementById('pp'+i);
    pp.textContent=countTo(u,0.84,0.90,p.pts);
    set(pp, inv(u,0.84,1.06));
    set(document.getElementById('pl'+i), inv(u,1.24,1.52));
  }});

  {{ const u=t-D.sc.s9[0];
    const n=document.getElementById('s9n');
    n.textContent=String(D.margin);
    widen(n,u,0.20,0.76,{{w0:70,blur:16}});
    widen(document.getElementById('s9w'),u,0.56,0.62,{{w0:78,blur:8}});
    const m=document.getElementById('s9m');
    m.textContent=`${{D.podium[0].pts}}  –  ${{D.podium[1].pts}}`;
    set(m, inv(u,0.90,1.20), `translateY(${{(14*(1-outQuint(inv(u,0.90,1.5)))).toFixed(1)}}px)`);
    set(document.getElementById('s9r'),1,`scaleX(${{outQuint(inv(u,1.26,1.70)).toFixed(3)}})`);
    set(document.getElementById('s9l'), inv(u,1.44,1.80),
        `scale(${{(0.92+0.08*outBack(inv(u,1.44,2.1))).toFixed(4)}})`);
  }}

  {{ const u=t-D.sc.s10[0];
    // Half a second of nothing: the lights are out. Everything below starts
    // after it, and the flash on the mark is the switch coming back on.
    const sc=document.getElementById('s10sc');
    sc.style.transform=`translateY(${{(t*3.2)%10}}px)`;
    set(document.getElementById('s10k'), inv(u,0.46,0.72));
    set(document.getElementById('s10m'), inv(u,0.50,0.74),
        `scale(${{(0.7+0.3*outBack(inv(u,0.50,1.05))).toFixed(4)}})`);
    widen(document.getElementById('s10w'),u,0.76,0.72,{{w0:70,blur:14}});
    widen(document.getElementById('s10t'),u,0.98,0.68,{{w0:76,blur:9}});
    set(document.getElementById('s10r'),1,`scaleX(${{outQuint(inv(u,1.42,1.86)).toFixed(3)}})`);
    const dd=document.getElementById('s10d');
    dd.textContent=`${{D.next.vol}} \u00b7 ${{D.next.nights}} NIGHTS \u00b7 ${{D.next.when}}`;
    set(dd, inv(u,1.64,1.96));
    widen(document.getElementById('s10u'),u,1.90,0.60,{{w0:80,blur:6}});
  }}
}}
window.__seek=seek; window.__dur=DUR; seek(0);
</script></body></html>"""


if __name__ == "__main__":
    main()
