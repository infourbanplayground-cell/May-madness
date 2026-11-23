// Muscat Heist player-photos page: drives heist-photos/index.html against the
// real heist-api/api.js. Locally: three mock upstreams + the API + a front
// server on :8099 (see the session notes); BASE= points it elsewhere.
//   node ops/check-heist-photos.mjs
import { chromium } from 'playwright'; import fs from 'fs';
const SC = '/tmp/claude-0/-home-user-May-madness/0e44f0ad-a683-5f0d-9de6-9459ae328963/scratchpad';
const BASE = process.env.BASE || 'http://127.0.0.1:8099', PIN = process.env.PIN || '4242';
const PUB = process.env.PUB || '/var/www/heist.urbanpadel.om/public/players/';
const b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
const fails = []; const ok = (c, m) => { console.log((c ? '  ok   ' : '  FAIL ') + m); if (!c) fails.push(m); };
const pg = await (await b.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 2 })).newPage();
const errs = []; pg.on('pageerror', e => errs.push(e.message));
await pg.goto(BASE + '/photos/'); await pg.waitForSelector('.card'); await pg.evaluate(() => document.fonts.ready);
ok(await pg.$$eval('.card', e => e.length) > 100, 'playing-now grid renders (' + await pg.$$eval('.card', e => e.length) + ')');
await pg.screenshot({ path: SC + '/photos-page.png' });
ok(await pg.evaluate(() => document.documentElement.scrollWidth <= innerWidth), 'no sideways scroll at 390');
ok(await pg.evaluate(() => [...document.querySelectorAll('button,a,label.btn')].filter(e => e.offsetParent).every(e => { const r = e.getBoundingClientRect(); return r.height >= 44; })), 'every visible control at least 44px tall');
await pg.click('.card'); ok(await pg.isVisible('#dlg'), 'tapping a player opens the sheet');
ok(!(await pg.isVisible('#pick')), 'upload hidden until signed in');
await pg.click('#close');
await pg.fill('#pin', '0000'); await pg.click('#in'); await pg.waitForTimeout(400); ok(/wrong PIN/.test(await pg.textContent('#inMsg')), 'wrong PIN refused');
await pg.fill('#pin', PIN); await pg.click('#in'); await pg.waitForTimeout(400); ok(/Signed in/.test(await pg.textContent('#auth')), 'right PIN signs in');
ok(!(await pg.isVisible('#dlg')), 'signing in does not reopen a closed sheet');
const png = await pg.evaluate(() => { const c = document.createElement('canvas'); c.width = 1024; c.height = 1536; const x = c.getContext('2d'); x.fillStyle = '#F26B5B'; x.fillRect(0, 0, 1024, 1536); x.fillStyle = '#2FB7B0'; x.fillRect(300, 200, 424, 500); return c.toDataURL('image/png'); });
fs.mkdirSync(SC + '/hapi/batch', { recursive: true }); fs.writeFileSync(SC + '/hapi/gpt.png', Buffer.from(png.split(',')[1], 'base64'));
await pg.click('.card'); ok(await pg.isVisible('#pick'), 'upload offered once signed in');
await pg.setInputFiles('#file', SC + '/hapi/gpt.png'); await pg.waitForTimeout(300);
ok(await pg.isVisible('#cropRow'), 'a 2:3 image (ChatGPT\'s shape) offers the crop slider');
await pg.screenshot({ path: SC + '/photos-sheet.png' });
await pg.click('#save'); await pg.waitForTimeout(900);
ok(/Saved/.test(await pg.textContent('#dlgMsg')), 'saved: ' + await pg.textContent('#dlgMsg'));
const id = await pg.evaluate(() => current.id);
const f = PUB + id + '.jpg';
if (!process.env.BASE) {
  ok(fs.existsSync(f), 'file on disk');
  const buf = fs.readFileSync(f); let i = 2, dim = null;
  while (i < buf.length) { const m = buf[i + 1], l = buf.readUInt16BE(i + 2); if (m >= 0xc0 && m <= 0xcf && ![0xc4, 0xc8, 0xcc].includes(m)) { dim = [buf.readUInt16BE(i + 7), buf.readUInt16BE(i + 5)]; break; } i += 2 + l; }
  ok(dim && dim[0] === 1080 && dim[1] === 1350, 'stored at 1080x1350 (' + dim + ')');
}
const served = await pg.evaluate(async id => { const p = (await (await fetch('/api/roster')).json()).players.find(x => x.id === id); const r = await fetch(p.heist); return r.ok && r.headers.get('content-type'); }, id);
ok(/jpeg/.test(served || ''), 'the saved photo is served: ' + served);
await pg.click('#close');
for (const n of ['Hamed Amri', 'Mohammed', 'Nobody Here']) fs.copyFileSync(SC + '/hapi/gpt.png', SC + '/hapi/batch/' + n + '.png');
await pg.setInputFiles('#batch', ['Hamed Amri', 'Mohammed', 'Nobody Here'].map(n => SC + '/hapi/batch/' + n + '.png')); await pg.waitForTimeout(2500);
const log = await pg.textContent('#batchLog');
ok(/✓ Hamed Amri.png → Hamed Amri/.test(log) && /Mohammed.png: matches/.test(log) && /Nobody Here.png: no player/.test(log), 'batch: matched / ambiguous refused / unknown refused');
const r1 = await pg.evaluate(async id => (await fetch('/api/photo/' + id, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ image: 'data:image/jpeg;base64,AAAA' }) })).status, id);
ok(r1 === 401, 'upload without a token refused: ' + r1);
const r2 = await pg.evaluate(async id => { const c = document.createElement('canvas'); c.width = 500; c.height = 500; return (await fetch('/api/photo/' + id, { method: 'POST', headers: { 'Content-Type': 'application/json', Authorization: 'Bearer ' + token }, body: JSON.stringify({ image: c.toDataURL('image/jpeg') }) })).json(); }, id);
ok(!r2.ok && /1080x1350/.test(r2.error), 'wrong size refused: ' + r2.error);
// clean up: remove both test uploads through the page's own API
for (const who of [id, await pg.evaluate(() => players.find(p => p.name === 'Hamed Amri').id)])
  await pg.evaluate(async i => fetch('/api/photo/' + i, { method: 'DELETE', headers: { Authorization: 'Bearer ' + token } }), who);
const left = await pg.evaluate(async () => (await (await fetch('/api/roster')).json()).players.filter(p => p.heist).length);
ok(left === 0, 'test uploads removed (' + left + ' left)');
ok(!errs.length, 'no page errors ' + errs.join());
await b.close(); if (fails.length) process.exit(1);
