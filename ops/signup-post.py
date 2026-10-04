# -*- coding: utf-8 -*-
"""The WhatsApp sign-up sheet for a Blackout night.

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

    L = []
    L.append(f"🔥 *{cfg['name']} · Session {n}* 🔥")
    L.append(f"_Urban Social Series · {cfg['volume']}_")
    L.append("")
    if dbl:
        L.append("*⚡ DOUBLE POINTS ⚡ DOUBLE POINTS ⚡ DOUBLE POINTS*")
        L.append("")
    L.append("📍 Urban Playground")
    L.append(f"🗓️ {date_str} · 5:30 PM")
    L.append(f"💸 {cfg['entry']} OMR")
    L.append("")
    L.append(f"🏆 Win = {cfg['voucher']} OMR voucher per player")
    if dbl:
        L.append("🔥🔥 *EVERY POINT COUNTS TWICE — leaderboard about to FLIP* 🔥🔥")
    if n == 1:
        # Night one has no standings to tease and no sessions behind it, so it
        # gets the thing that is actually true of it: everyone starts level.
        L.append(f"📊 {len(nights)} nights · season starts at zero tonight")
        L.append(f"🥇 Season top 3: {' / '.join(str(p) for p in cfg['seasonPrizes'])} OMR")
    elif left > 0:
        L.append(f"📊 {left} session{'s' if left != 1 else ''} left · "
                 f"this is where champions are made")
    L.append("")
    L.append(f"🎾 Full table & your own rank: https://{cfg['host']}")
    L.append("")
    L.append("Drop name + partner below 👇")
    L.append("")
    L += [f"{i}-" for i in range(1, MAX_TEAMS + 1)]
    L.append("")
    L.append("⏳ Waitlist")
    L += [f"{i}-" for i in range(1, WL_SIZE + 1)]
    L.append("")
    L.append(f"⚠️ *{MAX_TEAMS} teams max* · first come, first served")
    L.append("💥 *Lights out.* 👑")

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
