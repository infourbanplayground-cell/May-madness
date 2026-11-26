"""Rewrite brand/national/history.json so every duplicate id in
ops/player-aliases.json reads as the id that was kept.

The archived volumes still hold both records (their tables are history), so
`ops/build-history.py` puts the duplicates back every time it is re-run; run
this straight after it. Idempotent.

    python3 ops/apply-aliases-history.py
"""
import json, os
HERE = os.path.dirname(os.path.abspath(__file__))
P = os.path.join(os.path.dirname(HERE), "brand", "national", "history.json")
A = {k: v for k, v in json.load(open(os.path.join(HERE, "player-aliases.json"))).items() if not k.startswith("_")}
H = json.load(open(P))
clash = lambda: {i for i, m in enumerate(H["m"]) if len({m[4], m[5], m[6], m[7]}) < 4}
before = clash()      # June Fury already carries 8 such rows of its own: not ours to judge
n = 0
for m in H["m"]:
    for i in range(4, 8):
        if m[i] in A:
            m[i] = A[m[i]]; n += 1
for dup in A:
    H["names"].pop(dup, None)
# a merge must never put one person on both sides of a match, or twice on one team
new = clash() - before
assert not new, f"aliasing put one person twice into {len(new)} matches: {[H['m'][i] for i in list(new)[:2]]}"
json.dump(H, open(P, "w"), separators=(",", ":"))
print(f"history.json: {n} references rewritten across {len(A)} aliases")
