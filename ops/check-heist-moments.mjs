// Muscat Heist phase 4: the moment STATES no screenshot shows — tier up / hold /
// down copy, rep up at the top level, the rival screen at #1, the finale
// before / during / after, the Boss Kill row following its config flag, the
// loading screen refusing a tap until ready, and once-per-device. Each state
// is made by editing the preview's data in the page and re-rendering.
//   node ops/check-heist-moments.mjs
import { chromium } from 'playwright'; import fs from 'fs'; import http from 'http'; import path from 'path';
const ROOT = path.resolve(path.dirname(new URL(import.meta.url).pathname), '..');
const SC = '/tmp/claude-0/-home-user-May-madness/0e44f0ad-a683-5f0d-9de6-9459ae328963/scratchpad';
const T = { '.html': 'text/html', '.css': 'text/css', '.woff2': 'font/woff2', '.jpg': 'image/jpeg', '.png': 'image/png' };
const srv = http.createServer((q, r) => { const f = path.join(ROOT, decodeURIComponent(q.url.split('?')[0])); if (!fs.existsSync(f) || fs.statSync(f).isDirectory()) { r.writeHead(404); return r.end(); } r.writeHead(200, { 'Content-Type': T[path.extname(f)] || 'x' }); r.end(fs.readFileSync(f)); }).listen(0);
const b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
const fails = []; const ok = (c, m) => { console.log((c ? '  ok   ' : '  FAIL ') + m); if (!c) fails.push(m); };
const pg = await (await b.newContext({ viewport: { width: 375, height: 812 } })).newPage();
const errs = []; pg.on('pageerror', e => errs.push(e.message));
await pg.route('**/unpkg.com/**', r => { const u = r.request().url(); const f = /babel/.test(u) ? 'babel.js' : /react-dom/.test(u) ? 'react-dom.js' : 'react.js'; r.fulfill({ status: 200, contentType: 'application/javascript', body: fs.readFileSync(path.join(SC, 'vendor', f), 'utf8') }); });
await pg.goto(`http://127.0.0.1:${srv.address().port}/brand/heist/preview.html#home`); await pg.waitForSelector('.mh-page');
const ORIG = await pg.evaluate(() => JSON.stringify(window.MH_PREVIEW));
// edit the data, then re-route so the screen re-renders from it
async function show(hash, edit) {
  await pg.evaluate(([o, e]) => { window.MH_PREVIEW = JSON.parse(o); if (e) new Function('D', 'S', e)(window.MH_PREVIEW, window.MH_SEASON); location.hash = 'x'; }, [ORIG, edit || '']);
  await pg.evaluate(h => { location.hash = h; }, hash); await pg.waitForTimeout(250);
  return pg.evaluate(() => document.body.innerText.replace(/\s+/g, ' '));
}
let t;
t = await show('cardpull/5'); ok(/TIER UP: LEGEND/i.test(t) && /Upgraded from Elite · top of the table/i.test(t), 'tier up: copy + line');
t = await show('cardpull/5', 'D.moments[1].from="legend"'); ok(/HOLDING LEGEND/i.test(t) && /Still Legend/i.test(t), 'holding: copy');
t = await show('cardpull/5', 'D.moments[1]={type:"tierUp",playerId:"p04",from:"elite",to:"pro",session:5}'); ok(/TIER DOWN: PRO/i.test(t) && /Down from Elite · #4 on the table/i.test(t), 'tier down: copy + rank');
t = await show('repup/p05'); ok(/MOSSA IS RISING/i.test(t) && /80 pts · 10 to Known/i.test(t), 'rep up: 10 to Known derived (18 x 5 - 80)');
t = await show('repup/p05', 'D.moments[0].to="legend";D.moments[0].points=104'); ok(/Top rep reached/i.test(t), 'rep up to Legend: "Top rep reached"');
t = await show('rival'); ok(/YOUR RIVAL/i.test(t) && /2 PTS TO SETTLE IT/i.test(t) && /1–1/i.test(t), 'rival: gap 2 from points, h2h 1–1');
t = await show('rival', 'D.players[4].points=70'); ok(/12 PTS TO SETTLE IT/i.test(t), 'rival: gap follows the data (82-70)');
t = await show('rival', 'D.meId="p01"'); ok(/#2 CHASING/i.test(t) && /HAMED/i.test(t) && /11 PTS IN HAND/i.test(t), 'at #1: #2 chasing, 11 in hand');
t = await show('settled'); ok(/#4 ▲1/i.test(t) && /mossa 86 · Baraa 84/i.test(t) && /NOOH AMRI 4 pts ahead/i.test(t), 'settled: rank and next rival recomputed');
t = await show('settled', 'D.moments[2].points=[91,84]'); ok(/#3 ▲2/i.test(t) && /HAMED AMRI 2 pts ahead/i.test(t), 'settled: recomputed when the points change');
t = await show('finale'); ok(/SIGN UP FOR THE FINALE/i.test(t) && /11 \/ 11/i.test(t) && !/\+3/i.test(t), 'finale before: sign up, lead 11/11, no +3 row');
t = await show('finale', 'D.sessions[8].state="live";D.finale.leadAtStart=14'); ok(/LIVE · OPEN/i.test(t) && /11 \/ 14/i.test(t), 'finale during: LIVE · OPEN, lead now / at start');
t = await show('finale', 'D.sessions[8].state="done"'); ok(/FULL RESULTS/i.test(t), 'finale after: FULL RESULTS');
t = await show('finale', 'S.bossKillBonus.enabled=true'); ok(/\+3 Beat a top-3 team/i.test(t), 'Boss Kill row only when enabled');
await pg.evaluate(() => { window.MH_SEASON.bossKillBonus.enabled = false; });
// loading: a tap before the data is ready does nothing; after it, Home
t = await show('loading/64'); ok(await pg.isDisabled('.mh-loadtap'), 'loading: not tappable before ready');
ok(/Baraa is 2 points ahead of you/i.test(t), 'loading: personal tip filled from the rival');
await pg.evaluate(() => { location.hash = 'loading'; }); await pg.waitForTimeout(1500);
ok(!(await pg.isDisabled('.mh-loadtap')), 'loading: tappable once ready and 1.2s passed');
await pg.click('.mh-loadtap'); await pg.waitForTimeout(200); ok(await pg.evaluate(() => location.hash === '#home'), 'loading: tap -> Home');
ok(await pg.evaluate(() => { const o = mhOnce('loaded', '2026-12-21'); const a = o.due(); o.seen(); const b2 = o.due(); const c = mhOnce('loaded', '2026-12-23').due(); return a && !b2 && c; }), 'loading: once per device per day');
ok(await pg.evaluate(() => { const o = mhOnce('card', 'p05/5'); const a = o.due(); o.seen(); return a && !o.due() && mhOnce('card', 'p05/6').due(); }), 'card pull: once per player per session');
ok(!errs.length, 'no page errors' + (errs.length ? ': ' + errs[0] : ''));
await b.close(); srv.close(); if (fails.length) process.exit(1);
