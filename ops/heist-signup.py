# -*- coding: utf-8 -*-
"""The WhatsApp sign-up sheet for a Muscat Heist night.

The sibling of ops/signup-post.py (Blackout) and the same discipline: every
fact comes from heist-season.json — the date from `nights`, double points from
`doubleNights`, the entry, the voucher, the season prizes — so the sheet cannot
advertise a figure the app contradicts. The first night's sheet has to go out
before anyone has created the session in the app, which is why it exists.

WhatsApp has no colour, so the volume is carried by three squares and nothing
else: 🟧 a night played, ⬛ a night to come, 🩷 a double night. A post wearing a
dozen unrelated emoji reads as spam, not as a series.

  python3 ops/heist-signup.py 1      # Wed 2 Dec
  python3 ops/heist-signup.py 8      # Mon 28 Dec, double
"""
import datetime, json, os, sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAX_TEAMS = 16      # the venue's cap, the app's own MAX_TEAMS
WL_SIZE = 5


def sheet(n, cfg):
    nights = cfg["nights"]
    if not 1 <= n <= len(nights):
        raise SystemExit(f"night {n}: this volume has {len(nights)}")
    d = datetime.date.fromisoformat(nights[n - 1])
    dbl = nights[n - 1] in cfg["doubleNights"]
    ep = cfg["episodes"][n - 1]["code"]
    hh, mm = map(int, cfg["time"].split(":"))
    clock = datetime.time(hh, mm).strftime("%-I:%M %p")
    strip = "".join("🩷" if x in cfg["doubleNights"] else "🟧" if i < n else "⬛"
                    for i, x in enumerate(nights, 1))
    left = len(nights) - n
    RULE = "━━━━━━━━━━━━━━"
    L = [f"*{cfg['name'].upper()} · {ep.replace('.', ' ')}*",
         f"_Urban Social Series · {cfg['volumeLabel'].title()} · {cfg['month']}_",
         "", strip, f"_night {n} of {len(nights)}  ·  🩷 double points_", "", RULE]
    if dbl:
        L += ["🩷 *DOUBLE POINTS TONIGHT*", ""]
    L += [f"📍 {cfg['venue']}",
          f"🗓️ {d.strftime('%a %-d %b')}  ·  {clock}",
          f"💳 {cfg['entry']} OMR entry",
          f"🏆 {cfg['voucher']} OMR voucher to each of the night's champions"]
    if n == 1:
        L.append(f"🥇 Season top three: {' / '.join(map(str, cfg['seasonPrizes']))} OMR")
    elif left:
        L.append(f"{left} night{'s' if left != 1 else ''} left after this one")
    L += [RULE, "", f"Table, cards and your rank: https://{cfg['host']}", "",
          "*Name + partner* 👇", ""]
    L += [f"{i}-" for i in range(1, MAX_TEAMS + 1)]
    L += ["", "*Waitlist*"] + [f"{i}-" for i in range(1, WL_SIZE + 1)]
    L += ["", f"{MAX_TEAMS} teams. First come, first served.", "_Now loading Muscat._"]
    return "\n".join(L)


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    cfg = json.load(open(os.path.join(HERE, "heist-season.json")))
    out = sheet(n, cfg)
    # the claims, checked against the config they came from
    assert f"{cfg['entry']} OMR entry" in out and f"{cfg['voucher']} OMR voucher" in out
    assert ("DOUBLE POINTS" in out) == (cfg["nights"][n - 1] in cfg["doubleNights"])
    path = os.path.join(HERE, "brand", "heist", "posts", f"signup-night-{n}.txt")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, "w").write(out + "\n")
    print(out)
    print(f"\n--- {os.path.relpath(path, HERE)}", file=sys.stderr)


if __name__ == "__main__":
    main()
