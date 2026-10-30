# -*- coding: utf-8 -*-
"""UPRISING — the NIGHT FILM. 1080x1920, ~29s. The ladder moving, live.

The infographic states the rule and the explainer shows one chip climbing.
This shows the whole field: sixteen players, four courts, twelve rounds, every
chip moving to the court the engine actually put it on, with the table building
underneath.

NOTHING HERE IS CHOREOGRAPHED. `ops/uprising-night-sim.mjs` plays a real night
with the shipped `uprising-engine.js` and prints it; this animates that JSON.
Every court a chip moves to is the court `upBuildRound` dealt, every score is
the one the match was given, and every total is `upStandings` run over the night
as it stood after that round. A hand-drawn "winners go up" would be a drawing of
what we think the rule does; this is the rule doing it.

THE SEED IS A CHOICE AND THE FILM CHECKS ITS OWN STORY. Seeds are free, so one
was picked that makes a watchable night — but the card then SAYS the last round
decided it, and a seed that stopped doing that would make the film a liar. The
builder re-reads the night it was given and refuses unless the lead really does
change hands in the doubled final.

Deterministic: no CSS animations, every moving value a pure function of t
behind window.__seek(t).

  node ops/uprising-night-sim.mjs 2026 > $SP/night.json
  python3 build-uprising-nightfilm.py
  python3.13 build-uprising-nightfilm-audio.py
  node record-uprising-nightfilm.mjs
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "ops"))
from font_bundle import bundle as font_bundle          # noqa: E402

SP = os.environ.get("SP") or (
    "/tmp/claude-0/-home-user-May-madness/0e44f0ad-a683-5f0d-9de6-9459ae328963/scratchpad")
NIGHT = os.path.join(SP, "night.json")
OUT = os.path.join(SP, "uprising-night.html")
SEED = int(os.environ.get("SEED", 2026))

W, H = 1080, 1920
VOLT, UV, VOID, CREAM, DIM = "#00F5C8", "#9D6BFF", "#06060A", "#F2F0F7", "#6E6B7A"
WARN = "#FF4D6D"

INTRO = 3.20          # the title card
ROUND = 1.72          # one round on screen: arrive, score, verdict
OUTRO = 4.60          # the finish


def night():
    """Play the night with the engine, or re-read the one already played."""
    if not os.path.exists(NIGHT) or os.environ.get("REPLAY"):
        r = subprocess.run(["node", os.path.join(HERE, "ops", "uprising-night-sim.mjs"),
                            str(SEED)], capture_output=True, text=True, cwd=HERE)
        if r.returncode != 0:
            raise SystemExit("ops/uprising-night-sim.mjs failed:\n" + (r.stderr or r.stdout))
        with open(NIGHT, "w") as fh:
            fh.write(r.stdout)
    return json.load(open(NIGHT))


def check_story(N):
    """The card says the last round decided it. Make the night prove that."""
    if len(N["frames"]) < 3:
        raise SystemExit("a night of two rounds is not a night")
    if not N["doubleFinal"]:
        raise SystemExit("the engine did not double the last round of this night — "
                         "the film's closing card says it did")
    before, after = N["frames"][-2]["top"], N["frames"][-1]["top"]
    swing = before[0]["id"] != after[0]["id"]
    gap = before[0]["pts"] - before[1]["pts"]
    if not swing and gap > 8:
        raise SystemExit(
            f"seed {N['seed']} gives a night the last round could not decide — "
            f"the leader was {gap} clear going into it and still won.\n"
            f"  The closing card claims the double final settled it. Pick another "
            f"seed (SEED=... REPLAY=1) or rewrite the card.")
    return swing, gap


def main():
    N = night()
    swing, gap = check_story(N)
    rounds = len(N["frames"])
    dur = INTRO + rounds * ROUND + OUTRO

    lab = {p["id"]: p["label"] for p in N["players"]}
    final = N["frames"][-1]["top"]
    champ, runner = final[0], final[1]

    close = ("It changed hands in the last round."
             if swing else f"It came down to the last round — {gap} points in it.")

    payload = json.dumps({
        "intro": INTRO, "round": ROUND, "outro": OUTRO, "dur": dur,
        "courts": N["courts"], "target": N["target"], "rounds": rounds,
        "shuffleRounds": N["shuffleRounds"],
        "players": N["players"], "frames": N["frames"],
        "champ": lab[champ["id"]], "champPts": champ["pts"],
        "runner": lab[runner["id"]], "runnerPts": runner["pts"],
    })

    html = TEMPLATE
    for k, v in {
        "__FACES__": font_bundle(), "__DATA__": payload,
        "__W__": str(W), "__H__": str(H),
        "__VOLT__": VOLT, "__UV__": UV, "__VOID__": VOID,
        "__CREAM__": CREAM, "__DIM__": DIM, "__WARN__": WARN,
        "__PLAYERS__": str(len(N["players"])),
        "__COURTS__": str(N["courts"]),
        "__ROUNDS__": str(rounds),
        "__TARGET__": str(N["target"]),
        "__CLOSE__": close,
        "__CHAMP__": lab[champ["id"]],
        "__CHAMPPTS__": str(champ["pts"]),
    }.items():
        html = html.replace(k, v)

    with open(OUT, "w") as fh:
        fh.write(html)
    print(f"wrote {OUT}  ({len(html)/1024:.0f}KB)  {dur:.1f}s, {rounds} rounds")
    print(f"the night (seed {N['seed']}, played by the engine): "
          f"{len(N['players'])} players · {N['courts']} courts · first to {N['target']}")
    print(f"  champion {lab[champ['id']]} on {champ['pts']}, "
          f"{lab[runner['id']]} on {runner['pts']}"
          + ("  — the lead CHANGED HANDS in the doubled final"
             if swing else f"  — {gap} points in it going into the final"))
    print("\nnow:  python3.13 build-uprising-nightfilm-audio.py "
          "&& node record-uprising-nightfilm.mjs")


TEMPLATE = r"""<!doctype html><html lang="en"><head><meta charset="utf-8"><style>
__FACES__
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:__W__px;height:__H__px;overflow:hidden;background:__VOID__;color:__CREAM__;
  font-family:'Archivo',system-ui,sans-serif;-webkit-font-smoothing:antialiased}
body{position:relative}
.bg{position:absolute;inset:0;background:
  radial-gradient(ellipse 80% 40% at 16% 5%,rgba(157,107,255,.18),transparent),
  radial-gradient(ellipse 85% 42% at 86% 9%,rgba(0,245,200,.15),transparent),
  linear-gradient(180deg,#030305,__VOID__ 58%,#04040A)}
.grid{position:absolute;inset:0;background-image:
  linear-gradient(rgba(0,245,200,.045) 1px,transparent 1px),
  linear-gradient(90deg,rgba(0,245,200,.045) 1px,transparent 1px);background-size:72px 72px}
#flash{position:absolute;inset:0;background:__CREAM__;opacity:0;z-index:40;pointer-events:none}
.bars{position:absolute;left:0;right:0;height:0;background:__VOID__;z-index:30}
#barT{top:0} #barB{bottom:0}
.d{font-family:'Archivo';font-style:italic;font-variation-settings:'wdth' 125,'wght' 900;
  text-transform:uppercase;line-height:.88;letter-spacing:.005em}
.mono{font-family:'JetBrains Mono',monospace;font-weight:700}

/* ── title ─────────────────────────────────────────────────────────────── */
#title{position:absolute;inset:0;padding:230px 76px;display:flex;flex-direction:column;
  justify-content:center;z-index:12}
#tk{font-family:'JetBrains Mono',monospace;font-weight:700;font-size:25px;
  letter-spacing:.28em;text-transform:uppercase;color:__VOLT__}
#tt{font-size:150px;margin-top:40px}
#tt span{color:__VOLT__}
#ts{font-size:33px;line-height:1.42;color:#A9A4B8;margin-top:30px;max-width:900px}
#ts b{color:__CREAM__;font-weight:800}

/* ── the board ─────────────────────────────────────────────────────────── */
/* Centred, not top-aligned: the board is shorter than the frame and the
   bottom third was dead space. */
#board{position:absolute;inset:0;padding:212px 60px 236px;display:none;
  flex-direction:column;justify-content:center;z-index:12}
#board.on{display:flex}
#hd{display:flex;align-items:baseline;justify-content:space-between}
#hr{font-family:'Archivo';font-style:italic;font-variation-settings:'wdth' 125,'wght' 900;
  font-size:62px;text-transform:uppercase}
#hs{font-family:'JetBrains Mono',monospace;font-weight:700;font-size:24px;
  letter-spacing:.2em;color:__DIM__;text-transform:uppercase}
#hs b{color:__VOLT__}

#lanes{position:relative;margin-top:30px}
.lane{position:relative;height:150px;border:1px solid rgba(242,240,247,.13);
  background:rgba(242,240,247,.028);margin-bottom:14px;display:flex;align-items:center;
  padding:0 26px}
.lane.c1{border-color:rgba(0,245,200,.42);background:rgba(0,245,200,.075)}
.lnum{font-family:'JetBrains Mono',monospace;font-weight:700;font-size:23px;
  letter-spacing:.18em;color:__DIM__;width:128px}
.lane.c1 .lnum{color:__VOLT__}
.lsc{margin-left:auto;font-family:'JetBrains Mono',monospace;font-weight:700;
  font-size:40px;color:__CREAM__;min-width:150px;text-align:right}
.lsc i{font-style:normal;color:__DIM__;font-size:30px}

/* The chips live in one layer over the lanes, so a chip moving from Court 3 to
   Court 2 is one element changing position rather than two elements appearing
   and disappearing — which is the whole point of the film. */
#chips{position:absolute;inset:0;pointer-events:none}
.chip{position:absolute;width:86px;height:86px;border-radius:50%;
  display:flex;align-items:center;justify-content:center;
  font-family:'Archivo';font-style:italic;font-variation-settings:'wdth' 125,'wght' 900;
  font-size:36px;border:2px solid rgba(242,240,247,.30);
  background:rgba(12,12,18,.96);color:__CREAM__}
.chip.win{border-color:__VOLT__;background:rgba(0,245,200,.22);color:__VOLT__}
.chip.lose{border-color:rgba(157,107,255,.75);background:rgba(157,107,255,.16);color:__UV__}
.chip.lead{border-color:__VOLT__;border-width:4px;color:__VOLT__}
#vees{position:absolute;inset:0;pointer-events:none}
.vee{position:absolute;font-family:'Archivo';font-style:italic;
  font-variation-settings:'wdth' 125,'wght' 900;font-size:30px;color:__DIM__}

/* ── the table ─────────────────────────────────────────────────────────── */
#tbl{margin-top:26px}
#tbk{font-family:'JetBrains Mono',monospace;font-weight:700;font-size:20px;
  letter-spacing:.26em;color:__DIM__;text-transform:uppercase;margin-bottom:14px}
.trow{display:flex;align-items:center;gap:20px;height:62px}
.tpos{font-family:'JetBrains Mono',monospace;font-weight:700;font-size:22px;color:__DIM__;width:42px}
.tlab{width:62px;height:62px;border-radius:50%;border:2px solid rgba(242,240,247,.3);
  display:flex;align-items:center;justify-content:center;
  font-family:'Archivo';font-style:italic;font-variation-settings:'wdth' 125,'wght' 900;
  font-size:27px}
.trow.one .tlab{border-color:__VOLT__;color:__VOLT__;background:rgba(0,245,200,.16)}
.tbar{flex:1;height:14px;background:rgba(242,240,247,.08);position:relative}
.tbar span{position:absolute;left:0;top:0;bottom:0;background:rgba(0,245,200,.45)}
.trow.one .tbar span{background:__VOLT__}
.tpts{font-family:'JetBrains Mono',monospace;font-weight:700;font-size:34px;width:100px;
  text-align:right}
.trow.one .tpts{color:__VOLT__}

/* ── outro ─────────────────────────────────────────────────────────────── */
#out{position:absolute;inset:0;padding:230px 76px;display:none;flex-direction:column;
  justify-content:center;z-index:12}
#out.on{display:flex}
#ok{font-family:'JetBrains Mono',monospace;font-weight:700;font-size:25px;
  letter-spacing:.28em;text-transform:uppercase;color:__VOLT__}
#ot{font-size:132px;margin-top:34px}
#ot span{color:__VOLT__}
#os{font-size:33px;line-height:1.42;color:#A9A4B8;margin-top:28px;max-width:900px}
#os b{color:__CREAM__;font-weight:800}
#of{position:absolute;left:76px;right:76px;bottom:252px}
#of .host{font-family:'JetBrains Mono',monospace;font-weight:700;font-size:26px;
  letter-spacing:.16em;color:__VOLT__}

#rail{position:absolute;left:60px;right:60px;bottom:188px;height:3px;
  background:rgba(242,240,247,.13);z-index:32}
#railfill{display:block;height:100%;width:0;background:__VOLT__}
</style></head><body>
<div class="bg"></div><div class="grid"></div>
<div class="bars" id="barT"></div><div class="bars" id="barB"></div>
<div id="flash"></div>
<div id="rail"><span id="railfill"></span></div>

<div id="title">
  <div id="tk">One night, start to finish</div>
  <div id="tt" class="d">Watch the<br><span>ladder</span></div>
  <div id="ts"><b>__PLAYERS__ players. __COURTS__ courts. __ROUNDS__ rounds.</b>
    Win and you go up a court, lose and you go down — every round, all night.</div>
</div>

<div id="board">
  <div id="hd"><span id="hr" class="d">Round 1</span><span id="hs"></span></div>
  <div id="lanes"></div>
  <div id="tbl"><div id="tbk">The table</div><div id="trows"></div></div>
</div>

<div id="out">
  <div id="ok">Twelve rounds later</div>
  <div id="ot" class="d"><span>__CHAMP__</span><br>takes it</div>
  <div id="os">__CHAMPPTS__ points. __CLOSE__ <b>The last round counts double,
    so the night is not over until it is.</b></div>
  <div id="of"><span class="host">AMERICANO.URBANPADEL.OM</span></div>
</div>

<script>
const D = __DATA__;
const DUR = D.dur, R0 = D.intro, RL = D.round;
const $ = id => document.getElementById(id);
const cl = (x, a, b) => x < a ? a : x > b ? b : x;
const ease = u => 1 - Math.pow(1 - cl(u, 0, 1), 3);
const rise = (el, u, px) => {
  el.style.opacity = cl(u, 0, 1);
  el.style.transform = `translateY(${(1 - ease(u)) * (px === undefined ? 44 : px)}px)`;
};

// ── build the furniture once ──────────────────────────────────────────────
const lanes = $('lanes');
for (let c = 1; c <= D.courts; c++) {
  const el = document.createElement('div');
  el.className = 'lane' + (c === 1 ? ' c1' : '');
  el.id = 'lane' + c;
  el.innerHTML = `<span class="lnum">COURT ${c}</span><span class="lsc" id="sc${c}"></span>`;
  lanes.appendChild(el);
}
const chipLayer = document.createElement('div'); chipLayer.id = 'chips';
const veeLayer = document.createElement('div'); veeLayer.id = 'vees';
lanes.appendChild(veeLayer); lanes.appendChild(chipLayer);
const chip = {};
for (const p of D.players) {
  const el = document.createElement('div');
  el.className = 'chip'; el.textContent = p.label; el.id = 'ch_' + p.id;
  chipLayer.appendChild(el);
  chip[p.id] = el;
}
for (let c = 1; c <= D.courts; c++) {
  const v = document.createElement('span');
  v.className = 'vee'; v.textContent = 'v'; v.id = 'vee' + c;
  veeLayer.appendChild(v);
}
const rows = [];
for (let i = 0; i < 5; i++) {
  const el = document.createElement('div');
  el.className = 'trow';
  el.innerHTML = `<span class="tpos">${i + 1}</span><span class="tlab"></span>`
    + `<span class="tbar"><span></span></span><span class="tpts"></span>`;
  $('trows').appendChild(el);
  rows.push(el);
}

// Slot geometry: four chips to a lane, read off the lane the page actually
// laid out rather than from a hard-coded pixel, so a three-court night or a
// different chip size re-spaces itself.
const SLOTX = [172, 272, 410, 510];
function slotPos(court, slot) {
  const ln = $('lane' + Math.min(court, D.courts));
  const b = ln.getBoundingClientRect(), ref = lanes.getBoundingClientRect();
  return { x: SLOTX[slot], y: b.top - ref.top + b.height / 2 - 43 };
}
// Resting players park under the board. At sixteen on four courts nobody
// rests, but a thirteen-player night has one every round and a chip that
// simply vanished would be the film telling a lie about the format.
function restPos(i) {
  const ref = lanes.getBoundingClientRect();
  return { x: 700 + i * 96, y: ref.height + 14 };
}

function placement(fi) {
  // Where every chip is in frame fi: {id: {x,y,court,slot,win}}
  const f = D.frames[fi];
  const out = {};
  for (const m of f.courts) {
    const four = [m.team1[0], m.team1[1], m.team2[0], m.team2[1]];
    const t1 = m.s1 > m.s2;
    four.forEach((id, s) => {
      const p = slotPos(m.court, s);
      out[id] = { x: p.x, y: p.y, court: m.court, slot: s, win: s < 2 ? t1 : !t1 };
    });
  }
  (f.resting || []).forEach((id, i) => {
    const p = restPos(i);
    out[id] = { x: p.x, y: p.y, court: 0, slot: -1, win: null };
  });
  return out;
}
const PLACE = D.frames.map((_, i) => null);   // filled lazily, after layout

function seek(t) {
  t = cl(t, 0, DUR);
  const boardStart = R0, boardEnd = R0 + D.frames.length * RL;
  const onTitle = t < boardStart, onOut = t >= boardEnd;
  $('title').style.display = onTitle ? 'flex' : 'none';
  $('board').classList.toggle('on', !onTitle && !onOut);
  $('out').classList.toggle('on', onOut);
  $('railfill').style.width = (t / DUR * 100) + '%';

  // The flash belongs UNDER the letterbox; above it, it washes the bars too
  // and reads as a strobe rather than as a cut.
  const sinceCut = onTitle ? t : (onOut ? t - boardEnd : (t - boardStart) % RL);
  $('flash').style.opacity = (!onTitle && sinceCut < 0.07) ? 0.22 * (1 - sinceCut / 0.07) : 0;
  const punch = Math.pow(1 - cl(sinceCut / 0.40, 0, 1), 3);
  $('barT').style.height = (26 + 14 * punch) + 'px';
  $('barB').style.height = (26 + 14 * punch) + 'px';

  if (onTitle) {
    rise($('tk'), t / 0.45, 18);
    rise($('tt'), (t - 0.25) / 0.7);
    rise($('ts'), (t - 0.75) / 0.7);
    return;
  }
  if (onOut) {
    const s = t - boardEnd;
    rise($('ok'), s / 0.45, 18);
    rise($('ot'), (s - 0.3) / 0.75);
    rise($('os'), (s - 0.9) / 0.7);
    rise($('of'), (s - 1.5) / 0.7, 26);
    return;
  }

  const fi = Math.min(D.frames.length - 1, Math.floor((t - boardStart) / RL));
  const s = (t - boardStart) - fi * RL;
  const f = D.frames[fi];

  // PHASES. arrive: chips travel from last round's court to this one. score:
  // the numbers count to the result. verdict: the winning pair lights up.
  const MOVE = 0.56, SCORE = 0.46;
  const mv = ease(cl(s / MOVE, 0, 1));
  const sc = cl((s - MOVE) / SCORE, 0, 1);
  const verdict = s > MOVE + SCORE;

  if (!PLACE[fi]) PLACE[fi] = placement(fi);
  if (fi > 0 && !PLACE[fi - 1]) PLACE[fi - 1] = placement(fi - 1);
  const to = PLACE[fi], from = fi > 0 ? PLACE[fi - 1] : PLACE[fi];
  const leadId = fi > 0 ? D.frames[fi - 1].top[0].id : null;

  for (const p of D.players) {
    const a = from[p.id] || to[p.id], b = to[p.id];
    const el = chip[p.id];
    if (!b) { el.style.opacity = 0; continue; }
    el.style.opacity = 1;
    el.style.transform = `translate(${a.x + (b.x - a.x) * mv}px,`
      + `${a.y + (b.y - a.y) * mv}px)`;
    el.className = 'chip'
      + (verdict ? (b.win ? ' win' : (b.win === false ? ' lose' : '')) : '')
      + (p.id === leadId && !verdict ? ' lead' : '');
  }
  for (let c = 1; c <= D.courts; c++) {
    const v = $('vee' + c), p = slotPos(c, 1);
    v.style.transform = `translate(${(SLOTX[1] + SLOTX[2]) / 2 + 43 - 8}px,${p.y + 26}px)`;
  }

  $('hr').textContent = 'Round ' + f.n;
  $('hs').innerHTML = f.shuffle
    ? 'THE SHUFFLE &middot; SCORES NOTHING'
    : (f.doubled ? '<b>FINAL ROUND &middot; DOUBLE POINTS</b>'
                 : 'FIRST TO ' + D.target + ' &middot; ' + f.n + ' OF ' + D.rounds);

  for (const m of f.courts) {
    const el = $('sc' + m.court);
    if (!el) continue;
    // The count stops at the real score, so a frame never shows a scoreline
    // the match did not reach.
    const a = Math.round(m.s1 * sc), b = Math.round(m.s2 * sc);
    el.innerHTML = s < MOVE ? '<i>&mdash;</i>' : `${a}<i> : </i>${b}`;
  }

  const maxPts = Math.max(1, f.top[0].pts);
  f.top.forEach((row, i) => {
    const el = rows[i];
    el.classList.toggle('one', i === 0);
    el.querySelector('.tlab').textContent =
      (D.players.find(p => p.id === row.id) || {}).label || '';
    // Points ease to the new total over the scoring phase rather than jumping,
    // so the table is visibly a consequence of the courts above it.
    const prev = fi > 0 ? ((D.frames[fi - 1].pts || {})[row.id] ?? row.pts) : 0;
    const shown = Math.round(prev + (row.pts - prev) * cl((s - MOVE) / (SCORE + 0.2), 0, 1));
    el.querySelector('.tpts').textContent = shown;
    el.querySelector('.tbar span').style.width = (shown / maxPts * 100) + '%';
    rise(el, (s - 0.1 - i * 0.03) / 0.4, 10);
  });
}

window.__seek = seek;
window.__dur = DUR;
window.__intro = R0;
window.__roundLen = RL;
window.__rounds = D.frames.length;
seek(0);
</script>
</body></html>"""


if __name__ == "__main__":
    main()
