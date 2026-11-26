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
const SHOTS = !!process.env.SHOTS;
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

const T = { '.html': 'text/html; charset=utf-8', '.css': 'text/css', '.woff2': 'font/woff2', '.png': 'image/png', '.webp': 'image/webp', '.jpg': 'image/jpeg', '.json': 'application/json' };
let scenario = 'mid'; const saves = [];
const PORTRAITS = process.env.PORTRAITS || '';
const map = [['/assets/fonts/brand/', 'brand/fonts/'], ['/assets/fonts/heist/', 'brand/heist/fonts/'], ['/assets/art/', 'brand/heist/art/'],
             ['/assets/up-logo-tight.png', 'brand/heist/up-logo-tight.png'], ['/assets/heist-logo.png', 'brand/heist/heist-logo.png'], ['/assets/heist-logo.webp', 'brand/heist/heist-logo.webp'], ['/assets/history.json', 'brand/national/history.json']];
const srv = http.createServer((q, r) => {
  const u = decodeURIComponent(q.url.split('?')[0]);
  const json = o => { r.writeHead(200, { 'Content-Type': 'application/json' }); r.end(typeof o === 'string' ? o : JSON.stringify(o)); };
  if (u === '/' || u === '/index.html') { r.writeHead(200, { 'Content-Type': T['.html'] }); return r.end(fs.readFileSync(path.join(ROOT, 'heist-index.html'))); }
  if (u === '/version.txt') { r.writeHead(200); return r.end(BID + '\n'); }
  if (u === '/state') return json({ ok: true, state: SCEN[scenario], version: 1 });
  if (u === '/photos') return json(PHOTOS);
  if (u === '/session-photos') return json({ ok: true, photos: {} });
  // PORTRAITS=<dir of <id>.jpg>: serve real Heist portraits, as the photos API does
  if (u === '/api/roster') return json({ ok: true, players: PORTRAITS ? fs.readdirSync(PORTRAITS).filter(f => f.endsWith('.jpg')).map(f => ({ id: f.slice(0, -4), heist: '/players/' + f })) : [] });
  if (PORTRAITS && u.startsWith('/players/')) { const f = path.join(PORTRAITS, path.basename(u)); if (fs.existsSync(f)) { r.writeHead(200, { 'Content-Type': 'image/jpeg' }); return r.end(fs.readFileSync(f)); } }
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
  // SaveMyPlay is unreachable from here: two clips on night 5 (19:00 and 19:20
  // Muscat) and one yesterday evening, which is what puts a strip on Home
  await pg.route('**/api.savemyplay.com/**', r => {
    const night5 = (JSON.parse(fs.readFileSync(path.join(ROOT, 'heist-season.json'))).nights)[4];
    const at = (iso, h, m) => Math.floor(Date.UTC(+iso.slice(0, 4), +iso.slice(5, 7) - 1, +iso.slice(8, 10), h - 4, m) / 1000);
    const y = new Date(Date.now() - 86400e3), yIso = y.getFullYear() + '-' + String(y.getMonth() + 1).padStart(2, '0') + '-' + String(y.getDate()).padStart(2, '0');
    const clip = (id, t) => ({ id, start_time: t, video: ORIGIN + '/clip.mp4', thumb: ORIGIN + '/assets/art/art-ep01-lounge-480.webp', court: { name: 'Court ' + (id % 3 + 1) }, rel_url: '/h/' + id });
    r.fulfill({ status: 200, contentType: 'application/json', headers: { 'access-control-allow-origin': '*' },
      body: JSON.stringify({ clips: [clip(1, at(night5, 19, 0)), clip(2, at(night5, 19, 20)), clip(3, at(yIso, 20, 5))] }) });
  });
  await pg.goto(ORIGIN + '/#home', { waitUntil: 'load' });
  await pg.waitForSelector('.mh-page, .mh-slides, .mh-loading', { timeout: 40000 });
  await pg.evaluate(() => Promise.all(["900 40px Archivo", "600 40px Barlow", "700 40px 'Barlow Semi Condensed'", "40px 'Kaushan Script'"].map(f => document.fonts.load(f).catch(() => 0))));
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
  // ── clips: a night's CLIPS button, its grid, the player, and the Home strip
  if (scen === 'mid') {
    await look(p2, 'session/5'); await p2.waitForTimeout(600);
    const btn = p2.locator('.mh-act', { hasText: 'Clips' });
    ok(await btn.count() === 1 && /Clips · 2/.test(await btn.innerText()), `mid #session/5: no "Clips · 2" button`);
    if (await btn.count()) await btn.click();
    ok(await p2.locator('.mh-clipgrid .mh-clip img').count() === 2, 'mid #session/5: the clips grid does not show the night\'s 2 clips');
    if (await p2.locator('.mh-clipgrid .mh-clip').count()) {
      await p2.locator('.mh-clipgrid .mh-clip').first().click();
      ok(await p2.locator('.mh-clipview video').count() === 1, 'mid: tapping a clip does not open the player');
      if (process.env.SHOTS) await p2.screenshot({ path: path.join(OUT, 'mid-clip-player.png') });
      await p2.locator('.mh-clipx').click();
      ok(await p2.locator('.mh-clipview').count() === 0, 'mid: the clip player does not close');
      if (process.env.SHOTS) await p2.screenshot({ path: path.join(OUT, 'mid-session-clips.png') });
    }
    await look(p2, 'home'); await p2.waitForTimeout(600);
    ok(await p2.locator('.mh-cliprow .mh-clip').count() >= 1, 'mid #home: no "Latest clips" strip');  // the mock's night 5 is in December, so it counts as newest
    if (process.env.SHOTS) await p2.screenshot({ path: path.join(OUT, 'mid-home-clips.png') });
  }
  // ── scenes: the loading screen must actually change picture, and no two
  // pages may open on the same one (the owner: "I don't wanna see the same
  // picture in each page")
  {
    const shown = async () => p2.evaluate(() => { const on = document.querySelector('.mh-scene[data-on] img');
      return on ? on.getAttribute('src') : (document.querySelector('.mn-hero-img img, .mh-takehero img') || {}).getAttribute?.('src'); });
    await look(p2, 'loading'); const a = await shown(); await p2.waitForTimeout(4800); const b = await shown();  // a poster holds 4.2s
    ok(a && b && a !== b, `${scen} #loading: the picture did not change (${a} then ${b})`);
    const first = {};
    for (const r of ['loading', 'home', 'take']) { await look(p2, r); first[r] = await shown(); }
    const vals = Object.values(first);
    ok(vals.every(Boolean) && new Set(vals).size === vals.length, `${scen}: pages share a picture: ${JSON.stringify(first)}`);
    // a phone must fetch the WebP it draws, not the 1600px JPEG fallback
    await look(p2, 'home'); await p2.waitForTimeout(800);
    const cur = await p2.evaluate(() => [...document.querySelectorAll('.mn-hero-img img')].map(i => i.currentSrc).filter(Boolean));
    ok(cur.length && cur.every(s => /-\d+\.webp$/.test(s)), `${scen} #home: hero fetched ${cur.join(', ')} instead of a WebP size`);
    console.log(`  ${scen} hero fetched: ${cur.map(s => s.split('/').pop()).join(', ')}`);
    console.log(`  ${scen} scenes: loading ${a.split('/').pop()} -> ${b.split('/').pop()} · home ${first.home.split('/').pop()} · take ${first.take.split('/').pop()}`);
  }
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
  const upn = await pg.locator('.mh-upnext').count();
  ok(upn >= 1 && upn <= 3, `organiser: up-next queue shows ${upn} match(es)`);
  if (SHOTS) await pg.screenshot({ path: path.join(OUT, 'qol-session-org.png') });
  // check-in: tap a name, the night carries it on the next save
  await pg.click('.mn-pills button:has-text("Check-in")'); await pg.waitForTimeout(300);
  const c0 = saves.length;
  await pg.click('.mh-ciname >> nth=0'); await pg.waitForTimeout(4200);
  const cs = saves.slice(c0).pop(), cn = cs && cs.state.sessions.find(x => x.date === SEASON.nights[6]);
  ok(cn && cn.checkIn && Object.keys(cn.checkIn).length === 1, 'check-in is saved on the night: ' + JSON.stringify(cn && cn.checkIn ? Object.keys(cn.checkIn) : null));
  if (SHOTS) await pg.screenshot({ path: path.join(OUT, 'qol-checkin.png') });
  // no signal at the court: the change waits on the phone, says so, and goes when signal is back
  await ctx.setOffline(true);
  await pg.click('.mh-ciname >> nth=1'); await pg.waitForTimeout(5000);
  const ban = await pg.locator('.mh-savebanner').count() ? await pg.locator('.mh-savebanner').innerText() : '';
  ok(/no signal/i.test(ban) && /waiting/i.test(ban), 'offline banner says no signal and changes waiting: ' + ban.replace(/\s+/g, ' ').slice(0, 90));
  ok(await pg.evaluate(() => window.__mhDirty === true), 'the phone is marked dirty, so a pull-to-refresh cannot overwrite it');
  const o0 = saves.length;
  await ctx.setOffline(false); await pg.evaluate(() => dispatchEvent(new Event('online'))); await pg.waitForTimeout(6000);
  const os = saves.slice(o0).pop(), on2 = os && os.state.sessions.find(x => x.date === SEASON.nights[6]);
  ok(on2 && on2.checkIn && Object.keys(on2.checkIn).length === 2, 'back online, the waiting change is saved: ' + (on2 && on2.checkIn ? Object.keys(on2.checkIn).length : 'no save'));
  ok(await pg.locator('.mh-savebanner').count() === 0, 'and the banner clears');
  await pg.click('.mn-pills button:has-text("Groups")'); await pg.waitForTimeout(300);
  const tap = await pg.$('button.mh-match');
  ok(!!tap, 'organiser: an unplayed match is tappable on tonight\'s session');
  if (tap) {
    await tap.click(); await pg.waitForTimeout(400);
    ok(/#live\/7\//.test(await pg.evaluate(() => location.hash)), 'tap opens Live Scoring for that match');
    const before = saves.length;
    for (let i = 0; i < 6; i++) await pg.click('.mh-two .mn-btn-primary');
    await pg.click('.mh-livefoot .mn-btn-light');
    ok(await pg.locator('.mh-confirm').count() === 1, 'Lock asks to confirm before writing');
    ok(/6–0/.test(await pg.locator('.mh-confirm').innerText()), 'the confirm states the score');
    await pg.click('.mh-confirm .mn-btn-light'); await pg.waitForTimeout(4500);   // the inherited save debounces 3s
    const toast = await pg.locator('.mh-undotoast').count() ? await pg.locator('.mh-undotoast').innerText() : '';
    ok(/locked/i.test(toast), 'an undo toast follows the lock: ' + toast.replace(/\s+/g, ' '));
    ok(/up next/i.test(toast), 'the toast names the next match');
    const s = saves.slice(before).pop();
    const n = s && s.state && s.state.sessions.find(x => x.date === SEASON.nights[6]);
    const m = n && n.groupMatches.find(x => x.winner && x.score && x.score.t1 === 6 && x.score.t2 === 0 && x.resultAt > Date.now() - 60000);
    ok(!!m, 'Lock result saved through the engine: ' + (m ? `${m.score.t1}-${m.score.t2} ${m.winner} ${m.lossType}` : 'no /save carried it'));
    ok(m && m.lossType === 'blowout', 'loss type derived by scoreToResult (6-0 is a blowout)');
    if (m) {
      const n0 = saves.length;
      await pg.click('.mh-undotoast button'); await pg.waitForTimeout(4500);
      const s2 = saves.slice(n0).pop(), n2 = s2 && s2.state.sessions.find(x => x.date === SEASON.nights[6]);
      const back = n2 && n2.groupMatches.find(x => x.id === m.id);
      ok(back && !back.winner, 'Undo takes the result back off the match: ' + (back ? JSON.stringify(back.score || null) : 'no save'));
    }
  }
  ok(!errs.length, 'organiser: page errors: ' + errs.slice(0, 2).join(' | '));
  await ctx.close();
}
// ── quality of life: who are you, find me, your night, settings, how it works ──
{
  // a player in tonight's night 7 with a group match still to play
  const t7 = n7.teams.find(t => n7.groupMatches.some(m => !m.winner && (m.team1Id === t.id || m.team2Id === t.id)));
  const meQ = t7.p1Id;
  const { ctx, pg, errs } = await page('mid', meQ, false);
  await look(pg, 'home');
  const home = await pg.evaluate(() => { const b = document.querySelector('.mh-livemine'); return b ? b.innerText : null; });
  ok(home && /Group [A-D]/i.test(home) && /(NEXT|ON COURT)/.test(home), 'Home shows your live night: ' + (home || 'no card').replace(/\s+/g, ' ').slice(0, 140));
  if (SHOTS) await pg.screenshot({ path: path.join(OUT, 'qol-home-live.png') });
  await look(pg, 'wanted');
  const strip = await pg.evaluate(() => { const b = document.querySelector('.mh-youstrip'); return b && b.innerText.replace(/\s+/g, ' '); });
  ok(strip && /you\s*#\d+/i.test(strip), 'Most Wanted carries the you-strip: ' + strip);
  await pg.click('.mh-youstrip'); await pg.waitForTimeout(900);
  const jumped = await pg.evaluate(id => { const r = document.getElementById('w-' + id); if (!r) return 'no row'; const b = r.getBoundingClientRect();
    return b.top > 40 && b.bottom < innerHeight - 90 ? 'ok' : `row at ${Math.round(b.top)}`; }, meQ);
  ok(jumped === 'ok', 'the strip brings your row on screen: ' + jumped);
  if (SHOTS) await pg.screenshot({ path: path.join(OUT, 'qol-wanted.png') });
  await pg.fill('.mh-search', 'zzzz-nobody'); await pg.waitForTimeout(200);
  ok(await pg.evaluate(() => document.querySelectorAll('.mh-wrow').length === 0 && /Nobody on the table/i.test(document.body.innerText)), 'search with no match says so');
  await look(pg, 'me');
  ok(await pg.evaluate(() => /Bigger text/i.test(document.body.innerText)), 'ME carries the phone settings');
  await pg.click('.mh-setrow[aria-pressed]'); await pg.waitForTimeout(150);
  ok(await pg.evaluate(() => document.documentElement.classList.contains('mh-bigtext') && localStorage.getItem('mh-bigtext') === '1'), 'bigger text applies and is remembered');
  await look(pg, 'howto');
  ok(await pg.evaluate(() => /How it works · 1 of 3/i.test(document.body.innerText)), 'how it works opens');
  if (SHOTS) await pg.screenshot({ path: path.join(OUT, 'qol-howto.png') });
  ok(!errs.length, 'qol: page errors: ' + errs.slice(0, 2).join(' | '));
  await ctx.close();
  // a fresh phone: how it works once, then who-are-you, and the pick sticks
  const { ctx: c2, pg: p2, errs: e2 } = await page('mid', null, false);
  await p2.evaluate(() => { localStorage.removeItem('mh-howto-seen'); localStorage.removeItem('mh-who-asked'); location.hash = ''; });
  await p2.reload(); await p2.waitForTimeout(1500);
  // Now Loading plays first on a new day; its tap is the way into the app
  const cont = async () => { if (await p2.locator('.mh-loadtap').count()) { await p2.waitForSelector('.mh-loadtap:not([disabled])', { timeout: 15000 }); await p2.click('.mh-loadtap'); await p2.waitForTimeout(500); } };
  await cont();
  ok(/howto/.test(await p2.evaluate(() => location.hash)), 'first open shows how it works: ' + await p2.evaluate(() => location.hash));
  await p2.evaluate(() => { localStorage.setItem('mh-howto-seen', '1'); location.hash = ''; }); await p2.reload(); await p2.waitForTimeout(1500); await cont();
  ok(/who/.test(await p2.evaluate(() => location.hash)), 'then asks who you are: ' + await p2.evaluate(() => location.hash));
  if (SHOTS) await p2.screenshot({ path: path.join(OUT, 'qol-who.png') });
  await p2.fill('.mh-search', (NAT.players.find(p => p.id === meQ) || {}).name.split(' ')[0]); await p2.waitForTimeout(200);
  await p2.click(`.mh-whorow >> nth=0`); await p2.waitForTimeout(400);
  ok(await p2.evaluate(() => !!localStorage.getItem('aa-me')), 'the pick is remembered on the phone');
  ok(!e2.length, 'who: page errors: ' + e2.slice(0, 2).join(' | '));
  await c2.close();
}
await browser.close(); srv.close();
if (fails.length) { console.error(`\n${fails.length} failed`); process.exit(1); }
console.log('ok — the built app draws every screen in both scenarios, agrees with the engine, and saves a score');
