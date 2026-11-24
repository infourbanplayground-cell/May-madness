#!/usr/bin/env python3
"""56 National Series — the FINAL ROUND cut. 1080x1920, 14.4s, five scenes.

The last night of the season, and the only one where the season prizes are on
the table. So it argues the money and the race for it: FINAL ROUND, what the
top three take, the table, how few points cover the paid places, and the date.

EVERY FIGURE IS READ. The table comes from ops/national-standings.mjs (the
app's own engine over the live state); the night, the time, the entry and the
prizes from national-season.json. The hook is chosen from the table: the points
that cover the paid places, plus the thinner of the two gaps inside them.

IT REFUSES TO BUILD unless exactly ONE night remains, it is the finals date
and it is a double night — the cut says FINAL ROUND and DOUBLE in 200px type.
Its first word (TONIGHT / TOMORROW / the weekday) comes from the calendar in
MUSCAT, not the container's UTC clock.

IT NEVER SAYS WHAT A DOUBLED NIGHT IS WORTH (2X skips the streak bonus). It
prints the biggest night actually recorded beside the spread, and the reader
does the arithmetic. Nor does it say anyone is "out of it": that is a claim
about the future the table cannot make.

The motion engine (reveal / open / pop, scene clear-out, fit passes) is the
double-night cut's, copied at generation time from build-national-double-video.py.

  ssh urbanpadel 'curl -s localhost:3011/state' > $SP/na.json
  node ops/national-standings.mjs $SP/na.json $SP/na-standings.json
  python3 build-national-lastround-video.py         # AS_OF=2026-11-29 to pin the day; SHORT=1 for 7.2s
  CUT=$SP/national-lastround.cut.json python3.13 build-national-audio.py
  PAGE=national-lastround.html NAME=national-lastround WAV=national-lastround.wav \\
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

_spec = importlib.util.spec_from_file_location(
    "nvideo", os.path.join(HERE, "build-national-video.py"))
NV = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(NV)
d, longish, check_arabic, WORDS, SP = NV.d, NV.longish, NV.check_arabic, NV.WORDS, NV.SP

OUT = os.path.join(SP, "national-lastround.html")
CUT = os.path.join(SP, "national-lastround.cut.json")
CAPS = os.path.join(HERE, "brand", "national", "posts", "FINAL-ROUND-CAPTIONS.txt")
W, H = 1080, 1920
# Six scenes: FINAL ROUND, the prizes, the table, the spread, HOW IT SHAPED UP
# (the race chart, owner 24 Nov: "add a graph showing how the leaderboard
# shaped up"), and the ask.
DUR = 17.70
SCENES = [0.00, 2.40, 5.40, 8.40, 11.40, 14.70]
BEATS = [0.00, 1.20, 2.40, 3.90, 5.40, 6.90, 8.40, 9.90, 11.40, 12.60, 13.80, 14.70, 16.20]
HERO = [0.00, 2.40, 8.40, 14.70]
BASE = [2.40, 3.00, 3.00, 3.00, 3.30, 3.00]
SHORT = bool(os.environ.get("SHORT"))
if SHORT:
    DUR = 9.00
    SCENES = [0.00, 1.20, 2.40, 4.20, 5.40, 7.20]
    BEATS = [0.00, 0.60, 1.20, 1.80, 2.40, 3.00, 3.60, 4.20, 4.80, 5.40, 6.00, 6.60, 7.20, 7.80, 8.40]
    HERO = [0.00, 1.20, 4.20, 7.20]
    OUT = os.path.join(SP, "national-lastround-7s.html")
    CUT = os.path.join(SP, "national-lastround-7s.cut.json")
FULLDAY = ["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY", "SUNDAY"]
ORD = {1: "1ST", 2: "2ND", 3: "3RD", 4: "4TH", 5: "5TH"}
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

    # ── the guards: this cut's headline must be TRUE ────────────────────────
    if len(ST["remaining"]) != 1:
        raise SystemExit(f"{len(ST['remaining'])} nights remain — this cut says FINAL ROUND")
    night = ST["remaining"][0]
    if night != cfg["finalsDate"]:
        raise SystemExit(f"the last night left is {night}, not the finals date {cfg['finalsDate']}")
    if night not in cfg["doubleNights"]:
        raise SystemExit(f"{night} is not a double night — this cut says DOUBLE")
    away = (d(night) - today).days
    if away < 0:
        raise SystemExit(f"{night} has passed and is not marked completed — refresh the state")
    n_paid = len(cfg["seasonPrizes"])
    table = ST["table"][:n_paid + 2]
    if len(table) < n_paid + 1:
        raise SystemExit("not enough players in the series to show the race")
    n_night = cfg["nights"].index(night) + 1
    assert n_night == cfg["sessions"], f"the finals date is night {n_night} of {cfg['sessions']}"
    assert ST["played"] == n_night - 1, f"{ST['played']} nights played before night {n_night}"

    when = "TONIGHT" if away == 0 else "TOMORROW" if away == 1 else FULLDAY[d(night).weekday()]
    mt = re.search(r"(\d{1,2}(?::\d{2})?\s*(?:AM|PM))", cfg["schedule"], re.I)
    if not mt:
        raise SystemExit(f"no start time in schedule line {cfg['schedule']!r}")
    start = mt.group(1).upper()
    tag = cfg["tagline"].strip()
    beats = [x.strip() for x in re.findall(r"[^.!?]+[.!?]", tag)]
    assert len(beats) == 2, f"tagline must be two sentences, got {tag!r}"
    name_ar = cfg["nameAr"]
    # the finals night's landmark: the app cycles the list in order
    lm = cfg["landmarks"][(n_night - 1) % len(cfg["landmarks"])]
    lm_art = A[lm["asset"] + "@white"]
    check_arabic(cfg, [name_ar, lm["nameAr"]])

    # ── the hook, read off the table ────────────────────────────────────────
    spread = table[0]["pts"] - table[n_paid - 1]["pts"]        # what covers the paid places
    inner = min(((table[i]["pts"] - table[i + 1]["pts"], i + 1, i + 2) for i in range(n_paid - 1)), key=lambda g: g[0])
    chase = table[n_paid - 1]["pts"] - table[n_paid]["pts"]      # first place outside the money
    unit = lambda n: "POINT" if n == 1 else "POINTS"
    prizes = cfg["seasonPrizes"]

    # ── HOW IT SHAPED UP: the race chart ───────────────────────────────────
    # Every point is the app's engine re-run over the first n nights
    # (ops/national-standings.mjs), never a running sum. The lines are the top
    # five on the table; the lead line is read over EVERYBODY (ST['leaders']),
    # so "went top on night n" cannot be an artefact of which five are drawn.
    raceby = {r["id"]: r for r in ST["race"]}
    lines = [raceby[r["id"]] for r in table[:5] if r["id"] in raceby]
    assert len(lines) == 5, "the race does not cover the top five"
    L = ST["leaders"]
    changes = sum(1 for a, b in zip(L, L[1:]) if a["id"] != b["id"])
    holders = len({x["id"] for x in L})
    ldr = L[-1]
    since = len(L)
    while since > 1 and L[since - 2]["id"] == ldr["id"]:
        since -= 1
    lead_line = (f"{ldr['name'].upper()} WENT TOP ON NIGHT {since}" if since == len(L)
                 else f"{ldr['name'].upper()} HAS LED SINCE NIGHT {since}")
    VW, VH = 952, 820
    X0, X1, Y0, Y1 = 78, 600, 48, 720          # plot box inside the plate
    top = max(max(r["pts"]) for r in lines)
    ymax = (top // 50 + 1) * 50
    nN = ST["played"]
    xa = lambda i: X0 + (X1 - X0) * i / max(1, nN - 1)
    ya = lambda v: Y1 - (Y1 - Y0) * v / ymax
    INK = [P["bg"], P["green"], P["ink"], P["muted"], P["muted"]]
    DASH = [None, None, None, None, "14 10"]
    grid = "".join(f'<line x1="{X0}" x2="{X1}" y1="{ya(v):.1f}" y2="{ya(v):.1f}" stroke="rgba(26,10,12,.10)" stroke-width="2"/>'
                   f'<text x="{X0 - 14}" y="{ya(v) + 8:.1f}" text-anchor="end" class="ax">{v}</text>'
                   for v in range(0, ymax + 1, 50 if ymax <= 250 else 100))
    xlab = "".join(f'<text x="{xa(i):.1f}" y="{Y1 + 46}" text-anchor="middle" class="ax">N{i + 1}</text>' for i in range(nN))
    paths, dots, ends = [], [], []
    for k, r in enumerate(lines):
        pts = [(xa(i), ya(v)) for i, v in enumerate(r["pts"]) if i >= r["from"]]
        dpath = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts)
        dash = f' data-dash="{DASH[k]}"' if DASH[k] else ""
        paths.append(f'<path class="rl" d="{dpath}" pathLength="1" fill="none" stroke="{INK[k]}" stroke-width="{9 if k == 0 else 6}"'
                     f' stroke-linejoin="round" stroke-linecap="round"{dash}/>')
        for j, (x, y) in enumerate(pts):
            dots.append(f'<circle class="rd" data-at="{(j / max(1, len(pts) - 1)):.3f}" cx="{x:.1f}" cy="{y:.1f}" r="{11 if j == len(pts) - 1 else 6}" fill="{INK[k]}"/>')
        ends.append([pts[-1][1], k, r])
    # end labels never touch: sorted by height, each at least 46px under the last
    ends.sort()
    for i in range(1, len(ends)):
        ends[i][0] = max(ends[i][0], ends[i - 1][0] + 46)
    if ends[-1][0] > Y1 + 4:                   # pushed off the bottom: shift the stack up
        shift = ends[-1][0] - (Y1 + 4)
        for e in ends:
            e[0] -= shift
    labels = "".join(
        f'<g class="rlab" data-k="{k}"><line x1="{X1 + 14}" x2="{X1 + 34}" y1="{ya(r["pts"][-1]):.1f}" y2="{yy:.1f}" stroke="{INK[k]}" stroke-width="3"/>'
        f'<text x="{X1 + 44}" y="{yy + 10:.1f}" class="nm2" fill="{P["ink"]}">{r["name"].upper()}'
        f'<tspan class="pv" fill="{INK[k] if k < 3 else P["ink"]}" dx="12">{r["pts"][-1]}</tspan></text></g>'
        for yy, k, r in ends)
    chart = (f'<svg id="s6svg" viewBox="0 0 {VW} {VH}" width="{VW}" height="{VH}">{grid}{xlab}'
             f'{"".join(paths)}{"".join(dots)}{labels}</svg>')

    rows = "".join(
        f'<div class="tr{" paid" if i < n_paid else ""}"><div class="rk disp">{i + 1}</div>'
        f'<div class="nm"><span class="fitcell disp">{r["name"].upper()}</span></div>'
        f'<div class="pt disp" data-pts="{r["pts"]}">{r["pts"]}</div></div>'
        for i, r in enumerate(table[:5]))
    money = "".join(
        f'<div class="mr"><span class="mo mono">{ORD[i + 1]}</span><span class="ma disp">{p}</span>'
        f'<span class="mu mono">OMR</span></div>' for i, p in enumerate(prizes))

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

/* 1 · FINAL ROUND */
#s1a{{top:370px}}
#s1k{{top:630px}}
#s1b{{top:700px;font-size:230px}}
#s1c{{top:960px;font-size:230px}}
#s1d{{top:1270px;font-size:56px}}
#s1e{{top:1380px;font-size:44px;color:{ROSE}}}

/* 2 · the money, on the plate you read, under the finals night's landmark */
#s2med{{position:absolute;top:210px;left:50%;margin-left:-90px;width:180px;height:180px;z-index:2;
  background-image:url("{lm_art}")}}
#s2a{{top:420px}}
#s2plate{{position:absolute;top:500px;left:90px;right:90px;z-index:2;background:{P['ivory']};
  border-radius:44px;box-shadow:0 0 0 7px {P['bg']},0 0 0 11px {P['ivory']};padding:30px 50px}}
.mr{{display:flex;align-items:baseline;gap:26px;height:170px;align-items:center;border-top:2px solid rgba(26,10,12,.10)}}
.mr:first-child{{border-top:0}}
.mo{{flex:0 0 120px;font-size:40px;letter-spacing:.1em;color:{P['muted']}}}
.ma{{font-size:150px;color:{P['bg']};flex:1 1 auto;text-align:right}}
.mu{{font-size:34px;letter-spacing:.14em;color:{P['ink']}}}
#s2b{{top:1110px;font-size:64px}}
#s2c{{top:1200px;font-size:34px;letter-spacing:.2em;color:{ROSE}}}

/* 3 · the table: the paid places lit, the chase dimmed */
#s3a{{top:300px}}
#s3rows{{position:absolute;top:380px;left:64px;right:64px;z-index:2;background:{P['ivory']};
  border-radius:44px;box-shadow:0 0 0 7px {P['bg']},0 0 0 11px {P['ivory']};padding:14px 34px}}
.tr{{display:flex;align-items:center;gap:24px;height:150px;border-top:2px solid rgba(26,10,12,.10)}}
.tr:first-child{{border-top:0}}
.rk{{flex:0 0 84px;width:84px;height:84px;border-radius:50%;background:{P['muted']};color:{P['ivory']};
  display:flex;align-items:center;justify-content:center;font-size:44px}}
.tr.paid .rk{{background:{P['bg']}}}
.tr:first-child .rk{{background:{P['green']};color:#FFFFFF}}
.nm{{flex:1 1 0;min-width:0;text-align:left;font-size:58px;color:{P['ink']};white-space:nowrap}}
.pt{{flex:0 0 auto;font-size:80px;color:{P['bg']};min-width:170px;text-align:right}}
.tr:not(.paid) .nm, .tr:not(.paid) .pt{{opacity:.5}}
#s3c{{top:1230px;font-size:28px;letter-spacing:.16em;color:{ROSE}}}
#s3d{{top:1300px;font-size:30px;letter-spacing:.2em;color:{P['ivory']}}}

/* 4 · the spread */
#s4a{{top:400px}}
#s4arch{{position:absolute;top:480px;left:150px;right:150px;height:540px;z-index:2;display:flex;
  flex-direction:column;align-items:center;justify-content:center;gap:26px;padding-top:50px}}
#s4n{{font-size:250px;color:{P['bg']};line-height:.84}}
#s4u{{font-size:44px;letter-spacing:.22em;color:{P['ink']}}}
#s4k{{font-size:25px;letter-spacing:.2em;color:{P['muted']}}}
#s4b{{top:1150px;font-size:60px;white-space:nowrap}}
#s4c{{top:1300px;font-size:120px}}
#s4d{{top:1480px;font-size:34px;letter-spacing:.2em;color:{ROSE}}}

/* 6 · HOW IT SHAPED UP: the race chart on the plate you read */
#s6a{{top:330px}}
#s6plate{{position:absolute;top:410px;left:64px;right:64px;z-index:2;background:{P['ivory']};
  border-radius:44px;box-shadow:0 0 0 7px {P['bg']},0 0 0 11px {P['ivory']};padding:24px 0 20px;overflow:hidden}}
#s6svg{{display:block;margin:0 auto}}
#s6svg .ax{{font-family:'JetBrains Mono',monospace;font-weight:700;font-size:24px;fill:{P['muted']}}}
#s6svg .nm2{{font-family:'JetBrains Mono',monospace;font-weight:700;font-size:23px;letter-spacing:.02em}}
#s6svg .pv{{font-family:'Archivo',sans-serif;font-style:italic;font-variation-settings:'wdth' 125,'wght' 900;font-size:36px}}
#s6b{{top:1330px;font-size:30px;letter-spacing:.18em;color:{P['ivory']}}}
#s6c{{top:1400px;font-size:28px;letter-spacing:.2em;color:{ROSE}}}

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
  <div class="blk mono k" id="s1k">NIGHT {n_night} OF {cfg['sessions']} &middot; THE LAST ONE</div>
  <div class="blk disp" id="s1b"><span class="fitspan">FINAL</span></div>
  <div class="blk disp" id="s1c"><span class="fitspan">ROUND</span></div>
  <div class="blk disp" id="s1d"><span class="fitspan">{(when + " &middot; ") if away <= 1 else ""}{longish(night)} &middot; {start}</span></div>
  <div class="blk kufi" id="s1e">{name_ar}</div>
</div>

<div class="scene" id="s2">
  <div class="med" id="s2med"></div>
  <div class="blk mono k" id="s2a">THE SEASON PRIZES</div>
  <div id="s2plate">{money}</div>
  <div class="blk disp" id="s2b">DECIDED ON ONE NIGHT</div>
  <div class="blk mono" id="s2c">AND IT PAYS DOUBLE</div>
</div>

<div class="scene" id="s3">
  <div class="blk mono k" id="s3a">THE TABLE AFTER {WORDS[ST['played']]} NIGHTS</div>
  <div id="s3rows">{rows}</div>
  <div class="blk mono" id="s3c">TOP {WORDS[n_paid]} ARE PAID</div>
  <div class="blk mono" id="s3d">{ORD[n_paid + 1]} IS {chase} BEHIND {ORD[n_paid]}</div>
</div>

<div class="scene" id="s4">
  <div class="blk mono k" id="s4a">THE RACE FOR THE MONEY</div>
  <div class="arch" id="s4arch">
    <div class="disp" id="s4n">{spread}</div>
    <div class="mono" id="s4u">{unit(spread)}</div>
    <div class="mono" id="s4k">COVER 1ST TO {ORD[n_paid]}</div>
  </div>
  <div class="blk disp" id="s4b">BIGGEST NIGHT SO FAR</div>
  <div class="blk disp" id="s4c">+{ST['bestNight']}</div>
  <div class="blk mono" id="s4d">{inner[0]} {unit(inner[0])} BETWEEN {ORD[inner[1]]} AND {ORD[inner[2]]}</div>
</div>

<div class="scene" id="s6">
  <div class="blk mono k" id="s6a">HOW THE TABLE SHAPED UP</div>
  <div id="s6plate">{chart}</div>
  <div class="blk mono" id="s6b">THE LEAD CHANGED HANDS {changes} TIME{"" if changes == 1 else "S"}</div>
  <div class="blk mono" id="s6c">{lead_line}</div>
</div>

<div class="scene" id="s5">
  <div class="blk mono k" id="s5a">{cfg['name']} &middot; FINAL ROUND</div>
  <div class="blk disp" id="s5b"><span class="fitspan">{longish(night)}</span></div>
  <div class="blk disp" id="s5c">{start} &middot; {cfg['entry']} OMR</div>
  <div class="arch" id="s5arch">
    <div class="disp" id="s5t1">{beats[0]}</div>
    <div class="disp" id="s5t2">{beats[1]}</div>
  </div>
  <div class="blk disp" id="s5d">PLAY IT OR COME WATCH IT</div>
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
const expo = u => { u = clamp(u, 0, 1); return u >= 1 ? 1 : 1 - Math.pow(2, -10 * u); };
const back = u => { u = clamp(u, 0, 1); const c = 1.15, v = u - 1; return 1 + (c + 1) * v * v * v + c * v * v; };
// A line rising from behind its baseline. The element is shifted down by d
// and the bottom d px of it is clipped, so the window it shows through stays
// where the line will finally sit. Negative side insets, or the italic's
// overhang is sliced.
function reveal(el, u, wide) {
  const e = expo(u), h = el.offsetHeight || 1, d = (1 - e) * h;
  el.style.opacity = u <= 0 ? 0 : 1;
  el.style.transform = 'translateY(' + d.toFixed(2) + 'px)';
  el.style.clipPath = u >= 1 ? 'none' : 'inset(-30px -60px ' + d.toFixed(2) + 'px -60px)';
  if (wide) {
    const sp = el.querySelector('.fitspan') || el;
    sp.style.fontVariationSettings = "'wdth' " + (104 + 21 * e).toFixed(1) + ",'wght' 900";
  }
}
function fade(el, u) {
  const e = expo(u);
  el.style.opacity = clamp(u * 2.2, 0, 1);
  el.style.transform = 'translateY(' + ((1 - e) * 10).toFixed(2) + 'px)';
}
// A surface opening. `side` is the edge it grows FROM. The other three insets
// are negative so the double-line ring, which is a box-shadow outside the
// border box, is not clipped off once the surface is open.
function open(el, u, side) {
  const e = expo(u), r = ((1 - e) * 100).toFixed(2) + '%%';
  el.style.opacity = u <= 0 ? 0 : 1;
  el.style.clipPath = u >= 1 ? 'none'
    : side === 'left'   ? 'inset(-20px ' + r + ' -20px -20px round 999px)'
    : side === 'top'    ? 'inset(-20px -20px ' + r + ' -20px)'
    :                     'inset(' + r + ' -20px -20px -20px)';
}
function pop(el, u, spin) {
  const e = back(u);
  el.style.opacity = clamp(u * 3, 0, 1);
  el.style.transform = 'scale(' + (0.6 + 0.4 * e).toFixed(4) + ')'
    + (spin ? ' rotate(' + ((1 - expo(u)) * spin).toFixed(2) + 'deg)' : '');
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
  const i = sceneAt(t), t0 = SCENES[i];
  const last = i + 1 >= SCENES.length;
  const t1 = last ? DUR : SCENES[i + 1], len = t1 - t0;
  // scene-local time on the LONG cut's clock; a little faster still, so a
  // short scene holds its settled frame for most of its length
  const S = (t - t0) * Math.max(1, BASE[i] / len * (len < BASE[i] ? 1.25 : 1));

  // EACH SCENE CLEARS OUT before the next lands: four frames, up and away.
  // And while it is on screen it drifts in by one percent — the only
  // continuous motion in the film, linear, and too slow to read as a move.
  const x = last ? 1 : clamp((t1 - t) / 0.14, 0, 1);
  document.querySelectorAll('.scene').forEach((el, k) => {
    el.style.display = (k === i) ? 'block' : 'none';
    if (k !== i) return;
    el.style.opacity = (x * x).toFixed(3);
    el.style.transformOrigin = '50%% 50%%';
    el.style.transform = 'translateY(' + (-(1 - x) * 26).toFixed(2) + 'px) scale('
      + (1 + 0.010 * (t - t0) / len).toFixed(5) + ')';
  });

  if (i === 0) {
    pop(E('s1a'), S / 0.50);
    fade(E('s1k'), (S - 0.12) / 0.45);
    reveal(E('s1b'), (S - 0.16) / 0.65, true);
    reveal(E('s1c'), (S - 0.30) / 0.65, true);
    reveal(E('s1d'), (S - 0.55) / 0.60);
    fade(E('s1e'), (S - 0.80) / 0.50);
  } else if (i === 1) {
    pop(E('s2med'), S / 0.50);
    fade(E('s2a'), (S - 0.08) / 0.40);
    open(E('s2plate'), (S - 0.06) / 0.60, 'top');
    document.querySelectorAll('#s2plate .mr').forEach((el, k) => {
      const uu = (S - 0.30 - k * 0.12) / 0.50, ee = expo(uu);
      el.style.opacity = clamp(uu * 2.4, 0, 1);
      el.style.transform = 'translateX(' + (-(1 - ee) * 46).toFixed(2) + 'px)';
    });
    reveal(E('s2b'), (S - 1.00) / 0.60);
    fade(E('s2c'), (S - 1.30) / 0.50);
  } else if (i === 2) {
    fade(E('s3a'), S / 0.40);
    open(E('s3rows'), (S - 0.10) / 0.60, 'top');
    document.querySelectorAll('#s3rows .tr').forEach((el, k) => {
      const uu = (S - 0.22 - k * 0.09) / 0.50, ee = expo(uu);
      el.style.opacity = clamp(uu * 2.4, 0, 1);
      el.style.transform = 'translateX(' + (-(1 - ee) * 46).toFixed(2) + 'px)';
      const pt = el.querySelector('.pt');
      pt.textContent = Math.round(+pt.dataset.pts * expo((S - 0.26 - k * 0.09) / 0.62));
    });
    fade(E('s3c'), (S - 1.00) / 0.45);
    fade(E('s3d'), (S - 1.12) / 0.45);
  } else if (i === 3) {
    fade(E('s4a'), S / 0.40);
    open(E('s4arch'), (S - 0.08) / 0.65, 'bottom');
    E('s4n').textContent = Math.round(GAP * expo((S - 0.20) / 0.55));
    reveal(E('s4b'), (S - 0.90) / 0.60);
    reveal(E('s4c'), (S - 1.04) / 0.65, true);
    fade(E('s4d'), (S - 1.45) / 0.50);
  } else if (i === 4) {
    fade(E('s6a'), S / 0.40);
    open(E('s6plate'), (S - 0.08) / 0.60, 'top');
    // the lines draw together, left to right, one night at a time on the eye
    const p = clamp((S - 0.45) / 1.55, 0, 1), pe = 1 - Math.pow(1 - p, 2);
    document.querySelectorAll('#s6svg .rl').forEach(el => {
      const d = el.dataset.dash;
      if (d) { el.style.strokeDasharray = d; el.style.opacity = pe > 0 ? 1 : 0;
               el.style.clipPath = 'inset(0 ' + ((1 - pe) * 100).toFixed(2) + '%% 0 0)'; }
      else { el.style.strokeDasharray = '1'; el.style.strokeDashoffset = (1 - pe).toFixed(4); }
    });
    document.querySelectorAll('#s6svg .rd').forEach(el => {
      const at = +el.dataset.at;
      el.style.opacity = pe >= at - 0.001 ? 1 : 0;
    });
    document.querySelectorAll('#s6svg .rlab').forEach(el => {
      el.style.opacity = clamp((S - 1.90 - (+el.dataset.k) * 0.05) / 0.35, 0, 1);
    });
    fade(E('s6b'), (S - 2.15) / 0.45);
    fade(E('s6c'), (S - 2.35) / 0.45);
  } else {
    fade(E('s5a'), S / 0.40);
    reveal(E('s5b'), (S - 0.08) / 0.70, true);
    reveal(E('s5c'), (S - 0.30) / 0.60);
    open(E('s5arch'), (S - 0.48) / 0.65, 'bottom');
    fade(E('s5t1'), (S - 0.72) / 0.45);
    fade(E('s5t2'), (S - 0.86) / 0.45);
    reveal(E('s5d'), (S - 1.00) / 0.60);
    fade(E('s5e'), (S - 1.25) / 0.50);
  }
};
document.fonts.ready.then(() => { fitAll(); window.__seek(0); window.__ready = true; });
window.__seek(0);
</script>
""" % {"dur": DUR, "scenes": json.dumps(SCENES), "beats": json.dumps(BEATS),
       "hero": json.dumps(HERO), "gap": spread, "base": json.dumps(BASE)}

    html = ("<!doctype html><html><head><meta charset='utf-8'>\n<style>"
            + style + "</style></head><body>\n" + body + js + "\n</body></html>")
    os.makedirs(SP, exist_ok=True)
    open(OUT, "w", encoding="utf-8").write(html)
    json.dump({"dur": DUR, "scenes": SCENES, "beats": BEATS, "hero": HERO,
               "wav": os.path.join(SP, "video", "national-lastround-7s.wav" if SHORT else "national-lastround.wav")}, open(CUT, "w"))

    # ── captions, from the same figures ─────────────────────────────────────
    x = d(night)
    nice = f"{['Mon','Tue','Wed','Thu','Fri','Sat','Sun'][x.weekday()]} {x.day} {cfg['month'][:3]}"
    lead = when.capitalize() if away <= 1 else f"This {when.capitalize()}"
    top = "\n".join(f"{i + 1}. {r['name']} — {r['pts']}" for i, r in enumerate(table[:5]))
    pz = " / ".join(f"{p} OMR" for p in prizes)
    cap = f"""{cfg['name']} — FINAL ROUND cut ({nice})
{'=' * 54}
1080x1920 · {DUR:.1f}s · built {today} for a night {away} day(s) away, so it opens on "{when}"
Table from the app's own engine after {ST['played']} nights; every figure is read.

— WHATSAPP —

🏁 *FINAL ROUND — {lead}, {nice}.* Night {n_night} of {cfg['sessions']}, and it pays *DOUBLE POINTS*.

The season prizes are decided on this one night: {pz}.

The table after {WORDS[ST['played']].lower()} nights:
{top}

The lead has changed hands {changes} time{"" if changes == 1 else "s"} this season; {ldr['name']} {lead_line[len(ldr['name']) + 1:].lower()}.

{spread} points cover 1st to {ORD[n_paid].lower()}, with {inner[0]} between {ORD[inner[1]].lower()} and {ORD[inner[2]].lower()}. The biggest night anyone has had this season is +{ST['bestNight']}.

{start} · {cfg['entry']} OMR to play. Drop your name in the group — or come and watch it settled.
{cfg['host']}

— INSTAGRAM —

Final round. {nice}, {start}. Double points.

{table[0]['name']} {table[0]['pts']} · {table[1]['name']} {table[1]['pts']} · {table[2]['name']} {table[2]['pts']} — {spread} points across the top {WORDS[n_paid].lower()}, and {pz} on the line.

{tag}

#urbanplayground #padel #oman #56nationalseries #عمان
"""
    os.makedirs(os.path.dirname(CAPS), exist_ok=True)
    if not SHORT:
        open(CAPS, "w", encoding="utf-8").write(cap)
    print(f"built {OUT}  {len(html)/1024:.0f}KB  {DUR}s")
    print(f"  night {n_night} is {longish(night)}, {away} day(s) from {today} (Muscat) -> \"{when}\"")
    print(f"  table: " + ", ".join(f"{r['name']} {r['pts']}" for r in table[:5]))
    print(f"  race: {changes} lead changes, {holders} leaders · {lead_line}")
    print(f"  hook: {spread} cover 1st-{ORD[n_paid]} · inner {inner} · chase {chase} · best +{ST['bestNight']}")


if __name__ == "__main__":
    main()
