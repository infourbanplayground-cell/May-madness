# -*- coding: utf-8 -*-
"""Attendance table, July-September 2026, as a shareable PNG.

Counts are read from the three volumes' live state, not typed in: July Heat,
August Attack and September Surge are separate apps with separate tables, so the
quarter only exists once the three are put side by side.

A player counts as having played a session if they were on a team in it, which
is the same rule the apps' own `sessionsPlayed` uses.

  python3 build-attendance-table.py && node render-attendance-table.mjs
"""
import base64, json, os

HERE = os.path.dirname(os.path.abspath(__file__))
SP = "/tmp/claude-0/-home-user-May-madness/0e44f0ad-a683-5f0d-9de6-9459ae328963/scratchpad"
FONT_BUNDLE = "/tmp/certs/fonts/bundle.css"
BRAND = os.path.join(HERE, "brand", "september-surge")
OUT = os.path.join(HERE, "brand", "reports")

VOLS = [("jh", "JULY", "July Heat"),
        ("aa", "AUGUST", "August Attack"),
        ("ss", "SEPTEMBER", "September Surge")]

# Stored names per person. Several are registered twice — merged deliberately,
# because otherwise one human's record splits in half and both halves look thin.
# "Aziz" plays as 7up and "Al Khatab" also as KB7 — both confirmed by the owner.
# A night where two of one person's handles both appear still counts once, since
# the count is over sessions, not over registrations.
GROUPS = {
    "Munther Rahbi": ["Munther Rahbi"],
    "Mutaz":         ["Mutaz Zadjali"],
    "Muntaser":      ["Muntaser Hasni"],
    "Aziz":          ["7up"],
    "Muether":       ["Muether Wahaibi"],
    "Mustafa":       ["Mustafa"],
    "Muatasim":      ["Muatasim Sabri", "Muatasim"],
    "Majdi":         ["Majdi"],
    "Al Khatab":     ["AL khatab", "KB7"],
}

INK   = "#0A0F14"
VOID  = "#050709"
CYAN  = "#00E5FF"
CHALK = "#F4F9FA"
STEEL = "#8A9BA8"
DIM   = "#5C6B78"
AMBER = "#FF9E1B"

W, H = 1200, 1220


def b64(p):
    with open(p, "rb") as f:
        return base64.b64encode(f.read()).decode()


def collect():
    rows, totals = {}, {}
    for key, _, _ in VOLS:
        st = json.load(open(f"{SP}/{key}.json"))
        st = st.get("state", st)
        totals[key] = len(st["sessions"])
        byid = {p["id"]: p.get("name", "") for p in st["players"]}
        for label, variants in GROUPS.items():
            ids = {i for i, n in byid.items() if n in variants}
            n = sum(1 for s in st["sessions"]
                    if any(t for t in s.get("teams", [])
                           if t.get("p1Id") in ids or t.get("p2Id") in ids))
            rows.setdefault(label, {})[key] = n
    return rows, totals


def build():
    rows, totals = collect()
    possible = sum(totals.values())
    order = sorted(GROUPS, key=lambda l: -sum(rows[l].values()))
    faces = open(FONT_BUNDLE).read()
    emblem = b64(os.path.join(BRAND, "up-logo-cyan-2x.png"))

    tr = []
    for i, label in enumerate(order):
        tot = sum(rows[label].values())
        pct = tot / possible * 100
        cells = ""
        for key, _, _ in VOLS:
            n = rows[label][key]
            cls = "zero" if n == 0 else ("full" if n == totals[key] else "")
            txt = "—" if n == 0 else f"{n}<span class='of'>/{totals[key]}</span>"
            cells += f'<td class="num {cls}">{txt}</td>'
        # The bar is the share of the whole quarter, so the column reads as a
        # ranking at a glance without anyone having to compare three numbers.
        tr.append(
            f'<tr class="{"top" if i < 4 else ""}">'
            f'<td class="rk">{i+1}</td>'
            f'<td class="nm">{label}</td>'
            f'{cells}'
            f'<td class="tot">{tot}</td>'
            f'<td class="pc"><div class="bar"><i style="width:{pct:.0f}%"></i></div>'
            f'<span>{pct:.0f}%</span></td></tr>')

    heads = "".join(f'<th>{short}<span class="sub">{totals[k]} nights</span></th>'
                    for k, short, _ in VOLS)

    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
{faces}
*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{width:{W}px;height:{H}px;background:{INK};overflow:hidden;
  font-family:'Archivo',sans-serif;color:{CHALK};-webkit-font-smoothing:antialiased}}
body{{background:radial-gradient(ellipse 900px 620px at 50% 26%, #121B23 0%, {INK} 68%), {INK};
  position:relative;padding:52px 56px}}
.trace{{position:absolute;inset:0;pointer-events:none;
  background:repeating-linear-gradient(to bottom, rgba(0,229,255,.045) 0 1px, transparent 1px 14px)}}
.rule{{position:absolute;left:0;right:0;top:0;height:7px;background:{CYAN}}}
header{{position:relative;text-align:center;margin-bottom:34px}}
header img{{height:96px;display:block;margin:0 auto 16px}}
h1{{font-style:italic;font-variation-settings:'wdth' 125,'wght' 900;font-size:74px;
  line-height:.95;letter-spacing:.5px}}
.kick{{font-family:'JetBrains Mono',monospace;font-weight:700;font-size:19px;
  letter-spacing:.34em;color:{CYAN};margin-top:12px}}
table{{position:relative;width:100%;border-collapse:collapse}}
th{{font-family:'JetBrains Mono',monospace;font-weight:700;font-size:15px;
  letter-spacing:.16em;color:{STEEL};padding:0 10px 16px;text-align:center;
  vertical-align:bottom}}
th .sub{{display:block;font-size:11px;letter-spacing:.1em;color:{DIM};
  margin-top:5px;font-weight:500}}
th:nth-child(1),th:nth-child(2){{text-align:left}}
tbody tr{{border-top:1px solid rgba(244,249,250,.09)}}
tbody tr.top{{background:linear-gradient(90deg, rgba(0,229,255,.07), rgba(0,229,255,0))}}
td{{padding:17px 10px;font-size:29px;vertical-align:middle}}
.rk{{width:52px;font-family:'JetBrains Mono',monospace;font-weight:700;
  font-size:22px;color:{DIM}}}
tr.top .rk{{color:{CYAN}}}
.nm{{font-style:italic;font-variation-settings:'wdth' 118,'wght' 900;
  font-size:33px;white-space:nowrap}}
.num{{text-align:center;font-family:'JetBrains Mono',monospace;font-weight:700;
  width:140px;color:{CHALK}}}
.num .of{{font-size:17px;color:{DIM};font-weight:500}}
.num.full{{color:{CYAN}}}
.num.zero{{color:{DIM}}}
.tot{{text-align:center;width:104px;font-family:'JetBrains Mono',monospace;
  font-weight:700;font-size:36px;color:{CYAN}}}
tr:not(.top) .tot{{color:{CHALK}}}
.pc{{width:196px;text-align:right;white-space:nowrap}}
.pc .bar{{display:inline-block;width:112px;height:9px;border-radius:5px;
  background:#131C24;overflow:hidden;vertical-align:middle;margin-right:12px}}
.pc .bar i{{display:block;height:100%;background:{CYAN}}}
.pc span{{font-family:'JetBrains Mono',monospace;font-weight:700;font-size:21px;
  color:{STEEL};vertical-align:middle}}
footer{{position:absolute;left:56px;right:56px;bottom:40px;display:flex;
  justify-content:space-between;align-items:center;
  font-family:'JetBrains Mono',monospace;font-size:15px;letter-spacing:.2em;color:{DIM}}}
footer b{{color:{AMBER};font-weight:700}}
</style></head><body>
<div class="trace"></div><div class="rule"></div>
<header>
  <img src="data:image/png;base64,{emblem}" alt="">
  <h1>ATTENDANCE</h1>
  <div class="kick">JULY &middot; AUGUST &middot; SEPTEMBER 2026</div>
</header>
<table>
  <thead><tr><th></th><th>PLAYER</th>{heads}
    <th>TOTAL<span class="sub">of {possible}</span></th><th></th></tr></thead>
  <tbody>{''.join(tr)}</tbody>
</table>
<footer><span>URBAN PLAYGROUND &middot; MUSCAT</span>
  <span><b>{possible}</b> NIGHTS ACROSS THREE VOLUMES</span></footer>
</body></html>"""


def main():
    os.makedirs(OUT, exist_ok=True)
    p = os.path.join(OUT, "attendance-jul-sep.html")
    with open(p, "w") as f:
        f.write(build())
    print(f"built {os.path.basename(p)}")
    print("now render:  node render-attendance-table.mjs")


if __name__ == "__main__":
    main()
