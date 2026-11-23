/* Muscat Heist API — part 1: the player photos.
 *
 * heist.urbanpadel.om/photos/ lists every player with the photo the apps hold
 * today; the organiser makes a Heist-format portrait (ChatGPT, from that
 * photo and the style prompt on the page) and uploads it against the player.
 * The page crops and sizes it in the browser (4:5, 1080x1350) before it is
 * sent, so what is previewed is exactly what is stored.
 *
 *   GET    /api/roster            everyone, ordered: playing now first, most nights first
 *   GET    /api/ref/:id           the player's CURRENT photo (from the live volume), as a file
 *   POST   /api/login {pin}       -> { token }   admin or photographer PIN
 *   POST   /api/photo/:id {image} Bearer token; image = data:image/jpeg;base64,...
 *   DELETE /api/photo/:id         Bearer token; the previous Heist photo goes to history
 *
 * Photos are files: /var/www/heist.urbanpadel.om/public/players/<id>.jpg, served
 * by nginx, with every replaced one kept in /opt/heist-api/history/ — an
 * upload is never destructive. The roster is READ LIVE from the National API
 * (the same ids every volume uses since June) and the Americano app's guests,
 * so it cannot drift from the apps.
 *
 * env: ADMIN_PIN, PHOTOGRAPHER_PIN, TOKEN_SECRET, PORT (3012)
 */
const express = require("express");
const crypto = require("crypto");
const fs = require("fs");
const path = require("path");
const http = require("http");

const PORT = +process.env.PORT || 3012;
const PUB = "/var/www/heist.urbanpadel.om/public/players";
const HIST = path.join(__dirname, "history");
const LOG = path.join(__dirname, "uploads.log");
const CURRENT_FROM = "2026-10-01";      // "playing now": a team since Blackout began, or an UPRISING night
const TOKEN_TTL = 60 * 60 * 24 * 30;
const MAX = 6 * 1024 * 1024;            // a 1080x1350 JPEG is ~300KB; this is a guard, not a target
fs.mkdirSync(PUB, { recursive: true });
fs.mkdirSync(HIST, { recursive: true });

const app = express();
app.use(express.json({ limit: "10mb" }));

const get = (port, p) => new Promise((ok, no) => {
  http.get({ host: "127.0.0.1", port, path: p, timeout: 15000 }, r => {
    let b = ""; r.setEncoding("utf8"); r.on("data", c => b += c);
    r.on("end", () => { try { ok(JSON.parse(b)); } catch (e) { no(e); } });
  }).on("error", no).on("timeout", function () { this.destroy(new Error("timeout")); });
});

// ── the roster, live, cached for a minute ───────────────────────────────
let cache = { at: 0, data: null, refs: {} };
async function roster() {
  if (cache.data && Date.now() - cache.at < 60000) return cache;
  const [na, bo, am, ph] = await Promise.all([
    get(3011, "/state"), get(3009, "/state").catch(() => ({})), get(3007, "/state").catch(() => ({})),
    get(3011, "/photos").catch(() => ({})),
  ]);
  const people = new Map();
  for (const p of (na.state || {}).players || []) people.set(p.id, { id: p.id, name: p.name, nights: 0, uprising: 0, last: null });
  for (const st of [na.state || {}, bo.state || {}]) {
    for (const s of st.sessions || []) {
      const ids = new Set();
      for (const t of s.teams || []) { ids.add(t.p1Id); ids.add(t.p2Id); }
      for (const i of ids) {
        const r = people.get(i); if (!r) continue;
        r.nights++; if (s.date && (!r.last || s.date > r.last)) r.last = s.date;
      }
    }
  }
  const A = am.state || {};
  const guests = new Map((A.guests || []).map(g => [g.id, g.name]));
  for (const t of A.tournaments || []) for (const i of t.playerIds || []) {
    if (!people.has(i) && guests.has(i)) people.set(i, { id: i, name: guests.get(i), nights: 0, uprising: 0, last: null, walkIn: true });
    if (people.has(i)) people.get(i).uprising++;
  }
  const refs = (ph.photos) || {};
  const fold = s => (s || "").normalize("NFKD").replace(/[̀-ͯ]/g, "").toLowerCase().replace(/\b(al|el)[\s-]+/g, "al").replace(/[^a-z0-9]+/g, "") || s;
  const byName = {};
  for (const r of people.values()) (byName[fold(r.name)] = byName[fold(r.name)] || []).push(r.id);
  const data = [...people.values()].map(r => {
    const f = path.join(PUB, r.id + ".jpg");
    const has = fs.existsSync(f);
    return { ...r, now: r.uprising > 0 || (r.last || "") >= CURRENT_FROM, ref: !!refs[r.id],
      sameName: (byName[fold(r.name)] || []).length > 1,
      heist: has ? `/players/${r.id}.jpg?v=${Math.floor(fs.statSync(f).mtimeMs)}` : null };
  }).sort((a, b) => (b.now - a.now) || (b.nights + b.uprising - a.nights - a.uprising) || a.name.localeCompare(b.name));
  cache = { at: Date.now(), data, refs };
  return cache;
}

app.get("/api/roster", async (req, res) => {
  try { res.set("Cache-Control", "no-store").json({ ok: true, players: (await roster()).data }); }
  catch (e) { res.status(502).json({ ok: false, error: "roster unavailable: " + e.message }); }
});

app.get("/api/ref/:id", async (req, res) => {
  const { refs, data } = await roster();
  const url = refs[req.params.id];
  if (!url) return res.status(404).json({ ok: false, error: "no current photo" });
  const m = /^data:(image\/[a-z]+);base64,(.*)$/s.exec(url);
  if (!m) return res.status(404).end();
  const p = data.find(x => x.id === req.params.id);
  const name = (p ? p.name : req.params.id).replace(/[^\w .-]+/g, "").trim() || req.params.id;
  res.set("Content-Type", m[1]).set("Content-Disposition", `inline; filename="${name}.${m[1].split("/")[1]}"`)
    .set("Cache-Control", "no-store").send(Buffer.from(m[2], "base64"));
});

// ── the brief: one page ChatGPT can read ────────────────────────────────
// The style prompt (the SAME file the page shows) and every player still to
// do, with the link to their current photo and the exact file name to save
// the result as — a file named that way goes straight in through the page's
// batch upload. A name two players share is given as the id instead, which
// is the only file name the batch will accept for them.
const STYLE_FILE = "/var/www/heist.urbanpadel.om/public/photos/style.txt";
app.get("/api/brief", async (req, res) => {
  try {
    const { data } = await roster();
    const all = req.query.all != null;
    const todo = data.filter(p => (all || p.now) && !p.heist);
    const host = "https://heist.urbanpadel.om";
    const fname = p => (p.sameName ? p.id : p.name.replace(/[\\/:*?"<>|]+/g, "").trim()) + ".png";
    const withRef = todo.filter(p => p.ref), noRef = todo.filter(p => !p.ref);
    const style = fs.existsSync(STYLE_FILE) ? fs.readFileSync(STYLE_FILE, "utf8").trim() : "";
    const out = [
      "# MUSCAT HEIST — player portraits", "",
      "For EACH player below: open their photo link, make ONE portrait of that person following the style prompt, " +
      "and save it with the exact file name given. Do one player at a time so faces never mix. " +
      "Then upload the files at " + host + "/photos/ (Upload a batch).", "",
      "## Style prompt", "", style, "",
      `## To do — ${withRef.length} players with a photo`, "",
      ...withRef.map((p, i) => `${i + 1}. ${p.name} — photo: ${host}/api/ref/${p.id} — save as: ${fname(p)}`), "",
      `## Need a photo first — ${noRef.length} players`, "",
      "No current photo, so no likeness to work from. Ask the player for a selfie, or take one on the night.", "",
      ...noRef.map(p => `- ${p.name}`), "",
      `_${data.filter(p => p.heist).length} portraits done. ${all ? "Everyone on the roster." : "Players playing now (on a team since 1 Oct, or at an UPRISING night). Add ?all for everyone."}_`, "",
    ];
    res.set("Content-Type", "text/plain; charset=utf-8").set("Cache-Control", "no-store").send(out.join("\n"));
  } catch (e) { res.status(502).send("roster unavailable: " + e.message); }
});

// ── auth: the club's own PINs, the same token shape as every volume ─────
const hmac = d => crypto.createHmac("sha256", process.env.TOKEN_SECRET).update(d).digest("base64url");
const sign = role => { const exp = Math.floor(Date.now() / 1000) + TOKEN_TTL; return `${role}.${exp}.${hmac(role + "." + exp)}`; };
function authed(req) {
  const t = (req.get("authorization") || "").replace(/^Bearer /, "");
  const [role, exp, sig] = t.split(".");
  if (!role || !exp || !sig || +exp < Date.now() / 1000) return null;
  const want = hmac(role + "." + exp);
  if (sig.length !== want.length || !crypto.timingSafeEqual(Buffer.from(sig), Buffer.from(want))) return null;
  return ["admin", "photographer"].includes(role) ? role : null;
}
const tries = new Map();
app.post("/api/login", (req, res) => {
  const ip = req.get("x-real-ip") || req.ip;
  const n = (tries.get(ip) || []).filter(t => Date.now() - t < 10 * 60000);
  if (n.length >= 10) return res.status(429).json({ ok: false, error: "too many tries — wait ten minutes" });
  const pin = String((req.body || {}).pin || "");
  let role = null;
  if (process.env.ADMIN_PIN && pin === String(process.env.ADMIN_PIN)) role = "admin";
  else if (process.env.PHOTOGRAPHER_PIN && pin === String(process.env.PHOTOGRAPHER_PIN)) role = "photographer";
  if (!role) { n.push(Date.now()); tries.set(ip, n); return res.status(401).json({ ok: false, error: "wrong PIN" }); }
  res.json({ ok: true, role, token: sign(role) });
});

// ── upload / remove ──────────────────────────────────────────────────────
const JPEG = Buffer.from([0xff, 0xd8, 0xff]);
function jpegSize(b) {                     // width/height from the SOF marker
  let i = 2;
  while (i < b.length) {
    if (b[i] !== 0xff) return null;
    const m = b[i + 1], len = b.readUInt16BE(i + 2);
    if (m >= 0xc0 && m <= 0xcf && ![0xc4, 0xc8, 0xcc].includes(m)) return { h: b.readUInt16BE(i + 5), w: b.readUInt16BE(i + 7) };
    i += 2 + len;
  }
  return null;
}
function keep(id, why) {
  const f = path.join(PUB, id + ".jpg");
  if (fs.existsSync(f)) fs.renameSync(f, path.join(HIST, `${id}.${Date.now()}.${why}.jpg`));
}
app.post("/api/photo/:id", async (req, res) => {
  const role = authed(req);
  if (!role) return res.status(401).json({ ok: false, error: "sign in first" });
  const { data } = await roster();
  const p = data.find(x => x.id === req.params.id);
  if (!p) return res.status(404).json({ ok: false, error: "no such player" });
  const m = /^data:image\/jpeg;base64,(.+)$/s.exec((req.body || {}).image || "");
  if (!m) return res.status(400).json({ ok: false, error: "send a JPEG data URL" });
  const buf = Buffer.from(m[1], "base64");
  if (buf.length > MAX || !buf.subarray(0, 3).equals(JPEG)) return res.status(400).json({ ok: false, error: "not a JPEG, or too large" });
  const d = jpegSize(buf);
  if (!d || d.w !== 1080 || d.h !== 1350) return res.status(400).json({ ok: false, error: `must be 1080x1350, got ${d ? d.w + "x" + d.h : "unreadable"}` });
  keep(p.id, "replaced");
  const tmp = path.join(PUB, `.${p.id}.tmp`);
  fs.writeFileSync(tmp, buf); fs.renameSync(tmp, path.join(PUB, p.id + ".jpg"));
  fs.appendFileSync(LOG, `${new Date().toISOString()}\t${role}\tput\t${p.id}\t${p.name}\t${buf.length}\n`);
  cache.at = 0;
  res.json({ ok: true, url: `/players/${p.id}.jpg?v=${Date.now()}` });
});
app.delete("/api/photo/:id", (req, res) => {
  const role = authed(req);
  if (!role) return res.status(401).json({ ok: false, error: "sign in first" });
  if (!/^[\w-]+$/.test(req.params.id)) return res.status(400).end();
  keep(req.params.id, "removed");
  fs.appendFileSync(LOG, `${new Date().toISOString()}\t${role}\tdel\t${req.params.id}\n`);
  cache.at = 0;
  res.json({ ok: true });
});

app.listen(PORT, "127.0.0.1", () => console.log(`Muscat Heist API :${PORT}`));
