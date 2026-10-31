# -*- coding: utf-8 -*-
"""Derive the 56 National Series (Vol.9) app from the Blackout Series (Vol.8) app.

Every volume in this series inherits the previous one's markup — July Heat became
August Attack became September Surge became Blackout. Doing it as a script rather
than a hand-fork means Vol.8 fixes can be pulled forward by re-running this, and
every substitution is asserted, so a rename that stops matching fails the build
instead of shipping a half-rebranded app.

WHAT THIS PASS DOES NOT DO: the National re-skin. This is the "working app
first" build — the volume's identity, numbers, host and schedule, on Vol.8's
markup and Vol.8's black-and-lime skin. The red/ivory/arch system in
brand/national/handoff/ is a separate pass, and keeping them apart means the
club can run night one on a correct app rather than waiting for a correct
*looking* one.

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

ASSETS = [
    ("assets/blackout-lockup.webp", "assets/national-lockup.webp"),
    ("assets/blackout-lockup.png", "assets/national-lockup.png"),
    ("assets/blackout-og.png", "assets/national-og.png"),
]


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
    s = plain(s, ASSETS, report, "assets")
    s = plain(s, SHARE_NAMES, report, "downloaded filenames")
    s = plain(s, ARCHIVE, report, "previous volume's archive link")
    s = plain(s, SEASON, report, "season shape")
    s = double_by_date(s, report)

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
                  "blackout.urbanpadel.om", "VOL.8", "Vol.8", "blackout-")
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
