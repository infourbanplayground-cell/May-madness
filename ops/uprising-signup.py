# -*- coding: utf-8 -*-
"""The WhatsApp sign-up list for an UPRISING night.

The sibling of ops/signup-post.py, which does the same job for Blackout. Two
differences, both of which matter:

  · UPRISING is entered ALONE. Blackout's list asks for "name + partner" and
    counts 16 teams; this one counts 16 PEOPLE, and says so twice, because the
    single thing most likely to stop someone replying is assuming they need to
    find a partner first.
  · The cap is the engine's, not a constant typed here. 16 is 4 courts x 4,
    and if the court count ever moves the list has to move with it or the
    organiser is taking names for places that do not exist.

WhatsApp gives you *bold*, _italic_ and emoji and nothing else — no colour. So
the volt/UV palette is carried by the two squares that match it, 🟩 and 🟪, and
nothing else; a post wearing six unrelated emoji reads as spam rather than as
a series.

  python3 ops/uprising-signup.py          # the list, for the group
  python3 ops/uprising-signup.py --full   # with the format block on top,
                                          # for a group that has not seen it

Every figure is derived: the date, entry, cap and prize from
uprising-social.json, and the courts, matches, target and points table out of
the SHIPPED engine via ops/uprising-facts.mjs — the same source the cards and
the app read, so the list cannot advertise a number they contradict.
"""
import datetime
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S = json.load(open(os.path.join(HERE, "uprising-social.json")))
F = json.loads(subprocess.check_output(
    ["node", os.path.join(HERE, "ops", "uprising-facts.mjs")], text=True))

# Waitlist of five, same as Blackout's. Long enough to cover the usual drop-outs
# on the day, short enough that nobody sits in it all week believing they are in.
WL_SIZE = 5
RULE = "━━━━━━━━━━━━━━"

# Local date arithmetic only — never toISOString(), the server is UTC and Oman
# is UTC+4, which has moved a date back a day in this repo before.
y, m, d = (int(x) for x in S["date"].split("-"))
DT = datetime.date(y, m, d)
TODAY = datetime.date.today()
WHEN = ("TODAY" if DT == TODAY
        else "TOMORROW" if DT == TODAY + datetime.timedelta(days=1)
        else DT.strftime("%A").upper())
DATE_STR = f'{DT.strftime("%a")} {DT.day} {DT.strftime("%b")}'
CUR = S["currency"]
CAP = min(S["cap"], F["players"])
CHAMP = f"{S['championPrize']} {CUR} {S.get('championPrizeKind', '')}".strip()


def main():
    full = "--full" in sys.argv[1:]
    L = []

    L.append(f"⬛🟩 *{S['name']} · {WHEN}* 🟩⬛")
    L.append(f"_{S['tagline']}_")
    L.append("")
    # Four lines and a link. The format used to be explained here in a block
    # the owner called too long, and it was: a sign-up post is read at a glance
    # by people who have already decided, and scrolled past by everyone else.
    # The explaining is the LINK's job now — americano-index.html carries
    # og: tags and a 1200x630 card, so the preview under this post is the
    # format. Hence the link sits above the list, where the preview renders,
    # rather than at the bottom as a footnote.
    L.append(f"🗓️ {DATE_STR}  ·  📍 Urban Playground")
    L.append(f"💸 {S['entry']} {CUR}  ·  🏆 {CHAMP}")
    L.append("🤝 *Come alone* — no partner needed")
    L.append("")
    L.append(f"👇 What it is: https://{S['host']}")
    L.append("")

    if full:
        # For a group that has not seen the cards. Kept to the three things
        # somebody needs before they can decide, not the whole rulebook —
        # the long version is a card and the full version is the app.
        L.append(f"🪜 *{F['courts']} courts, one ladder.* Win your match and you")
        L.append("move UP a court. Lose it and you move DOWN.")
        L.append("")
        L.append(f"🎾 *Every match is first to {F['target']}* — straight rallies,")
        L.append("no 15-30-40, no games, no sets.")
        L.append("")
        L.append("📊 *What you bank is what the COURT pays:*")
        # One court per line. As a single sentence this ran past 90 characters
        # and WhatsApp broke it wherever it liked, which put "2 on Court 4" on
        # a line of its own anyway — the one list in the post that has to be
        # scannable should not be left to the client's line breaks.
        L += [f"   Court {c} — *{F['win'][str(c)]}* for a win, {F['lose'][str(c)]} for a loss"
              for c in range(1, F["courts"] + 1)]
        L.append("Highest total at the end takes the night.")
        L.append("")
        L.append(f"🔁 Up to {F['matches']} matches each, a new partner almost")
        L.append("every round. Last round counts DOUBLE.")
        L.append("")
        L.append(RULE)
        L.append("")

    L.append("*Drop your name below* 👇")
    L.append("")
    L += [f"{i}-" for i in range(1, CAP + 1)]
    L.append("")
    L.append("🟪 *WAITLIST*")
    L += [f"{i}-" for i in range(1, WL_SIZE + 1)]
    L.append("")
    L.append(f"⚠️ *{CAP} places only* · first come, first on")

    out = "\n".join(L)
    print(out)

    # Two files, not one overwritten: the organiser wants the long one once and
    # the short one every month, and a run of the other should not take the
    # first away from them.
    name = "signup-list-full.txt" if full else "signup-list.txt"
    path = os.path.join(HERE, "brand", "uprising", "posts", name)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(out + "\n")
    print(f"\n--- written to {os.path.relpath(path, HERE)}"
          f"   ({DATE_STR}, {CAP} places + {WL_SIZE} waitlist,"
          f" {'with' if full else 'without'} the format block)", file=sys.stderr)


if __name__ == "__main__":
    main()
