/**
 * AMERICANO — standalone VPS API server for the classic Americano tournament format
 * (individual players, partners rotate every round, points accumulate individually).
 * Runs on the urbanpadel.om VPS, proxied by nginx at americano.urbanpadel.om.
 *
 * Routes:
 *   GET  /state                    → { ok, state }   (public)
 *   POST /login  { pin }           → { ok, role, token }
 *   POST /save   { state }         → { ok }           (requires Bearer token)
 *   GET  /photos                   → { ok, photos: { playerId: dataUrl } } (public)
 *   POST /photos { photos }        → { ok }           (requires Bearer token)
 *
 * Env vars (set in /opt/americano-api/.env):
 *   DATABASE_URL   postgresql://urbanpadel_app:...@127.0.0.1:5432/urbanpadel
 *   ADMIN_PIN      admin PIN
 *   SCORER_PIN     scorer PIN
 *   TOKEN_SECRET   long random string
 *   PORT           (optional, default 3007)
 */

require("dotenv").config();
const express = require("express");
const { Pool } = require("pg");
const crypto = require("crypto");

const app = express();
app.use(express.json({ limit: "50mb" }));

const pool = new Pool({ connectionString: process.env.DATABASE_URL });
const TOKEN_TTL = 60 * 60 * 12; // 12 h

// ── Bootstrap DB tables ────────────────────────────────────────────
async function initDb() {
  await pool.query(`
    CREATE TABLE IF NOT EXISTS americano_state (
      id         INTEGER PRIMARY KEY DEFAULT 1,
      data       JSONB    NOT NULL DEFAULT '{}',
      updated_at TIMESTAMPTZ DEFAULT NOW()
    )
  `);
  await pool.query(`
    INSERT INTO americano_state (id, data) VALUES (1, '{}')
    ON CONFLICT (id) DO NOTHING
  `);
  await pool.query(`
    CREATE TABLE IF NOT EXISTS americano_photos (
      player_id  TEXT PRIMARY KEY,
      photo_data TEXT NOT NULL,
      updated_at TIMESTAMPTZ DEFAULT NOW()
    )
  `);
  console.log("DB ready");
}

// ── Routes ────────────────────────────────────────────────────────

app.get("/state", async (req, res) => {
  try {
    const r = await pool.query("SELECT data FROM americano_state WHERE id = 1");
    res.json({ ok: true, state: r.rows[0]?.data || {} });
  } catch (e) {
    res.status(500).json({ ok: false, error: String(e.message) });
  }
});

app.post("/login", async (req, res) => {
  const pin = String(req.body?.pin ?? "");
  let role = null;
  if (process.env.ADMIN_PIN && pin === String(process.env.ADMIN_PIN)) role = "admin";
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

  // Strip base64 photos from state before storing (photos stored separately)
  const clean = JSON.parse(JSON.stringify(state));
  if (Array.isArray(clean.players)) {
    clean.players = clean.players.map(p => {
      if (p.photoUrl?.startsWith("data:")) { const { photoUrl, ...rest } = p; return rest; }
      return p;
    });
  }

  try {
    await pool.query(
      `INSERT INTO americano_state (id, data, updated_at)
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
    const r = await pool.query("SELECT player_id, photo_data FROM americano_photos");
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
        `INSERT INTO americano_photos (player_id, photo_data, updated_at)
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

// ── Auth helper ────────────────────────────────────────────────────

function requireAuth(req, res) {
  const auth = req.headers.authorization || "";
  const token = auth.replace(/^Bearer\s+/i, "");
  const payload = verifyToken(token);
  if (!payload) { res.status(401).json({ ok: false, error: "Unauthorized" }); return null; }
  return payload;
}

// ── HMAC token ─────────────────────────────────────────────────────

function hmac(data) {
  return crypto
    .createHmac("sha256", process.env.TOKEN_SECRET)
    .update(data)
    .digest("base64url");
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

// ── Start ─────────────────────────────────────────────────────────
const PORT = process.env.PORT || 3007;
initDb()
  .then(() => app.listen(PORT, "127.0.0.1", () => console.log(`Americano API :${PORT}`)))
  .catch(e => { console.error("Startup failed:", e); process.exit(1); });
