// Muscat Heist — THE WALL (?tv=), the big screen beside the courts.
//   python3 build-heist-app.py && node ops/check-heist-wall.mjs
//   ONLY=<state>   SHOTS=1 (screens in <scratch>/heist-qa/wall/)
//
// Runs the BUILT app on National's real state moved onto the Heist dates, in
// every state a night has — before it (soon), the group stage half played,
// the knockout half played, full time — at a portrait panel, a landscape TV
// and a small portrait screen. On each: no page error, no scroll, nothing
// cut by its box or by the panel it sits in, no two text runs overlapping,
// the faces and the display face really drawn. Then the reason the wall
// exists: a score locked on another phone takes the wall over with that
// score, and a final ends on the champions.
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
const OUT = path.join(SC, 'heist-qa', 'wall'); fs.mkdirSync(OUT, { recursive: true });
const clone = o => JSON.parse(JSON.stringify(o));
const clear = m => { if (m) { delete m.winner; delete m.score; delete m.lossType; delete m.resultAt; } };

const base = clone(NAT);
base.sessions.forEach((s, i) => { s.date = SEASON.nights[i]; s.doublePoints = SEASON.doubleNights.includes(s.date); });
const ids = base.sessions.map(s => s.id);
// groups: night 7 tonight, half its group matches to play
const groups = clone(base); { const n = groups.sessions[6]; n.completed = false; n.bracket = {}; n.groupMatches.slice(12).forEach(clear); }
// ko: night 6 with the quarter-finals played and the semis and final still to come
const ko = clone(base); { const n = ko.sessions[5]; n.completed = false; (n.bracket.sf || []).forEach(clear); clear(n.bracket.final);
  if (n.bracket.final) { n.bracket.final.team1Id = null; n.bracket.final.team2Id = null; } }
const done = clone(base);
const soon = clone(base); { soon.sessions = soon.sessions.slice(0, 7); const n = clone(soon.sessions[6]); n.id = 'soon8'; n.date = SEASON.nights[7]; n.completed = false; n.groupMatches.forEach(clear); n.bracket = {}; soon.sessions.push(n); }
const STATES = { soon: [soon, 'soon8'], groups: [groups, ids[6]], ko: [ko, ids[5]], done: [done, ids[4]] };

let cur = groups;
const T = { '.html': 'text/html; charset=utf-8', '.css': 'text/css', '.woff2': 'font/woff2', '.png': 'image/png', '.webp': 'image/webp', '.jpg': 'image/jpeg', '.json': 'application/json' };
const map = [['/assets/fonts/brand/', 'brand/fonts/'], ['/assets/fonts/heist/', 'brand/heist/fonts/'], ['/assets/art/', 'brand/heist/art/'],
             ['/assets/up-logo-tight.png', 'brand/heist/up-logo-tight.png'], ['/heist-logo.webp', 'brand/heist/heist-logo.webp'], ['/assets/heist-logo.webp', 'brand/heist/heist-logo.webp'], ['/assets/history.json', 'brand/national/history.json']];
const srv = http.createServer((q, r) => {
  const u = decodeURIComponent(q.url.split('?')[0]);
  const json = o => { r.writeHead(200, { 'Content-Type': 'application/json' }); r.end(typeof o === 'string' ? o : JSON.stringify(o)); };
  if (u === '/' || u === '/index.html') { r.writeHead(200, { 'Content-Type': T['.html'] }); return r.end(fs.readFileSync(path.join(ROOT, 'heist-index.html'))); }
  if (u === '/version.txt') { r.writeHead(200); return r.end(BID + '\n'); }
  if (u === '/state') return json({ ok: true, state: cur, version: 1 });
  if (u === '/photos') return json(PHOTOS);
  if (u === '/session-photos') return json({ ok: true, photos: {} });
  if (u === '/api/roster') return json({ ok: true, players: [] });
  for (const [a, b] of map) if (u.startsWith(a)) {
    const f = path.join(ROOT, b + u.slice(a.length));
    if (fs.existsSync(f) && !fs.statSync(f).isDirectory()) { r.writeHead(200, { 'Content-Type': T[path.extname(f)] || 'x' }); return r.end(fs.readFileSync(f)); }
  }
  r.writeHead(404); r.end();
}).listen(0);
const ORIGIN = `http://127.0.0.1:${srv.address().port}`;
const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
const fails = []; const ok = (c, m) => { if (!c) { fails.push(m); console.log('  FAIL ' + m); } else if (process.env.V) console.log('  ok   ' + m); };

async function open(vp, sid) {
  const ctx = await browser.newContext({ viewport: vp, deviceScaleFactor: 1 });
  const pg = await ctx.newPage();
  const errs = []; pg.on('pageerror', e => errs.push(e.message));
  await pg.route('**/unpkg.com/**', r => {
    const u = r.request().url();
    const f = /html-to-image/.test(u) ? 'h2i.js' : /babel/.test(u) ? 'babel.js' : /react-dom/.test(u) ? 'react-dom.js' : 'react.js';
    r.fulfill({ status: 200, contentType: 'application/javascript', body: fs.readFileSync(path.join(SC, 'vendor', f), 'utf8') });
  });
  await pg.route('**/fonts.googleapis.com/**', r => r.fulfill({ status: 200, contentType: 'text/css', body: '' }));
  await pg.route('**/api.savemyplay.com/**', r => r.fulfill({ status: 200, contentType: 'application/json', headers: { 'access-control-allow-origin': '*' }, body: '{"clips":[]}' }));
  await pg.goto(`${ORIGIN}/?tv=1&s=${sid}`, { waitUntil: 'load' });
  await pg.waitForSelector('.mhw', { timeout: 40000 });
  await pg.evaluate(() => Promise.all(["900 40px Archivo", "800 40px Barlow", "700 40px 'Barlow Semi Condensed'"].map(f => document.fonts.load(f).catch(() => 0))));
  await pg.evaluate(() => Promise.all([...document.images].map(i => i.complete ? 0 : new Promise(r => { i.onload = i.onerror = r; }))));
  await pg.waitForTimeout(900);
  return { ctx, pg, errs };
}

const audit = pg => pg.evaluate(() => {
  const bad = [];
  const leaves = [...document.querySelectorAll('.mhw *')].filter(e => [...e.childNodes].some(n => n.nodeType === 3 && n.textContent.trim()) && e.offsetWidth && !e.closest('.mhw-tick'));
  const vis = e => { for (let x = e; x; x = x.parentElement) { const cs = getComputedStyle(x); if (cs.opacity === '0' || cs.visibility === 'hidden') return false; } return true; };
  for (const e of leaves) {
    if (e.scrollWidth > e.clientWidth + 1 && getComputedStyle(e).overflow !== 'visible') bad.push(`cut "${e.textContent.trim().slice(0, 30)}" ${e.scrollWidth}>${e.clientWidth}`);
    const r = document.createRange(); r.selectNodeContents(e); const b = r.getBoundingClientRect();
    if (b.right > innerWidth + 1 || b.bottom > innerHeight + 1 || b.left < -1 || b.top < -1) bad.push(`off screen "${e.textContent.trim().slice(0, 30)}"`);
    // every box it sits in, not only the nearest: a group can fit its rows and still run out of the panel
    for (let box = e.closest('.mhw-now, .mhw-panel, .mhw-court, .mhw-group, .mhw-kmatch'); box; box = box.parentElement && box.parentElement.closest('.mhw-now, .mhw-panel, .mhw-court, .mhw-group, .mhw-kmatch')) {
      const c = box.getBoundingClientRect(); const tol = Math.max(2, b.height * .22);
      if (b.bottom > c.bottom + tol || b.top < c.top - tol || b.right > c.right + 1) { bad.push(`outside its box "${e.textContent.trim().slice(0, 30)}" (${box.className})`); break; }
    }
  }
  // overlap: per line box, across different blocks
  const runs = [];
  for (const e of leaves) { if (!vis(e) || e.closest('.mhw-flash')) continue; const r = document.createRange(); r.selectNodeContents(e);
    // Bowlby One's font box is far taller than its letters (the screenshots show clear
    // ground between "17:30" and the line under it while the boxes cross by 40px),
    // so display type is measured by its em box around the line's centre
    const disp = e.closest('.mn-display, .mhw-time'); const fs = parseFloat(getComputedStyle(e).fontSize);
    for (const b0 of r.getClientRects()) if (b0.width > 2) { let b = b0;
      if (disp && b0.height > fs) { const cut = (b0.height - fs) / 2; b = { left: b0.left, right: b0.right, top: b0.top + cut, bottom: b0.bottom - cut, height: fs, width: b0.width }; }
      runs.push({ e, b }); } }
  const blk = e => { for (let x = e; x; x = x.parentElement) if (/^(block|flex|grid|list-item)$/.test(getComputedStyle(x).display)) return x; };
  for (let i = 0; i < runs.length; i++) for (let j = i + 1; j < runs.length; j++) {
    const a = runs[i], c = runs[j]; if (blk(a.e) === blk(c.e) || a.e.contains(c.e) || c.e.contains(a.e)) continue;
    const ox = Math.min(a.b.right, c.b.right) - Math.max(a.b.left, c.b.left), oy = Math.min(a.b.bottom, c.b.bottom) - Math.max(a.b.top, c.b.top);
    if (ox > 3 && oy > Math.max(3, .3 * Math.min(a.b.height, c.b.height))) bad.push(`overlap "${a.e.textContent.trim().slice(0, 20)}" / "${c.e.textContent.trim().slice(0, 20)}"`);
  }
  const probe = (fam, fb) => { const s = document.createElement('span'); s.textContent = 'muscat heist 0123'; s.style.cssText = `position:absolute;font:40px ${fam},${fb};white-space:nowrap`; document.body.append(s); const w = s.offsetWidth; s.style.fontFamily = fb; const w2 = s.offsetWidth; s.remove(); return w !== w2; };
  return { bad: [...new Set(bad)], scroll: document.documentElement.scrollHeight - innerHeight + (document.documentElement.scrollWidth - innerWidth),
    bowlby: probe("'Archivo'", 'serif'), manrope: probe("'Barlow'", 'serif'),
    faces: document.querySelectorAll('.mhw-face').length, art: !!document.querySelector('.mhw-kb img') && document.querySelector('.mhw-kb img').naturalWidth > 0,
    logo: (document.querySelector('.mhw-logo') || {}).naturalWidth > 0, stage: document.querySelector('.mhw').dataset.stage,
    panel: (document.querySelector('.mhw-panel .mhw-label') || {}).textContent, text: document.querySelector('.mhw').innerText };
});

if (process.env.DEBUG) { cur = STATES.done[0]; const { pg } = await open({ width: 1080, height: 1920 }, STATES.done[1]);
  console.log(await pg.evaluate(() => { const c = document.querySelector('.mhw-champs'); const q = s => { const r = document.querySelector(s).getBoundingClientRect(); return s + ' ' + Math.round(r.top) + '-' + Math.round(r.bottom); }; return [q('.mhw-now'), q('.mhw-champs'), q('.mhw-champfaces'), q('.mhw-champname'), q('.mhw-champscore'), getComputedStyle(document.querySelector('.mhw-champname')).fontSize].join(' | '); })); process.exit(0);
  console.log(await pg.evaluate(() => { const e = document.querySelector('.mhw-title'); const r = []; r.push(e.style.fontSize, getComputedStyle(e).fontSize, e.scrollWidth, e.clientWidth, e.className); mhFitAll(); r.push(e.style.fontSize, e.scrollWidth, e.clientWidth); return r.join(' '); })); process.exit(0); }
const SIZES = { portrait: { width: 1080, height: 1920 }, tv: { width: 1920, height: 1080 }, small: { width: 720, height: 1280 } };
for (const [st, [state, sid]] of Object.entries(STATES)) {
  if (process.env.ONLY && process.env.ONLY !== st) continue;
  cur = state;
  for (const [sz, vp] of Object.entries(SIZES)) {
    const { ctx, pg, errs } = await open(vp, sid);
    for (let k = 0; k < 4; k++) {
      const a = await audit(pg);
      const tag = `${st} ${sz} [${a.panel}]`;
      ok(!errs.length, `${tag}: page error ${errs.join(' | ')}`);
      ok(a.stage === st, `${tag}: stage ${a.stage}, wanted ${st}`);
      ok(a.scroll <= 0, `${tag}: scrolls by ${a.scroll}px`);
      ok(!a.bad.length, `${tag}: ${a.bad.slice(0, 6).join('; ')}`);
      ok(a.bowlby && a.manrope, `${tag}: face not drawn (bowlby ${a.bowlby}, manrope ${a.manrope})`);
      ok(a.art && a.logo, `${tag}: painting ${a.art} logo ${a.logo}`);
      ok(a.faces >= 4, `${tag}: only ${a.faces} faces`);
      if (st === 'done') ok(/champions|big score/i.test(a.text), `${tag}: no champions on a finished night`);
      if (st === 'groups') ok(/on court now/i.test(a.text) && /next/i.test(a.text), `${tag}: no ON COURT / NEXT`);
      if (process.env.SHOTS) await pg.screenshot({ path: path.join(OUT, `${st}-${sz}-${k}.png`) });
      if (k < 3) { const before = a.panel; await pg.evaluate(() => dispatchEvent(new Event('mh-wall-next'))); await pg.waitForTimeout(900);
        const n = await pg.evaluate(() => (document.querySelector('.mhw-panel .mhw-label') || {}).textContent); if (n === before) break; }
    }
    await ctx.close();
  }
}

// THE TAKEOVER: a score locked on another phone, then the final
if (!process.env.ONLY || process.env.ONLY === 'flash') {
  cur = clone(groups);
  const { ctx, pg, errs } = await open(SIZES.portrait, ids[6]);
  const n = cur.sessions[6]; const m = n.groupMatches[12];
  m.score = { t1: 6, t2: 2 }; m.winner = 'team1'; m.lossType = 'normal';
  await pg.evaluate(() => dispatchEvent(new Event('mh-wall-poll')));
  await pg.waitForSelector('.mhw-flash', { timeout: 5000 }).catch(() => {});
  await pg.waitForTimeout(1600);
  const f = await pg.evaluate(() => { const e = document.querySelector('.mhw-flash'); return e && { text: e.innerText, score: e.querySelector('.mhw-fscore').innerText.replace(/\s/g, '') }; });
  ok(f && f.score === '6–2', `flash: a locked 6-2 did not take the wall over (${JSON.stringify(f)})`);
  ok(f && /result · group/i.test(f.text), `flash: no RESULT · GROUP kicker`);
  if (process.env.SHOTS) await pg.screenshot({ path: path.join(OUT, 'flash-result.png') });
  const a = await audit(pg); ok(!a.bad.filter(x => !/overlap/.test(x)).length, `flash: ${a.bad.join('; ')}`);
  await pg.waitForTimeout(8400);
  ok(!(await pg.$('.mhw-flash')), 'flash: did not clear after eight seconds');
  // nothing on first load: an existing result is not news
  await ctx.close();
  cur = clone(ko);
  const o2 = await open(SIZES.portrait, ids[5]);
  ok(!(await o2.pg.$('.mhw-flash')), 'flash: fired on first load for results already on the board');
  const k = cur.sessions[5], src = base.sessions[5];
  k.bracket.sf = clone(src.bracket.sf); k.bracket.final = clone(src.bracket.final);
  await o2.pg.evaluate(() => dispatchEvent(new Event('mh-wall-poll')));
  await o2.pg.waitForTimeout(1800);
  const q = await o2.pg.evaluate(() => { const e = document.querySelector('.mhw-flash'); return e && e.innerText; });
  ok(q && /semi-final/i.test(q), `flash: semis not shown first (${q && q.slice(0, 40)})`);
  if (process.env.SHOTS) await o2.pg.screenshot({ path: path.join(OUT, 'flash-semi.png') });
  let fin = null;
  for (let w = 0; w < 30 && !(fin && fin.final); w++) { await o2.pg.waitForTimeout(1000); fin = await o2.pg.evaluate(() => { const e = document.querySelector('.mhw-flash'); return e && { final: e.dataset.final !== undefined, t: e.innerText }; }); }
  await o2.pg.waitForTimeout(1500);
  ok(fin && fin.final, `flash: final not the last takeover (${JSON.stringify(fin)})`);
  if (process.env.SHOTS) await o2.pg.screenshot({ path: path.join(OUT, 'flash-final.png') });
  ok(!errs.length && !o2.errs.length, 'flash: page error ' + [...errs, ...o2.errs].join(' | '));
  await o2.ctx.close();
}

await browser.close(); srv.close();
console.log(fails.length ? `\n${fails.length} FAILED` : '\nwall: all clear');
process.exit(fails.length ? 1 : 0);
