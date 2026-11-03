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

# THE TAGLINE IS TWO BEATS, and the hero needs them separately because it sets
# the second half in the accent ink. Split here, with the shape asserted, so a
# one-sentence line fails the build rather than rendering as a headline with an
# empty second colour.
TAG = CFG["tagline"].strip()
_parts = [x.strip() for x in re.findall(r"[^.!?]+[.!?]", TAG)]
assert len(_parts) == 2, (
    f"tagline must be two sentences for the hero's two inks, got {len(_parts)}: {TAG!r}")
TAG_A, TAG_B = _parts
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
    #
    # ALL FOUR FORMS ARE DERIVED FROM THE ONE JSON KEY. Two of them used to be
    # typed out here, so `tagline` in national-season.json was right on the
    # surfaces that read the file and silently stale on the two the app
    # actually shows biggest — the hero headline and the WhatsApp sign-off.
    # Changing the line is one edit again.
    ("LIGHTS <b>OUT.</b>", f"{TAG_A.upper()} <b>{TAG_B.upper()}</b>"),
    ("Lights Out.", TAG),
    ("Lights out.", TAG),
    # The hero sets the two halves in different inks, so it is markup and not a
    # string — a plain "LIGHTS OUT." rule matches nothing and asserts.
    ('LIGHTS <span style={{color:"#C6FF00"}}>OUT.</span>',
     f'{TAG_A.upper()} <span style={{{{color:"#C6FF00"}}}}>{TAG_B.upper()}</span>'),
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
    # EVERY Arabic string in the config, not just the `arabic` block — the
    # landmark names and the National Day label are set in Kufi too, on the
    # app's hero and on the posts, and the first version of this guard did not
    # look at them. It walks the config rather than listing keys, because
    # listing them is how the next one gets missed.
    def walk(node):
        if isinstance(node, str):
            if re.search(r"[\u0600-\u06FF]", node):
                yield node
        elif isinstance(node, dict):
            for k, v in node.items():
                if k != "_note":
                    yield from walk(v)
        elif isinstance(node, list):
            for v in node:
                yield from walk(v)

    want = {c for t in walk(CFG) for c in t}
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
# ...ON THE FLAG. The mark used to sit on the bare red header, which meant the
# only National colour in the chrome was the one the whole page is already
# made of. It now stands on a plaque carrying the flag's three bands — white,
# red, green, with the red hoist bar down the left — so the white and the
# green are present on every screen without being spent as accents anywhere
# else. The green offset shadow comes OFF: against a green band it read as a
# printing error rather than as depth.
MARK_56 = (
    '<span className="na-flag" aria-hidden="true">'
    '<span style={{fontFamily:"\'Archivo\',sans-serif",fontStyle:"italic",'
    'fontVariationSettings:"\'wdth\' 125,\'wght\' 900",fontSize:26,lineHeight:.9,'
    'color:"#FFFFFF",WebkitTextStroke:"1.2px #1A0A0C",paintOrder:"stroke fill",'
    'textShadow:"1.5px 1.5px 0 #1A0A0C",'
    'letterSpacing:"-.02em"}}>56</span></span>'
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
def _long_date(d):
    from datetime import date as _d
    y, m, dd = (int(x) for x in d.split("-"))
    t = _d(y, m, dd)
    return t.strftime("%a %-d %b")


def _short_date(d):
    return _long_date(d)


def _double_label():
    """'Session 6' / 'Sessions 8 & 9' / 'Sessions 6, 8 & 9' — from the dates."""
    nums = [CFG["nights"].index(d) + 1 for d in CFG["doubleNights"]
            if d in CFG["nights"]]
    assert len(nums) == len(CFG["doubleNights"]), (
        "a doubleNights date is not in nights: "
        f"{set(CFG['doubleNights']) - set(CFG['nights'])}")
    word = "Session" if len(nums) == 1 else "Sessions"
    if len(nums) == 1:
        body = str(nums[0])
    else:
        body = ", ".join(str(n) for n in nums[:-1]) + f" & {nums[-1]}"
    return f"{word} {body}"


# THE MASAR TRIM FOR THE SHARE CARDS, as one top-level helper rather than a
# closure inside one painter.
#
# It began as a `const luBand` inside luPaint, and the anchor that appended the
# foot call matched TWICE — so gcPaint got `luBand(...)` too, with luBand not
# in its scope: a ReferenceError that would have thrown on every bracket and
# champions card the moment somebody shared one. ops/check-lineup.mjs drives
# luPaint and never saw it. One helper, declared where all three painters can
# reach it, is the shape that cannot go wrong that way.
#
# AND IT IS INSET AND PILLED, not a full-bleed stripe. The handoff's band is
# "24px tall, 14px side inset, pill radius" — a trim on the edge of the page.
# At 1080 wide a story is seen at about 430, so 56px and a 36px inset are that
# same trim at this scale. Run full-bleed to the bitmap edge it stopped being a
# trim and became a bar, which is the mistake already recorded for the page
# band, and it crowded the night label at the foot.
# The year comes off the schedule, not off the clock: a card built in
# December must still say the season it is about.
_season_year = CFG["nights"][0][:4]

BAND_JS = f"""const LU_BAND = {A['masar']!r};
let LU_BAND_IMG = null;
// LOADED EAGERLY, not on the way through one painter. The slot used to be
// filled only by drawLineup/drawLineupAt, and drawCutCardAt does not load the
// band at all — so a NO-BACKGROUND card drawn before any photo card came out
// with no masar trim on it, silently, depending only on which card somebody
// opened first. Caught by rendering the cut-out card for the first time.
luImg(LU_BAND).then(b => {{ LU_BAND_IMG = LU_BAND_IMG || b; }});
// The khanjar tile, for the card ground and the arch's interior. Same art
// the page is laid on, so a card and the app cannot drift apart.
const LU_TILE = {A['khanjar']!r};
let LU_TILE_IMG = null;
luImg(LU_TILE).then(b => {{ LU_TILE_IMG = LU_TILE_IMG || b; }});
// Read from the season file, never typed on a card.
const SERIES_NAME = {CFG['name']!r};
const SERIES_NAME_AR = {CFG['nameAr']!r};
const VOLUME_LABEL = {CFG['volume']!r};
const SEASON_MONTH_SHORT = {CFG['monthUpper'][:3]!r};
const SEASON_YEAR = {_season_year!r};

function luWeave(g, y) {{
  const b = LU_BAND_IMG;
  if (!b) return;
  const h = 56, pad = 36, x0 = pad, bw = LU_W - pad * 2;
  // The width always keeps the art's own 100:56 ratio: a woven band stretched
  // off its aspect is the one place a pattern looks obviously wrong.
  const w = Math.round(h * b.width / b.height);
  g.save();
  g.beginPath();
  if (g.roundRect) g.roundRect(x0, y, bw, h, h / 2); else g.rect(x0, y, bw, h);
  g.clip();
  g.fillStyle = "#9E1520"; g.fillRect(x0, y, bw, h);
  for (let x = x0; x < x0 + bw; x += w) g.drawImage(b, x, y, w, h);
  g.restore();
}}
// Head and foot. The side inset is 36 and the edge offset 18, which is the
// handoff's own 14-against-7 at this scale — the band is a trim ON the edge,
// so it sits nearer to it than to the sides. Inset 36 all round instead, the
// foot band needed the footer moved 54px up and that clipped the top of the
// club mark behind the lower name plate.
const luTrim = (g) => {{ luWeave(g, 18); luWeave(g, LU_H - 74); }};
"""

# VOL.9'S OWN CARD PAINTER. It is a module rather than another pile of
# MOTIFS anchors because this is a new COMPOSITION, not a recolour of
# Vol.8's — and patching a layout one anchor at a time is exactly how the
# cards ended up as a black-card design wearing red.
import national_cards  # noqa: E402
CARDS_JS = national_cards.painter(CFG['palette'])

# ...and the OTHER three cards. national_cards.py gave the line-up cards this
# volume's design and left the draw, the tables and the bracket wearing Vol.8's
# — swept red, violet corner wash and all, with square tiles, square rows, a
# centred mark and none of the motifs. The canvas is invisible to every DOM
# harness here, so nothing complained and nothing would have.
import national_group_cards  # noqa: E402
GROUP_CARDS_JS = national_group_cards.painter(CFG['palette'])

DATE_JS = (
    "// The schedule's own words for the double nights, so the WhatsApp copy\n"
    "// and the admin hint cannot drift from DOUBLE_NIGHTS.\n"
    + f"const NATIONAL_DAY_LABEL = {_long_date(CFG['nationalDay'])!r};\n"
    + f"const NATIONAL_DAY_LABEL_SHORT = {_short_date(CFG['nationalDay'])!r};\n"
)

LANDMARK_JS = (
    "const LANDMARK_ART = {\n"
    # THE ASSET NAME IS THE KEY. It used to be reconstructed from the second
    # word of the name — fine while every asset was `mon-<word>`, and a
    # KeyError the moment one was `mon-sail-ph`. Nothing is gained by
    # rebuilding a string that is already in hand.
    + "".join(f'  {l["asset"]!r}: {A[l["asset"] + "@white"]!r},\n'
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

# ── THE WHATSAPP ANNOUNCEMENT, GENERATED ─────────────────────────────────
# What the organiser copies out of the SESSIONS screen and pastes into the
# group. It was inherited as a literal and it was WRONG IN VOL.8 ALREADY:
# "8 sessions total · Sessions 7 & 8 pay DOUBLE POINTS" against a nine-night
# season that doubled from the 8th. Swept into Vol.9 it also still read
# "September Surge is done and dusted" — the archive rule rewrote the
# standings LINK and left the sentence above it naming the volume before last.
#
# So it is derived, like every other figure in this repo. The session count,
# the double nights, the previous volume, the pool, the entry and the tagline
# all come from national-season.json, which means a post cannot advertise a
# shape the app contradicts.
ANNOUNCE = f"""🔥🔥🔥 *IT'S BACK* 🔥🔥🔥

*{CFG['name']} · Urban Social Series Vol. 9*
_{TAG}_ ⚡

{CFG['previousVolume']} is done and dusted — new season, new partners, new rivalries 🏆

━━━━━━━━━━━━━━━━━━━━
📅 *{CFG['schedule'].upper().replace(', ', ' · ')} · ALL {CFG['monthUpper']}*
📍 Urban Playground, Oman
💸 {CFG['entry']} OMR per player
━━━━━━━━━━━━━━━━━━━━

🗓️ {CFG['sessions']} sessions total · {_double_label()} pay *DOUBLE POINTS* 🔥
🇴🇲 *Session {CFG['nights'].index(CFG['nationalDay']) + 1}* is the *{CFG['nationalDayLabel']}*
💰 *{POOL} OMR prize pool* up for grabs

━━━━━━━━━━━━━━━━━━━━
Series points reset to *zero* — your *all-time* total carries over 👑

🏆 *{CFG['previousVolume']} final standings:*
{CFG['previousHost']} ▶ Leaderboard

📊 *{CFG['nameTitle']} live tracker:*
https://{CFG['host']}
━━━━━━━━━━━━━━━━━━━━

Drop your name + partner below to lock your spot 👇

⚠️ *16 teams max · first come, first served*
💥 *{TAG}* 👑"""


MOTIFS = [
    # -1a · THE "HOW IT WORKS" SHEET CARRIED VOL.8'S DOUBLE NIGHTS. The
    #        FORMAT button on the SESSIONS screen writes a WhatsApp explainer,
    #        and its 2X line was the literal "Sessions 7 & 8" — wrong for
    #        Vol.9, where the schedule says 6, 8 and 9, and which no reader
    #        could tell apart from the generated figures around it.
    ("⚡ *Sessions 7 & 8 pay DOUBLE points* — the table can still flip on the "
     "last night, so it's never too late to join.",
     f"⚡ *{_double_label()} pay DOUBLE points* — including the "
     f"{CFG['nationalDayLabel'].lower()} on "
     + "${NATIONAL_DAY_LABEL}" + ". The table can still flip on the last "
     "night, so it's never too late to join."),
    # -1b · ...and the admin hint beside the 2X toggle still described Vol.8's
    #        rule ("from Session 8 — the last two nights"), which is not how
    #        this volume works at all: the nights are a LIST, and the toggle
    #        now defaults from the date.
    ("`On by default from Session ${DOUBLE_FROM_SESSION} — the last two nights. "
     "Turn off to override.`",
     "`On by default — " + "${NATIONAL_DAY_LABEL_SHORT}" + " and the last two "
     "nights are double. Turn off to override.`"),
    # 0 · The landmark table and its lookup, in front of the first screen that
    #     uses it.
    ("function SessionsView({",
     BAND_JS + DATE_JS + LANDMARK_JS + CARDS_JS + GROUP_CARDS_JS
     + "\nfunction SessionsView({"),
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
    # 2b · THE HAIRLINE DIVIDER GOES, now that the flag plaque stands where it
    #      did. It was 1px plus two gaps — about 21px, almost exactly what the
    #      plaque costs — and its job was to separate the club's mark from the
    #      volume's. A plaque with its own ink ring does that better than a
    #      rule does, and keeping both left the volume name 14px short of its
    #      own line and firing the ellipsis.
    ('<span style={{width:1,height:28,background:"rgba(255,255,255,.14)",flexShrink:0}} />',
     ''),
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
    # 5b · THE COUNTDOWN GOES IVORY. The home screen was red on red on red —
    #      an ivory hero at the top and then four hundred pixels of deep-red
    #      cards, which reads as one colour however many surfaces are in it.
    #      The countdown is the natural second panel: it is a self-contained
    #      block, it is the thing people actually look at between nights, and
    #      an ivory plate halfway down gives the page a rhythm instead of a
    #      wash. `.na-ivory` carries the ink flip, the same way `.sg-hero`
    #      does. Matched before the sweep, so the values here are Vol.8's.
    ('<div style={{ border: "1px solid rgba(255,46,136,.4)", background: "rgba(20,20,20,.96)",\n'
     '                  padding: 16, marginTop: 20 }}>',
     '<div className="na-ivory" style={{ padding: 18, marginTop: 20 }}>'),
    # 5c · THE NATIONAL DAY PILL, which the handoff puts on the Sessions
    #      screen and which the home screen had nothing of. It is the single
    #      largest piece of green in the design and the one night of the nine
    #      that is actually an occasion, so it belongs where everybody lands.
    #      Green is spent HERE and nowhere else, which is the handoff's rule
    #      and the reason it still means something.
    ("      {/* ── NEXT UP ── */}",
     '''      <div className="na-natday">
        <div style={{flex:"1 1 auto",minWidth:0}}>
          <div className="na-natday-when">{NATIONAL_DAY_LABEL.toUpperCase()} &middot; '''
     + CFG["schedule"].split(",")[-1].strip().upper() + '''</div>
          <div className="na-natday-title">''' + CFG["nationalDayLabel"] + '''</div>
          <div className="na-natday-ar">''' + CFG["nationalDayLabelAr"] + '''</div>
        </div>
        <div className="na-natday-2x">2X</div>
      </div>

      {/* ── NEXT UP ── */}'''),
    # 5d · THE SHARE CARDS GET THE MOTIFS TOO. They are drawn on a CANVAS,
    #      so the skin cannot reach them and ops/check-national-skin.mjs
    #      cannot even see them — every assertion there reads the DOM, and a
    #      canvas is one opaque element with a bitmap inside it. The colour
    #      sweep did reach their hex literals, so they came out red; they
    #      came out red with NONE of the volume's motifs on them, which is
    #      exactly the "recolour, not a volume" fault the app itself had.
    #      The masar band is loaded beside the logo and tiled at the head and
    #      the foot of every card.
    #      The band image is held in ONE module-level slot rather than threaded
    #      through each painter's arguments: gcPaint and luPaintCut take
    #      different parameters, and the first version's foot-band anchor
    #      matched both luPaint's closing brace and gcPaint's — appending a
    #      call to a closure that was not in gcPaint's scope. That is a
    #      ReferenceError on every bracket and champions card, and
    #      ops/check-lineup.mjs drives luPaint and never saw it.
    ('const [im, logo] = await Promise.all([luImg(photo), luImg("assets/up-logo-national.png")]);',
     'const [im, logo, band] = await Promise.all([luImg(photo), '
     'luImg("assets/up-logo-national.png"), luImg(LU_BAND)]);\n'
     '  LU_BAND_IMG = LU_BAND_IMG || band;\n'
     '  await ncPreload(d);'),
    # ...and the cut-out path, which loads neither and would otherwise rely on
    # a photo card having been drawn first.
    ('const [cut, logo] = await Promise.all([luImg(cutUrl), '
     'luImg("assets/up-logo-national.png")]);',
     'const [cut, logo, band] = await Promise.all([luImg(cutUrl), '
     'luImg("assets/up-logo-national.png"), luImg(LU_BAND)]);\n'
     '  LU_BAND_IMG = LU_BAND_IMG || band;\n'
     '  await ncPreload(d);'),
    # 5f · THE PAINTER BECOMES THIS VOLUME'S OWN. luPaint and luPaintCut are
    #      the PREVIOUS volume's composition — a photo window with two dark
    #      plates stacked under it, a card designed for black. No amount of
    #      recolouring moves a shape, which is why the cards kept reading as
    #      inherited however many colours were swept. ncPaint lives in
    #      is the owner's design: the arch, the medallion on its apex, the
    #      ivory result plate, the score as the hero.
    #      Both inherited painters stay in the page UNREFERENCED rather than
    #      being cut, because this file is what the NEXT volume inherits and
    #      it should still read as the previous volume wrote it.
    ('    luPaint(c.getContext("2d"), kind, d, img, logo, adj);',
     '    ncPaint(c.getContext("2d"), kind, d, img, logo, adj, "photo");'),
    ('    luPaint(g, kind, d, img, logo, adj);',
     '    ncPaint(g, kind, d, img, logo, adj, "photo");'),
    ('  luPaintCut(g, kind, d, cut, logo, adj);',
     '  ncPaint(g, kind, d, cut, logo, adj, "cut");'),
    # 5e7 · NAME THE SAVE BANNER, so the session overlay can get out from
    #       under it. The banner is `sticky; top:0; z-index:50` and the open
    #       session is `fixed inset-0 z-40`, so the banner paints over the
    #       session's own header — and the BACK ARROW out of a night sits in
    #       that header. With a failed save showing, the organiser could not
    #       leave the screen they were stuck on, which is the worst possible
    #       moment for it. The banner is right to be on top; the overlay just
    #       has to start below it.
    ('<div onClick={() => { if (!getToken()) setShowLogin(true); }} style={{ position: "sticky", top: 0, zIndex: 50,',
     '<div className="na-savebanner" onClick={() => { if (!getToken()) setShowLogin(true); }} '
     'style={{ position: "sticky", top: 0, zIndex: 50,'),
    # 5e6 · THE SHARE CHIPS DECLARE THEIR OWN HEIGHT, so no stylesheet can
    #       raise it. `minHeight:36` is inline on the session's action row —
    #       LINE-UP, SHARE, PHOTOS, POSTS — and an inline declaration beats a
    #       rule. 36 is under the 44px floor every mobile guideline sets, on
    #       the row the organiser taps all evening. Changed where it is
    #       written rather than shouted down with !important.
    ('style={{ flex:"0 0 auto", minHeight:36, display:"inline-flex", alignItems:"center", gap:6,',
     'style={{ flex:"0 0 auto", minHeight:44, display:"inline-flex", alignItems:"center", gap:6,'),
    # 5e5 · NAME THE TWO LINES IN THE BRAND BAR, so the collapsing header can
    #       take the second one away without a `:nth-child` guess. The skin
    #       folds the header once the page moves; the volume's title stays
    #       because it is what tells you which app you are in, and the Arabic
    #       sub-line goes, because it is identity rather than navigation and
    #       it is the difference between a 46px row and a 58px one.
    ('            <div style={{minWidth:0}}>\n'
     '              <div style={{fontStyle:"italic",fontVariationSettings:"\'wdth\' 118,\'wght\' 900",\n'
     '                fontSize:20,lineHeight:1,whiteSpace:"nowrap"}}>56 NATIONAL SERIES</div>\n'
     '              <div style={{fontFamily:"\'JetBrains Mono\',monospace",fontWeight:700,fontSize:8,',
     '            <div style={{minWidth:0}}>\n'
     '              <div className="na-brand-name" '
     'style={{fontStyle:"italic",fontVariationSettings:"\'wdth\' 118,\'wght\' 900",\n'
     '                fontSize:20,lineHeight:1,whiteSpace:"nowrap"}}>56 NATIONAL SERIES</div>\n'
     '              <div className="na-brand-sub" '
     'style={{fontFamily:"\'JetBrains Mono\',monospace",fontWeight:700,fontSize:8,'),
    # 5e3 · THE RANK LEADER CARD COLLIDED WITH ITSELF.
    #       On a 390px phone the champion's row rendered
    #       "1 SESSIONS · 100% WIN WR5TSST R" — three text runs stacked on
    #       each other — and the name ran under the points.
    #       The meta row is a flex row holding two `white-space: nowrap`
    #       spans. A flex item defaults to `min-width: auto`, so a nowrap
    #       span CANNOT shrink below its content: the row simply overflows.
    #       Measured in the card's own box: "STREAK" ends at x403 in a 358px
    #       card, 45px past the edge, lying across "30" and "PTS". The card
    #       carries `overflow: hidden`, so there was nothing to scroll and
    #       nothing ran off the PAGE — it just overprinted.
    #       The HOME screen's version of the same card gets it right, with
    #       one span and an ellipsis. This one lets the row WRAP instead,
    #       which keeps both facts at any width rather than truncating the
    #       streak away on a narrow phone.
    #       INHERITED from Vol.7 through Vol.8, so blackout.urbanpadel.om has
    #       it too. Spliced here rather than fixed at source because Vol.8 is
    #       finished and its file should keep saying what it shipped.
    # 5e4 · THE SWEEP TURNED AN INK INTO A GROUND, AND THE INITIALS WENT WITH
    #       IT. A photo-less player gets a tinted disc with their initials,
    #       and the component picks the ink by LUMINANCE — dark on the light
    #       tints, light on the dark ones. Vol.8 wrote that dark ink as
    #       `#050505`, which is also its app background, so the colour sweep
    #       mapped it to `#B8141F`: right for a ground, and far too light for
    #       type on a light tint. Measured on the two bright tints, flag red
    #       is 5.92:1 on ivory and **3.91:1 on rose** — under AA on a third of
    #       the photo-less avatars in a 340-name roster.
    #       This volume's ink is `#1A0A0C`: 17.1:1 and 11.3:1 on the same two.
    #       A sweep entry could not fix this, because the SAME literal is a
    #       correct ground everywhere else in the file — it is the role that
    #       changed, not the colour, which is the whole reason this is an
    #       anchored replacement and not a table row.
    ('> 140 ? "#050505" : "#F2F2F2", fontSize: size * 0.36,',
     '> 140 ? "#1A0A0C" : "#F2F2F2", fontSize: size * 0.36,'),
    ('      color: lum > 140 ? "#050505" : "#F2F2F2", fontFamily: "\'Archivo\',sans-serif",',
     '      color: lum > 140 ? "#1A0A0C" : "#F2F2F2", fontFamily: "\'Archivo\',sans-serif",'),
    #       ...AND THE 2X CHIPS, which are the same mistake in three more
    #       places: Vol.8 set them `background:#FF2E88, color:#050505` — its
    #       accent with its ink on top — and the sweep turned that ink into
    #       the base red again, giving flag red on rose at 3.91:1 on the one
    #       chip in this app whose whole job is to be noticed. str.replace
    #       takes all three.
    ('style={{ background:"#FF2E88", color:"#050505", letterSpacing:".08em" }}>2X</div>',
     'style={{ background:"#F2B8BC", color:"#1A0A0C", letterSpacing:".08em" }}>2X</div>'),
    #       ANCHORED ON THE VOL.8 LITERAL: MOTIFS runs BEFORE the colour
    #       sweep, so the span still says #CFCFCF here, not this volume's
    #       ivory.
    ('                <div style={{display:"flex",gap:8,marginTop:5}}>\n'
     '                  <span style={{whiteSpace:"nowrap",fontFamily:"\'Archivo\',sans-serif",fontWeight:800,fontSize:9,\n'
     '                        letterSpacing:".16em",color:"#CFCFCF"}}>'
     '{leader.stats.sessionsPlayed} SESSIONS · {en.winRate}% WIN</span>',
     '                <div style={{display:"flex",gap:8,marginTop:5,flexWrap:"wrap"}}>\n'
     '                  <span style={{whiteSpace:"nowrap",fontFamily:"\'Archivo\',sans-serif",fontWeight:800,fontSize:9,\n'
     '                        letterSpacing:".16em",color:"#CFCFCF"}}>'
     '{leader.stats.sessionsPlayed} {leader.stats.sessionsPlayed === 1 ? "SESSION" : "SESSIONS"}'
     ' · {en.winRate}% WIN</span>'),
    # 5f2 · AND THE DRAW, THE TABLES AND THE BRACKET, which the first pass
    #       left behind entirely. Reported by the owner from the live night:
    #       "there's overlap in the posts, also needs to be updated to the
    #       newest theme" — two faults in one card and both real.
    #       The OVERLAP was a floor. The caller divides the band evenly
    #       between the groups, and gcGroup then sized its rows
    #       `Math.max(52, Math.min(96, fit))` — so at four rows a block drew
    #       62 + 4*(52+8) = 302px into a 232px slot, 70px over, every group,
    #       compounding down the card until GROUP B's header sat on GROUP A's
    #       last row. A floor that cannot be honoured does not make the row
    #       taller; it makes the block taller than the space it was given.
    #       ngGroup has no floor and sizes its type from the row it got.
    #       The THEME was the same "recolour, not a volume" fault the app
    #       needed teaching twice: these three were a true-black composition
    #       swept red. ngPaint gives them the volume's chrome — the inset
    #       masar bands, the khanjar ground, the header row with the Arabic
    #       opposite, the landmark medallion, pilled rows, green as the
    #       winner's EDGE and the champions on the same ivory plate the
    #       line-up card's result sits on.
    #       The band and the landmark art have to be loaded before the first
    #       paint, for the same reason every other draw entry point does it:
    #       a canvas draw of an undecoded image is a silent no-op, and an
    #       empty medallion looks exactly like a design choice.
    ('  const logo = await luImg("assets/up-logo-national.png");',
     '  const [logo, band] = await Promise.all([\n'
     '    luImg("assets/up-logo-national.png"), luImg(LU_BAND)]);\n'
     '  LU_BAND_IMG = LU_BAND_IMG || band;\n'
     '  LU_TILE_IMG = LU_TILE_IMG || await luImg(LU_TILE);\n'
     '  await ngPreload(d);'),
    ('  gcPaint(c.getContext("2d"), kind, d, logo, faces);',
     '  ngPaint(c.getContext("2d"), kind, d, logo, faces);'),
    #       The key's swatches follow the rows they describe: THROUGH is the
    #       flag's green, because that is what a green edge means everywhere
    #       else in this set, and "still in it" is the flag red. Swept, they
    #       were both ivory-ish and the key described nothing.
    ('      ? [["#C6FF00", "THROUGH"],\n'
     '         ["#FF2E88", session.thirdPlaceMode === "playoff" '
     '? "IN THE PLAYOFF" : "STILL IN IT"]]\n'
     '      : [["#C6FF00", groupsDone ? "THROUGH TO THE KNOCKOUT" '
     ': "CURRENTLY QUALIFYING"]],',
     '      ? [["' + CFG['palette']['green'] + '", "THROUGH"],\n'
     '         ["' + CFG['palette']['flag'] + '", '
     'session.thirdPlaceMode === "playoff" ? "IN THE PLAYOFF" : "STILL IN IT"]]\n'
     '      : [["' + CFG['palette']['green'] + '", groupsDone '
     '? "THROUGH TO THE KNOCKOUT" : "CURRENTLY QUALIFYING"]],'),
    ('function luPaint(g, kind, d, im, logo, adj) {\n'
     '  adj = adj || LU_ADJ0;\n'
     '  g.fillStyle = "#050505"; g.fillRect(0, 0, LU_W, LU_H);',
     'function luPaint(g, kind, d, im, logo, adj) {\n'
     '  adj = adj || LU_ADJ0;\n'
     '  g.fillStyle = "#B8141F"; g.fillRect(0, 0, LU_W, LU_H);'),
    #      THE WHOLE FOOTER BLOCK COMES UP 20px, mark and label together.
    #      The label sat 96 off the foot, which leaves 34px under it — and
    #      once the trim is inset 36 as the handoff draws it, the band lands
    #      on the label outright. Moving the LABEL alone put NIGHT 06 across
    #      the club mark's PLAYGROUND arc: the two are one lockup and the gap
    #      between them is the design, so they move by the same 20 or not at
    #      all. All three painters shift together; a card whose footer sat at
    #      a different height would read as a different set.
    ('g.fillText(ch, cx, LU_H - 96);', 'g.fillText(ch, cx, LU_H - 116);'),
    ('g.drawImage(off, (LU_W - lw) / 2, LU_H - 330);',
     'g.drawImage(off, (LU_W - lw) / 2, LU_H - 350);'),
    ('g.drawImage(off, (LU_W - lw) / 2, LU_H - 290);',
     'g.drawImage(off, (LU_W - lw) / 2, LU_H - 310);'),
    # The trim goes on LAST on each painter, so nothing can land on top of it.
    # Each anchor is that painter's own closing brace, and each is unique.
    ('  }\n}\n\n// Returns a data URL.',
     '  }\n  luTrim(g);\n}\n\n// Returns a data URL.'),
    # luPaintCut's closing: scanlines over everything, then the brace.
    ('  for (let y = 0; y < LU_H; y += 8) g.fillRect(0, y, LU_W, 2);\n}',
     '  for (let y = 0; y < LU_H; y += 8) g.fillRect(0, y, LU_W, 2);\n  luTrim(g);\n}'),
    # 5e · THE PLAYERS ARE NOT GRADED. The inherited treatment darkened the
    #      photo 34%, pushed contrast and took 62% of the saturation out, so
    #      the picture became a ground for the type to sit on. On black that
    #      is a look; on this red it is murk, and the owner's call is that
    #      the people in the photograph should be sharp and full colour —
    #      "no filter on the players, it needs to be more HD".
    #      What stays is the FLOOR and the two end fades, which are not a
    #      grade on anybody: without them the plates have nothing to sit on
    #      and the photo has a hard edge across the card.
    ('    if (LU_CAN_FILTER) {\n'
     '      g.filter = `brightness(${(br * (1 - 0.34 * gr)).toFixed(3)}) `\n'
     '               + `contrast(${(1 + 0.26 * gr).toFixed(3)}) `\n'
     '               + `saturate(${(1 - 0.62 * gr).toFixed(3)})`;\n'
     '      luCoverAdj(g, im, 0, top, LU_W, hh, adj);\n'
     '      g.filter = "none";\n'
     '    } else {',
     '    if (LU_CAN_FILTER) {\n'
     '      // Only what the organiser dialled in. `grade` no longer\n'
     '      // desaturates: it is the strength of the LIGHT below, not a\n'
     '      // wash over the people.\n'
     '      g.filter = br === 1 ? "none" : `brightness(${br.toFixed(3)})`;\n'
     '      luCoverAdj(g, im, 0, top, LU_W, hh, adj);\n'
     '      g.filter = "none";\n'
     '    } else {'),
    #      ...and GREEN IN THE LIGHT. The handoff reserves green for National
    #      Day and that rule holds for the chrome, but the owner asked for
    #      more of it on the line-up cards specifically. It goes in as a lamp
    #      and a pair of hairlines rather than as a tint: light in the room
    #      behind the players, which is what the two lamps were always for.
    ('    lamp(LU_W * 0.04, top + hh * 0.34, LU_W * 0.50, "255,46,136", 0.72);\n'
     '    lamp(LU_W * 0.98, top + hh * 0.26, LU_W * 0.48, "198,255,0",  0.62);\n'
     '    g.globalCompositeOperation = "source-over";',
     '    lamp(LU_W * 0.02, top + hh * 0.40, LU_W * 0.56, "12,168,86",  0.92);\n'
     '    lamp(LU_W * 1.00, top + hh * 0.30, LU_W * 0.50, "12,168,86",  0.62);\n'
     '    lamp(LU_W * 0.50, top + hh * 0.06, LU_W * 0.42, "247,241,230", 0.30);\n'
     '    g.globalCompositeOperation = "source-over";'),
    #      A HAIRLINE ACROSS THE PHOTO WINDOW DOES NOTHING, which is worth
    #      recording because it looked right in the source. The window closes
    #      with a vertical fade to the ground at both ends, drawn AFTER
    #      everything else — so a green rule at `top` and `top+hh` is painted
    #      over by opaque red. Measured: 0% green on either row. The green has
    #      to be light (the lamps above) or structure outside the window (the
    #      winner's edge below), never a line inside it.
    #      THE NO-BACKGROUND CARD GETS THE SAME LAMPS. luPaintCut has its own
    #      pair, which the colour sweep turned rose and ivory along with
    #      everything else — so the cut-out card carried no green at all while
    #      the photo card beside it did. Two cards from one night that do not
    #      look like one set is the fault worth engineering against.
    ('  lamp(40, 760, 620, "255,46,136", 0.62);\n'
     '  lamp(1050, 600, 600, "198,255,0", 0.56);',
     '  lamp(20, 820, 700, "12,168,86", 0.88);\n'
     '  lamp(1060, 660, 620, "12,168,86", 0.58);\n'
     '  lamp(540, 300, 480, "247,241,230", 0.26);'),
    #      THE WINNER'S PLATE IS EDGED IN THE FLAG'S GREEN. It is the one
    #      place on the card where green means something — this pair won —
    #      rather than being spent as decoration, which is the handoff's whole
    #      argument for reserving it. The SCORE stays ivory: #087A3F on the
    #      ink plate is about 2.6:1, fine for a 3px rule and not for 52px type.
    ('    plate(baseY, (d.a || "").toUpperCase(), "", "#C6FF00", d.aScore);',
     '    plate(baseY, (d.a || "").toUpperCase(), "", "#F7F1E6", d.aScore,\n'
     '          false, "#0CA856");'),
    ('  const plate = (y, name, chip, colour, score, dim) => {\n'
     '    g.fillStyle = "rgba(15,15,15,.92)";\n'
     '    g.fillRect(L, y, W, PH);\n'
     '    g.strokeStyle = colour; g.lineWidth = 3;',
     '  const plate = (y, name, chip, colour, score, dim, edge) => {\n'
     '    g.fillStyle = "rgba(15,15,15,.92)";\n'
     '    g.fillRect(L, y, W, PH);\n'
     '    g.strokeStyle = edge || colour; g.lineWidth = edge ? 5 : 3;'),
    #      THE CARDS' NEUTRAL GREYS ARE MUD ON RED, and the colour sweep never
    #      reached them: its table was built from the colours the DOM harness
    #      can see, and these are canvas fillStyles. #8A8A8A on the base red is
    #      about 1.9:1 — the night label under the club mark on every share
    #      card, and the dim state on every losing name.
    #      NOT done with a blanket sweep entry: #8A8A8A is also the "comeback"
    #      swatch in the points-receipt legend, and mapping it to the muted
    #      rose would make it identical to "streak" two rows below. A legend
    #      with two segments the same colour is a worse bug than a dim one.
    #      That legend still carries #8A8A8A and #4A4A4A and needs a palette
    #      decision, not a find-and-replace.
    ('g.fillStyle = "#8A8A8A";', 'g.fillStyle = "#F2D0D3";'),
    ('g.fillStyle = out ? "#8A8A8A" : "#F2F2F2";',
     'g.fillStyle = out ? "#F2B8BC" : "#FFFFFF";'),
    ('g.fillStyle = nm ? (won ? "#F2F2F2" : "#8A8A8A") : "#5A5A5A";',
     'g.fillStyle = nm ? (won ? "#FFFFFF" : "#F2B8BC") : "rgba(247,241,230,.35)";'),
    # gcPaint's closing, which is where the broken `luBand` call landed. Its
    # footer block is identical to luPaint's, so the brace alone is no anchor —
    # it is pinned to the comment that opens the next section.
    ('  }\n}\n\n// ── the knockout, round by round',
     '  }\n  luTrim(g);\n}\n\n// ── the knockout, round by round'),
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
    # THE CLUB MARK IS RE-INKED FOR THIS VOLUME. The shipped one is white with
    # an ORANGE ball (#F56530) — a Blackout-era accent belonging to no colour
    # here, and the first thing on every screen. Vol.9's cut is white with a
    # GREEN ball: on the red ground a red ball is red-on-red inside a thin
    # ivory ring and the dots turn to mud, which is a legibility result and
    # not a decorative one. ops/national-logo.py builds six variations and a
    # contact sheet composited on all five grounds.
    ("assets/up-logo-tight.png", "assets/up-logo-national.png"),
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
    # A NEUTRAL NEAR-BLACK SURFACE, in five places and never swept: the
    # lost-team chip and the disabled-button ground in both inherited copies
    # of the screens, and the disc a player's INITIAL is drawn on when they
    # have no photo — which is on every bracket card. A neutral grey-black on
    # a warm red reads as a hole punched in the page; this volume's near-black
    # is its ink, which is a very dark red and sits on the ground.
    ("#1A1A1A", "@@NB@@",  "#1A0A0C"),
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


def set_announcement(s, report):
    """Swap the whole template literal, not a line of it.

    Patching it line by line is how it got into this state: Vol.8's own
    announcement was already advertising eight sessions for a nine-night
    season, because each volume edited the lines it noticed.
    """
    pat = re.compile(r"(SEASON_ANNOUNCEMENT = `)(?:[^`\\]|\\.)*(`)", re.S)
    s2, n = pat.subn(lambda m: m.group(1) + ANNOUNCE + m.group(2), s, count=1)
    assert n == 1, "could not find SEASON_ANNOUNCEMENT to replace"
    # The copy people actually read must not contradict the season file.
    for claim in (f"{CFG['sessions']} sessions total", f"{POOL} OMR prize pool",
                  f"{CFG['entry']} OMR per player", CFG["previousVolume"],
                  CFG["host"], TAG):
        assert claim in ANNOUNCE, f"the announcement lost {claim!r}"
    assert "September Surge" not in ANNOUNCE, \
        "the announcement still names the volume before last"
    report(f"announcement: generated, {len(ANNOUNCE)} chars, "
           f"{_double_label().lower()} double")
    return s2


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

    # A STRAY `*/` SILENTLY EATS THE RULE AFTER IT, and nothing downstream can
    # see that. Editing a comment here left five lines of prose outside any
    # comment followed by a second `*/`; the parser threw away the block that
    # came next, and the tap-target floor it carried simply never applied —
    # with the stylesheet on screen plainly saying it should. The measurement
    # disagreeing with the source is the only thing that caught it.
    # Comments do not nest in CSS, so the test is exact: walking the file, an
    # opener must never appear while already inside a comment, and a closer
    # must never appear outside one.
    depth, i2, line = 0, 0, 1
    while i2 < len(skin) - 1:
        two = skin[i2:i2 + 2]
        if skin[i2] == "\n":
            line += 1
        if two == "/*":
            if depth:
                raise AssertionError(f"national-skin.css line {line}: a comment "
                                     f"opens inside a comment — CSS comments do "
                                     f"not nest, and the rule after the first "
                                     f"`*/` is being thrown away")
            depth, i2 = 1, i2 + 2
            continue
        if two == "*/":
            if not depth:
                raise AssertionError(f"national-skin.css line {line}: a stray "
                                     f"`*/` outside a comment — everything "
                                     f"between the previous `*/` and this one "
                                     f"is being parsed as CSS, and the next "
                                     f"rule is silently dropped")
            depth, i2 = 0, i2 + 2
            continue
        i2 += 1
    assert not depth, "national-skin.css ends inside an unclosed comment"

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
    # THE ONE THING THE SKIN CANNOT DO BY ITSELF. The collapsing header needs
    # to know whether the page has moved, and CSS has no scroll selector that
    # works here. This is a plain listener rather than a React effect on
    # purpose: it is chrome, it is the same on every screen, and threading a
    # piece of presentation state through the app to drive a stylesheet is how
    # the two get out of step.
    #   · PASSIVE, and it only writes when the answer CHANGES, so a scroll is
    #     not a attribute write per frame.
    #   · 8px of hysteresis, or a header that collapses at exactly 0 flickers
    #     against its own layout shift — folding it makes the page shorter,
    #     which can scroll you back to 0, which unfolds it.
    #   · It also listens in the CAPTURE phase, because the deepest screen in
    #     this app scrolls inside a `fixed inset-0` pane and never moves the
    #     window at all; without capture the header stays expanded there.
    boot = (
        '<script id="vol9-chrome">(function(){'
        'var on=false,h=document.documentElement;'
        'function f(e){'
        'var y=window.scrollY||0;'
        'var t=e&&e.target;'
        'if(t&&t!==document&&t.scrollTop!==undefined&&t.scrollTop>y)y=t.scrollTop;'
        'var n=on?y>2:y>8;'
        'if(n!==on){on=n;if(n)h.setAttribute("data-scrolled","1");'
        'else h.removeAttribute("data-scrolled");}}'
        'addEventListener("scroll",f,{passive:true,capture:true});'
        'addEventListener("resize",f,{passive:true});f();'
        # ...and the save banner's height, published as a custom property so
        # the open session can start below it. The banner wraps to two or
        # three lines depending on the width and on whether it is retrying, so
        # the number cannot be written down anywhere — it has to be measured.
        # A MutationObserver rather than a timer: it only costs anything when
        # React has actually re-rendered, and the banner appearing IS a
        # re-render.
        'var q=null;function b(){'
        'var e=document.querySelector(".na-savebanner");'
        'var v=e?Math.round(e.getBoundingClientRect().height):0;'
        'if(v!==q){q=v;h.style.setProperty("--na-banner",v+"px");}}'
        'var r=0;function s(){if(r)return;r=requestAnimationFrame(function(){r=0;b();});}'
        'new MutationObserver(s).observe(document.documentElement,'
        '{childList:true,subtree:true});'
        'addEventListener("resize",s,{passive:true});s();'
        '})();</script>\n')
    s = (s[:i] + '<style id="vol9-skin">\n' + skin + "\n</style>\n" + boot + s[i:])
    report(f"skin: {len(skin)} bytes appended as the last style block"
           ' (id="vol9-skin"), plus the collapsing-header listener')
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
    s = set_announcement(s, report)
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
    # signup post links Vol.8's final standings, and TWO code comments explain
    # what Vol.8 did differently — DOUBLE_NIGHTS (a threshold, not a list) and
    # the skin's note on the tagline's second ink. A comment naming the volume
    # it is contrasting with is the point of the comment; the check is for
    # renames that stopped matching, and it stays tight rather than being
    # loosened to "any number".
    allowed = {"Blackout Series": 5, "blackout.urbanpadel.om": 1, "Vol.8": 2}
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
