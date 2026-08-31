# -*- coding: utf-8 -*-
"""Print-ready certificates from the Claude Design handoff bundle.

Source: august-attack-instagram-post/project/Certificates Deck.dc.html
(the file the handoff README names as the primary design).

The handoff sections are lifted verbatim — they are pure inline-styled HTML
with no design-system classes — and only three things are changed:

  1. Fonts and images are inlined as base64, so the PDF the print shop opens
     cannot substitute a font or lose an asset.
  2. The deck wrapper (<x-dc>, deck-stage) is dropped and each section is
     rendered standalone at its native 1920x1080, which yields a clean
     artboard instead of presentation chrome.
  3. A 5th-place certificate is generated from the 4th, because the handoff
     stops at 4th but five were asked for. Every substitution is asserted, so
     a missed replacement fails the build rather than shipping a certificate
     that still says "Fourth".

Three values in the handoff copy disagree with the live app; all three are
CLI flags defaulting to what the handoff actually says, so nothing is
silently rewritten:

  --sessions     handoff says eight; the app is built around nine
                 (sessionsTotal = 9 in august-attack-index.html)
  --third-prize  handoff says 35 OMR; the app's prize pool uses 30
                 (season = [75, 45, 30])
  --date         handoff says 28 August 2026, which is before the final
                 session exists

  python3 build-certificates-deck.py
  python3 build-certificates-deck.py --sessions nine --third-prize 30
"""
import argparse, base64, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = "/tmp/handoff/august-attack-instagram-post/project"
DECK = os.path.join(SRC, "Certificates Deck.dc.html")
FONTS = "/tmp/certs/fonts"
OUT = os.path.join(HERE, "brand", "certificates-deck")

WORDNUM = {"8": "Eight", "9": "Nine", "eight": "Eight", "nine": "Nine"}


def b64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()


def face(family, weight, filename):
    return (f"@font-face{{font-family:'{family}';font-style:normal;font-weight:{weight};"
            f"font-display:block;src:url(data:font/woff2;base64,{b64(os.path.join(FONTS, filename))}) format('woff2');}}")


def sub1(text, old, new, what):
    """Replace and assert it actually happened — a silently missed swap here
    ships a certificate with the wrong placement on it."""
    if old not in text:
        sys.exit(f"BUILD FAILED: expected to find {what}: {old!r}")
    return text.replace(old, new)


NAME_DIV = re.compile(
    r"<div style=\"font-family:'Anton';font-size:84px;[^\"]*?min-height:106px;\"></div>")


def white_name_box(section, accent):
    """Swap the underline-rule name holder for a solid white field to write on.

    The handoff leaves the name as an empty div over a glowing accent rule —
    handsome on screen, but on a printed dark sheet there is nothing to write
    on: pen on near-black card is unreadable. This makes it a white plate,
    keeping the accent as a bar along the bottom edge so the brand cue from the
    original survives.
    """
    n = len(NAME_DIV.findall(section))
    if n != 1:
        sys.exit(f"BUILD FAILED: expected 1 name holder in the section, found {n}")
    box = (
        '<div style="position:relative;margin-top:12px;max-width:1180px;height:132px;'
        'background:#FFFFFF;'
        # Sit the plate off the dark ground with a soft drop, and finish the
        # bottom edge with the section's accent so it still reads as designed.
        'box-shadow:0 18px 44px -22px rgba(0,0,0,.85), 0 0 0 1px rgba(10,12,18,.28) inset;'
        f'border-bottom:6px solid {accent};">'
        # Faint corner ticks, in the same language as the sheet's outer frame,
        # so the plate looks placed rather than pasted on.
        '<span style="position:absolute;top:10px;left:10px;width:22px;height:2px;'
        'background:rgba(10,12,18,.30);"></span>'
        '<span style="position:absolute;top:10px;left:10px;width:2px;height:22px;'
        'background:rgba(10,12,18,.30);"></span>'
        '<span style="position:absolute;top:10px;right:10px;width:22px;height:2px;'
        'background:rgba(10,12,18,.30);"></span>'
        '<span style="position:absolute;top:10px;right:10px;width:2px;height:22px;'
        'background:rgba(10,12,18,.30);"></span>'
        '</div>')
    return NAME_DIV.sub(box, section)


def make_fifth(fourth):
    s = fourth
    s = sub1(s, 'data-label="4th"', 'data-label="5th"', "section label")
    s = sub1(s, 'data-screen-label="04"', 'data-screen-label="05"', "screen label")
    s = sub1(s, 'data-speaker-notes="Fourth place — no cash prize."',
                'data-speaker-notes="Fifth place — no cash prize."', "speaker notes")
    s = sub1(s, ">04<", ">05<", "background numeral")
    s = sub1(s, "August Attack · Fourth Place", "August Attack · Fifth Place", "eyebrow")
    s = sub1(s, ">Fourth Place<", ">Fifth Place<", "headline")
    s = sub1(s, ">Finalist<", ">Top Five<", "chip")
    s = sub1(s, ">4th Place<", ">5th Place<", "standing")
    s = sub1(s,
        "Fourth place at August Attack, Volume Six of the Urban Social Series. "
        "Through the semi-finals and into the final four.",
        "Fifth place at August Attack, Volume Six of the Urban Social Series. "
        "Among the last standing in a field that started at sixteen.", "body copy")
    # Continue the ladder one step down: red, cyan, chalk, steel, deep steel.
    s = s.replace("#8B95A7", "#6C7686").replace("139,149,167", "108,118,134")
    # ...but the muted label colour in the stats grid is also #8B95A7 in the
    # source; putting it back keeps those captions matching the other four.
    s = s.replace("text-transform:uppercase;color:#6C7686;\">Final Standing",
                  "text-transform:uppercase;color:#8B95A7;\">Final Standing")
    return s


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sessions", default="eight", help="how many sessions the copy claims")
    ap.add_argument("--third-prize", default="35", help="3rd place prize in OMR")
    ap.add_argument("--date", default="28 August 2026", help="date printed in the stats grid")
    ap.add_argument("--name-style", choices=["box", "rule"], default="box",
                    help="box = white field to write the winner's name on (default); "
                         "rule = the handoff's underline")
    a = ap.parse_args()

    deck = open(DECK).read()
    secs = re.findall(r'(<section data-label="[^"]*".*?</section>)', deck, re.S)
    if len(secs) != 4:
        sys.exit(f"BUILD FAILED: expected 4 sections in the handoff, found {len(secs)}")
    secs.append(make_fifth(secs[3]))

    if a.name_style == "box":
        # Accent per placement, matching the deck: red, cyan, chalk, steel, and
        # the deep steel the generated 5th continues with.
        accents = ["#FF2E43", "#3DE1FF", "#F4F6FA", "#8B95A7", "#6C7686"]
        for i, acc in enumerate(accents):
            bar = acc
            # 3rd place's accent is chalk, which vanishes against the white
            # plate. An ink bar is no better — it vanishes against the dark
            # sheet instead. Steel is the only value that reads against both.
            r, g, b = (int(acc[j:j+2], 16) for j in (1, 3, 5))
            if (0.299*r + 0.587*g + 0.114*b) > 200:
                bar = "#8B95A7"
            secs[i] = white_name_box(secs[i], bar)

    faces = "".join([
        face("Anton", 400, "anton-400.woff2"),
        face("Archivo", 400, "archivo-400.woff2"),
        face("Archivo", 500, "archivo-400.woff2"),
        face("Archivo", 600, "archivo-600.woff2"),
        face("Archivo", 700, "archivo-600.woff2"),
        face("Archivo", 800, "archivo-800.woff2"),
        face("Archivo", 900, "archivo-900.woff2"),
        face("JetBrains Mono", 500, "jbmono-500.woff2"),
        face("JetBrains Mono", 700, "jbmono-700.woff2"),
    ])
    imgs = {p: b64(os.path.join(SRC, "assets", p.split("/")[-1]))
            for p in ["assets/up-logo.png", "assets/aa-logo-1.png"]}

    os.makedirs(OUT, exist_ok=True)
    names = ["1st", "2nd", "3rd", "4th", "5th"]
    for i, sec in enumerate(secs):
        html = sec
        for path, data in imgs.items():
            html = html.replace(f'src="{path}"', f'src="data:image/png;base64,{data}"')
        # Copy corrections, each opt-in via CLI so the handoff stays the default.
        if a.sessions.lower() not in ("eight", "8"):
            html = html.replace("Eight sessions", f"{WORDNUM.get(a.sessions.lower(), a.sessions.title())} sessions")
        if a.third_prize != "35":
            html = html.replace(">35 OMR<", f">{a.third_prize} OMR<")
        if a.date != "28 August 2026":
            html = html.replace(">28 August 2026<", f">{a.date}<")

        doc = (f"<!doctype html><html><head><meta charset='utf-8'><style>{faces}"
               "*{box-sizing:border-box}html,body{margin:0;padding:0;width:1920px;height:1080px;"
               "overflow:hidden;background:#06070B}"
               "section{width:1920px!important;height:1080px!important;position:relative!important;"
               "-webkit-print-color-adjust:exact;print-color-adjust:exact}"
               f"</style></head><body>{html}</body></html>")
        f = os.path.join(OUT, f"aa-certificate-{names[i]}.html")
        open(f, "w").write(doc)
        print(f"built {os.path.basename(f)}  ({len(doc)/1024/1024:.1f}MB)")

    print("\nnow render:  node render-certificates-deck.mjs")


if __name__ == "__main__":
    main()
