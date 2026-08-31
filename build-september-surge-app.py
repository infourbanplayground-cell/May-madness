# -*- coding: utf-8 -*-
"""Derive the September Surge (Vol.7) app from the August Attack (Vol.6) app.

Every volume in this series inherits the previous one's markup — that is how
July Heat became August Attack. Doing it as a script rather than a hand-fork
means Vol.6 fixes can be pulled forward by re-running this, and every
substitution is asserted, so a rename that stops matching fails the build
instead of shipping a half-rebranded app.

What it does NOT change: the scoring engine, the bracket seeding, the API
contract. Vol.7 runs the same rules on its own data (ss_* tables, port 3008).

  python3 build-september-surge-app.py
"""
import os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "august-attack-index.html")
DST = os.path.join(HERE, "september-surge-index.html")

# ── Palette: Attack (red-led, court black) -> Surge (cyan-led, deep current) ──
# Two passes via sentinels, because the old secondary (#3DE1FF) and the new
# primary (#00E5FF) are both cyans — a naive sequential replace would collide.
# Tokens are read out of surge-index.html's :root, which is the page built to
# the September Surge design language — not invented here. Surge is a two-colour
# system: cyan leads, amber supports. August's red was the lead, so red -> cyan;
# August's cyan was its second voice (crowns, trophies, badges, the glitch pair),
# so it becomes amber. No third accent is introduced.
COLOURS = [
    # was                     sentinel      becomes      what it is
    ("#FF2E43", "@@P@@", "#00E5FF"),   # lead: Attack Red -> Surge Cyan
    ("#3DE1FF", "@@S@@", "#FF9E1B"),   # support: Ice -> Strike Amber
    ("#1FA8C4", "@@S2@@", "#C77A12"),  # deep variant of the support accent
    ("#8DE8F5", "@@S3@@", "#FFC46B"),  # soft variant of the support accent
    ("#0A0C12", "@@BG@@", "#0A0F14"),  # Court Black -> Deep Current
    ("#06070B", "@@BG2@@", "#050709"), # Deep Black -> Void
    ("#F4F6FA", "@@FG@@", "#F4F9FA"),  # Chalk -> Voltage White
    ("#8B95A7", "@@MU@@", "#8A9BA8"),  # Steel -> Deep Steel (prose weight)
]
# The same colours again as rgb() triples, which the app uses inside rgba().
RGBS = [
    ("255,46,67", "@@RP@@", "0,229,255"),
    ("61,225,255", "@@RS@@", "255,158,27"),
    ("10,12,18", "@@RBG@@", "10,15,20"),
    ("6,7,11", "@@RBG2@@", "5,7,9"),
    ("244,246,250", "@@RFG@@", "244,249,250"),
    ("139,149,167", "@@RMU@@", "138,155,168"),
]
# Motion and depth also differ. Surge overshoots slightly where Attack eased
# flat, and its glow is wider and softer than Attack's tight 14px halo.
MOTION = [
    ("cubic-bezier(.23,1,.32,1)", "cubic-bezier(.34,1.56,.64,1)"),
    ("0 0 14px rgba(0,229,255,.32)",
     "0 0 40px rgba(0,229,255,.24), 0 0 90px rgba(0,229,255,.12)"),
]

# ── Display face. Attack stands tall (Anton); Surge leans forward — Archivo
# pushed wide, heavy and italic, the same treatment surge-index.html uses. This
# is the biggest single "is it Surge or is it Attack in cyan paint" lever, so it
# is done properly rather than left as a colour swap. Both the CSS and the JSX
# inline-style forms are declaration lists, so siblings can be added safely.
# Matched by regex, not exact strings: the Vol.6 app writes this declaration in
# at least five shapes (CSS and JSX, with and without spaces, with 'cursive' or
# 'Impact,sans-serif' fallbacks), and an exact-match table silently missed 35 of
# them on the first attempt — leaving most of the app still standing tall.
DISPLAY_RE = [
    # CSS:  font-family:'Anton',cursive   /   font-family: 'Anton', Impact, sans-serif
    (re.compile(r"font-family:\s*'Anton'[^;}\"']*"),
     "font-family:'Archivo',sans-serif;font-style:italic;"
     "font-variation-settings:'wdth' 118,'wght' 900"),
    # JSX:  fontFamily: "'Anton',cursive"
    (re.compile(r'fontFamily:\s*"\'Anton\'[^"]*"'),
     'fontFamily:"\'Archivo\',sans-serif",fontStyle:"italic",'
     'fontVariationSettings:"\'wdth\' 118,\'wght\' 900"'),
    # The splash preloads the display face by name before first paint.
    (re.compile(r'document\.fonts\.load\("(\d+)px \'Anton\'"\)'),
     r'document.fonts.load("italic \1px Archivo")'),
    # The shareable player card is drawn on a canvas, where the display face is
    # a font shorthand string rather than a CSS declaration. Missing this would
    # leave every card players post to WhatsApp still set in Attack's face.
    (re.compile(r"px \'Anton\', Impact, sans-serif`"),
     "px 'Archivo', sans-serif`"),
    (re.compile(r"ctx\.font = `\$\{([^}]+)\}px 'Archivo', sans-serif`"),
     r"ctx.font = `italic 900 ${\1}px 'Archivo', sans-serif`"),
    (re.compile(r"/\* ── Fonts: Anton for all display text ── \*/"),
     "/* ── Fonts: Archivo, leaned forward, for all display text ── */"),
]
DISPLAY = [
    # Load the variable axes Surge needs instead of Anton. The static Archivo
    # request that Vol.6 also made is dropped in the same step — the variable
    # axes cover every weight it asked for, and requesting the family twice in
    # one URL just fetches a second overlapping face.
    ("family=Anton&", "family=Archivo:ital,wdth,wght@0,62..125,400..900;1,62..125,400..900&"),
    ("family=Archivo:ital,wght@0,400;0,500;0,600;0,700;0,800;0,900;1,700;1,800&", ""),
]

# ── Assets. The Surge lockup replaces the Attack wordmark; the cyan Urban
# Playground emblem (already on this subdomain) replaces the Attack emblem. ──
ASSETS = [
    ("assets/aa-wordmark.png", "assets/surge-lockup.png"),
    ("assets/aa-emblem.png", "assets/up-logo-cyan.png"),
    ("assets/jh-watermark.png", "assets/surge-lockup.png"),   # splash mark
    ("assets/up-logo.png", "assets/up-logo-cyan.png"),
    ("assets/og-cover.png", "assets/surge-og.png"),
]

# ── Wording. Deliberately NOT replacing the bare word "August", which appears
# in real dates and in copy about the previous volume. ──
TEXT = [
    ("AUGUST ATTACK", "SEPTEMBER SURGE"),
    ("August Attack", "September Surge"),
    ("attack.urbanpadel.om", "surge.urbanpadel.om"),
    ("VOL.6", "VOL.7"),
    ("Vol.6", "Vol.7"),
    ("Vol. 6", "Vol. 7"),
    # Month-bound copy: these run in meta descriptions, the mock signup card and
    # the generated WhatsApp posts, so leaving them would have Vol.7 telling
    # players it runs "all August".
    ("all August", "all September"),
    ("ALL AUGUST", "ALL SEPTEMBER"),
    # Vol.6's tagline. Surge's is set in DESIGN.md / the landing page.
    ("SERVE FIRST. <b>STRIKE HARD.</b>", "RIDE <b>THE SURGE.</b>"),
    # The tagline recurs in three casings across the season config and the
    # generated WhatsApp posts, which is what the organiser actually sends out.
    ("Serve First. Strike Hard.", "Ride The Surge."),
    ("Serve first. Strike hard.", "Ride the surge."),
    ("URBAN SOCIAL SERIES · VOL. 6", "URBAN SOCIAL SERIES · VOL. 7"),
    ("VOL. 6", "VOL. 7"),
    # Vol.6 shipped with Vol.5 as its "previous series"; Vol.7's is Vol.6.
    ('"June Fury", "July Heat"]', '"June Fury", "July Heat", "August Attack"]'),
    ("July Heat is done and dusted", "August Attack is done and dusted"),
    # Vol.6 told players their previous *series* points carried over. For Vol.7
    # only the all-time total does: the series table starts at zero, while
    # prevSeriesPts keeps every earlier volume alive in the all-time ranking.
    # Saying either half alone would be wrong, so the line says both.
    ("Your *July Heat* points carry over — but the throne is wide open 👑",
     "Series points reset to *zero* — your *all-time* total carries over 👑"),
    ("🏆 *July Heat final standings:*\nheat.urbanpadel.om → Leaderboard",
     "🏆 *August Attack final standings:*\nattack.urbanpadel.om → Leaderboard"),
]


def main():
    s = open(SRC).read()
    orig_len = len(s)
    report = []

    # Colours, sentinel round-trip so old/new cyans cannot collide.
    for table in (COLOURS, RGBS):
        for old, sent, _ in table:
            for variant in ({old, old.upper(), old.lower()} if old.startswith("#") else {old}):
                s = s.replace(variant, sent)
        for old, sent, new in table:
            n = s.count(sent)
            s = s.replace(sent, new)
            if n:
                report.append(f"  colour {old:<12} -> {new:<12} {n:>5}")

    for rx, new in DISPLAY_RE:
        s, n = rx.subn(new, s)
        if n:
            report.append(f"  display {rx.pattern[:44]:<44} {n:>4}")

    for old, new in DISPLAY:
        n = s.count(old)
        if n:
            s = s.replace(old, new)
            report.append(f"  display {old[:44]:<44} {n:>4}")

    for old, new in MOTION:
        n = s.count(old)
        if n:
            s = s.replace(old, new)
            report.append(f"  motion {old[:34]:<34} -> {new[:26]:<26} {n:>3}")

    # The three copies of the emblem carried inline as base64 are ~950KB of a
    # 1.6MB file (DESIGN.md flags this). Vol.7 points them at the asset instead,
    # which is both correct branding and a large cut to every cold load.
    b64 = re.search(r'const UP_LOGO_FULL = "data:image/png;base64,[A-Za-z0-9+/=]+";', s)
    if not b64:
        sys.exit("BUILD FAILED: could not find the inline UP_LOGO_FULL constant")
    saved = len(b64.group(0))
    s = s.replace(b64.group(0), 'const UP_LOGO_FULL = "assets/up-logo-cyan.png";')
    report.append(f"  inlined emblem -> assets/up-logo-cyan.png  (-{saved/1024:.0f}KB)")

    for old, new in ASSETS:
        n = s.count(old)
        if n:
            s = s.replace(old, new)
            report.append(f"  asset  {old:<26} -> {new:<26} {n:>3}")

    # Class names too. DESIGN.md's standing complaint about this codebase is
    # that "class names lie" — the Vol.6 app is full of .jh-* classes inherited
    # from July Heat. Since this fork is mechanical, rename rather than add
    # another volume's worth of misleading selectors.
    for old, new in [("aa-wordmark", "surge-lockup-img"), ("aa-emblem", "surge-emblem")]:
        n = s.count(old)
        s = s.replace(old, new)
        report.append(f"  class  .{old:<21} -> .{new:<21} {n:>3}")

    for old, new in TEXT:
        n = s.count(old)
        if not n:
            sys.exit(f"BUILD FAILED: expected to rename {old!r} but found none — "
                     f"has the Vol.6 app been reworded?")
        s = s.replace(old, new)
        report.append(f"  text   {old:<22} -> {new:<22} {n:>3}")

    # Anything left over would ship as Vol.6 branding on a Vol.7 site.
    #
    # Two Vol.6 references are legitimate and deliberate: Vol.7 names Vol.6 as
    # its predecessor, the way Vol.6 named July Heat. Those are pinned to exact
    # counts rather than waved through, so an accidental leftover still fails.
    EXPECTED = {"August Attack": 3, "attack.urbanpadel.om": 1}
    FORBIDDEN = ["AUGUST ATTACK", "aa-wordmark", "aa-emblem", "jh-watermark",
                 "#FF2E43", "#3DE1FF", "Serve first", "Serve First", "Anton",
                 "VOL. 6", "Vol.6", "all August", "heat.urbanpadel.om"]

    bad = {p: s.count(p) for p in FORBIDDEN if s.count(p)}
    if bad:
        sys.exit(f"BUILD FAILED: Vol.6/Vol.5 references survived: {bad}")
    for p, want in EXPECTED.items():
        got = s.count(p)
        if got != want:
            sys.exit(f"BUILD FAILED: expected exactly {want} reference(s) to {p!r} "
                     f"(Vol.7 citing its predecessor), found {got}")
    report.append(f"  kept   {EXPECTED} as predecessor references")

    open(DST, "w").write(s)
    print("\n".join(report))
    print(f"\nwrote {os.path.basename(DST)}  {orig_len/1024/1024:.2f}MB -> {len(s)/1024/1024:.2f}MB")


if __name__ == "__main__":
    main()
