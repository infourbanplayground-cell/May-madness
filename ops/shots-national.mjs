// LOOK AT THE SCREENS. The review tool, not an assertion harness.
//
// Everything else in ops/ answers a yes/no question — is the colour right, is
// the band drawn, does the button reach. None of them answer "does this look
// like something a club would be proud of", which is a question only a person
// can answer and only from a picture. The design changes in this volume have
// repeatedly passed every check while being wrong in a way that was obvious
// the moment somebody looked (a 128px header, a poster above the live table,
// a roster 55 screens long), so the picture comes before the deploy.
//
//   node ops/shots-national.mjs
//   APP=<file>      which build to shoot (default national-index.html)
//   OUT=<dir>       where the PNGs land (default <scratchpad>/vol9-shots)
//   VP=390x844      one viewport instead of the sweep
//   ROLE=admin      shoot the organiser's view as well as the visitor's
//   FULL=1          whole-page shots instead of one screen's worth
//   SEEDED=1        serve the season's nine nights, so inner screens have data
//
// It writes a contact sheet (`sheet.png`) beside the individual shots, because
// a design is judged against its own siblings and five files in a folder is
// not a design review.
import { chromium } from 'playwright';
import fs from 'fs';
import http from 'http';
import path from 'path';

const SC = '/tmp/claude-0/-home-user-May-madness/0e44f0ad-a683-5f0d-9de6-9459ae328963/scratchpad';
const APP = process.env.APP || 'national-index.html';
const OUT = process.env.OUT || (SC + '/vol9-shots');
const FULL = !!process.env.FULL;
const SEEDED = !!process.env.SEEDED;
const ROLE = process.env.ROLE || '';
fs.rmSync(OUT, { recursive: true, force: true });
fs.mkdirSync(OUT, { recursive: true });

const PORT = 8137;
const ORIGIN = `http://127.0.0.1:${PORT}`;
const VENDOR = SC + '/vendor';
const app = fs.readFileSync(APP, 'utf8');
const FONTCSS = fs.readFileSync('brand/fonts/fonts.css', 'utf8')
  .replace(/url\(([^)]+)\)/g, (m, u) => `url(/fonts/${path.basename(u.replace(/['"]/g, ''))})`);
const VERSION = fs.existsSync(APP + '.version')
  ? fs.readFileSync(APP + '.version', 'utf8').trim() : 'dev';

// THE LIVE STATE, not an empty season. Vol.9 has played a night; a shot of the
// empty-state cards is a picture of a screen nobody will see again.
const stateFile = fs.existsSync(SC + '/na-live.json') ? '/na-live.json' : '/na.json';
let state = fs.readFileSync(SC + stateFile, 'utf8');
const photos = fs.existsSync(SC + '/na-photos.json')
  ? fs.readFileSync(SC + '/na-photos.json', 'utf8') : '{"ok":true,"photos":{}}';
if (SEEDED) {
  const st = JSON.parse(state);
  const cfg = JSON.parse(fs.readFileSync('national-season.json', 'utf8'));
  if (!(st.state.sessions || []).length)
    st.state.sessions = cfg.nights.map((d, i) => ({
      id: 's' + i, name: 'Session ' + (i + 1), date: d,
      groupCount: 4, qualifyCount: 2, teams: [], groupMatches: [],
      bracket: { qf: [], sf: [], final: null }, waitlist: [],
      doublePoints: cfg.doubleNights.includes(d), completed: false,
    }));
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

// THE CHROME IS A FIXED COST, so the small phone is the one that shows the
// crowding. 390x844 is the common iPhone; 375x667 is the small one still in
// the club's hands and the size every layout problem here has shown up on.
const VPS = process.env.VP
  ? [process.env.VP.split('x').map(Number)]
  : [[390, 844], [375, 667]];

const SCREENS = ['home', 'sessions', 'rank', 'me', 'players'];

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
  const errs = [];
  pg.on('pageerror', e => errs.push(e.message));

  if (ROLE === 'admin')
    await pg.addInitScript(() => {
      try { localStorage.setItem('na-role', 'admin'); } catch {}
    });

  await pg.goto(ORIGIN + '/', { waitUntil: 'load' });
  await pg.waitForSelector('nav.fixed.bottom-0', { timeout: 25000 });
  await pg.evaluate(() => document.fonts.ready);
  await pg.waitForTimeout(700);
  // The sign-in sheet re-opens itself whenever a save fails, so dismissing it
  // once is not enough — but at start-up it is the only thing in the way.
  await pg.keyboard.press('Escape').catch(() => {});

  for (const screen of SCREENS) {
    if (screen !== 'home') {
      const ok = await pg.evaluate((l) => {
        const b = [...document.querySelectorAll('nav.fixed.bottom-0 button, nav.fixed.bottom-0 a')]
          .find(x => (x.innerText || '').trim().toLowerCase().startsWith(l));
        if (!b) return false; b.click(); return true;
      }, screen);
      if (!ok) { console.log(`  no ${screen} tab`); continue; }
      await pg.waitForTimeout(800);
      await pg.evaluate(() => document.fonts.ready);
    }
    await pg.evaluate(() => window.scrollTo(0, 0));
    await pg.waitForTimeout(250);
    const name = `${screen}-${w}x${h}${ROLE ? '-' + ROLE : ''}.png`;
    const file = path.join(OUT, name);
    // VIEWPORT BY DEFAULT. The roster is 340 people and a full-page shot of it
    // is 46,000px tall, which is not a thing anybody can look at — and looking
    // at it is the entire reason the shot exists.
    await pg.screenshot({ path: file, fullPage: FULL });
    const box = await pg.evaluate(() => ({
      doc: Math.round(document.documentElement.scrollHeight),
      vh: innerHeight,
    }));
    shots.push({ file, name, label: `${screen.toUpperCase()}  ${w}x${h}`,
                 note: `page ${box.doc}px = ${(box.doc / box.vh).toFixed(1)} screens` });
    console.log(`  ${name.padEnd(26)} ${box.doc}px  ${(box.doc / box.vh).toFixed(1)} screens`);
  }
  if (errs.length) console.log('  page errors: ' + errs.slice(0, 3).join(' | '));
  await pg.close();
}

// ── the contact sheet ────────────────────────────────────────────────────────
// A design is judged against its own siblings. Five files in a folder is not a
// review; one sheet is.
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
  </style><h1>${APP} &nbsp;·&nbsp; ${VERSION}${ROLE ? ' · ' + ROLE : ''}${SEEDED ? ' · seeded' : ''}</h1>
  <div class="grid">${cards}</div>`);
  await pg.waitForTimeout(400);
  await pg.screenshot({ path: path.join(OUT, 'sheet.png'), fullPage: true });
  await pg.close();
  console.log(`\n  ${path.join(OUT, 'sheet.png')}`);
}

await browser.close();
srv.close();
