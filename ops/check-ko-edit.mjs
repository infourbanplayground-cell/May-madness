// Two faults reported from the 26 Oct night, driven through the REAL
// components rather than described:
//
//   A. a corrected group score did not redraw the bracket on a 4-group night
//      ("if the score is incorrect after correcting it doesn't change who's
//      through")
//   B. changing WHO is in a knockout match forced a score to be entered
//      ("when I change the names after correcting, I have to input scores")
//
// BracketTab is a top-level function, so a Playwright page can mount it
// directly with a session of our choosing — the same trick the group-card
// checks use. That is deliberate: clicking from the home screen down to the
// bracket is four brittle hops through a UI none of this changed, and a
// harness that fails because a tab label moved teaches nothing.
//
// Both tests read the SESSION THE COMPONENT WROTE, not the pixels: a bracket
// row can look right while the state behind it carries a result nobody played.
//
//   node ops/check-ko-edit.mjs
import { chromium } from 'playwright';
import fs from 'fs';
import http from 'http';
import path from 'path';

const SC = '/tmp/claude-0/-home-user-May-madness/0e44f0ad-a683-5f0d-9de6-9459ae328963/scratchpad';
const VENDOR = SC + '/vendor';
const PORT = 8121;
const ORIGIN = `http://127.0.0.1:${PORT}`;
// APP= points the harness at another build, which is how both tests were
// proved to fail: against the build before the fix, A is not redrawn and B
// has no way to save a team change.
const app = fs.readFileSync(process.env.APP || 'blackout-index.html', 'utf8');
const FONTCSS = fs.readFileSync('brand/fonts/fonts.css', 'utf8')
  .replace(/url\(\.\//g, `url(${ORIGIN}/fonts/`);
const VERSION = fs.existsSync('blackout-index.html.version')
  ? fs.readFileSync('blackout-index.html.version', 'utf8').trim() : '';

const srv = http.createServer({ maxHeaderSize: 1 << 20 }, (req, res) => {
  const u = (req.url || '/').split('?')[0];
  if (u === '/version.txt') { res.writeHead(200, { 'Content-Type': 'text/plain' }); return res.end(VERSION); }
  if (u.startsWith('/fonts/') && u.endsWith('.woff2')) {
    const f = path.join('brand/fonts', path.basename(u));
    if (fs.existsSync(f)) { res.writeHead(200, { 'Content-Type': 'font/woff2' }); return res.end(fs.readFileSync(f)); }
  }
  res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
  res.end(app);
}).listen(PORT);

const base = JSON.parse(fs.readFileSync(SC + '/bo-ko2.json', 'utf8')).state;
const night = base.sessions.find(s => s.date === '2026-10-26');
const players = Object.fromEntries(base.players.map(p => [p.id, p.name]));
const byId = Object.fromEntries(night.teams.map(t => [t.id, t]));
const grp = (id) => (byId[id] || {}).group || '?';
const nm = (id) => byId[id]
  ? `${(players[byId[id].p1Id] || '?').split(' ')[0]} & ${(players[byId[id].p2Id] || '?').split(' ')[0]}` : '—';

// The merit pairing the app produced on the night: A1 v B2, C1 v D2,
// B1 v C2, D1 v A2. Teams are taken in group order, which is enough to build
// a bracket that disagrees with the tables.
function staleSession(extra) {
  const s = JSON.parse(JSON.stringify(night));
  const at = (g, r) => s.teams.filter(t => t.group === g).map(t => t.id)[r];
  s.bracket = { qf: [
    { id: 'q1', slot: 1, team1Id: at('A', 0), s1: 'A1', team2Id: at('B', 1), s2: 'B2', winner: null },
    { id: 'q2', slot: 2, team1Id: at('C', 0), s1: 'C1', team2Id: at('D', 1), s2: 'D2', winner: null },
    { id: 'q3', slot: 3, team1Id: at('B', 0), s1: 'B1', team2Id: at('C', 1), s2: 'C2', winner: null },
    { id: 'q4', slot: 4, team1Id: at('D', 0), s1: 'D1', team2Id: at('A', 1), s2: 'A2', winner: null },
  ], sf: [], final: null };
  delete s.seedSig;
  s.seedManual = false;
  return Object.assign(s, extra || {});
}

async function mount(p, session) {
  await p.evaluate(({ sess, st }) => {
    document.getElementById('root').style.display = 'none';
    let host = document.getElementById('harness');
    if (host) host.remove();
    host = document.createElement('div');
    host.id = 'harness';
    document.body.appendChild(host);
    let cur = sess;
    window.__get = () => cur;
    function Harness() {
      const [s, setS] = React.useState(sess);
      React.useEffect(() => { cur = s; }, [s]);
      return React.createElement(BracketTab, {
        session: s, state: st,
        updateSession: (fn) => setS(prev => fn({ ...prev })),
        isAdmin: true, canScore: true, canUploadPhotos: false,
      });
    }
    ReactDOM.createRoot(host).render(React.createElement(Harness));
  }, { sess: session, st: base });
  await p.waitForTimeout(1500);
}

async function open() {
  const p = await b.newPage({ viewport: { width: 430, height: 932 } });
  await p.route('**/unpkg.com/**', r => {
    const url = r.request().url();
    const f = /babel/.test(url) ? 'babel.js' : /react-dom/.test(url) ? 'react-dom.js' : 'react.js';
    r.fulfill({ status: 200, contentType: 'application/javascript', body: fs.readFileSync(path.join(VENDOR, f), 'utf8') });
  });
  await p.route('**/fonts.googleapis.com/**', r => r.fulfill({ status: 200, contentType: 'text/css', body: FONTCSS }));
  await p.route('**/state', r => r.fulfill({ status: 200, contentType: 'application/json',
    body: JSON.stringify({ ok: true, state: base, version: 1 }) }));
  await p.route('**/photos', r => r.fulfill({ status: 200, contentType: 'application/json', body: '{"ok":true,"photos":{}}' }));
  await p.route('**/session-photos*', r => r.fulfill({ status: 200, contentType: 'application/json', body: '{"ok":true,"photos":{}}' }));
  await p.route('**/save', r => r.fulfill({ status: 200, contentType: 'application/json', body: '{"ok":true,"version":2}' }));
  p.on('pageerror', e => console.log('   PAGEERROR ' + String(e).slice(0, 200)));
  await p.goto(`${ORIGIN}/index.html`, { waitUntil: 'load', timeout: 60000 });
  await p.waitForTimeout(4000);
  return p;
}

const b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
let fails = 0;
const fail = (m) => { fails++; console.log('  FAIL ' + m); };
const ok = (m) => console.log('  ok   ' + m);
const WANT = ['A1 v D2', 'B1 v C2', 'C1 v B2', 'D1 v A2'];

// ── A. a bracket that no longer matches the group tables is redrawn ──────
{
  console.log('\nA. a corrected group result redraws the bracket (4 groups)');
  const p = await open();
  await mount(p, staleSession());
  await p.waitForTimeout(1500);
  const qf = await p.evaluate(() => window.__get().bracket.qf);
  const pairs = qf.map(m => `${grp(m.team1Id)}1 v ${grp(m.team2Id)}2`);
  console.log('       ' + pairs.join('  |  '));
  if (pairs.join() !== WANT.join()) fail(`redrawn as ${pairs.join(', ')} — expected ${WANT.join(', ')}`);
  else ok('redrawn by letter: ' + WANT.join(', '));
  const badLbl = qf.filter(m => m.s1 !== grp(m.team1Id) + '1' || m.s2 !== grp(m.team2Id) + '2');
  if (badLbl.length) fail(`${badLbl.length} seed label(s) do not name the team's own group`);
  else ok('seed labels name the teams\' own groups');
  if (qf.some(m => m.winner)) fail('the redraw invented a result');
  else ok('no result invented');

  // And it must NOT redraw once the knockout has started, nor over a bracket
  // the organiser arranged by hand. Those are the guards that stop this from
  // eating real work.
  await mount(p, staleSession({ seedManual: true }));
  const manual = await p.evaluate(() => window.__get().bracket.qf.map(m => m.s1 + ' v ' + m.s2).join(','));
  if (manual !== 'A1 v B2,C1 v D2,B1 v C2,D1 v A2') fail('a hand-arranged bracket was overwritten: ' + manual);
  else ok('a hand-arranged bracket is left alone');

  const played = staleSession();
  played.bracket.qf[0].winner = 'team1';
  played.bracket.qf[0].score = { t1: 6, t2: 3 };
  await mount(p, played);
  const after = await p.evaluate(() => window.__get().bracket.qf.map(m => m.s1 + ' v ' + m.s2).join(','));
  if (after !== 'A1 v B2,C1 v D2,B1 v C2,D1 v A2') fail('a started knockout was redrawn: ' + after);
  else ok('a knockout with a result is left alone');
  await p.close();
}

// ── B. changing who is in a match, with no score ─────────────────────────
{
  console.log('\nB. correcting a pairing without inventing a score');
  const p = await open();
  // seedManual, or A's redraw fires first and there is nothing left to fix.
  await mount(p, staleSession({ seedManual: true }));

  const before = await p.evaluate(() => window.__get().bracket.qf[0]);
  // Open QF1 by clicking the row that carries its first team's name.
  const first = nm(before.team1Id).split(' & ')[0];
  const clicked = await p.evaluate((n) => {
    const host = document.getElementById('harness');
    const cands = [...host.querySelectorAll('div,button')].filter(e =>
      (e.innerText || '').includes(n) && e.offsetHeight > 20 && e.offsetHeight < 220);
    const el = cands[cands.length - 1];
    if (!el) return false;
    el.click();
    return true;
  }, first);
  await p.waitForTimeout(900);
  const inModal = await p.evaluate(() => /EDIT QUARTERFINAL/i.test(document.body.innerText));
  if (!clicked || !inModal) fail('could not open the quarter-final editor');
  else {
    const changed = await p.evaluate(() => {
      const sels = [...document.querySelectorAll('select')];
      if (sels.length < 2) return null;
      const sel = sels[1];
      const opt = [...sel.options].find(o => o.value && o.value !== sel.value);
      if (!opt) return null;
      Object.getOwnPropertyDescriptor(window.HTMLSelectElement.prototype, 'value').set.call(sel, opt.value);
      sel.dispatchEvent(new Event('change', { bubbles: true }));
      return opt.value;
    });
    await p.waitForTimeout(500);
    if (!changed) fail('the team pickers were not there');
    else {
      const hasBtn = await p.evaluate(() => {
        const t = [...document.querySelectorAll('button')].find(x => /Save teams only/i.test(x.innerText));
        if (!t) return false;
        t.click(); return true;
      });
      if (!hasBtn) fail('there is no way to save a team change without a score — the reported fault');
      else {
        await p.waitForTimeout(1200);
        const q1 = await p.evaluate(() => window.__get().bracket.qf.find(m => m.id === 'q1'));
        if (q1.team2Id !== changed) fail('the saved match still holds the old team');
        else ok(`team 2 changed to ${nm(changed)} (group ${grp(changed)}) with no score entered`);
        if (q1.winner || q1.score) fail('saving a team change invented a result');
        else ok('no winner, no score');
        if (q1.s2 !== grp(changed) + '1' && q1.s2 !== grp(changed) + '2' && q1.s2 !== grp(changed) + '3')
          fail(`the seed label reads "${q1.s2}" for a team in group ${grp(changed)}`);
        else ok(`seed label follows the team: ${q1.s2}`);
      }
    }
  }
  await p.close();
}

await b.close();
srv.close();
console.log(fails ? `\n${fails} failure(s)` : '\nko edit ok');
process.exit(fails ? 1 : 0);
