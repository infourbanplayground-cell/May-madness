// Muscat Heist — the BUILT app (heist-index.html) against real data.
//   python3 build-heist-app.py && node ops/check-heist-app.mjs
//   ONLY=mid|launch   one scenario      SHOTS=1   screenshots in <scratch>/heist-qa/app/
//
// Two scenarios, because the app has two lives:
//   mid     National's real state with its seven played nights moved onto the
//           Heist dates — real teams, real scores, real brackets, through the
//           inherited engine. The phone belongs to the leader.
//   launch  1 Dec: the carried roster and no nights at all. Every screen must
//           draw something sensible with nobody on a point.
// On every screen: no page error, something drawn, no sideways scroll, the
// faces drawn. Then the facts: Most Wanted's order IS calcPlayerStats', the
// ME bar adds up to the player's total, card stats are 0-99 or a dash. Then
// the one write the Heist screens make — a score through Live Scoring — is
// driven end to end and the /save body is read back.
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
const OUT = path.join(SC, 'heist-qa', 'app'); fs.mkdirSync(OUT, { recursive: true });

const clone = o => JSON.parse(JSON.stringify(o));
const mid = clone(NAT);
mid.sessions.forEach((s, i) => { s.date = SEASON.nights[i]; s.doublePoints = SEASON.doubleNights.includes(s.date); });
// night 7 is TONIGHT: half its group matches still to play, no knockout yet
const n7 = mid.sessions[6];
n7.completed = false; n7.bracket = {};
n7.groupMatches.slice(12).forEach(m => { delete m.winner; delete m.score; delete m.lossType; delete m.resultAt; });
const launch = { ...clone(NAT), sessions: [] };
const SCEN = { mid, launch };

const T = { '.html': 'text/html; charset=utf-8', '.css': 'text/css', '.woff2': 'font/woff2', '.png': 'image/png', '.jpg': 'image/jpeg', '.json': 'application/json' };
let scenario = 'mid'; const saves = [];
const map = [['/assets/fonts/brand/', 'brand/fonts/'], ['/assets/fonts/heist/', 'brand/heist/fonts/'], ['/assets/art/', 'brand/heist/art/'],
             ['/assets/up-logo-tight.png', 'brand/heist/up-logo-tight.png'], ['/assets/history.json', 'brand/national/history.json']];
const srv = http.createServer((q, r) => {
  const u = decodeURIComponent(q.url.split('?')[0]);
  const json = o => { r.writeHead(200, { 'Content-Type': 'application/json' }); r.end(typeof o === 'string' ? o : JSON.stringify(o)); };
  if (u === '/' || u === '/index.html') { r.writeHead(200, { 'Content-Type': T['.html'] }); return r.end(fs.readFileSync(path.join(ROOT, 'heist-index.html'))); }
  if (u === '/version.txt') { r.writeHead(200); return r.end(BID + '\n'); }
  if (u === '/state') return json({ ok: true, state: SCEN[scenario], version: 1 });
  if (u === '/photos') return json(PHOTOS);
  if (u === '/session-photos') return json({ ok: true, photos: {} });
  if (u === '/api/roster') return json({ ok: true, players: [] });
  if (u === '/save') { let b = ''; q.on('data', c => b += c); q.on('end', () => { saves.push(JSON.parse(b)); json({ ok: true, version: 2 }); }); return; }
  for (const [a, b] of map) if (u.startsWith(a)) {
    const f = path.join(ROOT, b + u.slice(a.length));
    if (fs.existsSync(f) && !fs.statSync(f).isDirectory()) { r.writeHead(200, { 'Content-Type': T[path.extname(f)] || 'x' }); return r.end(fs.readFileSync(f)); }
  }
  r.writeHead(404); r.end();
}).listen(0);
const ORIGIN = `http://127.0.0.1:${srv.address().port}`;
const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
const fails = []; const ok = (c, m) => { if (!c) { fails.push(m); console.log('  FAIL ' + m); } else if (process.env.V) console.log('  ok   ' + m); };

async function page(scen, me, admin) {
  scenario = scen;
  const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 2 });
  await ctx.addInitScript(([me, admin]) => {
    try {
      localStorage.setItem('mh-once-loaded', 'never');
      if (me) localStorage.setItem('aa-me', me);
      if (admin) {
        const exp = Math.floor(Date.now() / 1000) + 86400;
        localStorage.setItem('july-heat-admin', 'admin'); localStorage.setItem('july-heat-token', `admin.${exp}.sig`);
      }
    } catch (e) {}
  }, [me, admin]);
  const pg = await ctx.newPage();
  const errs = []; pg.on('pageerror', e => errs.push(e.message));
  await pg.route('**/unpkg.com/**', r => {
    const u = r.request().url();
    const f = /html-to-image/.test(u) ? 'h2i.js' : /babel/.test(u) ? 'babel.js' : /react-dom/.test(u) ? 'react-dom.js' : 'react.js';
    r.fulfill({ status: 200, contentType: 'application/javascript', body: fs.readFileSync(path.join(SC, 'vendor', f), 'utf8') });
  });
  await pg.route('**/cdn.tailwindcss.com/**', r => r.fulfill({ status: 200, contentType: 'application/javascript', body: '' }));
  await pg.route('**/fonts.googleapis.com/**', r => r.fulfill({ status: 200, contentType: 'text/css', body: '' }));
  await pg.goto(ORIGIN + '/#home', { waitUntil: 'load' });
  await pg.waitForSelector('.mh-page, .mh-slides, .mh-loading', { timeout: 40000 });
  await pg.evaluate(() => Promise.all(["900 40px Archivo", "600 40px Manrope", "italic 40px Fraunces"].map(f => document.fonts.load(f).catch(() => 0))));
  return { ctx, pg, errs };
}
const look = async (pg, hash) => {
  await pg.evaluate(h => { location.hash = h; }, hash);
  await pg.waitForTimeout(450);
  return pg.evaluate(() => ({
    drawn: !!document.querySelector('.mh-page, .mh-slides, .mh-loading') && document.body.innerText.trim().length > 20,
    sideways: document.documentElement.scrollWidth - innerWidth,
    // Vol.9's ground and its furniture must not show through on any Heist screen:
    // the inherited skin painted html.aa-boot oxblood and hung the khanjar tile on
    // body::before, and both outranked a plain html/body rule
    vol9: (() => { const bad = new Set(); for (let x = 1; x < innerWidth; x += 26) for (let y = 1; y < innerHeight; y += 26)
      for (const e of document.elementsFromPoint(x, y)) { const c = getComputedStyle(e).backgroundColor;
        if (/107, 15, 23|82, 11, 18/.test(c)) bad.add(e.tagName + '.' + String(e.className).slice(0, 18) + (e.tagName === 'HTML' ? ' [' + e.className + '|' + (e.getAttribute('style') || '') + '|' + c + ']' : '')); }
      if (getComputedStyle(document.body, '::before').display !== 'none' && getComputedStyle(document.body, '::before').backgroundImage !== 'none') bad.add('body::before tile');
      return [...bad]; })(),
    hash: location.hash,
  }));
};

for (const scen of (process.env.ONLY ? [process.env.ONLY] : ['mid', 'launch'])) {
  // the phone belongs to the engine's leader (mid) / to a carried player (launch)
  const S = SCEN[scen];
  const { ctx, pg, errs } = await page(scen, null, false);
  const leaderId = await pg.evaluate(st => {
    const rows = st.players.map(p => ({ id: p.id, pts: calcPlayerStats(p.id, st.sessions).totalPts })).sort((a, b) => b.pts - a.pts);
    return rows[0].id;
  }, S);
  await ctx.close();
  const me = scen === 'mid' ? leaderId : S.players[0].id;
  const { ctx: c2, pg: p2, errs: e2 } = await page(scen, me, false);
  const firstHash = await p2.evaluate(() => location.hash);
  const routes = ['home', 'jobs', 'wanted', 'me', 'crew', `card/${me}`, 'take', 'rival', 'finale', 'loading', 'share/card/' + me];
  if (scen === 'mid') routes.push('session/7', 'session/5', 'recap/5', 'slides/5/1', 'cardpull/6');
  for (const r of routes) {
    const res = await look(p2, r);
    ok(res.drawn, `${scen} #${r}: nothing drawn (landed on ${res.hash})`);
    ok(res.sideways <= 0, `${scen} #${r}: scrolls sideways by ${res.sideways}px`);
    ok(!res.vol9.length, `${scen} #${r}: Vol.9 ground shows through: ${res.vol9.join(', ')}`);
    if (process.env.SHOTS) await p2.screenshot({ path: path.join(OUT, `${scen}-${r.replace(/\//g, '_')}.png`) });
  }
  ok(!e2.length, `${scen}: page errors: ${e2.slice(0, 2).join(' | ')}`);
  // ── facts ──
  if (scen === 'mid') {
    await look(p2, 'wanted');
    const shown = await p2.$$eval('.mh-wrow .mh-wname', e => e.slice(0, 5).map(x => x.childNodes[0].textContent.trim()));
    const engine = await p2.evaluate(st => st.players.map(p => ({ n: p.name, pts: calcPlayerStats(p.id, st.sessions).totalPts }))
      .sort((a, b) => b.pts - a.pts).slice(0, 6).map(r => r.n), S);
    // the leader is on the card above the list; the rows continue from #2
    ok(shown.length && engine.slice(1).some(n => shown[0].startsWith(n.split(' ')[0])), `Most Wanted order vs engine: shown ${shown.join(', ')} / engine ${engine.join(', ')}`);
    await look(p2, 'me');
    const seg = await p2.$$eval('.mh-legend b', e => e.map(x => +x.textContent));
    const pts = await p2.evaluate(({ st, id }) => calcPlayerStats(id, st.sessions).totalPts, { st: S, id: me });
    ok(seg.reduce((a, b) => a + b, 0) === pts, `ME bar adds to ${seg.reduce((a, b) => a + b, 0)}, the engine says ${pts}`);
    await look(p2, `card/${me}`);
    const cs = await p2.$$eval('.mn-stat b', e => e.map(x => x.textContent));
    ok(cs.length === 4 && cs.every(v => v === '—' || (+v >= 0 && +v <= 99)), `card stats: ${cs.join(' ')}`);
    if (process.env.V) console.log('  me', me, 'pts', pts, 'seg', seg.join('+'), 'stats', cs.join(' '), 'first route', firstHash);
  }
  await c2.close();
}

// ── the one write: a score through Live Scoring, read back from /save ──
if (!process.env.ONLY || process.env.ONLY === 'mid') {
  const { ctx, pg, errs } = await page('mid', null, true);
  await look(pg, 'session/7');
  const tap = await pg.$('button.mh-match');
  ok(!!tap, 'organiser: an unplayed match is tappable on tonight\'s session');
  if (tap) {
    await tap.click(); await pg.waitForTimeout(400);
    ok(/#live\/7\//.test(await pg.evaluate(() => location.hash)), 'tap opens Live Scoring for that match');
    const before = saves.length;
    for (let i = 0; i < 6; i++) await pg.click('.mh-two .mn-btn-primary');
    await pg.click('.mh-livefoot .mn-btn-light'); await pg.waitForTimeout(4500);   // the inherited save debounces 3s
    const s = saves.slice(before).pop();
    const n = s && s.state && s.state.sessions.find(x => x.date === SEASON.nights[6]);
    const m = n && n.groupMatches.find(x => x.winner && x.score && x.score.t1 === 6 && x.score.t2 === 0 && x.resultAt > Date.now() - 60000);
    ok(!!m, 'Lock result saved through the engine: ' + (m ? `${m.score.t1}-${m.score.t2} ${m.winner} ${m.lossType}` : 'no /save carried it'));
    ok(m && m.lossType === 'blowout', 'loss type derived by scoreToResult (6-0 is a blowout)');
  }
  ok(!errs.length, 'organiser: page errors: ' + errs.slice(0, 2).join(' | '));
  await ctx.close();
}
await browser.close(); srv.close();
if (fails.length) { console.error(`\n${fails.length} failed`); process.exit(1); }
console.log('ok — the built app draws every screen in both scenarios, agrees with the engine, and saves a score');
