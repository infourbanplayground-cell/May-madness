// (server set-up shared with record-motion.mjs)
// RECORD HOW THE APP MOVES — a screenshot cannot show motion, and motion is
// what is being reviewed. Drives the real app through a fixed script on a
// phone-sized page and saves a video, so a before and an after can be watched
// side by side.
//
//   node ops/record-motion.mjs [app.html] [out-name]      default national-index.html
//
// The script: home for four seconds (the ground — does it drift?), SESSIONS
// (does the table arrive, do moved rows move?), RANK, PLAYERS, then into the
// first night's full results (does the champions plate open?).
// localStorage starts EMPTY, so every once-only moment is seen fresh.
import { chromium } from 'playwright';
import fs from 'fs';
import http from 'http';
import path from 'path';
import { execFileSync } from 'child_process';

const SC = '/tmp/claude-0/-home-user-May-madness/0e44f0ad-a683-5f0d-9de6-9459ae328963/scratchpad';
const APP = process.argv[2] || 'national-index.html';
const OUT = path.join(SC, 'player-shots');
fs.mkdirSync(OUT, { recursive: true });
const VENDOR = SC + '/vendor';
const app = fs.readFileSync(APP, 'utf8');
const VERSION = (/BUILD_ID\s*=\s*"([0-9a-f]+)"/.exec(app) || [])[1]
  || (fs.existsSync(APP + '.version') ? fs.readFileSync(APP + '.version', 'utf8').trim() : 'dev');
const FONTCSS = fs.readFileSync('brand/fonts/fonts.css', 'utf8')
  .replace(/url\(([^)]+)\)/g, (m, u) => `url(/fonts/${path.basename(u.replace(/['"]/g, ''))})`);
const state = fs.readFileSync(SC + (fs.existsSync(SC + '/na-live.json') ? '/na-live.json' : '/na.json'), 'utf8');

const PORT = 8139;
const srv = http.createServer({ maxHeaderSize: 1 << 20 }, (req, res) => {
  const u = (req.url || '/').split('?')[0];
  const json = b => { res.writeHead(200, { 'Content-Type': 'application/json' }); res.end(b); };
  if (u === '/version.txt') { res.writeHead(200, { 'Content-Type': 'text/plain' }); return res.end(VERSION); }
  if (u === '/state') return json(state);
  if (u === '/photos') return json('{"ok":true,"photos":{}}');
  if (u === '/session-photos') return json('{"ok":true,"photos":{}}');
  if (u.startsWith('/fonts/')) {
    const f = path.join('brand/fonts', path.basename(u));
    if (fs.existsSync(f)) { res.writeHead(200, { 'Content-Type': 'font/woff2' }); return res.end(fs.readFileSync(f)); }
  }
  const b = path.basename(u);
  for (const d of ['brand/national', 'assets']) {
    const f = path.join(d, b);
    if (/\.(png|webp|jpe?g|svg|json)$/.test(b) && fs.existsSync(f)) {
      res.writeHead(200, { 'Content-Type': b.endsWith('.json') ? 'application/json' : 'image/' + b.split('.').pop() }); return res.end(fs.readFileSync(f));
    }
  }
  res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' }); res.end(app);
}).listen(PORT);


// LOOK AT A PLAYER CARD AND THE HEAD TO HEAD SHEET.
//   node ops/shots-player.mjs [app] "Muatasim Sabri" "Muntaser Hasni"
const A = process.argv[3] || 'Muatasim Sabri', B = process.argv[4] || 'Muntaser Hasni';
const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
const pg = await browser.newPage({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 2 });
const errs = []; pg.on('pageerror', e => errs.push(e.message));
await pg.route('**/unpkg.com/**', r => {
  const url = r.request().url();
  const f = /babel/.test(url) ? 'babel.js' : /react-dom/.test(url) ? 'react-dom.js' : 'react.js';
  r.fulfill({ status: 200, contentType: 'application/javascript', body: fs.readFileSync(path.join(VENDOR, f), 'utf8') });
});
await pg.route('**/fonts.googleapis.com/**', r => r.fulfill({ status: 200, contentType: 'text/css', body: FONTCSS }));
await pg.goto(`http://127.0.0.1:${PORT}/`, { waitUntil: 'load' });
await pg.waitForSelector('nav.fixed.bottom-0', { timeout: 30000 });
await pg.evaluate(() => document.fonts.ready);
await pg.keyboard.press('Escape').catch(() => {});
const tab = l => pg.evaluate(l => [...document.querySelectorAll('nav.fixed.bottom-0 button')]
  .find(x => (x.innerText || '').trim().toLowerCase().startsWith(l))?.click(), l);
const shot = async (n, full) => { await pg.waitForTimeout(700); await pg.screenshot({ path: path.join(OUT, n + '.png'), fullPage: !!full }); console.log('  ' + n); };

await tab('players'); await pg.waitForTimeout(800);
if (errs.length) console.log('  ERR after players: ' + errs.join(' | ').slice(0, 600));
await shot('players');
// the player card: search, open the first tile
await pg.fill('input[placeholder^="Find a player"]', A);
await pg.waitForTimeout(500);
await pg.evaluate(name => {
  const t = [...document.querySelectorAll('main button, main [role=button], main div')]
    .find(x => x.onclick !== undefined && (x.innerText || '').trim().startsWith(name.split(' ')[0]) && x.querySelector('img,svg,div'));
  (t || [...document.querySelectorAll('main *')].find(x => (x.innerText || '').trim() === name))?.click();
}, A);
await pg.waitForTimeout(1200);
// the plate sits low on the card: bring it into view
const at = await pg.evaluate(() => { const e = document.querySelector('.na-alltime'); if (!e) return false; e.scrollIntoView({ block: 'center' }); return true; });
console.log('  all-time plate ' + (at ? 'found' : 'MISSING'));
await shot('card-alltime');
// head to head from the card, second player picked through the picker
await pg.evaluate(() => document.querySelector('.na-vsbtn')?.click());
await pg.waitForTimeout(800);
const pick = async (which, name) => {
  await pg.evaluate(w => [...document.querySelectorAll('.na-vs .relative > button')][w]?.click(), which);
  await pg.waitForTimeout(300);
  await pg.fill('.na-vs input', name.split(' ')[0]);
  await pg.waitForTimeout(300);
  await pg.evaluate(n => [...document.querySelectorAll('.na-vs .absolute button')].find(x => x.textContent.trim() === n)?.click(), name);
};
await pick(1, B);
await shot('vs-top');
await pg.evaluate(() => { const l = document.querySelector('.na-meet'); if (l) l.scrollIntoView({ block: 'start' }); });
await shot('vs-meetings');
if (errs.length) console.log('  page errors: ' + errs.slice(0, 3).join(' | '));
await browser.close(); srv.close();
