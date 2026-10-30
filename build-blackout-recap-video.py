# -*- coding: utf-8 -*-
"""BLACKOUT VOL.8 — the SEASON RECAP film. 1080x1920, ~23s.

Nine nights in one cut, ending on the three podium posters.

THE POSTERS ARE THE PAYOFF AND NOTHING IS DRAWN OVER THEM. They already carry
the lockup, the name, the placement and the points — `build-hype-video.py`
records what happens when branded photographs are used as a backdrop for more
branding: a frame inside a frame, two URLs on screen. So each player gets TWO
beats instead: a data card that says what the poster CANNOT, then the poster
full bleed with a slow push and no type on it at all.

EVERY FIGURE COMES FROM ops/blackout-standings.mjs, which runs the app's own
engine over the final state — so the film cannot claim a total the leaderboard
contradicts. The posters were made by hand, so the builder CHECKS them: the
points printed on each one are passed in and must match the engine's table, or
it refuses to build. A recap that disagrees with the poster inside it is worse
than no recap.

THE LEAD STAT ON EACH CARD IS CHOSEN FROM THE DATA, not written here — most
nights won, best win rate, or played every night — so next volume's run does
not keep this volume's story after the facts have moved.

  node ops/blackout-standings.mjs $SP/bo4.json $SP/final.json
  python3 build-blackout-recap-video.py
  python3.13 build-blackout-recap-audio.py
  node record-blackout-recap-video.mjs
"""
import json
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "ops"))
from font_bundle import bundle as font_bundle          # noqa: E402

SP = os.environ.get("SP") or (
    "/tmp/claude-0/-home-user-May-madness/0e44f0ad-a683-5f0d-9de6-9459ae328963/scratchpad")
STANDINGS = os.path.join(SP, "final.json")
OUT = os.path.join(SP, "blackout-recap.html")
SHOTS = os.path.join(SP, "podium")

W, H = 1080, 1920
LIME, MAGENTA, VOID, INK, MUTED = "#C6FF00", "#FF2E88", "#050505", "#F2F2F2", "#9A9A9A"
UV = "#7B2BFF"

# The three posters, newest-first on the timeline (3rd, 2nd, 1st), with the
# points each one has printed on it. Those are checked against the engine.
POSTERS = [
    dict(rank=3, file="3rd.png", printed=200),
    dict(rank=2, file="2nd.png", printed=233),
    dict(rank=1, file="1st.png", printed=258),
]

SCENES = [
    ("title", 3.00), ("facts", 3.00),
    ("stat3", 1.60), ("shot3", 2.40),
    ("stat2", 1.60), ("shot2", 2.40),
    ("stat1", 1.60), ("shot1", 3.20),
    ("outro", 4.00),
]
ORD = {1: "1ST", 2: "2ND", 3: "3RD"}


def lead_stat(row, top3, sessions_total):
    """The one number that made this player's season, picked from the data.

    Written down, these go stale the moment a volume ends differently. Chosen
    by rule, the film describes whatever actually happened.
    """
    rate = row["wins"] / row["played"] if row["played"] else 0
    if row["titles"] == max(r["titles"] for r in top3) and row["titles"] > 0:
        n = row["titles"]
        return f"{n} NIGHT{'S' if n != 1 else ''} WON", "More than anyone in the series."
    if rate == max((r["wins"] / r["played"]) if r["played"] else 0 for r in top3):
        return f"{round(rate * 100)}% WIN RATE", f"{row['wins']} wins from {row['played']} matches."
    if row["nights"] >= sessions_total:
        return "EVERY NIGHT PLAYED", f"All {sessions_total}, start to finish."
    return f"{row['wins']} WINS", f"Across {row['nights']} nights."


def main():
    if not os.path.exists(STANDINGS):
        raise SystemExit(f"no standings at {STANDINGS} — run ops/blackout-standings.mjs first")
    D = json.load(open(STANDINGS))
    season = json.load(open(os.path.join(HERE, "blackout-season.json")))

    if D["played"] < D["sessionsTotal"] or D.get("remaining"):
        raise SystemExit(f"the season is not finished ({D['played']} of {D['sessionsTotal']} "
                         f"nights) — this film ends on a champion")

    top3 = D["table"][:3]
    # THE POSTERS ARE HAND-MADE, SO THEY ARE CHECKED. If somebody re-exports one
    # with the wrong total, the film must not quietly wrap it in figures that
    # disagree with it.
    for p in POSTERS:
        row = top3[p["rank"] - 1]
        if row["pts"] != p["printed"]:
            raise SystemExit(
                f"the {ORD[p['rank']]} poster has {p['printed']} points printed on it, but the "
                f"engine gives {row['name']} {row['pts']}.\n"
                f"  Fix the poster or the POSTERS table — do not ship a film that "
                f"contradicts the picture inside it.")
        if not os.path.exists(os.path.join(SHOTS, p["file"])):
            raise SystemExit(f"missing poster {os.path.join(SHOTS, p['file'])}")

    cards = []
    for p in POSTERS:
        row = top3[p["rank"] - 1]
        big, sub = lead_stat(row, top3, D["sessionsTotal"])
        cards.append(dict(
            rank=p["rank"], ord=ORD[p["rank"]], file=p["file"],
            name=row["name"].upper(), pts=row["pts"],
            big=big, sub=sub,
            # Earnings, split the way the app now splits them. A night win is a
            # voucher and the season prize is cash; merging them would tell a
            # player they have more of whichever they happen to need.
            voucher=row["titles"] * season["voucher"],
            cash=season["seasonPrizes"][p["rank"] - 1],
        ))

    starts, t = [], 0.0
    for _, d in SCENES:
        starts.append(t); t += d
    dur = t
    payload = json.dumps(dict(
        scenes=[s for s, _ in SCENES], starts=starts, dur=dur,
        cards={c["rank"]: c for c in cards},
        nights=D["sessionsTotal"], matches=D["matches"], players=D["playersIn"],
        pool=D["pool"], volume=D["volume"],
    ))

    html = TEMPLATE
    for k, v in {
        "__FACES__": font_bundle(), "__DATA__": payload,
        "__W__": str(W), "__H__": str(H),
        "__LIME__": LIME, "__MAGENTA__": MAGENTA, "__VOID__": VOID,
        "__INK__": INK, "__MUTED__": MUTED, "__UV__": UV,
        "__VOLUME__": D["volume"], "__HOST__": season["host"].upper(),
        "__CHAMP__": cards[-1]["name"], "__CHAMPPTS__": str(cards[-1]["pts"]),
    }.items():
        html = html.replace(k, v)

    with open(OUT, "w") as fh:
        fh.write(html)
    print(f"wrote {OUT}  ({len(html)/1024:.0f}KB)  {dur:.1f}s, {len(SCENES)} scenes")
    for c in cards:
        print(f"  {c['ord']}  {c['name']:<20} {c['pts']} pts  ·  {c['big']}  ·  "
              f"{c['voucher']} voucher + {c['cash']} cash")
    print(f"\nseason: {D['sessionsTotal']} nights · {D['matches']} matches · "
          f"{D['playersIn']} players · {D['pool']} OMR")
    print("\nnow:  python3.13 build-blackout-recap-audio.py "
          "&& node record-blackout-recap-video.mjs")


TEMPLATE = r"""<!doctype html><html lang="en"><head><meta charset="utf-8"><style>
__FACES__
*{margin:0;padding:0;box-sizing:border-box;border-radius:0}
html,body{width:__W__px;height:__H__px;overflow:hidden;background:__VOID__;color:__INK__;
  font-family:'Archivo',system-ui,sans-serif;-webkit-font-smoothing:antialiased}
body{position:relative}
.bg{position:absolute;inset:0;background:
  radial-gradient(ellipse 80% 42% at 84% 8%,rgba(255,46,136,.16),transparent),
  radial-gradient(ellipse 80% 40% at 14% 6%,rgba(198,255,0,.10),transparent),
  linear-gradient(180deg,#070707,__VOID__ 60%,#030303)}
.grid{position:absolute;inset:0;background-image:
  repeating-linear-gradient(0deg,rgba(198,255,0,.055) 0 2px,transparent 2px 64px),
  repeating-linear-gradient(90deg,rgba(198,255,0,.055) 0 2px,transparent 2px 64px)}
#flash{position:absolute;inset:0;background:__INK__;opacity:0;z-index:40}
.bars{position:absolute;left:0;right:0;height:0;background:__VOID__;z-index:30}
#barT{top:0}#barB{bottom:0}
.d{font-family:'Archivo';font-style:italic;font-variation-settings:'wdth' 125,'wght' 900;
  text-transform:uppercase;line-height:.86;letter-spacing:.004em}
.k{font-family:'JetBrains Mono',monospace;font-weight:700;text-transform:uppercase;
  letter-spacing:.28em;font-size:25px;color:__LIME__}

.scene{position:absolute;inset:0;padding:240px 76px 260px;display:none;
  flex-direction:column;justify-content:center;z-index:12}
.scene.on{display:flex}

#tt{font-size:150px;margin-top:38px}
#tt span{color:__LIME__}
#ts{font-size:33px;line-height:1.42;color:#B9B9B9;margin-top:30px;max-width:900px}

.facts{display:grid;grid-template-columns:1fr 1fr;gap:18px;margin-top:40px}
.fact{border:1px solid rgba(242,242,242,.14);background:rgba(242,242,242,.03);padding:26px 24px}
.fact b{display:block;font-family:'Archivo';font-style:italic;
  font-variation-settings:'wdth' 125,'wght' 900;font-size:72px;line-height:1;color:__LIME__}
.fact i{display:block;font-style:normal;font-family:'JetBrains Mono',monospace;
  font-weight:700;font-size:17px;letter-spacing:.2em;color:__MUTED__;margin-top:10px}

.rk{font-family:'Archivo';font-style:italic;font-variation-settings:'wdth' 125,'wght' 900;
  font-size:120px;line-height:1;color:__MAGENTA__}
.nm{font-size:76px;margin-top:10px}
.big{font-size:104px;margin-top:40px;color:__LIME__}
.sub{font-size:30px;color:#B9B9B9;margin-top:18px}
.earn{display:flex;gap:10px;margin-top:34px;font-family:'JetBrains Mono',monospace;
  font-weight:700;font-size:19px;letter-spacing:.14em}
.earn span{border:1px solid rgba(242,242,242,.18);padding:12px 18px}
.earn .v{color:__LIME__} .earn .c{color:__MAGENTA__}

/* The poster fills the frame and carries no type of its own from us. It
   already has the lockup, the name and the points on it. */
.shot{position:absolute;inset:0;z-index:14;display:none;overflow:hidden;background:__VOID__}
.shot.on{display:block}
.shot img{position:absolute;left:50%;top:50%;width:1080px;height:1920px;object-fit:cover;
  transform-origin:center}

#ot{font-size:118px;margin-top:34px}
#ot span{color:__LIME__}
#os{font-size:32px;line-height:1.4;color:#B9B9B9;margin-top:26px;max-width:900px}
#of{position:absolute;left:76px;right:76px;bottom:262px;
  font-family:'JetBrains Mono',monospace;font-weight:700;font-size:26px;
  letter-spacing:.16em;color:__LIME__}
#rail{position:absolute;left:76px;right:76px;bottom:196px;height:3px;
  background:rgba(242,242,242,.14);z-index:32}
#railfill{display:block;height:100%;width:0;background:__LIME__}
</style></head><body>
<div class="bg"></div><div class="grid"></div>
<div class="bars" id="barT"></div><div class="bars" id="barB"></div>
<div id="flash"></div><div id="rail"><span id="railfill"></span></div>

<div class="scene" id="s_title">
  <div class="k" id="t_k">Blackout Series &middot; __VOLUME__</div>
  <div class="d" id="tt">Nine nights.<br><span>One table.</span></div>
  <div id="ts">October 2026 at Urban Playground. This is how it finished.</div>
</div>

<div class="scene" id="s_facts">
  <div class="k" id="f_k">The season</div>
  <div class="facts" id="f_g"></div>
</div>

<div class="scene" id="s_stat3"></div>
<div class="scene" id="s_stat2"></div>
<div class="scene" id="s_stat1"></div>

<div class="shot" id="s_shot3"><img id="i3"></div>
<div class="shot" id="s_shot2"><img id="i2"></div>
<div class="shot" id="s_shot1"><img id="i1"></div>

<div class="scene" id="s_outro">
  <div class="k" id="o_k">Vol.8 champion</div>
  <div class="d" id="ot"><span>__CHAMP__</span><br>__CHAMPPTS__ points</div>
  <div id="os">Nine nights, one table, and it was his from the first.
    Vol.9 starts over at zero.</div>
  <div id="of">__HOST__</div>
</div>

<script>
const D = __DATA__;
const SC = D.scenes, ST = D.starts, DUR = D.dur;
const $ = id => document.getElementById(id);
const cl = (x, a, b) => x < a ? a : x > b ? b : x;
const ease = u => 1 - Math.pow(1 - cl(u, 0, 1), 3);
const rise = (el, u, px) => { if (!el) return;
  el.style.opacity = cl(u, 0, 1);
  el.style.transform = `translateY(${(1 - ease(u)) * (px === undefined ? 44 : px)}px)`; };

// Furniture built once, from the data.
$('f_g').innerHTML =
  [[D.nights, 'NIGHTS'], [D.matches, 'MATCHES'], [D.players, 'PLAYERS'], [D.pool + ' OMR', 'PAID OUT']]
  .map(([v, l]) => `<div class="fact"><b>${v}</b><i>${l}</i></div>`).join('');
for (const r of [1, 2, 3]) {
  const c = D.cards[r];
  $('s_stat' + r).innerHTML =
    `<div class="rk" id="r_rk${r}">${c.ord}</div>`
    + `<div class="d nm" id="r_nm${r}">${c.name}</div>`
    + `<div class="d big" id="r_bg${r}">${c.big}</div>`
    + `<div class="sub" id="r_sb${r}">${c.sub}</div>`
    + `<div class="earn" id="r_er${r}"><span class="v">${c.voucher} VOUCHER</span>`
    + `<span class="c">${c.cash} CASH</span></div>`;
  $('i' + r).src = 'podium/' + c.file;
}

function seek(t) {
  t = cl(t, 0, DUR);
  let i = 0;
  for (let k = 0; k < ST.length; k++) if (t >= ST[k]) i = k;
  const name = SC[i], s = t - ST[i];
  for (const k of SC) {
    const el = $('s_' + k);
    if (el) el.classList.toggle('on', k === name);
  }
  $('railfill').style.width = (t / DUR * 100) + '%';
  // The flash sits UNDER the letterbox; over it, it washes the bars too and
  // reads as a strobe rather than as a cut.
  $('flash').style.opacity = (i > 0 && s < 0.08) ? 0.26 * (1 - s / 0.08) : 0;
  const punch = Math.pow(1 - cl(s / 0.38, 0, 1), 3);
  $('barT').style.height = (26 + 14 * punch) + 'px';
  $('barB').style.height = (26 + 14 * punch) + 'px';

  if (name === 'title') {
    rise($('t_k'), s / 0.45, 18); rise($('tt'), (s - 0.25) / 0.7); rise($('ts'), (s - 0.75) / 0.7);
  } else if (name === 'facts') {
    rise($('f_k'), s / 0.4, 18);
    [...$('f_g').children].forEach((e, n) => rise(e, (s - 0.25 - n * 0.14) / 0.5, 26));
  } else if (name.startsWith('stat')) {
    const r = name.slice(4);
    rise($('r_rk' + r), s / 0.4, 20);
    rise($('r_nm' + r), (s - 0.15) / 0.5);
    rise($('r_bg' + r), (s - 0.4) / 0.55);
    rise($('r_sb' + r), (s - 0.7) / 0.5);
    rise($('r_er' + r), (s - 0.9) / 0.5, 22);
  } else if (name.startsWith('shot')) {
    const r = name.slice(4), img = $('i' + r);
    // A slow push, direction alternating so three cuts do not all drift the
    // same way. Nothing is drawn over the poster.
    const u = s / (ST[i + 1] !== undefined ? ST[i + 1] - ST[i] : 2.4);
    const inward = r !== '2';
    const k = inward ? 1.0 + 0.055 * u : 1.055 - 0.055 * u;
    img.style.transform = `translate(-50%,-50%) scale(${k.toFixed(4)})`;
    img.style.opacity = cl(s / 0.18, 0, 1);
  } else if (name === 'outro') {
    rise($('o_k'), s / 0.45, 18); rise($('ot'), (s - 0.3) / 0.75);
    rise($('os'), (s - 0.9) / 0.7); rise($('of'), (s - 1.5) / 0.7, 24);
  }
}
window.__seek = seek; window.__dur = DUR; window.__starts = ST; window.__scenes = SC;
seek(0);
</script>
</body></html>"""


if __name__ == "__main__":
    main()
