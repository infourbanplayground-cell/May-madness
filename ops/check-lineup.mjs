// Render the share cards and prove they are not still Vol.8.
//
// THE SHARE CARDS ARE DRAWN ON A CANVAS, which means ops/check-national-skin.mjs
// cannot see them at all. Every assertion in that harness reads the DOM — the
// computed colour of an element, the box of a text run — and a canvas is one
// opaque element with a bitmap inside it. The line-up, the champions, the
// bracket and the tables cards could all still be lime on black and the skin
// audit would stay green, because the only thing it can see is a 1080x1920
// rectangle.
//
// So this one samples the PIXELS. It calls the app's own `buildLineups` and
// `drawLineup` directly — both are top-level functions — with a synthetic
// night, and then asks the bitmap what colour it actually is.
//
//   node ops/check-lineup.mjs
//   APP=blackout-index.html node ops/check-lineup.mjs    # must go red
import { chromium } from 'playwright';
import fs from 'fs';
import http from 'http';
import path from 'path';

const SC = '/tmp/claude-0/-home-user-May-madness/0e44f0ad-a683-5f0d-9de6-9459ae328963/scratchpad';
const APP = process.env.APP || 'national-index.html';
// A sabotage run writes SOMEWHERE ELSE. Pointed at the Vol.8 build it used to
// overwrite the Vol.9 cards and the contact sheet with Vol.8's, so the next
// thing to open them showed black-and-lime cards from a run that was supposed
// to fail — which is exactly what happened here.
const OUT = SC + (APP !== 'national-index.html' ? '/vol9-cards-sabotage'
                 : process.env.CUT ? '/vol9-cards-cutout'
                 : process.env.PHOTO ? '/vol9-cards-photo' : '/vol9-cards');
fs.mkdirSync(OUT, { recursive: true });

// PHOTO=<file or directory of jpgs>. With it the cards are drawn over real
// session photographs, which is how they are actually posted.
const dirList = (p, re) => {
  const st = fs.statSync(p);
  return st.isDirectory()
    ? fs.readdirSync(p).filter(f => re.test(f)).sort().map(f => path.join(p, f))
    : [p];
};
const CUTS = process.env.CUT ? dirList(process.env.CUT, /\.png$/i) : null;
const PHOTOS = (() => {
  const p = process.env.PHOTO;
  if (!p) return null;
  const st = fs.statSync(p);
  return st.isDirectory()
    ? fs.readdirSync(p).filter(f => /\.(jpe?g|png)$/i.test(f)).sort().map(f => path.join(p, f))
    : [p];
})();

const app = fs.readFileSync(APP, 'utf8');
const state = fs.readFileSync(SC + '/na.json', 'utf8');
const PORT = 8129;
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
    // PHOTO=<file|dir> renders the cards over a real session photo instead of
    // the no-photo washes. The photo window is the whole middle of the card
    // and gets a grade, two lamps and a floor — none of which the washes
    // exercise, so a card checked only without one is half unchecked. Served
    // locally on purpose: the live store is Cloudinary, and a cross-origin
    // draw taints the canvas so toDataURL throws and the app silently falls
    // back to the photo-less card.
    if (PHOTOS && bn.startsWith('__ph')) {
      const f = PHOTOS[parseInt(bn.slice(4), 10) % PHOTOS.length];
      res.writeHead(200, { 'Content-Type': 'image/jpeg' });
      return res.end(fs.readFileSync(f));
    }
    // CUT=<dir> renders the NO-BACKGROUND card — luPaintCut, the other
    // painter, which stands background-removed players on a floor under a
    // ghost word. It is a different layout, not the photo card with the
    // backdrop knocked out, and nothing had ever rendered it in this volume.
    if (CUTS && bn.startsWith('__cut')) {
      const f = CUTS[parseInt(bn.slice(5), 10) % CUTS.length];
      res.writeHead(200, { 'Content-Type': 'image/png' });
      return res.end(fs.readFileSync(f));
    }
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

// A night with a bracket in it. Vol.9 has played none, so without this every
// card renders zero times and every assertion about them passes having seen
// nothing — the same hole the skin harness's seeded pass closes.
const cards = await pg.evaluate(async ({ nPhotos, nCuts }) => {
  const names = ['Muntaser Hasni', 'Hassan Salhi', 'Faisal Al Harthi',
                 'Muatasim Sabri', 'Munther Rahbi', 'Nooh Al Balushi',
                 'Khalid Al Amri', 'Saif Al Hinai'];
  const players = names.map((name, i) => ({ id: 'p' + i, name }));
  const teams = [0, 2, 4, 6].map((i, k) => ({
    id: 't' + k, p1Id: 'p' + i, p2Id: 'p' + (i + 1),
    group: 'ABCD'[k],
  }));
  const session = {
    id: 's1', name: 'Session 6', date: '2026-11-18', teams, groupMatches: [],
    bracket: {
      qf: [],
      sf: [{ team1Id: 't0', team2Id: 't1' }, { team1Id: 't2', team2Id: 't3' }],
      final: { team1Id: 't0', team2Id: 't2', winner: 'team1',
               score: { t1: 6, t2: 3 } },
    },
    completed: true,
  };
  const st = { players, sessions: [session] };
  const lus = buildLineups(session, st, 412);
  const logoImg = await luImg('assets/up-logo-national.png');
  const out = [];
  for (let i = 0; i < lus.length; i++) {
    const d = lus[i];
    let url;
    if (nCuts) {
      // The cut-out path is not reachable through drawLineup: it derives a
      // Cloudinary background-removal URL from the photo, and these are
      // served locally. ncPaint is top-level, so call it directly in "cut"
      // mode — the same entry drawCutCardAt uses.
      await ncPreload(d);
      url = await new Promise(res => {
        const im = new Image();
        im.onload = () => {
          const c = document.createElement('canvas');
          c.width = LU_W; c.height = LU_H;
          ncPaint(c.getContext('2d'), d.kind, d, im, logoImg, null, 'cut');
          res(c.toDataURL('image/png'));
        };
        im.onerror = () => res(null);
        im.src = `__cut${i}.png`;
      });
    } else {
      url = await drawLineup(d.kind, d, nPhotos ? `__ph${i}.jpg` : null, null);
    }
    if (!url) throw new Error('card ' + d.key + ' did not render');
    out.push({ key: d.key, kind: d.kind, label: d.label, url, caption: d.caption });
  }
  return out;
}, { nPhotos: PHOTOS ? PHOTOS.length : 0, nCuts: CUTS ? CUTS.length : 0 });

// The card's own geometry, so the checks below cannot drift from the painter.
const GEO2 = await pg.evaluate(() => (typeof NC !== 'undefined')
  ? { ARCH_TOP: NC.ARCH_TOP, ARCH_BOT: NC.PLATE_B }
  : { ARCH_TOP: 420, ARCH_BOT: 1560 });
const GEO = await pg.evaluate(() => (typeof NC !== 'undefined')
  ? { PAD: NC.PAD, EDGE: 72, H: NC.BAND }
  : { PAD: 36, EDGE: 18, H: 56 });

// ── what the bitmap actually is ─────────────────────────────────────────────
const VOL8 = [[198, 255, 0, 'Blackout lime'], [255, 46, 136, 'Blackout magenta']];
const NEAR = (a, b) => Math.abs(a[0] - b[0]) + Math.abs(a[1] - b[1]) + Math.abs(a[2] - b[2]) < 40;

let failed = 0;
for (const c of cards) {
  const png = Buffer.from(c.url.split(',')[1], 'base64');
  const file = path.join(OUT, `lineup-${c.key}.png`);
  fs.writeFileSync(file, png);

  const stats = await pg.evaluate(async ({ url, geo2 }) => {
    const im = new Image();
    await new Promise(r => { im.onload = r; im.src = url; });
    const cv = document.createElement('canvas');
    cv.width = im.width; cv.height = im.height;
    const g = cv.getContext('2d');
    g.drawImage(im, 0, 0);
    const d = g.getImageData(0, 0, cv.width, cv.height).data;
    const hist = new Map();
    let red = 0, n = 0;
    // THE GROUND IS WHAT THIS MEASURES, so the photo window is excluded.
    // luPaint draws the photograph into rows 420..1560 — 59% of the card —
    // graded and lamp-lit but legitimately not red. Counting it dropped a
    // perfectly good photo card to 50% and failed it. Outside that window
    // both kinds of card are the same thing: this volume's ground.
    const PH_TOP = geo2.ARCH_TOP, PH_BOT = geo2.ARCH_BOT;
    // Every 7th pixel: enough to find a colour that is anywhere on the card,
    // fast enough to run on five 1080x1920 bitmaps.
    for (let i = 0; i < d.length; i += 4 * 7) {
      const k = `${d[i]},${d[i + 1]},${d[i + 2]}`;
      hist.set(k, (hist.get(k) || 0) + 1);
      const y = Math.floor((i / 4) / im.width);
      if (y >= PH_TOP && y < PH_BOT) continue;
      n++;
      // Anywhere on the ramp from the deep red to the flag red: clearly red,
      // clearly not the ink plates and not the ivory.
      if (d[i] > 70 && d[i] > d[i + 1] * 2 && d[i] > d[i + 2] * 2) red++;
    }
    const top = [...hist].sort((a, b) => b[1] - a[1]).slice(0, 12);
    return { w: im.width, h: im.height, red: red / n,
             top: top.map(([k, v]) => [k, v / n]) };
  }, { url: c.url, geo2: GEO2 });

  const bad = [];
  for (const [k, share] of stats.top) {
    const rgb = k.split(',').map(Number);
    for (const [r, g, b, name] of VOL8)
      if (NEAR(rgb, [r, g, b])) bad.push(`${name} is ${(share * 100).toFixed(1)}% of the card`);
  }
  // The ground has to be this volume's. A card that lost its background to
  // the sweep comes back near-black and nothing else here would say so.
  //
  // NOT the modal triple. The ground is a GRADIENT, so its red is spread over
  // thousands of distinct triples while a flat ink name plate is exactly one —
  // the mode is the plate, every time, and a near-black card with a few red
  // chips on it would have passed. It is the share of pixels that are RED,
  // counted across the whole bitmap.
  if (stats.red < 0.5)
    bad.push(`only ${(stats.red * 100).toFixed(0)}% of the card's GROUND is red `
           + `(modal colour rgb(${stats.top[0][0]}))`);
  // THE MASAR BAND HAS TO BE ON IT. A card that is merely the right colour is
  // a recolour, not a volume — the lesson the app itself had to learn twice.
  // The band carries the flag's green, which appears nowhere else on a card,
  // so looking for green where the trim is drawn is the whole test.
  //
  // The windows are the trim's OWN box (inset 36, 56 tall), not the first and
  // last 56 rows of the bitmap. While the band ran full-bleed the two happened
  // to be the same thing; once it was inset the row windows still clipped 20
  // rows of it and passed on a sliver, which would go on passing if the trim
  // drifted another 40px in.
  const weave = await pg.evaluate(async ({ url, geo }) => {
    const im = new Image();
    await new Promise(r => { im.onload = r; im.src = url; });
    const cv = document.createElement('canvas');
    cv.width = im.width; cv.height = im.height;
    cv.getContext('2d').drawImage(im, 0, 0);
    const g = cv.getContext('2d');
    // READ FROM THE PAINTER, not written here. The band's inset and height
    // are geometry the card owns; the first time the painter moved them the
    // windows kept looking at the old rows and reported no band at all on a
    // card that plainly had one.
    const PAD = geo.PAD, EDGE = geo.EDGE, H = geo.H;
    const green = (y0) => {
      const w = im.width - PAD * 2;
      const d = g.getImageData(PAD, y0, w, H).data;
      let n = 0;
      for (let i = 0; i < d.length; i += 4)
        if (d[i] < 80 && d[i + 1] > 85 && d[i + 1] < 170 && d[i + 2] < 110) n++;
      return n / (w * H);
    };
    return { head: green(EDGE), foot: green(im.height - EDGE - H) };
  }, { url: c.url, geo: GEO });
  if (weave.head < 0.08) bad.push(`no masar band at the head (${(weave.head * 100).toFixed(1)}% green)`);
  if (weave.foot < 0.08) bad.push(`no masar band at the foot (${(weave.foot * 100).toFixed(1)}% green)`);

  if (bad.length) failed++;
  console.log(`lineup-${c.key}.png  ${stats.w}x${stats.h}  ${c.label}  `
    + `ground ${(stats.red * 100).toFixed(0)}% red`
    + (bad.length ? `\n  !! ${bad.join('\n  !! ')}` : '  ok'));
}

// A contact sheet, because a card is judged by looking at it.
const sheet = `<!doctype html><meta charset="utf-8">
<body style="margin:0;background:#141414;padding:30px;display:flex;gap:18px;font-family:system-ui">
${cards.map(c => `<div>
  <div style="color:#F2B8BC;font:700 12px monospace;margin-bottom:7px;letter-spacing:.12em">
    ${c.label}</div>
  <img src="${c.url}" style="width:250px;display:block;border-radius:8px">
</div>`).join('')}</body>`;
const sp = await browser.newPage({ viewport: { width: 1420, height: 520 } });
await sp.setContent(sheet, { waitUntil: 'load' });
await sp.screenshot({ path: path.join(OUT, 'LINEUP-CARDS.png'), fullPage: true });
await sp.close();

await pg.close();
await browser.close();
srv.close();

if (!cards.length) { console.error('no cards built — buildLineups returned nothing'); process.exit(1); }
if (failed) { console.error(`\n${failed} card(s) are still Vol.8`); process.exit(1); }
console.log(`\nok — ${cards.length} cards  ${path.join(OUT, 'LINEUP-CARDS.png')}`);
