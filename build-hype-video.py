# -*- coding: utf-8 -*-
"""Blackout Vol.8 — the 18-second FINAL WEEK hype cut, led by photographs.

Different film from build-finalweek-video.py, not a trim of it. That one is a
35-second argument: a race chart, a form read, an explanation. This is a hook —
four beats, the club's own faces under them, and the dates. Anybody who wants
the detail has the longer cut and the app.

PHOTOS. The session photos come off `/session-photos` already wearing a
Blackout frame, a footer bar and a URL — one of them still says
attack.urbanpadel.om. Used as-is they would be a frame inside a frame with two
different URLs on screen, so ops/crop-session-photos.sh strips the border and
the footer and fills 1080x1920 before anything here sees them.

Every figure still comes from ops/blackout-standings.mjs, which runs the app's
own engine over the live state. Pictures changed; the discipline did not.

Deterministic: no CSS animations, every moving value a function of t behind
window.__seek(t), so a frame can be scrubbed rather than grabbed off a clock.

  python3 build-hype-audio.py
  python3 build-hype-video.py
  node record-hype-video.mjs
"""
import base64, datetime, glob, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SP = "/tmp/claude-0/-home-user-May-madness/0e44f0ad-a683-5f0d-9de6-9459ae328963/scratchpad"
VID = os.path.join(SP, "video")
PHOTOS = os.path.join(SP, "bocrop")
STD = os.path.join(SP, "bo-standings.json")
OUT = os.path.join(SP, "hype.html")

W, H = 1080, 1920
LIME, MAGENTA, INK, MUTED, BG = "#C6FF00", "#FF2E88", "#F2F2F2", "#9A9A9A", "#050505"

# Shared verbatim with build-hype-audio.py so the cuts land on the hits.
SCENES = [0.00, 4.20, 8.60, 12.40]
DUR = 18.00
BEATS = [0.10, 4.22, 8.62, 10.50, 12.42, 14.30, 16.10]
HERO = [8.62, 12.42]
# The picture changes on a hit, not between them. That is the whole difference
# between a slideshow and a cut.
CUTS = [0.00, 2.20, 4.22, 6.40, 8.62, 10.50, 12.42, 14.30, 16.10]

MONS = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN",
        "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
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

    pics = sorted(glob.glob(os.path.join(PHOTOS, "*.jpg")))
    if len(pics) < len(CUTS):
        sys.exit(f"{len(pics)} cropped photos for {len(CUTS)} cuts — "
                 "run ops/crop-session-photos.sh")
    assert d["remaining"], "no nights left — this is not a final-week film"
    assert d["doubleNights"], "no doubled nights left; scene 3 would be a lie"

    frames = "".join(
        f'<div class="ph" id="ph{i}"><img src="data:image/jpeg;base64,{b64(pics[i])}"></div>'
        for i in range(len(CUTS)))

    rows = "".join(
        f'<div class="std{" ld" if i == 0 else ""}" id="t{i}">'
        f'<span class="pos">{i+1}</span><span class="who">{r["name"].upper()}</span>'
        f'<span class="amt">{r["pts"]}</span></div>'
        for i, r in enumerate(d["table"][:4]))

    dates = " · ".join(short(x) for x in d["remaining"])
    dbl = " & ".join(short(x) for x in d["doubleNights"])

    payload = json.dumps({
        "scenes": SCENES, "dur": DUR, "beats": BEATS, "hero": HERO,
        "cuts": CUTS, "n": len(CUTS), "rows": 4, "gap": d["gap14"],
    })

    html = TEMPLATE.format(
        faces=inline_fonts(), data=payload, W=W, H=H,
        lime=LIME, magenta=MAGENTA, ink=INK, muted=MUTED, bg=BG,
        frames=frames, rows=rows,
        left=len(d["remaining"]), dates=dates, dbl=dbl, gap=d["gap14"],
        host=cfg["host"].upper(),
    )
    with open(OUT, "w") as f:
        f.write(html)
    print(f"built hype.html  {len(html.encode())/1024/1024:.1f}MB  {DUR:.1f}s  "
          f"{len(CUTS)} cuts over {len(pics)} photos")
    print(f"  {d['played']}/{d['sessionsTotal']} nights · {dates} left · {dbl} double")
    print(f"  top four within {d['gap14']} points")
    print("\nnow:  node record-hype-video.mjs")


TEMPLATE = r"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
{faces}
*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{width:{W}px;height:{H}px;background:{bg};overflow:hidden}}
body{{font-family:'Archivo',sans-serif;color:{ink};-webkit-font-smoothing:antialiased}}
#cam{{position:absolute;inset:0;overflow:hidden;background:{bg}}}
/* Photographs sit UNDER everything, one visible at a time, each one slowly
   pushing in. A still that does not move reads as a slideshow. */
.ph{{position:absolute;inset:0;overflow:hidden;opacity:0;will-change:opacity}}
.ph img{{position:absolute;left:50%;top:50%;width:1080px;height:1920px;
  object-fit:cover;transform-origin:50% 50%;will-change:transform}}
/* The scrim is what makes type survive a photograph. Heavier at the foot,
   where the copy lives, and never flat — a flat 50% wash kills the picture. */
.scrim{{position:absolute;inset:0;pointer-events:none;
  background:linear-gradient(180deg,rgba(5,5,5,.80) 0%,rgba(5,5,5,.26) 22%,
    rgba(5,5,5,.22) 40%,rgba(5,5,5,.72) 54%,rgba(5,5,5,.93) 66%,
    rgba(5,5,5,.97) 80%,rgba(5,5,5,.99) 100%)}}
.grade{{position:absolute;inset:0;pointer-events:none;mix-blend-mode:multiply;
  background:radial-gradient(ellipse 80% 60% at 50% 45%,rgba(198,255,0,.00),rgba(5,5,5,.55))}}
.rail{{position:absolute;left:0;right:0;height:10px;background:{lime};transform-origin:0 50%;z-index:9}}
.scene{{position:absolute;inset:0;will-change:opacity;z-index:5}}
.disp{{font-style:italic;font-variation-settings:'wdth' 125,'wght' 900;line-height:.88;
  letter-spacing:-.5px;white-space:pre-line;text-shadow:0 6px 34px rgba(0,0,0,.75)}}
.kick{{font-family:'JetBrains Mono',monospace;font-weight:700;letter-spacing:.3em;color:{lime};
  text-shadow:0 2px 16px rgba(0,0,0,.85)}}
.mono{{font-family:'JetBrains Mono',monospace;font-weight:700}}
.ctr{{position:absolute;left:0;right:0;text-align:center}}
/* Square, like everything else in this volume. */
.plate{{position:absolute;left:52px;right:52px;background:rgba(5,5,5,.56);
  border-top:3px solid rgba(198,255,0,.55);border-bottom:3px solid rgba(198,255,0,.18)}}
.fit{{white-space:nowrap}}
.std{{display:flex;align-items:center;gap:20px;padding:13px 0;
  border-bottom:3px solid rgba(242,242,242,.16);will-change:transform,opacity}}
.std .pos{{font-family:'JetBrains Mono',monospace;font-weight:700;font-size:26px;
  color:{muted};width:42px}}
.std .who{{flex:1;min-width:0;font-style:italic;
  font-variation-settings:'wdth' 104,'wght' 900;font-size:46px;white-space:nowrap;
  text-shadow:0 3px 18px rgba(0,0,0,.8)}}
.std .amt{{font-style:italic;font-variation-settings:'wdth' 110,'wght' 900;
  font-size:58px;text-shadow:0 3px 18px rgba(0,0,0,.8)}}
.std.ld .who,.std.ld .amt{{color:{lime}}}
.flash{{position:absolute;inset:0;pointer-events:none;background:{lime};
  mix-blend-mode:screen;opacity:0;z-index:8}}
.mag{{position:absolute;inset:0;pointer-events:none;background:{magenta};
  mix-blend-mode:overlay;opacity:0;z-index:4}}
</style></head><body>

<div id="cam">
  {frames}
  <div class="scrim"></div>
  <div class="grade"></div>
  <div class="mag" id="mag"></div>
  <div class="rail" id="rail" style="top:0"></div>

  <!-- 1 · the hook -->
  <div class="scene" id="s1">
    <div class="kick ctr" style="top:1210px;font-size:26px" id="s1k">BLACKOUT SERIES &middot; VOL.8</div>
    <div class="disp ctr fit" style="top:1272px;font-size:190px" id="s1t">FINAL WEEK</div>
    <div class="disp ctr" style="top:1468px;font-size:78px;color:{lime}" id="s1g">{left} NIGHTS LEFT.</div>
  </div>

  <!-- 2 · how close it is -->
  <div class="scene" id="s2">
    <div class="plate" id="s2p" style="top:1032px;height:492px"></div>
    <div class="kick ctr" style="top:1054px;font-size:24px" id="s2k">SIX NIGHTS IN</div>
    <div id="s2g" style="position:absolute;left:84px;right:84px;top:1110px">{rows}</div>
    <div class="ctr" style="top:1530px;font-size:38px;color:{ink}" id="s2n">
      <b style="color:{lime}">{gap} points</b> cover the top four.</div>
  </div>

  <!-- 3 · the multiplier -->
  <div class="scene" id="s3">
    <div class="kick ctr" style="top:1140px;font-size:26px;color:{magenta}" id="s3k">{dbl}</div>
    <div class="ctr" id="s3b" style="top:1196px">
      <span class="disp" style="font-size:264px;color:{magenta}" id="s3x">2X</span>
    </div>
    <div class="disp ctr" style="top:1486px;font-size:86px" id="s3t">DOUBLE POINTS.</div>
  </div>

  <!-- 4 · the dates -->
  <div class="scene" id="s4">
    <div class="disp ctr" style="top:1180px;font-size:112px" id="s4t">SEE IT OUT.</div>
    <div style="position:absolute;left:50%;top:1330px;width:460px;height:5px;margin-left:-230px;background:{lime}" id="s4r"></div>
    <div class="mono ctr fit" style="top:1382px;font-size:36px;letter-spacing:.14em;color:{lime}" id="s4d">{dates}</div>
    <div class="disp ctr fit" style="top:1462px;font-size:52px;color:{lime}" id="s4u">{host}</div>
    <div class="mono ctr" style="top:1552px;font-size:24px;letter-spacing:.3em;color:{muted}" id="s4e">URBAN PLAYGROUND &middot; MUSCAT</div>
  </div>
</div>
<div class="flash" id="flash"></div>

<script>
const D = {data};
const DUR = D.dur, XF = 0.14;
const clamp=(v,a=0,b=1)=>Math.max(a,Math.min(b,v));
const inv=(t,a,b)=>clamp((t-a)/(b-a));
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

// Which photograph is up, and how far through its own slow push it is. The
// pushes alternate direction so consecutive cuts do not all drift the same
// way, which reads as a camera rather than as a filter.
const ENDS=[...D.cuts.slice(1), DUR];
function photos(t){{
  for(let i=0;i<D.n;i++){{
    const a=D.cuts[i], b=ENDS[i];
    const el=document.getElementById('ph'+i);
    // a hard cut in, a short dissolve out, so the hit lands on a new picture
    const o=Math.min(inv(t,a-0.02,a+0.04), 1-inv(t,b-0.10,b+0.02));
    el.style.opacity=o.toFixed(3);
    el.style.display=o<=0.002?'none':'block';
    if(o<=0.002) continue;
    const p=inv(t,a,b), dir=i%2?-1:1;
    const s=1.06+0.07*p, x=dir*(-18+36*p), y=(i%3?1:-1)*(10-20*p);
    el.firstElementChild.style.transform=
      `translate(calc(-50% + ${{x.toFixed(1)}}px), calc(-50% + ${{y.toFixed(1)}}px)) scale(${{s.toFixed(4)}})`;
  }}
}}

const S=D.scenes, END=[...S.slice(1), DUR];
function seek(t){{
  fitOnce();
  photos(t);
  const [e,h]=energy(t);
  document.getElementById('flash').style.opacity=(e*0.05+h*0.10).toFixed(3);
  // The magenta wash belongs to the 2X beat and nothing else — it is the one
  // colour in this palette that means "this scores".
  document.getElementById('mag').style.opacity=
    (0.26*Math.min(inv(t,S[2],S[2]+0.5), 1-inv(t,END[2]-0.4,END[2]))).toFixed(3);
  document.getElementById('rail').style.transform=
    `scaleX(${{outExpo(inv(t,0.02,0.55)).toFixed(3)}})`;

  for(let i=0;i<S.length;i++){{
    const o=Math.min(inv(t,S[i]-XF,S[i]+0.02), 1-inv(t,END[i],END[i]+XF));
    const el=document.getElementById('s'+(i+1));
    el.style.opacity=o.toFixed(3);
    el.style.display=o<=0.002?'none':'block';
  }}
  const g=(i)=>document.getElementById(i);

  {{ const u=t-S[0];
    rise(g('s1k'), u, 0.18, 0.46, 12);
    widen(g('s1t'), u, 0.34, 0.80);
    widen(g('s1g'), u, 1.10, 0.60, {{w0:86,blur:7}});
  }}
  {{ const u=t-S[1];
    set(g('s2p'), inv(u,0.02,0.26));
    rise(g('s2k'), u, 0.10, 0.36, 10);
    for(let i=0;i<D.rows;i++){{
      const a=0.26+i*0.22, q=outBack(inv(u,a,a+0.42));
      set(g('t'+i), inv(u,a,a+0.16), `translateX(${{(-30*(1-q)).toFixed(1)}}px)`);
    }}
    rise(g('s2n'), u, 1.42, 0.44, 14);
  }}
  {{ const u=t-S[2];
    rise(g('s3k'), u, 0.04, 0.30, 10);
    const q=outBack(inv(u,0.10,0.62));
    set(g('s3b'), inv(u,0.10,0.24),
        `scale(${{(1.30-0.30*q).toFixed(4)}})`, `blur(${{(12*(1-outExpo(inv(u,0.10,0.52)))).toFixed(2)}}px)`);
    widen(g('s3t'), u, 0.72, 0.60, {{w0:74,blur:8}});
  }}
  {{ const u=t-S[3];
    widen(g('s4t'), u, 0.12, 0.70);
    set(g('s4r'), 1, `scaleX(${{outQuint(inv(u,0.62,1.02)).toFixed(3)}})`);
    set(g('s4d'), inv(u,0.86,1.12));
    widen(g('s4u'), u, 1.14, 0.56, {{w0:80,blur:6}});
    set(g('s4e'), inv(u,1.62,1.92));
  }}
}}
window.__seek=seek; window.__dur=DUR; window.__outro=S[3]; seek(0);
</script></body></html>"""


if __name__ == "__main__":
    main()
