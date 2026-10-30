# -*- coding: utf-8 -*-
"""Blackout Series (Vol.8) placement certificates, 1st through 5th.

A4 landscape, print-ready: a 300 DPI PNG for preview and sharing, packed into a
PDF page at exactly 297 x 210mm for the print shop.

This is Vol.7's certificate re-cut for Vol.8 rather than a new design, the same
way the app inherits its markup volume to volume. What changes is what the
volume changes:

  - Palette. Deep Current -> true black #050505, Surge Cyan -> lime #C6FF00.
    Lime leads; magenta is the rare one and appears on the champion's sheet
    only. Violet (uv) is a STRUCTURE colour here and is never set as type —
    3.1:1 on #050505 fails at body size.
  - Geometry. Radius 0 everywhere except the seal, which is a deliberate
    circle. Vol.7's soft accent rules become hard bars and corner ticks.
  - NO SOFT GLOWS. Vol.7's numeral carried a 4mm and an 18mm shadow.
    build-blackout-brand.py already records why that is wrong in print:
    Chromium tiles big blurred shadows and the seams print as hard-edged
    rectangles. The placement here is carried by size and colour alone.
  - Texture. Vol.7's horizontal surge trace gives way to Vol.8's tactical
    grid and scanline field — the app's own page texture.

PLACEMENT IS CARRIED BY THE NUMERAL AND THE LABEL, NOT BY FADING. Vol.7 records
stepping 4th and 5th down to a dimmer accent and it printed washed out, which is
the wrong thing for a certificate somebody keeps. All five sheets lead lime;
what changes down the five is the numeral, the label, and whether the second
voice is magenta (the champion, because magenta is the one thing that scores) or
violet (the rest, because violet is structure). There is no gold/silver/bronze:
it is not in this palette.

THE NAMES AND THE FIGURES ARE READ, NEVER TYPED. `--standings` takes the JSON
`ops/blackout-standings.mjs` writes, which runs the app's own engine over the
live state, so a certificate cannot award a placement or print a total that the
leaderboard contradicts. And it REFUSES to put a name on a sheet while a night
is still to play, because the season is not decided until it has been — pass
`--provisional` to override, and the sheet says so in magenta.

  python3 build-blackout-certificates.py                        # blank name lines
  python3 build-blackout-certificates.py --standings $SP/bo-standings.json
  python3 build-blackout-certificates.py --standings ... --provisional
  python3 build-blackout-certificates.py --places 1 2 3
"""
import argparse, base64, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "ops"))
from font_bundle import bundle as font_bundle          # noqa: E402

BRAND = os.path.join(HERE, "brand", "blackout")
OUT = os.path.join(HERE, "brand", "certificates-blackout")
SEASON = os.path.join(HERE, "blackout-season.json")

# ── Palette (blackout-season.json, which is the single source of truth) ────
_S = json.load(open(SEASON))
PAL = _S["palette"]
BG      = PAL["bg"]          # #050505
LIME    = PAL["lime"]        # #C6FF00  — 17.1:1 on black, the lead
LIMEPALE= PAL["limePale"]
MAGENTA = PAL["magenta"]     # #FF2E88  — the rare one: the thing that scores
UV      = PAL["uv"]          # #7B2BFF  — STRUCTURE ONLY, never type
INK     = PAL["ink"]
MUTED   = PAL["muted"]
MUTED2  = PAL["muted2"]
# Every field that gets filled in by hand sits on a light plate, because black
# pen on #050505 is invisible. Not pure white: a hair of warmth stops it
# glaring against the black field and reads as a label stock.
PLATE      = "#EFEFEA"
PLATE_EDGE = "#B4B4AE"
PLATE_INK  = "#0A0A0A"

PLACES = {
    1: dict(ord_="1ST", word="FIRST",  label="SERIES CHAMPION", second=MAGENTA),
    2: dict(ord_="2ND", word="SECOND", label="RUNNER-UP",       second=UV),
    3: dict(ord_="3RD", word="THIRD",  label="PODIUM FINISH",   second=UV),
    4: dict(ord_="4TH", word="FOURTH", label="TOP FIVE",        second=UV),
    5: dict(ord_="5TH", word="FIFTH",  label="TOP FIVE",        second=UV),
}

MONTHS = ("January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October", "November", "December")


def b64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()


def long_date(iso):
    y, m, d = (int(x) for x in iso.split("-"))
    return f"{d} {MONTHS[m-1]} {y}"


def seal(second, mark_b64, volume):
    """The one deliberate circle on the sheet.

    Arc text is SVG textPath — CSS cannot set type on a circle. BOTH arcs run
    left to right: the bottom one takes sweep 0 from the left point, which
    traces the LOWER arc. Carrying on clockwise from the right point sets the
    words mirrored, which is how the first UPRISING seal came out.
    """
    return f"""<svg class="sealsvg" viewBox="0 0 400 400" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <path id="arcTop" d="M 60 200 A 140 140 0 0 1 340 200"/>
    <path id="arcBot" d="M 62 200 A 138 138 0 0 0 338 200"/>
  </defs>
  <circle cx="200" cy="200" r="176" fill="none" stroke="{LIME}" stroke-width="2.5" opacity=".9"/>
  <circle cx="200" cy="200" r="166" fill="none" stroke="rgba(242,242,242,.26)" stroke-width="1"/>
  <circle cx="200" cy="200" r="124" fill="none" stroke="{second}" stroke-opacity=".40" stroke-width="1.2"/>
  <text font-family="'JetBrains Mono', monospace" font-size="21" font-weight="700"
        letter-spacing="4.4" fill="{INK}" opacity=".92">
    <textPath href="#arcTop" startOffset="50%" text-anchor="middle">URBAN PLAYGROUND</textPath>
  </text>
  <text font-family="'JetBrains Mono', monospace" font-size="16" font-weight="700"
        letter-spacing="3.0" fill="{LIME}" opacity=".95">
    <textPath href="#arcBot" startOffset="50%" text-anchor="middle">BLACKOUT SERIES · {volume}</textPath>
  </text>
  <image href="data:image/png;base64,{mark_b64}" x="148" y="148" width="104" height="104"
         preserveAspectRatio="xMidYMid meet"/>
</svg>"""


def stat_strip(row, second):
    """POINTS / NIGHTS / NIGHTS WON, straight off the engine's own table.

    Vol.7's sheet carried no figures at all, which made it a template somebody
    had filled in rather than a record of what happened. These three are the
    ones the app's own player card leads with, and every one of them is read
    from `ops/blackout-standings.mjs` — a certificate that can disagree with
    the leaderboard is worse than one that says nothing.
    """
    cells = [("POINTS", row["pts"]), ("NIGHTS", row["nights"]),
             ("NIGHTS WON", row["titles"])]
    inner = "".join(
        f'<div class="cell"><div class="num">{v}</div>'
        f'<div class="cap">{k}</div></div>' for k, v in cells)
    return f'<div class="stats" style="--second:{second}">{inner}</div>'


def build_html(place, season, name=None, row=None, date_str=None, provisional=False):
    p = PLACES[place]
    second = p["second"]
    faces = font_bundle()
    wordmark = b64(os.path.join(BRAND, "blackout-lockup-transparent.png"))
    mark = b64(os.path.join(BRAND, "blackout-mark-transparent.png"))
    volume = season["volume"]
    nights = season["sessions"]
    date_str = date_str or long_date(season["finalsDate"])

    # The top rule and the kicker are the loud parts of the sheet, so they are
    # what carries the warning: a provisional certificate must be impossible to
    # mistake for a final one at arm's length, not footnoted at the bottom.
    kicker = "CERTIFICATE OF ACHIEVEMENT"
    kick_colour = LIME
    rule_colour = LIME
    if provisional:
        kicker = "PROVISIONAL · THE SEASON IS NOT FINISHED"
        kick_colour = rule_colour = MAGENTA

    # A typed name replaces the ruled line; otherwise the line stays blank so
    # the organiser can write it in. Both are deliberate states, not a fallback.
    typed = f'<div class="typed">{name}</div>' if name else ""
    strip = stat_strip(row, second) if row else ""

    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
{faces}
@page {{ size: A4 landscape; margin: 0; }}
*{{margin:0;padding:0;box-sizing:border-box;border-radius:0;}}
html,body{{width:297mm;height:210mm;overflow:hidden;}}
body{{
  background:{BG};
  font-family:'Archivo',system-ui,sans-serif;
  color:{INK};
  -webkit-print-color-adjust:exact; print-color-adjust:exact;
  position:relative; overflow:hidden;
}}
.layer{{position:absolute;inset:0;pointer-events:none;}}

/* Vol.8's page texture, as the app draws it: a tactical grid and a scanline
   field. Both are hard-edged, which is the whole point — the brand art already
   records that soft glows tile in Chromium's print path and the seams show. */
.grid{{background:
   repeating-linear-gradient(0deg,  rgba(198,255,0,.055) 0 .18mm, transparent .18mm 12mm),
   repeating-linear-gradient(90deg, rgba(198,255,0,.055) 0 .18mm, transparent .18mm 12mm);}}
.scan{{background:repeating-linear-gradient(0deg,
    rgba(198,255,0,.030) 0 .20mm, transparent .20mm 1.1mm);}}
/* One violet wash, low and wide. uv is a structure colour, so it is a surface
   under the type and never the type itself. */
.wash{{background:linear-gradient(to bottom, transparent 54%, rgba(123,43,255,.16) 100%);}}

.edge{{position:absolute;inset:7mm;border:.6pt solid rgba(242,242,242,.14);}}
.rule{{position:absolute;top:7mm;left:7mm;right:7mm;height:2.4mm;background:{rule_colour};}}
.rulebot{{position:absolute;bottom:7mm;left:7mm;right:7mm;height:.9mm;background:{LIME};}}
/* The app's card marker is four corner ticks, 16x2px. Same marker, in mm. */
.tick{{position:absolute;background:{LIME};}}
.t-h{{width:11mm;height:1.1mm;}} .t-v{{width:1.1mm;height:11mm;}}

.wrap{{position:relative;height:100%;display:flex;flex-direction:column;
  align-items:center;justify-content:flex-start;padding:13mm 26mm 56mm;text-align:center;}}

.wordmark{{height:19mm;}}
.vol{{font-family:'JetBrains Mono',monospace;font-weight:700;font-size:7.6pt;
  letter-spacing:.34em;color:{MUTED};text-transform:uppercase;margin-top:3.4mm;}}

.kickwrap{{display:flex;align-items:center;gap:5mm;margin-top:5.4mm;}}
.kickwrap .ln{{width:22mm;height:.7pt;background:{kick_colour};opacity:.5;}}
.kicker{{font-family:'JetBrains Mono',monospace;font-weight:700;font-size:7.4pt;
  letter-spacing:.40em;color:{kick_colour};white-space:nowrap;}}

/* Vol.8's display face, and no shadow of any kind. */
.place{{font-family:'Archivo',sans-serif;font-style:italic;
  font-variation-settings:'wdth' 125,'wght' 900;
  letter-spacing:.004em;line-height:.92;
  font-size:58pt;color:{LIME};margin-top:1.4mm;}}

.labelrow{{display:flex;align-items:center;gap:0;margin-top:2.2mm;}}
.label{{font-family:'Archivo',sans-serif;font-weight:900;font-size:10.5pt;
  letter-spacing:.30em;color:{BG};text-transform:uppercase;
  padding:2.0mm 7mm;background:{LIME};}}
.labelcap{{width:2.2mm;height:7.2mm;background:{second};}}

.awarded{{font-size:9pt;color:{MUTED};margin-top:5.4mm;letter-spacing:.04em;}}

.plate{{position:relative;background:{PLATE};border:.6pt solid {PLATE_EDGE};}}
/* A cap bar in lime along the top edge, so the plate reads as a labelled field
   belonging to the frame rather than as a white box dropped on the sheet. */
.plate::before{{content:"";position:absolute;left:0;right:0;top:0;height:.9mm;
  background:{LIME};}}
.nameplate{{width:168mm;height:15mm;margin:3.8mm auto 0;}}
.namehint{{font-family:'JetBrains Mono',monospace;font-size:6.2pt;letter-spacing:.30em;
  color:{MUTED2};margin-top:2.2mm;text-transform:uppercase;}}
.nameplate .typed{{position:absolute;inset:0;display:flex;align-items:center;
  justify-content:center;font-style:italic;
  font-variation-settings:'wdth' 112,'wght' 900;
  font-size:20pt;line-height:1;color:{PLATE_INK};white-space:nowrap;}}

.stats{{display:flex;gap:0;margin-top:4.6mm;}}
.cell{{width:38mm;padding:2.4mm 0 2.6mm;border:.6pt solid rgba(242,242,242,.16);
  border-left-width:0;}}
.cell:first-child{{border-left-width:.6pt;}}
.cell .num{{font-family:'JetBrains Mono',monospace;font-weight:700;font-size:15pt;
  line-height:1;color:{LIME};}}
.cell .cap{{font-family:'JetBrains Mono',monospace;font-weight:700;font-size:5.8pt;
  letter-spacing:.26em;color:{MUTED};margin-top:1.8mm;}}

.body{{font-size:8.8pt;color:{MUTED};margin-top:4.6mm;max-width:160mm;line-height:1.65;}}
.body b{{color:{INK};font-weight:800;}}

/* A single centred stack at the foot: seal, award date, imprint. Vol.7 records
   flanking the seal with a date plate and a director plate and the three
   crowding each other, so there is one column and no director box. */
.sealsvg{{position:absolute;left:50%;bottom:25mm;transform:translateX(-50%);
  width:30mm;height:30mm;}}
.issued{{position:absolute;left:0;right:0;bottom:15.4mm;text-align:center;
  font-family:'JetBrains Mono',monospace;font-weight:700;font-size:7.2pt;
  letter-spacing:.28em;color:{INK};text-transform:uppercase;}}
.issued span{{color:{LIME};}}
.serial{{position:absolute;left:0;right:0;bottom:10mm;text-align:center;
  font-family:'JetBrains Mono',monospace;font-size:5.8pt;letter-spacing:.28em;
  color:{MUTED2};text-transform:uppercase;}}
</style></head><body>
<div class="layer grid"></div>
<div class="layer scan"></div>
<div class="layer wash"></div>
<div class="edge"></div>
<div class="rule"></div><div class="rulebot"></div>
<div class="tick t-h" style="left:7mm;top:12.4mm"></div>
<div class="tick t-v" style="left:7mm;top:12.4mm"></div>
<div class="tick t-h" style="right:7mm;top:12.4mm"></div>
<div class="tick t-v" style="right:7mm;top:12.4mm"></div>
<div class="tick t-h" style="left:7mm;bottom:12.4mm"></div>
<div class="tick t-v" style="left:7mm;bottom:12.4mm"></div>
<div class="tick t-h" style="right:7mm;bottom:12.4mm"></div>
<div class="tick t-v" style="right:7mm;bottom:12.4mm"></div>

<div class="wrap">
  <img class="wordmark" src="data:image/png;base64,{wordmark}" alt="Blackout Series">
  <div class="vol">Urban Playground · {season['monthUpper'].title()} {season['finalsDate'][:4]} · Muscat</div>

  <div class="kickwrap">
    <span class="ln"></span>
    <span class="kicker">{kicker}</span>
    <span class="ln"></span>
  </div>
  <div class="place">{p['ord_']} PLACE</div>
  <div class="labelrow">
    <span class="labelcap"></span>
    <span class="label">{p['label']}</span>
    <span class="labelcap"></span>
  </div>

  <div class="awarded">This certificate is proudly awarded to</div>
  <div class="plate nameplate">{typed}</div>
  <div class="namehint">Name</div>
  {strip}

  <div class="body">
    for finishing <b>{p['word']}</b> in the <b>Blackout Series</b> at Urban Playground —
    earned across {nights} nights of group play and knockouts.
  </div>
</div>

{seal(second, mark, volume)}
<div class="issued">Awarded <span>{date_str}</span></div>
<div class="serial">{"Provisional · not a final result · " if provisional else ""}Blackout Series · {volume} · Urban Playground · Muscat, Oman</div>
</body></html>"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--places", nargs="*", type=int, default=[1, 2, 3, 4, 5])
    ap.add_argument("--standings", help="JSON written by ops/blackout-standings.mjs. "
                                       "Omit for blank name lines and no figures.")
    ap.add_argument("--provisional", action="store_true",
                    help="Allow names while a night is still to play. The sheet says so.")
    ap.add_argument("--date", help="Award date printed on the sheet "
                                   "(default: the season's finals date)")
    a = ap.parse_args()

    season = json.load(open(SEASON))
    table, left = None, []
    if a.standings:
        st = json.load(open(a.standings))
        table, left = st["table"], st.get("remaining", [])
        if left and not a.provisional:
            raise SystemExit(
                f"refusing to print names: {len(left)} night(s) still to play "
                f"({', '.join(left)}).\n"
                f"  The top five is not decided until they have been — 1st to 4th are "
                f"covered by {st.get('gap14', '?')} points.\n"
                f"  Run with no --standings for blank name lines, or --provisional "
                f"to stamp the sheet.")
        need = max(a.places)
        if len(table) < need:
            raise SystemExit(f"standings hold {len(table)} players, need {need}")

    os.makedirs(OUT, exist_ok=True)
    for place in a.places:
        row = table[place - 1] if table else None
        html = build_html(place, season, row["name"] if row else None, row,
                          a.date, provisional=bool(left))
        h = os.path.join(OUT, f"bo-certificate-{place}.html")
        with open(h, "w") as f:
            f.write(html)
        who = f"{row['name']} · {row['pts']} pts" if row else "blank name line"
        print(f"built {os.path.basename(h)}  ({len(html)/1024:.0f}KB)  {who}"
              + ("  [PROVISIONAL]" if left else ""))
    print("\nnow render:  node render-blackout-certificates.mjs")


if __name__ == "__main__":
    main()
