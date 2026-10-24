# -*- coding: utf-8 -*-
"""Promote Americano/UPRISING guests into the shared roster — or merge them
into the person they already are.

WHY. `state.guests` is a dead end. The roster is a live read from August
Attack's table (`fetchSharedPlayers` in the API) and `/save` deletes
`state.players`, so a walk-in added on the check-in screen stays a guest
forever: they are pickable next week, but they hold no series or all-time
points in any volume and they are invisible to Blackout. On 24 Oct 2026
EIGHT of the fourteen playing were guests.

WHY NOT JUST PROMOTE THEM ALL. Because several are not new people. Matched
against the 286-name roster, "Al muatasim" is Muatasim, "Khalili" is Khalil,
"Harith" is Alharith. Promoting those creates a second record for somebody who
already has one, splits their history permanently, and is far harder to undo
than it was to cause — the same fault the Ghassan/ghassan pair already shows.

So every guest needs a decision, and only the club can make it: NEW, or the id
of the person they already are. This script does not guess. It prints the
candidates with a match score and refuses to run without a decision for each.

  python3 ops/promote-guests.py                      review: print the matches
  python3 ops/promote-guests.py --write-template     write a decisions file
  python3 ops/promote-guests.py --build              build the apply script

Then, and only when no night is being played:

  scp ops/apply-guest-decisions.js urbanpadel:/opt/americano-api/
  ssh urbanpadel 'cd /opt/americano-api && DRY=1 node apply-guest-decisions.js'
  ssh urbanpadel 'cd /opt/americano-api && node apply-guest-decisions.js'
"""
import difflib, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SP = "/tmp/claude-0/-home-user-May-madness/0e44f0ad-a683-5f0d-9de6-9459ae328963/scratchpad"
STATE = os.path.join(SP, "am2.json")
DECISIONS = os.path.join(HERE, "guest-decisions.json")
OUT = os.path.join(HERE, "apply-guest-decisions.js")


def norm(s):
    """Fold the things that differ between the same person typed twice.

    The Arabic article is the big one: "Al muatasim" and "Muatasim" are the
    same name with and without it, and an unfolded comparison scores them 0.62
    — below any threshold worth having.
    """
    s = s.lower().strip()
    s = re.sub(r"[^a-z ]", " ", s)
    s = re.sub(r"\b(al|el|bin|ibn)\b", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def load():
    if not os.path.exists(STATE):
        sys.exit(f"missing {STATE}\n"
                 f"  ssh urbanpadel 'curl -s localhost:3007/state' > {STATE}")
    d = json.load(open(STATE))
    d = d.get("state", d)
    return d["players"], d.get("guests", []), d.get("tournaments", [])


def matches(guest, players, n=4):
    gn = norm(guest["name"])
    gtok = set(gn.split())
    out = []
    for p in players:
        pn = norm(p["name"])
        r = difflib.SequenceMatcher(None, gn, pn).ratio()
        if gtok & set(pn.split()):
            r = max(r, 0.70)          # a shared whole name is worth a look
        if r >= 0.55:
            out.append((r, p["id"], p["name"]))
    return sorted(out, reverse=True)[:n]


def review(players, guests, tours):
    playing = set()
    for t in tours:
        for pid in (t.get("playerIds") or []):
            playing.add(pid)
    print(f"{len(players)} on the roster, {len(guests)} guests\n")
    for g in guests:
        ms = matches(g, players)
        seen = sum(1 for t in tours if g["id"] in (t.get("playerIds") or []))
        print(f"  {g['name']:<16} {g['id']}   played {seen} night(s)")
        if not ms:
            print(f"       no roster match — almost certainly NEW")
        for r, pid, nm in ms:
            mark = "  <-- same person?" if r >= 0.85 else ""
            print(f"       {r:.2f}  {nm:<22} {pid}{mark}")
        print()


def template(players, guests):
    """A decisions file with the best guess PRE-FILLED AS A COMMENT ONLY.

    Every value starts as null, which the builder refuses. Nothing here is a
    default: a wrong merge is worse than a wrong new record, because it hides
    one person's points inside another's.
    """
    doc = {
        "_comment": [
            "One entry per guest. Set each value to:",
            "   \"new\"          — a real new person, add them to the roster",
            "   \"<player id>\"  — they already exist, merge into that record",
            "   \"skip\"         — leave them as a guest for now",
            "null is not a decision and the builder refuses it.",
            "",
            "A merge rewrites the guest's id to the roster id EVERYWHERE in",
            "americano_state — every night's playerIds, every round's teams and",
            "sit-outs, the rest rota and the opening ladder — so the points they",
            "have already scored follow them. It is not reversible from here.",
        ],
        "guests": {},
    }
    for g in guests:
        ms = matches(g, players)
        doc["guests"][g["id"]] = {
            "name": g["name"],
            "decision": None,
            "candidates": [{"id": pid, "name": nm, "score": round(r, 2)} for r, pid, nm in ms],
        }
    with open(DECISIONS, "w") as f:
        json.dump(doc, f, indent=2, ensure_ascii=False)
    print(f"wrote {DECISIONS} — fill in every \"decision\", then --build")


def build(players, guests, tours):
    if not os.path.exists(DECISIONS):
        sys.exit("no decisions file — run --write-template first")
    doc = json.load(open(DECISIONS))["guests"]
    by_id = {p["id"]: p["name"] for p in players}

    promote, merge, skip = [], [], []
    for g in guests:
        e = doc.get(g["id"])
        if not e or e.get("decision") in (None, ""):
            sys.exit(f"no decision for {g['name']} ({g['id']}) — every guest needs one")
        dec = e["decision"]
        if dec == "skip":
            skip.append(g)
        elif dec == "new":
            promote.append(g)
        elif dec in by_id:
            merge.append((g, dec, by_id[dec]))
        else:
            sys.exit(f"{g['name']}: \"{dec}\" is neither new, skip, nor a roster id")

    # A merge that puts one person on a court twice would corrupt a night that
    # has already been played, and no amount of care downstream recovers it.
    for g, pid, nm in merge:
        for t in tours:
            ids = t.get("playerIds") or []
            if g["id"] in ids and pid in ids:
                sys.exit(f"REFUSING: {g['name']} and {nm} are both in "
                         f"\"{t.get('name')}\" — merging would put one person "
                         f"on two courts in the same night. Resolve that night first.")

    plan = {
        "promote": [{"id": g["id"], "name": g["name"]} for g in promote],
        "merge": [{"from": g["id"], "to": pid, "name": g["name"], "into": nm}
                  for g, pid, nm in merge],
        "skip": [g["id"] for g in skip],
    }
    with open(OUT, "w") as f:
        f.write(APPLY.replace("__PLAN__", json.dumps(plan, indent=2, ensure_ascii=False)))
    print(f"wrote {OUT}")
    print(f"  promote {len(promote)}: " + ", ".join(g["name"] for g in promote))
    for g, pid, nm in merge:
        print(f"  merge   {g['name']} -> {nm}")
    if skip:
        print(f"  skip    {len(skip)}: " + ", ".join(g["name"] for g in skip))
    print("\nnow, and only when no night is being played:")
    print("  scp ops/apply-guest-decisions.js urbanpadel:/opt/americano-api/")
    print("  ssh urbanpadel 'cd /opt/americano-api && DRY=1 node apply-guest-decisions.js'")
    print("  ssh urbanpadel 'cd /opt/americano-api && node apply-guest-decisions.js'")


APPLY = r"""// Generated by ops/promote-guests.py — do not edit by hand.
//
// Promotes guests into the shared roster (aa_tournament_state.data.players)
// and merges the ones who already have a record, rewriting their id
// everywhere in americano_state so the points they scored follow them.
//
//   DRY=1 node apply-guest-decisions.js    print the changes, write nothing
//         node apply-guest-decisions.js    apply them
const { Pool } = require("pg");
require("dotenv").config();
const pool = new Pool({ connectionString: process.env.DATABASE_URL });
const DRY = !!process.env.DRY;
const PLAN = __PLAN__;

// Rewrite every occurrence of an id: array values, string values and OBJECT
// KEYS — ladder0 and the court map are keyed by player id, so a value-only
// walk would leave a merged player standing on their own old court.
function rewrite(node, from, to) {
  if (Array.isArray(node)) return node.map(v => rewrite(v, from, to));
  if (node && typeof node === "object") {
    const out = {};
    for (const [k, v] of Object.entries(node)) out[k === from ? to : k] = rewrite(v, from, to);
    return out;
  }
  return node === from ? to : node;
}

(async () => {
  const aa = await pool.query("SELECT data FROM aa_tournament_state WHERE id = 1");
  const am = await pool.query("SELECT data FROM americano_state WHERE id = 1");
  if (!aa.rows[0] || !am.rows[0]) throw new Error("missing state row");
  const roster = aa.rows[0].data;
  let state = am.rows[0].data;
  const before = (roster.players || []).length;

  const have = new Set((roster.players || []).map(p => p.id));
  for (const g of PLAN.promote) {
    if (have.has(g.id)) { console.log(`  already on the roster: ${g.name}`); continue; }
    // Keeps the guest's OWN id, so every night they have already played
    // still points at them and nothing has to be rewritten.
    roster.players.push({ id: g.id, name: g.name, photoUrl: "" });
    have.add(g.id);
    console.log(`  + roster: ${g.name} (${g.id})`);
  }

  for (const m of PLAN.merge) {
    if (!have.has(m.to)) throw new Error(`merge target missing: ${m.to}`);
    state = rewrite(state, m.from, m.to);
    console.log(`  ~ merged: ${m.name} -> ${m.into}`);
  }

  // Everything decided is out of the guest list; anything skipped stays.
  const decided = new Set([...PLAN.promote.map(g => g.id), ...PLAN.merge.map(m => m.from)]);
  const keptGuests = (state.guests || []).filter(g => !decided.has(g.id));
  state = { ...state, guests: keptGuests };

  console.log(`\n  roster ${before} -> ${roster.players.length}`);
  console.log(`  guests ${(am.rows[0].data.guests || []).length} -> ${keptGuests.length}`);

  if (DRY) { console.log("\nDRY — nothing written"); await pool.end(); return; }
  await pool.query("UPDATE aa_tournament_state SET data = $1 WHERE id = 1", [roster]);
  await pool.query("UPDATE americano_state SET data = $1, updated_at = NOW() WHERE id = 1", [state]);
  console.log("\nwritten");
  await pool.end();
})().catch(e => { console.error(e); process.exit(1); });
"""


if __name__ == "__main__":
    players, guests, tours = load()
    if "--write-template" in sys.argv:
        template(players, guests)
    elif "--build" in sys.argv:
        build(players, guests, tours)
    else:
        review(players, guests, tours)
