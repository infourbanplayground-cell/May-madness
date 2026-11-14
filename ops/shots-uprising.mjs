// LOOK AT THE UPRISING APP'S SCREENS. The review tool it has never had.
//
// Everything in ops/ for UPRISING is about the FORMAT (stress, fairness,
// court-change, the sims) or the BRAND ART (the renderers). Not one thing has
// ever opened the app and looked at it — while the Vol.9 app has four
// harnesses watching its UI. And this is the app somebody holds for two hours
// beside a court, in the dark, with a night riding on it.
//
//   node ops/shots-uprising.mjs
//   VP=390x844        one viewport instead of the sweep
//   ROLE=admin        the scorer's view as well as the visitor's
//   FULL=1            whole-page shots
//   STATE=<file>      a state json to serve (default: the live snapshot)
//
// It writes a contact sheet beside the shots, because a design is judged
// against its siblings and five files in a folder is not a review.
import { chromium } from 'playwright';
import fs from 'fs';
import http from 'http';
import path from 'path';

const SC = process.env.SCRATCH
  || '/tmp/claude-0/-home-user-May-madness/0e44f0ad-a683-5f0d-9de6-9459ae328963/scratchpad';
const APP = process.env.APP || 'americano-index.html';
const OUT = process.env.OUT || (SC + '/uprising-shots');
const FULL = !!process.env.FULL;
const ROLE = process.env.ROLE || '';
const PORT = 8137;
const ORIGIN = `http://127.0.0.1:${PORT}`;
const VENDOR = path.join(SC, 'vendor');

fs.mkdirSync(OUT, { recursive: true });
const app = fs.readFileSync(APP, 'utf8');

// Served wrong, the app's own update check reloads the page for ever — so the
// version has to be the id the page was stamped with, not a timestamp.
const VERSION = fs.existsSync(APP + '.version')
  ? fs.readFileSync(APP + '.version', 'utf8').trim()
  : (/var V = "([0-9a-f]+)"/.exec(app) || [, 'dev'])[1];

const STATE = process.env.STATE || path.join(SC, 'am-live.json');
let state = fs.existsSync(STATE)
  ? fs.readFileSync(STATE, 'utf8')
  : JSON.stringify({ ok: true, state: { tournaments: [], players: [], guests: [] } });

const FONTCSS = fs.readdirSync('brand/fonts')
  .filter(f => f.endsWith('.woff2'))
  .map(f => `@font-face{font-family:'${/Archivo/i.test(f) ? 'Archivo' : 'JetBrains Mono'}';`
          + `src:url(/fonts/${f}) format('woff2');font-display:swap;font-weight:100 900;}`)
  .join('\n');

const srv = http.createServer({ maxHeaderSize: 1 << 20 }, (req, res) => {
  const u = (req.url || '/').split('?')[0];
  if (u === '/version.txt') { res.writeHead(200, { 'Content-Type': 'text/plain' }); return res.end(VERSION); }
  if (u === '/state') { res.writeHead(200, { 'Content-Type': 'application/json' }); return res.end(state); }
  if (u.startsWith('/fonts/') && u.endsWith('.woff2')) {
    const f = path.join('brand/fonts', path.basename(u));
    if (fs.existsSync(f)) { res.writeHead(200, { 'Content-Type': 'font/woff2' }); return res.end(fs.readFileSync(f)); }
  }
  const b = path.basename(u);
  for (const d of ['brand/uprising', 'brand/uprising/posts', 'assets']) {
    const f = path.join(d, b);
    if (/\.(png|webp|jpe?g|svg)$/.test(b) && fs.existsSync(f)) {
      res.writeHead(200, { 'Content-Type': 'image/' + b.split('.').pop() });
      return res.end(fs.readFileSync(f));
    }
  }
  res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
  res.end(app);
}).listen(PORT);

// The small phone is the one that shows the crowding, and 375x667 is still in
// the club's hands. Court-side the scorer is on whatever they own.
const VPS = process.env.VP
  ? [process.env.VP.split('x').map(Number)]
  : [[390, 844], [375, 667]];

const browser = await chromium.launch({
  executablePath: process.env.PW_CHROMIUM || '/opt/pw-browsers/chromium',
});
const shots = [];

for (const [w, h] of VPS) {
  const pg = await browser.newPage({ viewport: { width: w, height: h }, deviceScaleFactor: 2 });
  // Chromium here does not trust the agent proxy's CA, so React, Babel and the
  // Google Fonts stylesheet all fail and there is no page to look at at all.
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
    await pg.addInitScript(() => { try { localStorage.setItem('am-role', 'admin'); } catch {} });

  await pg.goto(ORIGIN + '/', { waitUntil: 'load' });
  await pg.waitForSelector('nav.bottom', { timeout: 25000 }).catch(() => {});
  await pg.evaluate(() => document.fonts.ready);
  await pg.waitForTimeout(800);
  await pg.keyboard.press('Escape').catch(() => {});

  // Read the tabs off the nav the app actually rendered rather than a list
  // typed here — the first label is "Board" on a live night and "Setup" when
  // there is none, and a hard-coded sweep would quietly shoot four of five.
  const tabs = await pg.evaluate(() =>
    [...document.querySelectorAll('nav.bottom button')].map(b => (b.innerText || '').trim()));
  if (!tabs.length) console.log('  !! no nav — the app did not render');

  for (const label of tabs) {
    const ok = await pg.evaluate((l) => {
      const b = [...document.querySelectorAll('nav.bottom button')]
        .find(x => (x.innerText || '').trim() === l);
      if (!b) return false; b.click(); return true;
    }, label);
    if (!ok) continue;
    await pg.waitForTimeout(800);
    await pg.evaluate(() => document.fonts.ready);
    await pg.evaluate(() => window.scrollTo(0, 0));
    await pg.waitForTimeout(250);
    const name = `${label.toLowerCase()}-${w}x${h}${ROLE ? '-' + ROLE : ''}.png`;
    const file = path.join(OUT, name);
    await pg.screenshot({ path: file, fullPage: FULL });
    const box = await pg.evaluate(() => ({
      doc: Math.round(document.documentElement.scrollHeight), vh: innerHeight,
    }));
    shots.push({ file, name, label: `${label.toUpperCase()}  ${w}x${h}`,
                 note: `page ${box.doc}px = ${(box.doc / box.vh).toFixed(1)} screens` });
    console.log(`  ${name.padEnd(26)} ${box.doc}px  ${(box.doc / box.vh).toFixed(1)} screens`);
  }
  if (errs.length) console.log('  page errors: ' + errs.slice(0, 3).join(' | '));
  await pg.close();
}

{
  const pg = await browser.newPage({ viewport: { width: 1600, height: 900 } });
  const cards = shots.map(s =>
    `<figure><img src="data:image/png;base64,${fs.readFileSync(s.file).toString('base64')}">`
    + `<figcaption><b>${s.label}</b><span>${s.note}</span></figcaption></figure>`).join('');
  await pg.setContent(`<!doctype html><meta charset="utf-8"><style>
    *{box-sizing:border-box;margin:0}
    body{background:#0A0A10;color:#F2F0F7;font:13px/1.4 ui-sans-serif,system-ui,sans-serif;padding:24px}
    h1{font-size:15px;letter-spacing:.14em;text-transform:uppercase;color:#6E6B7A;margin-bottom:18px}
    .grid{display:flex;flex-wrap:wrap;gap:20px;align-items:flex-start}
    figure{width:300px}
    img{width:300px;display:block;border:1px solid #23232e;border-radius:6px}
    figcaption{display:flex;flex-direction:column;gap:2px;padding-top:7px}
    b{font-size:12px;letter-spacing:.1em;color:#00F5C8}
    span{font-size:11px;color:#6E6B7A}
  </style><h1>${APP} · ${VERSION}${ROLE ? ' · ' + ROLE : ''}</h1><div class="grid">${cards}</div>`);
  await pg.waitForTimeout(400);
  const sheet = path.join(OUT, 'sheet.png');
  await pg.screenshot({ path: sheet, fullPage: true });
  console.log(`\n  ${sheet}`);
  await pg.close();
}

await browser.close();
srv.close();
