# -*- coding: utf-8 -*-
"""Blackout Series Vol.8 — "what's new in the app", 1080x1920, ~25s.

For the players, not the organiser: it shows the four things they will actually
use — their points explained, the receipt behind every night, badges, and the
share card — and ends on where to find it.

The screens are REAL captures of the live app, not mockups. The data in them is
last season's, because Vol.8 has not been played yet, so the frame carries a
label saying so rather than letting a 189 read as a Vol.8 claim.

Deterministic, like the winner video: no CSS animations anywhere, every moving
value a pure function of t behind window.__seek(t).

  node capture-app-screens.mjs      # refreshes /tmp/shots
  python3 build-feature-video.py
  python3 build-feature-audio.py
  node record-feature-video.mjs
"""
import base64, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SP = "/tmp/claude-0/-home-user-May-madness/0e44f0ad-a683-5f0d-9de6-9459ae328963/scratchpad"
VID = os.path.join(SP, "video")
SHOTS = "/tmp/shots"
OUT = os.path.join(SP, "feature.html")

W, H = 1080, 1920
LIME, MAGENTA, INK, MUTED, BG = "#C6FF00", "#FF2E88", "#F2F2F2", "#9A9A9A", "#050505"

# Scene table. Each feature gets the same shape so the cut has a rhythm: the
# caption lands, then the screen, then it holds long enough to actually read.
SCENES = [
    dict(k="s1", t=[0.00, 3.40], kind="title"),
    dict(k="s2", t=[3.40, 8.00], shot="me",      kick="YOUR POINTS",
         head="EVERY POINT,\nEXPLAINED.",
         note="Where every single one came from."),
    dict(k="s3", t=[8.00, 12.60], shot="receipt", kick="TAP ANY NIGHT",
         head="THE FULL\nRECEIPT.",
         note="Every match, the score, the points."),
    dict(k="s4", t=[12.60, 16.80], shot="badges", kick="SEVEN TO COLLECT",
         head="BADGES.",
         note="Iron man. Giant killer. On a run."),
    dict(k="s5", t=[16.80, 21.00], shot="share",  kick="ONE TAP",
         head="SHARE YOUR\nNIGHT.",
         note="Straight to your story."),
    dict(k="s6", t=[21.00, 24.60], shot="roster", kick="EVERY PLAYER, EVERY VOLUME",
         head="314 OF US.",
         note="All-time points, carried over."),
    dict(k="s7", t=[24.60, 28.20], kind="outro"),
]
DUR = SCENES[-1]["t"][1]
BEATS = [0.14, 1.05, 3.42, 8.02, 12.62, 16.82, 21.02, 24.62, 25.60]
HERO = {24.62}


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
    cfg = json.load(open(os.path.join(HERE, "blackout-season.json")))
    shots = {}
    for s in SCENES:
        if not s.get("shot"):
            continue
        p = os.path.join(SHOTS, s["shot"] + ".png")
        if not os.path.exists(p):
            sys.exit(f"missing {p} — run the capture first")
        shots[s["shot"]] = "data:image/png;base64," + b64(p)

    mark = open(os.path.join(HERE, "brand", "blackout", "blackout-mark.svg")).read()
    payload = json.dumps({
        "scenes": SCENES, "shots": shots, "dur": DUR,
        "beats": BEATS, "hero": sorted(HERO),
        "host": cfg["host"], "schedule": "MON & WED · 5:30 PM · ALL OCTOBER",
        "finals": cfg["finalsDate"],
    })

    html = TEMPLATE.format(
        faces=inline_fonts(), data=payload, W=W, H=H,
        mark=base64.b64encode(mark.encode()).decode(),
        lime=LIME, magenta=MAGENTA, ink=INK, muted=MUTED, bg=BG,
        host=cfg["host"].upper(),
    )
    with open(OUT, "w") as f:
        f.write(html)
    print(f"built feature.html  {len(html.encode())/1024/1024:.1f}MB  {DUR:.1f}s")
    for s in SCENES:
        if s.get("head"):
            print(f"  {s['t'][0]:5.2f}-{s['t'][1]:5.2f}  {s['head'].replace(chr(10), ' ')}")
    print("\nnow:  python3 build-feature-audio.py && node record-feature-video.mjs")


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
.scene{{position:absolute;inset:0;will-change:opacity,transform}}
.disp{{font-style:italic;font-variation-settings:'wdth' 125,'wght' 900;line-height:.88;
  letter-spacing:-.5px;white-space:pre-line}}
.kick{{font-family:'JetBrains Mono',monospace;font-weight:700;letter-spacing:.3em;color:{lime}}}
.mono{{font-family:'JetBrains Mono',monospace;font-weight:700}}
/* The phone: a frame, not a photo of a phone. Square corners, like the brand. */
/* Centred by translate(-50%) in the seek function, NOT by a margin: both at
   once shifts the phone a full half-width off the frame, which is how this
   first rendered. */
.phone{{position:absolute;left:50%;width:660px;height:1180px;
  border:5px solid rgba(242,242,242,.16);background:#000;overflow:hidden;
  box-shadow:0 0 70px rgba(198,255,0,.16)}}
.phone img{{width:100%;display:block}}
.tag{{position:absolute;left:0;right:0;bottom:0;padding:12px 0;text-align:center;
  background:rgba(5,5,5,.86);font-family:'JetBrains Mono',monospace;font-weight:700;
  font-size:17px;letter-spacing:.2em;color:{muted}}}
.flash{{position:absolute;inset:0;pointer-events:none;background:{lime};
  mix-blend-mode:screen;opacity:0}}
</style></head><body>

<div id="cam">
  <div class="wash"></div><div class="scan" id="scan"></div>
  <div class="rail" id="rail" style="top:0"></div>

  <div class="scene" id="s1">
    <div style="position:absolute;left:50%;top:430px;width:150px;height:150px;margin-left:-75px" id="s1m">
      <img src="data:image/svg+xml;base64,{mark}" style="width:100%;display:block">
    </div>
    <div class="kick" style="position:absolute;left:0;right:0;top:640px;text-align:center;font-size:27px" id="s1k">BLACKOUT SERIES &middot; VOL.8</div>
    <div class="disp" style="position:absolute;left:0;right:0;top:720px;text-align:center;font-size:132px" id="s1t">THE APP
JUST GOT
BETTER.</div>
    <div style="position:absolute;left:50%;top:1180px;width:420px;height:5px;margin-left:-210px;background:{lime}" id="s1r"></div>
    <div class="mono" style="position:absolute;left:0;right:0;top:1250px;text-align:center;font-size:27px;letter-spacing:.22em;color:{muted}" id="s1s"></div>
  </div>

  <div class="scene" id="s2"></div>
  <div class="scene" id="s3"></div>
  <div class="scene" id="s4"></div>
  <div class="scene" id="s5"></div>
  <div class="scene" id="s6"></div>

  <div class="scene" id="s7">
    <div class="disp" style="position:absolute;left:0;right:0;top:600px;text-align:center;font-size:118px" id="s7t">IT'S ALL
IN THERE.</div>
    <div style="position:absolute;left:50%;top:900px;width:520px;height:5px;margin-left:-260px;background:{lime}" id="s7r"></div>
    <div class="disp fit" style="position:absolute;left:0;right:0;top:970px;text-align:center;font-size:62px;color:{lime}" id="s7u">{host}</div>
    <div class="mono" style="position:absolute;left:0;right:0;top:1110px;text-align:center;font-size:26px;letter-spacing:.24em;color:{muted}" id="s7d"></div>
    <div style="position:absolute;left:50%;top:1240px;width:120px;height:120px;margin-left:-60px" id="s7m">
      <img src="data:image/svg+xml;base64,{mark}" style="width:100%;display:block">
    </div>
    <div class="mono" style="position:absolute;left:0;right:0;top:1440px;text-align:center;font-size:24px;letter-spacing:.3em;color:#6E6E6E">URBAN PLAYGROUND &middot; MUSCAT</div>
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
// VARIABLE font -- a static instance accepts 'wdth' and ignores it.
function widen(el,t,t0,d,{{w0=66,w1=125,blur=12}}={{}}){{
  const p=outExpo(inv(t,t0,t0+d)), o=inv(t,t0,t0+d*0.3);
  el.style.fontVariationSettings=`'wdth' ${{(w0+(w1-w0)*p).toFixed(1)}},'wght' 900`;
  set(el,o,`scale(${{(1+0.04*(1-p)).toFixed(4)}})`,`blur(${{(blur*(1-p)).toFixed(2)}}px)`);
}}
// Shrink-to-fit, once the real face is in. document.fonts.status reads "loaded"
// before any face has been requested, so gating on it measures fallback metrics
// and shrinks nothing.
let fitted=false;
function fitOnce(){{
  if(fitted || !document.fonts.check("italic 900 40px Archivo")) return;
  // Every scene has to be laid out to be measured. A scene left display:none by
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

/* Feature scenes are generated from the table, so six screens cannot drift
   apart in spacing, timing or type size. */
D.scenes.filter(s=>s.shot).forEach(s=>{{
  const host=document.getElementById(s.k);
  host.innerHTML=`
    <div class="kick" id="${{s.k}}k" style="position:absolute;left:0;right:0;top:118px;text-align:center;font-size:24px">${{s.kick}}</div>
    <div class="disp" id="${{s.k}}h" style="position:absolute;left:0;right:0;top:176px;text-align:center;font-size:96px">${{s.head}}</div>
    <div id="${{s.k}}n" style="position:absolute;left:0;right:0;top:${{s.head.includes("\n")?400:300}}px;text-align:center;font-size:30px;color:#9A9A9A">${{s.note}}</div>
    <div class="phone" id="${{s.k}}p" style="top:452px">
      <img src="${{D.shots[s.shot]}}" alt="">
      <div class="tag">EXAMPLE &middot; LAST SEASON'S NUMBERS</div>
    </div>`;
}});

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

  for(const s of D.scenes){{
    const [a,b]=s.t;
    const o=Math.min(inv(t,a-XF,a+0.02), 1-inv(t,b,b+XF));
    const el=document.getElementById(s.k);
    el.style.opacity=o.toFixed(3);
    el.style.display=o<=0.002?'none':'block';
  }}

  {{ // title
    const u=t-D.scenes[0].t[0];
    set(document.getElementById('s1m'), inv(u,0.10,0.50),
        `scale(${{(0.86+0.14*outBack(inv(u,0.10,0.80))).toFixed(4)}})`);
    set(document.getElementById('s1k'), inv(u,0.56,0.86),
        `translateY(${{(12*(1-outQuint(inv(u,0.56,1.1)))).toFixed(1)}}px)`);
    widen(document.getElementById('s1t'),u,0.72,0.82);
    const r=document.getElementById('s1r');
    set(r,1,`scaleX(${{outQuint(inv(u,1.40,1.85)).toFixed(3)}})`);
    const sg=document.getElementById('s1s'); sg.textContent=D.schedule;
    set(sg, inv(u,1.72,2.05));
    const rail=document.getElementById('rail');
    rail.style.transform=`scaleX(${{outExpo(inv(t,0.02,0.60)).toFixed(3)}})`;
  }}

  for(const s of D.scenes.filter(x=>x.shot)){{
    const u=t-s.t[0];
    set(document.getElementById(s.k+'k'), inv(u,0.10,0.38),
        `translateY(${{(10*(1-outQuint(inv(u,0.10,0.7)))).toFixed(1)}}px)`);
    widen(document.getElementById(s.k+'h'), u, 0.22, 0.70, {{w0:72,blur:9}});
    set(document.getElementById(s.k+'n'), inv(u,0.58,0.86),
        `translateY(${{(10*(1-outQuint(inv(u,0.58,1.2)))).toFixed(1)}}px)`);
    // the phone rises in, then drifts very slowly so the frame is never static
    const p=outBack(inv(u,0.30,1.05));
    const drift=-14*inv(u,0.9,s.t[1]-s.t[0]);
    set(document.getElementById(s.k+'p'), inv(u,0.30,0.62),
        `translate(-50%,${{(70*(1-p)+drift).toFixed(1)}}px) scale(${{(0.94+0.06*p).toFixed(4)}})`);
  }}

  {{ // outro
    const u=t-D.scenes[D.scenes.length-1].t[0];
    widen(document.getElementById('s7t'),u,0.16,0.76);
    const r=document.getElementById('s7r');
    set(r,1,`scaleX(${{outQuint(inv(u,0.80,1.25)).toFixed(3)}})`);
    widen(document.getElementById('s7u'),u,0.94,0.62,{{w0:80,blur:6}});
    const dd=document.getElementById('s7d'); dd.textContent=D.schedule;
    set(dd, inv(u,1.30,1.60));
    set(document.getElementById('s7m'), inv(u,1.52,1.86),
        `scale(${{(0.9+0.1*outBack(inv(u,1.52,2.2))).toFixed(4)}})`);
  }}
}}
window.__seek=seek; window.__dur=DUR; seek(0);
</script></body></html>"""


if __name__ == "__main__":
    main()
