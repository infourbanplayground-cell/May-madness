// Muscat Heist — the CHAMPION ARTWORK upload (heist-photos "Knockout cards" +
// heist-api /api/loot), end to end with nothing on the network.
//   node ops/check-heist-loot-art.mjs
//
// Starts the REAL heist-api/api.js on a spare port with mock upstreams on 3011
// (National: roster), 3013 (Heist: the season, one night played) and a front
// server that serves the page and proxies /api like the vhost does. Then:
//   - the night's two champions are listed, nobody else
//   - upload needs the PIN; a 2:3 picture offers the crop; Save stores a
//     1080x1350 JPEG named ep01-<id>.jpg and /api/loot lists it
//   - art for somebody who did NOT win that night is refused by the API
//   - Remove moves it to history and the card goes back to automatic
// The API writes /var/www/heist.urbanpadel.om/public/loot as on the server;
// this cleans up after itself.
import { chromium } from 'playwright';
import { spawn } from 'child_process';
import fs from 'fs';
import http from 'http';
import path from 'path';

const ROOT = path.resolve(path.dirname(new URL(import.meta.url).pathname), '..');
const SC = '/tmp/claude-0/-home-user-May-madness/0e44f0ad-a683-5f0d-9de6-9459ae328963/scratchpad';
const SEASON = JSON.parse(fs.readFileSync(path.join(ROOT, 'heist-season.json'), 'utf8'));
const LOOT = '/var/www/heist.urbanpadel.om/public/loot';
const PIN = '4242', API = 3912;
const players = [['a1', 'Hamed Amri'], ['a2', 'Hassan Salhi'], ['b1', 'Amjad K'], ['b2', 'Majdi R'], ['c1', 'Other One']].map(([id, name]) => ({ id, name }));
const heist = { players, sessions: [{ id: 's1', date: SEASON.nights[0], completed: true,
  teams: [{ id: 't1', p1Id: 'a1', p2Id: 'a2' }, { id: 't2', p1Id: 'b1', p2Id: 'b2' }],
  bracket: { final: { team1Id: 't1', team2Id: 't2', winner: 'team1', score: { t1: 9, t2: 7 } } } }] };
const mock = (port, body) => http.createServer((q, r) => { r.writeHead(200, { 'Content-Type': 'application/json' }); r.end(JSON.stringify(body(q.url))); }).listen(port, '127.0.0.1');
const up = [mock(3011, u => u === '/state' ? { state: { players, sessions: [] } } : {}), mock(3013, () => ({ ok: true, state: heist }))];

// the API, with the season beside it the way the deploy puts it there
const dir = fs.mkdtempSync(path.join(SC, 'lootapi-'));
fs.copyFileSync(path.join(ROOT, 'heist-api/api.js'), path.join(dir, 'api.js'));
fs.copyFileSync(path.join(ROOT, 'heist-season.json'), path.join(dir, 'heist-season.json'));
fs.symlinkSync(fs.existsSync('/opt/national-api/node_modules') ? '/opt/national-api/node_modules' : path.join(SC, 'hapi/node_modules'), path.join(dir, 'node_modules'), 'dir');
const before = fs.existsSync(LOOT) ? fs.readdirSync(LOOT) : [];
const api = spawn('node', ['api.js'], { cwd: dir, env: { ...process.env, PORT: String(API), ADMIN_PIN: PIN, TOKEN_SECRET: 'test' }, stdio: 'pipe' });
await new Promise(ok => { api.stdout.on('data', d => /Heist API/.test(d) && ok()); setTimeout(ok, 4000); });

const front = http.createServer((q, r) => {
  const u = q.url.split('?')[0];
  if (u.startsWith('/api/')) {
    const p = http.request({ host: '127.0.0.1', port: API, path: q.url, method: q.method, headers: q.headers }, pr => { r.writeHead(pr.statusCode, pr.headers); pr.pipe(r); });
    return q.pipe(p);
  }
  const f = u.startsWith('/loot/') ? path.join(LOOT, path.basename(u)) : u === '/photos/' ? path.join(ROOT, 'heist-photos/index.html')
    : u === '/photos/style.txt' ? path.join(ROOT, 'heist-photos/style.txt') : null;
  if (f && fs.existsSync(f)) { r.writeHead(200, { 'Content-Type': f.endsWith('.jpg') ? 'image/jpeg' : f.endsWith('.html') ? 'text/html' : 'text/plain' }); return r.end(fs.readFileSync(f)); }
  r.writeHead(404); r.end();
}).listen(0);
const BASE = `http://127.0.0.1:${front.address().port}`;

const fails = []; const ok = (c, m) => { console.log((c ? '  ok   ' : '  FAIL ') + m); if (!c) fails.push(m); };
const b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
try {
  const pg = await (await b.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 1 })).newPage();
  const errs = []; pg.on('pageerror', e => errs.push(e.message)); pg.on('dialog', d => d.accept());
  await pg.goto(BASE + '/photos/'); await pg.waitForSelector('.champ', { timeout: 15000 });
  const names = await pg.$$eval('.champ b', e => e.map(x => x.textContent));
  ok(names.join() === 'Hamed Amri,Hassan Salhi', 'night 1 lists its two champions: ' + names.join(', '));
  ok(await pg.locator('#lootList input[type=file]').count() === 0, 'no upload before signing in');
  await pg.fill('#pin', PIN); await pg.click('#in'); await pg.waitForTimeout(500);
  ok(await pg.locator('#lootList input[type=file]').count() === 2, 'upload offered for each champion once signed in');
  const png = await pg.evaluate(() => { const c = document.createElement('canvas'); c.width = 1024; c.height = 1536; const x = c.getContext('2d');
    x.fillStyle = '#FFC24A'; x.fillRect(0, 0, 1024, 1536); x.fillStyle = '#FF2D78'; x.fillRect(260, 200, 500, 600); return c.toDataURL('image/png'); });
  const pf = path.join(dir, 'art.png'); fs.writeFileSync(pf, Buffer.from(png.split(',')[1], 'base64'));
  await pg.setInputFiles('[data-pick="1/a1"]', pf); await pg.waitForTimeout(300);
  ok(await pg.locator('[data-crop="1/a1"]').count() === 1, 'a 2:3 picture offers the crop');
  ok(await pg.evaluate(() => [...document.querySelectorAll('#lootList button, #lootList label.btn')].filter(e => e.offsetParent).every(e => e.getBoundingClientRect().height >= 44)), 'every loot control at least 44px');
  await pg.screenshot({ path: path.join(SC, 'loot-art-staged.png'), fullPage: true });
  await pg.click('[data-save="1/a1"]'); await pg.waitForTimeout(900);
  const f = path.join(LOOT, 'ep01-a1.jpg');
  ok(fs.existsSync(f), 'stored as ep01-a1.jpg');
  if (fs.existsSync(f)) {
    const buf = fs.readFileSync(f); let i = 2, dim = null;
    while (i < buf.length) { const m = buf[i + 1], l = buf.readUInt16BE(i + 2); if (m >= 0xc0 && m <= 0xcf && ![0xc4, 0xc8, 0xcc].includes(m)) { dim = [buf.readUInt16BE(i + 7), buf.readUInt16BE(i + 5)]; break; } i += 2 + l; }
    ok(dim && dim[0] === 1080 && dim[1] === 1350, 'at 1080x1350 (' + dim + ')');
  }
  const list = await pg.evaluate(async () => (await (await fetch('/api/loot')).json()).art);
  ok(/^\/loot\/ep01-a1\.jpg\?v=\d+$/.test(list['1/a1'] || ''), '/api/loot lists it for the app: ' + list['1/a1']);
  ok(await pg.locator('.champ[data-k="1/a1"] img[src^="/loot/"]').count() === 1, 'the page shows the uploaded art');
  const wrong = await pg.evaluate(async () => { const c = document.createElement('canvas'); c.width = 1080; c.height = 1350;
    return (await fetch('/api/loot/1/b1', { method: 'POST', headers: { 'Content-Type': 'application/json', Authorization: 'Bearer ' + token }, body: JSON.stringify({ image: c.toDataURL('image/jpeg') }) })).json(); });
  ok(!wrong.ok && /champions/.test(wrong.error), 'art for the losing finalist refused: ' + wrong.error);
  const anon = await pg.evaluate(async () => (await fetch('/api/loot/1/a2', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{}' })).status);
  ok(anon === 401, 'upload without the PIN refused: ' + anon);
  await pg.click('.champ[data-k="1/a1"] [data-del]'); await pg.waitForTimeout(700);
  ok(!fs.existsSync(f), 'Remove takes it off the site');
  ok(fs.readdirSync(path.join(dir, 'history')).some(x => x.startsWith('loot-ep01-a1.')), 'and keeps a copy in history');
  ok(await pg.locator('.champ[data-k="1/a1"] .ph .s').count() === 1, 'the card goes back to "automatic card"');
  ok(!errs.length, 'no page errors ' + errs.join());
} finally {
  await b.close(); api.kill(); up.forEach(s => s.close()); front.close();
  for (const x of fs.existsSync(LOOT) ? fs.readdirSync(LOOT) : []) if (!before.includes(x)) fs.rmSync(path.join(LOOT, x));
}
console.log(fails.length ? `FAIL ${fails.length}` : 'ok — champion artwork');
process.exit(fails.length ? 1 : 0);
