#!/usr/bin/env python3.13
"""56 National Series — the FINAL ROUND film. 1080x1920, 18.2s (SHORT=1: 9.6s).

Second version (24 Nov 2026). The owner on the first: "animation and design
could be a lot better" and "better music or Omani music". So this is a film,
not a sequence of type cards:

  1  FINAL ROUND      an Omani door draws itself, the words SLAM in
  2  THE CONTENDERS   the top three's own painted portraits, each in an arch
  3  HOW IT SHAPED UP the race chart, faces riding the line ends
  4  THE MONEY        who holds each paid place right now, and the spread
  5  2X               the double stamp, shock rings
  6  THE ASK          date, time, entry, the tagline, the host

Scenes change through a DOOR WIPE (an arch rising out of the floor) rather
than a fade; sparks drift up through every scene; the khanjar tile drifts.
Every motion is a pure function of t through window.__seek(t), so the
recorder scrubs it frame-exact and no CSS animation exists to drift.

EVERY FIGURE IS READ. The table, the race and the lead changes come from
ops/national-standings.mjs (the app's own engine over the live state); the
night, time, entry and prizes from national-season.json. The portraits are
the Heist portraits the owner made (/players/<id>.jpg), read from
PORTRAITS=<dir> or fetched; a contender without one gets an initial.

IT REFUSES TO BUILD unless exactly ONE night remains, it is the finals date
and it is a double night. It never says what a doubled night is worth, nor
that anybody is out of it.

  ssh urbanpadel 'curl -s localhost:3011/state' > $SP/na.json
  node ops/national-standings.mjs $SP/na.json $SP/na-standings.json
  python3.13 build-national-lastround-video.py   # AS_OF=, SHORT=1, PORTRAITS=<dir>
  CUT=$SP/national-lastround.cut.json python3.13 build-national-omani-audio.py
  PAGE=national-lastround.html NAME=national-lastround WAV=national-lastround.wav \\
      node record-national-video.mjs             # CONTACT=1 for a strip
"""
import base64
import datetime
import importlib.util
import io
import json
import os
import random
import re
import sys
import urllib.request
from zoneinfo import ZoneInfo

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "ops"))
from font_bundle import bundle          # noqa: E402
from national_assets import assets      # noqa: E402

_spec = importlib.util.spec_from_file_location("nvideo", os.path.join(HERE, "build-national-video.py"))
NV = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(NV)
d, longish, check_arabic, WORDS, SP = NV.d, NV.longish, NV.check_arabic, NV.WORDS, NV.SP

OUT = os.path.join(SP, "national-lastround.html")
CUT = os.path.join(SP, "national-lastround.cut.json")
CAPS = os.path.join(HERE, "brand", "national", "posts", "FINAL-ROUND-CAPTIONS.txt")
W, H = 1080, 1920

DUR = 18.20
SCENES = [0.00, 2.60, 6.00, 9.60, 12.80, 15.00]
BASE = [2.60, 3.40, 3.60, 3.20, 2.20, 3.20]          # each scene's own clock
HERO = [0.00, 0.62, 2.60, 6.00, 9.60, 12.80, 15.00]
SHORT = bool(os.environ.get("SHORT"))
if SHORT:
    DUR = 9.60
    SCENES = [0.00, 1.40, 3.20, 5.10, 6.80, 7.90]
    HERO = [0.00, 0.40, 1.40, 3.20, 5.10, 6.80, 7.90]
    OUT = os.path.join(SP, "national-lastround-7s.html")
    CUT = os.path.join(SP, "national-lastround-7s.cut.json")
FULLDAY = ["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY", "SUNDAY"]
ORD = {1: "1ST", 2: "2ND", 3: "3RD", 4: "4TH", 5: "5TH"}
ROSE = "#F2D0D3"


def portrait(pid):
    """A Heist portrait as a small JPEG data URL, or None."""
    raw = None
    src = os.environ.get("PORTRAITS") or os.path.join(SP, "live-portraits")
    f = os.path.join(src, pid + ".jpg")
    if os.path.exists(f):
        raw = open(f, "rb").read()
    else:
        try:
            req = urllib.request.Request(f"https://heist.urbanpadel.om/players/{pid}.jpg",
                                         headers={"User-Agent": "Mozilla/5.0"})
            raw = urllib.request.urlopen(req, timeout=20).read()
        except Exception:
            return None
    try:
        from PIL import Image
        im = Image.open(io.BytesIO(raw)).convert("RGB")
        im.thumbnail((640, 800))
        b = io.BytesIO(); im.save(b, "JPEG", quality=84); raw = b.getvalue()
    except ImportError:
        pass
    return "data:image/jpeg;base64," + base64.b64encode(raw).decode()


def main():
    cfg = json.load(open(os.path.join(HERE, "national-season.json"), encoding="utf-8"))
    st_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(SP, "na-standings.json")
    if not os.path.exists(st_path):
        raise SystemExit(f"no standings at {st_path} — run ops/national-standings.mjs first")
    ST = json.load(open(st_path, encoding="utf-8"))
    P, A = cfg["palette"], assets()
    today = (d(os.environ["AS_OF"]) if os.environ.get("AS_OF")
             else datetime.datetime.now(ZoneInfo("Asia/Muscat")).date())

    # ── the guards: this film's headline must be TRUE ───────────────────────
    if len(ST["remaining"]) != 1:
        raise SystemExit(f"{len(ST['remaining'])} nights remain — this film says FINAL ROUND")
    night = ST["remaining"][0]
    if night != cfg["finalsDate"]:
        raise SystemExit(f"the last night left is {night}, not the finals date {cfg['finalsDate']}")
    if night not in cfg["doubleNights"]:
        raise SystemExit(f"{night} is not a double night — this film says 2X")
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
    lm = cfg["landmarks"][(n_night - 1) % len(cfg["landmarks"])]
    lm_art = A[lm["asset"] + "@white"]
    check_arabic(cfg, [name_ar, lm["nameAr"]])
    prizes = cfg["seasonPrizes"]

    # ── the figures ─────────────────────────────────────────────────────────
    spread = table[0]["pts"] - table[n_paid - 1]["pts"]
    unit = lambda n: "POINT" if n == 1 else "POINTS"
    L = ST["leaders"]
    changes = sum(1 for a, b in zip(L, L[1:]) if a["id"] != b["id"])
    ldr = L[-1]
    since = len(L)
    while since > 1 and L[since - 2]["id"] == ldr["id"]:
        since -= 1
    lead_line = (f"{ldr['name'].upper()} WENT TOP ON NIGHT {since}" if since == len(L)
                 else f"{ldr['name'].upper()} HAS LED SINCE NIGHT {since}")
    faces = {r["id"]: portrait(r["id"]) for r in table[:5]}
    initials = lambda n: "".join(w[0] for w in n.split()[:2]).upper()

    def face(pid, name, cls):
        src = faces.get(pid)
        if src:
            return f'<div class="{cls}" style="background-image:url({src})"></div>'
        return f'<div class="{cls} noface"><span class="disp">{initials(name)}</span></div>'

    # 2 · the contenders: the leader large, 2nd and 3rd beside each other
    c = table[:3]
    gap = lambda i: c[i - 1]["pts"] - c[i]["pts"]
    contenders = f"""
  <div class="arch big" id="c1">{face(c[0]['id'], c[0]['name'], 'ph')}<div class="gloss"></div></div>
  <div class="rk disp" id="c1r">1</div>
  <div class="blk disp" id="c1n"><span class="fitspan">{c[0]['name'].upper()}</span></div>
  <div class="blk mono" id="c1p"><span data-n="{c[0]['pts']}">{c[0]['pts']}</span> PTS &middot; TOP OF THE TABLE</div>
  <div class="arch small" id="c2">{face(c[1]['id'], c[1]['name'], 'ph')}<div class="gloss"></div></div>
  <div class="rk disp sm" id="c2r">2</div>
  <div class="chip mono" id="c2g">&minus;{gap(1)}</div>
  <div class="sname disp" id="c2n"><span class="fitbox">{c[1]['name'].upper()}</span></div>
  <div class="spts mono" id="c2p"><span data-n="{c[1]['pts']}">{c[1]['pts']}</span> PTS</div>
  <div class="arch small" id="c3">{face(c[2]['id'], c[2]['name'], 'ph')}<div class="gloss"></div></div>
  <div class="rk disp sm" id="c3r">3</div>
  <div class="chip mono" id="c3g">&minus;{gap(2)}</div>
  <div class="sname disp" id="c3n"><span class="fitbox">{c[2]['name'].upper()}</span></div>
  <div class="spts mono" id="c3p"><span data-n="{c[2]['pts']}">{c[2]['pts']}</span> PTS</div>"""

    # 3 · the race chart, faces riding the line ends
    raceby = {r["id"]: r for r in ST["race"]}
    lines = [raceby[r["id"]] for r in table[:5] if r["id"] in raceby]
    assert len(lines) == 5, "the race does not cover the top five"
    VW, VH = 952, 860
    X0, X1, Y0, Y1 = 78, 560, 56, 760
    top = max(max(r["pts"]) for r in lines)
    ymax = (top // 50 + 1) * 50
    nN = ST["played"]
    xa = lambda i: X0 + (X1 - X0) * i / max(1, nN - 1)
    ya = lambda v: Y1 - (Y1 - Y0) * v / ymax
    INK = [P["bg"], P["green"], P["ink"], P["muted"], P["muted"]]
    grid = "".join(f'<line x1="{X0}" x2="{X1}" y1="{ya(v):.1f}" y2="{ya(v):.1f}" stroke="rgba(26,10,12,.10)" stroke-width="2"/>'
                   f'<text x="{X0 - 14}" y="{ya(v) + 8:.1f}" text-anchor="end" class="ax">{v}</text>'
                   for v in range(0, ymax + 1, 50 if ymax <= 250 else 100))
    xlab = "".join(f'<text x="{xa(i):.1f}" y="{Y1 + 46}" text-anchor="middle" class="ax">N{i + 1}</text>' for i in range(nN))
    defs, paths, ends, heads = [], [], [], []
    for k, r in enumerate(lines):
        pts = [(xa(i), ya(v)) for i, v in enumerate(r["pts"]) if i >= r["from"]]
        dpath = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts)
        dash = ' stroke-dasharray="14 10"' if k == 4 else ""
        paths.append(f'<path class="rl" data-k="{k}" d="{dpath}" fill="none" stroke="{INK[k]}" stroke-width="{10 if k == 0 else 6}"'
                     f' stroke-linejoin="round" stroke-linecap="round"{dash}/>')
        ends.append([pts[-1][1], k, r])
        src = faces.get(r["id"])
        rad = 30 if k < 3 else 13
        if src and k < 3:
            defs.append(f'<clipPath id="cp{k}"><circle r="{rad}" cx="0" cy="0"/></clipPath>')
            inner = (f'<image href="{src}" x="{-rad}" y="{-rad}" width="{2 * rad}" height="{2 * rad}" '
                     f'preserveAspectRatio="xMidYMin slice" clip-path="url(#cp{k})"/>')
        else:
            inner = f'<circle r="{rad}" fill="{INK[k]}"/>'
        heads.append(f'<g class="hd" data-k="{k}" data-path=\'{json.dumps([[round(x, 1), round(y, 1)] for x, y in pts])}\'>'
                     f'<circle r="{rad + 5}" fill="{P["ivory"]}" stroke="{INK[k]}" stroke-width="5"/>{inner}</g>')
    ends.sort(key=lambda e: e[0])
    for i in range(1, len(ends)):
        ends[i][0] = max(ends[i][0], ends[i - 1][0] + 50)
    if ends[-1][0] > Y1 + 4:
        sh = ends[-1][0] - (Y1 + 4)
        for e in ends:
            e[0] -= sh
    LX = X1 + 56
    labels = "".join(
        f'<g class="rlab" data-k="{k}"><text x="{LX}" y="{yy + 10:.1f}" class="nm2" fill="{P["ink"]}">{r["name"].upper()}'
        f'<tspan class="pv" fill="{INK[k] if k < 3 else P["ink"]}" dx="12">{r["pts"][-1]}</tspan></text></g>'
        for yy, k, r in ends)
    scan = f'<g id="scan"><line x1="0" x2="0" y1="{Y0 - 10}" y2="{Y1}" stroke="{P["bg"]}" stroke-width="3" stroke-dasharray="6 8"/></g>'
    chart = (f'<svg id="s6svg" viewBox="0 0 {VW} {VH}" width="{VW}" height="{VH}"><defs>{"".join(defs)}</defs>{grid}{xlab}'
             f'{scan}{"".join(paths)}{"".join(heads)}{labels}</svg>')
    chart_meta = {"x0": X0, "x1": X1, "n": nN}

    # 4 · the money: who holds each paid place right now
    money = "".join(
        f'<div class="mr" id="mr{i}"><span class="mo mono">{ORD[i + 1]}</span>'
        f'{face(table[i]["id"], table[i]["name"], "mf")}'
        f'<span class="mh"><span class="mhn mono">{table[i]["name"].upper()}</span>'
        f'<span class="mhp mono">{table[i]["pts"]} PTS</span></span>'
        f'<span class="ma disp" data-n="{p}">{p}</span><span class="mu mono">OMR</span></div>'
        for i, p in enumerate(prizes))

    # sparks: positions seeded, so every render of the film is the same film
    rng = random.Random(56)
    sparks = "".join(f'<i class="sp" data-x="{rng.uniform(40, 1040):.0f}" data-s="{rng.uniform(0, 1):.3f}" '
                     f'data-v="{rng.uniform(.55, 1.25):.3f}" data-z="{rng.uniform(3, 8):.1f}"></i>' for _ in range(42))

    css = CSS
    for k, v in {"@@BUNDLE@@": bundle(), "@@BG@@": P["bg"], "@@DEEP@@": P["deep"], "@@IVORY@@": P["ivory"],
                 "@@INK@@": P["ink"], "@@MUTED@@": P["muted"], "@@GREEN@@": P["green"], "@@FLAG@@": P["flag"],
                 "@@ROSE@@": ROSE, "@@KHANJAR@@": A["khanjar"], "@@MASAR@@": A["masar"], "@@LM@@": lm_art,
                 "@@W@@": str(W), "@@H@@": str(H)}.items():
        css = css.replace(k, v)

    body = f"""
<div id="sky"></div><div id="rays"></div><div id="tile"></div><div id="vig"></div>
<div class="band t"></div><div class="band b"></div>
<div id="sparks">{sparks}</div>
<div id="stage">

<div class="scene" id="s1">
  <svg id="s1door" viewBox="0 0 800 1160" width="800" height="1160">
    <path id="s1dp" d="M30,1150 L30,400 Q30,30 400,30 Q770,30 770,400 L770,1150" fill="none" stroke="{P['ivory']}" stroke-width="8"/>
    <path id="s1dq" d="M60,1150 L60,410 Q60,64 400,64 Q740,64 740,410 L740,1150" fill="none" stroke="{P['green']}" stroke-width="3"/>
  </svg>
  <div class="blk" id="s1a"><span class="flag"><span class="n disp" style="font-size:132px">56</span></span></div>
  <div class="blk mono k" id="s1k">NIGHT {n_night} OF {cfg['sessions']} &middot; THE LAST ONE</div>
  <div class="blk disp" id="s1b"><span class="fitspan">FINAL</span></div>
  <div class="blk disp" id="s1c"><span class="fitspan">ROUND</span></div>
  <div class="blk disp" id="s1d"><span class="fitspan">{(when + " &middot; ") if away <= 1 else ""}{longish(night)} &middot; {start}</span></div>
  <div class="blk kufi" id="s1e">{name_ar}</div>
</div>

<div class="scene" id="s2">
  <div class="blk mono k" id="s2a">THE CONTENDERS</div>
  <div class="med" id="s2med"></div>
  {contenders}
</div>

<div class="scene" id="s6">
  <div class="blk mono k" id="s6a">HOW THE TABLE SHAPED UP</div>
  <div id="s6plate">{chart}</div>
  <div class="blk mono" id="s6n">AFTER NIGHT <span id="s6nn">1</span> OF {nN}</div>
  <div class="blk mono" id="s6b">THE LEAD CHANGED HANDS {changes} TIME{"" if changes == 1 else "S"}</div>
  <div class="blk mono" id="s6c">{lead_line}</div>
</div>

<div class="scene" id="s4">
  <div class="blk mono k" id="s4a">THE SEASON PRIZES &middot; WHO HOLDS THEM NOW</div>
  <div id="s4plate">{money}</div>
  <div class="arch" id="s4arch">
    <div class="disp" id="s4n">{spread}</div>
    <div class="mono" id="s4u">{unit(spread)} COVER 1ST TO {ORD[n_paid]}</div>
  </div>
  <div class="blk disp" id="s4b">BIGGEST NIGHT SO FAR &middot; +{ST['bestNight']}</div>
</div>

<div class="scene" id="s7">
  <div id="ring1" class="ring"></div><div id="ring2" class="ring"></div><div id="ring3" class="ring"></div>
  <div class="blk disp" id="s7x">2X</div>
  <div class="blk disp" id="s7b"><span class="fitspan">DOUBLE POINTS</span></div>
  <div class="blk mono" id="s7c">ON THE NIGHT THAT DECIDES IT</div>
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

</div>
<div id="wipe"><div id="wipe2"></div></div>
<div id="flash"></div>
"""
    js = JS
    for k, v in {"@@DUR@@": str(DUR), "@@SCENES@@": json.dumps(SCENES), "@@BASE@@": json.dumps(BASE),
                 "@@HERO@@": json.dumps(HERO), "@@GAP@@": str(spread), "@@CHART@@": json.dumps(chart_meta)}.items():
        js = js.replace(k, v)
    html = ("<!doctype html><html><head><meta charset='utf-8'>\n<style>" + css
            + "</style></head><body>\n" + body + "<script>" + js + "</script>\n</body></html>")
    os.makedirs(SP, exist_ok=True)
    open(OUT, "w", encoding="utf-8").write(html)
    json.dump({"dur": DUR, "scenes": SCENES, "hero": HERO, "beats": sorted(set(HERO + SCENES)),
               "wav": os.path.join(SP, "video", "national-lastround-7s.wav" if SHORT else "national-lastround.wav")},
              open(CUT, "w"))

    # ── captions, from the same figures ─────────────────────────────────────
    x = d(night)
    nice = f"{['Mon','Tue','Wed','Thu','Fri','Sat','Sun'][x.weekday()]} {x.day} {cfg['month'][:3]}"
    lead = when.capitalize() if away <= 1 else f"This {when.capitalize()}"
    top5 = "\n".join(f"{i + 1}. {r['name']} — {r['pts']}" for i, r in enumerate(table[:5]))
    pz = " / ".join(f"{p} OMR" for p in prizes)
    cap = f"""{cfg['name']} — FINAL ROUND film ({nice})
{'=' * 54}
1080x1920 · {DUR:.1f}s · built {today} for a night {away} day(s) away, so it opens on "{when}"
Table from the app's own engine after {ST['played']} nights; every figure is read.

— WHATSAPP —

🏁 *FINAL ROUND — {lead}, {nice}.* Night {n_night} of {cfg['sessions']}, and it pays *DOUBLE POINTS*.

The season prizes are decided on this one night: {pz}.

The table after {WORDS[ST['played']].lower()} nights:
{top5}

The lead has changed hands {changes} time{"" if changes == 1 else "s"} this season; {ldr['name']} {lead_line[len(ldr['name']) + 1:].lower()}.

{spread} points cover 1st to {ORD[n_paid].lower()}. The biggest night anyone has had this season is +{ST['bestNight']}.

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
    print("  contenders: " + ", ".join(f"{r['name']} {r['pts']}{' (face)' if faces.get(r['id']) else ' (initials)'}" for r in c))
    print(f"  race: {changes} lead changes · {lead_line} · spread {spread} · best +{ST['bestNight']}")


CSS = r"""
@@BUNDLE@@
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:@@W@@px;height:@@H@@px;overflow:hidden;background:@@DEEP@@;
  font-family:'Archivo',system-ui,sans-serif;-webkit-font-smoothing:antialiased;color:@@IVORY@@}
body{position:relative}
#sky{position:absolute;inset:0;z-index:0;background:
  radial-gradient(120% 70% at 50% 38%, @@BG@@ 0%, @@DEEP@@ 55%, #5A0A10 100%)}
#rays{position:absolute;left:50%;top:38%;width:2600px;height:2600px;margin:-1300px 0 0 -1300px;z-index:0;opacity:.16;
  background:repeating-conic-gradient(from 0deg, rgba(255,236,214,.55) 0deg 4deg, rgba(255,236,214,0) 4deg 15deg);
  -webkit-mask:radial-gradient(circle, #000 0%, rgba(0,0,0,.6) 30%, transparent 62%);
          mask:radial-gradient(circle, #000 0%, rgba(0,0,0,.6) 30%, transparent 62%)}
#tile{position:absolute;inset:-340px 0 0 0;opacity:.13;pointer-events:none;z-index:0;
  background-image:url("@@KHANJAR@@");background-size:340px 340px}
#vig{position:absolute;inset:0;z-index:1;pointer-events:none;
  background:radial-gradient(120% 90% at 50% 45%, transparent 55%, rgba(30,0,4,.55) 100%)}
.band{position:absolute;left:36px;right:36px;height:56px;border-radius:28px;pointer-events:none;
  z-index:10;background-color:@@DEEP@@;background-image:url("@@MASAR@@");
  background-size:100px 56px;background-repeat:repeat-x}
.band.t{top:18px} .band.b{bottom:18px;transform:scaleY(-1)}
#sparks{position:absolute;inset:0;z-index:2;pointer-events:none}
.sp{position:absolute;top:0;left:0;border-radius:50%;background:#FFE2B8;box-shadow:0 0 12px 3px rgba(255,200,140,.55)}
#stage{position:absolute;inset:0;z-index:3}
.scene{position:absolute;inset:0;z-index:3}
.blk{position:absolute;left:0;right:0;text-align:center}
.disp{font-style:italic;font-variation-settings:'wdth' 125,'wght' 900;line-height:.88;text-transform:uppercase}
.mono{font-family:'JetBrains Mono',monospace;font-weight:700;text-transform:uppercase}
.kufi{font-family:'Noto Kufi Arabic',sans-serif;font-weight:700}
.k{font-size:26px;letter-spacing:.3em;color:@@ROSE@@}
.arch{background:@@IVORY@@;color:@@INK@@;border-radius:50% 50% 28px 28px / 34% 34% 28px 28px;
  box-shadow:0 0 0 7px @@BG@@,0 0 0 11px @@IVORY@@,0 30px 60px rgba(40,0,6,.45);overflow:hidden}
.flag{display:inline-flex;align-items:center;justify-content:center;border-radius:10px;padding:10px 28px 10px 44px;
  background-image:linear-gradient(90deg,@@FLAG@@ 0 22px,transparent 22px),
    linear-gradient(180deg,#FFFFFF 0 34%,@@FLAG@@ 34% 66%,@@GREEN@@ 66% 100%);box-shadow:0 0 0 4px @@INK@@}
.flag .n{color:#FFFFFF;-webkit-text-stroke:4px @@INK@@;paint-order:stroke fill;letter-spacing:-.02em}
.med{position:absolute;border-radius:50%;background-color:@@BG@@;background-repeat:no-repeat;background-position:center 54%;
  background-size:62% auto;box-shadow:0 0 0 3px @@IVORY@@,0 0 0 7px @@GREEN@@;background-image:url("@@LM@@")}

/* 1 · FINAL ROUND inside a door */
#s1door{position:absolute;left:140px;top:300px}
#s1a{top:400px}
#s1k{top:610px}
#s1b{top:690px;font-size:240px}
#s1c{top:930px;font-size:240px}
#s1d{top:1210px;font-size:54px;left:190px;right:190px}
#s1e{top:1310px;font-size:42px;color:@@ROSE@@}
#s1b .fitspan,#s1c .fitspan{text-shadow:0 10px 0 rgba(40,0,6,.35)}

/* 2 · the contenders */
#s2a{top:196px}
#s2med{left:50%;margin-left:-58px;top:244px;width:116px;height:116px;z-index:4}
.ph{position:absolute;inset:0;background-size:114% auto;background-repeat:no-repeat;background-position:center 8%}
.noface{display:flex;align-items:center;justify-content:center;background:@@DEEP@@;color:@@IVORY@@;font-size:120px}
.gloss{position:absolute;inset:0;background-repeat:no-repeat;background-size:300% 100%;background-position:100% 0;
  background-image:linear-gradient(100deg,rgba(255,255,255,0) 40%,rgba(255,255,255,.38) 50%,rgba(255,255,255,0) 60%)}
#c1{position:absolute;left:250px;top:300px;width:580px;height:600px}
.rk{position:absolute;border-radius:50%;background:@@GREEN@@;color:#FFF;display:flex;align-items:center;justify-content:center;
  box-shadow:0 0 0 5px @@IVORY@@;z-index:5;width:96px;height:96px;font-size:54px}
.rk.sm{width:72px;height:72px;font-size:40px;background:@@INK@@}
#c1r{left:218px;top:820px}
#c1n{top:938px;font-size:76px}
#c1p{top:1024px;font-size:28px;letter-spacing:.2em;color:@@ROSE@@}
.arch.small{position:absolute;top:1110px;width:340px;height:380px;border-radius:50% 50% 24px 24px / 30% 30% 24px 24px}
#c2{left:150px} #c3{left:590px}
#c2r{left:126px;top:1438px} #c3r{left:566px;top:1438px}
.chip{position:absolute;top:1126px;padding:8px 14px;border-radius:999px;background:@@INK@@;color:@@IVORY@@;
  font-size:24px;letter-spacing:.06em;z-index:5}
#c2g{left:400px} #c3g{left:840px}
.sname{position:absolute;top:1516px;width:340px;text-align:center;font-size:44px;white-space:nowrap}
#c2n{left:150px} #c3n{left:590px}
.spts{position:absolute;top:1574px;width:340px;text-align:center;font-size:26px;letter-spacing:.18em;color:@@ROSE@@}
#c2p{left:150px} #c3p{left:590px}

/* 3 · the chart */
#s6a{top:230px}
#s6plate{position:absolute;top:300px;left:64px;right:64px;background:@@IVORY@@;border-radius:44px;
  box-shadow:0 0 0 7px @@BG@@,0 0 0 11px @@IVORY@@,0 30px 60px rgba(40,0,6,.45);padding:20px 0 14px;overflow:hidden}
#s6svg{display:block;margin:0 auto}
#s6svg .ax{font-family:'JetBrains Mono',monospace;font-weight:700;font-size:24px;fill:@@MUTED@@}
#s6svg .nm2{font-family:'JetBrains Mono',monospace;font-weight:700;font-size:23px;letter-spacing:.02em}
#s6svg .pv{font-family:'Archivo',sans-serif;font-style:italic;font-variation-settings:'wdth' 125,'wght' 900;font-size:36px}
#s6n{top:1250px;font-size:30px;letter-spacing:.2em;color:@@IVORY@@}
#s6b{top:1340px;font-size:32px;letter-spacing:.16em;color:@@IVORY@@}
#s6c{top:1404px;font-size:30px;letter-spacing:.16em;color:@@ROSE@@}

/* 4 · the money */
#s4a{top:230px;font-size:24px}
#s4plate{position:absolute;top:300px;left:64px;right:64px;background:@@IVORY@@;border-radius:44px;
  box-shadow:0 0 0 7px @@BG@@,0 0 0 11px @@IVORY@@,0 30px 60px rgba(40,0,6,.45);padding:16px 34px}
.mr{display:flex;align-items:center;gap:18px;height:168px;border-top:2px solid rgba(26,10,12,.10)}
.mr:first-child{border-top:0}
.mo{flex:0 0 74px;font-size:30px;letter-spacing:.06em;color:@@MUTED@@}
.mf{position:relative;flex:0 0 108px;width:108px;height:108px;border-radius:50%;background-size:cover;background-position:center 6%;
  box-shadow:0 0 0 4px @@BG@@}
.mf.noface{font-size:40px}
.mh{flex:1 1 0;min-width:0;display:flex;flex-direction:column;gap:6px;text-align:left}
.mhn{font-size:28px;color:@@INK@@;white-space:nowrap;overflow:hidden}
.mhp{font-size:22px;color:@@MUTED@@;letter-spacing:.1em}
.ma{font-size:116px;color:@@BG@@;flex:0 0 auto;text-align:right;min-width:150px}
.mu{font-size:24px;letter-spacing:.12em;color:@@INK@@;flex:0 0 auto}
#s4arch{position:absolute;top:920px;left:180px;right:180px;height:440px;display:flex;flex-direction:column;
  align-items:center;justify-content:center;gap:24px;padding-top:56px}
#s4n{font-size:240px;color:@@BG@@;line-height:.84}
#s4u{font-size:26px;letter-spacing:.14em;color:@@INK@@}
#s4b{top:1450px;font-size:50px}

/* 5 · 2X */
#s7x{top:470px;font-size:560px;line-height:.9;color:@@IVORY@@;-webkit-text-stroke:10px @@INK@@;paint-order:stroke fill;
  text-shadow:0 22px 0 rgba(40,0,6,.45)}
.ring{position:absolute;left:50%;top:760px;width:600px;height:600px;margin:-300px 0 0 -300px;border-radius:50%;
  border:10px solid @@IVORY@@;opacity:0}
#s7b{top:1150px;font-size:120px}
#s7c{top:1310px;font-size:30px;letter-spacing:.22em;color:@@ROSE@@}

/* 6 · the ask */
#s5a{top:330px}
#s5b{top:420px;font-size:150px}
#s5c{top:630px;font-size:60px}
#s5arch{position:absolute;top:800px;left:110px;right:110px;height:380px;display:flex;flex-direction:column;
  align-items:center;justify-content:center;gap:12px;padding-top:40px}
#s5t1{font-size:88px;color:@@INK@@}
#s5t2{font-size:88px;color:@@BG@@}
#s5d{top:1290px;font-size:48px}
#s5e{top:1400px;font-size:32px;letter-spacing:.2em;color:@@ROSE@@}

/* the door wipe and the flash */
#wipe{position:absolute;left:-60px;right:-60px;bottom:0;height:0;z-index:8;pointer-events:none;
  border-radius:50% 50% 0 0 / 280px 280px 0 0;background:@@IVORY@@;overflow:hidden}
#wipe2{position:absolute;left:0;right:0;bottom:0;height:0;background:@@DEEP@@;
  border-radius:50% 50% 0 0 / 260px 260px 0 0}
#flash{position:absolute;inset:0;z-index:9;background:#FFF6EA;opacity:0;pointer-events:none}
"""

JS = r"""
const DUR = @@DUR@@, SCENES = @@SCENES@@, BASE = @@BASE@@, HERO = @@HERO@@, GAP = @@GAP@@, CH = @@CHART@@;
window.__dur = DUR; window.__scenes = SCENES;
const E = id => document.getElementById(id);
const clamp = (x,a,b) => x < a ? a : x > b ? b : x;
const expo = u => { u = clamp(u,0,1); return u >= 1 ? 1 : 1 - Math.pow(2, -10 * u); };
const back = u => { u = clamp(u,0,1); const c = 1.4, v = u - 1; return 1 + (c + 1) * v * v * v + c * v * v; };
const ease = u => 1 - Math.pow(1 - clamp(u,0,1), 3);
const mix = (a,b,u) => a + (b - a) * u;

function reveal(el, u, wide) {
  const e = expo(u), h = el.offsetHeight || 1, dd = (1 - e) * h;
  el.style.opacity = u <= 0 ? 0 : 1;
  el.style.transform = 'translateY(' + dd.toFixed(2) + 'px)';
  el.style.clipPath = u >= 1 ? 'none' : 'inset(-40px -80px ' + dd.toFixed(2) + 'px -80px)';
  if (wide) {
    const sp = el.querySelector('.fitspan') || el;
    sp.style.fontVariationSettings = "'wdth' " + (104 + 21 * e).toFixed(1) + ",'wght' 900";
  }
}
function fade(el, u, dy) {
  const e = expo(u);
  el.style.opacity = clamp(u * 2.2, 0, 1);
  el.style.transform = 'translateY(' + ((1 - e) * (dy == null ? 14 : dy)).toFixed(2) + 'px)';
}
// a word that lands: big and blurred, then hard on its mark. It stays faint
// while it is oversized, so nothing legible ever stands past the frame.
function slam(el, u, from, rot) {
  const e = expo(u);
  el.style.opacity = clamp((u - 0.1) * 3, 0, 1);
  el.style.transform = 'scale(' + mix(from || 1.6, 1, e).toFixed(4) + ')' + (rot ? ' rotate(' + ((1 - e) * rot).toFixed(2) + 'deg)' : '');
  el.style.filter = u >= 1 ? 'none' : 'blur(' + ((1 - e) * 14).toFixed(2) + 'px)';
}
function pop(el, u, spin) {
  const e = back(u);
  el.style.opacity = clamp(u * 3, 0, 1);
  el.style.transform = 'scale(' + (0.4 + 0.6 * e).toFixed(4) + ')' + (spin ? ' rotate(' + ((1 - expo(u)) * spin).toFixed(2) + 'deg)' : '');
}
// a surface rising out of the floor
function rise(el, u, dist) {
  const e = expo(u);
  el.style.opacity = u <= 0 ? 0 : clamp(u * 3, 0, 1);
  el.style.transform = 'translateY(' + ((1 - e) * (dist || 160)).toFixed(2) + 'px)';
}
// a portrait settling into its arch, and a sheen across it — both drawn as
// BACKGROUND motion, because a transformed child overflows its arch and the
// recorder (rightly) reads that as content cut off
function push(el, uz, ug) {
  el.querySelector('.ph').style.backgroundSize = mix(114, 100, ease(uz)).toFixed(2) + '% auto';
  el.querySelector('.gloss').style.backgroundPosition = mix(100, 0, clamp(ug, 0, 1)).toFixed(1) + '% 0';
}
function count(el, u) { el.textContent = Math.round(+el.dataset.n * expo(u)); }

function fitAll() {
  const scenes = [...document.querySelectorAll('.scene')];
  const was = scenes.map(el => el.style.display);
  scenes.forEach(el => { el.style.display = 'block'; });
  for (const s of document.querySelectorAll('.fitspan')) {
    const box = s.parentElement, room = box.clientWidth - 96;
    let px = parseFloat(getComputedStyle(box).fontSize);
    s.style.whiteSpace = 'nowrap'; s.style.display = 'inline-block';
    s.style.fontVariationSettings = "'wdth' 125,'wght' 900";
    if (room <= 0) throw new Error('fit: ' + box.id + ' has no width');
    while (s.getBoundingClientRect().width > room && px > 10) { px -= 2; box.style.fontSize = px + 'px'; }
    if (px <= 10) throw new Error('fit: ' + box.id + ' hit the floor');
  }
  // .fitbox: a name in a fixed-width column, shrunk to its own box
  for (const s of document.querySelectorAll('.fitbox')) {
    const box = s.parentElement; let px = parseFloat(getComputedStyle(box).fontSize);
    s.style.display = 'inline-block';
    while (s.getBoundingClientRect().width > box.clientWidth - 12 && px > 20) { px -= 1; box.style.fontSize = px + 'px'; }
  }
  scenes.forEach((el, k) => { el.style.display = was[k]; });
}
function sceneAt(t) { let i = 0; for (let k = 0; k < SCENES.length; k++) if (t >= SCENES[k]) i = k; return i; }
const SC = [...document.querySelectorAll('.scene')];
const SPARK = [...document.querySelectorAll('.sp')];
const PATHS = [...document.querySelectorAll('#s6svg .rl')];
const HEADS = [...document.querySelectorAll('#s6svg .hd')].map(g => ({ g, pts: JSON.parse(g.dataset.path) }));
PATHS.forEach(p => { p.__len = p.getTotalLength(); });
function along(pts, f) {          // a point f of the way along a polyline, by length
  if (pts.length < 2) return pts[0];
  let tot = 0; const seg = [];
  for (let i = 1; i < pts.length; i++) { const l = Math.hypot(pts[i][0] - pts[i-1][0], pts[i][1] - pts[i-1][1]); seg.push(l); tot += l; }
  let want = tot * clamp(f, 0, 1);
  for (let i = 0; i < seg.length; i++) {
    if (want <= seg[i] || i === seg.length - 1) { const u = seg[i] ? clamp(want / seg[i], 0, 1) : 0;
      return [mix(pts[i][0], pts[i+1][0], u), mix(pts[i][1], pts[i+1][1], u)]; }
    want -= seg[i];
  }
  return pts[pts.length - 1];
}

window.__seek = function (t) {
  t = clamp(t, 0, DUR);
  const i = sceneAt(t), t0 = SCENES[i];
  const last = i + 1 >= SCENES.length;
  const t1 = last ? DUR : SCENES[i + 1], len = t1 - t0;
  // a scene shorter than its own clock (the short cut) runs faster, and
  // finishes with a beat to spare rather than on the cut
  const S = (t - t0) * (len < BASE[i] ? BASE[i] / len * 1.18 : 1);

  // the world: slow drift, rays turning, sparks rising — all pure functions of t
  E('tile').style.transform = 'translateY(' + ((t * 22) % 340).toFixed(1) + 'px)';
  E('rays').style.transform = 'rotate(' + (t * 6).toFixed(2) + 'deg)';
  for (const s of SPARK) {
    const v = +s.dataset.v, ph = (+s.dataset.s + t * 0.11 * v) % 1, y = 1980 - ph * 2100;
    const x = +s.dataset.x + Math.sin(t * 1.3 * v + +s.dataset.s * 9) * 26, z = +s.dataset.z;
    s.style.width = s.style.height = z + 'px';
    s.style.opacity = (Math.sin(ph * Math.PI) * 0.85).toFixed(3);
    s.style.transform = 'translate(' + x.toFixed(1) + 'px,' + y.toFixed(1) + 'px)';
  }
  // the camera: a slow push, and a kick on every hero hit
  let kick = 0;
  for (const h of HERO) { const dt = t - h; if (dt >= 0 && dt < 0.35) kick = Math.max(kick, 1 - dt / 0.35); }
  const sx = Math.sin(t * 91) * 12 * kick * kick, sy = Math.cos(t * 77) * 9 * kick * kick;
  E('stage').style.transform = 'translate(' + sx.toFixed(1) + 'px,' + sy.toFixed(1) + 'px) scale(' + (1 + 0.012 * (t - t0) / len).toFixed(5) + ')';
  E('flash').style.opacity = (kick > 0.85 ? (kick - 0.85) * 1.0 : 0).toFixed(3);

  // THE DOOR WIPE: an ivory arch with a red one inside it rises over the cut, then lifts away
  let wh = 0, wh2 = 0, off = 0;
  for (let k = 1; k < SCENES.length; k++) {
    const a = t - SCENES[k];
    if (a > -0.22 && a < 0.22) {
      const up = a < 0 ? ease((a + 0.22) / 0.22) : 1;
      off = a >= 0 ? ease(a / 0.22) : 0;
      wh = up * 2300; wh2 = Math.max(0, up * 2300 - 90);
    }
  }
  E('wipe').style.height = wh.toFixed(1) + 'px'; E('wipe2').style.height = wh2.toFixed(1) + 'px';
  E('wipe').style.transform = 'translateY(' + (-off * 2300).toFixed(1) + 'px)';

  SC.forEach((el, k) => { el.style.display = (k === i) ? 'block' : 'none'; });

  if (i === 0) {
    for (const p of [E('s1dp'), E('s1dq')]) {
      const L = p.getTotalLength();
      p.style.strokeDasharray = L; p.style.strokeDashoffset = (L * (1 - ease(S / 0.9))).toFixed(1);
    }
    pop(E('s1a'), (S - 0.30) / 0.45, -10);
    fade(E('s1k'), (S - 0.45) / 0.40);
    slam(E('s1b'), (S - 0.55) / 0.34);
    slam(E('s1c'), (S - 0.75) / 0.34);
    reveal(E('s1d'), (S - 1.15) / 0.55);
    fade(E('s1e'), (S - 1.45) / 0.45);
  } else if (i === 1) {
    fade(E('s2a'), S / 0.35);
    rise(E('c1'), (S - 0.05) / 0.70, 220);
    pop(E('s2med'), (S - 0.40) / 0.45, 30);
    push(E('c1'), S / 2.4, (S - 0.7) / 0.9);
    pop(E('c1r'), (S - 0.55) / 0.40);
    reveal(E('c1n'), (S - 0.55) / 0.55, true);
    fade(E('c1p'), (S - 0.70) / 0.40); count(E('c1p').firstElementChild, (S - 0.70) / 0.80);
    for (const [k, at] of [[2, 1.05], [3, 1.25]]) {
      rise(E('c' + k), (S - at) / 0.60, 260);
      push(E('c' + k), (S - at) / 2.0, (S - at - 0.5) / 0.8);
      pop(E('c' + k + 'r'), (S - at - 0.30) / 0.40);
      pop(E('c' + k + 'g'), (S - at - 0.45) / 0.40, 12);
      fade(E('c' + k + 'n'), (S - at - 0.25) / 0.45);
      fade(E('c' + k + 'p'), (S - at - 0.35) / 0.45); count(E('c' + k + 'p').firstElementChild, (S - at - 0.35) / 0.8);
    }
  } else if (i === 2) {
    fade(E('s6a'), S / 0.35);
    rise(E('s6plate'), (S - 0.05) / 0.60, 120);
    const p = clamp((S - 0.50) / 1.90, 0, 1), pe = 1 - Math.pow(1 - p, 2);
    PATHS.forEach(el => {
      if (el.dataset.k === '4') { el.style.clipPath = 'inset(-20px ' + ((1 - pe) * 100).toFixed(2) + '% -20px -20px)'; return; }
      el.style.strokeDasharray = el.__len; el.style.strokeDashoffset = (el.__len * (1 - pe)).toFixed(2);
    });
    for (const h of HEADS) {
      const [x, y] = along(h.pts, pe);
      h.g.setAttribute('transform', 'translate(' + x.toFixed(1) + ',' + y.toFixed(1) + ')');
      h.g.style.opacity = p > 0 ? 1 : 0;
    }
    E('s6nn').textContent = 1 + Math.min(CH.n - 1, Math.floor(pe * (CH.n - 1) + 0.0001));
    E('scan').setAttribute('transform', 'translate(' + mix(CH.x0, CH.x1, pe).toFixed(1) + ',0)');
    E('scan').style.opacity = p > 0 && p < 1 ? 0.6 : 0;
    fade(E('s6n'), (S - 0.50) / 0.30);
    document.querySelectorAll('#s6svg .rlab').forEach(el => { el.style.opacity = clamp((S - 2.35 - (+el.dataset.k) * 0.05) / 0.30, 0, 1); });
    fade(E('s6b'), (S - 2.50) / 0.40);
    fade(E('s6c'), (S - 2.70) / 0.40);
  } else if (i === 3) {
    fade(E('s4a'), S / 0.35);
    rise(E('s4plate'), (S - 0.05) / 0.60, 120);
    for (let k = 0; k < 3; k++) {
      const r = E('mr' + k), uu = (S - 0.30 - k * 0.14) / 0.50, ee = expo(uu);
      r.style.opacity = clamp(uu * 2.4, 0, 1);
      r.style.transform = 'translateX(' + (-(1 - ee) * 70).toFixed(2) + 'px)';
      count(r.querySelector('.ma'), (S - 0.36 - k * 0.14) / 0.70);
    }
    rise(E('s4arch'), (S - 0.95) / 0.60, 200);
    E('s4n').textContent = Math.round(GAP * expo((S - 1.10) / 0.70));
    reveal(E('s4b'), (S - 1.60) / 0.55);
  } else if (i === 4) {
    slam(E('s7x'), (S - 0.05) / 0.30, 1.4, -8);
    for (const [k, at] of [[1, 0.20], [2, 0.32], [3, 0.46]]) {
      const u = clamp((S - at) / 0.9, 0, 1), r = E('ring' + k);
      r.style.opacity = u > 0 && u < 1 ? (1 - u) * 0.8 : 0;
      r.style.transform = 'scale(' + (0.3 + ease(u) * 2.1).toFixed(3) + ')';
    }
    reveal(E('s7b'), (S - 0.40) / 0.50, true);
    fade(E('s7c'), (S - 0.70) / 0.40);
  } else {
    fade(E('s5a'), S / 0.35);
    reveal(E('s5b'), (S - 0.08) / 0.70, true);
    reveal(E('s5c'), (S - 0.30) / 0.60);
    rise(E('s5arch'), (S - 0.48) / 0.65, 200);
    fade(E('s5t1'), (S - 0.80) / 0.45);
    fade(E('s5t2'), (S - 0.95) / 0.45);
    reveal(E('s5d'), (S - 1.10) / 0.60);
    fade(E('s5e'), (S - 1.35) / 0.50);
  }
};
document.fonts.ready.then(() => { fitAll(); window.__seek(0); window.__ready = true; });
window.__seek(0);
"""

if __name__ == "__main__":
    main()
