#!/usr/bin/env python3
"""56 National Series — the DOUBLE NIGHT cut. 1080x1920, 14.4s, five scenes.

Not a trim of the opening film. That one could argue nothing but the shape of
a season, because nothing had been played; this one is mid-season and has a
table, so it argues the table: who leads, how thin the gap is at the place
that pays, and that the next night is one of the three that count double.

EVERY FIGURE IS READ. The table comes from ops/national-standings.mjs, which
runs the app's own engine over the live state; the night, the time, the entry
and the prizes come from national-season.json.

IT REFUSES TO BUILD if the next unplayed night is not a double night, because
the cut says DOUBLE POINTS in 200px type — and it picks its own first word
(TONIGHT / TOMORROW / the weekday) from the calendar in MUSCAT, not from the
container's UTC clock, so a build at 11pm cannot be a day out.

IT NEVER SAYS WHAT A DOUBLED NIGHT IS WORTH. 2X skips the streak bonus, so
"every point counts twice" is very nearly true and still wrong. It prints the
biggest night actually recorded and lets the reader do the arithmetic.

  ssh urbanpadel 'curl -s localhost:3011/state' > $SP/na.json
  node ops/national-standings.mjs $SP/na.json $SP/na-standings.json
  python3 build-national-double-video.py            # AS_OF=2026-11-17 to pin the day
  CUT=$SP/national-double.cut.json python3.13 build-national-audio.py
  # SHORT=1 on the build for the 7-second cut (national-double-7s.*)
  PAGE=national-double.html NAME=national-double WAV=national-double.wav \\
      node record-national-video.mjs                # CONTACT=1 for a strip
"""
import datetime
import importlib.util
import json
import os
import re
import sys
from zoneinfo import ZoneInfo

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "ops"))
from font_bundle import bundle          # noqa: E402
from national_assets import assets      # noqa: E402

# The opening film's helpers, imported rather than copied: two copies of a
# date formatter is how two films end up writing the same night two ways.
_spec = importlib.util.spec_from_file_location(
    "nvideo", os.path.join(HERE, "build-national-video.py"))
NV = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(NV)
d, longish, check_arabic, WORDS, SP = NV.d, NV.longish, NV.check_arabic, NV.WORDS, NV.SP

OUT = os.path.join(SP, "national-double.html")
CUT = os.path.join(SP, "national-double.cut.json")
CAPS = os.path.join(HERE, "brand", "national", "posts", "DOUBLE-NIGHT-CAPTIONS.txt")
W, H = 1080, 1920

# 100bpm, so a beat is 0.6s and every cut lands on one.
DUR = 14.40
SCENES = [0.00, 2.40, 5.40, 8.40, 11.40]
BEATS = [0.00, 1.20, 2.40, 3.90, 5.40, 6.90, 8.40, 9.90, 11.40, 12.90]
HERO = [0.00, 2.40, 11.40]
# SHORT=1 — THE 7-SECOND CUT. The same five scenes on the same beat grid,
# not a different film: a reel that opens on a table nobody has time to read
# is worse than no table, so the scenes keep their order and the table and the
# ask keep the extra beat. Every entrance is written against the long cut's
# scene lengths (BASE) and the seek scales time by BASE/actual, so nothing in
# the short cut is still arriving when its scene ends.
BASE = [2.40, 3.00, 3.00, 3.00, 3.00]
SHORT = bool(os.environ.get("SHORT"))
if SHORT:
    DUR = 7.20
    SCENES = [0.00, 1.20, 2.40, 4.20, 5.40]
    BEATS = [0.00, 0.60, 1.20, 1.80, 2.40, 3.00, 3.60, 4.20, 4.80, 5.40, 6.00, 6.60]
    HERO = [0.00, 1.20, 5.40]
    OUT = os.path.join(SP, "national-double-7s.html")
    CUT = os.path.join(SP, "national-double-7s.cut.json")
FULLDAY = ["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY", "SUNDAY"]
ORD = {1: "1ST", 2: "2ND", 3: "3RD", 4: "4TH"}
ROSE = "#F2D0D3"


def main():
    cfg = json.load(open(os.path.join(HERE, "national-season.json"), encoding="utf-8"))
    st_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(SP, "na-standings.json")
    if not os.path.exists(st_path):
        raise SystemExit(f"no standings at {st_path} — run ops/national-standings.mjs first")
    ST = json.load(open(st_path, encoding="utf-8"))
    P, A = cfg["palette"], assets()

    today = (d(os.environ["AS_OF"]) if os.environ.get("AS_OF")
             else datetime.datetime.now(ZoneInfo("Asia/Muscat")).date())

    # ── the guards ──────────────────────────────────────────────────────────
    if not ST["remaining"]:
        raise SystemExit("the season is over — there is no next night to sell")
    night = ST["remaining"][0]
    if night not in cfg["doubleNights"]:
        raise SystemExit(f"the next night is {night}, which is not a double night "
                         f"({', '.join(cfg['doubleNights'])}). This cut says DOUBLE POINTS.")
    away = (d(night) - today).days
    if away < 0:
        raise SystemExit(f"{night} has passed and is not marked completed — "
                         "refresh the state before building")
    table = ST["table"][:4]
    if len(table) < 4:
        raise SystemExit("fewer than four players in the series — no table to show")
    n_night = cfg["nights"].index(night) + 1
    assert ST["played"] == n_night - 1, \
        f"{ST['played']} nights played but the next is night {n_night} — a night is missing"

    when = "TONIGHT" if away == 0 else "TOMORROW" if away == 1 else FULLDAY[d(night).weekday()]
    is_natday = night == cfg["nationalDay"]

    mt = re.search(r"(\d{1,2}(?::\d{2})?\s*(?:AM|PM))", cfg["schedule"], re.I)
    if not mt:
        raise SystemExit(f"no start time in schedule line {cfg['schedule']!r}")
    start = mt.group(1).upper()

    # THE HOOK IS READ OFF THE TABLE. The two gaps that matter are the lead
    # and the last place that pays; whichever is thinner is the story.
    n_paid = len(cfg["seasonPrizes"])
    gaps = [(table[0]["pts"] - table[1]["pts"], 1, 2, "THE LEAD"),
            (table[n_paid - 1]["pts"] - table[n_paid]["pts"], n_paid, n_paid + 1,
             "THE LAST PRIZE PLACE")]
    gap, ga, gb, gap_kicker = min(gaps, key=lambda g: g[0])
    gap_unit = "POINT" if gap == 1 else "POINTS"
    if gap == 0:
        gap_kicker, gap_unit = gap_kicker, "POINTS"

    tag = cfg["tagline"].strip()
    beats = [x.strip() for x in re.findall(r"[^.!?]+[.!?]", tag)]
    assert len(beats) == 2, f"tagline must be two sentences, got {tag!r}"

    # The night's landmark: the app cycles the list in order.
    lm = cfg["landmarks"][(n_night - 1) % len(cfg["landmarks"])]
    lm_art = A[lm["asset"] + "@white"]

    name_ar, natday_ar = cfg["nameAr"], cfg["nationalDayLabelAr"]
    check_arabic(cfg, [name_ar, natday_ar, lm["nameAr"]])

    pill_title = cfg["nationalDayLabel"] if is_natday else "DOUBLE POINTS NIGHT"
    pill_ar = natday_ar if is_natday else name_ar
    s2_kicker = ("THE ONE NIGHT THAT IS AN OCCASION" if is_natday
                 else f"NIGHT {n_night} OF {cfg['sessions']}")

    rows = "".join(
        f'<div class="tr"><div class="rk disp">{i + 1}</div>'
        f'<div class="nm"><span class="fitcell disp">{r["name"].upper()}</span></div>'
        f'<div class="pt disp" data-pts="{r["pts"]}">{r["pts"]}</div></div>'
        for i, r in enumerate(table))

    style = f"""
{bundle()}
*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{width:{W}px;height:{H}px;overflow:hidden;background:{P['bg']};
  font-family:'Archivo',system-ui,sans-serif;-webkit-font-smoothing:antialiased;color:{P['ivory']}}}
body{{position:relative}}
#tile{{position:absolute;inset:0;opacity:.18;pointer-events:none;z-index:0;
  background-image:url("{A['khanjar']}");background-size:340px 340px}}
.band{{position:absolute;left:36px;right:36px;height:56px;border-radius:28px;pointer-events:none;
  z-index:3;background-color:{P['deep']};background-image:url("{A['masar']}");
  background-size:100px 56px;background-repeat:repeat-x}}
.band.t{{top:18px}} .band.b{{bottom:18px;transform:scaleY(-1)}}
.scene{{position:absolute;inset:0;z-index:2}}
.blk{{position:absolute;left:0;right:0;text-align:center}}
.disp{{font-style:italic;font-variation-settings:'wdth' 125,'wght' 900;line-height:.88;
  text-transform:uppercase}}
.mono{{font-family:'JetBrains Mono',monospace;font-weight:700;text-transform:uppercase}}
.kufi{{font-family:'Noto Kufi Arabic',sans-serif;font-weight:700}}
.arch{{background:{P['ivory']};color:{P['ink']};
  border-radius:50% 50% 28px 28px / 34% 34% 28px 28px;
  box-shadow:0 0 0 7px {P['bg']},0 0 0 11px {P['ivory']};overflow:hidden}}
.flag{{display:inline-flex;align-items:center;justify-content:center;border-radius:10px;
  padding:12px 30px 12px 46px;
  background-image:linear-gradient(90deg,{P['flag']} 0 22px,transparent 22px),
    linear-gradient(180deg,#FFFFFF 0 34%,{P['flag']} 34% 66%,{P['green']} 66% 100%);
  box-shadow:0 0 0 4px {P['ink']}}}
.flag .n{{color:#FFFFFF;-webkit-text-stroke:4px {P['ink']};paint-order:stroke fill;letter-spacing:-.02em}}
.med{{border-radius:50%;background-color:{P['bg']};background-repeat:no-repeat;
  background-position:center 54%;background-size:62% auto;
  box-shadow:0 0 0 3px {P['ivory']},0 0 0 7px {P['green']}}}
.k{{font-size:26px;letter-spacing:.3em;color:{ROSE}}}

/* 1 · the hook */
#s1a{{top:470px}}
#s1k{{top:740px}}
#s1b{{top:810px;font-size:210px}}
#s1c{{top:1070px;font-size:62px}}
#s1d{{top:1230px;font-size:44px;color:{ROSE}}}

/* 2 · the occasion. GREEN IS SPENT HERE: the pill and the disc, nowhere else
   as a fill. */
#s2a{{top:430px}}
#s2pill{{position:absolute;top:510px;left:52px;right:52px;z-index:2;background:{P['green']};
  border-radius:999px;padding:32px 34px 32px 48px;display:flex;align-items:center;gap:22px}}
#s2pill .l{{flex:1 1 auto;min-width:0;text-align:left}}
#s2when{{font-size:26px;letter-spacing:.14em;color:#FFFFFF}}
#s2t{{font-size:46px;margin-top:8px;color:#FFFFFF;white-space:nowrap}}
#s2ar{{font-size:28px;margin-top:12px;color:#FFFFFF}}
#s2x{{flex:0 0 auto;width:120px;height:120px;border-radius:50%;background:#FFFFFF;color:{P['green']};
  display:flex;align-items:center;justify-content:center;font-size:48px}}
#s2b{{top:900px;font-size:230px}}
#s2c{{top:1120px;font-size:230px}}
#s2d{{top:1400px;font-size:30px;letter-spacing:.2em;color:{ROSE}}}

/* 3 · the table, on the plate you read */
#s3med{{position:absolute;top:250px;left:50%;margin-left:-95px;width:190px;height:190px;z-index:2;
  background-image:url("{lm_art}")}}
#s3a{{top:500px}}
#s3rows{{position:absolute;top:580px;left:64px;right:64px;z-index:2;background:{P['ivory']};
  border-radius:44px;box-shadow:0 0 0 7px {P['bg']},0 0 0 11px {P['ivory']};padding:14px 34px}}
.tr{{display:flex;align-items:center;gap:24px;height:158px;border-top:2px solid rgba(26,10,12,.10)}}
.tr:first-child{{border-top:0}}
.rk{{flex:0 0 84px;width:84px;height:84px;border-radius:50%;background:{P['bg']};color:{P['ivory']};
  display:flex;align-items:center;justify-content:center;font-size:44px}}
.tr:first-child .rk{{background:{P['green']};color:#FFFFFF}}
.nm{{flex:1 1 0;min-width:0;text-align:left;font-size:60px;color:{P['ink']};white-space:nowrap}}
.pt{{flex:0 0 auto;font-size:84px;color:{P['bg']};min-width:170px;text-align:right}}
#s3c{{top:1330px;font-size:28px;letter-spacing:.16em;color:{ROSE}}}
#s3d{{top:1400px;font-size:30px;letter-spacing:.2em;color:{P['ivory']}}}

/* 4 · the gap */
#s4a{{top:430px}}
#s4arch{{position:absolute;top:510px;left:150px;right:150px;height:520px;z-index:2;display:flex;
  flex-direction:column;align-items:center;justify-content:center;gap:30px;padding-top:50px}}
#s4n{{font-size:250px;color:{P['bg']};line-height:.84}}
#s4u{{font-size:44px;letter-spacing:.22em;color:{P['ink']}}}
#s4k{{font-size:25px;letter-spacing:.2em;color:{P['muted']}}}
#s4b{{top:1170px;font-size:60px;white-space:nowrap}}
#s4c{{top:1320px;font-size:120px}}
#s4d{{top:1500px;font-size:34px;letter-spacing:.2em;color:{ROSE}}}

/* 5 · the ask */
#s5a{{top:400px}}
#s5b{{top:480px;font-size:150px}}
#s5c{{top:690px;font-size:60px}}
#s5arch{{position:absolute;top:860px;left:110px;right:110px;height:330px;z-index:2;display:flex;
  flex-direction:column;align-items:center;justify-content:center;gap:10px;padding-top:30px}}
#s5t1{{font-size:88px;color:{P['ink']}}}
#s5t2{{font-size:88px;color:{P['bg']}}}
#s5d{{top:1290px;font-size:46px}}
#s5e{{top:1400px;font-size:32px;letter-spacing:.2em;color:{ROSE}}}
"""

    body = f"""
<div id="tile"></div>
<div class="band t"></div><div class="band b"></div>

<div class="scene" id="s1">
  <div class="blk" id="s1a"><span class="flag"><span class="n disp" style="font-size:150px">56</span></span></div>
  <div class="blk mono k" id="s1k">{cfg['name']} &middot; NIGHT {n_night} OF {cfg['sessions']}</div>
  <div class="blk disp" id="s1b"><span class="fitspan">{when}</span></div>
  <div class="blk disp" id="s1c">{longish(night)} &middot; {start}</div>
  <div class="blk kufi" id="s1d">{name_ar}</div>
</div>

<div class="scene" id="s2">
  <div class="blk mono k" id="s2a">{s2_kicker}</div>
  <div id="s2pill">
    <div class="l">
      <div class="mono" id="s2when">{longish(night)} &middot; {start}</div>
      <div class="disp" id="s2t">{pill_title}</div>
      <div class="kufi" id="s2ar">{pill_ar}</div>
    </div>
    <div class="disp" id="s2x">2X</div>
  </div>
  <div class="blk disp" id="s2b"><span class="fitspan">DOUBLE</span></div>
  <div class="blk disp" id="s2c"><span class="fitspan">POINTS</span></div>
  <div class="blk mono" id="s2d">ONE OF {WORDS[len(cfg['doubleNights'])]} THIS SEASON</div>
</div>

<div class="scene" id="s3">
  <div class="med" id="s3med"></div>
  <div class="blk mono k" id="s3a">THE TABLE AFTER {WORDS[ST['played']]} NIGHT{'S' if ST['played'] != 1 else ''}</div>
  <div id="s3rows">{rows}</div>
  <div class="blk mono" id="s3c">TOP {WORDS[n_paid]} SHARE</div>
  <div class="blk mono" id="s3d">{' &middot; '.join(str(x) for x in cfg['seasonPrizes'])} OMR</div>
</div>

<div class="scene" id="s4">
  <div class="blk mono k" id="s4a">{gap_kicker}</div>
  <div class="arch" id="s4arch">
    <div class="disp" id="s4n">{gap}</div>
    <div class="mono" id="s4u">{gap_unit}</div>
    <div class="mono" id="s4k">BETWEEN {ORD[ga]} AND {ORD[gb]}</div>
  </div>
  <div class="blk disp" id="s4b">BIGGEST NIGHT SO FAR</div>
  <div class="blk disp" id="s4c">+{ST['bestNight']}</div>
  <div class="blk mono" id="s4d">{when} PAYS DOUBLE</div>
</div>

<div class="scene" id="s5">
  <div class="blk mono k" id="s5a">{cfg['name']}</div>
  <div class="blk disp" id="s5b"><span class="fitspan">{longish(night)}</span></div>
  <div class="blk disp" id="s5c">{start} &middot; {cfg['entry']} OMR</div>
  <div class="arch" id="s5arch">
    <div class="disp" id="s5t1">{beats[0]}</div>
    <div class="disp" id="s5t2">{beats[1]}</div>
  </div>
  <div class="blk disp" id="s5d">DROP YOUR NAME IN THE GROUP</div>
  <div class="blk mono" id="s5e">{cfg['host']}</div>
</div>
"""

    js = """
<script>
const DUR = %(dur)s, SCENES = %(scenes)s, BEATS = %(beats)s, HERO = %(hero)s, GAP = %(gap)s, BASE = %(base)s;
window.__dur = DUR; window.__scenes = SCENES;
const E = id => document.getElementById(id);
const clamp = (x,a,b) => x < a ? a : x > b ? b : x;
const ease  = u => 1 - Math.pow(1 - clamp(u,0,1), 3);
function enter(el, u, rise, wide) {
  const e = ease(u);
  el.style.opacity = clamp(u * 1.6, 0, 1);
  el.style.transform = 'translateY(' + ((1 - e) * (rise === undefined ? 34 : rise)).toFixed(2) + 'px)';
  if (wide) {
    const s = el.querySelector('.fitspan') || el;
    s.style.fontVariationSettings = "'wdth' " + (84 + 41 * e).toFixed(1) + ",'wght' 900";
  }
}
// clamped where it is made: the window opens 20ms early, so (1-u)^3 can pass one
function energy(t) {
  let e = 0;
  for (const b of BEATS) {
    const u = (t - (b - 0.02)) / 0.30;
    if (u >= 0 && u <= 1) e = Math.max(e, Math.pow(1 - clamp(u,0,1), 3) * (HERO.includes(b) ? 1 : 0.55));
  }
  return clamp(e, 0, 1);
}
// Every scene visible while it measures: a hidden box measures 0 and the loop
// would run every headline in it to the floor.
function fitAll() {
  const scenes = [...document.querySelectorAll('.scene')];
  const was = scenes.map(el => el.style.display);
  scenes.forEach(el => { el.style.display = 'block'; });
  for (const s of document.querySelectorAll('.fitspan')) {
    const box = s.parentElement, room = box.clientWidth - 96;
    let px = parseFloat(getComputedStyle(box).fontSize);
    s.style.whiteSpace = 'nowrap'; s.style.display = 'inline-block';
    // MEASURE AT FULL WIDTH. __seek(0) has already run, so a headline in the
    // opening scene is sitting at the START of its entrance — 'wdth' 84 — and
    // fitting it there fits the narrow letters: TOMORROW passed at 210px and
    // then widened to 1362px of a 1080px frame.
    s.style.fontVariationSettings = "'wdth' 125,'wght' 900";
    if (room <= 0) throw new Error('fit: ' + box.id + ' has no width');
    while (s.getBoundingClientRect().width > room && px > 10) { px -= 2; box.style.fontSize = px + 'px'; }
    if (px <= 10) throw new Error('fit: ' + box.id + ' hit the floor');
  }
  // .fitcell is the CELL-width pass. The name cell is `flex:1 1 0;min-width:0`,
  // so its width does not depend on what is in it and is safe to measure
  // against — the frame-width pass above must never go on a flex cell.
  let cellpx = 1e9;
  const cells = [...document.querySelectorAll('.fitcell')];
  for (const s of cells) {
    const box = s.parentElement; let px = parseFloat(getComputedStyle(box).fontSize);
    s.style.display = 'inline-block';
    while (s.getBoundingClientRect().width > box.clientWidth - 6 && px > 20) { px -= 1; box.style.fontSize = px + 'px'; }
    cellpx = Math.min(cellpx, px);
  }
  // one size for the whole table: four names at four sizes reads as four tables
  for (const s of cells) s.parentElement.style.fontSize = cellpx + 'px';
  scenes.forEach((el, k) => { el.style.display = was[k]; });
}
function sceneAt(t) { let i = 0; for (let k = 0; k < SCENES.length; k++) if (t >= SCENES[k]) i = k; return i; }

window.__seek = function (t) {
  t = clamp(t, 0, DUR);
  const i = sceneAt(t), t0 = SCENES[i], e = energy(t);
  const len = ((i + 1 < SCENES.length) ? SCENES[i + 1] : DUR) - t0;
  // scene-local time on the LONG cut's clock; a little faster still, so a
  // short scene holds its settled frame for most of its length
  const S = (t - t0) * Math.max(1, BASE[i] / len * (len < BASE[i] ? 1.25 : 1));
  document.querySelectorAll('.scene').forEach((el, k) => { el.style.display = (k === i) ? 'block' : 'none'; });
  E('tile').style.opacity = (0.18 + 0.10 * e).toFixed(3);
  E('tile').style.backgroundSize = (340 + 26 * e).toFixed(1) + 'px ' + (340 + 26 * e).toFixed(1) + 'px';
  for (const b of document.querySelectorAll('.band')) b.style.opacity = (0.82 + 0.18 * e).toFixed(3);

  if (i === 0) {
    enter(E('s1a'), S / 0.55, 26);
    enter(E('s1k'), (S - 0.14) / 0.50, 16);
    enter(E('s1b'), (S - 0.20) / 0.65, 40, true);
    enter(E('s1c'), (S - 0.48) / 0.55, 24);
    enter(E('s1d'), (S - 0.70) / 0.55, 18);
    E('s1a').style.transform += ' scale(' + (1 + 0.035 * e).toFixed(4) + ')';
  } else if (i === 1) {
    enter(E('s2a'), S / 0.45, 16);
    enter(E('s2pill'), (S - 0.10) / 0.60, 34);
    enter(E('s2b'), (S - 0.55) / 0.60, 40, true);
    enter(E('s2c'), (S - 0.80) / 0.60, 40, true);
    enter(E('s2d'), (S - 1.30) / 0.55, 18);
    E('s2x').style.transform = 'scale(' + (1 + 0.10 * e).toFixed(4) + ')';
  } else if (i === 2) {
    enter(E('s3med'), S / 0.55, 20);
    E('s3med').style.transform += ' scale(' + (1 + 0.05 * e).toFixed(4) + ')';
    enter(E('s3a'), (S - 0.12) / 0.50, 16);
    enter(E('s3rows'), (S - 0.20) / 0.60, 30);
    // rows land in turn and their points count up to the engine's totals
    document.querySelectorAll('#s3rows .tr').forEach((el, k) => {
      const uu = (S - 0.40 - k * 0.16) / 0.50;
      el.style.opacity = clamp(uu * 1.7, 0, 1);
      const pt = el.querySelector('.pt');
      pt.textContent = Math.round(+pt.dataset.pts * ease((S - 0.45 - k * 0.16) / 0.85));
    });
    enter(E('s3c'), (S - 1.45) / 0.50, 16);
    enter(E('s3d'), (S - 1.60) / 0.50, 16);
  } else if (i === 3) {
    enter(E('s4a'), S / 0.45, 16);
    enter(E('s4arch'), (S - 0.12) / 0.65, 38);
    E('s4n').textContent = Math.round(GAP * ease((S - 0.20) / 0.80));
    enter(E('s4b'), (S - 1.10) / 0.55, 26);
    enter(E('s4c'), (S - 1.30) / 0.60, 34, true);
    enter(E('s4d'), (S - 1.70) / 0.55, 18);
  } else {
    enter(E('s5a'), S / 0.45, 16);
    enter(E('s5b'), (S - 0.10) / 0.65, 40, true);
    enter(E('s5c'), (S - 0.36) / 0.55, 26);
    enter(E('s5arch'), (S - 0.60) / 0.70, 40);
    enter(E('s5d'), (S - 1.05) / 0.55, 22);
    enter(E('s5e'), (S - 1.25) / 0.55, 18);
    E('s5arch').style.transform += ' scale(' + (1 + 0.02 * e).toFixed(4) + ')';
  }
};
document.fonts.ready.then(() => { fitAll(); window.__seek(0); window.__ready = true; });
window.__seek(0);
</script>
""" % {"dur": DUR, "scenes": json.dumps(SCENES), "beats": json.dumps(BEATS),
       "hero": json.dumps(HERO), "gap": gap, "base": json.dumps(BASE)}

    html = ("<!doctype html><html><head><meta charset='utf-8'>\n<style>"
            + style + "</style></head><body>\n" + body + js + "\n</body></html>")
    os.makedirs(SP, exist_ok=True)
    open(OUT, "w", encoding="utf-8").write(html)
    # ONE TABLE, TWO MEDIA: the bed reads this rather than a second copy.
    json.dump({"dur": DUR, "scenes": SCENES, "beats": BEATS, "hero": HERO,
               "wav": os.path.join(SP, "video", "national-double-7s.wav" if SHORT else "national-double.wav")}, open(CUT, "w"))

    # ── captions, from the same figures ─────────────────────────────────────
    x = d(night)
    nice = f"{['Mon','Tue','Wed','Thu','Fri','Sat','Sun'][x.weekday()]} {x.day} {cfg['month'][:3]}"
    lead = when.capitalize() if away <= 1 else f"This {when.capitalize()}"
    occasion = (f"{cfg['nationalDayLabel'].title()} — {natday_ar}" if is_natday
                else f"Night {n_night} of {cfg['sessions']}")
    top = "\n".join(f"{i + 1}. {r['name']} — {r['pts']}" for i, r in enumerate(table))
    gap_line = (f"{gap} {gap_unit.lower()} between {ORD[ga].lower()} and {ORD[gb].lower()}"
                + (" — and only the top " + WORDS[n_paid].lower() + " are paid." if ga == n_paid else "."))
    cap = f"""{cfg['name']} — double night cut ({nice})
{'=' * 54}
1080x1920 · {DUR:.1f}s · built {today} for a night {away} day(s) away, so it opens on "{when}"
Table from the app's own engine after {ST['played']} nights; every figure is read.

— WHATSAPP —

🇴🇲 *{lead}: DOUBLE POINTS.*

{occasion}. {nice}, {start}.

The table after {WORDS[ST['played']].lower()} nights:
{top}

{gap_line} The biggest night anyone has had so far is +{ST['bestNight']}, and this one pays double.

{cfg['entry']} OMR to play. Drop your name in the group.
{cfg['host']}

— INSTAGRAM —

{lead}, the points are double. {occasion}.

{table[0]['name']} leads on {table[0]['pts']}, {table[1]['name']} is on {table[1]['pts']}, and there {'is' if gap == 1 else 'are'} {gap_line}

{nice} · {start} · {cfg['entry']} OMR. {tag}

#urbanplayground #padel #oman #56nationalseries #العيد_الوطني #عمان
"""
    os.makedirs(os.path.dirname(CAPS), exist_ok=True)
    if not SHORT:      # one caption file; the short cut posts with the same words
        open(CAPS, "w", encoding="utf-8").write(cap)

    print(f"built {OUT}  {len(html)/1024:.0f}KB  {DUR}s")
    print(f"  night {n_night} is {longish(night)}, {away} day(s) from {today} (Muscat) -> \"{when}\"")
    print(f"  table: " + ", ".join(f"{r['name']} {r['pts']}" for r in table))
    print(f"  hook: {gap} {gap_unit} between {ORD[ga]} and {ORD[gb]} ({gap_kicker})  ·  best night +{ST['bestNight']}")
    print(f"  landmark {lm['nameEn']}  ·  captions {CAPS}")


if __name__ == "__main__":
    main()
