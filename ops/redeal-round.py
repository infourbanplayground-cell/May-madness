# Re-deal round 4 of the live UPRISING night.
#
# R4 was dealt while round 3's Court 1 still read 10-11 (Talal + Muether
# winning). The score was corrected to 11-10 and the already-dealt round was
# not re-dealt, so the losers stayed on Court 1 and the winners went down.
#
# The replacement round is computed by the SHIPPED engine (uprising-engine.js)
# on the corrected state, not by hand. This only writes it in, and refuses
# unless the night is exactly as it was when that round was built.
import json, sys, subprocess, datetime

TID = "t_19s0g7lx"
new_round = json.load(open(sys.argv[1]))
fingerprint = json.load(open(sys.argv[2]))

def psql(sql, *args):
    cmd = ["sudo", "-u", "postgres", "psql", "-tAq", "urbanpadel", "-c", sql]
    out = subprocess.run(cmd, capture_output=True, text=True)
    if out.returncode: sys.exit("psql failed: " + out.stderr)
    return out.stdout

data = json.loads(psql("SELECT data FROM americano_state WHERE id = 1"))
t = next((x for x in data.get("tournaments", []) if x.get("id") == TID), None)
if t is None: sys.exit("ABORT: tournament not found")
if t.get("format") != "uprising": sys.exit("ABORT: not an uprising night")
if len(t.get("rounds", [])) != 4: sys.exit(f"ABORT: {len(t.get('rounds',[]))} rounds, expected 4 — the night moved on")

r4 = t["rounds"][3]
scored = [m for m in r4["courts"] if m.get("score1") is not None or m.get("score2") is not None]
if scored: sys.exit("ABORT: round 4 already has a score — not overwriting played results")

if json.dumps(t["rounds"][:3], sort_keys=True) != json.dumps(fingerprint, sort_keys=True):
    sys.exit("ABORT: rounds 1-3 changed since this fix was computed — re-run it")

stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
with open(f"/root/americano-state.bak-{stamp}.json", "w") as f: json.dump(data, f)

t["rounds"][3] = new_round
psql("UPDATE americano_state SET data = $json$" + json.dumps(data) + "$json$, updated_at = NOW() WHERE id = 1")
print(f"ok — round 4 re-dealt, backup /root/americano-state.bak-{stamp}.json")
for m in new_round["courts"]:
    print("   C%s %s vs %s" % (m["court"], m["team1"], m["team2"]))
