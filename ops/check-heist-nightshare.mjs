// Muscat Heist — a NIGHT's posts (brand/heist/heist-night-share.jsx).
//   python3 build-heist-app.py && node ops/check-heist-nightshare.mjs
// The organiser's POSTS and LINE-UP in the inherited night editor must open
// the Heist night share (not Vol.9's canvas cards), and every card must come
// out of the in-app "Share image" at exactly 1080x1920.
// Muscat Heist — the ORGANISER's screens: the inherited Vol.9 UI (?classic)
// and the sheets that open over the Heist screens, after the re-skin.
//   python3 build-heist-app.py && node ops/check-heist-classic.mjs
//   SHOTS go to <scratch>/heist-qa/classic/
// On every screen: no element computes a Vol.9 colour, no Vol.9 artwork is
// drawn (a data: image in a background), every text run clears WCAG AA
// against the ground it actually sits on (composited down the ancestors —
// reading backgroundColor alone hands back a confident 1:1), nothing scrolls
// sideways, and the page throws nothing.
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
const OUT = path.join(SC, 'heist-qa', 'classic'); fs.mkdirSync(OUT, { recursive: true });
const st = JSON.parse(JSON.stringify(NAT));
st.sessions.forEach((s, i) => { s.date = SEASON.nights[i]; s.doublePoints = SEASON.doubleNights.includes(s.date); });
const T = { '.html': 'text/html; charset=utf-8', '.css': 'text/css', '.woff2': 'font/woff2', '.png': 'image/png', '.jpg': 'image/jpeg', '.json': 'application/json' };
const map = [['/assets/fonts/brand/', 'brand/fonts/'], ['/assets/fonts/heist/', 'brand/heist/fonts/'], ['/assets/art/', 'brand/heist/art/'],
             ['/assets/up-logo-tight.png', 'brand/heist/up-logo-tight.png'], ['/assets/history.json', 'brand/national/history.json'],
             ['/assets/', 'brand/national/']];
const srv = http.createServer((q, r) => {
  const u = decodeURIComponent(q.url.split('?')[0]);
  const json = o => { r.writeHead(200, { 'Content-Type': 'application/json' }); r.end(typeof o === 'string' ? o : JSON.stringify(o)); };
  if (u === '/' || u === '/index.html') { r.writeHead(200, { 'Content-Type': T['.html'] }); return r.end(fs.readFileSync(path.join(ROOT, 'heist-index.html'))); }
  if (u === '/version.txt') { r.writeHead(200); return r.end(BID + '\n'); }
  if (u === '/state') return json({ ok: true, state: st, version: 1 });
  if (u === '/photos') return json(PHOTOS);
  if (u === '/session-photos') return json({ ok: true, photos: {} });
  if (u === '/api/roster') return json({ ok: true, players: [] });
  if (u === '/save') { q.resume(); return json({ ok: true }); }
  for (const [a, b] of map) if (u.startsWith(a)) {
    const f = path.join(ROOT, b + u.slice(a.length));
    if (fs.existsSync(f) && !fs.statSync(f).isDirectory()) { r.writeHead(200, { 'Content-Type': T[path.extname(f)] || 'x' }); return r.end(fs.readFileSync(f)); }
  }
  r.writeHead(404); r.end();
}).listen(0);
const ORIGIN = `http://127.0.0.1:${srv.address().port}`;
const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
const fails = [];

async function open(admin, url) {
  const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 2 });
  await ctx.addInitScript(admin => { try {
    localStorage.setItem('mh-once-loaded', 'never');
    localStorage.setItem('aa-me', 'p_mptqpbkf_p7qv5');
    if (admin) { const exp = Math.floor(Date.now() / 1000) + 86400; localStorage.setItem('july-heat-admin', 'admin'); localStorage.setItem('july-heat-token', `admin.${exp}.sig`); }
  } catch (e) {} }, admin);
  const pg = await ctx.newPage();
  const errs = []; pg.on('pageerror', e => errs.push(e.message));
  await pg.route('**/unpkg.com/**', r => {
    const u = r.request().url();
    const f = /html-to-image/.test(u) ? 'h2i.js' : /babel/.test(u) ? 'babel.js' : /react-dom/.test(u) ? 'react-dom.js' : 'react.js';
    r.fulfill({ status: 200, contentType: 'application/javascript', body: fs.readFileSync(path.join(SC, 'vendor', f), 'utf8') });
  });
  // Tailwind's runtime is what lays the inherited screens out — served from
  // the local copy the National harness uses, or there is no layout to check
  const tw = path.join(SC, 'vendor', 'tailwind.js');
  await pg.route('**/cdn.tailwindcss.com/**', r => r.fulfill({ status: 200, contentType: 'application/javascript', body: fs.existsSync(tw) ? fs.readFileSync(tw, 'utf8') : '' }));
  await pg.route('**/fonts.googleapis.com/**', r => r.fulfill({ status: 200, contentType: 'text/css', body: '' }));
  await pg.goto(ORIGIN + url, { waitUntil: 'load' });
  if (process.env.WHY) await pg.evaluate(() => { window.__why = 1; });
  await pg.waitForTimeout(1800);
  return { ctx, pg, errs };
}


const results = [];
{
  const { ctx, pg, errs } = await open(true, '/?classic');
  // the organiser's POSTS and LINE-UP in the inherited night editor
  await pg.locator('nav button', { hasText: 'SESSIONS' }).first().click(); await pg.waitForTimeout(600);
  await pg.locator('.jh-mock-sess').last().click(); await pg.waitForTimeout(800);
  await pg.locator('button', { hasText: /FULL RESULTS/ }).first().click(); await pg.waitForTimeout(800);
  for (const [chip, want] of [['Posts', 'draw'], ['Line-up', 'lineup']]) {
    const b = pg.locator('button').filter({ hasText: new RegExp('(^|[^A-Za-z])' + chip + '\\W*$', 'i') }).first();
    if (!await b.count()) { results.push(`classic ${chip}: chip not found`); continue; }
    await b.click(); await pg.waitForTimeout(800);
    await pg.waitForSelector('.mh-sharescale .mh-story', { timeout: 15000 }).catch(() => {});
    const h = await pg.evaluate(() => location.hash + ' ' + !!document.querySelector('.mh-sharescale .mh-story'));
    results.push(`classic ${chip} -> ${h}` + (h.includes('nightshare/7/' + want) && h.endsWith('true') ? '  ok' : '  FAIL'));
    await pg.goto(ORIGIN + '/?classic'); await pg.waitForTimeout(1500);
    await pg.locator('nav button', { hasText: 'SESSIONS' }).first().click(); await pg.waitForTimeout(600);
    await pg.locator('.jh-mock-sess').last().click(); await pg.waitForTimeout(800);
    await pg.locator('button', { hasText: /FULL RESULTS/ }).first().click(); await pg.waitForTimeout(800);
  }
  await ctx.close();
}
{
  // every card exports at exactly 1080x1920 through the in-app button
  const { ctx, pg, errs } = await open(true, '/#nightshare/7/lineup');
  for (const k of ['lineup', 'draw', 'tables', 'bracket', 'champions', 'points']) {
    await pg.evaluate(k => { window.__mhLastExport = null; location.hash = 'nightshare/7/' + k; }, k); await pg.waitForTimeout(1200);
    const dl = pg.waitForEvent('download', { timeout: 20000 }).catch(() => null);
    await pg.locator('button', { hasText: 'Share image' }).click();
    await dl;
    const r = await pg.evaluate(async () => { for (let i = 0; i < 40 && !window.__mhLastExport; i++) await new Promise(r => setTimeout(r, 250));
      const b = window.__mhLastExport; if (!b) return null; const im = await createImageBitmap(b); return [im.width, im.height, b.size]; });
    results.push(`export ${k}: ${r ? r.join('x').replace(/x(\d+)$/, ' · $1 bytes') : 'NOTHING'}` + (r && r[0] === 1080 && r[1] === 1920 ? '  ok' : '  FAIL'));
  }
  if (errs.length) results.push('page errors: ' + errs.join(' | '));
  await ctx.close();
}
console.log(results.join('\n'));
await browser.close(); srv.close();
if (results.some(r => /FAIL|NOTHING|errors/.test(r))) process.exit(1);
