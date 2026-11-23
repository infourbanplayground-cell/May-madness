// Merge duplicate player records in a live volume's state (owner's call, 23 Nov 2026:
// "Merge the two MSM records", "Aamir is the same").
//
//   node merge-players.js <prefix> <dupId>:<keepId> [...]      (run on the server)
//   DRY=1 ...                                                   prints, writes nothing
//
// What it does, per pair, in <prefix>_tournament_state:
//   - every occurrence of dupId (values AND object keys) becomes keepId, so each
//     night the duplicate played now counts for the kept record;
//   - the duplicate's player entry is removed; prevSeriesPts are combined per
//     volume taking the LARGER value, never the sum — both MSM records carried
//     the same July Heat 50 from an earlier roster merge, and a sum would have
//     invented 50 points;
//   - refuses if any session would then hold keepId twice in one team or one
//     match (the "one person on two sides" case);
//   - writes a backup row to <prefix>_state_history first, bumps `version` so a
//     phone holding the old state gets a conflict instead of overwriting this;
//   - moves the duplicate's stored photo if the kept record has none.
const { Pool } = require("/opt/national-api/node_modules/pg");
const fs = require("fs");
// run with the API's own .env sourced (set -a; . /opt/national-api/.env); it never leaves the server
const pool = new Pool(process.env.DATABASE_URL ? { connectionString: process.env.DATABASE_URL } : {});
const [prefix, ...pairs] = process.argv.slice(2);
if (!/^[a-z]{2}$/.test(prefix || "") || !pairs.length) { console.error("usage: node merge-players.js <prefix> dup:keep ..."); process.exit(2); }
const DRY = !!process.env.DRY;

function rewrite(x, dup, keep) {
  if (Array.isArray(x)) return x.map(v => rewrite(v, dup, keep));
  if (x && typeof x === "object") {
    const o = {};
    for (const [k, v] of Object.entries(x)) o[k === dup ? keep : k] = rewrite(v, dup, keep);
    return o;
  }
  return x === dup ? keep : x;
}
const count = (x, id) => (JSON.stringify(x).match(new RegExp(id, "g")) || []).length;

(async () => {
  const c = await pool.connect();
  try {
    await c.query("BEGIN");
    const cur = await c.query(`SELECT data, version FROM ${prefix}_tournament_state WHERE id = 1 FOR UPDATE`);
    let data = cur.rows[0].data; const version = cur.rows[0].version;
    fs.writeFileSync(`/root/merge-backup-${prefix}-${Date.now()}.json`, JSON.stringify(data));
    for (const pair of pairs) {
      const [dup, keep] = pair.split(":");
      const P = data.players || [];
      const d = P.find(p => p.id === dup), k = P.find(p => p.id === keep);
      if (!k) throw new Error(`${keep} is not in ${prefix}'s roster`);
      if (!d) { console.log(`${dup}: not in ${prefix}'s roster, rewriting references only`); }
      console.log(`${prefix}: ${d ? d.name : dup} (${dup}, ${count(data, dup)} refs) -> ${k.name} (${keep}, ${count(data, keep)} refs)`);
      if (d) {
        const a = k.prevSeriesPts || {}, b = d.prevSeriesPts || {}, m = { ...a };
        for (const [vol, pts] of Object.entries(b)) {
          if (vol in a && a[vol] !== pts) console.log(`  ${vol}: kept ${a[vol]}, duplicate had ${pts} -> ${Math.max(a[vol], pts)}`);
          m[vol] = vol in a ? Math.max(a[vol], pts) : pts;
        }
        if (Object.keys(m).length) k.prevSeriesPts = m;
        if (!k.photoUrl && d.photoUrl) k.photoUrl = d.photoUrl;
        data.players = P.filter(p => p.id !== dup);
      }
      data = rewrite(data, dup, keep);
      // one person may not end up on both sides of anything
      for (const s of data.sessions || []) {
        for (const t of s.teams || []) if (t.p1Id === keep && t.p2Id === keep) throw new Error(`session ${s.id}: ${keep} partners himself`);
        const teamOf = id => (s.teams || []).filter(t => t.p1Id === id || t.p2Id === id).length;
        if (teamOf(keep) > 1) throw new Error(`session ${s.id}: ${keep} is in ${teamOf(keep)} teams`);
      }
      console.log(`  after: ${count(data, dup)} refs to ${dup}, ${count(data, keep)} to ${keep}`);
      const ph = await c.query(`SELECT player_id FROM ${prefix}_player_photos WHERE player_id = ANY($1)`, [[dup, keep]]);
      const has = new Set(ph.rows.map(r => r.player_id));
      if (has.has(dup) && !has.has(keep)) {
        console.log(`  moving ${dup}'s photo to ${keep}`);
        if (!DRY) await c.query(`UPDATE ${prefix}_player_photos SET player_id = $2 WHERE player_id = $1`, [dup, keep]);
      }
    }
    if (DRY) { console.log("DRY: nothing written"); await c.query("ROLLBACK"); return; }
    await c.query(`INSERT INTO ${prefix}_state_history (data, player_ct, match_ct, role) VALUES ($1,$2,$3,$4)`,
      [cur.rows[0].data, (cur.rows[0].data.players || []).length, 0, "pre-merge"]);
    await c.query(`UPDATE ${prefix}_tournament_state SET data = $1, version = $2, updated_at = NOW() WHERE id = 1`, [data, version + 1]);
    await c.query("COMMIT");
    console.log(`${prefix}: written, version ${version} -> ${version + 1}`);
  } catch (e) { await c.query("ROLLBACK"); console.error("ABORTED:", e.message); process.exitCode = 1; }
  finally { c.release(); await pool.end(); }
})();
