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
const NAME = process.argv[3] || 'motion';
const OUT = path.join(SC, 'motion-video');
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

const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 2,
  recordVideo: { dir: OUT, size: { width: 390, height: 844 } } });
const pg = await ctx.newPage();
await pg.route('**/unpkg.com/**', r => {
  const url = r.request().url();
  const f = /babel/.test(url) ? 'babel.js' : /react-dom/.test(url) ? 'react-dom.js' : 'react.js';
  r.fulfill({ status: 200, contentType: 'application/javascript', body: fs.readFileSync(path.join(VENDOR, f), 'utf8') });
});
await pg.route('**/fonts.googleapis.com/**', r => r.fulfill({ status: 200, contentType: 'text/css', body: FONTCSS }));
await pg.route('**/api.savemyplay.com/**', r => r.fulfill({ status: 200, contentType: 'application/json',
  headers: { 'access-control-allow-origin': '*' }, body: fs.readFileSync(path.join(SC, 'smp/clips.json')) }));
await pg.route('**/smpw.b-cdn.net/**', r => {
  const f = path.join(SC, 'smp/cdn', path.basename(new URL(r.request().url()).pathname));
  return fs.existsSync(f) ? r.fulfill({ status: 200, contentType: 'image/jpeg', body: fs.readFileSync(f) }) : r.fulfill({ status: 404 });
});

// The page needs a moment to boot (Babel compiles the app in the browser);
// that stretch is trimmed off the front of the video afterwards.
const t0 = Date.now();
await pg.goto(`http://127.0.0.1:${PORT}/`, { waitUntil: 'load' });
await pg.waitForSelector('nav.fixed.bottom-0', { timeout: 30000 });
await pg.evaluate(() => document.fonts.ready);
await pg.keyboard.press('Escape').catch(() => {});
const boot = (Date.now() - t0) / 1000;

const tab = async l => {
  await pg.evaluate(l => [...document.querySelectorAll('nav.fixed.bottom-0 button')]
    .find(x => (x.innerText || '').trim().toLowerCase().startsWith(l))?.click(), l);
};
await pg.waitForTimeout(4000);               // home: watch the ground
await tab('sessions'); await pg.waitForTimeout(2600);
await tab('rank');     await pg.waitForTimeout(1800);
await tab('players');  await pg.waitForTimeout(1500);
await tab('sessions'); await pg.waitForTimeout(1200);
await pg.evaluate(() => document.querySelector('.jh-mock-sess')?.click());
await pg.waitForTimeout(1000);
await pg.evaluate(() => [...document.querySelectorAll('button')].find(x => /FULL RESULTS/i.test(x.textContent || ''))?.click());
await pg.waitForTimeout(3000);               // the night: champions plate
const vid = await pg.video().path();
await ctx.close(); await browser.close(); srv.close();

const mp4 = path.join(OUT, NAME + '.mp4');
execFileSync('/usr/bin/ffmpeg', ['-y', '-loglevel', 'error', '-ss', String(boot + 0.3), '-i', vid,
  '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '20', '-movflags', '+faststart', mp4]);
fs.rmSync(vid);
console.log(`${mp4}  (boot ${boot.toFixed(1)}s trimmed)`);
