# -*- coding: utf-8 -*-
"""UPRISING — the EXPLAINER film. 1080x1920, ~34s.

A different film from `build-uprising-video.py`, not a re-cut of it. That one is
the night before: it sells tomorrow's place and teaches one rule on the way past.
This one has a single job — somebody who has never played the format watches it
and knows how the night works.

WHY A FILM AND NOT THE INFOGRAPHIC. The infographic can state the rule; it
cannot show it. The whole format is one movement — you win and you go UP a
court — and a poster has to describe that in words while a film just moves the
player. Scene 5 is the reason this exists: a chip climbs from Court 3 to Court 1
across three rounds while a second one drops, and that is the format.

EVERY FORMAT NUMBER IS READ OUT OF THE ENGINE, via ops/uprising-facts.mjs —
courts, rounds, matches each, the points table, the target, and whether the last
round doubles. Nothing about the format is typed here. Scene 8's doubling is
DROPPED when the engine says nobody rests is false, the same way the cards drop
their own double-points line rather than advertising a rule that will not apply.

Deterministic, like every film in this repo: no CSS animations anywhere, every
moving value a pure function of t behind window.__seek(t), so a scrubbed frame
is always the same frame.

FONTS COME FROM brand/fonts/, not the scratchpad. The older UPRISING film reads
its faces from $SP/video/fonts, which a fresh container does not have — the same
trap build-lastround-video.py records.

  python3 build-uprising-explainer.py
  python3.13 build-uprising-explainer-audio.py
  node record-uprising-explainer.mjs
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "ops"))
from font_bundle import bundle as font_bundle          # noqa: E402

from build_uprising_explainer_consts import SCENES, BEATS, HERO, DUR, SP   # noqa: E402

OUT = os.path.join(SP, "uprising-explainer.html")
SOCIAL = os.path.join(HERE, "uprising-social.json")

W, H = 1080, 1920
VOLT, UV, VOID, CREAM, DIM = "#00F5C8", "#9D6BFF", "#06060A", "#F2F0F7", "#6E6B7A"

ORDINAL = ("", "one", "two", "three", "four", "five", "six", "seven",
           "eight", "nine", "ten", "eleven", "twelve")


def facts():
    r = subprocess.run(["node", os.path.join(HERE, "ops", "uprising-facts.mjs")],
                       capture_output=True, text=True, cwd=HERE)
    if r.returncode != 0:
        raise SystemExit("ops/uprising-facts.mjs failed:\n" + (r.stderr or r.stdout))
    f = json.loads(r.stdout)
    if f["courts"] < 3:
        # The climb scene needs somewhere to climb from. Two courts is a legal
        # night and a film that shows a three-step ladder would be lying about it.
        raise SystemExit(f"the engine reports {f['courts']} courts — "
                         "the climb scene needs at least three to be honest")
    return f


def main():
    S = json.load(open(SOCIAL))
    f = facts()
    os.makedirs(SP, exist_ok=True)

    courts = f["courts"]
    matches = int(f["matches"]) if f["even"] else None
    each = (f"{ORDINAL[matches].capitalize()} matches, {ORDINAL[matches]} different partners."
            if matches and matches < len(ORDINAL)
            else (f"{matches} matches, {matches} different partners."
                  if matches else "Everyone plays within one match of everyone else."))

    # Scene 8 states the doubling only when the engine applies it. doubleFinal
    # is false whenever anybody rests the last round, because the player sitting
    # it out could not win the night, and the engine switches the doubling off.
    if f["doubleFinal"]:
        ending_kicker = f"{f['rounds']} ROUNDS &middot; LAST ONE DOUBLES"
        ending_note = (f"Every round counts. The last one counts twice — "
                       f"the night is not over until it is.")
    else:
        ending_kicker = f"{f['rounds']} ROUNDS"
        ending_note = (f"{f['resting']} rest each round, so the table ranks on "
                       f"points per round played. Nobody wins on court time.")

    rows = "".join(
        f'<div class="prow" id="pr{c}"><span class="pc">COURT {c}</span>'
        f'<span class="pn"><b>{f["win"][str(c)]}</b><i> / {f["lose"][str(c)]}</i></span></div>'
        for c in range(1, courts + 1))

    lanes = "".join(
        f'<div class="lane{" top" if c == 1 else ""}" id="ln{c}">'
        f'<span class="lc">COURT {c}</span></div>'
        for c in range(1, courts + 1))

    payload = json.dumps({
        "scenes": SCENES, "dur": DUR, "beats": BEATS, "hero": HERO,
        "courts": courts, "target": f["target"], "rounds": f["rounds"],
        "scoring": f["scoring"], "double": f["doubleFinal"],
    })

    html = TEMPLATE
    for k, v in {
        "__FACES__": font_bundle(),
        "__DATA__": payload,
        "__W__": str(W), "__H__": str(H),
        "__VOLT__": VOLT, "__UV__": UV, "__VOID__": VOID,
        "__CREAM__": CREAM, "__DIM__": DIM,
        "__NAME__": S["name"],
        "__HOST__": S["host"].upper(),
        "__PROMISE__": S["promise"],
        "__PLAYERS__": str(f["players"]),
        "__COURTS__": str(courts),
        "__COURTWORD__": ORDINAL[courts].upper(),
        "__TARGET__": str(f["target"]),
        "__ROUNDS__": str(f["rounds"]),
        "__EACH__": each,
        "__LANES__": lanes,
        "__PROWS__": rows,
        "__ENDKICK__": ending_kicker,
        "__ENDNOTE__": ending_note,
    }.items():
        html = html.replace(k, v)

    with open(OUT, "w") as fh:
        fh.write(html)
    print(f"wrote {OUT}  ({len(html)/1024:.0f}KB)  {DUR:.1f}s, {len(SCENES)} scenes")
    print(f"from the engine: {f['players']} players · {courts} courts · "
          f"first to {f['target']} · {f['rounds']} rounds · "
          + ("last round doubles" if f["doubleFinal"] else f"{f['resting']} resting, no double"))
    print("\nnow:  python3.13 build-uprising-explainer-audio.py "
          "&& node record-uprising-explainer.mjs")


TEMPLATE = r"""<!doctype html><html lang="en"><head><meta charset="utf-8"><style>
__FACES__
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:__W__px;height:__H__px;overflow:hidden;background:__VOID__;color:__CREAM__;
  font-family:'Archivo',system-ui,sans-serif;-webkit-font-smoothing:antialiased}
body{position:relative}
.bg{position:absolute;inset:0;background:
  radial-gradient(ellipse 80% 42% at 18% 6%,rgba(157,107,255,.20),transparent),
  radial-gradient(ellipse 85% 45% at 84% 10%,rgba(0,245,200,.16),transparent),
  radial-gradient(ellipse 70% 40% at 50% 100%,rgba(0,245,200,.10),transparent),
  linear-gradient(180deg,#030305,__VOID__ 56%,#04040A)}
.grid{position:absolute;inset:0;background-image:
  linear-gradient(rgba(0,245,200,.05) 1px,transparent 1px),
  linear-gradient(90deg,rgba(0,245,200,.05) 1px,transparent 1px);background-size:72px 72px}
#flash{position:absolute;inset:0;background:__CREAM__;opacity:0;z-index:40;pointer-events:none}
.bars{position:absolute;left:0;right:0;height:0;background:__VOID__;z-index:30}
#barT{top:0} #barB{bottom:0}

.scene{position:absolute;inset:0;padding:230px 76px 250px;display:none;
  flex-direction:column;justify-content:center;z-index:10}
.scene.on{display:flex}

.d{font-family:'Archivo';font-style:italic;font-variation-settings:'wdth' 125,'wght' 900;
  text-transform:uppercase;line-height:.88;letter-spacing:.005em}
.k{font-family:'JetBrains Mono',monospace;font-weight:700;text-transform:uppercase;
  letter-spacing:.28em;font-size:25px;color:__VOLT__}
.k.uv{color:__UV__}
.sub{font-size:33px;line-height:1.42;color:#A9A4B8;margin-top:28px;max-width:900px}
.sub b{color:__CREAM__;font-weight:800}
.vt{color:__VOLT__}

.mark{width:70px;height:70px;border:2px solid rgba(0,245,200,.55);
  background:rgba(0,245,200,.12);display:flex;align-items:center;justify-content:center}
.chips{display:flex;gap:18px;margin-top:46px;flex-wrap:wrap}
.chip{border:1px solid rgba(242,240,247,.16);background:rgba(242,240,247,.04);
  padding:18px 26px}
.chip b{display:block;font-family:'Archivo';font-style:italic;
  font-variation-settings:'wdth' 125,'wght' 900;font-size:46px}
.chip i{display:block;font-style:normal;font-family:'JetBrains Mono',monospace;
  font-size:17px;font-weight:700;letter-spacing:.2em;color:__DIM__;margin-top:8px}

/* The ladder the chip climbs. One lane per court, laid out by the page so a
   different court count re-spaces it instead of running off the frame. */
.ladder{position:relative;margin-top:54px}
.lane{position:relative;height:118px;border:1px solid rgba(242,240,247,.14);
  background:rgba(242,240,247,.03);margin-bottom:16px;display:flex;align-items:center;
  padding-left:34px}
.lane.top{border-color:rgba(0,245,200,.5);background:rgba(0,245,200,.09)}
.lc{font-family:'JetBrains Mono',monospace;font-weight:700;font-size:26px;
  letter-spacing:.2em;color:__DIM__}
.lane.top .lc{color:__VOLT__}
#you{position:absolute;right:124px;width:100px;height:100px;border-radius:50%;
  background:__VOLT__;color:#04120F;display:flex;align-items:center;justify-content:center;
  font-family:'Archivo';font-style:italic;font-variation-settings:'wdth' 125,'wght' 900;
  font-size:29px;z-index:3}
#them{position:absolute;right:252px;width:100px;height:100px;border-radius:50%;
  background:__UV__;color:#120A20;display:flex;align-items:center;justify-content:center;
  font-family:'Archivo';font-style:italic;font-variation-settings:'wdth' 125,'wght' 900;
  font-size:26px;z-index:3}
#verdict{position:absolute;left:0;right:0;text-align:center;font-family:'Archivo';
  font-style:italic;font-variation-settings:'wdth' 125,'wght' 900;font-size:62px;
  text-transform:uppercase;z-index:4}

.prow{display:flex;align-items:center;justify-content:space-between;
  border:1px solid rgba(242,240,247,.14);background:rgba(242,240,247,.03);
  padding:26px 32px;margin-bottom:14px}
.prow:first-child{border-color:rgba(0,245,200,.5);background:rgba(0,245,200,.09)}
.pc{font-family:'JetBrains Mono',monospace;font-weight:700;font-size:28px;
  letter-spacing:.2em;color:__DIM__}
.prow:first-child .pc{color:__VOLT__}
.pn{font-family:'JetBrains Mono',monospace;font-weight:700;font-size:44px}
.pn i{font-style:normal;color:__DIM__}
.prow:first-child .pn b{color:__VOLT__}

.pair{display:flex;align-items:center;gap:26px;margin-top:50px}
.seat{width:132px;height:132px;border:1px solid rgba(0,245,200,.4);
  background:rgba(0,245,200,.08);display:flex;align-items:center;justify-content:center;
  font-family:'Archivo';font-style:italic;font-variation-settings:'wdth' 125,'wght' 900;
  font-size:52px;color:__VOLT__}
.seat.b{border-color:rgba(157,107,255,.45);background:rgba(157,107,255,.10);color:__UV__}
.plus{font-size:44px;color:__DIM__}
.v{font-family:'Archivo';font-style:italic;font-variation-settings:'wdth' 125,'wght' 900;
  font-size:46px;color:__CREAM__;margin:0 10px}

/* A rail, so the film reads as something with a length rather than as a
   stack of slides. It sits ABOVE the bottom letterbox bar, which grows on
   every beat — drawn under it, the punch would swallow it on each cut. */
#rail{position:absolute;left:76px;right:76px;bottom:188px;height:3px;
  background:rgba(242,240,247,.14);z-index:32}
#railfill{display:block;height:100%;width:0;background:__VOLT__}
#step{position:absolute;left:76px;bottom:208px;font-family:'JetBrains Mono',monospace;
  font-size:19px;font-weight:700;letter-spacing:.24em;color:__DIM__;z-index:32}
.foot{position:absolute;left:76px;right:76px;bottom:250px}
.host{font-family:'JetBrains Mono',monospace;font-weight:700;font-size:26px;
  letter-spacing:.16em;color:__VOLT__}
.host small{display:block;font-size:21px;letter-spacing:.1em;color:__DIM__;margin-top:12px}
</style></head><body>
<div class="bg"></div><div class="grid"></div>
<div class="bars" id="barT"></div><div class="bars" id="barB"></div>
<div id="flash"></div>
<div id="rail"><span id="railfill"></span></div>
<div id="step"></div>

<div class="scene" id="s1">
  <div style="display:flex;align-items:center;gap:26px" id="s1h">
    <span class="mark"><svg viewBox="0 0 100 100" width="36" height="36">
      <path d="M18 64 L50 32 L82 64" fill="none" stroke="__VOLT__" stroke-width="13"
            stroke-linecap="square"/></svg></span>
    <span class="d" style="font-size:72px">__NAME__</span>
  </div>
  <div class="d" id="s1t" style="font-size:148px;margin-top:54px">How it<br><span class="vt">works</span></div>
  <div class="sub" id="s1s">Padel, but the court you play on is the prize.</div>
</div>

<div class="scene" id="s2">
  <div class="k" id="s2k">Start here</div>
  <div class="d" id="s2t" style="font-size:136px;margin-top:34px">Come<br><span class="vt">alone</span></div>
  <div class="sub" id="s2s">No partner needed. You are paired on arrival and
    <b>re-paired every single round</b>.</div>
  <div class="chips" id="s2c">
    <span class="chip"><b>__PLAYERS__</b><i>Players</i></span>
    <span class="chip"><b>__COURTS__</b><i>Courts</i></span>
    <span class="chip"><b>1</b><i>Ladder</i></span>
  </div>
</div>

<div class="scene" id="s3">
  <div class="k uv" id="s3k">Round one</div>
  <div class="d" id="s3t" style="font-size:132px;margin-top:34px">The<br><span class="vt">shuffle</span></div>
  <div class="sub" id="s3s">It scores <b>nothing</b>. It decides where you start —
    so your court is <b>won, not drawn</b>. Win big and you open on Court 1.</div>
</div>

<div class="scene" id="s4">
  <div class="k" id="s4k">Every match</div>
  <div class="d" id="s4t" style="font-size:300px;margin-top:20px"><span class="vt"
    id="s4n">0</span></div>
  <div class="sub" id="s4s"><b>First to __TARGET__.</b> Straight rallies, no games and
    no sets. About ten minutes, then everybody moves.</div>
</div>

<div class="scene" id="s5">
  <div class="k" id="s5k">The whole format</div>
  <div class="d" id="s5t" style="font-size:112px;margin-top:26px">Win and<br><span
    class="vt">you climb</span></div>
  <div class="ladder" id="s5l">
    __LANES__
    <div id="you">YOU</div>
    <div id="them"></div>
    <div id="verdict"></div>
  </div>
</div>

<div class="scene" id="s6">
  <div class="k" id="s6k">What you bank</div>
  <div class="d" id="s6t" style="font-size:96px;margin-top:26px">The court<br><span
    class="vt">pays you</span></div>
  <div class="sub" id="s6s" style="font-size:29px;margin-top:22px">Win / lose, per match.
    Climb and the same win is worth more.</div>
  <div style="margin-top:36px" id="s6r">__PROWS__</div>
</div>

<div class="scene" id="s7">
  <div class="k" id="s7k">Every round</div>
  <div class="d" id="s7t" style="font-size:112px;margin-top:26px">New<br><span
    class="vt">partners</span></div>
  <div class="pair" id="s7p">
    <span class="seat">1</span><span class="plus">+</span><span class="seat">4</span>
    <span class="v">v</span>
    <span class="seat b">2</span><span class="plus">+</span><span class="seat b">3</span>
  </div>
  <div class="sub" id="s7s">Ranked on the court, then split. __EACH__</div>
</div>

<div class="scene" id="s8">
  <div class="k" id="s8k">__ENDKICK__</div>
  <div class="d" id="s8t" style="font-size:118px;margin-top:34px">Highest<br><span
    class="vt">total wins</span></div>
  <div class="sub" id="s8s">__ENDNOTE__</div>
  <div class="foot" id="s8f">
    <span class="host">__HOST__<small>__PROMISE__</small></span>
  </div>
</div>

<script>
const D = __DATA__;
const SC = D.scenes, DUR = D.dur, BEATS = D.beats, HERO = D.hero;
const $ = id => document.getElementById(id);
const cl = (x, a, b) => x < a ? a : x > b ? b : x;
const ease = u => 1 - Math.pow(1 - cl(u, 0, 1), 3);
// A scene-local clock: u is 0 at the cut and 1 at the next one.
const local = t => {
  let i = 0;
  for (let k = 0; k < SC.length; k++) if (t >= SC[k]) i = k;
  const end = i + 1 < SC.length ? SC[i + 1] : DUR;
  return { i, s: t - SC[i], len: end - SC[i] };
};
// Energy from the nearest beat, used for the flash and the bar punch. Clamped
// where it is MADE: the window opens 20ms early so a hit is never late, which
// otherwise pushes (1-u)^3 above one and sends derived radii negative.
const beat = t => {
  let e = 0;
  for (const b of BEATS) {
    const u = (t - (b - 0.02)) / 0.42;
    if (u >= 0 && u <= 1) e = Math.max(e, Math.pow(1 - u, 3));
  }
  return cl(e, 0, 1);
};
const rise = (el, u, px) => {
  el.style.opacity = cl(u, 0, 1);
  el.style.transform = `translateY(${(1 - ease(u)) * (px === undefined ? 46 : px)}px)`;
};

function seek(t) {
  t = cl(t, 0, DUR);
  const { i, s, len } = local(t);
  const n = i + 1;
  for (let k = 1; k <= SC.length; k++) {
    const el = $('s' + k);
    if (el) el.classList.toggle('on', k === n);
  }
  const e = beat(t);

  // The flash belongs UNDER the letterbox. Above the bars it washes them too
  // and reads as a strobe rather than as a cut.
  $('flash').style.opacity = (s < 0.09 && i > 0) ? 0.30 * (1 - s / 0.09) : 0;
  const pad2 = n2 => String(n2).padStart(2, '0');
  $('railfill').style.width = (t / DUR * 100) + '%';
  $('step').textContent = pad2(n) + ' / ' + pad2(SC.length);
  const bar = 26 + 16 * e;
  $('barT').style.height = bar + 'px';
  $('barB').style.height = bar + 'px';

  if (n === 1) {
    rise($('s1h'), s / 0.5, 24);
    rise($('s1t'), (s - 0.25) / 0.65);
    rise($('s1s'), (s - 0.7) / 0.6);
  } else if (n === 2) {
    rise($('s2k'), s / 0.4, 18);
    rise($('s2t'), (s - 0.2) / 0.6);
    rise($('s2s'), (s - 0.6) / 0.6);
    rise($('s2c'), (s - 0.95) / 0.6);
  } else if (n === 3) {
    rise($('s3k'), s / 0.4, 18);
    rise($('s3t'), (s - 0.2) / 0.6);
    rise($('s3s'), (s - 0.65) / 0.65);
  } else if (n === 4) {
    rise($('s4k'), s / 0.4, 18);
    rise($('s4t'), (s - 0.2) / 0.5);
    rise($('s4s'), (s - 0.9) / 0.6);
    // The count is the scene: it reaches the target and stops, so the number
    // on screen is only ever one the match could really be at.
    const u = cl((s - 0.35) / 1.5, 0, 1);
    $('s4n').textContent = Math.round(ease(u) * D.target);
  } else if (n === 5) {
    rise($('s5k'), s / 0.4, 18);
    rise($('s5t'), (s - 0.2) / 0.6);
    rise($('s5l'), (s - 0.55) / 0.7, 34);
    climb(s);
  } else if (n === 6) {
    rise($('s6k'), s / 0.4, 18);
    rise($('s6t'), (s - 0.2) / 0.6);
    rise($('s6s'), (s - 0.6) / 0.5);
    const rows = $('s6r').children;
    for (let r = 0; r < rows.length; r++) rise(rows[r], (s - 0.85 - r * 0.24) / 0.5, 26);
  } else if (n === 7) {
    rise($('s7k'), s / 0.4, 18);
    rise($('s7t'), (s - 0.2) / 0.6);
    rise($('s7p'), (s - 0.6) / 0.6, 30);
    rise($('s7s'), (s - 1.0) / 0.6);
  } else if (n === 8) {
    rise($('s8k'), s / 0.4, 18);
    rise($('s8t'), (s - 0.25) / 0.7);
    rise($('s8s'), (s - 0.75) / 0.6);
    rise($('s8f'), (s - 1.25) / 0.7, 26);
  }
}

// THE CLIMB. Three rounds on screen: the chip wins on Court 3 and goes up, wins
// again on Court 2 and goes up, and the violet chip it beat drops the other way.
// Positions are read off the lanes themselves, so a different court count moves
// the chip to wherever the lane actually is rather than to a hard-coded pixel.
const STEPS = [
  { at: 0.95, you: 3, them: 2, say: 'WIN',  col: '__VOLT__' },
  { at: 2.35, you: 2, them: 3, say: 'WIN',  col: '__VOLT__' },
  { at: 3.75, you: 1, them: 4, say: 'TOP',  col: '__VOLT__' },
];
function laneY(c) {
  const el = $('ln' + Math.min(c, D.courts));
  const box = el.getBoundingClientRect();
  const ref = $('s5l').getBoundingClientRect();
  return box.top - ref.top + box.height / 2 - 50;
}
function climb(s) {
  const you = $('you'), them = $('them'), vd = $('verdict');
  if (!you) return;
  let from = STEPS[0].you, to = STEPS[0].you, u = 0, tf = 2, tt = 2, say = '', col = '', sayAt = -1;
  for (let k = 0; k < STEPS.length; k++) {
    const st = STEPS[k];
    if (s >= st.at) {
      from = st.you; to = st.you; tf = st.them; tt = st.them;
      if (k + 1 < STEPS.length) {
        const nx = STEPS[k + 1];
        u = cl((s - (nx.at - 0.45)) / 0.45, 0, 1);
        to = nx.you; tt = nx.them;
      }
      if (s < st.at + 0.75) { say = st.say; col = st.col; sayAt = st.at; }
    }
  }
  const m = ease(u);
  you.style.top = (laneY(from) + (laneY(to) - laneY(from)) * m) + 'px';
  you.style.opacity = cl(s / 0.5, 0, 1);
  them.style.top = (laneY(tf) + (laneY(tt) - laneY(tf)) * m) + 'px';
  them.style.opacity = cl(s / 0.5, 0, 1) * 0.9;
  // The verdict sits ON the lane the chip is leaving, which is where the eye
  // already is. Printed only for three quarters of a second after the result.
  //
  // The fade is driven by the step's own index, not by a search for a step
  // matching its label: two steps say WIN, so looking one up by text can find
  // the wrong one, and finding none at all gave `undefined.at` -> NaN -> an
  // opacity the browser silently ignores, which is a bug that looks like a
  // design decision.
  if (sayAt >= 0) {
    vd.textContent = say;
    vd.style.color = col;
    vd.style.top = (laneY(from) - 96) + 'px';
    const a = cl((s - sayAt) / 0.75, 0, 1);
    vd.style.opacity = 1 - a * a;
  } else {
    vd.style.opacity = 0;
  }
}

window.__seek = seek;
window.__dur = DUR;
window.__scenes = SC;
window.__hero = HERE_HERO;
seek(0);
</script>
</body></html>"""

TEMPLATE = TEMPLATE.replace("HERE_HERO", "D.hero")

if __name__ == "__main__":
    main()
