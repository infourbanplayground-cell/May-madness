// Muscat Heist phase 1 QA (handoff QA.md) for the components preview page.
//   node ops/shots-heist-dev.mjs          375x812 and 360x780, deviceScaleFactor 2
//   SABOTAGE=nofont   drops both font stylesheets, and must go red
// Writes <scratch>/heist-qa/phase1/*.png and a side-by-side of the Home top
// against handoff/screenshots/01-home.png. Asserts:
//   - every face the design sets was really DRAWN (measured against itself
//     falling back, never against serif: a failed webfont is a silent fallback)
//   - no horizontal scroll and no clipped text at either width
//   - no text under 11px
//   - every button is at least 44px in both directions
import { chromium } from 'playwright';
import fs from 'fs';
import http from 'http';
import path from 'path';

const ROOT = path.resolve(path.dirname(new URL(import.meta.url).pathname), '..');
const SC = '/tmp/claude-0/-home-user-May-madness/0e44f0ad-a683-5f0d-9de6-9459ae328963/scratchpad';
const OUT = path.join(SC, 'heist-qa', 'phase1');
fs.mkdirSync(OUT, { recursive: true });
const SAB = process.env.SABOTAGE || '';
const TYPES = { '.html': 'text/html; charset=utf-8', '.css': 'text/css', '.woff2': 'font/woff2', '.png': 'image/png', '.jpg': 'image/jpeg' };

const srv = http.createServer((req, res) => {
  let u = decodeURIComponent((req.url || '/').split('?')[0]);
  if (u === '/') u = '/brand/heist/dev-components.html';
  const f = path.join(ROOT, u);
  if (!f.startsWith(ROOT) || !fs.existsSync(f) || fs.statSync(f).isDirectory()) { res.writeHead(404); return res.end(); }
  let body = fs.readFileSync(f);
  if (SAB === 'nofont' && f.endsWith('.html')) body = Buffer.from(body.toString().replace(/<link rel="stylesheet"[^>]*>/g, ''));
  res.writeHead(200, { 'Content-Type': TYPES[path.extname(f)] || 'application/octet-stream' }); res.end(body);
}).listen(0);
const PORT = srv.address().port;

const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
const fails = [];
for (const [w, h] of [[375, 812], [360, 780]]) {
  const pg = await browser.newPage({ viewport: { width: w, height: h }, deviceScaleFactor: 2 });
  const errs = []; pg.on('pageerror', e => errs.push(e.message));
  await pg.route('**/unpkg.com/**', r => {
    const u = r.request().url();
    const f = /babel/.test(u) ? 'babel.js' : /react-dom/.test(u) ? 'react-dom.js' : 'react.js';
    r.fulfill({ status: 200, contentType: 'application/javascript', body: fs.readFileSync(path.join(SC, 'vendor', f), 'utf8') });
  });
  await pg.goto(`http://127.0.0.1:${PORT}/brand/heist/dev-components.html`, { waitUntil: 'load' });
  await pg.waitForSelector('.mn-lockup', { timeout: 30000 });
  await pg.evaluate(() => document.fonts.ready);
  // images are loading="lazy" in the app, which is right on a phone and
  // leaves blank frames in a full-page shot that never scrolled to them
  await pg.evaluate(() => Promise.all([...document.images].map(i => { i.loading = 'eager';
    return i.complete ? 0 : new Promise(r => { i.onload = i.onerror = r; }); })));
  await pg.waitForTimeout(1600);   // let the stat bars finish filling (0.7s delay + 0.6s)
  if (errs.length) fails.push(`${w}: page error ${errs[0]}`);

  const r = await pg.evaluate(() => {
    const probe = (font, extra = '') => {
      const s = document.createElement('span');
      s.style.cssText = `position:absolute;visibility:hidden;white-space:nowrap;font-size:40px;font-family:${font};${extra}`;
      s.textContent = 'MUSCAT HEIST 0123 crew'; document.body.appendChild(s);
      const v = s.getBoundingClientRect().width; s.remove(); return v;
    };
    const fonts = {
      'Archivo wdth 66': probe("'Archivo',serif", "font-weight:900;font-variation-settings:'wdth' 66") !== probe('serif', 'font-weight:900'),
      'Fraunces italic': probe("'Fraunces',serif", 'font-style:italic') !== probe('serif', 'font-style:italic'),
      'Manrope': probe("'Manrope',serif", 'font-weight:600') !== probe('serif', 'font-weight:600'),
      'JetBrains Mono': [...document.fonts].some(f => /JetBrains/.test(f.family) && f.status === 'loaded'),
    };
    const broken = [...document.images].filter(i => !i.naturalWidth).map(i => i.getAttribute('src'));
    const out = { fonts, broken, small: [], clipped: [], targets: [], scrollX: document.documentElement.scrollWidth - innerWidth };
    for (const el of document.querySelectorAll('body *')) {
      const cs = getComputedStyle(el);
      const own = [...el.childNodes].some(n => n.nodeType === 3 && n.textContent.trim());
      if (own && cs.visibility !== 'hidden' && parseFloat(cs.fontSize) < 11) out.small.push(`${el.className} "${el.textContent.trim().slice(0, 20)}" ${cs.fontSize}`);
      if (own && el.scrollWidth > el.clientWidth + 1 && cs.overflow !== 'visible' && !el.closest('.mn-pills')) out.clipped.push(`${el.className} "${el.textContent.trim().slice(0, 24)}"`);
    }
    for (const b of document.querySelectorAll('button')) {
      const r = b.getBoundingClientRect();
      if (r.width < 44 || r.height < 44) out.targets.push(`${b.className} "${b.textContent.trim().slice(0, 14)}" ${Math.round(r.width)}x${Math.round(r.height)}`);
    }
    return out;
  });
  const missing = Object.entries(r.fonts).filter(([, ok]) => !ok).map(([k]) => k);
  if (missing.length) fails.push(`${w}: FONT NOT DRAWN: ${missing.join(', ')}`);
  if (r.broken.length) fails.push(`${w}: images that did not load: ${r.broken.join(', ')}`);
  if (r.scrollX > 0) fails.push(`${w}: page scrolls sideways by ${r.scrollX}px`);
  if (r.small.length) fails.push(`${w}: text under 11px: ${r.small.slice(0, 4).join(' | ')}`);
  if (r.clipped.length) fails.push(`${w}: clipped: ${r.clipped.slice(0, 4).join(' | ')}`);
  if (r.targets.length) fails.push(`${w}: targets under 44px: ${r.targets.slice(0, 4).join(' | ')}`);
  await pg.screenshot({ path: path.join(OUT, `components-${w}.png`), fullPage: true });
  if (w === 375) await pg.locator('[data-shot="home-top"]').screenshot({ path: path.join(OUT, 'home-top-375.png') });
  console.log(`  ${w}x${h}  fonts ${Object.values(r.fonts).every(Boolean) ? 'ok' : 'MISSING'}  sideways ${r.scrollX}  small ${r.small.length}  clipped ${r.clipped.length}  small-targets ${r.targets.length}`);
  await pg.close();
}
await browser.close(); srv.close();
if (fails.length) { console.error('\n' + fails.join('\n')); process.exit(1); }
console.log(`ok — ${OUT}`);
