// Create the season's nine nights in the Heist state, one per date in
// heist-season.json, so the organiser never has to (owner, 26 Nov: "fix
// everything so we are ready").
//
//   scp ops/seed-heist-nights.js heist-season.json urbanpadel:/opt/heist-season-api/
//   ssh urbanpadel 'cd /opt/heist-season-api && set -a && . ./.env && set +a && DRY=1 node seed-heist-nights.js'
//   ssh urbanpadel 'cd /opt/heist-season-api && set -a && . ./.env && set +a && node seed-heist-nights.js'
//
// Each night is exactly what the app's own "+ New session" writes (same shape,
// same defaults: 4 groups, top 2 through, best2 thirds), with two things the
// form gets wrong for this volume set right:
//   - the DATE is the season's date, not the form's default, which is built
//     with toISOString() and reads yesterday before 4am Muscat;
//   - doublePoints comes from the season's doubleNights LIST (28 and 30 Dec),
//     not the inherited night-number threshold.
// The name is the episode ("EP.01 · The Briefing").
// Idempotent: a date that already has a night is left alone. A backup row goes
// to he_state_history and `version` is bumped, so a stale phone conflicts
// instead of overwriting.
const { Pool } = require("/opt/national-api/node_modules/pg");
const fs = require("fs");
const S = JSON.parse(fs.readFileSync(__dirname + "/heist-season.json", "utf8"));
const pool = new Pool(process.env.DATABASE_URL ? { connectionString: process.env.DATABASE_URL } : {});
const DRY = !!process.env.DRY;
const uid = p => p + "_" + Date.now().toString(36) + "_" + Math.random().toString(36).slice(2, 7);

(async () => {
  const c = await pool.connect();
  try {
    await c.query("BEGIN");
    const cur = await c.query("SELECT data, version FROM he_tournament_state WHERE id = 1 FOR UPDATE");
    const data = cur.rows[0].data, version = cur.rows[0].version;
    data.sessions = data.sessions || [];
    const have = new Set(data.sessions.map(s => s.date));
    const add = [];
    S.nights.forEach((date, i) => {
      if (have.has(date)) { console.log(`${date}: already has a night, left alone`); return; }
      const ep = S.episodes[i];
      add.push({ id: uid("s"), name: `${ep.code} · ${ep.title}`, date, groupCount: 4, qualifyCount: 2, thirdPlaceMode: "best2",
        doublePoints: S.doubleNights.includes(date), teams: [], groupMatches: [], bracket: { qf: [], sf: [], final: null },
        waitlist: [], completed: false });
    });
    add.forEach(s => console.log(`+ ${s.date}  ${s.name}${s.doublePoints ? "  2X" : ""}`));
    if (!add.length) { console.log("nothing to add"); await c.query("ROLLBACK"); return; }
    data.sessions = [...data.sessions, ...add].sort((a, b) => a.date.localeCompare(b.date));
    if (DRY) { console.log(`DRY: would write ${add.length} nights, version ${version} -> ${version + 1}`); await c.query("ROLLBACK"); return; }
    fs.writeFileSync(`/root/heist-seed-backup-${Date.now()}.json`, JSON.stringify(cur.rows[0].data));
    await c.query("INSERT INTO he_state_history (data, player_ct, match_ct, role) VALUES ($1,$2,$3,$4)",
      [cur.rows[0].data, (data.players || []).length, 0, "seed-nights"]);
    await c.query("UPDATE he_tournament_state SET data = $1, version = $2, updated_at = NOW() WHERE id = 1", [data, version + 1]);
    await c.query("COMMIT");
    console.log(`written: ${add.length} nights, version ${version} -> ${version + 1}`);
  } catch (e) { await c.query("ROLLBACK"); console.error(e.message); process.exit(1); }
  finally { c.release(); await pool.end(); }
})();
