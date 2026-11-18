#!/usr/bin/env python3
"""Every decided match from June Fury to Blackout, in one file the app can read.

The series app knows its own nine nights and nothing before them; the all-time
table carries only POINTS across volumes. So "Muatasim against Muntaser, all
time" — asked for on 16 Nov 2026 — had to be worked out by hand from five
databases. This writes the finished volumes' matches to
`brand/national/history.json`, which deploy-national.sh ships beside the page;
the app adds the running volume's matches from its own live state, so the
file only changes when a volume finishes.

    python3 ops/build-history.py                 # fetch each volume's state
    python3 ops/build-history.py --from <dir>    # use saved <port>.json files

Players are keyed by id, and ids have been carried volume to volume since June
(the roster merge keeps them), so one person is one key across all of it.
Guests merged later keep the merged id; names here are only a fallback for ids
the running roster no longer has.

Shape, kept small because a phone downloads it:
  { "built": "...", "vols": ["June Fury", ...],
    "names": { id: name },
    "m": [[vol, "YYYY-MM-DD", night, round, a1, a2, b1, b2, winner(1|2), sa, sb], ...] }
"""
import json
import os
import subprocess
import sys
import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "brand", "national", "history.json")

# Oldest first. Surge is archived: its API is stopped and the vhost serves a
# static snapshot of /state, so it is read over HTTPS like any visitor would.
VOLS = [
    ("June Fury", "ssh", 3001),
    ("July Heat", "ssh", 3004),
    ("August Attack", "ssh", 3005),
    ("September Surge", "file", "/var/www/surge.urbanpadel.om/public/state.json"),
    ("Blackout", "ssh", 3009),
]
ROUNDS = (("r16", "R16"), ("qf", "QF"), ("sf", "SF"))


def fetch(how, where, src_dir):
    if src_dir:
        name = ("surge" if how == "file" else str(where)) + ".json"
        return json.load(open(os.path.join(src_dir, name)))
    if how == "ssh":
        raw = subprocess.check_output(["ssh", "urbanpadel", f"curl -s localhost:{where}/state"], timeout=60)
        return json.loads(raw)
    raw = subprocess.check_output(["ssh", "urbanpadel", f"cat {where}"], timeout=60)
    return json.loads(raw)


def matches(st, vi):
    out = []
    for n, s in enumerate(st.get("sessions") or [], 1):
        teams = {t["id"]: (t.get("p1Id"), t.get("p2Id")) for t in s.get("teams") or []}
        b = s.get("bracket") or {}
        ms = [("G", m) for m in s.get("groupMatches") or []]
        for k, lab in ROUNDS:
            ms += [(lab, m) for m in b.get(k) or []]
        if b.get("thirdsPlayoff"):
            ms.append(("Q3", b["thirdsPlayoff"]))
        if b.get("final"):
            ms.append(("F", b["final"]))
        for rnd, m in ms:
            if not m or m.get("winner") not in ("team1", "team2"):
                continue
            a, c = teams.get(m.get("team1Id")), teams.get(m.get("team2Id"))
            if not a or not c or not all(a) or not all(c):
                continue
            sc = m.get("score") or {}
            out.append([vi, s.get("date") or "", n, rnd, a[0], a[1], c[0], c[1],
                        1 if m["winner"] == "team1" else 2, sc.get("t1"), sc.get("t2")])
    return out


def main():
    src = sys.argv[sys.argv.index("--from") + 1] if "--from" in sys.argv else None
    names, allm, per = {}, [], []
    for vi, (vol, how, where) in enumerate(VOLS):
        raw = fetch(how, where, src)
        st = raw.get("state", raw)
        for p in st.get("players") or []:
            names[p["id"]] = p.get("name") or names.get(p["id"], "?")
        ms = matches(st, vi)
        per.append((vol, len(st.get("sessions") or []), len(ms)))
        allm += ms
    used = {x for m in allm for x in m[4:8]}
    names = {k: v for k, v in names.items() if k in used}
    doc = {"built": datetime.date.today().isoformat(), "vols": [v[0] for v in VOLS],
           "names": names, "m": allm}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(doc, f, separators=(",", ":"), ensure_ascii=False)
    for vol, n, k in per:
        print(f"  {vol:<16} {n} nights  {k} matches")
    # The volumes are finished, so these totals should never shrink. A state
    # served empty by a restarting API would quietly write a history with a
    # volume missing, which every card would then report as the truth.
    assert all(k > 100 for _, _, k in per), "a volume came back nearly empty — not writing a history from it"
    print(f"wrote {os.path.relpath(OUT)}  {len(allm)} matches, {len(names)} players, "
          f"{os.path.getsize(OUT) // 1024}KB")


if __name__ == "__main__":
    main()
