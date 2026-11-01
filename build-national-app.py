# -*- coding: utf-8 -*-
"""Derive the 56 National Series (Vol.9) app from the Blackout Series (Vol.8) app.

Every volume in this series inherits the previous one's markup — July Heat became
August Attack became September Surge became Blackout. Doing it as a script rather
than a hand-fork means Vol.8 fixes can be pulled forward by re-running this, and
every substitution is asserted, so a rename that stops matching fails the build
instead of shipping a half-rebranded app.

THE RE-SKIN IS PART OF THIS BUILD. It is three things, and only the first is
a find-and-replace:

  · the colour sweep (COLOURS / RGBS), by ROLE rather than by hue
  · ops/national-skin.css, appended as the last style block, which carries
    everything a sweep cannot do — the inversion to ivory heroes, the shapes,
    and the handoff's own artwork
  · MOTIFS, below: markup changes, because a stylesheet cannot put a landmark
    medallion on a session row or a "56" mark in the header. Those are the
    volume's identity, and the first pass shipped without them: a red app with
    Blackout's furniture is a recolour, not a volume.

The artwork is the handoff's own (ops/national_assets.py), never an
approximation of it — the first skin drew the khanjar tile as four CSS
gradients and the masar band as two repeating gradients, which look like the
brief from across the room and are not the brief.

What it NEVER changes: the scoring engine, the bracket seeding, the API
contract. Five volumes have now been stood up this way and the one thing that
has never been hand-written is the engine.

Season numbers come from national-season.json, which the brand art and the
signup posts also read, so none of them can advertise a figure the others
contradict.

  python3 build-national-app.py
"""
import hashlib
import json
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "ops"))
from national_assets import assets as national_assets      # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "blackout-index.html")
DST = os.path.join(HERE, "national-index.html")
CFG = json.load(open(os.path.join(HERE, "national-season.json")))

POOL = CFG["voucher"] * 2 * CFG["sessions"] + sum(CFG["seasonPrizes"])
PREV_POOL = 412          # what Vol.8 paid out, which this replaces

# ── Wording ───────────────────────────────────────────────────────────────
# Order matters: the longer, more specific strings first, or a short rule eats
# the text a long one was waiting for.
TEXT = [
    ("URBAN SOCIAL SERIES · VOL. 8", "URBAN SOCIAL SERIES · VOL. 9"),
    ("BLACKOUT SERIES", CFG["name"]),
    ("Blackout Series", CFG["nameTitle"]),
    ("BLACKOUT", CFG["shortName"]),
    ("Blackout", "National"),
    ("blackout.urbanpadel.om", CFG["host"]),
    ("VOL.8", CFG["volume"]),
    ("Vol.8", "Vol.9"),
    ("Vol. 8", "Vol. 9"),
    ("VOL. 8", "VOL. 9"),
    # Month-bound copy: it runs in meta descriptions, the signup card and the
    # generated WhatsApp posts, so leaving it would have Vol.9 telling players
    # it runs "all October".
    ("all October", "all " + CFG["month"]),
    ("ALL OCTOBER", "ALL " + CFG["monthUpper"]),
    ("October", CFG["month"]),
    ("OCTOBER", CFG["monthUpper"]),
    # Vol.8's tagline -> Vol.9's. Blackout's was a pun on its own name and
    # carrying it into a National volume would be meaningless.
    ("LIGHTS <b>OUT.</b>", "SAME COURT. <b>DIFFERENT STORY.</b>"),
    ("Lights Out.", CFG["tagline"]),
    ("Lights out.", CFG["tagline"]),
    # The hero sets the two words in different inks, so it is markup and not a
    # string — a plain "LIGHTS OUT." rule matches nothing and asserts.
    ('LIGHTS <span style={{color:"#C6FF00"}}>OUT.</span>',
     'SAME COURT <span style={{color:"#C6FF00"}}>DIFFERENT STORY.</span>'),
    # Vol.8 shipped with Vol.7 as its "previous series"; Vol.9's is Vol.8.
    ('"June Fury", "July Heat", "August Attack", "September Surge"]',
     '"June Fury", "July Heat", "August Attack", "September Surge", "Blackout Series"]'),
]

# ── Season shape. These are Vol.9's numbers and are SET here, not inherited. ──
SEASON = [
    ("const SESSIONS_TOTAL = %d;" % 9, "const SESSIONS_TOTAL = %d;" % CFG["sessions"]),
    ("const SEASON_PRIZES = [75, 50, 35];",
     "const SEASON_PRIZES = [%s];\n"
     "// The nights that count double, BY DATE. Vol.8 used a threshold —\n"
     "// DOUBLE_FROM_SESSION, every night from the Nth onward — which cannot\n"
     "// express \"the National Day night is double\" when the night after it is\n"
     "// not. The engine has always honoured a per-session doublePoints flag, so\n"
     "// a list is what the app actually reads; the threshold below is kept only\n"
     "// because the countdown copy still refers to it.\n"
     "const DOUBLE_NIGHTS = [%s];\n"
     "// The season's own schedule, so a session can be created on the right\n"
     "// night without anybody typing a date twice.\n"
     "const SEASON_NIGHTS = [%s];"
     % (", ".join(str(p) for p in CFG["seasonPrizes"]),
        ", ".join('"%s"' % d for d in CFG["doubleNights"]),
        ", ".join('"%s"' % d for d in CFG["nights"]))),
    ("const SEASON_VOUCHER = %d;" % 14, "const SEASON_VOUCHER = %d;" % CFG["voucher"]),
    ('const FINALS_DATE = "2026-10-30";', 'const FINALS_DATE = "%s";' % CFG["finalsDate"]),
]


# ── The previous volume's archive link ────────────────────────────────────
# The signup post ends with "<previous volume> final standings" and a link to
# it. Vol.8 shipped pointing at Vol.7, which was right FOR VOL.8 — and means
# Vol.9 inherits a link to a volume two back. It cannot go in TEXT above: the
# blanket rules there would rewrite the Blackout name and host straight back
# out again, so it runs as its own pass afterwards.
ARCHIVE = [
    ("September Surge final standings", "Blackout Series final standings"),
    ("surge.urbanpadel.om \u25b6", "blackout.urbanpadel.om \u25b6"),
]


# ── Assets ────────────────────────────────────────────────────────────────
# The page asks for its art by filename, and those filenames are lowercase, so
# none of the TEXT rules above touch them: the first Vol.9 build shipped with
# BLACKOUT's wordmark — VOL.8 baked into the bitmap — as the first thing a
# player sees at national.urbanpadel.om.
# THE FILENAMES A PLAYER DOWNLOADS. The share cards and the recap image are
# saved as `blackout-1.jpg` / `blackout-recap.png` — hard-coded, lowercase,
# and therefore untouched by every rename above. A Vol.9 player sharing a
# story card would have put a file named after Vol.8 into their camera roll,
# which is the same fault CLAUDE.md records of Vol.6's host riding through two
# rebrands stamped on every shared photo. The backup filename was fixed for
# Vol.8 and these were missed.
# One rule for every template-literal download name — there are four distinct
# ones (`${idx + 1}.jpg`, `${kind}.png`, `${item.key}.png`, `${it.key}.png`)
# and enumerating them is how the next volume misses the fifth.
SHARE_NAMES = [
    ("`blackout-${", "`national-${"),
    ('"blackout-recap.png"', '"national-recap.png"'),
    # A code comment that names the config file, which is a different file now.
    ("blackout-season.json", "national-season.json"),
]

# ── Two things no rename or skin rule can reach ───────────────────────────
INHERITED = [
    # The volume watermark behind the hero is the literal "08", set at 170px.
    # It is not "VOL.8", so no wording rule touches it — the first re-skin put
    # a two-foot-tall EIGHT on Vol.9's home screen.
    # It also has to change COLOUR: it is a tint of the lead, which on
    # Blackout's black card was a faint lime ghost and on an ivory hero is
    # white on cream — invisible. Ink at a few per cent is the same gesture on
    # the new ground. Matched before the sweep, so the value here is Vol.8's.
    #
    # THE INLINE COLOUR IS NOT ENOUGH, AND SETTING IT ALONE MADE THIS WORSE.
    # The skin flips everything inside an ivory hero to ink with
    # `.sg-hero * { color: var(--ink) !important }` — which beats an inline
    # style — so the 170px ghost rendered at FULL OPACITY, a two-foot near-black
    # numeral across the eyebrow and the headline. It needs a hook the skin can
    # exempt, so it gets a class; both sizes share this exact tail, so one rule
    # carries them. The alpha then lives in ops/national-skin.css beside the
    # rule that was overriding it, where the two cannot drift apart.
    ('color:"rgba(198,255,0,.06)",pointerEvents:"none"}}>08</div>',
     'color:"rgba(26,10,12,.055)",pointerEvents:"none"}} className="vol-mark"'
     ' aria-hidden="true">09</div>'),
    # A universal rule from an inherited skin layer — three :not() pseudo
    # classes, so specificity (0,3,0) — which beats any single-class selector
    # a later layer can write. It set every corner to 2px and quietly won
    # against the arch. This volume is pills everywhere, so the default it
    # imposes is simply corrected at source rather than fought. It becomes the
    # SHEET radius, not a pill, for the reason round_inline() records: a
    # universal 999px turns every tall block into an ellipse.
    ('*:not(.rounded-full):not([style*="border-radius: 50"]):not([style*="border-radius:50"]) {\n'
     '  border-radius: 2px !important;\n}',
     '*:not(.rounded-full):not([style*="border-radius: 50"]):not([style*="border-radius:50"]) {\n'
     '  border-radius: 28px !important;\n}'),
    # The roster card's photo placeholder: initials in the hairline colour on
    # the card-black slot. On Blackout that was charcoal on near-black, which
    # is a deliberate ghost. Swept by role it becomes deep red on deep red —
    # 2.32:1, and it is on 338 cards. The placeholder should be quiet, not
    # absent, so it goes to rose, which is 5.15:1 on the slot. Matched before
    # the sweep, so the value here is Vol.8's.
    ('fontSize: 26, color: "#2A2A2A" }}>', 'fontSize: 26, color: "#F2B8BC" }}>'),
    # THE "NOT SAVING" BANNER WAS WHITE ON ITS OWN BACKGROUND. Vol.8 drew it
    # as `background:"#C6FF00", color:"#fff"` — white on lime, about 1.6:1,
    # which is a Vol.8 bug we inherited rather than caused. Swept by role it
    # became white on IVORY: 1.07:1, i.e. a blank cream bar. This is the one
    # piece of UI in the app that exists to be impossible to miss — CLAUDE.md
    # records the night it cost — so it is ink on ivory, 16.6:1, which is also
    # the loudest thing that can appear on a red page.
    ('zIndex: 50, background: "#C6FF00", color: "#fff"',
     'zIndex: 50, background: "#F7F1E6", color: "#1A0A0C"'),
    # THE HEADER SUB-LINE IS SHORTENED, because the volume name above it grew.
    # "BLACKOUT" is eight characters; "56 NATIONAL SERIES" is eighteen, set
    # italic at wdth 118 — and with the sub-line at its full length the two of
    # them ran under the SYNCED button. Nothing overflowed a box, so no width
    # check saw it; they simply collided.
    # Shortening the sub-line is the right half to give up: the series name is
    # spelled out in full directly above it, and this line's job is the volume
    # number. Shrinking the type instead would mean going under the handoff's
    # 11px floor on the one line that is on every screen.
    # (matched AFTER the wording table has already moved VOL.8 to VOL.9)
    ('URBAN SOCIAL SERIES &middot; VOL.9', 'URBAN SOCIAL &middot; VOL.9'),
]

# ── The Arabic, and the face that has to be able to draw it ───────────────
AR = {k: v for k, v in CFG["arabic"].items() if k != "_note"}


def check_arabic():
    """Refuse to ship a word Noto Kufi was not subsetted for.

    ops/vendor-fonts.py cuts the Arabic face down to the characters in
    CFG["arabic"] — 120KB a weight becomes 16 — and the cost of that is a word
    added anywhere else rendering in the container's DejaVu with nothing on
    screen to say so. A silent font fallback is the exact failure the Latin
    faces were vendored to prevent; this is the Arabic half of it.
    """
    cov = os.path.join(HERE, "brand", "fonts", "kufi-coverage.txt")
    if not os.path.exists(cov):
        raise AssertionError("brand/fonts/kufi-coverage.txt is missing — "
                             "run python3 ops/vendor-fonts.py")
    have = set(open(cov, encoding="utf-8").read())
    want = {c for v in AR.values() for c in v}
    missing = sorted(want - have)
    if missing:
        raise AssertionError(
            "the vendored Noto Kufi cannot draw " + " ".join(missing)
            + " — add the word to national-season.json's `arabic` block and "
              "re-run ops/vendor-fonts.py")
    return len(have)


# ── MOTIFS ────────────────────────────────────────────────────────────────
# Markup, not style, because a stylesheet cannot put a mark in the header or a
# landmark on a session row. Each of these is a thing the handoff specifies and
# the first re-skin shipped without.
A = national_assets()

# The "56" mark, to the handoff's own recipe: white fill, a 1.2px ink stroke,
# and TWO offset shadows — ink at +1.5px and the flag's green at +3px. The
# green is the only place in the chrome it appears; everywhere else in this
# volume it means National Day and nothing else.
MARK_56 = (
    '<span aria-hidden="true" style={{fontFamily:"\'Archivo\',sans-serif",fontStyle:"italic",'
    'fontVariationSettings:"\'wdth\' 125,\'wght\' 900",fontSize:26,lineHeight:.9,'
    'color:"#FFFFFF",WebkitTextStroke:"1.2px #1A0A0C",paintOrder:"stroke fill",'
    'textShadow:"1.5px 1.5px 0 #1A0A0C, 3px 3px 0 #087A3F",flexShrink:0,'
    'letterSpacing:"-.02em",marginRight:2}}>56</span>'
)

# The landmark art, and the rule that picks one per night.
#
# THE MAPPING IS THE HANDOFF'S PLACEHOLDER AND SAYS SO. The handoff is explicit
# that the landmark-per-session assignment is the product owner's to confirm,
# and the silhouettes themselves are placeholder vector drawings to be replaced
# with commissioned artwork in the same slots. Neither of those is a reason to
# ship no motif at all, which is what the first re-skin did — a volume whose
# whole identity is Omani landmarks, with none on screen. It cycles the four in
# order, deterministically, so the same night always wears the same landmark
# and swapping the mapping later is a line in national-season.json.
#
# Rule from the handoff, carried here so it cannot be lost: NO MOSQUES.
LANDMARK_JS = (
    "const LANDMARK_ART = {\n"
    + "".join(f'  {l["asset"]!r}: {A["mon-" + l["asset"].split("-")[1] + "@white"]!r},\n'
             for l in CFG["landmarks"])
    + "};\n"
    + "const LANDMARKS = " + json.dumps(CFG["landmarks"], ensure_ascii=False) + ";\n"
    + "// Deterministic, and NOT random: a night that changed its landmark on\n"
      "// every render would be noise rather than a label.\n"
      "function landmarkFor(i) { return LANDMARKS[((i % LANDMARKS.length) "
      "+ LANDMARKS.length) % LANDMARKS.length]; }\n"
    # WHICH NIGHT IS NEXT, by the same index the rows use — so the hero and
    # the row for that night always wear the same landmark. The first night
    # not yet completed; before any exist, night one.
    + "function nextNightIndex(st) {\n"
      "  const ss = (st && st.sessions) || [];\n"
      "  const i = ss.findIndex(s => !s.completed);\n"
      "  return i < 0 ? Math.max(0, ss.length - 1) : i;\n"
      "}\n"
)

MOTIFS = [
    # 0 · The landmark table and its lookup, in front of the first screen that
    #     uses it.
    ("function SessionsView({", LANDMARK_JS + "\nfunction SessionsView({"),
    # 1 · THE HEADER CARRIES THE VOLUME'S OWN MARK. It used to carry a 30px
    #     sunrise drawn out of four absolutely-positioned spans — a stand-in
    #     invented here, while the handoff specifies a "56" lockup and the
    #     repo ships the art to build it.
    ('<span style={{width:30,height:30,flexShrink:0,position:"relative",background:"#C6FF00"}}>',
     '<span style={{display:"none"}}>'),
    # 2 · ...and the Arabic line the handoff sets under every title. It
    #     replaces "URBAN SOCIAL", which was a shortening forced on us by the
    #     header running out of bar — the Arabic is shorter AND is the thing
    #     the brand actually asks for.
    ('URBAN SOCIAL &middot; VOL.9</div>',
     '<span style={{fontFamily:"\'Noto Kufi Arabic\',sans-serif",fontWeight:700}}>'
     + AR["series"] + '</span> &middot; VOL.9</div>'),
    # 3 · The mark itself, in the slot the sunrise vacated.
    ('<div style={{minWidth:0}}>\n              <div style={{fontStyle:"italic"',
     MARK_56 + '\n            <div style={{minWidth:0}}>\n'
     '              <div style={{fontStyle:"italic"'),
    # 4 · NOTO KUFI HAS TO BE ASKED FOR. The page's font link carries Archivo
    #     and JetBrains Mono; an Arabic string set in a stack that names a face
    #     nobody fetched is drawn in whatever the device has, which in this
    #     container is DejaVu — a text face, not a display one. Subsetted to
    #     the words in national-season.json, so this costs about 16KB.
    ("&family=JetBrains+Mono:wght@400;500;700&display=swap\" rel=\"stylesheet\"",
     "&family=JetBrains+Mono:wght@400;500;700"
     "&family=Noto+Kufi+Arabic:wght@500;700&display=swap\" rel=\"stylesheet\""),
    # 5 · THE SESSION ROW GETS ITS LANDMARK MEDALLION. The handoff draws each
    #     night as a circle carrying an Omani landmark, with the eyebrow
    #     reading "DATE · LANDMARK" — it is how a night is told apart at a
    #     glance, and it is most of what makes the screen Omani rather than
    #     merely red. The slot it replaces was a bordered square holding the
    #     session number, which the row's own title already carries.
    ('''<div style={{flex:"0 0 auto",width:48,height:48,display:"grid",placeItems:"center",
                 background:liveNow ? "rgba(198,255,0,.12)" : "rgba(255,255,255,.03)",
                 border:`1px solid ${liveNow ? "rgba(198,255,0,.5)" : "rgba(110,110,110,.3)"}`,
                 fontFamily:"'Archivo',sans-serif",fontStyle:"italic",fontVariationSettings:"'wdth' 125,'wght' 900",
                 fontSize:24,color:liveNow ? "#C6FF00" : "#CFCFCF"}}>{num}</div>''',
     '''<div className="na-medallion" data-live={liveNow ? "1" : "0"}
                 title={landmarkFor(idx).nameEn}
                 style={{flex:"0 0 auto",width:48,height:48,
                 backgroundImage:`url("${LANDMARK_ART[landmarkFor(idx).asset]}")`}} />'''),
    # 6a · THE HOME HERO CARRIES THE NEXT NIGHT'S MEDALLION. The handoff's
    #      hero is a landmark disc above the copy; ours had the volume ghost
    #      and nothing else, so the first screen a player opens showed none of
    #      the identity the rest of the app now wears. It names the landmark
    #      underneath, for the same reason the rows do: a disc nobody can name
    #      is decoration.
    ('''<div style={{position:"relative",fontFamily:"'Archivo',sans-serif",fontWeight:800,fontSize:9,
             letterSpacing:".34em",color:"#C6FF00"}}>''',
     '''<div className="na-hero-mark" style={{position:"relative"}}>
          <div className="na-medallion na-medallion-lg"
               title={landmarkFor(nextNightIndex(state)).nameEn}
               style={{backgroundImage:`url("${LANDMARK_ART[landmarkFor(nextNightIndex(state)).asset]}")`}} />
          <div className="na-hero-landmark">
            {landmarkFor(nextNightIndex(state)).nameEn.toUpperCase()}
            <span style={{fontFamily:"'Noto Kufi Arabic',sans-serif",fontWeight:700,marginInlineStart:8}}>
              {landmarkFor(nextNightIndex(state)).nameAr}</span>
          </div>
        </div>
        <div style={{position:"relative",fontFamily:"'Archivo',sans-serif",fontWeight:800,fontSize:9,
             letterSpacing:".34em",color:"#C6FF00"}}>'''),
    # 6b · ...and the eyebrow says which landmark it is, so the circle is a
    #     label and not decoration.
    ('''{ weekday:"short", day:"numeric", month:"short" }).toUpperCase() : "NO DATE"}</div>''',
     '''{ weekday:"short", day:"numeric", month:"short" }).toUpperCase() : "NO DATE"}'''
     ''' &middot; {landmarkFor(idx).nameEn.toUpperCase()}</div>'''),
]

SHEET = str(int(float(CFG["shape"]["sheet"].rstrip("px"))))

ASSETS = [
    ("assets/blackout-lockup.webp", "assets/national-lockup.webp"),
    ("assets/blackout-lockup.png", "assets/national-lockup.png"),
    ("assets/blackout-og.png", "assets/national-og.png"),
]


# ── Palette: Blackout (lime lead, magenta accent, true black)
#            -> 56 National Series (ivory on flag red, ink for fills)
#
# THIS IS NOT A COLOUR SWAP, IT IS A ROLE SWAP, and the two systems are built
# the opposite way round: Blackout is a dark page with one bright accent;
# National is a RED page with ivory surfaces and dark ink. So each Blackout
# token is mapped by the JOB IT DOES, not by hue.
#
#   lime     the lead — live, wins, primary fills, every number that matters.
#            On red the bright thing is IVORY, and a lime fill carrying black
#            text becomes an ivory fill carrying red text, which is exactly
#            the handoff's SHARE button and its hero cards.
#   magenta  the rare one — double points, "you", urgency. It becomes ROSE,
#            which is the handoff's own label colour on red. The obvious pick
#            was flag red, and it was measured at 1.60:1 against the deep red
#            the cards sit on — invisible. The handoff only ever uses flag red
#            as a FILL carrying white text, never as type on red, and the
#            audit is why that is. Inside an ivory hero the skin turns it back
#            into flag red, where it reads at 4.8:1.
#            It does NOT become the flag green, which the handoff reserves for
#            National Day and nothing else — spend it on ordinary urgency and
#            the 18th stops meaning anything.
#   blacks   the page and its cards become the red base and the deep red the
#            handoff uses for rows and bands.
#   greys    text on black becomes text on red: white for primary, rose for
#            labels, and the handoff's inactive tone for what is switched off.
#
# Two passes through sentinels, so no rule can eat another's output.
COLOURS = [
    # was         sentinel    becomes      what it is
    ("#C6FF00", "@@P@@",   "#F7F1E6"),   # lead: Lime -> Ivory
    ("#FF2E88", "@@S@@",   "#F2B8BC"),   # accent: Magenta -> Rose
    ("#C4215F", "@@S2@@",  "#9E1520"),   # deep variant of the accent
    ("#FF8FBE", "@@S3@@",  "#F2B8BC"),   # soft variant -> Rose
    ("#0A0A0A", "@@BG@@",  "#9E1520"),   # card black -> deep red (rows, bands)
    ("#050505", "@@BG2@@", "#B8141F"),   # app background -> the red base
    ("#F2F2F2", "@@FG@@",  "#FFFFFF"),   # primary text, now on red
    # SECONDARY TEXT GOES LIGHT, NOT ROSE. Measured on the red ground: rose
    # #F2B8BC is 3.64:1 and the inactive tone #CBBDB6 is 4.4:1, both under AA
    # for body copy — and this is where the app's secondary copy lives, which
    # on Blackout's black was 5-7:1. The handoff's own answer is that there is
    # no dark-on-red pair, so type on the base is light; these are the two
    # light tiers that clear it, the second measured at 4.72:1.
    ("#9A9A9A", "@@MU@@",  "#F2D0D3"),   # muted -> light rose, 4.72:1
    ("#CFCFCF", "@@MU2@@", "#F7F1E6"),   # ink-2 -> Ivory, 5.83:1
    ("#6E6E6E", "@@MU3@@", "#F2D0D3"),   # muted-2 -> light rose
    ("#2A2A2A", "@@HL@@",  "#9E1520"),   # hairline -> deep red
    # THREE-DIGIT HEX. The sweep matches six-digit literals, so `#111` went
    # through untouched — and it is the background of the roster card's photo
    # slot, 338 near-black tiles on a red page. `#fff` is already white and is
    # listed so the count says it was looked at rather than missed.
    ('"#111"', "@@SH1@@", '"#9E1520"'),
    ('"#fff"', "@@SH2@@", '"#FFFFFF"'),
    # THE SURGE-ERA STEEL GREYS. Two inherited skin layers set the
    # .text-stone-* utilities to a family of blue-greys that no Blackout rule
    # mentions — so nothing in the first sweep touched them, and "No sessions
    # yet" and "Ranking locked" rendered in #C3CAD6 at 3.94:1, a cold grey on
    # a warm red. They are the same two tiers as above.
    ("#C3CAD6", "@@G1@@",  "#F7F1E6"),
    ("#D5DAE3", "@@G2@@",  "#F7F1E6"),
    ("#A8B0BE", "@@G3@@",  "#F2D0D3"),
    ("#78818F", "@@G4@@",  "#F2D0D3"),
    ("#6B7484", "@@G5@@",  "#F2D0D3"),
]

# The same tokens written as rgb() components, for the tints built from them.
# Missing one of these leaves a Blackout glow around a National element — the
# exact failure the landing page's --live rollover produces.
RGBS = [
    ("198,255,0",   "@@RP@@",  "247,241,230"),
    ("255,46,136",  "@@RS@@",  "242,184,188"),
    ("5,5,5",       "@@RB@@",  "184,20,31"),
    ("242,242,242", "@@RF@@",  "255,255,255"),
    ("110,110,110", "@@RM@@",  "242,208,211"),
    # THE SURFACE TINTS. Blackout's cards are near-black rgba() built from
    # these three, and no hex rule touches them — so the first re-skin put
    # near-black cards on a red page and the contrast audit found ivory type
    # sitting on them at 3.6:1. They are the deep red the handoff uses for
    # rows and bands.
    ("14,14,14",    "@@RC1@@", "158,21,32"),
    ("20,20,20",    "@@RC2@@", "158,21,32"),
    ("10,10,10",    "@@RC3@@", "158,21,32"),
]


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
    report(f"{label}: {len(table) - len(missing)}/{len(table)} matched"
           + (f"; not present: {', '.join(missing)}" if missing else ""))
    return s


def round_inline(s, report):
    """NO SQUARE BLOCKS — the handoff's first shape rule.

    Blackout was radius 0 everywhere, which is the single reason a component
    carried over unchanged still reads as Vol.8 no matter what colour it is
    wearing. Every inline radius is re-pointed; deliberate circles are left.

    THE DEFAULT IS THE SHEET, NOT THE PILL. The first version made every
    inline radius 999px, on the grounds that the handoff's shape list leads
    with the pill. It does — for CHIPS. 999px on a 120px-tall block is not a
    pill, it is an ellipse: the countdown cells came out as four ovals, the
    section cards as lozenges, and the home screen read as a bubble bath
    rather than as the handoff's arches-and-sheets. A pill only looks like a
    pill when the box is much wider than it is tall, and nothing at build time
    knows how tall a box will be. So the sweep sets the sheet radius, which is
    right at any height, and the skin pills the things that ARE short by
    definition — buttons, inputs, the tab bar and the chips.
    """
    n = [0, 0]

    def rep(m):
        if m.group(0).endswith('"50%"') or m.group(0).endswith("50%"):
            n[1] += 1
            return m.group(0)
        n[0] += 1
        return "borderRadius: " + SHEET

    s = re.sub(r'borderRadius:\s*(?:"[^"]*"|\d+|[A-Za-z_$][\w$]*)', rep, s)
    report(f"shape: {n[0]} inline radii set to the {SHEET}px sheet, "
           f"{n[1]} circles kept")
    assert n[0] > 0, "no inline radii found — has the app's style shape changed?"
    return s


def apply_skin(s, report):
    skin = open(os.path.join(HERE, "ops", "national-skin.css")).read()
    # THE SKIN NAMES THE HANDOFF'S ARTWORK, IT DOES NOT DRAW IT. `@@A:name@@`
    # becomes a data: URL from ops/national_assets.py. Doing it here rather
    # than committing a stylesheet full of base64 keeps the skin readable and
    # means re-exported artwork is picked up by a rebuild rather than by a
    # hand-edit — the first version drew the tile and the band as CSS
    # gradients, which is an approximation of a brief that shipped its own art.
    art = national_assets()
    used = set()

    def put(m):
        k = m.group(1)
        if k not in art:
            raise AssertionError(f"the skin asks for asset {k!r}, which "
                                 f"ops/national_assets.py does not have")
        used.add(k)
        return art[k]

    skin, n = re.subn(r"@@A:([a-z0-9@-]+)@@", put, skin)
    assert n, "the skin references no artwork — the handoff's motifs are missing"
    report(f"artwork: {len(used)} asset(s) inlined, {n} reference(s), "
           f"{sum(len(art[k]) for k in used) // 1024}KB")
    i = s.rfind("</body>")
    assert i > 0, "no </body> to append the skin before"
    # THE BLOCK IS NAMED, and that is not decoration. Two inherited skin layers
    # (the August Attack and September Surge ones) carry their own banner
    # comments, and the wording sweep rewrites the volume name inside them — so
    # the shipped page holds THREE style blocks whose first line reads
    # "56 NATIONAL SERIES · VOL.9 SKIN", and only the last is this one. A
    # harness looking for that banner finds the wrong block: SABOTAGE=noskin
    # deleted an August-era layer, every check stayed green, and a sabotage
    # that silently does nothing is worse than no sabotage at all.
    s = (s[:i] + '<style id="vol9-skin">\n' + skin + "\n</style>\n" + s[i:])
    report(f"skin: {len(skin)} bytes appended as the last style block"
           ' (id="vol9-skin")')
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


def double_by_date(s, report):
    """Default the 2X toggle from the date, instead of from nothing.

    The toggle was `useState(false)` and the organiser had to remember to flip
    it. That is a flag somebody forgets, and the night it gets forgotten on is
    the one everybody was told would be worth double — National Day. The season
    file already knows which dates they are, so the toggle starts where the
    schedule says it should and the organiser can still override it.

    It changes a DEFAULT and nothing else: the stored session still carries its
    own doublePoints, and the engine still reads only that.
    """
    old = "  const [doublePoints, setDoublePoints] = useState(false);"
    assert old in s, "CreateSessionModal's doublePoints state no longer matches"
    new = ("  // Defaults from the schedule — see DOUBLE_NIGHTS. Overridable.\n"
           "  const [doublePoints, setDoublePoints] = useState(\n"
           "    () => DOUBLE_NIGHTS.includes(date));\n"
           "  // ...and follows the date if the organiser changes it, unless they\n"
           "  // have already touched the toggle themselves.\n"
           "  const touchedDouble = React.useRef(false);\n"
           "  React.useEffect(() => {\n"
           "    if (!touchedDouble.current) setDoublePoints(DOUBLE_NIGHTS.includes(date));\n"
           "  }, [date]);")
    s = s.replace(old, new)
    # The toggle must mark itself as touched, or the effect above would undo
    # the organiser's own choice the next time the date field is edited.
    tog = "<button onClick={() => setDoublePoints(v => !v)}"
    assert tog in s, "the 2X toggle no longer matches"
    s = s.replace(tog, "<button onClick={() => { touchedDouble.current = true; "
                       "setDoublePoints(v => !v); }}", 1)
    report("2X toggle: defaults from the night's date, organiser can override")
    return s


def main():
    if not os.path.exists(SRC):
        sys.exit(f"missing {os.path.basename(SRC)} — build Vol.8 first")
    src = open(SRC).read()
    lines = []
    report = lambda m: (lines.append(m), print("  " + m))[0]

    print(f"{CFG['nameTitle']} · {CFG['volume']}   from "
          f"{os.path.basename(SRC)} ({len(src)/1024:.0f}KB)")
    s = src
    s = plain(s, TEXT, report, "wording")
    s = plain(s, INHERITED, report, "inherited quirks")
    s = plain(s, ASSETS, report, "assets")
    s = plain(s, SHARE_NAMES, report, "downloaded filenames")
    s = plain(s, ARCHIVE, report, "previous volume's archive link")
    s = plain(s, SEASON, report, "season shape")
    report(f"arabic: {check_arabic()} characters vendored in Noto Kufi")
    # BEFORE the colour sweep, like every other markup rule here: the motifs
    # carry Vol.8 literals in the text they match.
    s = plain(s, MOTIFS, report, "motifs")
    s = double_by_date(s, report)
    s = sweep(s, COLOURS, report, "colours")
    s = sweep(s, RGBS, report, "rgb triples")
    s = round_inline(s, report)
    s = apply_skin(s, report)

    # A build id the page carries and version.txt must match: the self-healing
    # update check compares the two, and a mismatch makes every visitor reload
    # once, forever. The stamp is `var V = "<hex>";` in the inline boot script,
    # NOT a named BUILD_ID.
    bid = hashlib.sha256(s.encode()).hexdigest()[:12]
    s, n = re.subn(r'(\n\s*var V = )"[0-9a-f]{6,}";', r'\1"%s";' % bid, s, count=1)
    assert n == 1, 'could not find the build stamp (var V = "...") to rewrite'

    with open(DST, "w") as f:
        f.write(s)
    with open(DST + ".version", "w") as f:
        f.write(bid + "\n")

    # NOTHING FROM THE PREVIOUS VOLUME MAY SURVIVE IN THE SHIPPED BYTES, except
    # the handful of mentions that are deliberately about Vol.8.
    leftovers = {t: s.count(t) for t in
                 ("BLACKOUT SERIES", "Blackout Series", "BLACKOUT",
                  "blackout.urbanpadel.om", "VOL.8", "Vol.8", "blackout-",
                  "#C6FF00", "#FF2E88", "198,255,0")
                 if s.count(t)}
    # The all-time volume list names every previous volume by design, and the
    # final-standings link points at Vol.8's archive. Anything beyond that is a
    # rename that stopped matching.
    # Deliberate: the all-time volume list names every previous volume, the
    # signup post links Vol.8's final standings, and DOUBLE_NIGHTS carries a
    # comment explaining what Vol.8 did differently.
    allowed = {"Blackout Series": 5, "blackout.urbanpadel.om": 1, "Vol.8": 1}
    bad = {k: v for k, v in leftovers.items() if v > allowed.get(k, 0)}

    # ANY OTHER VOLUME'S HOST, in any casing. The named checks above only ever
    # catch the volume this build inherits from, which is how Vol.6's host rode
    # through two rebrands stamped on every shared photo.
    hosts = {h: s.count(h) for h in
             ("surge.urbanpadel.om", "attack.urbanpadel.om", "july.urbanpadel.om",
              "june.urbanpadel.om")
             if s.count(h)}
    if hosts:
        bad.update(hosts)

    if bad:
        raise SystemExit("previous-volume strings survived the build: "
                         + ", ".join(f"{k} x{v}" for k, v in bad.items()))
    if leftovers:
        report("deliberate Vol.8 references: "
               + ", ".join(f"{k}x{v}" for k, v in leftovers.items()))

    # The pool is derived, never typed. If it has not moved from Vol.8's, say
    # so rather than leaving somebody to wonder whether the file was read.
    assert str(PREV_POOL) not in s or POOL == PREV_POOL, \
        "Vol.8's pool figure survived into a volume with a different one"

    print(f"\nbuilt {os.path.basename(DST)}  {len(s)/1024:.0f}KB  build {bid}")
    print(f"  pool {POOL} OMR  ·  {CFG['sessions']} nights  ·  "
          f"season {'/'.join(str(p) for p in CFG['seasonPrizes'])}  ·  "
          f"{len(CFG['doubleNights'])} double nights")
    print(f"  {CFG['schedule']}  ·  {CFG['nights'][0]} to {CFG['nights'][-1]}")
    print(f"\nnow deploy:  bash ops/deploy-national.sh")


if __name__ == "__main__":
    main()
