/**
 * JULY HEAT — VPS API server
 * Runs on urbanpadel.om VPS, proxied by nginx at heat.urbanpadel.om
 *
 * Routes:
 *   GET  /state              → { ok, state }   (public)
 *   POST /login  { pin }     → { ok, role, token }
 *   POST /save   { state }   → { ok }           (requires Bearer token)
 *   GET  /photos             → { ok, photos: { playerId: dataUrl } } (public)
 *   POST /photos { photos }  → { ok }           (requires Bearer token)
 *   GET  /session-photos             → { ok, photos: { sessionId: [dataUrl, ...] } } (public)
 *   POST /session-photos { photos }  → { ok }           (requires Bearer token)
 *
 * Env: /opt/july-heat-api/.env
 *   DATABASE_URL, ADMIN_PIN, SCORER_PIN, TOKEN_SECRET, PORT (default 3004)
 */

require("dotenv").config();
const express = require("express");
const { Pool } = require("pg");
const crypto = require("crypto");

const app = express();
app.use(express.json({ limit: "50mb" }));

const pool = new Pool({ connectionString: process.env.DATABASE_URL });
const TOKEN_TTL = 60 * 60 * 12; // 12 h

async function initDb() {
  await pool.query(`
    CREATE TABLE IF NOT EXISTS jh_tournament_state (
      id         INTEGER PRIMARY KEY DEFAULT 1,
      data       JSONB    NOT NULL DEFAULT '{}',
      updated_at TIMESTAMPTZ DEFAULT NOW()
    )
  `);
  await pool.query(`
    INSERT INTO jh_tournament_state (id, data) VALUES (1, '{}')
    ON CONFLICT (id) DO NOTHING
  `);
  await pool.query(`
    CREATE TABLE IF NOT EXISTS jh_player_photos (
      player_id  TEXT PRIMARY KEY,
      photo_data TEXT NOT NULL,
      updated_at TIMESTAMPTZ DEFAULT NOW()
    )
  `);
  await pool.query(`
    CREATE TABLE IF NOT EXISTS jh_session_photos (
      session_id TEXT PRIMARY KEY,
      photos     JSONB NOT NULL DEFAULT '[]',
      updated_at TIMESTAMPTZ DEFAULT NOW()
    )
  `);
  console.log("July Heat DB ready");
}

app.get("/state", async (req, res) => {
  try {
    const r = await pool.query("SELECT data FROM jh_tournament_state WHERE id = 1");
    res.json({ ok: true, state: r.rows[0]?.data || {} });
  } catch (e) {
    res.status(500).json({ ok: false, error: String(e.message) });
  }
});

app.post("/login", async (req, res) => {
  const pin = String(req.body?.pin ?? "");
  let role = null;
  if (process.env.ADMIN_PIN  && pin === String(process.env.ADMIN_PIN))  role = "admin";
  else if (process.env.SCORER_PIN && pin === String(process.env.SCORER_PIN)) role = "scorer";
  if (!role) return res.status(401).json({ ok: false });
  const token = signToken(role);
  res.json({ ok: true, role, token });
});

app.post("/save", async (req, res) => {
  const payload = requireAuth(req, res); if (!payload) return;
  const { state } = req.body || {};
  if (!state || typeof state !== "object")
    return res.status(400).json({ ok: false, error: "Missing state" });

  const clean = JSON.parse(JSON.stringify(state));
  if (Array.isArray(clean.players)) {
    clean.players = clean.players.map(p => {
      if (p.photoUrl?.startsWith("data:")) { const { photoUrl, ...rest } = p; return rest; }
      return p;
    });
  }
  if (Array.isArray(clean.sessions)) {
    clean.sessions = clean.sessions.map(s => {
      if (Array.isArray(s.photos) && s.photos.length > 0) { const { photos, ...rest } = s; return rest; }
      return s;
    });
  }
  try {
    await pool.query(
      `INSERT INTO jh_tournament_state (id, data, updated_at)
       VALUES (1, $1, NOW())
       ON CONFLICT (id) DO UPDATE SET data = $1, updated_at = NOW()`,
      [clean]
    );
    res.json({ ok: true });
  } catch (e) {
    res.status(500).json({ ok: false, error: String(e.message) });
  }
});

app.get("/photos", async (req, res) => {
  try {
    const r = await pool.query("SELECT player_id, photo_data FROM jh_player_photos");
    const photos = {};
    r.rows.forEach(row => { photos[row.player_id] = row.photo_data; });
    res.json({ ok: true, photos });
  } catch (e) {
    res.status(500).json({ ok: false, error: String(e.message) });
  }
});

app.post("/photos", async (req, res) => {
  const payload = requireAuth(req, res); if (!payload) return;
  const { photos } = req.body || {};
  if (!photos || typeof photos !== "object")
    return res.status(400).json({ ok: false, error: "Missing photos" });
  try {
    const entries = Object.entries(photos).filter(([, v]) => typeof v === "string" && v.length > 0);
    for (const [playerId, photoData] of entries) {
      await pool.query(
        `INSERT INTO jh_player_photos (player_id, photo_data, updated_at)
         VALUES ($1, $2, NOW())
         ON CONFLICT (player_id) DO UPDATE SET photo_data = $2, updated_at = NOW()`,
        [playerId, photoData]
      );
    }
    res.json({ ok: true });
  } catch (e) {
    res.status(500).json({ ok: false, error: String(e.message) });
  }
});

app.get("/session-photos", async (req, res) => {
  try {
    const r = await pool.query("SELECT session_id, photos FROM jh_session_photos");
    const photos = {};
    r.rows.forEach(row => { photos[row.session_id] = row.photos || []; });
    res.json({ ok: true, photos });
  } catch (e) {
    res.status(500).json({ ok: false, error: String(e.message) });
  }
});

app.post("/session-photos", async (req, res) => {
  const payload = requireAuth(req, res); if (!payload) return;
  const { photos } = req.body || {};
  if (!photos || typeof photos !== "object")
    return res.status(400).json({ ok: false, error: "Missing photos" });
  try {
    const entries = Object.entries(photos).filter(([, v]) => Array.isArray(v));
    for (const [sessionId, arr] of entries) {
      await pool.query(
        `INSERT INTO jh_session_photos (session_id, photos, updated_at)
         VALUES ($1, $2, NOW())
         ON CONFLICT (session_id) DO UPDATE SET photos = $2, updated_at = NOW()`,
        [sessionId, JSON.stringify(arr)]
      );
    }
    res.json({ ok: true });
  } catch (e) {
    res.status(500).json({ ok: false, error: String(e.message) });
  }
});


// ── June Fury scoring (mirrors frontend calcPlayerStats) ─────────────
function jfTeamWon(m, tid) {
  if (!m || !m.winner) return false;
  return m.winner === "team1" ? m.team1Id === tid : m.team2Id === tid;
}
function jfKoMatchPts(m, tid) {
  if (jfTeamWon(m, tid)) return 3;
  const t = m.lossType || "tiebreak";
  return t === "tiebreak" ? 2 : t === "competitive" ? 1 : 0;
}
function jfCalcGroupStandings(session, group) {
  const teams = (session.teams || []).filter(t => t.group === group);
  return teams.map(team => {
    let pts = 0, wins = 0;
    (session.groupMatches || []).forEach(m => {
      if (m.team1Id !== team.id && m.team2Id !== team.id || !m.winner) return;
      if (jfTeamWon(m, team.id)) { pts += 3; wins++; }
      else { const t = m.lossType || "tiebreak"; pts += t === "tiebreak" ? 2 : t === "competitive" ? 1 : 0; }
    });
    return { team, pts, wins };
  }).sort((a, b) => b.pts - a.pts || b.wins - a.wins);
}
function jfGetTopOfGroup(s, g) {
  const ov = s.topOfGroupOverride && s.topOfGroupOverride[g];
  if (ov) return ov;
  return jfCalcGroupStandings(s, g)[0]?.team?.id || null;
}
function jfCalcStreak(idxs) {
  if (!idxs?.length) return 0;
  const sorted = [...idxs].sort((a, b) => a - b);
  let total = 0, len = 0, last = null;
  for (const i of sorted) {
    if (last === null || i === last + 1) len++; else len = 1;
    last = i;
    if (len === 2 || len === 3) total += 1;
    else if (len >= 4) total += 3;
  }
  return Math.min(total, 5);
}
function jfCalcPlayerPts(pid, sessions) {
  let total = 0;
  const attended = [];
  sessions.forEach((s, idx) => {
    const team = (s.teams || []).find(t => t.p1Id === pid || t.p2Id === pid);
    if (!team) return;
    const mult = s.doublePoints ? 2 : 1;
    let played = 0;
    (s.groupMatches || []).forEach(m => {
      if (m.team1Id !== team.id && m.team2Id !== team.id || !m.winner) return;
      played++;
      if (jfTeamWon(m, team.id)) total += 3 * mult;
      else { const t = m.lossType || "tiebreak"; total += (t === "tiebreak" ? 2 : t === "competitive" ? 1 : 0) * mult; }
    });
    if (played > 0 && jfGetTopOfGroup(s, team.group) === team.id) total += 1 * mult;
    if (played > 0) attended.push(idx);
    const qfM = (s.bracket?.qf || []).find(m => (m.team1Id === team.id || m.team2Id === team.id) && m.winner);
    if (qfM) total += (1 + jfKoMatchPts(qfM, team.id)) * mult;
    const sfM = (s.bracket?.sf || []).find(m => (m.team1Id === team.id || m.team2Id === team.id) && m.winner);
    if (sfM) total += (2 + jfKoMatchPts(sfM, team.id)) * mult;
    const f = s.bracket?.final;
    if (f && (f.team1Id === team.id || f.team2Id === team.id) && f.winner)
      total += (3 + jfKoMatchPts(f, team.id) + (jfTeamWon(f, team.id) ? 5 : 0)) * mult;
  });
  total += jfCalcStreak(attended);
  return total;
}

app.get("/jf-leaderboard", async (req, res) => {
  try {
    const r = await pool.query("SELECT data FROM tournament_state WHERE id = 1");
    const jfState = r.rows[0]?.data || {};
    const players = jfState.players || [];
    const sessions = jfState.sessions || [];
    const standings = players
      .map(p => ({ id: p.id, name: p.name, pts: jfCalcPlayerPts(p.id, sessions) }))
      .sort((a, b) => b.pts - a.pts);
    res.json({ ok: true, standings });
  } catch (e) {
    res.status(500).json({ ok: false, error: String(e.message) });
  }
});

function requireAuth(req, res) {
  const auth = req.headers.authorization || "";
  const token = auth.replace(/^Bearer\s+/i, "");
  const payload = verifyToken(token);
  if (!payload) { res.status(401).json({ ok: false, error: "Unauthorized" }); return null; }
  return payload;
}

function hmac(data) {
  return crypto.createHmac("sha256", process.env.TOKEN_SECRET).update(data).digest("base64url");
}

function signToken(role) {
  const exp = Math.floor(Date.now() / 1000) + TOKEN_TTL;
  const data = `${role}.${exp}`;
  return `${data}.${hmac(data)}`;
}

function verifyToken(token) {
  if (!token) return null;
  const parts = token.split(".");
  if (parts.length !== 3) return null;
  const [role, exp, sig] = parts;
  if (sig !== hmac(`${role}.${exp}`)) return null;
  if (Number(exp) < Math.floor(Date.now() / 1000)) return null;
  if (role !== "admin" && role !== "scorer") return null;
  return { role, exp: Number(exp) };
}

const PORT = process.env.PORT || 3004;
initDb()
  .then(() => app.listen(PORT, "127.0.0.1", () => console.log(`July Heat API :${PORT}`)))
  .catch(e => { console.error("Startup failed:", e); process.exit(1); });
