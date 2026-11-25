// Muscat Heist — THE LOOT (knockout cards), against the BUILT app on real brackets.
//   python3 build-heist-app.py && node ops/check-heist-loot.mjs      SHOTS=1 -> <scratch>/heist-qa/loot/
//
// National's real state with its played nights moved onto the Heist dates (the
// same "mid" scenario check-heist-app.mjs uses). The expected cards are worked
// out HERE, in Node, straight from each session's stored bracket — not by the
// module under test — and then read back off the screen:
//   - every knockout player holds exactly one card per night, of the right tier
//     (best round reached; the final's winners hold The Score)
//   - a player who never reached a knockout holds none, and the album still
//     draws all nine slots
//   - serials: "one of N" is the losers of that round x2 (2 for The Score)
//   - no text inside a card is cut or leaves it, at album and full size
//   - an uploaded champion artwork (/api/loot) replaces that SCORE card's picture
//   - the share sheet exports the card at exactly 1080x1920
//   - the loot moment: the phone's owner, champion of the last night, sees
//     "New knockout card"
// SABOTAGE=tier  (the build is patched to deal everybody The Job) must go red.
import { chromium } from 'playwright';
import fs from 'fs';
import http from 'http';
import path from 'path';

const ROOT = path.resolve(path.dirname(new URL(import.meta.url).pathname), '..');
const SC = '/tmp/claude-0/-home-user-May-madness/0e44f0ad-a683-5f0d-9de6-9459ae328963/scratchpad';
const SEASON = JSON.parse(fs.readFileSync(path.join(ROOT, 'heist-season.json'), 'utf8'));
const NAT = JSON.parse(fs.readFileSync(path.join(SC, 'roster', 'state-3011.json'), 'utf8')).state;
const PHOTOS = fs.readFileSync(path.join(SC, 'roster', 'photos-3011.json'), 'utf8');
const BID = fs.readFileSync(path.join(ROOT, 'heist-index.html.version'), 'utf8').trim();
const OUT = path.join(SC, 'heist-qa', process.env.SABOTAGE ? 'loot-sabotage' : 'loot'); fs.mkdirSync(OUT, { recursive: true });
let HTML = fs.readFileSync(path.join(ROOT, 'heist-index.html'), 'utf8');
if (process.env.SABOTAGE === 'tier') {
  const a = 'if (F && F.winner) deal(F.winner === "a" ? F.ta : F.tb, "score", { m: F });';
  if (!HTML.includes(a)) throw new Error('sabotage anchor missing');
  HTML = HTML.replace(a, '').replace('const rounds = [["job", K.qf || []], ["inside", K.sf || []], ["getaway", K.final ? [K.final] : []]];',
    'const rounds = [["job", [...(K.qf || []), ...(K.sf || []), ...(K.final ? [K.final] : [])]]];');
}

const st = JSON.parse(JSON.stringify(NAT));
st.sessions.forEach((s, i) => { s.date = SEASON.nights[i]; s.doublePoints = SEASON.doubleNights.includes(s.date); });
const n7 = st.sessions[6];
if (n7) { n7.completed = false; n7.bracket = {}; }
const byId = Object.fromEntries(st.players.map(p => [p.id, p]));
const NAMES = { job: 'the job', inside: 'inside man', getaway: 'getaway', score: 'the score' };
const RANK = ['job', 'inside', 'getaway', 'score'];

// ── expected, from the stored brackets ──
const want = {};               // pid -> { no: tier }
const serialOf = {};           // `${no}/${tier}` -> N
st.sessions.forEach((s, i) => {
  const no = SEASON.nights.indexOf(s.date) + 1, B = s.bracket || {};
  if (!no) return;
  const team = id => (s.teams || []).find(t => t.id === id);
  const put = (tid, tier) => { const t = team(tid); if (!t) return;
    [t.p1Id, t.p2Id].forEach(p => { want[p] = want[p] || {}; if (!want[p][no] || RANK.indexOf(tier) > RANK.indexOf(want[p][no])) want[p][no] = tier; }); };
  [['job', B.qf || []], ['inside', B.sf || []], ['getaway', B.final ? [B.final] : []]].forEach(([tier, ms]) => {
    const real = ms.filter(m => m && m.team1Id && m.team2Id);
    if (real.length && real.every(m => m.winner)) serialOf[`${no}/${tier}`] = real.length * 2;
    ms.forEach(m => { if (!m) return; put(m.team1Id, tier); put(m.team2Id, tier); });
  });
  if (B.final && B.final.winner) { put(B.final.winner === 'team1' ? B.final.team1Id : B.final.team2Id, 'score'); serialOf[`${no}/score`] = 2; }
});
const champOf = no => Object.keys(want).find(p => want[p][no] === 'score');
const lastDone = Math.max(...st.sessions.filter(s => s.completed).map(s => SEASON.nights.indexOf(s.date) + 1));
const ME = champOf(lastDone);
const someTier = t => { for (const p of Object.keys(want)) for (const n of Object.keys(want[p])) if (want[p][n] === t) return [p, +n]; return null; };
const nobody = st.players.find(p => !want[p.id] && st.sessions.some(s => (s.teams || []).some(t => t.p1Id === p.id || t.p2Id === p.id)));

// ── a server: the app, the state, the champion art ──
const ART = path.join(ROOT, 'brand/heist/art', SEASON.episodes[0].art);
const T = { '.html': 'text/html; charset=utf-8', '.css': 'text/css', '.woff2': 'font/woff2', '.png': 'image/png', '.webp': 'image/webp', '.jpg': 'image/jpeg', '.json': 'application/json' };
const map = [['/assets/fonts/brand/', 'brand/fonts/'], ['/assets/fonts/heist/', 'brand/heist/fonts/'], ['/assets/art/', 'brand/heist/art/'],
  ['/assets/up-logo-tight.png', 'brand/heist/up-logo-tight.png'], ['/assets/heist-logo.png', 'brand/heist/heist-logo.png'],
  ['/assets/heist-logo.webp', 'brand/heist/heist-logo.webp'], ['/assets/history.json', 'brand/national/history.json']];
const CUSTOM = champOf(1);
const srv = http.createServer((q, r) => {
  const u = decodeURIComponent(q.url.split('?')[0]);
  const json = o => { r.writeHead(200, { 'Content-Type': 'application/json' }); r.end(typeof o === 'string' ? o : JSON.stringify(o)); };
  if (u === '/' || u === '/index.html') { r.writeHead(200, { 'Content-Type': T['.html'] }); return r.end(HTML); }
  if (u === '/version.txt') { r.writeHead(200); return r.end(BID + '\n'); }
  if (u === '/state') return json({ ok: true, state: st, version: 1 });
  if (u === '/photos') return json(PHOTOS);
  if (u === '/session-photos') return json({ ok: true, photos: {} });
  if (u === '/api/roster') return json({ ok: true, players: [] });
  if (u === '/api/loot') return json({ ok: true, art: { [`1/${CUSTOM}`]: `/loot/ep01-${CUSTOM}.jpg?v=1` } });
  if (u.startsWith('/loot/')) { r.writeHead(200, { 'Content-Type': 'image/jpeg' }); return r.end(fs.readFileSync(ART)); }
  for (const [a, b] of map) if (u.startsWith(a)) {
    const f = path.join(ROOT, b + u.slice(a.length));
    if (fs.existsSync(f) && !fs.statSync(f).isDirectory()) { r.writeHead(200, { 'Content-Type': T[path.extname(f)] || 'x' }); return r.end(fs.readFileSync(f)); }
  }
  r.writeHead(404); r.end();
}).listen(0);
const ORIGIN = `http://127.0.0.1:${srv.address().port}`;
const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
const fails = []; const ok = (c, m) => { if (!c) { fails.push(m); console.log('  FAIL ' + m); } else if (process.env.V) console.log('  ok   ' + m); };

const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 2, acceptDownloads: true });
await ctx.addInitScript(me => { try { localStorage.setItem('mh-once-loaded', 'never'); localStorage.setItem('aa-me', me); } catch (e) {}
  Object.defineProperty(navigator, 'canShare', { value: () => false }); }, ME);
const pg = await ctx.newPage();
const errs = []; pg.on('pageerror', e => errs.push(e.message));
await pg.route('**/unpkg.com/**', r => {
  const u = r.request().url();
  const f = /html-to-image/.test(u) ? 'h2i.js' : /babel/.test(u) ? 'babel.js' : /react-dom/.test(u) ? 'react-dom.js' : 'react.js';
  r.fulfill({ status: 200, contentType: 'application/javascript', body: fs.readFileSync(path.join(SC, 'vendor', f), 'utf8') });
});
await pg.route('**/cdn.tailwindcss.com/**', r => r.fulfill({ status: 200, contentType: 'application/javascript', body: '' }));
await pg.route('**/fonts.googleapis.com/**', r => r.fulfill({ status: 200, contentType: 'text/css', body: '' }));
await pg.route('**/api.savemyplay.com/**', r => r.fulfill({ status: 200, contentType: 'application/json', headers: { 'access-control-allow-origin': '*' }, body: '{"clips":[]}' }));
await pg.goto(ORIGIN + '/#home', { waitUntil: 'load' });
await pg.waitForSelector('.mh-page, .mh-loading', { timeout: 40000 });
await pg.evaluate(() => Promise.all(["40px 'Bowlby One'", "40px 'Kaushan Script'", "700 12px 'JetBrains Mono'"].map(f => document.fonts.load(f).catch(() => 0))));
const go = async h => { await pg.evaluate(x => { location.hash = x; }, h); await pg.waitForTimeout(700); };
const shot = async n => { if (process.env.SHOTS) await pg.screenshot({ path: path.join(OUT, n + '.png'), fullPage: true }); };
// text cut by its box or leaving its card
const cut = () => pg.evaluate(() => {
  const bad = [];
  for (const card of document.querySelectorAll('.mh-loot')) {
    const cb = card.getBoundingClientRect();
    for (const el of card.querySelectorAll('.mh-loot-tier span, .mh-loot-name span, .mh-loot-with, .mh-loot-meta span, .mh-loot-code, .mh-loot-2x, .mh-loot-lock')) {
      if (!el.offsetWidth) continue;
      const b = el.getBoundingClientRect();
      // to the fraction: scrollWidth rounds, and a 0.4px overrun still draws the ellipsis
      // and with the ellipsis off, or the range measures the trimmed run
      const box = b.width, sv = [el.style.display, el.style.textOverflow];
      el.style.display = 'inline-block'; el.style.textOverflow = 'clip';
      const rg = document.createRange(); rg.selectNodeContents(el); const tw = rg.getBoundingClientRect().width;
      el.style.display = sv[0]; el.style.textOverflow = sv[1];
      if (getComputedStyle(el).overflow !== 'visible' && tw > box + .05) bad.push(`cut "${el.textContent}" ${tw.toFixed(2)}>${box.toFixed(2)}`);
      if (b.left < cb.left - .5 || b.right > cb.right + .5 || b.top < cb.top - .5 || b.bottom > cb.bottom + .5) bad.push(`off card "${el.textContent}"`);
      if (parseFloat(getComputedStyle(el).fontSize) < 10.95) bad.push(`under 11px "${el.textContent}" ${getComputedStyle(el).fontSize}`);
    }
  }
  return bad;
});

// 1 — every album agrees with the brackets
const people = [...new Set([ME, ...SEASON.nights.map((_, i) => champOf(i + 1)).filter(Boolean), ...['job', 'inside', 'getaway'].map(t => (someTier(t) || [])[0]).filter(Boolean)])];
for (const pid of people) {
  await go('card/' + pid);
  const got = await pg.$$eval('.mh-album-grid .mh-lootbtn', e => e.map(x => x.getAttribute('aria-label')));
  const slots = await pg.$$eval('.mh-album-grid > *', e => e.length);
  const exp = Object.entries(want[pid] || {}).map(([no, t]) => `${SEASON.episodes[no - 1].code} ${NAMES[t]}`);
  const gotKeys = got.map(l => l.split(',')[0].toLowerCase()).sort(), expKeys = exp.map(x => x.toLowerCase()).sort();
  ok(JSON.stringify(gotKeys) === JSON.stringify(expKeys), `${byId[pid].name}: album ${gotKeys.join(' | ')} — brackets say ${expKeys.join(' | ')}`);
  ok(slots === SEASON.nights.length, `${byId[pid].name}: album has ${slots} slots, not ${SEASON.nights.length}`);
  const c = await cut(); ok(!c.length, `${byId[pid].name} album: ${c.slice(0, 3).join(', ')}`);
}
if (nobody) {
  await go('card/' + nobody.id);
  const n = await pg.$$eval('.mh-album-grid .mh-lootbtn', e => e.length);
  ok(n === 0 && !want[nobody.id], `${nobody.name} never reached a knockout and holds ${n} cards`);
}
await go('me'); await shot('me-album');
ok(await pg.locator('.mh-album').count() === 1, 'ME has no album');

// 2 — each tier's big card: serial and fit
for (const t of RANK) {
  const hit = t === 'score' ? [ME, lastDone] : someTier(t);
  if (!hit) { console.log(`  (no ${t} card in this data)`); continue; }
  const [pid, no] = hit;
  await go(`loot/${pid}.${no}`);
  const txt = await pg.evaluate(() => document.querySelector('.mh-body').innerText);
  const N = serialOf[`${no}/${t}`];
  ok(new RegExp(`one of ${N} ${NAMES[t]} cards`, 'i').test(txt), `${t}: "${(txt.match(/one of.*cards[^\n]*/i) || ['no serial line'])[0]}" — want one of ${N}`);
  ok(await pg.locator(`.mh-loot-stage .mh-loot[data-tier="${t}"]`).count() === 1, `${t}: the big card is not drawn in its tier`);
  const c = await cut(); ok(!c.length, `${t} card: ${c.slice(0, 3).join(', ')}`);
  if (t === 'score') ok(/new knockout card/i.test(txt), 'the phone\'s owner, champion of the last night, is not shown "New knockout card"');
  await pg.evaluate(() => scrollTo(0, 0)); await pg.waitForTimeout(150);
  if (process.env.SHOTS) await pg.screenshot({ path: path.join(OUT, `card-${t}.png`) });
}

// 3 — the owner's champion art replaces the picture
await go(`loot/${CUSTOM}.1`);
const src = await pg.evaluate(() => { const i = document.querySelector('.mh-loot-stage .mh-loot-custom img'); return i && i.getAttribute('src'); });
ok(src && src.includes('/loot/ep01-'), `uploaded champion art not used on ${byId[CUSTOM].name}'s night-1 card (${src})`);
await shot('card-custom');

// 4 — the story export
await go(`share/loot/${ME}.${lastDone}`);
ok(await pg.locator('.mh-sharescale .mh-loot').count() === 1, 'share sheet does not show the knockout card');
await pg.waitForTimeout(500);
const dl = pg.waitForEvent('download', { timeout: 30000 }).catch(() => null);
await pg.locator('.mh-momentfoot button').click();
await dl;
const dims = await pg.waitForFunction(() => window.__mhLastExport, null, { timeout: 30000 }).then(() => pg.evaluate(async () => {
  const b = await createImageBitmap(window.__mhLastExport); return [b.width, b.height, window.__mhLastExport.size]; })).catch(() => null);
ok(dims && dims[0] === 1080 && dims[1] === 1920, `story export is ${dims ? dims[0] + 'x' + dims[1] : 'nothing'}`);
if (dims) {
  const b64 = await pg.evaluate(async () => { const r = new FileReader(); return await new Promise(ok => { r.onload = () => ok(r.result.split(',')[1]); r.readAsDataURL(window.__mhLastExport); }); });
  fs.writeFileSync(path.join(OUT, 'story-loot.png'), Buffer.from(b64, 'base64'));
}
ok(!errs.length, 'page errors: ' + errs.slice(0, 2).join(' | '));
console.log(`  phone: ${byId[ME].name} (champion of night ${lastDone}) · ${people.length} albums checked · export ${dims ? dims.join('x') : '-'}`);
await browser.close(); srv.close();
console.log(fails.length ? `FAIL ${fails.length}` : 'ok — the loot');
process.exit(fails.length ? 1 : 0);
