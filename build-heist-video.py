# -*- coding: utf-8 -*-
"""Muscat Heist (Vol.10) — the 18-second LAUNCH film, 1080x1920.

A heist film's trailer, in the posts' voice and not the app's (owner, 26 Nov
2026: "it shouldn't look childish"): the owner's own paintings full-bleed,
condensed Archivo caps tracking in like a title card, credits in mono, and the
logo as the one piece of play. Five scenes, cut on one beat table that the
score reads too (written to $SP/heist-launch.cut.json):

   0.0  the open       the logo over the clubhouse, VOL.10 · DECEMBER
   3.5  the crew       NINE NIGHTS — one painting per episode, cut on the beat,
                       each with its own code and title
   8.0  the job        THE LAST TWO PAY DOUBLE — EP.08 and EP.09 with their dates
  11.0  the take       412 OMR counting up, and what it is made of
  14.5  the ask        WED 2 DEC · bring a partner · the link

EVERY FIGURE COMES FROM heist-season.json and the pool is DERIVED (season
prizes + voucher x 2 x nights), the same expression the app build and the posts
use. It REFUSES to build once night one has been played, if the double nights
are not the last two (scene 3 says "the last two"), or if the pool and the
posts disagree. It never says what a doubled night is worth in points.

Deterministic: no CSS animations; every moving value is a pure function of t
behind window.__seek(t). Backgrounds live in #stage, OUTSIDE the scenes, so
their Ken Burns transform can never be read as text overflowing its box.

  python3 build-heist-video.py
  python3.13 build-heist-audio.py
  node record-heist-video.mjs            # CONTACT=1 for a strip, no encode
"""
import base64
import datetime
import html
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "ops"))
from font_bundle import bundle  # noqa: E402

SP = ("/tmp/claude-0/-home-user-May-madness/"
      "0e44f0ad-a683-5f0d-9de6-9459ae328963/scratchpad")
OUT = os.path.join(SP, "heist-launch.html")
CUT = os.path.join(SP, "heist-launch.cut.json")
CAPS = os.path.join(HERE, "brand", "heist", "posts", "VIDEO-CAPTIONS.txt")
ART = os.path.join(HERE, "brand", "heist", "art")

W, H = 1080, 1920
DUR = 18.0
BPM = 120.0
SPB = 60.0 / BPM
SCENES = [0.0, 3.5, 8.0, 11.0, 14.5]
HERO = [0.0, 3.5, 8.0, 11.0, 14.5]
BEATS = [round(k * SPB, 3) for k in range(int(DUR / SPB))]
MONTAGE = [round(3.5 + k * SPB, 3) for k in range(9)]   # one painting a beat
WORDS = ["ZERO", "ONE", "TWO", "THREE", "FOUR", "FIVE", "SIX", "SEVEN",
         "EIGHT", "NINE", "TEN"]


def durl(path, mime):
    return f"data:{mime};base64," + base64.b64encode(open(path, "rb").read()).decode()


def art(name):
    p = os.path.join(ART, name[:-4] + "-1200.webp")
    return durl(p, "image/webp") if os.path.exists(p) else durl(os.path.join(ART, name), "image/jpeg")


def main():
    S = json.load(open(os.path.join(HERE, "heist-season.json"), encoding="utf-8"))
    nights = [datetime.date.fromisoformat(x) for x in S["nights"]]
    dbl = S["doubleNights"]
    ep = S["episodes"]
    today = datetime.date.today()

    # ── the guards ──────────────────────────────────────────────────────────
    if today >= nights[0] and not os.environ.get("ANYDAY"):
        raise SystemExit(f"night one ({nights[0]}) has been played — this is a launch film")
    assert len(nights) == len(ep) == S["sessions"], "nights, episodes and sessions disagree"
    assert sorted(dbl) == S["nights"][-2:], \
        "scene 3 says THE LAST TWO PAY DOUBLE, but doubleNights is not the last two nights"
    pool = sum(S["seasonPrizes"]) + S["voucher"] * 2 * len(nights)
    assert pool == 412, f"pool derived as {pool}; the posts assert 412 — find out which part moved"

    hh, mm = map(int, S["time"].split(":"))
    clock = datetime.time(hh, mm).strftime("%-I:%M %p")
    order = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    days = " & ".join(sorted({d.strftime("%a") for d in nights}, key=order.index)).upper()
    first = nights[0].strftime("%a %-d %b").upper()
    n_word = WORDS[len(nights)]

    logo = durl(os.path.join(HERE, "brand", "heist", "heist-logo.webp"), "image/webp")
    # The scene paintings are CHOSEN, not cycled: several carry their own
    # lettering (the clubhouse poster's URBAN PLAYGROUND PADEL CLUB, the
    # walkout's banner), and a title over a title reads as neither. These four
    # keep clear sky where each scene's type sits. The montage uses all nine.
    pick = lambda k: (art(ep[k]["art"]), ep[k].get("artPos", "center"))
    plates = [("p0",) + pick(1) + (0,)]
    plates += [(f"m{k}", art(e["art"]), e.get("artPos", "center"), 1) for k, e in enumerate(ep)]
    plates += [("p2",) + pick(3) + (2,), ("p3",) + pick(6) + (3,), ("p4",) + pick(7) + (4,)]
    stage = "".join(
        f'<div class="plate" id="{i}" data-scene="{s}" style="background-image:url({u});'
        f'background-position:{pos}"></div>' for i, u, pos, s in plates)

    e8, e9 = ep[-2], ep[-1]
    d8, d9 = nights[-2].strftime("%a %-d %b").upper(), nights[-1].strftime("%a %-d %b").upper()
    eps_js = json.dumps([[e["code"], e["title"].upper(),
                          nights[k].strftime("%a %-d %b").upper(), S["nights"][k] in dbl]
                         for k, e in enumerate(ep)])
    prizes = " / ".join(str(x) for x in S["seasonPrizes"])
    esc = html.escape

    style = f"""
{bundle()}
:root{{--navy:#0F1B2B;--ink:#07040D;--sand:#F6EAD3;--peach:#FFB36B;--pink:#FF2D78;
  --gold:#FFC24A;--mist:#D8DEE8;--line:rgba(246,234,211,.28)}}
*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{width:{W}px;height:{H}px;overflow:hidden;background:var(--navy);color:var(--sand);
  font-family:'Archivo',sans-serif;-webkit-font-smoothing:antialiased}}
#stage{{position:absolute;inset:0;overflow:hidden;z-index:0}}
.plate{{position:absolute;inset:0;background-size:cover;opacity:0;
  filter:saturate(1.22) contrast(1.06);will-change:transform,opacity}}
/* The scrim belongs to the PICTURE, under the type: dark at the top where the
   kicker sits and heavy from mid-frame down where the copy lives. */
#scrim{{position:absolute;inset:0;z-index:1;pointer-events:none;
  background:linear-gradient(180deg,rgba(7,4,13,.80) 0,rgba(7,4,13,.52) 24%,rgba(7,4,13,.42) 46%,
  rgba(7,4,13,.86) 70%,rgba(7,4,13,.94) 100%)}}
#wash{{position:absolute;inset:0;z-index:1;pointer-events:none;opacity:0;
  background:radial-gradient(120% 70% at 50% 40%,rgba(255,45,120,.0),rgba(255,45,120,.30))}}
#flash{{position:absolute;inset:0;z-index:1;background:#FFF6E6;opacity:0;pointer-events:none}}
.bar{{position:absolute;left:0;right:0;height:0;background:var(--ink);z-index:6}}
#bt{{top:0}} #bb{{bottom:0}}
#grain{{position:absolute;inset:-40px;z-index:5;opacity:.10;mix-blend-mode:overlay;pointer-events:none;
  background-image:url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='180' height='180'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='.9' numOctaves='2' stitchTiles='stitch'/></filter><rect width='180' height='180' filter='url(%23n)'/></svg>")}}
.scene{{position:absolute;inset:0;z-index:3;display:none}}
.blk{{position:absolute;left:72px;right:72px}}
.c{{text-align:center}}
.mono{{font-family:'JetBrains Mono',monospace;font-weight:500;text-transform:uppercase;letter-spacing:.18em}}
.h{{font-weight:800;font-stretch:112%;text-transform:uppercase;line-height:.92;color:var(--sand);
  text-shadow:0 2px 0 rgba(7,4,13,.35),0 0 40px rgba(7,4,13,.45)}}
.h em{{font-style:normal;color:var(--pink)}}
.fitspan{{display:inline-block;white-space:nowrap}}
.kick{{font-size:26px;color:var(--peach);text-shadow:0 1px 3px rgba(7,4,13,.9)}}
.cred{{font-size:28px;color:var(--mist);line-height:1.7}}
.cred b{{color:var(--sand);font-weight:700}}
.logo{{display:block;margin:0 auto;height:auto}}
.rule{{height:2px;background:var(--line)}}

/* 1 · the open */
#s1logo{{top:620px}} #s1logo img{{width:760px}}
#s1k{{top:500px;font-size:26px}}
#s1c{{top:1240px;font-size:30px}}
/* 2 · the crew */
#s2k{{top:300px}}
#s2b{{top:360px;font-size:200px}}
#s2ep{{top:1330px}}
#s2code{{font-size:30px;color:var(--peach)}}
#s2title{{font-size:96px;margin-top:14px}}
#s2date{{font-size:28px;color:var(--mist);margin-top:18px}}
#s2c{{top:1600px;font-size:26px;color:var(--sand)}}
/* 3 · the job */
#s3k{{top:300px}}
#s3b{{top:360px;font-size:150px;line-height:1.02}}
#s3rows{{top:1060px}}
.job{{display:flex;align-items:center;gap:28px;padding:30px 0;border-top:2px solid var(--line)}}
.job:last-child{{border-bottom:2px solid var(--line)}}
.job .x{{flex:none;width:132px;height:132px;display:flex;align-items:center;justify-content:center;
  background:var(--pink);color:var(--ink);font-weight:800;font-stretch:112%;font-size:64px}}
.job .w{{min-width:0}}
.job .cd{{font-size:24px;color:var(--peach)}}
.job .t{{font-weight:800;font-stretch:112%;font-size:62px;line-height:1;text-transform:uppercase;margin:8px 0;white-space:nowrap}}
.job .d{{font-size:24px;color:var(--mist)}}
/* 4 · the take */
#s4k{{top:350px}}
#s4n{{top:490px;font-size:400px;line-height:.86;letter-spacing:-.03em;color:var(--sand)}}
#s4u{{top:910px;font-size:40px;color:var(--peach)}}
#s4rows{{top:1110px}}
.mr{{display:flex;justify-content:space-between;align-items:baseline;gap:24px;padding:24px 0;border-top:2px solid var(--line)}}
.mr:last-child{{border-bottom:2px solid var(--line)}}
.mr .k{{font-size:24px;color:var(--mist);white-space:nowrap}}
.mr .v{{font-weight:800;font-stretch:112%;font-size:58px;white-space:nowrap;color:var(--sand)}}
.mr .v small{{font-size:28px;color:var(--peach);margin-left:8px}}
/* 5 · the ask */
#s5logo{{top:250px}} #s5logo img{{width:520px}}
#s5k{{top:680px}}
#s5b{{top:740px;font-size:210px}}
#s5c{{top:1010px;font-size:30px;color:var(--peach)}}
#s5d{{top:1220px;font-size:96px}}
#s5e{{top:1420px;font-size:28px}}
#s5f{{top:1590px;font-size:34px;color:var(--sand);letter-spacing:.12em}}
"""

    body = f"""
<div id="stage">{stage}</div>
<div id="scrim"></div><div id="wash"></div><div id="flash"></div>

<div class="scene" id="sc1">
  <div class="blk c mono kick" id="s1k">Urban Social Series · {esc(S['volumeLabel'])}</div>
  <div class="blk" id="s1logo"><img class="logo" src="{logo}" alt="Urban Playground Muscat Heist"></div>
  <div class="blk c mono cred" id="s1c"><b>{esc(S['month'].upper())} {S['year']}</b> · Muscat</div>
</div>

<div class="scene" id="sc2">
  <div class="blk c mono kick" id="s2k">The crew assembles</div>
  <div class="blk c h" id="s2b"><span class="fitspan">{n_word} NIGHTS</span></div>
  <div class="blk c" id="s2ep">
    <div class="mono" id="s2code">{esc(ep[0]['code'])}</div>
    <div class="h" id="s2title"><span class="fitspan" id="s2tt">{esc(ep[0]['title'].upper())}</span></div>
    <div class="mono" id="s2date">{first}</div>
  </div>
  <div class="blk c mono" id="s2c">{days} · {clock} · {esc(S['venue'])}</div>
</div>

<div class="scene" id="sc3">
  <div class="blk c mono kick" id="s3k">The job</div>
  <div class="blk c h" id="s3b"><span class="fitspan">THE LAST TWO</span><br><span class="fitspan"><em>PAY DOUBLE</em></span></div>
  <div class="blk" id="s3rows">
    <div class="job"><div class="x">2X</div><div class="w"><div class="mono cd">{esc(e8['code'])} · {d8}</div><div class="t">{esc(e8['title'])}</div><div class="mono d">Double points</div></div></div>
    <div class="job"><div class="x">2X</div><div class="w"><div class="mono cd">{esc(e9['code'])} · {d9}</div><div class="t">{esc(e9['title'])}</div><div class="mono d">The finale · double points</div></div></div>
  </div>
</div>

<div class="scene" id="sc4">
  <div class="blk c mono kick" id="s4k">The take</div>
  <div class="blk c h" id="s4n" data-n="{pool}">{pool}</div>
  <div class="blk c mono" id="s4u">OMR on the table</div>
  <div class="blk" id="s4rows">
    <div class="mr"><div class="mono k">Every night's champions</div><div class="v">{S['voucher']}<small>OMR EACH</small></div></div>
    <div class="mr"><div class="mono k">Season top three</div><div class="v">{prizes}</div></div>
    <div class="mr"><div class="mono k">A night to play</div><div class="v">{S['entry']}<small>OMR</small></div></div>
  </div>
</div>

<div class="scene" id="sc5">
  <div class="blk" id="s5logo"><img class="logo" src="{logo}" alt="Urban Playground Muscat Heist"></div>
  <div class="blk c mono kick" id="s5k">Night one · {esc(ep[0]['title'])}</div>
  <div class="blk c h" id="s5b"><span class="fitspan">{first}</span></div>
  <div class="blk c mono" id="s5c">{clock} · {esc(S['venue'])}</div>
  <div class="blk c h" id="s5d"><span class="fitspan">BRING A <em>PARTNER.</em></span></div>
  <div class="blk c mono cred" id="s5e">Name + partner in the group</div>
  <div class="blk c mono" id="s5f">{esc(S['host'])}</div>
</div>
<div class="bar" id="bt"></div><div class="bar" id="bb"></div><div id="grain"></div>
"""

    js = """
<script>
const DUR = %(dur)s, SCENES = %(scenes)s, BEATS = %(beats)s, HERO = %(hero)s, MONT = %(mont)s, EPS = %(eps)s, POOL = %(pool)s;
window.__dur = DUR; window.__scenes = SCENES;
const E = id => document.getElementById(id);
const clamp = (x,a,b) => x < a ? a : x > b ? b : x;
const TRACK = 0.06;   // the widest a title card opens; the fit measures at it
const ease = u => 1 - Math.pow(1 - clamp(u,0,1), 3);
const inout = u => { u = clamp(u,0,1); return u < .5 ? 4*u*u*u : 1 - Math.pow(-2*u+2,3)/2; };
// A title card TRACKS IN: the letters arrive wide and close up while it fades
// and rises. Letter-spacing is applied to the span, so the Range box the
// recorder measures is the real width at every instant.
function enter(el, u, rise, track) {
  const e = ease(u);
  el.style.opacity = clamp(u * 1.6, 0, 1).toFixed(3);
  el.style.transform = 'translateY(' + ((1 - e) * (rise === undefined ? 30 : rise)).toFixed(2) + 'px)';
  if (track) for (const s of el.querySelectorAll('.fitspan')) s.style.letterSpacing = ((1 - e) * TRACK).toFixed(4) + 'em';
}
function energy(t) {
  let e = 0;
  for (const b of BEATS) {
    const u = (t - (b - 0.02)) / 0.28;
    if (u >= 0 && u <= 1) e = Math.max(e, Math.pow(1 - u, 3) * (HERO.includes(b) ? 1 : 0.4));
  }
  return clamp(e, 0, 1);
}
// SHRINK-TO-FIT once the face is in, with every scene shown while it measures:
// a hidden box measures 0, and a headline fitted against nothing runs to the floor.
function fitAll() {
  const sc = [...document.querySelectorAll('.scene')];
  sc.forEach(el => el.style.display = 'block');
  for (const s of document.querySelectorAll('.fitspan')) {
    const box = s.closest('.blk'), room = box.clientWidth;
    let px = parseFloat(getComputedStyle(s.parentElement).fontSize);
    if (room <= 0) throw new Error('fit: ' + box.id + ' has no width');
    const tgt = s.parentElement;
    // the montage title is refitted for the LONGEST episode title, so the
    // block never changes size between cuts
    const texts = s.id === 's2tt' ? EPS.map(x => x[1]) : [s.textContent];
    const keep = s.textContent;
    // fitted at its WIDEST: a tracked title is wider while it closes up, and a
    // fit taken at rest lets the entrance run the letters off the frame
    if (s.id !== 's2tt') s.style.letterSpacing = TRACK + 'em';
    for (const tx of texts) { s.textContent = tx;
      while (s.getBoundingClientRect().width > room && px > 10) { px -= 2; tgt.style.fontSize = px + 'px'; } }
    s.textContent = keep; s.style.letterSpacing = '';
    if (px <= 10) throw new Error('fit: ' + box.id + ' hit the floor');
  }
  sc.forEach(el => el.style.display = 'none');
}
function sceneAt(t) { let i = 0; for (let k = 0; k < SCENES.length; k++) if (t >= SCENES[k]) i = k; return i; }
const plates = [...document.querySelectorAll('.plate')];

window.__seek = function (t) {
  t = clamp(t, 0, DUR);
  const i = sceneAt(t), t0 = SCENES[i], t1 = i + 1 < SCENES.length ? SCENES[i + 1] : DUR;
  const S = t - t0, e = energy(t);
  document.querySelectorAll('.scene').forEach((el, k) => el.style.display = k === i ? 'block' : 'none');

  // the picture: one plate up at a time, pushing in slowly, directions alternating
  let m = -1;
  if (i === 1) for (let k = 0; k < MONT.length; k++) if (t >= MONT[k]) m = k;
  plates.forEach((p, k) => {
    const sc = +p.dataset.scene;
    let on = sc === i && (i !== 1 || p.id === 'm' + m);
    p.style.opacity = on ? '1' : '0';
    if (!on) return;
    const start = i === 1 ? MONT[m] : t0, len = i === 1 ? 0.5 : t1 - t0;
    const u = clamp((t - start) / len, 0, 1), dir = (k %% 2) ? 1 : -1;
    const z = (i === 1 ? 1.10 : 1.06) + (i === 1 ? 0.05 : 0.10) * u + 0.012 * e;
    p.style.transform = 'scale(' + z.toFixed(4) + ') translateX(' + (dir * 18 * u).toFixed(2) + 'px)';
  });

  // a cut is a hit: two frames of light under the letterbox, and the bars punch in
  const cutAge = Math.min(...[...SCENES, ...MONT].map(c => t >= c ? t - c : 99));
  E('flash').style.opacity = (cutAge < 0.067 ? 0.32 * (1 - cutAge / 0.067) : 0).toFixed(3);
  const bar = (i === 0 ? 120 * (1 - ease(S / 1.2)) : 0) + 26 * e;
  E('bt').style.height = E('bb').style.height = bar.toFixed(1) + 'px';
  E('wash').style.opacity = (i === 2 ? 0.45 + 0.30 * e : 0).toFixed(3);
  E('grain').style.transform = 'translate(' + ((t * 137) %% 40 - 20).toFixed(1) + 'px,' + ((t * 91) %% 40 - 20).toFixed(1) + 'px)';

  if (i === 0) {
    enter(E('s1k'), (S - 0.35) / 0.7, 14);
    const u = ease((S - 0.10) / 1.1);
    E('s1logo').style.opacity = clamp(((S - 0.10) / 1.1) * 1.4, 0, 1).toFixed(3);
    E('s1logo').style.transform = 'scale(' + (1.12 - 0.12 * u + 0.02 * e).toFixed(4) + ')';
    enter(E('s1c'), (S - 1.10) / 0.7, 16);
  } else if (i === 1) {
    enter(E('s2k'), S / 0.5, 14);
    enter(E('s2b'), (S - 0.05) / 0.6, 36, true);
    const x = EPS[Math.max(0, m)];
    E('s2code').textContent = x[0] + (x[3] ? ' · 2X' : '');
    E('s2tt').textContent = x[1];
    E('s2date').textContent = x[2];
    const mu = (t - MONT[Math.max(0, m)]) / 0.22;
    E('s2ep').style.opacity = clamp(mu * 1.8, 0, 1).toFixed(3);
    E('s2ep').style.transform = 'translateY(' + ((1 - ease(mu)) * 18).toFixed(2) + 'px)';
    enter(E('s2c'), (S - 0.40) / 0.6, 14);
  } else if (i === 2) {
    enter(E('s3k'), S / 0.5, 14);
    enter(E('s3b'), (S - 0.05) / 0.7, 36, true);
    document.querySelectorAll('#s3rows .job').forEach((el, k) => {
      const u = (S - 0.70 - k * 0.45) / 0.5;
      el.style.opacity = clamp(u * 1.7, 0, 1).toFixed(3);
      el.style.transform = 'translateX(' + ((1 - ease(u)) * -40).toFixed(2) + 'px)';
      el.querySelector('.x').style.transform = 'scale(' + (1 + 0.10 * e).toFixed(4) + ')';
    });
  } else if (i === 3) {
    enter(E('s4k'), S / 0.5, 14);
    E('s4n').style.opacity = clamp(S / 0.3, 0, 1).toFixed(3);
    E('s4n').textContent = Math.round(POOL * inout((S - 0.05) / 1.4));
    E('s4n').style.transform = 'scale(' + (1 + 0.025 * e).toFixed(4) + ')';
    enter(E('s4u'), (S - 0.9) / 0.5, 14);
    document.querySelectorAll('#s4rows .mr').forEach((el, k) => {
      const u = (S - 1.30 - k * 0.30) / 0.45;
      el.style.opacity = clamp(u * 1.7, 0, 1).toFixed(3);
      el.style.transform = 'translateY(' + ((1 - ease(u)) * 22).toFixed(2) + 'px)';
    });
  } else {
    const lu = ease(S / 0.9);
    E('s5logo').style.opacity = clamp(S / 0.6, 0, 1).toFixed(3);
    E('s5logo').style.transform = 'scale(' + (1.08 - 0.08 * lu + 0.015 * e).toFixed(4) + ')';
    enter(E('s5k'), (S - 0.30) / 0.5, 14);
    enter(E('s5b'), (S - 0.40) / 0.7, 36, true);
    enter(E('s5c'), (S - 0.80) / 0.5, 14);
    enter(E('s5d'), (S - 1.30) / 0.6, 30, true);
    enter(E('s5e'), (S - 1.70) / 0.5, 14);
    enter(E('s5f'), (S - 1.95) / 0.5, 14);
  }
};
// A face is only fetched once text is laid out in it, and every scene but the
// first is display:none — so fonts.ready resolves before the wide cut has even
// been asked for, and the fit measures the fallback. Lay every scene out first,
// and load every bundled face outright (they are data URLs) before fitting.
document.querySelectorAll('.scene').forEach(el => el.style.display = 'block');
Promise.all([...document.fonts].map(f => f.load().catch(() => 0))).then(() => document.fonts.ready).then(() => { fitAll(); window.__seek(0); window.__ready = true; });
window.__seek(0);
</script>
""" % {"dur": DUR, "scenes": json.dumps(SCENES), "beats": json.dumps(BEATS),
       "hero": json.dumps(HERO), "mont": json.dumps(MONTAGE), "eps": eps_js, "pool": pool}

    page = ("<!doctype html><html lang='en'><head><meta charset='utf-8'><title>Muscat Heist — launch film</title>"
            "<style>" + style + "</style></head><body>" + body + js + "</body></html>")
    os.makedirs(SP, exist_ok=True)
    open(OUT, "w", encoding="utf-8").write(page)
    json.dump({"dur": DUR, "bpm": BPM, "scenes": SCENES, "beats": BEATS, "hero": HERO,
               "montage": MONTAGE, "wav": os.path.join(SP, "video", "heist-launch.wav")},
              open(CUT, "w"))

    cap = f"""{S['name']} — launch film
{'=' * 54}
1080x1920 · {DUR:.0f}s · {S['host']}
Built from heist-season.json; every figure is read, none typed.

— WHATSAPP —

*{S['name'].upper()}* · {S['volumeLabel']} · {S['month']} {S['year']}

{n_word.capitalize()} nights, every {days.title().replace(' & ', ' & ')} at {clock}, {S['venue']}. Night one is {nights[0].strftime('%a %-d %b')}: {ep[0]['title']}.

{pool} OMR on the table: {S['voucher']} OMR vouchers to each of every night's champions, and {prizes} OMR for the season's top three. The last two nights, {ep[-2]['title']} and {ep[-1]['title']}, pay double points.

{S['entry']} OMR a night. Bring a partner: name + partner in the group.
https://{S['host']}

— INSTAGRAM —

The crew assembles. {S['name']} — {S['volumeLabel'].title()} of the Urban Social Series — opens {nights[0].strftime('%a %-d %b')} at {S['venue']}. {n_word.capitalize()} nights, {pool} OMR, and the last two pay double.

Link in bio.

#urbanplayground #padel #oman #muscat #muscatheist
"""
    os.makedirs(os.path.dirname(CAPS), exist_ok=True)
    open(CAPS, "w", encoding="utf-8").write(cap)
    print(f"built {OUT}  {len(page)/1024:.0f}KB  {DUR:.0f}s  {len(SCENES)} scenes, {len(MONTAGE)} montage cuts")
    print(f"  pool {pool} OMR (derived) · night one {first} · doubles {', '.join(dbl)}")
    print(f"  cut table {CUT}\n  captions {os.path.relpath(CAPS, HERE)}")


if __name__ == "__main__":
    main()
