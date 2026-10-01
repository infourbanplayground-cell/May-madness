# -*- coding: utf-8 -*-
"""September Surge Vol.7 — the winner video, 1080x1920, ~21s.

Self-contained: fonts, emblem and player photos are all inlined, so the page
renders identically on any machine and the recorder never races a network fetch.

Deterministic, not a screen recording. There are NO CSS animations anywhere in
this page -- every moving value is a pure function of t, exposed as
`window.__seek(t)`. The recorder scrubs to an exact time per frame, which is
what keeps the output honest: an earlier story captured with Playwright's own
video ran 3.2x slow and had to be rescued with setpts.

The numbers come from `brand/reports/surge-podium.json`, which is computed with
the app's own scoring engine (see make-winner-data.mjs) -- never typed in.

  node make-winner-data.mjs <state.json>
  python3 build-winner-video.py
  node record-winner-video.mjs
  python3 build-winner-audio.py     # then muxed by the recorder's last step
"""
import base64, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SP = "/tmp/claude-0/-home-user-May-madness/0e44f0ad-a683-5f0d-9de6-9459ae328963/scratchpad"
VID = os.path.join(SP, "video")
DATA = os.path.join(HERE, "brand", "reports", "surge-podium.json")
OUT = os.path.join(SP, "winner.html")

W, H = 1080, 1920

# Scene boundaries in seconds. The champion gets the longest hold by a wide
# margin -- he is the reason anyone is watching.
SC = {
    "s1": [0.00,  3.60],    # title
    "s2": [3.60,  7.40],    # third
    "s3": [7.40, 11.20],    # second
    "s4": [11.20, 17.20],   # champion
    "s5": [17.20, 21.00],   # the margin + outro
}
DUR = 21.00

# Impact times -- the camera kicks and the frame flashes on each. These are the
# same instants the audio lands its hits, so the two stay locked without either
# having to chase the other.
BEATS = [0.14, 1.05, 3.62, 4.30, 7.42, 8.10, 11.22, 12.05, 13.10, 17.22, 18.30]
HERO = {12.05}          # the one that gets the big flash


def b64_file(p):
    with open(p, "rb") as f:
        return base64.b64encode(f.read()).decode()


def inline_fonts():
    """Inline the woff2 payloads into the @font-face blocks.

    The variable axes matter here: the headline entrance animates 'wdth' from
    condensed to full width, and a static instance silently ignores it, which is
    what made an earlier cut's type look 20% too narrow.
    """
    css = open(os.path.join(VID, "fonts", "fonts.css")).read()
    seen = {}

    def sub(m):
        name = m.group(1)
        if name not in seen:
            seen[name] = b64_file(os.path.join(VID, "fonts", name))
        return "url(data:font/woff2;base64,%s) format('woff2')" % seen[name]

    css = re.sub(r"url\(([0-9a-f]+\.woff2)\)\s*format\('woff2'\)", sub, css)
    assert ".woff2)" not in css, "a font file was left as an external reference"
    return css


def photos():
    """Player photos as stored by the app, keyed by player id.

    The export writes a literal backslash-t between the two columns, so this
    splits on that rather than on a real tab.
    """
    out = {}
    p = os.path.join(VID, "winners", "winphotos.tsv")
    if not os.path.exists(p):
        return out
    for line in open(p):
        line = line.rstrip("\n")
        if not line:
            continue
        pid, _, data = line.partition("\\t")
        if data.startswith("data:"):
            out[pid] = data
    return out


def build():
    d = json.load(open(DATA))
    ph = photos()
    pod = d["podium"]
    for p in pod:
        p["photo"] = ph.get(p["id"], "")
    missing = [p["name"] for p in pod if not p["photo"]]
    if missing:
        print("  ! no photo for: " + ", ".join(missing), file=sys.stderr)

    payload = json.dumps({
        "pod": pod, "margin": d["margin"], "sessions": d["sessions"],
        "vol": d["vol"], "volume": d["volume"], "date": d.get("lastDate"),
    })

    return TEMPLATE.format(
        faces=inline_fonts(), logo=open(os.path.join(VID, "logo.txt")).read().strip(),
        data=payload, W=W, H=H,
        sc=json.dumps(SC), dur=DUR,
        beats=json.dumps(BEATS), hero=json.dumps(sorted(HERO)),
    )


TEMPLATE = r"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
{faces}
:root{{
  --void:#050709; --deep:#0A0F14; --cyan:#00E5FF; --white:#F4F9FA;
  --steel:#5C6B78; --steeltx:#8A9BA8; --silver:#C3D0D8; --amber:#FF9E1B;
}}
*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{width:{W}px;height:{H}px;background:#000;overflow:hidden}}
body{{font-family:'Archivo',sans-serif;color:var(--white);
  -webkit-font-smoothing:antialiased;text-rendering:geometricPrecision}}
#cam{{position:absolute;inset:0;transform-origin:50% 50%;
  background:radial-gradient(ellipse 760px 900px at 50% 44%, #121B23 0%, var(--deep) 62%, var(--void) 100%)}}
.scene{{position:absolute;inset:0;will-change:opacity,transform}}
.trace{{position:absolute;inset:-40px;pointer-events:none;
  background:repeating-linear-gradient(to bottom, rgba(0,229,255,.05) 0 1px, transparent 1px 15px)}}
.vig{{position:absolute;inset:0;pointer-events:none;
  background:radial-gradient(ellipse 70% 60% at 50% 45%, transparent 40%, rgba(0,0,0,.72) 100%)}}
.flash{{position:absolute;inset:0;pointer-events:none;background:var(--cyan);
  mix-blend-mode:screen;opacity:0}}
.rail{{position:absolute;left:0;right:0;height:8px;background:var(--cyan)}}

/* ── type ── */
.mono{{font-family:'JetBrains Mono',monospace;font-weight:700}}
.disp{{font-style:italic;font-variation-settings:'wdth' 125,'wght' 900;
  line-height:.92;letter-spacing:-.5px}}
.kick{{font-family:'JetBrains Mono',monospace;font-weight:700;
  letter-spacing:.34em;color:var(--cyan)}}

/* ── podium card ── */
.ghost{{position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);
  font-style:italic;font-variation-settings:'wdth' 125,'wght' 900;
  font-size:900px;line-height:.8;color:var(--cyan);opacity:.075;
  pointer-events:none}}
.portrait{{position:absolute;left:50%;top:454px;width:524px;height:524px;
  margin-left:-262px;border-radius:50%;overflow:hidden;
  border:7px solid var(--cyan);background:#0C141B}}
.portrait img{{width:100%;height:100%;object-fit:cover;display:block}}
.ring{{position:absolute;left:50%;top:454px;width:524px;height:524px;
  margin-left:-262px;border-radius:50%;border:3px solid var(--cyan);
  pointer-events:none}}
.place{{position:absolute;left:0;right:0;top:1052px;text-align:center}}
.nm{{position:absolute;left:0;right:0;top:1118px;text-align:center;
  font-size:118px;white-space:nowrap}}
/* Anything that must stay on one line is measured at full width and shrunk to
   fit -- "MUNTHER RAHBI" at the design size overran the frame by 180px. */
.fit{{white-space:nowrap}}
.pts{{position:absolute;left:0;right:0;top:1272px;text-align:center}}
.pts b{{font-family:'JetBrains Mono',monospace;font-weight:700;font-size:168px;
  color:var(--cyan);line-height:1}}
.pts i{{display:block;font-style:normal;font-family:'JetBrains Mono',monospace;
  font-size:26px;letter-spacing:.3em;color:var(--steeltx);margin-top:6px}}
.strip{{position:absolute;left:96px;right:96px;top:1500px;display:flex;
  justify-content:space-between}}
.strip div{{flex:1;text-align:center}}
.strip b{{display:block;font-family:'JetBrains Mono',monospace;font-weight:700;
  font-size:62px;color:var(--white)}}
.strip span{{display:block;font-family:'JetBrains Mono',monospace;font-size:21px;
  letter-spacing:.24em;color:var(--steel);margin-top:8px}}
.top-logo{{position:absolute;left:50%;top:150px;width:150px;margin-left:-75px}}
.top-logo img{{width:100%;display:block}}
</style></head><body>

<div id="cam">
  <div class="trace" id="trace"></div>

  <!-- ══ S1 title ══ -->
  <div class="scene" id="s1">
    <div class="rail" id="s1rail" style="top:0"></div>
    <div style="position:absolute;left:50%;top:430px;width:224px;margin-left:-112px" id="s1logo">
      <img src="{logo}" style="width:100%;display:block">
    </div>
    <div class="kick" style="position:absolute;left:0;right:0;top:800px;text-align:center;font-size:30px" id="s1v"></div>
    <div class="disp fit" style="position:absolute;left:0;right:0;top:856px;text-align:center;font-size:150px" data-fitgroup="title" id="s1t">SEPTEMBER</div>
    <div class="disp fit" style="position:absolute;left:0;right:0;top:1000px;text-align:center;font-size:150px" data-fitgroup="title" id="s1t2">SURGE</div>
    <div style="position:absolute;left:50%;top:1192px;width:420px;height:4px;margin-left:-210px;background:var(--cyan)" id="s1r"></div>
    <div class="disp fit" style="position:absolute;left:0;right:0;top:1248px;text-align:center;font-size:86px" id="s1s">FINAL STANDINGS</div>
    <div class="mono" style="position:absolute;left:0;right:0;top:1398px;text-align:center;font-size:26px;letter-spacing:.28em;color:var(--steeltx)" id="s1d"></div>
  </div>

  <!-- ══ S2/S3/S4 podium cards ══ -->
  <div class="scene" id="s2"></div>
  <div class="scene" id="s3"></div>
  <div class="scene" id="s4"></div>

  <!-- ══ S5 the margin ══ -->
  <div class="scene" id="s5">
    <div class="kick" style="position:absolute;left:0;right:0;top:600px;text-align:center;font-size:29px" id="s5k">DECIDED BY</div>
    <div class="disp" style="position:absolute;left:0;right:0;top:664px;text-align:center;font-size:300px;color:var(--cyan)" id="s5n"></div>
    <div class="disp" style="position:absolute;left:0;right:0;top:980px;text-align:center;font-size:104px" id="s5w"></div>
    <div class="mono" style="position:absolute;left:0;right:0;top:1150px;text-align:center;font-size:46px;color:var(--steeltx)" id="s5m"></div>
    <div style="position:absolute;left:50%;top:1300px;width:380px;height:3px;margin-left:-190px;background:var(--cyan)" id="s5r"></div>
    <div style="position:absolute;left:50%;top:1374px;width:160px;margin-left:-80px" id="s5logo">
      <img src="{logo}" style="width:100%;display:block">
    </div>
    <div class="mono" style="position:absolute;left:0;right:0;top:1600px;text-align:center;font-size:25px;letter-spacing:.32em;color:var(--steel)" id="s5f">URBAN PLAYGROUND &middot; MUSCAT</div>
  </div>

  <div class="vig"></div>
</div>
<div class="flash" id="flash"></div>

<script>
const D = {data};
const SCN = {sc}, DUR = {dur};
const BEATS = {beats}, HERO = new Set({hero});
const XF = 0.14;                      // near-cut, reads as an edit not a dissolve

const clamp=(v,a=0,b=1)=>Math.max(a,Math.min(b,v));
const inv=(t,a,b)=>clamp((t-a)/(b-a));
const outCubic=x=>1-Math.pow(1-x,3);
const outQuint=x=>1-Math.pow(1-x,5);
const outExpo =x=>x>=1?1:1-Math.pow(2,-10*x);
const outBack =x=>{{const c1=2.2,c3=c1+1;return 1+c3*Math.pow(x-1,3)+c1*Math.pow(x-1,2);}};

function set(el,o,tr,fl){{
  el.style.opacity=o.toFixed(3);
  if(tr!==undefined) el.style.transform=tr;
  if(fl!==undefined) el.style.filter=fl;
}}
// The Vol.7 signature entrance: type arrives condensed and widens to full.
// Needs a VARIABLE font -- a static instance ignores 'wdth' without complaining.
function widen(el,t,t0,d,{{w0=64,w1=125,blur=11}}={{}}){{
  const p=outExpo(inv(t,t0,t0+d)), o=inv(t,t0,t0+d*0.3);
  el.style.fontVariationSettings=`'wdth' ${{(w0+(w1-w0)*p).toFixed(1)}},'wght' 900`;
  set(el,o,`scale(${{(1+0.05*(1-p)).toFixed(4)}})`,`blur(${{(blur*(1-p)).toFixed(2)}}px)`);
  return p;
}}
const countTo=(t,t0,d,to)=>Math.round(to*outExpo(inv(t,t0,t0+d)));
/* Split the stored YYYY-MM-DD by hand rather than via Date(): the server runs
   UTC+4, and parsing then formatting walks the date back a day. */
const MONTHS=['JANUARY','FEBRUARY','MARCH','APRIL','MAY','JUNE','JULY',
  'AUGUST','SEPTEMBER','OCTOBER','NOVEMBER','DECEMBER'];
function fmtDate(s){{
  const m=/^(\d{{4}})-(\d{{2}})-(\d{{2}})$/.exec(s||'');
  return m ? `${{+m[3]}} ${{MONTHS[+m[2]-1]}} ${{m[1]}}` : (s||'').toUpperCase();
}}

/* Impact energy: a fast attack and a short decay, summed over every beat. This
   one function drives the camera kick, the flash and the rail jitter, so they
   cannot drift apart. */
function energy(t){{
  let e=0, h=0;
  for(const b of BEATS){{
    if(t<b-0.02||t>b+0.5) continue;
    const u=(t-b)/0.5, v=Math.max(0,Math.pow(1-u,3));
    e=Math.max(e,v); if(HERO.has(b)) h=Math.max(h,v);
  }}
  return [e,h];
}}
function shake(t,e){{
  if(e<=0.001) return [0,0];
  return [Math.sin(t*118)*7.5*e, Math.cos(t*97)*5.5*e];
}}
function sceneState(t,[a,b]){{
  return Math.min(inv(t,a-XF,a+0.02), 1-inv(t,b,b+XF));
}}

/* ── podium cards are generated, so the three stay identical in everything but
   their content; a hand-built trio drifts ── */
const LABEL=['CHAMPION','RUNNER-UP','THIRD PLACE'];
const NUM=['1','2','3'];
D.pod.forEach((p,i)=>{{
  const host=document.getElementById(['s4','s3','s2'][i]);
  host.innerHTML=`
    <div class="ghost" id="g${{i}}">${{NUM[i]}}</div>
    <div class="top-logo" id="tl${{i}}"><img src="${{D.logoSrc||''}}"></div>
    <div class="portrait" id="po${{i}}">${{p.photo?`<img src="${{p.photo}}">`:''}}</div>
    <div class="ring" id="ri${{i}}"></div>
    <div class="place kick" id="pl${{i}}" style="font-size:${{i===0?34:29}}px">${{LABEL[i]}}</div>
    <div class="nm disp" data-fitgroup="name" id="nm${{i}}" style="font-size:${{i===0?132:112}}px">${{p.name.toUpperCase()}}</div>
    <div class="pts" id="pt${{i}}"><b id="pn${{i}}">0</b><i>SERIES POINTS</i></div>
    <div class="strip" id="sp${{i}}">
      <div><b id="a${{i}}">0</b><span>NIGHTS</span></div>
      <div><b id="b${{i}}">0</b><span>WINS</span></div>
      <div><b id="c${{i}}">0</b><span>TITLES</span></div>
    </div>`;
  host.querySelector('.top-logo').remove();
}});

function card(i,u,host){{
  const p=D.pod[i];
  // ghost numeral drifts up and fades in behind everything
  set(document.getElementById('g'+i), 0.075*inv(u,0.05,0.9),
      `translate(-50%,calc(-50% + ${{(26*(1-outCubic(inv(u,0.05,1.1)))).toFixed(1)}}px))`);
  // portrait punches in
  const pp=outBack(inv(u,0.10,0.62));
  set(document.getElementById('po'+i), inv(u,0.10,0.34),
      `translateY(${{(26*(1-pp)).toFixed(1)}}px) scale(${{(0.86+0.14*pp).toFixed(4)}})`);
  // a ring leaves the portrait on arrival -- the only "effect" on the card
  const rq=inv(u,0.30,1.25);
  set(document.getElementById('ri'+i), rq>0&&rq<1?((1-rq)*0.5):0,
      `scale(${{(1+0.42*outCubic(rq)).toFixed(3)}})`);
  set(document.getElementById('pl'+i), inv(u,0.44,0.70),
      `translateY(${{(16*(1-outQuint(inv(u,0.44,0.86)))).toFixed(1)}}px)`);
  widen(document.getElementById('nm'+i), u, 0.56, 0.78);
  const pq=inv(u,0.80,1.00);
  set(document.getElementById('pt'+i), pq, `scale(${{(0.94+0.06*outBack(inv(u,0.80,1.20))).toFixed(4)}})`);
  document.getElementById('pn'+i).textContent = countTo(u,0.84,0.95,p.pts);
  const sq=inv(u,1.18,1.40);
  set(document.getElementById('sp'+i), sq,
      `translateY(${{(18*(1-outQuint(inv(u,1.18,1.70)))).toFixed(1)}}px)`);
  document.getElementById('a'+i).textContent=countTo(u,1.22,0.5,p.nights);
  document.getElementById('b'+i).textContent=countTo(u,1.30,0.6,p.wins);
  document.getElementById('c'+i).textContent=countTo(u,1.38,0.5,p.titles);
}}

/* Shrink-to-fit, once, after the fonts are in.
   Measured at the WIDEST the entrance ever reaches ('wdth' 125) -- measuring the
   condensed start passes a name that then overruns the frame as it widens. */
const FIT_MAX = {W} - 112;
let fitted = false;
function fitOnce(){{
  // NOT document.fonts.status: it reads 'loaded' before any face has even been
  // requested, so the first fit ran against fallback metrics, measured narrow,
  // and shrank nothing. check() is false until the real face is in.
  if (fitted || !document.fonts.check("italic 900 40px Archivo")) return;
  // Every scene has to be laid out to be measured. Scenes not on screen are
  // display:none, and a hidden element measures 0 wide -- which reads as "it
  // fits" and ships the names overrunning the frame.
  const hidden = [...document.querySelectorAll('.scene')].map(s => [s, s.style.display]);
  hidden.forEach(([s]) => {{ s.style.display = 'block'; }});
  for (const el of document.querySelectorAll('.fit, .nm')) {{
    // The text is wrapped in an inline span and THAT is measured: these blocks
    // are full-bleed (left:0;right:0), so the element's own width is the frame's
    // and tells you nothing about whether the words fit inside it.
    if (!el.firstElementChild || !el.firstElementChild.classList.contains('fitspan')) {{
      el.innerHTML = `<span class="fitspan" style="display:inline-block">${{el.textContent}}</span>`;
    }}
    const span = el.firstElementChild;
    const base = parseFloat(getComputedStyle(el).fontSize);
    const keep = el.style.fontVariationSettings;
    el.style.fontVariationSettings = "'wdth' 125,'wght' 900";
    const w = span.getBoundingClientRect().width;
    el.style.fontVariationSettings = keep;
    if (w > FIT_MAX) el.style.fontSize = (base * FIT_MAX / w).toFixed(2) + 'px';
  }}
  // Elements that belong together are then levelled to the smallest of the
  // group. Fitting each one independently left SEPTEMBER at 112px above SURGE
  // at 150px, and the three names at three different sizes -- correct widths,
  // but it stops reading as one set.
  const groups = {{}};
  for (const el of document.querySelectorAll('[data-fitgroup]')) {{
    const g = el.dataset.fitgroup;
    groups[g] = Math.min(groups[g] ?? Infinity, parseFloat(getComputedStyle(el).fontSize));
  }}
  for (const el of document.querySelectorAll('[data-fitgroup]')) {{
    el.style.fontSize = groups[el.dataset.fitgroup].toFixed(2) + 'px';
  }}
  hidden.forEach(([s, d]) => {{ s.style.display = d; }});
  fitted = true;
  document.body.dataset.fitted = '1';
}}

function seek(t){{
  fitOnce();
  const [e,h]=energy(t), [sx,sy]=shake(t,e);
  document.getElementById('cam').style.transform =
    `translate(${{sx.toFixed(2)}}px,${{sy.toFixed(2)}}px) scale(${{(1+e*0.013).toFixed(4)}})`;
  document.getElementById('flash').style.opacity=(e*0.055+h*0.12).toFixed(3);
  const tr=document.getElementById('trace');
  tr.style.transform=`translateY(${{(t*3.4)%15}}px) scaleY(${{(1+e*0.04).toFixed(3)}})`;
  tr.style.opacity=(0.85+e*1.5).toFixed(3);

  for(const k of Object.keys(SCN)){{
    const o=sceneState(t,SCN[k]), el=document.getElementById(k);
    el.style.opacity=o.toFixed(3);
    el.style.display=o<=0.002?'none':'block';
  }}

  /* S1 title */
  {{
    const u=t-SCN.s1[0];
    set(document.getElementById('s1logo'), inv(u,0.10,0.52),
        `scale(${{(0.9+0.1*outBack(inv(u,0.10,0.78))).toFixed(4)}})`);
    const v=document.getElementById('s1v');
    v.textContent=`${{D.vol}} · ${{D.sessions}} NIGHTS`;
    set(v, inv(u,0.62,0.90), `translateY(${{(12*(1-outQuint(inv(u,0.62,1.1)))).toFixed(1)}}px)`);
    widen(document.getElementById('s1t'), u, 0.74, 0.80);
    widen(document.getElementById('s1t2'), u, 0.90, 0.80);
    const r=document.getElementById('s1r');
    set(r,1,`scaleX(${{outQuint(inv(u,1.42,1.86)).toFixed(3)}})`);
    widen(document.getElementById('s1s'),u,1.54,0.70,{{w0:72}});
    const dd=document.getElementById('s1d');
    dd.textContent=fmtDate(D.date)+'  ·  URBAN PLAYGROUND';
    set(dd, inv(u,1.98,2.32));
    document.getElementById('s1rail').style.transform=
      `scaleX(${{outExpo(inv(u,0.02,0.60)).toFixed(3)}})`;
    document.getElementById('s1rail').style.transformOrigin='0 50%';
  }}

  card(2, t-SCN.s2[0]);
  card(1, t-SCN.s3[0]);
  card(0, t-SCN.s4[0]);

  /* S5 the margin */
  {{
    const u=t-SCN.s5[0];
    set(document.getElementById('s5k'), inv(u,0.12,0.42));
    const n=document.getElementById('s5n');
    n.textContent=String(D.margin);
    widen(n,u,0.30,0.74,{{w0:70,blur:16}});
    const w=document.getElementById('s5w');
    w.textContent=D.margin===1?'POINT':'POINTS';
    widen(w,u,0.62,0.62,{{w0:78,blur:8}});
    const m=document.getElementById('s5m');
    m.textContent=`${{D.pod[0].pts}}  –  ${{D.pod[1].pts}}`;
    set(m, inv(u,0.92,1.22), `translateY(${{(14*(1-outQuint(inv(u,0.92,1.5)))).toFixed(1)}}px)`);
    set(document.getElementById('s5r'),1,`scaleX(${{outQuint(inv(u,1.28,1.72)).toFixed(3)}})`);
    set(document.getElementById('s5logo'), inv(u,1.46,1.82),
        `scale(${{(0.92+0.08*outBack(inv(u,1.46,2.1))).toFixed(4)}})`);
    set(document.getElementById('s5f'), inv(u,1.80,2.20));
  }}
}}

window.__seek=seek;
window.__dur=DUR;
seek(0);
</script></body></html>"""


def main():
    html = build()
    with open(OUT, "w") as f:
        f.write(html)
    mb = len(html.encode()) / 1024 / 1024
    d = json.load(open(DATA))
    print(f"built winner.html  {mb:.1f}MB  {DUR:.1f}s")
    for i, p in enumerate(d["podium"], 1):
        print(f"  {i}. {p['name']:<20} {p['pts']} pts")
    print(f"  margin {d['margin']}")
    print("\nnow render:  node record-winner-video.mjs")


if __name__ == "__main__":
    main()
