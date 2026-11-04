// LOOK AT THE NIGHT. The review tool for the session screens.
//
// `ops/shots-national.mjs` shoots the five tabs, which is everything a player
// sees and none of what the organiser does. The night lives behind two more
// taps — SESSIONS, a row, FULL RESULTS — in a `fixed inset-0` pane with its
// own sub-screens, and it is the screen somebody holds for three hours.
//
//   node ops/shots-session.mjs
//   APP=<file>   which build       ROLE=admin   the organiser's view
//   VP=390x844   one viewport      FULL=1       whole-page shots
//
// It writes a contact sheet beside the shots, for the same reason the other
// one does: a screen is judged against its siblings.
import { chromium } from 'playwright';
import fs from 'fs';
import http from 'http';
import path from 'path';

const SC = '/tmp/claude-0/-home-user-May-madness/0e44f0ad-a683-5f0d-9de6-9459ae328963/scratchpad';
const APP = process.env.APP || 'national-index.html';
const OUT = process.env.OUT || (SC + '/vol9-session');
const FULL = !!process.env.FULL;
const ROLE = process.env.ROLE || '';
fs.rmSync(OUT, { recursive: true, force: true });
fs.mkdirSync(OUT, { recursive: true });

const PORT = 8147;
const ORIGIN = `http://127.0.0.1:${PORT}`;
const VENDOR = SC + '/vendor';
const app = fs.readFileSync(APP, 'utf8');
const FONTCSS = fs.readFileSync('brand/fonts/fonts.css', 'utf8')
  .replace(/url\(([^)]+)\)/g, (m, u) => `url(/fonts/${path.basename(u.replace(/['"]/g, ''))})`);
const VERSION = fs.existsSync(APP + '.version')
  ? fs.readFileSync(APP + '.version', 'utf8').trim() : 'dev';
let state = fs.readFileSync(SC + '/na-live.json', 'utf8');
const photos = fs.existsSync(SC + '/na-photos.json')
  ? fs.readFileSync(SC + '/na-photos.json', 'utf8') : '{"ok":true,"photos":{}}';

// MID=1 — A NIGHT IN PLAY, which the live state cannot give. Session 1 is
// finished, so ON COURT, NEXT, the half-full progress bar and the "not drawn
// yet" line all render ZERO TIMES against it and every look at the screen
// passes having seen none of them. That is the same hole the medallion check
// records: a screen with no data on it is not a screen that has been checked.
// It rewinds the real night rather than inventing one — the last six group
// results are unlocked, one of them is left part-scored the way the scorer's
// pad leaves it, and the knockout is taken off the board.
if (process.env.MID) {
  const st = JSON.parse(state);
  const s = (st.state.sessions || [])[0];
  if (!s) throw new Error('MID: there is no session in the live state to rewind');
  const ms = (s.groupMatches || []).filter(m => m.winner);
  if (ms.length < 6) throw new Error('MID: the night has too few results to rewind');
  ms.slice(-6).forEach(m => { m.winner = null; m.lossType = null; delete m.score; });
  const live = ms[ms.length - 6];
  live.score = { t1: 4, t2: 3 };          // opened on the pad, not yet locked
  s.bracket = { qf: [], sf: [], final: null };
  s.completed = false;
  state = JSON.stringify(st);
}

const srv = http.createServer({ maxHeaderSize: 1 << 20 }, (req, res) => {
  const u = (req.url || '/').split('?')[0];
  const json = (b) => { res.writeHead(200, { 'Content-Type': 'application/json' }); res.end(b); };
  if (u === '/version.txt') { res.writeHead(200, { 'Content-Type': 'text/plain' }); return res.end(VERSION); }
  if (u === '/state') return json(state);
  if (u === '/photos') return json(photos);
  if (u === '/session-photos') return json('{"ok":true,"photos":{}}');
  if (u.startsWith('/fonts/') && u.endsWith('.woff2')) {
    const f = path.join('brand/fonts', path.basename(u));
    if (fs.existsSync(f)) {
      res.writeHead(200, { 'Content-Type': 'font/woff2' });
      return res.end(fs.readFileSync(f));
    }
  }
  const b = path.basename(u);
  for (const d of ['brand/national', 'assets']) {
    const f = path.join(d, b);
    if (/\.(png|webp|jpe?g|svg)$/.test(b) && fs.existsSync(f)) {
      res.writeHead(200, { 'Content-Type': 'image/' + b.split('.').pop() });
      return res.end(fs.readFileSync(f));
    }
  }
  res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
  res.end(app);
}).listen(PORT);

const VPS = process.env.VP
  ? [process.env.VP.split('x').map(Number)]
  : [[390, 844], [375, 667]];

const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
const shots = [];

for (const [w, h] of VPS) {
  const pg = await browser.newPage({ viewport: { width: w, height: h }, deviceScaleFactor: 2 });
  await pg.route('**/unpkg.com/**', r => {
    const url = r.request().url();
    const f = /babel/.test(url) ? 'babel.js' : /react-dom/.test(url) ? 'react-dom.js' : 'react.js';
    r.fulfill({ status: 200, contentType: 'application/javascript',
                body: fs.readFileSync(path.join(VENDOR, f), 'utf8') });
  });
  await pg.route('**/fonts.googleapis.com/**', r =>
    r.fulfill({ status: 200, contentType: 'text/css', body: FONTCSS }));
  if (ROLE === 'admin')
    await pg.addInitScript(() => { try { localStorage.setItem('na-role', 'admin'); } catch {} });

  const errs = [];
  pg.on('pageerror', e => errs.push(e.message));
  await pg.goto(ORIGIN + '/', { waitUntil: 'load' });
  await pg.waitForSelector('nav.fixed.bottom-0', { timeout: 25000 });
  await pg.evaluate(() => document.fonts.ready);
  await pg.waitForTimeout(700);

  const shoot = async (label) => {
    await pg.evaluate(() => {
      const p = document.querySelector('.fixed.inset-0');
      if (p) p.scrollTop = 0; else window.scrollTo(0, 0);
    });
    await pg.waitForTimeout(250);
    const name = `${label.toLowerCase().replace(/[^a-z0-9]+/g, '-')}-${w}x${h}${ROLE ? '-' + ROLE : ''}.png`;
    const file = path.join(OUT, name);
    await pg.screenshot({ path: file, fullPage: FULL });
    // The night scrolls INSIDE a fixed pane, so documentElement.scrollHeight
    // says 844 however long the screen really is — the number that means
    // something is the pane's own.
    const tall = await pg.evaluate(() => {
      const p = [...document.querySelectorAll('.fixed.inset-0')]
        .find(e => e.scrollHeight > e.clientHeight + 4);
      return p ? { h: Math.round(p.scrollHeight), vh: p.clientHeight }
               : { h: Math.round(document.documentElement.scrollHeight), vh: innerHeight };
    });
    shots.push({ file, label: `${label}  ${w}x${h}`,
                 note: `${tall.h}px = ${(tall.h / tall.vh).toFixed(1)} screens` });
    console.log(`  ${label.padEnd(20)} ${tall.h}px  ${(tall.h / tall.vh).toFixed(1)} screens`);
  };

  // SESSIONS, a night, and then FULL RESULTS — a finished night's row opens
  // its recap, and the scorer's screens are one tap further in.
  await pg.evaluate(() => [...document.querySelectorAll('nav.fixed.bottom-0 button')]
    .find(x => (x.innerText || '').trim().toLowerCase().startsWith('sessions'))?.click());
  await pg.waitForTimeout(800);
  await shoot('SESSIONS');

  const opened = await pg.evaluate(() => {
    const r = document.querySelector('.jh-mock-sess'); if (!r) return false; r.click(); return true;
  });
  if (!opened) { console.log('  no session row to open'); await pg.close(); continue; }
  await pg.waitForTimeout(1000);
  await shoot('RECAP');

  const wentIn = await pg.evaluate(() => {
    const b = [...document.querySelectorAll('button')]
      .find(x => /FULL RESULTS/i.test(x.textContent || ''));
    if (!b) return false; b.click(); return true;
  });
  if (wentIn) { await pg.waitForTimeout(1000); await shoot('NIGHT'); }

  const subs = await pg.evaluate(() => [...new Set([...document.querySelectorAll('button')]
    .map(b => (b.textContent || '').trim())
    .filter(t => /^(GROUPS|TEAMS|BRACKET|RECAP|PHOTOS|MVP|KNOCKOUT|TABLE|SCORES|POINTS|LIST)$/i.test(t)))]);
  console.log('  sub-screens: ' + subs.join(', '));
  for (const s of subs) {
    await pg.evaluate((s) => {
      const b = [...document.querySelectorAll('button')]
        .find(x => (x.textContent || '').trim().toUpperCase() === s.toUpperCase());
      if (b) b.click();
    }, s);
    await pg.waitForTimeout(700);
    await shoot(s.toUpperCase());
  }
  if (errs.length) console.log('  page errors: ' + errs.slice(0, 3).join(' | '));
  await pg.close();
}

{
  const pg = await browser.newPage({ viewport: { width: 1600, height: 900 } });
  const cards = shots.map(s => {
    const b64 = fs.readFileSync(s.file).toString('base64');
    return `<figure><img src="data:image/png;base64,${b64}">`
         + `<figcaption><b>${s.label}</b><span>${s.note}</span></figcaption></figure>`;
  }).join('');
  await pg.setContent(`<!doctype html><meta charset="utf-8"><style>
    *{box-sizing:border-box;margin:0}
    body{background:#15171c;color:#e8e6e1;font:13px/1.4 ui-sans-serif,system-ui,sans-serif;padding:24px}
    h1{font-size:15px;letter-spacing:.14em;text-transform:uppercase;color:#9aa0ab;margin-bottom:18px}
    .grid{display:flex;flex-wrap:wrap;gap:20px;align-items:flex-start}
    figure{width:300px}
    img{width:300px;display:block;border:1px solid #2b2f37;border-radius:6px}
    figcaption{display:flex;justify-content:space-between;gap:8px;padding:7px 2px 0;
      font-size:11px;letter-spacing:.08em;text-transform:uppercase}
    figcaption b{color:#e8e6e1}figcaption span{color:#7f868f}
  </style><h1>THE NIGHT &nbsp;·&nbsp; ${APP} &nbsp;·&nbsp; ${VERSION}${ROLE ? ' · ' + ROLE : ''}</h1>
  <div class="grid">${cards}</div>`);
  await pg.waitForTimeout(400);
  await pg.screenshot({ path: path.join(OUT, 'sheet.png'), fullPage: true });
  await pg.close();
  console.log(`\n  ${path.join(OUT, 'sheet.png')}`);
}

await browser.close();
srv.close();
