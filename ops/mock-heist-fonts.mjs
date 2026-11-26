// Display-face options for the Heist app (owner, 26 Nov: "I still don't like the
// font"). Runs the BUILT app on National's real state moved onto Heist dates,
// injects ONLY a display-face layer per option (no layout change) and shoots the
// phone home, a night page and the big screen, then one contact sheet.
//   node ops/mock-heist-fonts.mjs   -> <scratch>/font-mock/sheet.png
import { chromium } from 'playwright';
import fs from 'fs'; import http from 'http'; import path from 'path';
const ROOT = path.resolve(path.dirname(new URL(import.meta.url).pathname), '..');
const SC = '/tmp/claude-0/-home-user-May-madness/0e44f0ad-a683-5f0d-9de6-9459ae328963/scratchpad';
const FC = path.join(SC, 'fontcand'); const OUT = path.join(SC, 'font-mock'); fs.mkdirSync(OUT, { recursive: true });
const SEASON = JSON.parse(fs.readFileSync(path.join(ROOT, 'heist-season.json'), 'utf8'));
const NAT = JSON.parse(fs.readFileSync(path.join(SC, 'roster', 'state-3011.json'), 'utf8')).state;
const PHOTOS = fs.readFileSync(path.join(SC, 'roster', 'photos-3011.json'), 'utf8');
const BID = fs.readFileSync(path.join(ROOT, 'heist-index.html.version'), 'utf8').trim();
const st = JSON.parse(JSON.stringify(NAT));
st.sessions.forEach((s, i) => { s.date = SEASON.nights[i]; s.doublePoints = SEASON.doubleNights.includes(s.date); });
const n7 = st.sessions[6]; n7.completed = false; n7.bracket = {};
n7.groupMatches.slice(12).forEach(m => { delete m.winner; delete m.score; delete m.lossType; });
const T = { '.html': 'text/html; charset=utf-8', '.css': 'text/css', '.woff2': 'font/woff2', '.png': 'image/png', '.webp': 'image/webp', '.jpg': 'image/jpeg', '.json': 'application/json' };
const map = [['/fc/', FC + '/'], ['/assets/fonts/brand/', 'brand/fonts/'], ['/assets/fonts/heist/', 'brand/heist/fonts/'], ['/assets/art/', 'brand/heist/art/'],
  ['/assets/up-logo-tight.png', 'brand/heist/up-logo-tight.png'], ['/heist-logo.webp', 'brand/heist/heist-logo.webp'], ['/assets/heist-logo.webp', 'brand/heist/heist-logo.webp'], ['/assets/history.json', 'brand/national/history.json']];
const srv = http.createServer((q, r) => {
  const u = decodeURIComponent(q.url.split('?')[0]);
  const json = o => { r.writeHead(200, { 'Content-Type': 'application/json' }); r.end(typeof o === 'string' ? o : JSON.stringify(o)); };
  if (u === '/' || u === '/index.html') { r.writeHead(200, { 'Content-Type': T['.html'] }); return r.end(fs.readFileSync(path.join(ROOT, 'heist-index.html'))); }
  if (u === '/version.txt') { r.writeHead(200); return r.end(BID + '\n'); }
  if (u === '/state') return json({ ok: true, state: st, version: 1 });
  if (u === '/photos') return json(PHOTOS);
  if (u === '/session-photos') return json({ ok: true, photos: {} });
  if (u === '/api/roster') return json({ ok: true, players: [] });
  for (const [a, b] of map) if (u.startsWith(a)) {
    const f = path.isAbsolute(b) ? b + u.slice(a.length) : path.join(ROOT, b + u.slice(a.length));
    if (fs.existsSync(f) && !fs.statSync(f).isDirectory()) { r.writeHead(200, { 'Content-Type': T[path.extname(f)] || 'x' }); return r.end(fs.readFileSync(f)); }
  }
  r.writeHead(404); r.end();
}).listen(0);
const O = `http://127.0.0.1:${srv.address().port}`;

// each option: the face, its axes, and the treatment. The alternatives drop the
// cartoon outline and set CAPS — the poster voice the launch posts already use.
const clean = `-webkit-text-stroke:0 !important; text-shadow:0 .04em .12em rgba(0,0,0,.45) !important; text-transform:uppercase !important;`;
const OPTS = {
  'NOW · Bowlby One': '',
  'A · Archivo Black Condensed': { face: `src:url(/assets/fonts/brand/Archivo-latin.woff2) format('woff2'); font-weight:100 900; font-stretch:62% 125%;`, axes: `'wdth' 72, 'wght' 900`, extra: 'letter-spacing:.005em !important;' },
  'B · Anton': { face: `src:url(/fc/Anton.woff2) format('woff2');`, axes: 'normal', extra: 'letter-spacing:.01em !important;' },
  'C · Bebas Neue': { face: `src:url(/fc/BebasNeue.woff2) format('woff2');`, axes: 'normal', extra: 'letter-spacing:.03em !important;' },
  'D · Barlow Condensed Italic': { face: `src:url(/fc/BarlowCondensed.woff2) format('woff2'); font-style:italic; font-weight:800;`, axes: 'normal', extra: 'font-style:italic !important; font-weight:800 !important; letter-spacing:.005em !important;' },
  'E · Oswald': { face: `src:url(/fc/Oswald.woff2) format('woff2'); font-weight:700;`, axes: 'normal', extra: 'font-weight:700 !important; letter-spacing:.01em !important;' },
};
const css = o => !o ? '' : `@font-face{font-family:'HX Display';${o.face}}
:root, html:not(#mh) { --mn-font-display:'HX Display', Impact, sans-serif !important; --mn-display-axes:${o.axes} !important; }
.mn-display, .mn-display *, .mn-l1, .mn-name, .mn-rank, .mn-pts, .mn-btn-primary, .mn-btn-ghost, .mn-scenetag, .mn-billing, .mhw-time, .mhw-gpos, .mhw-kside b, .mhw-prow b, .mhw-tick strong, .mhw-champscore b,
[style*="--mn-font-display"] { font-family:'HX Display', Impact, sans-serif !important; font-variation-settings:${o.axes} !important; ${clean} ${o.extra} }`;

// MODE=body: the display face is the app's own now (A), and the options are the
// sentence face and the label face
const BODY = {
  'NOW · Manrope + JetBrains Mono': null,
  '1 · Archivo throughout': { faces: '', ui: "'Archivo'", mono: "'Archivo'" },
  '2 · Barlow + Barlow Semi Condensed': { faces: [500, 600, 700, 800].map(w => `@font-face{font-family:'HX UI';font-weight:${w};src:url(/fc/Barlow-${w}.woff2) format('woff2')}`).join('') + `@font-face{font-family:'HX Lab';font-weight:400 900;src:url(/fc/BarlowSC-700.woff2) format('woff2')}`, ui: "'HX UI'", mono: "'HX Lab'" },
  '3 · Inter throughout': { faces: `@font-face{font-family:'HX UI';font-weight:100 900;src:url(/fc/Inter.woff2) format('woff2')}`, ui: "'HX UI'", mono: "'HX UI'" },
};
const bodyCss = o => !o ? '' : `${o.faces}
:root, html:not(#mh) { --mn-font-ui:${o.ui}, system-ui, sans-serif !important; --mn-font-mono:${o.mono}, system-ui, sans-serif !important; }
html:not(#mh) body, html:not(#mh) .mn-serif, html:not(#mh) .mh-page { font-family:${o.ui}, system-ui, sans-serif; }
.mn-label, .mhw-label, .mhw-code, .mhw-live, .mhw-progword, .mhw-progn, .mhw-ctag, .mhw-url { font-weight:700 !important; }`;
if (process.env.MODE === 'body') { for (const k of Object.keys(OPTS)) delete OPTS[k]; Object.assign(OPTS, BODY); }
const styleFor = o => process.env.MODE === 'body' ? bodyCss(o) : css(o);
const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
const shots = [];
for (const [name, o] of Object.entries(OPTS)) {
  const key = (process.env.MODE === 'body' ? 'body-' : '') + name.split(' ')[0];
  for (const [view, url, vp] of [['home', '/#home', { width: 390, height: 844 }], ['night', '/#session/7', { width: 390, height: 844 }], ['wall', `/?tv=1&s=${st.sessions[6].id}`, { width: 1080, height: 1920 }]]) {
    const ctx = await browser.newContext({ viewport: vp, deviceScaleFactor: view === 'wall' ? 1 : 2 });
    await ctx.addInitScript(() => { try { localStorage.setItem('mh-once-loaded', 'never'); localStorage.setItem('mh-howto-seen', '1'); localStorage.setItem('mh-who-asked', '1'); } catch (e) {} });
    const pg = await ctx.newPage();
    await pg.route('**/unpkg.com/**', r => { const u = r.request().url(); const f = /html-to-image/.test(u) ? 'h2i.js' : /babel/.test(u) ? 'babel.js' : /react-dom/.test(u) ? 'react-dom.js' : 'react.js';
      r.fulfill({ status: 200, contentType: 'application/javascript', body: fs.readFileSync(path.join(SC, 'vendor', f), 'utf8') }); });
    await pg.route('**/fonts.googleapis.com/**', r => r.fulfill({ status: 200, contentType: 'text/css', body: '' }));
    await pg.route('**/api.savemyplay.com/**', r => r.fulfill({ status: 200, contentType: 'application/json', headers: { 'access-control-allow-origin': '*' }, body: '{"clips":[]}' }));
    await pg.goto(O + url, { waitUntil: 'load' });
    await pg.waitForSelector(view === 'wall' ? '.mhw' : '.mh-page', { timeout: 40000 });
    if (o) await pg.addStyleTag({ content: styleFor(o) });
    await pg.evaluate(() => Promise.all(["40px 'HX Display'", "italic 800 40px 'HX Display'", "700 40px 'HX Display'", "600 16px 'HX UI'", "700 16px 'HX Lab'", "900 40px Archivo", "600 16px Archivo", "40px 'Bowlby One'", "600 40px Manrope"].map(f => document.fonts.load(f).catch(() => 0))));
    await pg.evaluate(() => { dispatchEvent(new Event('resize')); });
    await pg.waitForTimeout(1500);
    const drawn = await pg.evaluate(() => { const s = document.createElement('span'); s.textContent = 'THE HEAT 20:27'; s.style.cssText = "position:absolute;font:40px 'HX Display',serif"; document.body.append(s); const a = s.offsetWidth; s.style.fontFamily = 'serif'; const b = s.offsetWidth; s.remove(); return a !== b; });
    if (o && !drawn && process.env.MODE !== 'body') throw new Error(name + ': face not drawn');
    const f = path.join(OUT, `${key}-${view}.png`); await pg.screenshot({ path: f }); shots.push([name, view, f]);
    await ctx.close();
  }
  console.log('shot', name);
}
// contact sheet: one row per option
const b64 = f => 'data:image/png;base64,' + fs.readFileSync(f).toString('base64');
const rows = Object.keys(OPTS).map(n => `<div class="row"><div class="lab">${n}</div>${shots.filter(s => s[0] === n).map(s => `<img class="${s[1]}" src="${b64(s[2])}">`).join('')}</div>`).join('');
const ctx = await browser.newContext({ viewport: { width: 1500, height: 900 } }); const pg = await ctx.newPage();
await pg.setContent(`<style>body{margin:0;background:#111;font:600 26px system-ui;color:#fff}.row{display:flex;align-items:flex-start;gap:18px;padding:22px}.lab{width:220px}img{height:760px;border-radius:10px}</style>${rows}`);
await pg.screenshot({ path: path.join(OUT, (process.env.MODE === 'body' ? 'body-' : '') + 'sheet.png'), fullPage: true });
await browser.close(); srv.close(); console.log(path.join(OUT, 'sheet.png'));
