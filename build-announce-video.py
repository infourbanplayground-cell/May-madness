# -*- coding: utf-8 -*-
"""Blackout Series Vol.8 — the announcement film. 1080x1920, ~28s.

An announcement, not a teaser: by the end a player knows the nights, the money,
the entry fee, the two rule changes and where to sign up. Nothing is withheld
for effect.

EVERY NUMBER IS DERIVED, none typed. The nights, the entry, the voucher, the
season prizes and the pool all come out of blackout-season.json, and the pool is
computed from its parts the same way the app computes it — so the film cannot
advertise a figure the app contradicts. The Vol.7 champion and his margin come
out of archive/september-surge/final-standings.json rather than memory.

Deterministic, like every film in this repo: no CSS animations anywhere, every
moving value a pure function of t behind window.__seek(t).

  python3 build-announce-video.py
  python3 build-announce-audio.py
  node record-announce-video.mjs
"""
import base64, datetime, json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
SP = "/tmp/claude-0/-home-user-May-madness/0e44f0ad-a683-5f0d-9de6-9459ae328963/scratchpad"
VID = os.path.join(SP, "video")
OUT = os.path.join(SP, "announce.html")

W, H = 1080, 1920
LIME, MAGENTA, INK, MUTED, BG = "#C6FF00", "#FF2E88", "#F2F2F2", "#9A9A9A", "#050505"

# Scene table — shared verbatim with build-announce-audio.py, so the hits land
# on the cuts rather than near them.
SCENES = [0.00, 4.00, 8.20, 13.40, 18.20, 21.60, 24.40]
DUR = 28.20
BEATS = [0.14, 1.05, 4.02, 8.22, 13.42, 15.10, 18.22, 21.62, 24.42, 25.70]
HERO = [13.42, 24.42]


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


DAYS = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]


def main():
    cfg = json.load(open(os.path.join(HERE, "blackout-season.json")))
    std = json.load(open(os.path.join(HERE, "archive", "september-surge",
                                      "final-standings.json")))

    pool = cfg["voucher"] * 2 * cfg["sessions"] + sum(cfg["seasonPrizes"])
    champ, runner = std["podium"][0], std["podium"][1]
    margin = champ["pts"] - runner["pts"]

    nights = [datetime.date.fromisoformat(d) for d in cfg["nights"]]
    finals = datetime.date.fromisoformat(cfg["finalsDate"])
    assert len(nights) == cfg["sessions"], "the schedule and the session count disagree"

    chips = "".join(
        f'<div class="chip{" fin" if d == finals else ""}" id="c{i}">'
        f'<span class="cd">{DAYS[d.weekday()]}</span>'
        f'<span class="cn">{d.day}</span></div>'
        for i, d in enumerate(nights))

    payload = json.dumps({
        "scenes": SCENES, "dur": DUR, "beats": BEATS, "hero": HERO,
        "n": len(nights), "pool": pool,
    })

    mark = open(os.path.join(HERE, "brand", "blackout", "blackout-mark.svg")).read()
    html = TEMPLATE.format(
        faces=inline_fonts(), data=payload, W=W, H=H,
        mark=base64.b64encode(mark.encode()).decode(),
        lime=LIME, magenta=MAGENTA, ink=INK, muted=MUTED, bg=BG,
        chips=chips,
        host=cfg["host"].upper(),
        month=cfg["monthUpper"],
        prev=std["volume"],
        champ=champ["name"].upper(), champpts=champ["pts"],
        margin=f"BY {margin} POINT." if margin == 1 else f"BY {margin} POINTS.",
        sessions=cfg["sessions"],
        voucher=cfg["voucher"], entry=cfg["entry"], pool=pool,
        prizes=" / ".join(str(p) for p in cfg["seasonPrizes"]),
        dbl=cfg["doubleFromSession"],
        first=f"{DAYS[nights[0].weekday()]} {nights[0].day} {cfg['monthUpper'][:3]}",
        finalsday=f"{DAYS[finals.weekday()]} {finals.day} {cfg['monthUpper'][:3]}",
    )
    with open(OUT, "w") as f:
        f.write(html)

    print(f"built announce.html  {len(html.encode())/1024/1024:.1f}MB  {DUR:.1f}s")
    print(f"  pool      {pool} OMR  ({cfg['voucher']} x 2 x {cfg['sessions']} + {sum(cfg['seasonPrizes'])})")
    print(f"  nights    {len(nights)}, {nights[0]} .. {nights[-1]}  (finals {finals})")
    print(f"  handover  {std['volume']} — {champ['name']} {champ['pts']}, by {margin}")
    print("\nnow:  python3 build-announce-audio.py && node record-announce-video.mjs")


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
/* Every scene's content is laid out between roughly y=400 and y=1300, which
   centres on 850 in a 1920 frame — top-heavy, with a dead bottom third. The
   whole layer drops 100px rather than every `top` being re-typed one by one.
   seek() only ever sets opacity and display on .scene, so a transform here is
   safe. */
.scene{{position:absolute;inset:0;transform:translateY(100px);
  will-change:opacity,transform}}
.disp{{font-style:italic;font-variation-settings:'wdth' 125,'wght' 900;line-height:.88;
  letter-spacing:-.5px;white-space:pre-line}}
.kick{{font-family:'JetBrains Mono',monospace;font-weight:700;letter-spacing:.3em;color:{lime}}}
.mono{{font-family:'JetBrains Mono',monospace;font-weight:700}}
.ctr{{position:absolute;left:0;right:0;text-align:center}}
/* Square corners everywhere — Blackout has no radius. */
.chip{{width:150px;height:150px;border:3px solid rgba(242,242,242,.16);
  background:rgba(255,255,255,.03);display:flex;flex-direction:column;
  align-items:center;justify-content:center;will-change:transform,opacity}}
.chip .cd{{font-family:'JetBrains Mono',monospace;font-weight:700;font-size:20px;
  letter-spacing:.2em;color:{muted}}}
.chip .cn{{font-style:italic;font-variation-settings:'wdth' 125,'wght' 900;
  font-size:66px;line-height:1;margin-top:6px}}
.chip.fin{{border-color:{lime};background:rgba(198,255,0,.12)}}
.chip.fin .cn{{color:{lime}}}
.chip.fin .cd{{color:{lime}}}
.row{{display:flex;align-items:baseline;justify-content:center;gap:18px}}
.flash{{position:absolute;inset:0;pointer-events:none;background:{lime};
  mix-blend-mode:screen;opacity:0}}
</style></head><body>

<div id="cam">
  <div class="wash"></div><div class="scan" id="scan"></div>
  <div class="rail" id="rail" style="top:0"></div>

  <!-- 1 · title -->
  <div class="scene" id="s1">
    <div style="position:absolute;left:50%;top:400px;width:168px;height:168px;margin-left:-84px" id="s1m">
      <img src="data:image/svg+xml;base64,{mark}" style="width:100%;display:block">
    </div>
    <div class="kick ctr" style="top:640px;font-size:26px" id="s1k">URBAN SOCIAL SERIES &middot; VOL.8</div>
    <div class="disp ctr fit" style="top:714px;font-size:186px" id="s1t">BLACKOUT</div>
    <div class="disp ctr" style="top:930px;font-size:92px;color:{lime}" id="s1g">LIGHTS OUT.</div>
    <div style="position:absolute;left:50%;top:1092px;width:440px;height:5px;margin-left:-220px;background:{lime}" id="s1r"></div>
    <div class="mono ctr" style="top:1160px;font-size:30px;letter-spacing:.24em;color:{muted}" id="s1s">ALL {month} &middot; MUSCAT</div>
  </div>

  <!-- 2 · the volume that just finished -->
  <div class="scene" id="s2">
    <div class="kick ctr" style="top:470px;font-size:24px" id="s2k">VOL.7 &middot; DONE</div>
    <div class="disp ctr" style="top:528px;font-size:104px" id="s2t">{prev}</div>
    <div style="position:absolute;left:120px;right:120px;top:760px;height:3px;background:rgba(242,242,242,.14)" id="s2r"></div>
    <div class="mono ctr" style="top:812px;font-size:24px;letter-spacing:.26em;color:{muted}" id="s2c">CHAMPION</div>
    <div class="disp ctr fit" style="top:866px;font-size:112px;color:{lime}" id="s2n">{champ}</div>
    <div class="ctr" id="s2p" style="top:1020px">
      <span class="disp" style="font-size:110px">{champpts}</span>
      <span class="mono" style="font-size:30px;letter-spacing:.2em;color:{muted}">&nbsp;PTS</span>
    </div>
    <div class="disp ctr" style="top:1180px;font-size:58px;color:{magenta}" id="s2m">{margin}</div>
  </div>

  <!-- 3 · the schedule -->
  <div class="scene" id="s3">
    <div class="kick ctr" style="top:400px;font-size:24px" id="s3k">THE SCHEDULE</div>
    <div class="disp ctr" style="top:452px;font-size:150px" id="s3t">{sessions} NIGHTS</div>
    <div id="s3g" style="position:absolute;left:135px;top:700px;width:810px;
         display:flex;flex-wrap:wrap;gap:20px;justify-content:center">{chips}</div>
    <div class="mono ctr" style="top:1270px;font-size:30px;letter-spacing:.2em;color:{muted}" id="s3s">MON &amp; WED &middot; 5:30 PM</div>
    <div class="mono ctr" style="top:1330px;font-size:30px;letter-spacing:.2em;color:{lime}" id="s3f">FINALS NIGHT &middot; {finalsday}</div>
  </div>

  <!-- 4 · the money -->
  <div class="scene" id="s4">
    <div class="kick ctr" style="top:420px;font-size:24px" id="s4k">ON THE TABLE</div>
    <div class="ctr" id="s4b" style="top:480px">
      <span class="disp" style="font-size:240px;color:{lime}" id="s4n">0</span>
      <span class="disp" style="font-size:92px;color:{lime}">OMR</span>
    </div>
    <div style="position:absolute;left:150px;right:150px;top:800px;height:3px;background:rgba(242,242,242,.14)" id="s4r"></div>
    <div class="ctr" style="top:862px;font-size:40px" id="s4a">
      <b style="color:{lime}">{voucher} OMR</b> to each winner, every night</div>
    <div class="ctr" style="top:946px;font-size:40px" id="s4c">
      Season top 3 &middot; <b style="color:{lime}">{prizes} OMR</b></div>
    <div class="disp ctr" style="top:1080px;font-size:70px" id="s4d">DOUBLE POINTS
FROM NIGHT {dbl}.</div>
  </div>

  <!-- 5 · what changed -->
  <div class="scene" id="s5">
    <div class="kick ctr" style="top:560px;font-size:24px" id="s5k">NEW THIS VOLUME</div>
    <div class="disp ctr" style="top:620px;font-size:122px" id="s5t">NO FINALS
CUT.</div>
    <div class="ctr" style="top:900px;font-size:40px;color:{muted}" id="s5n">Night {sessions} is open to everyone.</div>
    <div style="position:absolute;left:50%;top:1010px;width:360px;height:5px;margin-left:-180px;background:{magenta}" id="s5r"></div>
    <div class="ctr" style="top:1080px;font-size:40px" id="s5s">Season top three on points take it.</div>
  </div>

  <!-- 6 · entry -->
  <div class="scene" id="s6">
    <div class="kick ctr" style="top:700px;font-size:24px" id="s6k">TO PLAY</div>
    <div class="disp ctr" style="top:756px;font-size:200px;color:{lime}" id="s6t">{entry} OMR</div>
    <div class="mono ctr" style="top:1000px;font-size:32px;letter-spacing:.24em;color:{muted}" id="s6s">A NIGHT</div>
  </div>

  <!-- 7 · where -->
  <div class="scene" id="s7">
    <div class="disp ctr" style="top:520px;font-size:120px" id="s7t">SIGN UP
NOW.</div>
    <div style="position:absolute;left:50%;top:800px;width:520px;height:5px;margin-left:-260px;background:{lime}" id="s7r"></div>
    <div class="disp ctr fit" style="top:866px;font-size:62px;color:{lime}" id="s7u">{host}</div>
    <div class="mono ctr" style="top:1010px;font-size:28px;letter-spacing:.22em;color:{muted}" id="s7d">FIRST NIGHT &middot; {first} &middot; 5:30 PM</div>
    <div style="position:absolute;left:50%;top:1150px;width:130px;height:130px;margin-left:-65px" id="s7m">
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
// VARIABLE font — a static instance accepts 'wdth' and nothing moves.
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

  {{ // 2 · the volume that just finished
    const u=t-S[1];
    rise(g('s2k'), u, 0.08, 0.40, 10);
    widen(g('s2t'), u, 0.18, 0.66, {{w0:74,blur:9}});
    set(g('s2r'), 1, `scaleX(${{outQuint(inv(u,0.60,1.00)).toFixed(3)}})`);
    set(g('s2c'), inv(u,0.80,1.02));
    widen(g('s2n'), u, 0.94, 0.62, {{w0:80,blur:7}});
    // the champion's total counts up — it is the one number of his the film shows
    const p=outExpo(inv(u,1.30,1.95));
    set(g('s2p'), inv(u,1.30,1.50), `scale(${{(0.96+0.04*p).toFixed(4)}})`);
    g('s2p').firstElementChild.textContent=Math.round({champpts}*p);
    widen(g('s2m'), u, 2.20, 0.58, {{w0:84,blur:6}});
  }}

  {{ // 3 · the schedule
    const u=t-S[2];
    rise(g('s3k'), u, 0.08, 0.40, 10);
    widen(g('s3t'), u, 0.18, 0.66, {{w0:72,blur:9}});
    // the nights land one after another, the finals night last and lit
    for(let i=0;i<D.n;i++){{
      const c=g('c'+i), a=0.62+i*0.115;
      const p=outBack(inv(u,a,a+0.42));
      set(c, inv(u,a,a+0.16),
          `translateY(${{(26*(1-p)).toFixed(1)}}px) scale(${{(0.86+0.14*p).toFixed(4)}})`);
    }}
    set(g('s3s'), inv(u,1.95,2.20));
    set(g('s3f'), inv(u,2.20,2.45));
  }}

  {{ // 4 · the money
    const u=t-S[3];
    rise(g('s4k'), u, 0.08, 0.40, 10);
    // the pool counts up: the number IS the news, so it arrives as an event
    const p=outExpo(inv(u,0.22,1.35));
    set(g('s4b'), inv(u,0.22,0.42), `scale(${{(0.94+0.06*p).toFixed(4)}})`);
    g('s4n').textContent=Math.round(D.pool*p);
    set(g('s4r'), 1, `scaleX(${{outQuint(inv(u,1.35,1.75)).toFixed(3)}})`);
    rise(g('s4a'), u, 1.52, 0.46, 14);
    rise(g('s4c'), u, 1.74, 0.46, 14);
    widen(g('s4d'), u, 2.16, 0.66, {{w0:76,blur:8}});
  }}

  {{ // 5 · what changed
    const u=t-S[4];
    rise(g('s5k'), u, 0.08, 0.40, 10);
    widen(g('s5t'), u, 0.18, 0.70, {{w0:70,blur:10}});
    rise(g('s5n'), u, 0.86, 0.46, 14);
    set(g('s5r'), 1, `scaleX(${{outQuint(inv(u,1.10,1.50)).toFixed(3)}})`);
    rise(g('s5s'), u, 1.38, 0.46, 14);
  }}

  {{ // 6 · entry
    const u=t-S[5];
    rise(g('s6k'), u, 0.06, 0.36, 10);
    widen(g('s6t'), u, 0.16, 0.70, {{w0:68,blur:11}});
    set(g('s6s'), inv(u,0.86,1.10));
  }}

  {{ // 7 · where
    const u=t-S[6];
    widen(g('s7t'), u, 0.16, 0.76);
    set(g('s7r'), 1, `scaleX(${{outQuint(inv(u,0.80,1.25)).toFixed(3)}})`);
    widen(g('s7u'), u, 0.94, 0.62, {{w0:80,blur:6}});
    set(g('s7d'), inv(u,1.30,1.60));
    set(g('s7m'), inv(u,1.52,1.86), `scale(${{(0.9+0.1*outBack(inv(u,1.52,2.2))).toFixed(4)}})`);
  }}
}}
window.__seek=seek; window.__dur=DUR; seek(0);
</script></body></html>"""


if __name__ == "__main__":
    main()
