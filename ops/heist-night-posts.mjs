// The morning after a Muscat Heist night: the night's posts, made from the
// live state by the app's OWN share screens, so a post cannot disagree with
// what the app shows.
//
//   node ops/heist-night-posts.mjs            # the latest completed night (fetched over ssh)
//   node ops/heist-night-posts.mjs 3          # a given night
//   STATE=<file> PHOTOS=<file> node ops/heist-night-posts.mjs 6   # offline, any state file
//
// Out: brand/heist/nights/epNN/ — champions, tonight's points, tables, bracket
// (1080x1920, exported through the in-app "Share image" button, exactly the
// file a player would get), each champion's knockout card, and CAPTION.txt
// (the WhatsApp/Instagram text: champions and final score, the table's top
// five after the night, the next night). It REFUSES a night that is not
// completed: a results post for a night still being played is worse than none.
import { chromium } from 'playwright';
import { execFileSync } from 'child_process';
import fs from 'fs';
import http from 'http';
import path from 'path';

const ROOT = path.resolve(path.dirname(new URL(import.meta.url).pathname), '..');
const SC = process.env.SCRATCH || '/tmp/claude-0/-home-user-May-madness/0e44f0ad-a683-5f0d-9de6-9459ae328963/scratchpad';
const S = JSON.parse(fs.readFileSync(path.join(ROOT, 'heist-season.json'), 'utf8'));
const remote = p => execFileSync('ssh', ['urbanpadel', `curl -s localhost:${p}`], { encoding: 'utf8', maxBuffer: 1 << 28, stdio: ['ignore', 'pipe', 'ignore'] });
const stateJ = process.env.STATE ? JSON.parse(fs.readFileSync(process.env.STATE, 'utf8')) : JSON.parse(remote('3013/state'));
const st = stateJ.state || stateJ;
const photos = process.env.PHOTOS ? fs.readFileSync(process.env.PHOTOS, 'utf8') : (process.env.STATE ? '{"ok":true,"photos":{}}' : remote('3013/photos'));
const roster = process.env.STATE ? '{"ok":true,"players":[]}' : remote('3012/api/roster');
const lootArt = process.env.STATE ? '{"ok":true,"art":{}}' : remote('3012/api/loot');

const done = st.sessions.filter(s => s.completed).map(s => S.nights.indexOf(s.date) + 1).filter(n => n > 0);
const no = +process.argv[2] || Math.max(0, ...done);
if (!no || !done.includes(no)) { console.error(`night ${no || '-'} is not completed (completed: ${done.join(', ') || 'none'}) — no posts`); process.exit(1); }
const ep = S.episodes[no - 1];
const OUT = path.join(ROOT, 'brand/heist/nights', `ep${String(no).padStart(2, '0')}`);
fs.mkdirSync(OUT, { recursive: true });

const html = fs.readFileSync(path.join(ROOT, 'heist-index.html'), 'utf8');
const BID = fs.readFileSync(path.join(ROOT, 'heist-index.html.version'), 'utf8').trim();
const T = { '.css': 'text/css', '.woff2': 'font/woff2', '.png': 'image/png', '.webp': 'image/webp', '.jpg': 'image/jpeg', '.json': 'application/json' };
const map = [['/assets/fonts/brand/', 'brand/fonts/'], ['/assets/fonts/heist/', 'brand/heist/fonts/'], ['/assets/art/', 'brand/heist/art/'], ['/assets/history.json', 'brand/national/history.json'], ['/assets/', 'brand/heist/']];
const json = (r, b) => { r.writeHead(200, { 'Content-Type': 'application/json' }); r.end(b); };
const imgCache = {};
const srv = http.createServer((q, r) => {
  const u = decodeURIComponent(q.url.split('?')[0]);
  if (u === '/' || u === '/index.html') { r.writeHead(200, { 'Content-Type': 'text/html' }); return r.end(html); }
  if (u === '/version.txt') { r.writeHead(200); return r.end(BID); }
  if (u === '/state') return json(r, JSON.stringify({ ok: true, state: st, version: 1 }));
  if (u === '/photos') return json(r, photos);
  if (u === '/session-photos') return json(r, '{"ok":true,"photos":{}}');
  if (u === '/api/roster') return json(r, roster);
  if (u === '/api/loot') return json(r, lootArt);
  if (u.startsWith('/players/') || u.startsWith('/loot/')) {          // portraits and champion art live on the server
    try { imgCache[u] = imgCache[u] || execFileSync('ssh', ['urbanpadel', `cat /var/www/heist.urbanpadel.om/public${u}`], { maxBuffer: 1 << 26, stdio: ['ignore', 'pipe', 'ignore'] });
      r.writeHead(200, { 'Content-Type': 'image/jpeg' }); return r.end(imgCache[u]); } catch (e) { r.writeHead(404); return r.end(); }
  }
  for (const [a, b] of map) if (u.startsWith(a)) {
    const f = path.join(ROOT, b + u.slice(a.length));
    if (fs.existsSync(f) && fs.statSync(f).isFile()) { r.writeHead(200, { 'Content-Type': T[path.extname(f)] || 'application/octet-stream' }); return r.end(fs.readFileSync(f)); }
  }
  r.writeHead(404); r.end();
}).listen(0);
const ORIGIN = `http://127.0.0.1:${srv.address().port}`;
const vendor = f => fs.readFileSync(path.join(SC, 'vendor', f), 'utf8');
const b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
const ctx = await b.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 2 });
await ctx.addInitScript(() => { try { localStorage.setItem('mh-once-loaded', 'never'); } catch (e) {}
  Object.defineProperty(navigator, 'canShare', { value: () => false }); });
const pg = await ctx.newPage();
const errs = []; pg.on('pageerror', e => errs.push(e.message));
await pg.route('**/unpkg.com/**', r => { const u = r.request().url();
  r.fulfill({ status: 200, contentType: 'application/javascript', body: vendor(/html-to-image/.test(u) ? 'h2i.js' : /react-dom/.test(u) ? 'react-dom.js' : 'react.js') }); });
await pg.route('**/cdn.tailwindcss.com/**', r => r.fulfill({ status: 200, contentType: 'application/javascript', body: vendor('tailwind.js') }));
await pg.route('**/fonts.googleapis.com/**', r => r.fulfill({ status: 200, contentType: 'text/css', body: '' }));
await pg.route('**/api.savemyplay.com/**', r => r.fulfill({ status: 200, contentType: 'application/json', headers: { 'access-control-allow-origin': '*' }, body: '{"clips":[]}' }));
await pg.goto(`${ORIGIN}/#nightshare/${no}/champions`);
await pg.waitForSelector('.mh-page', { timeout: 60000 });
await pg.evaluate(() => Promise.all(["40px 'Bowlby One'", "40px 'Kaushan Script'", "800 40px Archivo"].map(f => document.fonts.load(f).catch(() => 0))));

async function exportAt(hash, file) {
  await pg.evaluate(h => { window.__mhLastExport = null; location.hash = h; }, hash);
  await pg.waitForTimeout(1500);
  const btn = pg.locator('button', { hasText: /Share image/ });
  if (!(await btn.count())) return null;
  await btn.first().click();
  const b64 = await pg.evaluate(async () => { for (let i = 0; i < 80 && !window.__mhLastExport; i++) await new Promise(r => setTimeout(r, 250));
    const x = window.__mhLastExport; if (!x) return null; const fr = new FileReader();
    return await new Promise(ok => { fr.onload = () => ok(fr.result.split(',')[1]); fr.readAsDataURL(x); }); });
  if (!b64) return null;
  fs.writeFileSync(path.join(OUT, file), Buffer.from(b64, 'base64'));
  return file;
}
const made = [];
for (const k of ['champions', 'points', 'tables', 'bracket']) { const f = await exportAt(`nightshare/${no}/${k}`, `${k}.png`); if (f) made.push(f); }

// the engine is the inherited calcPlayerStats; run it over the state for the table after this night
const table = await pg.evaluate(({ st, upTo }) => {
  const ses = st.sessions.filter(s => s.completed && s.date <= upTo);
  return st.players.map(p => ({ id: p.id, name: p.name, pts: calcPlayerStats(p.id, ses).totalPts }))
    .filter(r => r.pts > 0).sort((a, b) => b.pts - a.pts).slice(0, 5);
}, { st, upTo: S.nights[no - 1] });
const sess = st.sessions.find(s => s.date === S.nights[no - 1]);
const F = (sess.bracket || {}).final, byId = Object.fromEntries(st.players.map(p => [p.id, p.name]));
const team = id => (sess.teams || []).find(t => t.id === id) || {};
const winT = F && F.winner ? team(F.winner === 'team1' ? F.team1Id : F.team2Id) : null;
const loseT = F && F.winner ? team(F.winner === 'team1' ? F.team2Id : F.team1Id) : null;
const score = F && F.score ? (F.winner === 'team1' ? `${F.score.t1}-${F.score.t2}` : `${F.score.t2}-${F.score.t1}`) : '';
const pair = t => t ? [t.p1Id, t.p2Id].map(i => byId[i] || '?').join(' & ') : '?';
for (const pid of winT ? [winT.p1Id, winT.p2Id] : []) {
  const f = await exportAt(`share/loot/${pid}.${no}`, `score-card-${(byId[pid] || pid).replace(/[^A-Za-z0-9]+/g, '-')}.png`);
  if (f) made.push(f);
}
const next = S.nights[no] ? `${S.episodes[no].code} · ${S.episodes[no].title}, ${new Date(S.nights[no] + 'T12:00:00').toLocaleDateString('en-GB', { weekday: 'short', day: 'numeric', month: 'short' })}${S.doubleNights.includes(S.nights[no]) ? ' (double points)' : ''}` : null;
const cap = [
  `*${S.name.toUpperCase()} · ${ep.code} · ${ep.title}*`,
  '',
  winT ? `🏆 Champions: *${pair(winT)}*${score ? `, ${score} in the final` : ''} against ${pair(loseT)}` : '',
  winT ? `A ${S.voucher} OMR voucher each.` : '',
  '',
  `*The table after ${ep.code}*`,
  ...table.map((r, i) => `${i + 1}. ${r.name} · ${r.pts}`),
  '',
  next ? `Next: ${next}` : 'That was the last night. The season is decided.',
  `Cards, table and your rank: https://${S.host}`,
].filter((l, i, a) => !(l === '' && a[i - 1] === '')).join('\n');
fs.writeFileSync(path.join(OUT, 'CAPTION.txt'), cap + '\n');
await b.close(); srv.close();
console.log(`${ep.code} ${ep.title}: ${made.length} images + CAPTION.txt in ${path.relative(ROOT, OUT)}`);
made.forEach(f => console.log('  ' + f));
if (errs.length) { console.error('page errors:', errs.slice(0, 3)); process.exit(1); }
if (made.length < 4) { console.error('fewer than the four night posts were made'); process.exit(1); }
