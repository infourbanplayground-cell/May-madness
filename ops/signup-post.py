# -*- coding: utf-8 -*-
"""The WhatsApp sign-up sheet for a Blackout night.

WhatsApp gives you *bold*, _italic_ and emoji, and that is the whole of it —
there is no colour. So the volume's palette is carried by the only three
coloured squares that match it (🟩 lime, 💗 magenta, 🟪 UV) and nothing else;
a post wearing six unrelated emoji reads as spam rather than as a series.

The app generates this itself once a session exists (generateReminderText), but
the first night's sheet has to go out BEFORE anyone has created the session —
and so does every night's, if the organiser wants it posted early. This writes
the same sheet from the season config, so the two cannot disagree.

  python3 ops/signup-post.py 1        # night 1
  python3 ops/signup-post.py 8        # night 8, which is double points

Everything is derived: the date comes from `nights`, the entry and the voucher
from the config, and whether a night is double points from `doubleFromSession`.
Nothing about the night is typed here.
"""
import datetime, json, os, sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# The app's own list sizes. 16 teams is the cap the venue can run; the waitlist
# is five. NOTE: the app's generateReminderText prints a 3-line waitlist while
# its own signup tab shows WL_SIZE = 5 — a hard-coded Array(3) against the
# constant. This follows the constant, which is what the organiser actually
# fills in.
MAX_TEAMS = 16
WL_SIZE = 5


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    cfg = json.load(open(os.path.join(HERE, "blackout-season.json")))
    nights = cfg["nights"]
    if not 1 <= n <= len(nights):
        sys.exit(f"night {n} — this volume has {len(nights)}")

    d = datetime.date.fromisoformat(nights[n - 1])
    dbl = n >= cfg["doubleFromSession"]
    left = len(nights) - n
    date_str = d.strftime("%a %-d %b")

    # ── the season strip ─────────────────────────────────────────────────
    # WhatsApp has no colour. Emoji are the only palette there is, and the
    # volume's three happen to exist as squares: 🟩 lime, 💗 magenta, 🟪 UV.
    # Using those three and nothing else keeps the post in the series' colours
    # instead of the usual confetti of unrelated emoji.
    #
    # The strip is the season's lights coming on, which is the one device that
    # could only belong to a volume called Blackout: a night that has been
    # played is lit, a night still to come is dark, and the double-points
    # nights are magenta from the start because everyone should see them
    # coming. On night 1 it reads 🟩⬛⬛⬛⬛⬛⬛💗💗.
    strip = ""
    for i in range(1, len(nights) + 1):
        if i >= cfg["doubleFromSession"]:
            strip += "💗"
        elif i <= n:
            strip += "🟩"
        else:
            strip += "⬛"

    RULE = "━━━━━━━━━━━━━━"

    L = []
    L.append(f"⬛🟩 *{cfg['nameTitle'].upper()} · NIGHT {n}* 🟩⬛")
    L.append(f"_Urban Social Series · {cfg['volume']}_")
    L.append("")
    L.append(strip)
    L.append(f"_night {n} of {len(nights)}  ·  💗 = double points_")
    L.append("")
    L.append(RULE)
    if dbl:
        L.append("💗 *DOUBLE POINTS TONIGHT* 💗")
        L.append("_every point counts twice_")
        L.append("")
    L.append("📍 Urban Playground")
    L.append(f"🗓️ {date_str}  ·  5:30 PM")
    L.append(f"💸 {cfg['entry']} OMR")
    L.append(f"🏆 {cfg['voucher']} OMR voucher — each winner")
    if n == 1:
        L.append(f"🥇 Season top 3 — {' / '.join(str(p) for p in cfg['seasonPrizes'])} OMR")
    elif left > 0:
        L.append(f"📊 {left} night{'s' if left != 1 else ''} left after tonight")
    L.append(RULE)
    L.append("")
    L.append(f"🎾 Table & your rank: https://{cfg['host']}")
    L.append("")
    L.append("*Drop name + partner* 👇")
    L.append("")
    L += [f"{i}-" for i in range(1, MAX_TEAMS + 1)]
    L.append("")
    L.append("🟪 *WAITLIST*")
    L += [f"{i}-" for i in range(1, WL_SIZE + 1)]
    L.append("")
    L.append(f"⚠️ *{MAX_TEAMS} teams max* · first come, first served")
    L.append("💥 *LIGHTS OUT.*")

    out = "\n".join(L)
    print(out)

    path = os.path.join(HERE, "brand", "blackout", "posts", f"signup-session-{n}.txt")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(out + "\n")
    print(f"\n--- written to {os.path.relpath(path, HERE)}"
          f"   ({date_str}, {'double points' if dbl else 'normal'},"
          f" {MAX_TEAMS} teams + {WL_SIZE} waitlist)", file=sys.stderr)


if __name__ == "__main__":
    main()
