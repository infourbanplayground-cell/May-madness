# -*- coding: utf-8 -*-
"""Mark an ACTIVE Americano/UPRISING night as abandoned, in the database.

Why not the app: /save requires a scorer token, and the PINs live in the
server's .env, which never leaves the server.

Why not a heredoc: CLAUDE.md, "Shell heredoc + backtick SQL". This gets scp'd
and run with python3 on the VPS instead.

ABANDONED, NOT DELETED — the app's own word for this. The scores stay in the
state, the night stops being `active` so Setup (and, for a guest, the home
page) comes back, and it does not appear in History, which only lists
`completed`. Reversible: set the status back to "active".

    scp ops/abandon-test-night.py urbanpadel:/tmp/
    ssh urbanpadel 'python3 -I /tmp/abandon-test-night.py --dry'
    ssh urbanpadel 'python3 -I /tmp/abandon-test-night.py'
"""
import json
import subprocess
import sys

DRY = "--dry" in sys.argv[1:]
PSQL = ["sudo", "-u", "postgres", "psql", "-tAq", "urbanpadel", "-c"]


def q(sql):
    return subprocess.run(PSQL + [sql], stdout=subprocess.PIPE,
                          check=True).stdout.decode()


raw = q("SELECT data FROM americano_state WHERE id = 1").strip()
if not raw:
    sys.exit("no row in americano_state")
state = json.loads(raw)
ts = state.get("tournaments", [])

print(f"{len(ts)} tournaments on record:")
hit = None
for t in ts:
    n = len(t.get("rounds") or [])
    print(f"  {t.get('status','?'):10} {t.get('format') or 'americano':10} "
          f"{len(t.get('playerIds') or []):3} players {n:3} rounds  {t.get('name')}")
    if t.get("status") == "active":
        hit = t

if not hit:
    print("\nnothing is active — nothing to do")
    sys.exit(0)

print(f"\nwould abandon: {hit.get('name')} "
      f"({len(hit.get('rounds') or [])} rounds, {len(hit.get('playerIds') or [])} players)")
if DRY:
    print("DRY — nothing written")
    sys.exit(0)

# Keep a copy of the row before touching it. Cheap, and the only undo there is.
q("CREATE TABLE IF NOT EXISTS americano_state_bak "
  "(taken_at timestamptz default now(), data jsonb)")
q("INSERT INTO americano_state_bak (data) SELECT data FROM americano_state WHERE id = 1")

hit["status"] = "abandoned"
hit["abandonedAt"] = hit.get("abandonedAt") or 0
blob = json.dumps(state).replace("'", "''")
q(f"UPDATE americano_state SET data = '{blob}'::jsonb, updated_at = now() WHERE id = 1")

after = json.loads(q("SELECT data FROM americano_state WHERE id = 1").strip())
act = [t for t in after.get("tournaments", []) if t.get("status") == "active"]
print(f"done — active nights now: {len(act)}")
print("backed up to americano_state_bak; to undo, set that night's status "
      "back to \"active\"")
