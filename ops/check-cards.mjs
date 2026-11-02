// Render the DRAW, the TABLES and the BRACKET cards, and prove they fit.
//
// NOTHING HAD EVER RENDERED THEM. ops/check-lineup.mjs drives buildLineups and
// drawLineup; ops/check-national-skin.mjs reads the DOM and a canvas is one
// opaque element with a bitmap inside it. So these three cards went out as
// Vol.8's composition swept red, AND overlapping themselves, and every harness
// in this repo stayed green — the owner found both by looking at a card.
//
// Two kinds of check here, because the two faults are not the same kind of
// thing:
//
//   · THE OVERLAP is geometry, and it is invisible in the bitmap. A group
//     header landing on the row above it is ivory type on a deep-red pill,
//     which no colour sample tells apart from the same type 40px higher. So
//     ngGroup reports the slot it was handed and the rows it actually drew,
//     and this reads NG_BLOCKS back: a block must fit its slot, and no block
//     may reach into the next one's.
//   · THE THEME is ink, so it is sampled from the pixels: the ground is this
//     volume's red, the masar band is at the head and the foot, the landmark
//     medallion has artwork in it, and no Vol.8 colour is anywhere on the card.
//
//   node ops/check-cards.mjs
//   APP=blackout-index.html node ops/check-cards.mjs   # must go red
//   SABOTAGE=floor node ops/check-cards.mjs            # the shipped bug, back
import { chromium } from 'playwright';
import fs from 'fs';
import http from 'http';
import path from 'path';

const SC = '/tmp/claude-0/-home-user-May-madness/0e44f0ad-a683-5f0d-9de6-9459ae328963/scratchpad';
const APP = process.env.APP || 'national-index.html';
const SAB = process.env.SABOTAGE || '';
// A sabotage run writes somewhere else, so a failing run cannot leave its
// cards where the next person to look expects the good ones.
const OUT = SC + (APP !== 'national-index.html' || SAB
                  ? '/vol9-groupcards-sabotage' : '/vol9-groupcards');
fs.mkdirSync(OUT, { recursive: true });

let app = fs.readFileSync(APP, 'utf8');

// SABOTAGE=floor puts back the one line that overlapped the card in the first
// place: a minimum row height, which does not make the row taller, it makes
// the block taller than the slot it was given. This is the shipped bug, not an
// invented one, and the bounds check has to catch it.
if (/floor/.test(SAB)) {
  const a = '  const rh = Math.min(96, (h - HEAD - gap * n) / n);';
  if (!app.includes(a)) throw new Error('sabotage anchor gone: floor');
  app = app.replace(a, '  const rh = Math.max(52, Math.min(96, (h - HEAD - gap * n) / n));');
}
// SABOTAGE=noart strips the landmark artwork, leaving the colours and the
// shapes alone — i.e. reproduces a medallion that is a ring with an empty disc
// in it, which looks exactly like a design choice.
if (/noart/.test(SAB)) {
  const before = app.length;
  app = app.replace(/const LANDMARK_ART = \{[\s\S]*?\n\};/,
                    'const LANDMARK_ART = {};');
  if (app.length === before) throw new Error('sabotage anchor gone: noart');
}

const state = fs.readFileSync(SC + '/na.json', 'utf8');
const PORT = 8131;
const ORIGIN = `http://127.0.0.1:${PORT}`;
const VENDOR = SC + '/vendor';
const FONTCSS = fs.readFileSync('brand/fonts/fonts.css', 'utf8')
  .replace(/url\(\.\//g, `url(${ORIGIN}/fonts/`);
const VERSION = fs.existsSync(APP + '.version')
  ? fs.readFileSync(APP + '.version', 'utf8').trim() : '';

const srv = http.createServer({ maxHeaderSize: 1 << 20 }, (req, res) => {
  const u = (req.url || '/').split('?')[0];
  const json = b => { res.writeHead(200, { 'Content-Type': 'application/json' }); res.end(b); };
  if (u === '/version.txt') { res.writeHead(200); return res.end(VERSION); }
  if (u === '/state') return json(state);
  if (u === '/photos' || u === '/session-photos') return json('{"ok":true,"photos":{}}');
  if (u.startsWith('/fonts/')) {
    const f = path.join('brand/fonts', path.basename(u));
    if (fs.existsSync(f)) { res.writeHead(200, { 'Content-Type': 'font/woff2' });
                            return res.end(fs.readFileSync(f)); }
  }
  const bn = path.basename(u);
  if (/\.(png|webp|jpe?g|svg)$/.test(bn)) {
    for (const d of ['brand/national', 'brand/blackout', 'assets']) {
      const f = path.join(d, bn);
      if (fs.existsSync(f)) {
        res.writeHead(200, { 'Content-Type': 'image/' + bn.split('.').pop() });
        return res.end(fs.readFileSync(f));
      }
    }
    res.writeHead(404); return res.end();
  }
  res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
  res.end(app);
}).listen(PORT);

const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
const pg = await browser.newPage({ viewport: { width: 430, height: 932 } });
await pg.route('**/unpkg.com/**', r => {
  const url = r.request().url();
  const f = /babel/.test(url) ? 'babel.js' : /react-dom/.test(url) ? 'react-dom.js' : 'react.js';
  r.fulfill({ status: 200, contentType: 'application/javascript',
              body: fs.readFileSync(path.join(VENDOR, f), 'utf8') });
});
await pg.route('**/fonts.googleapis.com/**', r =>
  r.fulfill({ status: 200, contentType: 'text/css', body: FONTCSS }));
await pg.goto(ORIGIN + '/', { waitUntil: 'load' });
await pg.waitForSelector('nav.fixed.bottom-0', { timeout: 25000 });
await pg.evaluate(() => document.fonts.ready);

// THE FOUR-GROUP NIGHT IS THE ONE THAT OVERLAPPED, so it is the first case
// here: 16 teams in 4 groups of 4 is the shape that drew 302px of block into
// a 232px slot. The three-group night is the uneven one (five and five and
// six, with a thirds playoff), and the six-team group is the tallest block
// the format can produce.
const SHAPES = [
  { key: '4x4', label: '4 groups of 4', groups: 'ABCD', per: 4 },
  { key: '3x6', label: '3 groups of 6', groups: 'ABC', per: 6 },
  { key: '2x4', label: '2 groups of 4', groups: 'AB', per: 4 },
];

const cards = await pg.evaluate(async (SHAPES) => {
  // Real-length names. "ALMUNTASER & MUATASIM" is the longest pair the roster
  // can produce and is what the width has to survive.
  const first = ['Almuntaser', 'Muatasim', 'Hassan', 'Faisal', 'Munther',
                 'Nooh', 'Khalid', 'Saif', 'Abdullah', 'Harith', 'Rashid',
                 'Yousuf', 'Talib', 'Majid', 'Hamed', 'Qais', 'Zahir',
                 'Ibrahim', 'Sultan', 'Nasser', 'Badr', 'Omar', 'Ali', 'Said'];
  const out = [];
  for (const sh of SHAPES) {
    const n = sh.groups.length * sh.per;
    const players = [];
    for (let i = 0; i < n * 2; i++)
      players.push({ id: 'p' + i, name: first[i % first.length] + ' Al Balushi' });
    const teams = [];
    for (let i = 0; i < n; i++)
      teams.push({ id: 't' + i, p1Id: 'p' + (i * 2), p2Id: 'p' + (i * 2 + 1),
                   group: sh.groups[Math.floor(i / sh.per)], seed: (i % sh.per) + 1 });
    // Every group match played, so the TABLES card has a real table in it and
    // teams that are actually through. Without results the through/alive/out
    // states render zero times and every assertion about them passes having
    // seen nothing.
    const groupMatches = [];
    for (const gr of sh.groups) {
      const inG = teams.filter(t => t.group === gr);
      for (let a = 0; a < inG.length; a++)
        for (let b = a + 1; b < inG.length; b++)
          groupMatches.push({
            id: `m${gr}${a}${b}`, group: gr,
            team1Id: inG[a].id, team2Id: inG[b].id,
            winner: a % 2 === 0 ? 'team1' : 'team2',
            score: { t1: a % 2 === 0 ? 6 : 3, t2: a % 2 === 0 ? 3 : 6 },
          });
    }
    const session = {
      id: 's' + sh.key, name: 'Session 3', date: '2026-11-11',
      teams, groupMatches,
      thirdPlaceMode: sh.groups.length === 3 ? 'playoff' : 'top2',
      bracket: {
        qf: [{ team1Id: 't0', team2Id: 't1' }, { team1Id: 't2', team2Id: 't3' },
             { team1Id: 't4', team2Id: 't5' }, { team1Id: 't6', team2Id: 't7' }],
        sf: [{ team1Id: 't0', team2Id: 't2', winner: 'team1',
               score: { t1: 6, t2: 2 } },
             { team1Id: 't4', team2Id: 't6', winner: 'team2',
               score: { t1: 3, t2: 6 } }],
        final: { team1Id: 't0', team2Id: 't6', winner: 'team1',
                 score: { t1: 6, t2: 4 } },
      },
      completed: true,
    };
    const st = { players, sessions: [session] };
    // buildGroupCards returns a LIST — [{key, label, d}] — and only of the
    // cards that have something on them. Indexing it by kind got undefined
    // for all three and the harness reported "no cards built" on a session
    // that produces all of them.
    const built = buildGroupCards(session, st, 2);
    for (const item of built) {
      const kind = item.key, d = item.d;
      const url = await drawGroupCard(kind, d);
      // NG_BLOCKS is the painter's own report of where each block was given
      // and where it ended. Read straight after the draw, before the next one
      // clears it.
      const blocks = (typeof NG_BLOCKS !== 'undefined')
        ? JSON.parse(JSON.stringify(NG_BLOCKS)) : null;
      out.push({ key: `${sh.key}-${kind}`, kind, label: `${sh.label} · ${kind}`,
                 url, blocks });
    }
  }
  return out;
}, SHAPES);

// The card's own geometry, read out of the painter so these windows cannot
// drift from it — the first time the line-up painter moved its band the
// hard-coded rows reported no band at all on a card that plainly had one.
const GEO = await pg.evaluate(() => {
  if (typeof NG === 'undefined' || typeof NC === 'undefined') return null;
  return { PAD: NC.PAD, EDGE: 72, BAND: NC.BAND,
           MED: NG.MED, L: NG.L, H1: NG.H1, H2: NG.H2,
           TOP: NG.TOP, BOT: NG.BOT };
});

// Vol.8's own inks. The near-black ground is matched TIGHTLY and the two
// accents loosely: this volume's ink is #1A0A0C, a very dark red, which is 33
// away from #050505 on the loose metric — so a 40-point window round Vol.8's
// black flagged the champions' name on the ivory plate as an inherited colour.
const VOL8 = [[198, 255, 0, 'Blackout lime', 40], [255, 46, 136, 'Blackout magenta', 40],
              [5, 5, 5, 'Blackout black', 10]];
const NEAR = (a, b, t) =>
  Math.abs(a[0] - b[0]) + Math.abs(a[1] - b[1]) + Math.abs(a[2] - b[2]) < t;

let failed = 0;
for (const c of cards) {
  const png = Buffer.from(c.url.split(',')[1], 'base64');
  fs.writeFileSync(path.join(OUT, `card-${c.key}.png`), png);
  const bad = [];

  // ── the overlap, from the painter's own report ────────────────────────────
  if (c.kind !== 'bracket') {
    if (!c.blocks || !c.blocks.length) {
      bad.push('the painter reported no group blocks — is this still gcPaint?');
    } else {
      c.blocks.forEach((b, i) => {
        const over = b.drawn[1] - b.slot[1];
        if (over > 1)
          bad.push(`GROUP ${b.letter} draws ${over.toFixed(0)}px past the slot `
                 + `it was given (${b.rows} rows at ${b.rh.toFixed(0)}px)`);
        const next = c.blocks[i + 1];
        if (next && b.drawn[1] > next.slot[0] + 1)
          bad.push(`GROUP ${b.letter} reaches ${(b.drawn[1] - next.slot[0]).toFixed(0)}px `
                 + `into GROUP ${next.letter}'s block`);
      });
      const last = c.blocks[c.blocks.length - 1];
      if (GEO && last.drawn[1] > GEO.BOT + 1)
        bad.push(`the last block ends at ${last.drawn[1].toFixed(0)}, `
               + `past the body's ${GEO.BOT}`);
      // A row so short the name in it is unreadable is a different failure
      // from an overlap and would otherwise pass this silently.
      const thin = c.blocks.filter(b => b.rh < 34);
      if (thin.length)
        bad.push(`${thin.length} group(s) have rows under 34px `
               + `(${thin.map(b => b.letter + ' ' + b.rh.toFixed(0)).join(', ')})`);
    }
  }

  // ── the ink ───────────────────────────────────────────────────────────────
  const ink = await pg.evaluate(async ({ url, geo }) => {
    const im = new Image();
    await new Promise(r => { im.onload = r; im.src = url; });
    const cv = document.createElement('canvas');
    cv.width = im.width; cv.height = im.height;
    const g = cv.getContext('2d');
    g.drawImage(im, 0, 0);
    const all = g.getImageData(0, 0, cv.width, cv.height).data;

    const hist = new Map();
    let red = 0, n = 0;
    for (let i = 0; i < all.length; i += 4 * 7) {
      hist.set(`${all[i]},${all[i + 1]},${all[i + 2]}`,
               (hist.get(`${all[i]},${all[i + 1]},${all[i + 2]}`) || 0) + 1);
      n++;
      if (all[i] > 70 && all[i] > all[i + 1] * 2 && all[i] > all[i + 2] * 2) red++;
    }
    // The flag's green, which is in the masar weave and nowhere else up there.
    const green = (y0, h) => {
      const w = im.width - geo.PAD * 2;
      const d = g.getImageData(geo.PAD, y0, w, h).data;
      let k = 0;
      for (let i = 0; i < d.length; i += 4)
        if (d[i] < 80 && d[i + 1] > 85 && d[i + 1] < 170 && d[i + 2] < 110) k++;
      return k / (w * h);
    };
    // Artwork inside the medallion: the silhouettes are white, and nothing
    // else is drawn inside that disc.
    const mr = geo.MED;
    const mcx = im.width - geo.PAD - 28 - mr;
    const mcy = (geo.H1 + geo.H2) / 2 - 26;
    const md = g.getImageData(Math.round(mcx - mr * 0.7), Math.round(mcy - mr * 0.7),
                              Math.round(mr * 1.4), Math.round(mr * 1.4)).data;
    let white = 0;
    for (let i = 0; i < md.length; i += 4)
      if (md[i] > 200 && md[i + 1] > 190 && md[i + 2] > 180) white++;
    return {
      w: im.width, h: im.height, red: red / n,
      head: green(geo.EDGE, geo.BAND),
      foot: green(im.height - geo.EDGE - geo.BAND, geo.BAND),
      med: white / (md.length / 4),
      top: [...hist].sort((a, b) => b[1] - a[1]).slice(0, 10)
        .map(([k, v]) => [k, v / n]),
    };
  }, { url: c.url, geo: GEO });

  for (const [k, share] of ink.top) {
    const rgb = k.split(',').map(Number);
    for (const [r, gr, b, name, t] of VOL8)
      if (NEAR(rgb, [r, gr, b], t))
        bad.push(`${name} is ${(share * 100).toFixed(1)}% of the card`);
  }
  // The share of RED pixels, never the modal colour: the ground is a flat
  // red with a tile over it, and a flat ink plate is exactly one triple, so
  // the mode can be the plate while the card is black.
  if (ink.red < 0.55)
    bad.push(`only ${(ink.red * 100).toFixed(0)}% of the card is red `
           + `(modal colour rgb(${ink.top[0][0]}))`);
  if (ink.head < 0.08)
    bad.push(`no masar band at the head (${(ink.head * 100).toFixed(1)}% green)`);
  if (ink.foot < 0.08)
    bad.push(`no masar band at the foot (${(ink.foot * 100).toFixed(1)}% green)`);
  if (ink.med < 0.06)
    bad.push(`the landmark medallion is empty (${(ink.med * 100).toFixed(1)}% ink)`);

  if (bad.length) failed++;
  console.log(`card-${c.key}.png  ${ink.w}x${ink.h}  ${c.label}  `
    + `red ${(ink.red * 100).toFixed(0)}%  band ${(ink.head * 100).toFixed(0)}/`
    + `${(ink.foot * 100).toFixed(0)}%  medallion ${(ink.med * 100).toFixed(0)}%`
    + (bad.length ? `\n  !! ${bad.join('\n  !! ')}` : '  ok'));
}

// A contact sheet, because a card is judged by looking at it.
const sheet = `<!doctype html><meta charset="utf-8">
<body style="margin:0;background:#141414;padding:26px;display:flex;flex-wrap:wrap;gap:16px;font-family:system-ui">
${cards.map(c => `<div>
  <div style="color:#F2B8BC;font:700 11px monospace;margin-bottom:6px;letter-spacing:.12em">
    ${c.label}</div>
  <img src="${c.url}" style="width:228px;display:block;border-radius:8px">
</div>`).join('')}</body>`;
const sp = await browser.newPage({ viewport: { width: 1560, height: 1000 } });
await sp.setContent(sheet, { waitUntil: 'load' });
await sp.screenshot({ path: path.join(OUT, 'GROUP-CARDS.png'), fullPage: true });
await sp.close();

await pg.close();
await browser.close();
srv.close();

if (!cards.length) { console.error('no cards built'); process.exit(1); }
if (!GEO) { console.error('the painter has no NG geometry — still gcPaint?'); process.exit(1); }
if (failed) { console.error(`\n${failed} card(s) failed`); process.exit(1); }
console.log(`\nok — ${cards.length} cards  ${path.join(OUT, 'GROUP-CARDS.png')}`);
