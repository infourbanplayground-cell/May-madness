# -*- coding: utf-8 -*-
"""Small comparison card: Session 9 group stage, the four leading teams.

Figures are taken as they stand in the app right now — no corrections applied.

  python3 build-session9-compare.py
"""
import base64, os, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = "/tmp/certs/fonts"
BRAND = os.path.join(HERE, "brand", "august-attack")
OUT = os.path.join(HERE, "brand", "session9-compare.html")

COURT, DEEP = "#0A0C12", "#06070B"
RED, CYAN, CHALK, STEEL = "#FF2E43", "#3DE1FF", "#F4F6FA", "#8B95A7"

# player, team, group, W-L, group points (all games), GD, session points
ROWS = [
    ("Muntaser Hasni",   "Muntaser & Aimen", "B", "4–0", 12, 17, 20),
    ("Faisal Al Harthi", "Faisal & Talal",   "C", "3–1", 11, 11, 20),
    ("Munther Rahbi",    "Munther & Ahmed",  "A", "3–1", 10,  8, 18),
    ("Hamed Amri",       "Hamed & Mustafa",  "C", "3–1", 10,  8, 18),
]


def b64(p):
    with open(p, "rb") as f:
        return base64.b64encode(f.read()).decode()


def face(fam, w, fn):
    return (f"@font-face{{font-family:'{fam}';font-weight:{w};font-display:block;"
            f"src:url(data:font/woff2;base64,{b64(os.path.join(FONTS, fn))}) format('woff2');}}")


faces = "".join([
    face("Anton", 400, "anton-400.woff2"),
    face("Archivo", 600, "archivo-600.woff2"),
    face("Archivo", 800, "archivo-800.woff2"),
    face("Archivo", 900, "archivo-900.woff2"),
    face("Mono", 500, "jbmono-500.woff2"),
    face("Mono", 700, "jbmono-700.woff2"),
])

rows_html = ""
for i, (player, team, grp, wl, pts, gd, tot) in enumerate(ROWS):
    lead = tot == 20
    acc = RED if lead else STEEL
    rows_html += f"""
    <div class="row" style="border-left:5px solid {acc};">
      <div class="rk" style="color:{acc};">{i+1}</div>
      <div class="who">
        <div class="pl">{player}</div>
        <div class="tm">{team} <span class="gp">· GROUP {grp}</span></div>
      </div>
      <div class="stat"><span class="lab">W–L</span><span class="val">{wl}</span></div>
      <div class="stat"><span class="lab">GRP PTS</span><span class="val">{pts}</span></div>
      <div class="stat"><span class="lab">GAME DIFF</span><span class="val">+{gd}</span></div>
      <div class="tot" style="color:{acc};">{tot}</div>
    </div>"""

html = f"""<!doctype html><html><head><meta charset="utf-8"><style>
{faces}
*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{width:1200px;height:648px;overflow:hidden}}
body{{background:radial-gradient(ellipse 90% 60% at 50% 0%, #131826 0%, {COURT} 60%), {COURT};
  font-family:'Archivo',sans-serif;color:{CHALK};position:relative;
  -webkit-print-color-adjust:exact;print-color-adjust:exact;padding:40px 52px;}}
.grid{{position:absolute;inset:0;opacity:.05;
  background-image:linear-gradient({CHALK} 1px,transparent 1px),linear-gradient(90deg,{CHALK} 1px,transparent 1px);
  background-size:60px 60px;}}
.floor{{position:absolute;left:0;right:0;bottom:0;height:180px;
  background:linear-gradient(to bottom, rgba(6,7,11,0), {DEEP});}}
.wrap{{position:relative}}
.head{{display:flex;align-items:center;justify-content:space-between;margin-bottom:6px}}
.wm{{height:48px}}
.chip{{font-family:'Mono';font-weight:700;font-size:14px;letter-spacing:.2em;
  color:{COURT};background:{RED};padding:9px 16px}}
.kick{{font-family:'Mono';font-weight:700;font-size:13px;letter-spacing:.32em;color:{STEEL};margin-top:12px}}
h1{{font-family:'Anton';font-size:62px;line-height:.95;letter-spacing:.02em;
  text-transform:uppercase;margin-top:6px}}
h1 span{{color:{RED}}}
.rows{{margin-top:22px;display:flex;flex-direction:column;gap:10px}}
.row{{display:grid;grid-template-columns:56px 1fr 120px 130px 150px 130px;align-items:center;
  gap:14px;background:rgba(244,246,250,.045);padding:13px 20px;}}
.rk{{font-family:'Anton';font-size:34px;line-height:1;text-align:center}}
.who{{min-width:0}}
.pl{{font-weight:900;font-size:23px;letter-spacing:.01em;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
.tm{{font-family:'Mono';font-weight:500;font-size:14px;color:{STEEL};margin-top:4px;
  white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
.gp{{color:rgba(139,149,167,.65)}}
.stat{{display:flex;flex-direction:column;gap:5px;align-items:center}}
.lab{{font-family:'Mono';font-weight:700;font-size:11px;letter-spacing:.18em;color:{STEEL}}}
.val{{font-family:'Mono';font-weight:700;font-size:23px}}
.tot{{font-family:'Anton';font-size:50px;line-height:1;text-align:right;letter-spacing:.01em}}
.note{{position:absolute;left:52px;right:52px;bottom:30px;display:flex;justify-content:space-between;
  align-items:flex-end;gap:24px}}
.note p{{font-size:14px;color:{STEEL};line-height:1.6;max-width:800px}}
.note b{{color:{CHALK};font-weight:800}}
.pts{{font-family:'Mono';font-weight:700;font-size:12px;letter-spacing:.22em;color:{STEEL};
  border:1px solid rgba(244,246,250,.18);padding:8px 14px;white-space:nowrap}}
</style></head><body>
<div class="grid"></div><div class="floor"></div>
<div class="wrap">
  <div class="head">
    <img class="wm" src="data:image/png;base64,{b64(os.path.join(BRAND,'aa-wordmark-full-colour@4x.png'))}">
    <div class="chip">SESSION 9</div>
  </div>
  <div class="kick">GROUP STAGE · BEFORE KNOCKOUTS</div>
  <h1>THE TOP <span>FOUR</span></h1>
  <div class="rows">{rows_html}</div>
</div>
<div class="note">
  <p>All four hit the <b>9-point ceiling</b> — only your best 3 group games count,
     so a bigger group is never an advantage. The gap is the <b>top-of-group bonus</b>,
     doubled on a 2× night.</p>
  <div class="pts">⚡ 2× POINTS SESSION</div>
</div>
</body></html>"""

with open(OUT, "w") as f:
    f.write(html)
print(f"built {OUT} ({len(html)/1024/1024:.1f}MB)")
