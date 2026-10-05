# -*- coding: utf-8 -*-
"""Derive the Blackout Series (Vol.8) app from the September Surge (Vol.7) app.

Every volume in this series inherits the previous one's markup — July Heat became
August Attack became September Surge. Doing it as a script rather than a hand-fork
means Vol.7 fixes can be pulled forward by re-running this, and every substitution
is asserted, so a rename that stops matching fails the build instead of shipping a
half-rebranded app.

What it does NOT change: the scoring engine, the bracket seeding, the API
contract. The Blackout handoff is explicit about this — "use the points logic
that already exists in the current production app, do not re-implement or change
the scoring rules" — so the engine is carried across untouched and Vol.8 runs the
same rules on its own data (`bo_*` tables, port 3009).

Season numbers come from blackout-season.json, which the brand art and the
signup posts also read, so none of them can advertise a figure the others
contradict.

  python3 build-blackout-app.py
"""
import hashlib, json, os, re, sys

import blackout_screens as SCREENS

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "september-surge-index.html")
DST = os.path.join(HERE, "blackout-index.html")
CFG = json.load(open(os.path.join(HERE, "blackout-season.json")))
SKIN = os.path.join(HERE, "ops", "blackout-skin.css")

POOL = CFG["voucher"] * 2 * CFG["sessions"] + sum(CFG["seasonPrizes"])
PREV_POOL = 379          # what Vol.7 advertised, which this replaces

# ── Palette: Surge (cyan lead, amber support, deep-current black) ──────────
#            -> Blackout (lime lead, magenta accent, true black)
#
# Two passes via sentinels. A naive sequential replace collides: Surge's amber
# (#FF9E1B) and Blackout's magenta are both warm, and more importantly the
# intermediate values of one rule can match the input of the next.
#
# Blackout is a two-colour system like Surge — lime leads, magenta accents — so
# the mapping is one-for-one and introduces no third voice. Lime carries
# everything positive (qualifiers, wins, live, primary actions); magenta carries
# "you", knockout points, prizes and urgency, which is exactly the load Surge put
# on amber.
COLOURS = [
    # was         sentinel    becomes      what it is
    ("#00E5FF", "@@P@@",   "#C6FF00"),   # lead: Surge Cyan -> Blackout Lime
    ("#FF9E1B", "@@S@@",   "#FF2E88"),   # support: Strike Amber -> Magenta
    ("#C77A12", "@@S2@@",  "#C4215F"),   # deep variant of the support accent
    ("#FFC46B", "@@S3@@",  "#FF8FBE"),   # soft variant of the support accent
    ("#0A0F14", "@@BG@@",  "#0A0A0A"),   # Deep Current -> card black
    ("#050709", "@@BG2@@", "#050505"),   # Void -> app background
    ("#F4F9FA", "@@FG@@",  "#F2F2F2"),   # Voltage White -> Ink
    ("#8A9BA8", "@@MU@@",  "#9A9A9A"),   # Steel Text -> Muted
    ("#9FB0BC", "@@MU2@@", "#CFCFCF"),   # bright steel -> Ink-2
    ("#5C6B78", "@@MU3@@", "#6E6E6E"),   # deep steel -> Muted-2
    ("#38444E", "@@HL@@",  "#2A2A2A"),   # cool hairline -> neutral hairline
    # Strays the Vol.7 sweep left behind, found by auditing what is actually in
    # the file rather than by trusting the previous build's list.
    ("#1B8EE0", "@@X1@@", "#C6FF00"),    # a surviving July blue
    # Lowercase in the source — a case-blind table silently misses them and
    # Tailwind's reds and greens survive into a two-colour brand.
    ("#ef4444", "@@X2@@", "#FF2E88"),    # Tailwind red-500
    ("#10b981", "@@X3@@", "#C6FF00"),    # Tailwind emerald-500
    ("#34d399", "@@X4@@", "#C6FF00"),    # Tailwind emerald-400
    ("#C9CFDA", "@@X5@@", "#CFCFCF"),    # cool light grey
    ("#1c1917", "@@X6@@", "#0E0E0E"),    # Tailwind stone-900 -> card black
    ("#0A0A0A", "@@X7@@", "#0A0A0A"),    # already correct; claimed so the
                                         # #0A0F14 rule cannot reach it
]
# The same colours as rgb() triples, which the app uses inside rgba().
RGBS = [
    ("0,229,255",     "@@RP@@",   "198,255,0"),
    ("255,158,27",    "@@RS@@",   "255,46,136"),
    ("10,15,20",      "@@RBG@@",  "10,10,10"),
    ("5,7,9",         "@@RBG2@@", "5,5,5"),
    ("244,249,250",   "@@RFG@@",  "242,242,242"),
    ("138,155,168",   "@@RMU@@",  "154,154,154"),
    ("92,107,120",    "@@RMU3@@", "110,110,110"),
    ("20,24,36",      "@@RC@@",   "14,14,14"),
    ("9,14,20",       "@@RC2@@",  "10,10,10"),
    ("11,8,20",       "@@RC3@@",  "10,10,10"),
    ("16,185,129",    "@@RG@@",   "198,255,0"),
]

# Motion. Surge overshoots; Blackout's press is tighter and its glow is a hard
# lime halo rather than Surge's wide soft one.
MOTION = [
    ("0 0 40px rgba(198,255,0,.24), 0 0 90px rgba(198,255,0,.12)",
     "0 0 30px rgba(198,255,0,.32)"),
]

# ── Assets ────────────────────────────────────────────────────────────────
ASSETS = [
    # The lockup is served WebP-first from a <picture>, so BOTH references have
    # to move. Renaming only the .png leaves the <source> pointing at Vol.7's
    # .webp, which 404s -- and a <picture> whose chosen source fails shows a
    # broken image rather than falling back to the <img>, so the header mark
    # disappears entirely. That is exactly how this first built.
    ("assets/surge-lockup.webp", "assets/blackout-lockup.webp"),
    ("assets/surge-lockup.png", "assets/blackout-lockup.png"),
    ("assets/up-logo-cyan.png", "assets/up-logo-tight.png"),
    ("assets/surge-og.png", "assets/blackout-og.png"),
]

# ── Wording. Deliberately NOT replacing the bare word "September", which runs
# in real dates and in copy about the previous volume. ──
TEXT = [
    ("SEPTEMBER SURGE", CFG["name"]),
    ("September Surge", CFG["nameTitle"]),
    ("surge.urbanpadel.om", CFG["host"]),
    ("VOL.7", CFG["volume"]),
    ("Vol.7", "Vol.8"),
    ("Vol. 7", "Vol. 8"),
    ("VOL. 7", "VOL. 8"),
    ("URBAN SOCIAL SERIES · VOL. 7", "URBAN SOCIAL SERIES · VOL. 8"),
    # Month-bound copy: these run in meta descriptions, the signup card and the
    # generated WhatsApp posts, so leaving them would have Vol.8 telling players
    # it runs "all September".
    ("all September", "all " + CFG["month"]),
    ("ALL SEPTEMBER", "ALL " + CFG["monthUpper"]),
    # Vol.7's tagline -> Vol.8's.
    ("RIDE THE <b>SURGE.</b>", CFG["taglineHtml"]),
    ("Ride The Surge.", CFG["tagline"]),
    ("Ride the surge.", "Lights out."),
    # Vol.7 shipped with Vol.6 as its "previous series"; Vol.8's is Vol.7.
    ('"June Fury", "July Heat", "August Attack"]',
     '"June Fury", "July Heat", "August Attack", "September Surge"]'),
    ("August Attack is done and dusted", "September Surge is done and dusted"),
    # Vol.7 swapped every navigational arrow to the solid triangle, so these
    # links carry ▶, not →. Placed after the generic renames above: the source
    # names only Vol.6, and plain() is a single ordered pass, so the Vol.7 names
    # this introduces are final and are not swept again.
    ("\U0001F3C6 *August Attack final standings:*\nattack.urbanpadel.om ▶ Leaderboard",
     "\U0001F3C6 *September Surge final standings:*\nsurge.urbanpadel.om ▶ Leaderboard"),
    # The advertised pool is derived, never typed, so the meta tags move with it.
    (f"{PREV_POOL} OMR", f"{POOL} OMR"),
    # The photo watermark and the download filename, which are Vol.SIX's and had
    # survived two rebrands. Nothing matched them because every rename table
    # since has swept the OUTGOING volume's name, and these carried the one
    # before that: Vol.7's table renamed "attack" strings to "surge" only where
    # it happened to name them, and this one renames "surge" strings. So every
    # photo shared out of Surge, and out of Blackout until now, was stamped
    # ATTACK.URBANPADEL.OM — sending anyone who read it to Vol.6's app.
    #
    # The lesson is in the build, not here: see the stray-host check below.
    ("ATTACK.URBANPADEL.OM", CFG["host"].upper()),
    ("august-attack-", "blackout-"),
]

# ── Things the colour sweep gets right and the brand still gets wrong. ───────
# A hex-for-hex swap preserves whatever contrast the previous volume had. Surge
# put near-white on cyan, which was marginal; the same pairing on lime is
# unreadable, because #C6FF00 is far brighter than #00E5FF. These are the places
# that needed a decision, not a substitution.
CONTRAST = [
    # The hero tagline is JSX with a span, not the <b> the signup copy uses.
    ('RIDE <span style={{color:"#C6FF00"}}>THE SURGE.</span>',
     'LIGHTS <span style={{color:"#C6FF00"}}>OUT.</span>'),
    # The volume watermark behind the hero and the splash.
    (">07</div>", ">08</div>"),
    # Seed badge: group winner was white on near-solid lime.
    ('{ bg: "rgba(198,255,0,.9)",   color: "#F2F2F2" }',
     '{ bg: "rgba(198,255,0,.9)",   color: "#050505" }'),
    # Avatar initials. Surge tinted them from a six-colour palette that the
    # sweep left carrying a red, an orange, a purple and a teal — four hues a
    # two-colour brand does not have — and set the text to --cream, which on the
    # two lime entries is white on lime. Blackout keeps the "distinct people"
    # idea but builds it from its own two colours plus four greys, and picks the
    # text colour from the tint's luminance so it can never be unreadable.
    ('const palette = ["#C6FF00", "#B31414", "#C6FF00", "#C77800", "#6B2FB3", "#0E7C7B"];',
     'const palette = ["#C6FF00", "#FF2E88", "#2A2A2A", "#C6FF00", "#3A3A3A", "#FF2E88"];'),
    ('style={{ ...commonStyle, background: tint, color: "var(--cream)",',
     'style={{ ...commonStyle, background: tint,\n'
     '        // Luminance picks the text colour, so a bright tint never gets\n'
     '        // light text. Lime is bright enough that white on it is unreadable.\n'
     '        color: (parseInt(tint.slice(1,3),16)*0.299 + parseInt(tint.slice(3,5),16)*0.587\n'
     '                + parseInt(tint.slice(5,7),16)*0.114) > 140 ? "#050505" : "#F2F2F2",'),
]

# ── Season shape. These are Vol.8's numbers and are SET here, not inherited. ──
SEASON = [
    ("const SESSIONS_TOTAL = 8;", f"const SESSIONS_TOTAL = {CFG['sessions']};"),
    ("const DOUBLE_FROM_SESSION = 7;", f"const DOUBLE_FROM_SESSION = {CFG['doubleFromSession']};"),
    ("const SEASON_PRIZES = [75, 50, 30];",
     "const SEASON_PRIZES = [%s];\n"
     "// The scheduled finals night, so the countdown works before any session\n"
     "// exists -- which is when people are deciding whether to sign up.\n"
     'const FINALS_DATE = "%s";' % (", ".join(str(p) for p in CFG["seasonPrizes"]),
                                    CFG["finalsDate"])),
    # The prose under those constants describes Vol.7's shape — eight nights,
    # session 9 dropped. Left stale it tells the next maintainer the wrong thing
    # about this volume. (The heading itself already says VOL.8: the rename pass
    # above got there first.)
    ("""// These three are Vol.8's numbers, not the standing format. Session 9 was
// dropped mid-series, so Vol.8 runs eight nights (Mondays and Wednesdays) and
// the two double-points nights are 7 and 8 -- the last two, as always.
// A later volume SETS these for itself; it does not inherit them. Nine nights
// with doubles on 8 & 9 and a 75/45/30 season pot is what Vol.6 ran, and is
// what the next one should start from unless it decides otherwise.""",
     """// These three are Vol.8's numbers, not the standing format. Blackout runs
// nine nights -- Mondays and Wednesdays through October, plus a Friday finals
// night -- with the two double-points nights at 8 and 9, the last two, as
// always.
//
// There is NO finals cut this volume: session 9 is open like any other night,
// and the season prizes go to the top three on points. Vol.7 cut to a final
// field; Blackout does not.
//
// A later volume SETS these for itself; it does not inherit them."""),
]

# ── Square. Blackout's defining shape rule is radius 0 everywhere. Doing it in
# the skin alone does not reach React inline styles, which win over a stylesheet,
# so the inline ones are rewritten here and the skin covers the CSS and the
# Tailwind classes. The exceptions the handoff names — status dots, the progress
# ring, the app icon — are circles set with `borderRadius:"50%"`, which this
# leaves alone. ──
RADIUS_KEEP = re.compile(r'borderRadius:\s*"50%"')


def square_inline(s, report):
    """Set every inline borderRadius to 0 except the deliberate circles."""
    n = [0, 0]

    def rep(m):
        if m.group(0).endswith('"50%"'):
            n[1] += 1
            return m.group(0)
        n[0] += 1
        return "borderRadius: 0"

    s = re.sub(r'borderRadius:\s*(?:"[^"]*"|\d+|[A-Za-z_$][\w$]*)', rep, s)
    report(f"square: {n[0]} inline radii zeroed, {n[1]} circles kept")
    assert n[0] > 0, "no inline radii found — has the app's style shape changed?"
    return s


def sweep(s, table, report, label):
    """Two-pass replace through sentinels, so no rule can eat another's output."""
    missing = []
    for old, sent, _ in table:
        if old not in s:
            missing.append(old)
        s = s.replace(old, sent)
    for _, sent, new in table:
        s = s.replace(sent, new)
    assert "@@" not in s, "a sentinel survived the second pass"
    if missing:
        report(f"{label}: {len(table) - len(missing)}/{len(table)} matched; "
               f"not present: {', '.join(missing)}")
    else:
        report(f"{label}: all {len(table)} matched")
    return s


def plain(s, table, report, label, required=True):
    missing = [a for a, _ in table if a not in s]
    for a, b in table:
        s = s.replace(a, b)
    if missing and required:
        raise AssertionError(f"{label}: these no longer match: {missing}")
    report(f"{label}: {len(table) - len(missing)}/{len(table)} matched"
           + (f"; absent: {len(missing)}" if missing else ""))
    return s


def replace_fn(s, name, new_src, report, label):
    """Swap a whole top-level function for a new one, matched by brace depth.

    Used where a component is being rewritten rather than tweaked -- an anchored
    string replace on a 90-line JSX body is a rename away from silently not
    matching, and this fails loudly on the signature instead.
    """
    i = s.find(f"function {name}(")
    assert i >= 0, f"{label}: function {name} not found"
    # Walk the PARAMETER list to its closing paren first. A destructured
    # signature -- function Foo({ a, b }) -- contains braces, and starting the
    # depth count at the first "{" after the name closes on the parameters,
    # cutting the function in half and leaving ") {" dangling in the output.
    pd, k = 0, s.index("(", i)
    for k in range(k, len(s)):
        if s[k] == "(":
            pd += 1
        elif s[k] == ")":
            pd -= 1
            if pd == 0:
                break
    d, j = 0, s.index("{", k)
    for k in range(j, len(s)):
        if s[k] == "{":
            d += 1
        elif s[k] == "}":
            d -= 1
            if d == 0:
                j = k + 1
                break
    report(f"{label}: {name} replaced ({j - i} -> {len(new_src)} bytes)")
    return s[:i] + new_src + s[j:]


# Ship a reviewed subset. SKIP=recap leaves the session-recap package out of the
# build entirely, which is how a court-side fix goes out mid-session without
# carrying screens that have only ever been tested against synthetic data.
SKIP = {x.strip() for x in os.environ.get("SKIP", "").split(",") if x.strip()}


def add_screens(s, report):
    """Splice in the Vol.8 screens: per-event engine, ME, receipts, badges, roster.

    These are the handoff's actual new features. Everything above this point is a
    reskin of Vol.7; this is the part that answers "how did I get my points",
    which is the question the volume was commissioned to answer.
    """
    # Engine goes directly after calcPlayerStats, which it calls to check itself.
    i = s.index("function calcPlayerStats(")
    d, j = 0, s.index("{", i)
    for k in range(j, len(s)):
        if s[k] == "{":
            d += 1
        elif s[k] == "}":
            d -= 1
            if d == 0:
                j = k + 1
                break
    s = s[:j] + SCREENS.ENGINE + s[j:]
    report(f"engine: +{len(SCREENS.ENGINE)} bytes after calcPlayerStats")

    # Views go immediately before App, so every component they use is defined.
    a = s.index("function App() {")
    s = s[:a] + SCREENS.CELEBRATE + SCREENS.COUNTUP + SCREENS.SHARED_SCORE + SCREENS.EXTRAS + SCREENS.CHROME + SCREENS.UIUX + SCREENS.KO_PHOTOS + ("" if "recap" in SKIP else SCREENS.RECAP2) + SCREENS.SHARE + SCREENS.LINEUP + SCREENS.VIEWS + "\n" + s[a:]
    report(f"views: +{len(SCREENS.CHROME) + len(SCREENS.SHARE) + len(SCREENS.VIEWS)} bytes "
           f"before App (chrome + share cards + ME + roster)")

    for name, old, new in (("icon", SCREENS.ICON_OLD, SCREENS.ICON_NEW),
                           ("nav", SCREENS.NAV_OLD, SCREENS.NAV_NEW),
                           ("nav grid", SCREENS.NAVGRID_OLD, SCREENS.NAVGRID_NEW),
                           ("nav button", SCREENS.NAVBTN_OLD, SCREENS.NAVBTN_NEW),
                           ("routes", SCREENS.ROUTE_OLD, SCREENS.ROUTE_NEW),
                           ("app state", SCREENS.APP_STATE_OLD, SCREENS.APP_STATE_NEW),
                           ("app guard", SCREENS.APP_GUARD_OLD, SCREENS.APP_GUARD_NEW),
                           ("main open", SCREENS.APP_MAIN_OLD, SCREENS.APP_MAIN_NEW),
                           ("main close", SCREENS.APP_MAIN_END_OLD, SCREENS.APP_MAIN_END_NEW),
                           ("dash sig", SCREENS.DASH_SIG_OLD, SCREENS.DASH_SIG_NEW),
                           ("countdown", SCREENS.DASH_ANCHOR_OLD, SCREENS.DASH_ANCHOR_NEW),
                           ("recap+prizes", SCREENS.DASH_TAIL_OLD, SCREENS.DASH_TAIL_NEW),
                           ("mvp open", SCREENS.MVP_OLD, SCREENS.MVP_NEW),
                           ("sessions eyebrow", SCREENS.LOGO_SESSIONS_OLD, SCREENS.LOGO_SESSIONS_NEW),
                           ("me eyebrow", SCREENS.LOGO_ME_OLD, SCREENS.LOGO_ME_NEW),
                           ("players eyebrow", SCREENS.LOGO_PLAYERS_OLD, SCREENS.LOGO_PLAYERS_NEW),
                           ("rank eyebrow", SCREENS.LOGO_RANK_OLD, SCREENS.LOGO_RANK_NEW),
                           ("recap eyebrow", SCREENS.LOGO_RECAP_OLD, SCREENS.LOGO_RECAP_NEW),
                           ("sessions table", SCREENS.TABLE_ON_SESSIONS_OLD, SCREENS.TABLE_ON_SESSIONS_NEW),
                           ("ko photos sig", SCREENS.KO_PHOTOS_SIG_OLD, SCREENS.KO_PHOTOS_SIG_NEW),
                           ("ko photos call", SCREENS.KO_PHOTOS_CALL_OLD, SCREENS.KO_PHOTOS_CALL_NEW),
                           ("ko photos strip", SCREENS.KO_PHOTOS_OLD, SCREENS.KO_PHOTOS_NEW),
                           ("ko photos empty", SCREENS.KO_PHOTOS_EMPTY_OLD, SCREENS.KO_PHOTOS_EMPTY_NEW),
                           ("line-up state", SCREENS.LU_STATE_OLD, SCREENS.LU_STATE_NEW),
                           ("line-up chip", SCREENS.LU_ACT_OLD, SCREENS.LU_ACT_NEW),
                           ("line-up sheet", SCREENS.LU_MOUNT_OLD, SCREENS.LU_MOUNT_NEW),
                           ("ko score", SCREENS.KO_SCORE_OLD, SCREENS.KO_SCORE_NEW),
                           ("ko lock", SCREENS.KO_BTN_OLD, SCREENS.KO_BTN_NEW),
                           ("header", SCREENS.HEADER_OLD, SCREENS.HEADER_NEW),
                           ("sync pill", SCREENS.SYNCPILL_OLD, SCREENS.SYNCPILL_NEW),
                           ("sessions sig", SCREENS.SESSVIEW_OLD, SCREENS.SESSVIEW_NEW),
                           ("sessions row", SCREENS.SESSROW_OLD, SCREENS.SESSROW_NEW),
                           ("sessions recap", SCREENS.SESSVIEW_TAIL_OLD, SCREENS.SESSVIEW_TAIL_NEW),
                           ("sessions prop", SCREENS.SESSVIEW_PROP_OLD, SCREENS.SESSVIEW_PROP_NEW),
                           ("player sig", SCREENS.PLAYEREXTRA_OLD, SCREENS.PLAYEREXTRA_NEW),
                           ("player prop", SCREENS.PLAYERPROP_OLD, SCREENS.PLAYERPROP_NEW),
                           ("player extras", SCREENS.PLAYERTAIL_OLD, SCREENS.PLAYERTAIL_NEW),
                           ("spotlight calc", SCREENS.SPOT_CALC_OLD, SCREENS.SPOT_CALC_NEW),
                           ("count-up (me)", SCREENS.COUNT_ME_OLD, SCREENS.COUNT_ME_NEW),
                           ):
        assert old in s, f"{name}: anchor no longer matches"
        s = s.replace(old, new, 1)
    # The worth-watching block is replaced by span, not by anchored text: it is
    # 20 lines of JSX and an anchor on its opening lines closes the fragment
    # early, leaving the old tiles dangling after it ("Adjacent JSX elements").
    a = s.index("      {/* \u2500\u2500 WORTH WATCHING \u2500\u2500 */}")
    b = s.index("\n      </>}", a) + len("\n      </>}")
    report(f"spotlight tiles: replaced {b - a} bytes of the two-tile block")
    s = s[:a] + SCREENS.SPOT_NEW + s[b:]

    report("nav: 5 tabs (HOME / SESSIONS / RANK / ME / PLAYERS)")
    s = replace_fn(s, "MatchEditorModal", SCREENS.SCORESHEET, report, "score sheet")
    # The recap sheet gains the MY NIGHT / EVERYONE toggle the social handoff
    # asks for; EVERYONE is what Vol.8 already showed, extended.
    if "recap" not in SKIP:
        s = replace_fn(s, "RecapSheet", SCREENS.RECAP_SHEET, report, "recap sheet")
    else:
        report("recap sheet: SKIPPED (SKIP=recap)")
    return s


def apply_skin(s, report):
    css = open(SKIN).read()
    block = ("\n<style>\n/* ══ BLACKOUT SERIES · VOL.8 SKIN — appended last ══ */\n"
             + css + SCREENS.SHIMMER + SCREENS.CELEBRATE_CSS + SCREENS.POLISH_CSS + "\n</style>\n")
    i = s.rfind("</body>")
    assert i > 0, "no </body> to append the skin before"
    report(f"skin: {len(css)} bytes appended as the last style block")
    return s[:i] + block + s[i:]


def widen_font_link(s, report):
    """Blackout uses the same Archivo axes as Surge, so this should already be
    right — assert it rather than assume, because a narrow link is silent."""
    assert "wdth,wght@0,62..125,400..900;1,62..125,400..900" in s, (
        "the Archivo link has lost its width/italic axes — the display type "
        "would render ~20% narrow with no error")
    report("font: Archivo variable axes present")
    return s


def main():
    if not os.path.exists(SRC):
        sys.exit(f"missing {os.path.basename(SRC)} — build Vol.7 first")
    src = open(SRC).read()
    lines = []
    report = lambda m: (lines.append(m), print("  " + m))[0]

    print(f"Blackout Series · Vol.8   from {os.path.basename(SRC)} ({len(src)/1024:.0f}KB)")
    s = src
    s = widen_font_link(s, report)
    s = sweep(s, COLOURS, report, "colours")
    s = sweep(s, RGBS, report, "rgb triples")
    s = plain(s, MOTION, report, "motion", required=False)
    s = plain(s, ASSETS, report, "assets", required=False)
    s = plain(s, TEXT, report, "wording")
    s = plain(s, CONTRAST, report, "contrast + copy")
    s = plain(s, SEASON, report, "season shape")
    s = square_inline(s, report)
    s = add_screens(s, report)
    s = apply_skin(s, report)

    # A build id the page carries and version.txt must match: the update check
    # compares the two, and a mismatch makes every visitor reload once, forever.
    # The self-healing update check compares this constant against the served
    # version.txt. The stamp is `var V = "<hex>";` inside the inline boot script,
    # NOT a named BUILD_ID — matching the wrong shape leaves Vol.7's id in the
    # page, every version.txt then mismatches, and every visitor reloads once on
    # every single load, forever.
    bid = hashlib.sha256(s.encode()).hexdigest()[:12]
    s, n = re.subn(r'(\n\s*var V = )"[0-9a-f]{6,}";', r'\1"%s";' % bid, s, count=1)
    assert n == 1, "could not find the build stamp (var V = \"...\") to rewrite"
    with open(DST, "w") as f:
        f.write(s)
    with open(DST + ".version", "w") as f:
        f.write(bid + "\n")

    # Nothing from the previous volume may survive in the shipped bytes.
    leftovers = {t: s.count(t) for t in
                 ("SEPTEMBER SURGE", "September Surge", "#00E5FF", "#FF9E1B",
                  "surge.urbanpadel.om", "VOL.7", "0,229,255")
                 if s.count(t)}
    # Four mentions of the previous volume are deliberate and must survive: the
    # all-time volume list, the "done and dusted" line in the signup post, the
    # final-standings link, and the skin's own header comment. Anything beyond
    # that is a rename that stopped matching.
    allowed = {"September Surge": 4, "surge.urbanpadel.om": 1}
    bad = {k: v for k, v in leftovers.items() if v > allowed.get(k, 0)}

    # Any OTHER volume's host, in any casing. The named checks above only ever
    # catch the volume this build inherits from, which is how Vol.6's host rode
    # through two rebrands stamped on every shared photo: Vol.7's table swept
    # "attack" where it named it, Vol.8's sweeps "surge", and nobody was looking
    # for the one before last. This looks for the shape instead of the name, so
    # it fails on a host from any volume, including ones not yet written.
    #
    # Comments are skipped. The first run of this check failed on
    # HEAT.URBANPADEL.OM and the match turned out to be a code comment left by
    # whoever fixed this same bug one volume earlier — which is worth keeping,
    # not renaming. Only text that reaches a user counts.
    hosts = {}
    for m in re.finditer(r"\b([a-z]+)\.urbanpadel\.om\b", s, re.I):
        h = m.group(0).lower()
        if h == CFG["host"]:
            continue
        line_start = s.rfind("\n", 0, m.start()) + 1
        before = s[line_start:m.start()]
        if "//" in before or before.lstrip().startswith(("*", "#")):
            continue
        hosts[h] = hosts.get(h, 0) + 1
    stray = {h: n for h, n in hosts.items()
             if n > {CFG["previousHost"]: 1}.get(h, 0)}
    if stray:
        bad.update(stray)
    print()
    print(f"built {os.path.basename(DST)}  {len(s)/1024:.0f}KB  build {bid}")
    print(f"  pool {POOL} OMR  ·  {CFG['sessions']} nights  ·  2X from {CFG['doubleFromSession']}"
          f"  ·  season {'/'.join(str(p) for p in CFG['seasonPrizes'])}")
    if leftovers:
        print("  deliberate Vol.7 references: "
              + ", ".join(f"{k}x{v}" for k, v in leftovers.items()))
    if bad:
        sys.exit("  !! Vol.7 branding survived: "
                 + ", ".join(f"{k} x{v}" for k, v in bad.items()))
    print("\nnow deploy:  bash ops/deploy-blackout.sh")


if __name__ == "__main__":
    main()
