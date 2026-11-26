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
// APP=<file> checks another build. DUMP=<json> writes every element's laid-out
// box and key computed styles per screen, so two builds (Tailwind at runtime
// vs compiled ahead) can be compared element by element.
const PAGE = () => fs.readFileSync(process.env.APP ? path.resolve(process.env.APP) : path.join(ROOT, 'heist-index.html'));
const DUMPS = {};
const srv = http.createServer((q, r) => {
  const u = decodeURIComponent(q.url.split('?')[0]);
  const json = o => { r.writeHead(200, { 'Content-Type': 'application/json' }); r.end(typeof o === 'string' ? o : JSON.stringify(o)); };
  if (u === '/' || u === '/index.html') { r.writeHead(200, { 'Content-Type': T['.html'] }); return r.end(PAGE()); }
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
    const f = /babel/.test(u) ? 'babel.js' : /react-dom/.test(u) ? 'react-dom.js' : 'react.js';
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

const AUDIT = () => {
  const VOL9 = [[107, 15, 23], [82, 11, 18], [215, 32, 46], [247, 241, 230], [242, 208, 211], [242, 184, 188], [8, 122, 63], [26, 10, 12], [203, 189, 182]];
  const parse = c => { const m = String(c).match(/rgba?\(([^)]+)\)/); if (!m) return null; const p = m[1].split(/[,\s/]+/).filter(Boolean).map(Number); return { r: p[0], g: p[1], b: p[2], a: p.length > 3 ? p[3] : 1 }; };
  const isVol9 = c => { const p = parse(c); return p && p.a > 0.05 && VOL9.some(([r, g, b]) => Math.abs(p.r - r) + Math.abs(p.g - g) + Math.abs(p.b - b) < 9); };
  const over = (f, b) => ({ r: f.r * f.a + b.r * (1 - f.a), g: f.g * f.a + b.g * (1 - f.a), b: f.b * f.a + b.b * (1 - f.a), a: 1 });
  const lum = c => { const f = v => { v /= 255; return v <= .03928 ? v / 12.92 : Math.pow((v + .055) / 1.055, 2.4); }; return .2126 * f(c.r) + .7152 * f(c.g) + .0722 * f(c.b); };
  const ground = el => { const chain = []; for (let e = el; e; e = e.parentElement) chain.push(e);
    let c = { r: 15, g: 27, b: 43, a: 1 };
    for (let i = chain.length - 1; i >= 0; i--) { const cs = getComputedStyle(chain[i]); if (cs.backgroundImage !== 'none' && /gradient/.test(cs.backgroundImage)) return null; const b = parse(cs.backgroundColor); if (b && b.a > 0) c = over(b, c); }
    return c; };
  const out = { vol9: new Set(), art: new Set(), contrast: [], sideways: document.documentElement.scrollWidth - innerWidth };
  for (const el of document.querySelectorAll('body *')) {
    const r = el.getBoundingClientRect(); if (!r.width || !r.height) continue;
    const cs = getComputedStyle(el);
    if (cs.visibility === 'hidden' || +cs.opacity === 0) continue;
    for (const p of ['color', 'backgroundColor', 'borderTopColor', 'borderLeftColor'])
      if ((p === 'color' || parseFloat(cs.borderTopWidth) > 0 || p === 'backgroundColor') && isVol9(cs[p])) out.vol9.add(`${el.tagName.toLowerCase()}.${String(el.className).slice(0, 24)} ${p} ${cs[p]}`);
    for (const pe of [cs, getComputedStyle(el, '::before'), getComputedStyle(el, '::after')])
      if (/url\("?data:image/.test(pe.backgroundImage) && !/mh-|mn-/.test(el.className)) out.art.add(`${el.tagName.toLowerCase()}.${String(el.className).slice(0, 24)}`);
    const own = [...el.childNodes].some(n => n.nodeType === 3 && n.textContent.trim());
    if (own && r.top < innerHeight * 3) {
      const g = ground(el); const f = parse(cs.color);
      if (g && f) { const fg = over(f, g); const L1 = lum(fg), L2 = lum(g); const ratio = (Math.max(L1, L2) + .05) / (Math.min(L1, L2) + .05);
        const big = parseFloat(cs.fontSize) >= 24 || (parseFloat(cs.fontSize) >= 18.66 && +cs.fontWeight >= 700);
        if (ratio < (big ? 3 : 4.5) && el.textContent.trim().length > 1) out.contrast.push(`"${el.textContent.trim().slice(0, 22)}" ${ratio.toFixed(2)}:1` + (window.__why ? ` [${el.className} c=${cs.color} bg=${cs.backgroundColor} bi=${cs.backgroundImage.slice(0,60)}]` : '')); }
    }
  }
  return { vol9: [...out.vol9], art: [...out.art], contrast: out.contrast, sideways: out.sideways };
};

async function check(pg, errs, name) {
  if (process.env.DUMP) DUMPS[name] = await pg.evaluate(() => [...document.querySelectorAll('body *')].filter(e => !e.closest('script,style,svg'))
    .map(e => { const c = getComputedStyle(e), b = e.getBoundingClientRect();
      return [e.tagName + '.' + (typeof e.className === 'string' ? e.className : ''), Math.round(b.x), Math.round(b.y), Math.round(b.width), Math.round(b.height),
        c.display, c.position, c.padding, c.margin, c.fontSize, c.fontWeight, c.color, c.backgroundColor, c.borderRadius, c.gap, c.justifyContent, c.alignItems, c.gridTemplateColumns, c.textAlign, c.opacity].join('|'); }));
  const r = await pg.evaluate(AUDIT);
  await pg.screenshot({ path: path.join(OUT, name + '.png') });
  const bad = [];
  if (r.vol9.length) bad.push(`Vol.9 colours: ${r.vol9.slice(0, 4).join(' | ')}${r.vol9.length > 4 ? ` (+${r.vol9.length - 4})` : ''}`);
  if (r.art.length) bad.push(`Vol.9 artwork drawn on: ${r.art.slice(0, 4).join(', ')}`);
  if (r.contrast.length) bad.push(`under AA: ${r.contrast.slice(0, 4).join(' | ')}${r.contrast.length > 4 ? ` (+${r.contrast.length - 4})` : ''}`);
  if (r.sideways > 0) bad.push(`scrolls sideways ${r.sideways}px`);
  if (errs.length) bad.push(`page error: ${errs[0]}`);
  console.log(`  ${name.padEnd(16)} ${bad.length ? 'FAIL' : 'ok'}  vol9 ${r.vol9.length}  art ${r.art.length}  contrast ${r.contrast.length}`);
  bad.forEach(b => { console.log('      ' + b); fails.push(name + ': ' + b); });
}

// the five inherited tabs, as the organiser sees them
{
  const { ctx, pg, errs } = await open(true, '/?classic');
  for (const [label, name] of [['HOME', 'home'], ['SESSIONS', 'sessions'], ['RANK', 'rank'], ['ME', 'me'], ['PLAYERS', 'players']]) {
    const b = pg.locator('nav button', { hasText: label }).first();
    if (await b.count()) { await b.click(); await pg.waitForTimeout(700); }
    await check(pg, errs, name);
    if (name === 'sessions') {
      // a finished night opens its recap; the editor is one tap further in
      const row = pg.locator('.jh-mock-sess').last();
      if (!await row.count()) { fails.push('sessions: no night row to open'); console.log('  night-editor     FAIL  no night row'); }
      else {
        await row.click(); await pg.waitForTimeout(900);
        await check(pg, errs, 'night-recap');
        const into = pg.locator('button', { hasText: /OPEN SESSION|EDIT|SCORE|FULL RESULTS|OPEN NIGHT/i }).first();
        if (await into.count()) { await into.click(); await pg.waitForTimeout(900); }
        await check(pg, errs, 'night-teams');
        for (const chip of ['GROUPS', 'KO', 'POINTS', 'LIST', 'MVP', 'POSTS']) {
          const c = pg.locator('button').filter({ hasText: new RegExp('(^|[^A-Za-z])' + chip + '\\W*\\d*\\W*$', 'i') }).first();
          if (!await c.count()) { fails.push('night: no ' + chip + ' chip'); console.log('  night-' + chip.toLowerCase().padEnd(10) + ' FAIL  chip not found'); continue; }
          await c.click(); await pg.waitForTimeout(600); await check(pg, errs, 'night-' + chip.toLowerCase());
        }
        await pg.goto(ORIGIN + '/?classic'); await pg.waitForTimeout(1500);
      }
    }
  }
  await ctx.close();
}
// the night editor as it opens OVER the Heist screens (FULL RESULTS / organiser)
{
  const { ctx, pg, errs } = await open(true, '/#home');
  await pg.evaluate(() => { location.hash = 'finale'; });
  await pg.waitForTimeout(500);
  await ctx.close();
}
// the sign-in sheet and the who-are-you picker, signed out
{
  const { ctx, pg, errs } = await open(false, '/?classic');
  const logo = pg.locator('header button[aria-label="Urban Playground"]').first();
  for (let i = 0; i < 5; i++) await logo.click();
  await pg.waitForTimeout(500); await check(pg, errs, 'sign-in');
  await ctx.close();
}
await browser.close(); srv.close();
if (process.env.DUMP) fs.writeFileSync(process.env.DUMP, JSON.stringify(DUMPS));
if (fails.length) { console.error(`\n${fails.length} problems`); process.exit(1); }
console.log(`ok — ${OUT}`);
