// Muscat Heist screen QA (handoff QA.md, steps 1, 2, 7, 8 in part).
//   node ops/shots-heist.mjs                every screen built so far
//   ONLY=wanted node ops/shots-heist.mjs    one screen
//   SABOTAGE=nofont | slice                 must go red
// For each screen: a 375x812 shot at deviceScaleFactor 2 — the reference
// PNGs' own frame — laid beside handoff/screenshots/<ref>.png in
// <scratch>/heist-qa/screens/<name>-compare.png, then the same checks at
// 375 and 360: faces really drawn, no sideways scroll, nothing clipped, no
// text under 11px, every button at least 44px, every image loaded, and
// with reduced motion on, nothing animating.
import { chromium } from 'playwright';
import fs from 'fs';
import http from 'http';
import path from 'path';
import { execFileSync } from 'child_process';

const ROOT = path.resolve(path.dirname(new URL(import.meta.url).pathname), '..');
const SC = '/tmp/claude-0/-home-user-May-madness/0e44f0ad-a683-5f0d-9de6-9459ae328963/scratchpad';
const SAB = process.env.SABOTAGE || '';
// a sabotage run must never overwrite the real shots: the next look at the
// compares would show a fallback face from a run that was meant to fail
const OUT = path.join(SC, 'heist-qa', SAB ? 'screens-sabotage' : 'screens');
fs.mkdirSync(OUT, { recursive: true });
const SCREENS = [
  ['home', 'home', '01-home'], ['jobs', 'jobs', '02-jobs'], ['wanted', 'wanted', '03-most-wanted'],
  ['me', 'me', '04-me'], ['crew', 'crew', '05-crew'], ['card', 'card/p01', '06-crew-card'], ['take', 'take', '17-the-take'],
  ['session', 'session/6', '07-session-groups'], ['live', 'live', '08-live-scoring'],
  ['recap', 'recap/5', '09-episode-recap'], ['slides', 'slides/5/1', '10-recap-slides'],
  ['loading', 'loading/64', '11-now-loading-muscat'], ['cardpull', 'cardpull/5', '12-new-crew-card'],
  ['repup', 'repup/p05', '13-rep-up'], ['rival', 'rival', '14-your-rival'],
  ['settled', 'settled', '15-score-settled'], ['finale', 'finale', '16-the-big-score'],
  ['share', 'share/card/p05', null], ['mycard', 'card/p05', null], ['who', 'who', null], ['howto', 'howto', null],
].filter(([n]) => !process.env.ONLY || process.env.ONLY.split(',').includes(n));
const TYPES = { '.html': 'text/html; charset=utf-8', '.css': 'text/css', '.woff2': 'font/woff2', '.png': 'image/png', '.jpg': 'image/jpeg', '.js': 'application/javascript' };

const srv = http.createServer((req, res) => {
  const u = decodeURIComponent((req.url || '/').split('?')[0]);
  const f = path.join(ROOT, u);
  if (!f.startsWith(ROOT) || !fs.existsSync(f) || fs.statSync(f).isDirectory()) { res.writeHead(404); return res.end(); }
  let body = fs.readFileSync(f);
  if (SAB === 'nofont' && f.endsWith('.html')) body = Buffer.from(body.toString().replace(/<link rel="stylesheet"[^>]*>/g, ''));
  // the pill row as it shipped in phases 2-4: no room for the drawn pill
  if (SAB === 'slice' && f.endsWith('.html')) {
    const t = body.toString(), u = t.replace('padding: 4px 0; margin: -4px 0; }', '}');
    if (u === t) throw new Error('SABOTAGE=slice: anchor not found, the sabotage would be vacuous');
    body = Buffer.from(u);
  }
  res.writeHead(200, { 'Content-Type': TYPES[path.extname(f)] || 'application/octet-stream' }); res.end(body);
}).listen(0);
const PORT = srv.address().port;
const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
const fails = [];

async function open(w, h, hash, reduced) {
  const ctx = await browser.newContext({ viewport: { width: w, height: h }, deviceScaleFactor: 2, reducedMotion: reduced ? 'reduce' : 'no-preference' });
  const pg = await ctx.newPage();
  const errs = []; pg.on('pageerror', e => errs.push(e.message));
  await pg.route('**/unpkg.com/**', r => {
    const u = r.request().url();
    const f = /babel/.test(u) ? 'babel.js' : /react-dom/.test(u) ? 'react-dom.js' : 'react.js';
    r.fulfill({ status: 200, contentType: 'application/javascript', body: fs.readFileSync(path.join(SC, 'vendor', f), 'utf8') });
  });
  await pg.goto(`http://127.0.0.1:${PORT}/brand/heist/preview.html#${hash}`, { waitUntil: 'load' });
  await pg.waitForSelector('.mh-page, .mh-slides', { timeout: 30000 });
  // a face no text on the screen uses is never fetched, and would measure as the
  // fallback; ask for each one, so the probe tests availability, not usage
  await pg.evaluate(() => Promise.all(["40px 'Kaushan Script'", "40px 'Bowlby One'", "600 40px Manrope"]
    .map(f => document.fonts.load(f).catch(() => 0))));
  await pg.evaluate(() => document.fonts.ready);
  await pg.waitForFunction(() => [...document.fonts].every(f => f.status !== 'loading'), null, { timeout: 15000 });
  await pg.evaluate(() => Promise.all([...document.images].map(i => { i.loading = 'eager';
    return i.complete ? 0 : new Promise(r => { i.onload = i.onerror = r; }); })));
  await pg.waitForTimeout(reduced ? 300 : 1600);
  return { ctx, pg, errs };
}

const audit = () => {
  const probe = (font, extra = '') => {
    const s = document.createElement('span');
    s.style.cssText = `position:absolute;visibility:hidden;white-space:nowrap;font-size:40px;font-family:${font};${extra}`;
    s.textContent = 'MUSCAT HEIST 0123 crew'; document.body.appendChild(s);
    const v = s.getBoundingClientRect().width; s.remove(); return v;
  };
  const fonts = {
    // the logo's faces since 25 Nov 2026 (Archivo / Fraunces before)
    'Bowlby One': probe("'Bowlby One',serif") !== probe('serif'),
    'Kaushan Script': probe("'Kaushan Script',serif") !== probe('serif'),
    'Manrope': probe("'Manrope',serif", 'font-weight:600') !== probe('serif', 'font-weight:600'),
  };
  // and the screen's OWN display text: the probe above is a span this check
  // made, which loads the face on demand; the 08 Live shot went out in the
  // fallback with that probe green. Each run is measured as it stands and again
  // forced to the fallback stack; identical widths mean it was never drawn.
  // only the element's OWN text: a child that sets its own face (the mono
  // points line inside a display figure) does not move when the parent's does
  const ownText = e => [...e.childNodes].find(n => n.nodeType === 3 && n.textContent.trim());
  const runs = [...document.querySelectorAll('.mn-display, .mn-l1, .mn-band > span, .mn-scenetag, .mn-name, .mn-rank, .mn-tiertag, .mn-pts')].filter(e => ownText(e) && e.offsetWidth).slice(0, 12);
  const undrawn = runs.filter(e => {
    const r = document.createRange(); r.selectNodeContents(ownText(e)); const w0 = r.getBoundingClientRect().width;
    const was = e.style.fontFamily; e.style.fontFamily = 'Impact, sans-serif';
    const w1 = r.getBoundingClientRect().width; e.style.fontFamily = was; return Math.abs(w0 - w1) < .5;
  });
  fonts['display text on screen'] = runs.length > 0 && undrawn.length === 0;
  if (undrawn.length) fonts['display text on screen: ' + undrawn.map(e => `"${e.textContent.trim().slice(0, 14)}"`).join(' ')] = false;
  const out = { fonts, broken: [...document.images].filter(i => !i.naturalWidth).map(i => i.getAttribute('src')),
    small: [], clipped: [], targets: [], scrollX: document.documentElement.scrollWidth - innerWidth, moving: [] };
  for (const el of document.querySelectorAll('body *')) {
    const cs = getComputedStyle(el);
    const own = [...el.childNodes].some(n => n.nodeType === 3 && n.textContent.trim());
    if (own && parseFloat(cs.fontSize) < 11 && cs.visibility !== 'hidden') out.small.push(`${el.className} "${el.textContent.trim().slice(0, 18)}" ${cs.fontSize}`);
    if (own && el.scrollWidth > el.clientWidth + 1 && cs.overflow !== 'visible') out.clipped.push(`${el.className} "${el.textContent.trim().slice(0, 24)}"`);
    if (cs.animationName && cs.animationName !== 'none') out.moving.push(`${el.className}:${cs.animationName}`);
  }
  // a row that scrolls sideways CLIPS vertically too: anything drawn (a border
  // or a fill) that pokes past its top or bottom is sliced. Every pill row lost
  // a pixel of outline top and bottom for three phases and no text check saw it.
  out.sliced = [];
  for (const row of document.querySelectorAll('body *')) {
    const cs = getComputedStyle(row);
    if (!/auto|scroll/.test(cs.overflowX)) continue;
    const R = row.getBoundingClientRect();
    for (const d of row.querySelectorAll('*')) {
      const ds = getComputedStyle(d);
      const drawn = parseFloat(ds.borderTopWidth) > 0 || (ds.backgroundColor !== 'rgba(0, 0, 0, 0)' && ds.backgroundColor !== 'transparent');
      if (!drawn) continue;
      const r = d.getBoundingClientRect();
      if (r.height && (r.top < R.top - .5 || r.bottom > R.bottom + .5))
        out.sliced.push(`"${d.textContent.trim().slice(0, 12)}" ${Math.round(r.top - R.top)}..${Math.round(r.bottom - R.top)} in ${Math.round(R.height)}`);
    }
  }
  out.unnamed = [];
  for (const b of document.querySelectorAll('button, a')) {
    // QA step 8: every action reachable and LABELLED — a control with no text
    // and no aria-label is announced as "button" and nothing else
    if (!b.innerText.trim() && !b.getAttribute('aria-label')) out.unnamed.push(b.className || b.tagName);
    const r = b.getBoundingClientRect();
    if (r.width && (r.width < 44 || r.height < 44)) out.targets.push(`${b.className} "${b.textContent.trim().slice(0, 14)}" ${Math.round(r.width)}x${Math.round(r.height)}`);
  }
  return out;
};

for (const [name, hash, ref] of SCREENS) {
  for (const [w, h] of [[375, 812], [360, 780]]) {
    const { ctx, pg, errs } = await open(w, h, hash, false);
    const r = await pg.evaluate(audit);
    const tag = `${name} ${w}`;
    if (errs.length) fails.push(`${tag}: page error ${errs[0]}`);
    const missing = Object.entries(r.fonts).filter(([, ok]) => !ok).map(([k]) => k);
    if (missing.length) fails.push(`${tag}: FONT NOT DRAWN: ${missing.join(', ')}`);
    if (r.broken.length) fails.push(`${tag}: images not loaded: ${r.broken.join(', ')}`);
    if (r.scrollX > 0) fails.push(`${tag}: scrolls sideways by ${r.scrollX}px`);
    if (r.small.length) fails.push(`${tag}: text under 11px: ${r.small.slice(0, 3).join(' | ')}`);
    if (r.clipped.length) fails.push(`${tag}: clipped: ${r.clipped.slice(0, 3).join(' | ')}`);
    if (r.sliced.length) fails.push(`${tag}: sliced by a scrolling row: ${r.sliced.slice(0, 3).join(' | ')}`);
    if (r.unnamed.length) fails.push(`${tag}: controls with no accessible name: ${r.unnamed.slice(0, 3).join(' | ')}`);
    if (r.targets.length) fails.push(`${tag}: targets under 44px: ${r.targets.slice(0, 3).join(' | ')}`);
    await pg.screenshot({ path: path.join(OUT, `${name}-${w}.png`) });
    if (w === 375) await pg.screenshot({ path: path.join(OUT, `${name}-full.png`), fullPage: true });
    console.log(`  ${tag.padEnd(12)} fonts ${missing.length ? 'MISSING' : 'ok'}  sideways ${r.scrollX}  small ${r.small.length}  clipped ${r.clipped.length}  targets ${r.targets.length}  imgs-broken ${r.broken.length}`);
    await ctx.close();
  }
  // reduced motion: nothing may still be animating
  const { ctx, pg } = await open(375, 812, hash, true);
  const m = await pg.evaluate(audit);
  if (m.moving.length) fails.push(`${name}: animating under reduced motion: ${m.moving.slice(0, 3).join(' | ')}`);
  await ctx.close();
  // side by side with the reference (screens the handoff never drew have none)
  if (!ref) continue;
  execFileSync('python3.13', ['-c', `
from PIL import Image
a=Image.open(${JSON.stringify(path.join(ROOT, 'brand/heist/handoff/screenshots', ref + '.png'))}).convert('RGB')
b=Image.open(${JSON.stringify(path.join(OUT, name + '-375.png'))}).convert('RGB')
W=375; a=a.resize((W,int(a.size[1]*W/a.size[0]))); b=b.resize((W,int(b.size[1]*W/b.size[0])))
H=max(a.size[1],b.size[1]); o=Image.new('RGB',(2*W+30,H+20),'#333'); o.paste(a,(10,10)); o.paste(b,(W+20,10))
o.save(${JSON.stringify(path.join(OUT, name + '-compare.png'))})`]);
}
await browser.close(); srv.close();
if (fails.length) { console.error('\n' + fails.join('\n')); process.exit(1); }
console.log(`ok — ${OUT}`);
