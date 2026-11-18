#!/usr/bin/env python3
"""56 National Series — the NIGHT RECAP cut. 1080x1920, 14.4s, five scenes.

The morning-after film for the night just played: the night, its champions,
the night's biggest earners, the table as it now stands with who moved, and
what is left. Same chrome, beat grid and motion language as the double-night
cut (`build-national-double-video.py`) — its seek engine is imported, not
copied, so the two films cannot drift into moving differently.

EVERY FIGURE IS READ. The table, the night's earners and the movement come
from ops/national-standings.mjs, which runs the app's own engine over the live
state; the final and the match count come from that same state; the dates,
doubles and landmark from national-season.json.

THE CLAIMS ARE DERIVED, NOT WRITTEN:
  - "NEW LEADER" prints only if the leader really changed on this night;
  - "BIGGEST NIGHT OF THE SEASON" only if this night's top gain IS the
    season's best;
  - "DOUBLED" only if the night was one of the double nights;
  - what is next is the remaining night list, with the doubles marked.
IT NEVER SAYS WHAT THE NIGHT WOULD HAVE BEEN WORTH UNDOUBLED: 2X skips the
streak bonus, so halving is close, and close is how a film contradicts the app.

IT REFUSES TO BUILD if the latest night has no decided final — a recap of a
night still being played is the worst thing this could publish.

  ssh urbanpadel 'curl -s localhost:3011/state' > $SP/na.json
  node ops/national-standings.mjs $SP/na.json $SP/na-standings.json
  python3 build-national-recap-video.py
  CUT=$SP/national-recap.cut.json python3.13 build-national-audio.py
  PAGE=national-recap.html NAME=national-recap WAV=national-recap.wav \\
      node record-national-video.mjs
"""
import importlib.util
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "ops"))
from font_bundle import bundle          # noqa: E402
from national_assets import assets      # noqa: E402


def _load(name, file):
    spec = importlib.util.spec_from_file_location(name, os.path.join(HERE, file))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


NV = _load("nvideo", "build-national-video.py")
d, longish, check_arabic, WORDS, SP = NV.d, NV.longish, NV.check_arabic, NV.WORDS, NV.SP

OUT = os.path.join(SP, "national-recap.html")
CUT = os.path.join(SP, "national-recap.cut.json")
CAPS = os.path.join(HERE, "brand", "national", "posts", "RECAP-CAPTIONS.txt")
W, H = 1080, 1920
DUR = 14.40
SCENES = [0.00, 2.40, 5.40, 8.40, 11.40]
BEATS = [0.00, 1.20, 2.40, 3.90, 5.40, 6.90, 8.40, 9.90, 11.40, 12.90]
HERO = [0.00, 2.40, 11.40]
BASE = [2.40, 3.00, 3.00, 3.00, 3.00]
ROSE = "#F2D0D3"
ORD = {1: "1ST", 2: "2ND", 3: "3RD", 4: "4TH"}


def seek_engine():
    """The motion helpers (expo, reveal, fade, open, pop, fitAll, sceneAt),
    lifted out of the double-night cut's own script at build time."""
    src = open(os.path.join(HERE, "build-national-double-video.py"), encoding="utf-8").read()
    a = src.index("const expo = u =>")
    b = src.index("function sceneAt(t)")
    b = src.index("\n", b) + 1
    js = src[a:b]
    # that file is a %-format template: %% is a literal percent there
    return js.replace("%%", "%")


def main():
    cfg = json.load(open(os.path.join(HERE, "national-season.json"), encoding="utf-8"))
    st_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(SP, "na-standings.json")
    state_path = sys.argv[2] if len(sys.argv) > 2 else os.path.join(SP, "na.json")
    ST = json.load(open(st_path, encoding="utf-8"))
    raw = json.load(open(state_path, encoding="utf-8"))
    state = raw.get("state", raw)
    P, A = cfg["palette"], assets()

    # ── the night ───────────────────────────────────────────────────────────
    n = ST["played"]
    if n < 1:
        raise SystemExit("nothing has been played — there is no night to recap")
    ses = state["sessions"][n - 1]
    night = ses.get("date")
    assert night == cfg["nights"][n - 1], f"night {n} is {night}, the season file says {cfg['nights'][n - 1]}"
    names = {p["id"]: p["name"] for p in state["players"]}
    team = {t["id"]: (names.get(t.get("p1Id"), "?"), names.get(t.get("p2Id"), "?")) for t in ses.get("teams") or []}
    br = ses.get("bracket") or {}
    fin = br.get("final") or {}
    if fin.get("winner") not in ("team1", "team2"):
        raise SystemExit(f"night {n} ({night}) has no decided final — it is not over")
    wk, lk = ("team1Id", "team2Id") if fin["winner"] == "team1" else ("team2Id", "team1Id")
    champ, runner = team[fin[wk]], team[fin[lk]]
    sc = fin.get("score") or {}
    ws, ls = (sc.get("t1"), sc.get("t2")) if fin["winner"] == "team1" else (sc.get("t2"), sc.get("t1"))
    played = [m for m in (ses.get("groupMatches") or []) if m.get("winner")]
    for k in ("r16", "qf", "sf"):
        played += [m for m in (br.get(k) or []) if m and m.get("winner")]
    played += [fin]
    n_teams = len(team)

    doubled = night in cfg["doubleNights"]
    is_natday = night == cfg.get("nationalDay")
    nt = ST["nightTop"][n - 1]
    assert nt["date"] == night
    top = [x for x in nt["top"] if x["played"]]
    best_gain = top[0]["gain"]
    season_best = best_gain >= ST["bestNight"]
    # who shares the top gain, and the next one down
    lead_gainers = [x["name"] for x in top if x["gain"] == best_gain]
    next_gain = next((x for x in top if x["gain"] < best_gain), None)

    # ── the table, before and after ────────────────────────────────────────
    race = ST["race"]
    if n >= 2:
        before = sorted(race, key=lambda r: -r["pts"][n - 2])
        pos_before = {r["id"]: i + 1 for i, r in enumerate(before)}
    else:
        pos_before = {}
    table = ST["table"][:4]
    new_leader = n >= 2 and pos_before.get(table[0]["id"]) != 1
    rows = []
    for i, r in enumerate(table):
        was = pos_before.get(r["id"])
        mv = (was - (i + 1)) if was else 0
        chip = (f'<span class="mv up">{mv}</span>' if mv > 0 else
                f'<span class="mv dn">{-mv}</span>' if mv < 0 else '<span class="mv eq"></span>')
        rows.append(f'<div class="tr"><div class="rk disp">{i + 1}</div>'
                    f'<div class="nm"><span class="fitcell disp">{r["name"].upper()}</span></div>'
                    f'{chip}<div class="pt disp" data-pts="{r["pts"]}">{r["pts"]}</div></div>')
    rows = "".join(rows)

    # ── what is left ───────────────────────────────────────────────────────
    left = ST["remaining"]
    nxt = left[0] if left else None
    left_doubles = [x for x in left if x in cfg["doubleNights"]]
    mt = re.search(r"(\d{1,2}(?::\d{2})?\s*(?:AM|PM))", cfg["schedule"], re.I)
    start = mt.group(1).upper() if mt else ""

    tag = cfg["tagline"].strip()
    beats = [x.strip() for x in re.findall(r"[^.!?]+[.!?]", tag)]
    assert len(beats) == 2, f"tagline must be two sentences, got {tag!r}"

    lm = cfg["landmarks"][(n - 1) % len(cfg["landmarks"])]
    lm_art = A[lm["asset"] + "@white"]
    name_ar, natday_ar = cfg["nameAr"], cfg["nationalDayLabelAr"]
    check_arabic(cfg, [name_ar, natday_ar, lm["nameAr"]])

    pill_title = (cfg["nationalDayLabel"] if is_natday
                  else "DOUBLE POINTS NIGHT" if doubled else f"NIGHT {n} OF {cfg['sessions']}")
    pill_ar = natday_ar if is_natday else name_ar
    def dd(x):
        y = d(x)
        return f"{['MON','TUE','WED','THU','FRI','SAT','SUN'][y.weekday()]} {y.day} {cfg['month'][:3].upper()}"

    s3_title = ("BIGGEST NIGHT OF THE SEASON" if season_best else "THE NIGHT'S BIGGEST")
    s3_names = " &middot; ".join(x.upper() for x in lead_gainers[:2])
    s3_next = (f"{next_gain['name'].upper()} +{next_gain['gain']}" if next_gain else "")
    s3_foot = "DOUBLE POINTS NIGHT" if doubled else f"NIGHT {n} OF {cfg['sessions']}"

    if left:
        s5_big = f"{WORDS[len(left)]} NIGHT{'S' if len(left) != 1 else ''} LEFT"
        s5_next = f"NEXT &middot; {dd(nxt)}" + (f" &middot; {start}" if start else "")
        s5_dbl = ("DOUBLE: " + " &middot; ".join(dd(x) for x in left_doubles)) if left_doubles else ""
    else:
        s5_big, s5_next, s5_dbl = "THAT'S THE SEASON", "", ""

    green_pill = P["green"] if doubled else P["deep"]
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

/* 1 · the night */
#s1a{{top:430px}}
#s1k{{top:650px}}
#s1b{{top:730px;font-size:190px}}
#s1pill{{position:absolute;top:960px;left:52px;right:52px;z-index:2;background:{green_pill};
  border-radius:999px;padding:32px 34px 32px 48px;display:flex;align-items:center;gap:22px}}
#s1pill .l{{flex:1 1 auto;min-width:0;text-align:left}}
#s1t{{font-size:46px;color:#FFFFFF;white-space:nowrap}}
#s1ar{{font-size:28px;margin-top:12px;color:#FFFFFF}}
#s1x{{flex:0 0 auto;width:120px;height:120px;border-radius:50%;background:#FFFFFF;color:{green_pill};
  display:flex;align-items:center;justify-content:center;font-size:48px}}
#s1c{{top:1260px;font-size:56px}}
#s1d{{top:1360px;font-size:30px;letter-spacing:.2em;color:{ROSE}}}

/* 2 · the champions, in the door */
#s2med{{position:absolute;top:300px;left:50%;margin-left:-90px;width:180px;height:180px;z-index:3;
  background-image:url("{lm_art}")}}
#s2arch{{position:absolute;top:390px;left:84px;right:84px;height:820px;z-index:2;display:flex;
  flex-direction:column;align-items:center;justify-content:center;gap:22px;padding:120px 0 40px}}
#s2k{{font-size:28px;letter-spacing:.3em;color:{P['muted']}}}
.ln{{width:100%;text-align:center;font-size:96px;color:{P['ink']}}}
#s2amp{{font-size:56px;color:{P['bg']}}}
#s2s{{font-size:200px;color:{P['bg']};margin-top:18px}}
#s2b{{top:1300px;font-size:30px;letter-spacing:.18em;color:{ROSE}}}
#s2c{{top:1370px;font-size:56px}}

/* 3 · the biggest night */
#s3a{{top:500px}}
#s3b{{top:580px;font-size:70px;white-space:nowrap}}
#s3n{{top:720px;font-size:330px}}
#s3c{{top:1090px;font-size:58px}}
#s3d{{top:1210px;font-size:34px;letter-spacing:.18em;color:{ROSE}}}
#s3e{{top:1340px}}
.chip{{display:inline-block;padding:16px 34px;border-radius:999px;background:{green_pill};color:#FFFFFF;
  font-size:30px;letter-spacing:.2em}}

/* 4 · the table, and who moved */
#s4med{{position:absolute;top:250px;left:50%;margin-left:-95px;width:190px;height:190px;z-index:2;
  background-image:url("{lm_art}")}}
#s4a{{top:490px}}
#s4rows{{position:absolute;top:570px;left:56px;right:56px;z-index:2;background:{P['ivory']};
  border-radius:44px;box-shadow:0 0 0 7px {P['bg']},0 0 0 11px {P['ivory']};padding:14px 30px}}
.tr{{display:flex;align-items:center;gap:20px;height:158px;border-top:2px solid rgba(26,10,12,.10)}}
.tr:first-child{{border-top:0}}
.rk{{flex:0 0 84px;width:84px;height:84px;border-radius:50%;background:{P['bg']};color:{P['ivory']};
  display:flex;align-items:center;justify-content:center;font-size:44px}}
.tr:first-child .rk{{background:{P['green']};color:#FFFFFF}}
.nm{{flex:1 1 0;min-width:0;text-align:left;font-size:58px;color:{P['ink']};white-space:nowrap}}
.mv{{flex:0 0 66px;display:flex;align-items:center;justify-content:center;gap:6px;
  font-family:'JetBrains Mono',monospace;font-weight:700;font-size:28px;color:{P['ink']}}}
.mv::before{{content:"";width:0;height:0;border-left:11px solid transparent;border-right:11px solid transparent}}
.mv.up::before{{border-bottom:16px solid {P['green']}}}
.mv.dn::before{{border-top:16px solid {P['bg']}}}
.mv.eq::before{{width:20px;height:4px;border:0;background:rgba(26,10,12,.3)}}
.pt{{flex:0 0 auto;font-size:80px;color:{P['bg']};min-width:160px;text-align:right}}
#s4c{{top:1320px;font-size:28px;letter-spacing:.16em;color:{ROSE}}}
#s4d{{top:1390px;font-size:30px;letter-spacing:.2em;color:{P['ivory']}}}

/* 5 · what is left */
#s5a{{top:380px}}
#s5b{{top:460px;font-size:150px}}
#s5c{{top:690px;font-size:52px}}
#s5e{{top:790px}}
#s5arch{{position:absolute;top:930px;left:110px;right:110px;height:330px;z-index:2;display:flex;
  flex-direction:column;align-items:center;justify-content:center;gap:10px;padding-top:30px}}
#s5t1{{font-size:88px;color:{P['ink']}}}
#s5t2{{font-size:88px;color:{P['bg']}}}
#s5d{{top:1360px;font-size:34px;letter-spacing:.2em;color:{ROSE}}}
"""

    body = f"""
<div id="tile"></div>
<div class="band t"></div><div class="band b"></div>

<div class="scene" id="s1">
  <div class="blk" id="s1a"><span class="flag"><span class="n disp" style="font-size:150px">56</span></span></div>
  <div class="blk mono k" id="s1k">{cfg['name']} &middot; NIGHT {n} OF {cfg['sessions']}</div>
  <div class="blk disp" id="s1b"><span class="fitspan">{dd(night)}</span></div>
  <div id="s1pill">
    <div class="l">
      <div class="disp" id="s1t">{pill_title}</div>
      <div class="kufi" id="s1ar">{pill_ar}</div>
    </div>
    {'<div class="disp" id="s1x">2X</div>' if doubled else ''}
  </div>
  <div class="blk disp" id="s1c">THE RESULTS ARE IN</div>
  <div class="blk mono" id="s1d">{n_teams} TEAMS &middot; {len(played)} MATCHES</div>
</div>

<div class="scene" id="s2">
  <div class="med" id="s2med"></div>
  <div class="arch" id="s2arch">
    <div class="mono" id="s2k">CHAMPIONS</div>
    <div class="ln disp"><span class="fitspan">{champ[0].upper()}</span></div>
    <div class="disp" id="s2amp">&amp;</div>
    <div class="ln disp"><span class="fitspan">{champ[1].upper()}</span></div>
    <div class="disp" id="s2s">{ws}&ndash;{ls}</div>
  </div>
  <div class="blk mono" id="s2b">IN THE FINAL, OVER</div>
  <div class="blk disp" id="s2c"><span class="fitspan">{runner[0].upper()} &amp; {runner[1].upper()}</span></div>
</div>

<div class="scene" id="s3">
  <div class="blk mono k" id="s3a">{'DOUBLED' if doubled else 'THE NIGHT'}</div>
  <div class="blk disp" id="s3b"><span class="fitspan">{s3_title}</span></div>
  <div class="blk disp" id="s3n" data-n="{best_gain}">+{best_gain}</div>
  <div class="blk disp" id="s3c"><span class="fitspan">{s3_names}</span></div>
  <div class="blk mono" id="s3d">{s3_next}</div>
  <div class="blk" id="s3e"><span class="chip mono">{s3_foot}</span></div>
</div>

<div class="scene" id="s4">
  <div class="med" id="s4med"></div>
  <div class="blk mono k" id="s4a">{'NEW LEADER' if new_leader else 'THE TABLE'} &middot; AFTER {WORDS[n]} NIGHT{'S' if n != 1 else ''}</div>
  <div id="s4rows">{rows}</div>
  <div class="blk mono" id="s4c">TOP {WORDS[len(cfg['seasonPrizes'])]} SHARE</div>
  <div class="blk mono" id="s4d">{' &middot; '.join(str(x) for x in cfg['seasonPrizes'])} OMR</div>
</div>

<div class="scene" id="s5">
  <div class="blk mono k" id="s5a">{cfg['name']}</div>
  <div class="blk disp" id="s5b"><span class="fitspan">{s5_big}</span></div>
  <div class="blk disp" id="s5c">{s5_next}</div>
  <div class="blk" id="s5e">{f'<span class="chip mono">{s5_dbl}</span>' if s5_dbl else ''}</div>
  <div class="arch" id="s5arch">
    <div class="disp" id="s5t1">{beats[0]}</div>
    <div class="disp" id="s5t2">{beats[1]}</div>
  </div>
  <div class="blk mono" id="s5d">{cfg['host']}</div>
</div>
"""

    js = """
<script>
const DUR = %(dur)s, SCENES = %(scenes)s, BEATS = %(beats)s, HERO = %(hero)s, BASE = %(base)s;
window.__dur = DUR; window.__scenes = SCENES;
const E = id => document.getElementById(id);
const clamp = (x,a,b) => x < a ? a : x > b ? b : x;
%(engine)s
window.__seek = function (t) {
  t = clamp(t, 0, DUR);
  const i = sceneAt(t), t0 = SCENES[i];
  const last = i + 1 >= SCENES.length;
  const t1 = last ? DUR : SCENES[i + 1], len = t1 - t0;
  const S = (t - t0) * Math.max(1, BASE[i] / len * (len < BASE[i] ? 1.25 : 1));
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
    reveal(E('s1b'), (S - 0.16) / 0.70, true);
    open(E('s1pill'), (S - 0.40) / 0.60, 'left');
    if (E('s1x')) pop(E('s1x'), (S - 0.80) / 0.55, -140);
    reveal(E('s1c'), (S - 0.90) / 0.60);
    fade(E('s1d'), (S - 1.15) / 0.50);
  } else if (i === 1) {
    open(E('s2arch'), S / 0.65, 'bottom');
    pop(E('s2med'), (S - 0.30) / 0.55);
    fade(E('s2k'), (S - 0.30) / 0.40);
    document.querySelectorAll('#s2arch .ln').forEach((el, k) => reveal(el, (S - 0.42 - k * 0.14) / 0.65, true));
    fade(E('s2amp'), (S - 0.52) / 0.40);
    pop(E('s2s'), (S - 0.95) / 0.55);
    fade(E('s2b'), (S - 1.25) / 0.45);
    reveal(E('s2c'), (S - 1.35) / 0.60);
  } else if (i === 2) {
    fade(E('s3a'), S / 0.40);
    reveal(E('s3b'), (S - 0.06) / 0.65, true);
    const n = E('s3n'); reveal(n, (S - 0.24) / 0.70, true);
    n.textContent = '+' + Math.round(+n.dataset.n * expo((S - 0.24) / 0.80));
    reveal(E('s3c'), (S - 0.70) / 0.60);
    fade(E('s3d'), (S - 0.95) / 0.45);
    open(E('s3e'), (S - 1.10) / 0.55, 'left');
  } else if (i === 3) {
    pop(E('s4med'), S / 0.50);
    fade(E('s4a'), (S - 0.10) / 0.40);
    open(E('s4rows'), (S - 0.14) / 0.60, 'top');
    document.querySelectorAll('#s4rows .tr').forEach((el, k) => {
      const uu = (S - 0.26 - k * 0.09) / 0.50, ee = expo(uu);
      el.style.opacity = clamp(uu * 2.4, 0, 1);
      el.style.transform = 'translateX(' + (-(1 - ee) * 46).toFixed(2) + 'px)';
      const pt = el.querySelector('.pt');
      pt.textContent = Math.round(+pt.dataset.pts * expo((S - 0.30 - k * 0.09) / 0.62));
      fade(el.querySelector('.mv'), (S - 0.95 - k * 0.06) / 0.40);
    });
    fade(E('s4c'), (S - 1.20) / 0.45);
    fade(E('s4d'), (S - 1.30) / 0.45);
  } else {
    fade(E('s5a'), S / 0.40);
    reveal(E('s5b'), (S - 0.08) / 0.70, true);
    reveal(E('s5c'), (S - 0.30) / 0.60);
    open(E('s5e'), (S - 0.50) / 0.55, 'left');
    open(E('s5arch'), (S - 0.62) / 0.65, 'bottom');
    fade(E('s5t1'), (S - 0.86) / 0.45);
    fade(E('s5t2'), (S - 1.00) / 0.45);
    fade(E('s5d'), (S - 1.25) / 0.50);
  }
};
document.fonts.ready.then(() => { fitAll(); window.__seek(0); window.__ready = true; });
window.__seek(0);
</script>
""" % {"dur": DUR, "scenes": json.dumps(SCENES), "beats": json.dumps(BEATS),
       "hero": json.dumps(HERO), "base": json.dumps(BASE),
       "engine": seek_engine().replace("%", "%%")}

    html = ("<!doctype html><html><head><meta charset='utf-8'>\n<style>"
            + style + "</style></head><body>\n" + body + js + "\n</body></html>")
    open(OUT, "w", encoding="utf-8").write(html)
    json.dump({"dur": DUR, "scenes": SCENES, "beats": BEATS, "hero": HERO,
               "wav": os.path.join(SP, "video", "national-recap.wav")}, open(CUT, "w"))

    # ── captions ───────────────────────────────────────────────────────────
    nice = dd(night).title()
    tbl = "\n".join(f"{i + 1}. {r['name']} — {r['pts']}" for i, r in enumerate(table))
    big = (f"+{best_gain} for {' and '.join(lead_gainers)} — the biggest night of the season"
           if season_best else f"+{best_gain} for {' and '.join(lead_gainers)}")
    nxt_line = ""
    if left:
        nxt_line = (f"{WORDS[len(left)].capitalize()} night{'s' if len(left) != 1 else ''} left. "
                    f"Next: {dd(nxt).title()}{', ' + start if start else ''}.")
        if left_doubles:
            nxt_line += " Double points on " + " and ".join(dd(x).title() for x in left_doubles) + "."
    cap = f"""{cfg['name']} — night {n} recap ({nice})
{'=' * 54}
1080x1920 · {DUR:.1f}s · every figure from the app's own engine.

— WHATSAPP —

🇴🇲 *{pill_title.title() if not is_natday else cfg['nationalDayLabel'].title()} — done.*

🏆 Champions: *{champ[0]} & {champ[1]}*, {ws}–{ls} over {runner[0]} & {runner[1]} in the final.
{big}{' (doubled)' if doubled else ''}.

The table after {WORDS[n].lower()} nights{' — new leader' if new_leader else ''}:
{tbl}

{nxt_line}
{cfg['host']}

— INSTAGRAM —

{pill_title.title() if not is_natday else cfg['nationalDayLabel'].title()} is in the books. {champ[0]} & {champ[1]} take it {ws}–{ls} over {runner[0]} & {runner[1]}.

{table[0]['name']} {'takes the lead' if new_leader else 'leads'} on {table[0]['pts']}. {nxt_line}

{tag}

#urbanplayground #padel #oman #56nationalseries #عمان
"""
    open(CAPS, "w", encoding="utf-8").write(cap)
    print(f"built {OUT}  {len(html)/1024:.0f}KB  {DUR}s")
    print(f"  night {n} {night}{' (2X)' if doubled else ''}: {champ[0]} & {champ[1]} {ws}-{ls} over {runner[0]} & {runner[1]}")
    print(f"  {len(played)} matches · {n_teams} teams · best +{best_gain} ({', '.join(lead_gainers)}) season-best={season_best}")
    print(f"  table: " + ", ".join(f"{r['name']} {r['pts']}" for r in table) + f"  new leader={new_leader}")
    print(f"  left: {left}  doubles {left_doubles}  ·  captions {CAPS}")


if __name__ == "__main__":
    main()
