// LOOK AT THE FRONT DOOR. urbanpadel.om is the one page every visitor sees
// first and nothing in ops/ had ever opened it at a phone's width.
//   node ops/shots-landing.mjs        VP=390x844  FULL=1
import { chromium } from 'playwright';
import fs from 'fs'; import http from 'http'; import path from 'path';
const SC = process.env.SCRATCH || '/tmp/claude-0/-home-user-May-madness/0e44f0ad-a683-5f0d-9de6-9459ae328963/scratchpad';
const OUT = process.env.OUT || SC + '/landing-shots';
fs.mkdirSync(OUT, { recursive: true });
const page = fs.readFileSync('landing/index.html', 'utf8');
const FONTCSS = fs.readdirSync('brand/fonts').filter(f => f.endsWith('.woff2'))
  .map(f => `@font-face{font-family:'${/Archivo/i.test(f) ? 'Archivo' : 'JetBrains Mono'}';src:url(/fonts/${f}) format('woff2');font-weight:100 900;font-display:swap;}`).join('\n');
const srv = http.createServer((q, r) => {
  const u = decodeURIComponent((q.url || '/').split('?')[0]);
  if (u.startsWith('/fonts/')) { const f = path.join('brand/fonts', path.basename(u));
    if (fs.existsSync(f)) { r.writeHead(200, { 'Content-Type': 'font/woff2' }); return r.end(fs.readFileSync(f)); } }
  // the landing references its art by path under the web root
  for (const root of ['landing', '.', 'brand']) {
    const f = path.join(root, u);
    if (u !== '/' && fs.existsSync(f) && fs.statSync(f).isFile()) {
      const ext = path.extname(f).slice(1);
      r.writeHead(200, { 'Content-Type': ({ png:'image/png', webp:'image/webp', jpg:'image/jpeg', jpeg:'image/jpeg', svg:'image/svg+xml', css:'text/css', js:'application/javascript' })[ext] || 'application/octet-stream' });
      return r.end(fs.readFileSync(f));
    }
  }
  // /assets/<name> on the server is a flat directory fed from several brand
  // folders; resolve by basename so the tool sees what the visitor sees.
  if (u.startsWith('/assets/')) {
    const want = path.basename(u);
    const hit = fs.readdirSync('brand', { recursive: true }).map(String).find(x => path.basename(x) === want);
    const f = hit && path.join('brand', hit);
    if (f && fs.statSync(f).isFile()) {
      const ext = path.extname(f).slice(1);
      r.writeHead(200, { 'Content-Type': ({ png:'image/png', webp:'image/webp', jpg:'image/jpeg', jpeg:'image/jpeg', svg:'image/svg+xml' })[ext] || 'application/octet-stream' });
      return r.end(fs.readFileSync(f));
    }
  }
  if (u === '/') { r.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' }); return r.end(page); }
  r.writeHead(404); r.end();
}).listen(8139);
const b = await chromium.launch({ executablePath: process.env.PW_CHROMIUM || '/opt/pw-browsers/chromium' });
const VPS = process.env.VP ? [process.env.VP.split('x').map(Number)] : [[390, 844], [1280, 800]];
for (const [w, h] of VPS) {
  const pg = await b.newPage({ viewport: { width: w, height: h }, deviceScaleFactor: w < 600 ? 2 : 1, acceptDownloads: true });
  const missing = [];
  pg.on('response', x => { if (x.status() === 404) missing.push(x.url().replace('http://127.0.0.1:8139', '')); });
  await pg.route('**/fonts.googleapis.com/**', r => r.fulfill({ status: 200, contentType: 'text/css', body: FONTCSS }));
  await pg.route('**/fonts.gstatic.com/**', r => r.abort());
  // SaveMyPlay, served from fixtures: Chromium here cannot reach it (proxy CA),
  // and the FROM THE COURTS strip stays hidden — correctly — without clips.
  const SMP = path.join(SC, 'smp');
  if (fs.existsSync(path.join(SMP, 'clips.json'))) {
    await pg.route('**/api.savemyplay.com/**', r => r.fulfill({ status: 200, contentType: 'application/json',
      headers: { 'access-control-allow-origin': '*' }, body: fs.readFileSync(path.join(SMP, 'clips.json')) }));
    await pg.route('**/smpw.b-cdn.net/**', r => {
      const f = path.join(SMP, 'cdn', path.basename(new URL(r.request().url()).pathname));
      if (fs.existsSync(f)) return r.fulfill({ status: 200, contentType: 'image/jpeg', body: fs.readFileSync(f) });
      const mp4 = path.join(SC, 'video', 'national-double-7s-TOMORROW.mp4');
      if (f.endsWith('.mp4') && fs.existsSync(mp4)) return r.fulfill({ status: 200, contentType: 'video/mp4',
        headers: { 'access-control-allow-origin': '*' }, body: fs.readFileSync(mp4) });
      return r.fulfill({ status: 404, body: '' });
    });
  }
  await pg.goto('http://127.0.0.1:8139/', { waitUntil: 'load' });
  await pg.evaluate(() => document.fonts.ready); await pg.waitForTimeout(500);
  const f = path.join(OUT, `landing-${w}x${h}.png`);
  await pg.screenshot({ path: f, fullPage: true });
  const doc = await pg.evaluate(() => document.documentElement.scrollHeight);
  const over = await pg.evaluate(() => document.documentElement.scrollWidth - innerWidth);
  // CLIPS=1 — open the first clip, shoot the player, and press Download
  if (process.env.CLIPS) {
    const shown = await pg.evaluate(() => !document.getElementById('clips').hidden);
    console.log('  clips strip ' + (shown ? 'shown' : 'HIDDEN'));
    if (shown) {
      await pg.evaluate(() => document.querySelector('#clips').scrollIntoView({ block: 'start' }));
      await pg.waitForTimeout(400);
      await pg.screenshot({ path: path.join(OUT, `clips-${w}x${h}.png`) });
      await pg.evaluate(() => document.querySelector('.clip').click());
      await pg.waitForTimeout(800);
      const dl = pg.waitForEvent('download', { timeout: 20000 }).catch(() => null);
      await pg.click('#pl-dl');
      const d = await dl;
      console.log(d ? `  DOWNLOAD ${d.suggestedFilename()}` : '  !! DOWNLOAD produced no file');
      await pg.waitForTimeout(300);
      await pg.screenshot({ path: path.join(OUT, `player-${w}x${h}.png`) });
    }
  }
  console.log(`  landing-${w}x${h}.png  ${doc}px  ${(doc / h).toFixed(1)} screens  h-overflow ${over}px` + (missing.length ? `  404: ${[...new Set(missing)].join(', ')}` : ''));
  await pg.close();
}
await b.close(); srv.close();
