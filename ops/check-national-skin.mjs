// Prove Vol.9 is actually WEARING Vol.9 — the harness for the re-skin.
//
// The re-skin is a colour sweep plus one appended stylesheet over a page built
// for Vol.8, which is a shape that fails quietly in four specific ways. Every
// check here is one of those failures, and every one of them has actually
// happened in this repo:
//
//   · A SWEEP MISSES WHAT IT CANNOT SEE. The first pass left `rgb(14,14,14)`,
//     `rgb(20,20,20)` and `rgb(10,10,10)` surface tints behind, so a third of
//     the screens were still near-black under a red page. So: no element may
//     compute to a Vol.8 palette value, read off the RENDERED page rather than
//     grepped out of the source.
//   · SPECIFICITY DECIDES, NOT ORDER. An inherited layer carries
//     `*:not(a):not(b):not(c){border-radius:2px}` at (0,3,0), which beats a
//     plain `.sg-hero` written a thousand lines later — the arch lost silently
//     and the hero rendered with 2px corners. So the shapes are asserted from
//     getComputedStyle, which is the only thing that knows who won.
//   · THE SAME RULE THAT FIXES ONE THING BREAKS ANOTHER. `.sg-hero *{color:ink
//     !important}` is what flips an ivory hero's type — and it beat the volume
//     watermark's own inline 5.5% alpha, so a 170px near-black 09 lay across
//     the eyebrow and the headline. So the watermark's EFFECTIVE alpha is
//     measured, not assumed from what the build wrote.
//   · CONTRAST MUST BE COMPOSITED. Reading backgroundColor alone reports
//     rgba(0,0,0,0) as black and hands back a confident 1.00:1 for type that
//     is perfectly readable. Every text run here is composited down the
//     ancestor chain to an opaque colour first.
//
// It runs the REAL app against the REAL Vol.9 state, because a skin check on a
// stub page proves nothing about the screens players use.
//
//   node ops/check-national-skin.mjs
//   APP=blackout-index.html node ops/check-national-skin.mjs   # must go red
//   SABOTAGE=noskin   drops the appended skin block
//   SABOTAGE=nofont   drops the webfont
//   ONLY=rank         narrows the sweep
import { chromium } from 'playwright';
import fs from 'fs';
import http from 'http';
import path from 'path';

const SC = '/tmp/claude-0/-home-user-May-madness/0e44f0ad-a683-5f0d-9de6-9459ae328963/scratchpad';
const OUT = SC + '/vol9-skin';
fs.mkdirSync(OUT, { recursive: true });

const APP = process.env.APP || 'national-index.html';
const SABOTAGE = process.env.SABOTAGE || '';
const ONLY = process.env.ONLY || '';

let app = fs.readFileSync(APP, 'utf8');
if (SABOTAGE === 'noskin') {
  // KEYED ON THE id, NOT ON THE BANNER COMMENT. Three style blocks in the
  // shipped page begin "56 NATIONAL SERIES · VOL.9 SKIN" — the two inherited
  // volume skins have their banners rewritten by the wording sweep — and the
  // first version of this cut the August-era layer instead. Every check stayed
  // green and the sabotage proved nothing.
  const a = '<style id="vol9-skin">';
  if (!app.includes(a)) throw new Error('sabotage anchor (noskin) no longer matches');
  const i = app.indexOf(a);
  const j = app.indexOf('</style>', i);
  const cut = app.slice(i, j);
  if (!cut.includes('--paper: #B8141F'))
    throw new Error('sabotage (noskin) cut the wrong block — it has no Vol.9 token in it');
  app = app.slice(0, i) + app.slice(j + 8);
}
if (SABOTAGE === 'longname') {
  // Put the header back the way it collided: the full sub-line, and no
  // ellipsis on the volume name. The overlap check must go red.
  app = app.replace('URBAN SOCIAL &middot; VOL.9', 'URBAN SOCIAL SERIES &middot; VOL.9')
           .replace(/font-size: 17px !important;\n  overflow: hidden; text-overflow: ellipsis;/, '');
  if (app.includes('URBAN SOCIAL &middot; VOL.9'))
    throw new Error('sabotage anchor (longname) no longer matches');
}
if (SABOTAGE === 'noart') {
  // Blank the handoff's artwork, leaving the colours and shapes exactly as
  // they are. This is the state the first re-skin actually shipped in — a red
  // app with no khanjar tile, no masar weave and no landmarks — and every
  // check in this harness passed it. The motif assertions must go red.
  const n = (app.match(/data:image\/(png|svg\+xml)[^"')]*/g) || []).length;
  if (n < 3) throw new Error('sabotage anchor (noart) no longer matches');
  app = app.replace(/url\("data:image\/(png|svg\+xml)[^"]*"\)/g, 'none');
  // The landmark art is handed to React as a template literal, not written
  // into the HTML as a url(), so the sweep above does not reach it — and the
  // first version of this sabotage reported medallions 1/1 with the tile and
  // the band both blanked, which is a sabotage that half worked.
  const before = app;
  app = app.replace(/const LANDMARK_ART = \{[\s\S]*?\n\};/,
                    'const LANDMARK_ART = new Proxy({}, { get: () => "" });');
  if (app === before) throw new Error('sabotage anchor (noart, landmarks) no longer matches');
}
if (SABOTAGE === 'strip') {
  // Take the room back out from under the header's masar strip, which is how
  // the weave came to sit across the Arabic line.
  const a = '  padding-bottom: 30px !important;';
  if (!app.includes(a)) throw new Error('sabotage anchor (strip) no longer matches');
  app = app.replace(a, '  padding-bottom: 0 !important;');
}
if (SABOTAGE === 'unstick') {
  // Put the header back the way it scrolled away: `position: relative`, which
  // is what a rule anchoring its masar strip actually wrote.
  const a = '.sg-hero { position: relative; }';
  if (!app.includes(a)) throw new Error('sabotage anchor (unstick) no longer matches');
  app = app.replace(a, 'header, .sticky.top-0, .sg-hero { position: relative; }');
}
if (SABOTAGE === 'nofont') {
  const a = '<link href="https://fonts.googleapis.com/css2?family=Archivo';
  if (!app.includes(a)) throw new Error('sabotage anchor (nofont) no longer matches');
  app = app.replace(a, '<link href="https://fonts.example.invalid/none?family=Archivo');
}

// Chromium here does not trust the agent proxy's CA, so React, Babel and the
// Google Fonts stylesheet all fail with ERR_CERT_AUTHORITY_INVALID — and with
// no React there is no page at all to check. Everything is served locally.
const PORT = 8123;
const ORIGIN = `http://127.0.0.1:${PORT}`;
const VENDOR = SC + '/vendor';
for (const f of ['babel.js', 'react.js', 'react-dom.js'])
  if (!fs.existsSync(path.join(VENDOR, f)))
    throw new Error(`missing ${VENDOR}/${f} — fetch it with curl first`);

const FONTCSS = fs.readFileSync('brand/fonts/fonts.css', 'utf8')
  .replace(/url\(\.\//g, `url(${ORIGIN}/fonts/`);

// The app polls version.txt and reloads when it differs from the build id it
// was stamped with. Served wrong, the page reloads forever and nothing is ever
// stable enough to measure.
const VERSION = fs.existsSync(APP + '.version')
  ? fs.readFileSync(APP + '.version', 'utf8').trim() : '';

const state = fs.readFileSync(SC + '/na.json', 'utf8');
// Whether there is anything for a medallion to sit on. With no nights created
// the sessions screen is an empty-state card, and asserting medallions there
// would fail for the right reason — so the check is gated on real data rather
// than quietly dropped.
const SESSIONS = (() => {
  try { return (JSON.parse(state).state.sessions || []).length; } catch { return 0; }
})();
const photos = fs.readFileSync(SC + '/na-photos.json', 'utf8');

// A STATE WITH NIGHTS IN IT, so the landmark medallions are actually
// exercised. Vol.9 has not been played yet, so the real state has zero
// sessions and every medallion assertion passes vacuously — the landmark
// lookup, the artwork and the eyebrow would all ship having never rendered.
// The nights are the season file's own dates, which is what the organiser
// will create, not invented shapes.
const SEEDED = (() => {
  const st = JSON.parse(state);
  const cfg = JSON.parse(fs.readFileSync('national-season.json', 'utf8'));
  st.state.sessions = cfg.nights.map((d, i) => ({
    id: 's' + i, name: 'Session ' + (i + 1), date: d,
    groupCount: 4, qualifyCount: 2, teams: [], groupMatches: [],
    bracket: { qf: [], sf: [], final: null }, waitlist: [],
    doublePoints: cfg.doubleNights.includes(d), completed: false,
  }));
  return JSON.stringify(st);
})();

const srv = http.createServer({ maxHeaderSize: 1 << 20 }, (req, res) => {
  const u = (req.url || '/').split('?')[0];
  const json = (b) => { res.writeHead(200, { 'Content-Type': 'application/json' }); res.end(b); };
  if (u === '/version.txt') { res.writeHead(200, { 'Content-Type': 'text/plain' }); return res.end(VERSION); }
  if (u === '/state') return json(state);
  if (u === '/photos') return json(photos);
  if (u === '/session-photos') return json('{"ok":true,"photos":{}}');
  if (u.startsWith('/fonts/') && u.endsWith('.woff2')) {
    const f = path.join('brand/fonts', path.basename(u));
    if (fs.existsSync(f)) {
      res.writeHead(200, { 'Content-Type': 'font/woff2' });
      return res.end(fs.readFileSync(f));
    }
  }
  // The lockup and the icon live on the VPS beside the page; locally they are
  // in brand/national. A missing one is a broken-image glyph in the header,
  // which is worth seeing in the screenshot rather than 404ing.
  const b = path.basename(u);
  for (const d of ['brand/national', 'assets']) {
    const f = path.join(d, b.replace(/^national-/, 'national-'));
    if (/\.(png|webp|jpe?g|svg)$/.test(b) && fs.existsSync(f)) {
      res.writeHead(200, { 'Content-Type': 'image/' + b.split('.').pop() });
      return res.end(fs.readFileSync(f));
    }
  }
  res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
  res.end(app);
}).listen(PORT);

// ── what Vol.8 looked like ───────────────────────────────────────────────────
// Any of these computing anywhere on a Vol.9 screen is the sweep having missed
// something. The near-blacks are in here because they are the ones that got
// through the first pass: they are not the lead colour, so nothing about them
// says "Blackout" until you see a charcoal card on a red page.
const VOL8 = {
  'rgb(198, 255, 0)': 'Blackout lime',
  'rgb(255, 46, 136)': 'Blackout magenta',
  'rgb(5, 5, 5)': 'Blackout true black',
  'rgb(10, 10, 10)': 'Blackout surface',
  'rgb(14, 14, 14)': 'Blackout card',
  'rgb(20, 20, 20)': 'Blackout card 2',
  'rgb(42, 42, 42)': 'Blackout hairline',
};

// The five nav tabs as the app labels them — HOME, SESSIONS, RANK, ME, PLAYERS.
// Guessing a sixth ("more") printed "no tab" every run, which is a silent hole
// in the sweep dressed up as a result.
const SCREENS = ['home', 'sessions', 'rank', 'me', 'players'];

const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
const pg = await browser.newPage({
  viewport: { width: 430, height: 932 }, deviceScaleFactor: 2,
});
await pg.route('**/unpkg.com/**', r => {
  const url = r.request().url();
  const f = /babel/.test(url) ? 'babel.js' : /react-dom/.test(url) ? 'react-dom.js' : 'react.js';
  r.fulfill({ status: 200, contentType: 'application/javascript',
              body: fs.readFileSync(path.join(VENDOR, f), 'utf8') });
});
await pg.route('**/fonts.googleapis.com/**', r =>
  r.fulfill({ status: 200, contentType: 'text/css', body: FONTCSS }));

const errs = [];
pg.on('pageerror', e => errs.push(e.message));
await pg.goto(ORIGIN + '/', { waitUntil: 'load' });
await pg.waitForSelector('nav.fixed.bottom-0', { timeout: 25000 });
await pg.evaluate(() => document.fonts.ready);
await pg.waitForTimeout(600);

// ── the audit ───────────────────────────────────────────────────────────────
// It is run on EVERY tab, not just the one the app opens on. The first version
// swept the home screen alone and reported a clean page while four other
// screens were unmeasured — and the near-black card tints that survived the
// first colour pass were on the inner screens, which is exactly where a sweep
// misses things.
const AUDIT = () => {
  // Composite a colour down the ancestor chain until it is opaque. Reading
  // backgroundColor alone gives rgba(0,0,0,0) for most elements and a
  // confident, wrong 1.00:1.
  const parse = (c) => {
    const m = String(c).match(/rgba?\(([^)]+)\)/);
    if (!m) return null;
    const p = m[1].split(/[,\s/]+/).filter(Boolean).map(Number);
    return { r: p[0], g: p[1], b: p[2], a: p.length > 3 ? p[3] : 1 };
  };
  const over = (f, b) => ({
    r: f.r * f.a + b.r * (1 - f.a),
    g: f.g * f.a + b.g * (1 - f.a),
    b: f.b * f.a + b.b * (1 - f.a), a: 1,
  });
  const bgOf = (el) => {
    let acc = null;
    for (let e = el; e; e = e.parentElement) {
      const c = parse(getComputedStyle(e).backgroundColor);
      if (!c || !c.a) continue;
      acc = acc ? over(acc, c) : c;
      if (acc.a >= 1) break;
    }
    if (!acc || acc.a < 1) acc = over(acc || { r: 0, g: 0, b: 0, a: 0 }, { r: 184, g: 20, b: 31, a: 1 });
    return acc;
  };
  const lum = (c) => {
    const f = (v) => { v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); };
    return 0.2126 * f(c.r) + 0.7152 * f(c.g) + 0.0722 * f(c.b);
  };
  const ratio = (a, b) => {
    const [x, y] = [lum(a), lum(b)].sort((p, q) => q - p);
    return (x + 0.05) / (y + 0.05);
  };

  const all = [...document.querySelectorAll('body *')];
  const visible = all.filter(e => {
    const s = getComputedStyle(e);
    if (s.display === 'none' || s.visibility === 'hidden' || +s.opacity === 0) return false;
    const b = e.getBoundingClientRect();
    return b.width > 0 && b.height > 0;
  });

  // 1 · Vol.8 colours, read off the render.
  const VOL8 = ['rgb(198, 255, 0)', 'rgb(255, 46, 136)', 'rgb(5, 5, 5)',
                'rgb(10, 10, 10)', 'rgb(14, 14, 14)', 'rgb(20, 20, 20)',
                'rgb(42, 42, 42)'];
  const stale = [];
  for (const e of visible) {
    const s = getComputedStyle(e);
    for (const prop of ['color', 'backgroundColor', 'borderTopColor', 'borderBottomColor']) {
      const v = s[prop];
      const hit = VOL8.find(c => v === c || v.startsWith(c.slice(0, -1) + ','));
      if (hit) stale.push({
        prop, value: v, hit,
        where: (e.className || e.tagName) + ' "' + (e.textContent || '').trim().slice(0, 24) + '"',
      });
    }
  }

  // 2 · Contrast, on leaf text runs only. A wrapper's textContent is all its
  // children's, and its own colour is not what anybody reads.
  // A path worth reading in a failure line. "rose on red somewhere" is not
  // actionable; `header > div > div` is.
  const pathOf = (el) => {
    const bits = [];
    for (let e = el; e && e !== document.body && bits.length < 4; e = e.parentElement) {
      const c = (typeof e.className === 'string' ? e.className : '').trim().split(/\s+/)[0];
      bits.unshift(e.tagName.toLowerCase() + (c ? '.' + c : ''));
    }
    return bits.join('>');
  };

  const bad = [];
  for (const e of visible) {
    if (e.childElementCount) continue;
    const t = (e.textContent || '').trim();
    if (!t) continue;
    // Decorative type is not type. The volume watermark is a 170px ghost
    // behind the copy and is deliberately 1.1:1 — auditing it as text is how a
    // contrast check gets ignored. It says so itself, with aria-hidden.
    if (e.closest('[aria-hidden="true"]')) continue;
    const s = getComputedStyle(e);
    const fg = parse(s.color);
    if (!fg) continue;
    const px = parseFloat(s.fontSize);
    const wt = parseInt(s.fontWeight) || 400;
    // WCAG's large-text allowance: 24px, or 18.66px at 700+.
    const need = (px >= 24 || (px >= 18.66 && wt >= 700)) ? 3 : 4.5;
    const r = ratio(over(fg, bgOf(e)), bgOf(e));
    if (r < need) bad.push({ text: t.slice(0, 34), px, wt, need, ratio: +r.toFixed(2),
                             where: pathOf(e), fg: s.color });
  }

  // 3 · Shapes. NO SQUARE BLOCKS is the whole difference between this volume
  // and Blackout's radius-0-everywhere, so a surface that kept its corners
  // reads as Vol.8 no matter what colour it is wearing.
  const square = [];
  for (const e of visible) {
    const b = e.getBoundingClientRect();
    if (b.width < 120 || b.height < 44) continue;        // a surface, not a chip
    const s = getComputedStyle(e);
    if (parse(s.backgroundColor)?.a < 0.5) continue;      // has to BE a surface
    const r = Math.min(...['TopLeft', 'TopRight', 'BottomLeft', 'BottomRight']
      .map(k => parseFloat(s['border' + k + 'Radius']) || 0));
    if (r < 12) square.push({
      where: (e.className || e.tagName).toString().slice(0, 40),
      radius: s.borderRadius, size: `${Math.round(b.width)}x${Math.round(b.height)}`,
    });
  }

  // 3a · NOTHING MAY BE ELLIPSISED. Every nowrap line in this app carries
  // text-overflow:ellipsis as a backstop, and a backstop that is FIRING is a
  // layout that did not fit — "56 NATIONAL SERI…" in the one bar that is on
  // every screen, with no overflow and no overlap for any other check to see,
  // because clipping is what ellipsis does instead of overflowing.
  const clipped = [];
  for (const e of visible) {
    if (e.childElementCount) continue;
    const t = (e.textContent || '').trim();
    if (!t) continue;
    if (e.scrollWidth > e.clientWidth + 1)
      clipped.push(`"${t.slice(0, 26)}" needs ${e.scrollWidth}px in ${e.clientWidth}px`);
  }

  // 3a2 · NO DECORATIVE STRIP MAY LIE ACROSS TEXT. The masar weave is drawn
  // as an ::after inside the header, the hero and the ivory panel — which is
  // neither a text run nor a box in flow, so the clipped check and the
  // overlap check are both blind to it. It sat straight across the header's
  // Arabic line. Measured against the pseudo-element's own box.
  const strips = [];
  for (const sel of ['header', '.sg-hero', '.na-ivory']) {
    for (const host of document.querySelectorAll(sel)) {
      const cs = getComputedStyle(host, '::after');
      const h = parseFloat(cs.height);
      if (!h || cs.content === 'none') continue;
      const hb = host.getBoundingClientRect();
      const top = hb.bottom - h;
      for (const e of host.querySelectorAll('*')) {
        if (e.childElementCount) continue;
        const t = (e.textContent || '').trim();
        if (!t) continue;
        const rg = document.createRange(); rg.selectNodeContents(e);
        for (const q of rg.getClientRects())
          if (q.bottom > top + 2 && q.top < hb.bottom - 2 && q.width > 1)
            strips.push(`${sel} strip over "${t.slice(0, 24)}"`);
      }
    }
  }

  // 3b · NO TWO TEXT RUNS MAY OVERLAP. This is the check that catches a
  // collision, and nothing else here does: "56 NATIONAL SERIES" ran straight
  // under the SYNCED button with every width assertion green, because nowrap
  // text that is wider than its box does not overflow anything the box checks
  // can see — it just sits on its neighbour.
  // Measured per LINE BOX and only across BLOCKS: getBoundingClientRect on a
  // run that wraps spans the whole paragraph and overlaps every sibling in it,
  // and inline runs inside one paragraph share line boxes by definition, which
  // is how prose works. Anything else is all false positives.
  const blockOf = (el) => {
    for (let e = el; e; e = e.parentElement)
      if (!/^(inline|contents|ruby.*)$/.test(getComputedStyle(e).display)) return e;
    return null;
  };
  const runs = [];
  for (const e of visible) {
    if (e.childElementCount) continue;
    if (!(e.textContent || '').trim()) continue;
    if (e.closest('[aria-hidden="true"]')) continue;
    // The tab bar FLOATS over the page and the header is sticky — both are
    // meant to sit on top of whatever scrolls under them, so chrome against
    // page is not a collision, it is the design. Chrome against CHROME still
    // is, and that is the case this check was added for, so they are tagged
    // rather than dropped: skipping the header outright would have excused
    // exactly the bug that prompted writing this.
    const chrome = !!e.closest('nav.fixed, header, .sticky.top-0');
    // A RANGE OVER THE TEXT, NOT THE ELEMENT'S BOX. This is the whole point:
    // nowrap text that is wider than its box does not widen the box, so the
    // element's own rect stops where the box stops and the collision is
    // invisible to it. "56 NATIONAL SERIES" sat on SYNCED while its div
    // measured a comfortable 180px. The Range measures where the type is.
    const rg = document.createRange();
    rg.selectNodeContents(e);
    for (const r of rg.getClientRects())
      if (r.width > 1 && r.height > 1) runs.push({ e, r, b: blockOf(e), chrome });
  }
  const overlap = [];
  for (let i = 0; i < runs.length; i++) for (let j = i + 1; j < runs.length; j++) {
    const a = runs[i], b = runs[j];
    if (a.chrome !== b.chrome) continue;
    if (a.b === b.b) continue;
    if (a.b && b.b && (a.b.contains(b.b) || b.b.contains(a.b))) continue;
    const w = Math.min(a.r.right, b.r.right) - Math.max(a.r.left, b.r.left);
    const h = Math.min(a.r.bottom, b.r.bottom) - Math.max(a.r.top, b.r.top);
    // A Range box is a line box, not the ink, so a few px of nominal overlap
    // between neighbours is normal. A real collision is much more than that.
    if (w > 6 && h > 6) overlap.push(
      `"${a.e.textContent.trim().slice(0, 20)}" over "${b.e.textContent.trim().slice(0, 20)}"`
      + ` by ${Math.round(w)}x${Math.round(h)}`);
  }

  // 4 · Nothing past the viewport, and no sideways scroll. A 3100px lockup in a
  // 430px header did exactly this.
  const W = document.documentElement.clientWidth;
  const past = visible.filter(e => e.getBoundingClientRect().right > W + 1)
    .map(e => (e.className || e.tagName).toString().slice(0, 40) + ' -> '
      + Math.round(e.getBoundingClientRect().right));

  // 5 · The volume watermark: present, saying 09, and still a GHOST. The
  // effective alpha is what matters, and it is not what the inline style says
  // — an !important colour rule upstream beat it once already.
  const marks = [...document.querySelectorAll('.vol-mark')].map(e => {
    const c = parse(getComputedStyle(e).color);
    return { text: (e.textContent || '').trim(), alpha: +(c ? c.a : 1).toFixed(3),
             px: parseFloat(getComputedStyle(e).fontSize) };
  });

  // 5b · THE MOTIFS ARE ON THE PAGE. This volume's identity is the khanjar
  // tile, the masar weave and the landmark medallions, and all three are
  // background-images that fail SILENTLY: a missing one is a flat rectangle
  // in the right colour, which is exactly what the first re-skin shipped and
  // what every other check here would pass. So each is asked for by name.
  // `url("")` starts with url( and draws nothing, which is exactly what a
  // blanked asset looks like — so the test is for a real image, not for the
  // syntax of one. Found by sabotage: with every data URL stripped, the
  // medallions still reported as drawn.
  const drawn = (v) => /url\(["']?data:image\/[a-z+]+[;,]/.test(v);
  const bgimg = (el, pseudo) => (el ? getComputedStyle(el, pseudo).backgroundImage : '') || 'none';
  const motifs = {
    khanjar: drawn(bgimg(document.body, '::before')),
    masar: drawn(bgimg(document.body, '::after')),
    masarHeader: drawn(bgimg(document.querySelector('header'), '::after')),
    mark56: [...document.querySelectorAll('header span')]
      .some(x => (x.textContent || '').trim() === '56'),
    arabic: /[\u0600-\u06FF]/.test(document.querySelector('header')?.innerText || ''),
    medallions: [...document.querySelectorAll('.na-medallion')]
      .filter(x => drawn(bgimg(x))).length,
    medallionTotal: document.querySelectorAll('.na-medallion').length,
  };

  // 6 · Archivo really DRAWN, measured against the same stack falling back.
  // getComputedStyle reports the stylesheet and document.fonts.check() answers
  // true with zero faces loaded.
  const probe = (stack) => {
    const s = document.createElement('span');
    s.textContent = 'NATIONAL HAMBURGEFONS 56';
    s.style.cssText = 'position:absolute;visibility:hidden;white-space:nowrap;'
      + 'font-size:100px;font-style:italic;font-weight:900;font-family:' + stack;
    document.body.appendChild(s);
    const w = s.getBoundingClientRect().width; s.remove(); return w;
  };

  return {
    stale, bad, square, past, marks, clipped, motifs, strips: [...new Set(strips)], overlap: [...new Set(overlap)],
    archivo: probe("'Archivo',serif") !== probe('serif'),
    pageBg: getComputedStyle(document.body).backgroundColor,
    scrollX: document.documentElement.scrollWidth > W + 1,
    counted: visible.length,
  };
};

// ── the shapes that are named, not merely generic ────────────────────────────
const NAMED = () => {
  const g = (sel) => {
    const e = document.querySelector(sel);
    if (!e) return null;
    const s = getComputedStyle(e);
    const b = e.getBoundingClientRect();
    return { radius: s.borderRadius, bg: s.backgroundColor,
             left: Math.round(b.left), width: Math.round(b.width) };
  };
  return { hero: g('.sg-hero'), nav: g('nav.fixed.bottom-0.inset-x-0'), card: g('.sg-card') };
};

const openTab = (label) => pg.evaluate((l) => {
  const b = [...document.querySelectorAll('nav.fixed.bottom-0 button, nav.fixed.bottom-0 a')]
    .find(x => (x.innerText || '').trim().toLowerCase().startsWith(l));
  if (!b) return false;
  b.click(); return true;
}, label);

const uniq = (a, k) => [...new Map(a.map(x => [k(x), x])).values()];
const fail = [];
const seen = [];

console.log(`${APP}${SABOTAGE ? '  SABOTAGE=' + SABOTAGE : ''}`);

for (const screen of SCREENS) {
  if (ONLY && !screen.includes(ONLY)) continue;
  if (screen !== 'home') {
    if (!await openTab(screen)) { fail.push(`there is no ${screen.toUpperCase()} tab`); continue; }
    await pg.waitForTimeout(700);
    await pg.evaluate(() => document.fonts.ready);
  }
  if (process.env.WHY) {
    // WHY=<text> explains ONE failing run: which rules set its colour, and in
    // what order. Guessing which stylesheet won is how an afternoon goes.
    const why = await pg.evaluate((needle) => {
      const el = [...document.querySelectorAll('body *')]
        .find(e => !e.childElementCount && (e.textContent || '').trim() === needle);
      if (!el) return null;
      const rules = [];
      for (const sh of document.styleSheets) {
        let list; try { list = sh.cssRules; } catch { continue; }
        for (const r of list) {
          if (!r.selectorText || !r.style || !r.style.color) continue;
          try { if (el.matches(r.selectorText)) rules.push(r.selectorText + ' { color: ' + r.style.color
            + (r.style.getPropertyPriority('color') ? ' !important' : '') + ' }'); } catch {}
        }
      }
      return { inline: el.getAttribute('style'), computed: getComputedStyle(el).color, rules };
    }, process.env.WHY);
    console.log('\n  WHY ' + JSON.stringify(why, null, 2));
  }
  // THE CHROME MUST SURVIVE A SCROLL. Nothing here looked at the page in any
  // state but the top of it, and a skin rule that set `position: relative` on
  // the header to anchor its masar strip silently overrode Tailwind's
  // `sticky` — so the brand bar scrolled away and the FIXED band at the top
  // was left floating over the content on its own. Reported as "a gradient in
  // the top part that moves while you scroll".
  const scrolled = await pg.evaluate(async () => {
    const h = document.querySelector('header');
    const nav = document.querySelector('nav.fixed.bottom-0');
    window.scrollTo(0, 600);
    await new Promise(r => setTimeout(r, 300));
    const y = window.scrollY;
    const out = {
      scrolled: Math.round(y),
      headerPos: h ? getComputedStyle(h).position : 'none',
      headerTop: h ? Math.round(h.getBoundingClientRect().top) : null,
      navBottom: nav ? Math.round(innerHeight - nav.getBoundingClientRect().bottom) : null,
    };
    window.scrollTo(0, 0);
    await new Promise(r => setTimeout(r, 250));
    return out;
  });

  const a = await pg.evaluate(AUDIT);
  const n = await pg.evaluate(NAMED);
  const shot = `${OUT}/${screen}.png`;
  // VIEWPORT, NOT fullPage. The roster is 338 people: a full-page shot of it
  // is 91,000px tall, which is not a thing anybody can look at — and looking
  // at it is the entire reason the shot exists.
  await pg.screenshot({ path: shot });
  seen.push(screen);

  const F = (m) => fail.push(`[${screen}] ${m}`);
  console.log(`\n  ${screen.toUpperCase()}  ${a.counted} elements  ${shot}`);
  if (n.hero) console.log(`    .sg-hero  ${n.hero.radius}  ${n.hero.bg}`);
  if (n.nav)  console.log(`    nav       ${n.nav.radius}  ${n.nav.bg}  left ${n.nav.left}`);
  if (n.card) console.log(`    .sg-card  ${n.card.radius}  ${n.card.bg}`);
  if (a.marks.length)
    console.log(`    mark      ${a.marks.map(m => `"${m.text}" ${m.px}px a=${m.alpha}`).join(', ')}`);

  if (!a.archivo) F('Archivo was NOT drawn — it fell back');
  if (scrolled.scrolled > 40) {
    // Only meaningful on a screen long enough to scroll.
    if (scrolled.headerPos !== 'sticky')
      F(`the header is ${scrolled.headerPos}, not sticky — it scrolls away`);
    if (Math.abs(scrolled.headerTop) > 2)
      F(`the header left the top of the screen on scroll (top ${scrolled.headerTop})`);
    if (scrolled.navBottom !== null && Math.abs(scrolled.navBottom - 14) > 4)
      F(`the tab bar moved on scroll (${scrolled.navBottom}px from the bottom)`);
  }
  const m = a.motifs;
  console.log(`    motifs    khanjar ${m.khanjar ? 'y' : 'NO'}  masar ${m.masar ? 'y' : 'NO'}`
    + `  header-weave ${m.masarHeader ? 'y' : 'NO'}  "56" ${m.mark56 ? 'y' : 'NO'}`
    + `  arabic ${m.arabic ? 'y' : 'NO'}  medallions ${m.medallions}/${m.medallionTotal}`);
  if (!m.khanjar) F('the khanjar tile is not drawn — the ground is flat colour');
  if (!m.masar) F('the masar band is not drawn');
  if (!m.masarHeader) F("the header's masar strip is not drawn");
  if (!m.mark56) F('the "56" mark is not in the header');
  if (!m.arabic) F('there is no Arabic in the header');
  // A medallion with no art is a plain red disc, which looks deliberate.
  if (m.medallionTotal !== m.medallions)
    F(`${m.medallionTotal - m.medallions} landmark medallion(s) carry no artwork`);
  if (screen === 'sessions' && SESSIONS && !m.medallionTotal)
    F('the sessions screen has no landmark medallions');
  if (a.pageBg !== 'rgb(184, 20, 31)') F(`the page ground is ${a.pageBg}, not the National red`);
  if (a.scrollX) F('the page scrolls sideways');
  if (!n.nav || parseFloat(n.nav.radius) < 100 || n.nav.left < 4)
    F(`the tab bar is not a floating pill: ${JSON.stringify(n.nav)}`);
  // The arch is a HOME-screen surface; the inner screens have no .sg-hero, and
  // asserting one there would fail for the right shape being absent.
  if (n.hero && parseFloat(n.hero.radius) < 100) F(`the hero is not an arch: ${n.hero.radius}`);
  if (screen === 'home' && !n.hero) F('there is no .sg-hero on the home screen');
  if (screen === 'home' && !a.marks.length) F('the volume watermark is gone');
  for (const m of a.marks) {
    if (m.text !== '09') F(`the watermark says "${m.text}", not 09`);
    // A ghost, not a slab. 12% is already generous for a 170px numeral lying
    // across the headline; full opacity is the bug this check exists for.
    if (m.alpha > 0.12) F(`the watermark is a slab, not a ghost: alpha ${m.alpha} at ${m.px}px`);
  }

  const staleU = uniq(a.stale, x => x.hit + x.prop);
  if (staleU.length) {
    F(`${a.stale.length} element(s) still compute a Vol.8 colour`);
    for (const x of staleU.slice(0, 8)) console.log(`    !! ${x.hit} as ${x.prop} on ${x.where}`);
  }
  if (a.clipped.length) {
    F(`${a.clipped.length} text run(s) clipped to an ellipsis`);
    for (const c of [...new Set(a.clipped)].slice(0, 6)) console.log(`    !! ${c}`);
  }
  if (a.strips.length) {
    F(`${a.strips.length} decorative strip(s) lying across text`);
    for (const x of a.strips.slice(0, 5)) console.log(`    !! ${x}`);
  }
  if (a.overlap.length) {
    F(`${a.overlap.length} pair(s) of text runs overlap`);
    for (const o of a.overlap.slice(0, 6)) console.log(`    !! ${o}`);
  }
  if (a.past.length) {
    F(`${a.past.length} element(s) run past the right edge`);
    for (const p of a.past.slice(0, 5)) console.log(`    !! ${p}`);
  }
  if (a.square.length) {
    F(`${a.square.length} square surface(s) — this volume has no square blocks`);
    for (const x of uniq(a.square, y => y.where).slice(0, 6))
      console.log(`    !! ${x.where}  ${x.radius}  ${x.size}`);
  }
  const badU = uniq(a.bad, x => x.text + x.px);
  if (badU.length) {
    F(`${badU.length} text run(s) under contrast`);
    for (const b of badU.slice(0, 10))
      console.log(`    !! ${b.ratio}:1 (needs ${b.need}) ${b.px}px/${b.wt} ${b.fg}`
        + `\n         "${b.text}"  in ${b.where}`);
  }
}

// ── the seeded pass ─────────────────────────────────────────────────────────
// The real Vol.9 state has no nights yet, so everything the landmark work
// touches — the lookup, the artwork, the medallion, the "DATE · LANDMARK"
// eyebrow — renders zero times in the sweep above and every assertion about it
// passes having seen nothing. This serves the season's own nine dates and
// checks the motif on a screen that has something to draw.
if (!ONLY) {
  await pg.route('**/state', r =>
    r.fulfill({ status: 200, contentType: 'application/json', body: SEEDED }));
  await pg.goto(ORIGIN + '/?seeded', { waitUntil: 'load' });
  await pg.waitForSelector('nav.fixed.bottom-0', { timeout: 25000 });
  await pg.evaluate(() => document.fonts.ready);
  await pg.waitForTimeout(600);
  if (!await openTab('sessions')) fail.push('[seeded] there is no SESSIONS tab');
  await pg.waitForTimeout(800);

  // THE CHROME MUST SURVIVE A SCROLL. Nothing here looked at the page in any
  // state but the top of it, and a skin rule that set `position: relative` on
  // the header to anchor its masar strip silently overrode Tailwind's
  // `sticky` — so the brand bar scrolled away and the FIXED band at the top
  // was left floating over the content on its own. Reported as "a gradient in
  // the top part that moves while you scroll".
  const scrolled = await pg.evaluate(async () => {
    const h = document.querySelector('header');
    const nav = document.querySelector('nav.fixed.bottom-0');
    window.scrollTo(0, 600);
    await new Promise(r => setTimeout(r, 300));
    const y = window.scrollY;
    const out = {
      scrolled: Math.round(y),
      headerPos: h ? getComputedStyle(h).position : 'none',
      headerTop: h ? Math.round(h.getBoundingClientRect().top) : null,
      navBottom: nav ? Math.round(innerHeight - nav.getBoundingClientRect().bottom) : null,
    };
    window.scrollTo(0, 0);
    await new Promise(r => setTimeout(r, 250));
    return out;
  });

  const a = await pg.evaluate(AUDIT);
  const land = await pg.evaluate(() => {
    const out = [...document.querySelectorAll('.na-medallion')].map(e => ({
      art: /url\(["']?data:image\/svg/.test(getComputedStyle(e).backgroundImage),
      name: e.getAttribute('title') || '',
      size: Math.round(e.getBoundingClientRect().width),
      radius: getComputedStyle(e).borderRadius,
    }));
    // The eyebrow must NAME the landmark, or the disc is decoration rather
    // than a label — which is the difference between a motif and a sticker.
    const eyebrows = [...document.querySelectorAll('.jh-mock-sess')]
      .map(r => (r.innerText || '').split('\n')[0]);
    return { out, eyebrows };
  });
  await pg.screenshot({ path: `${OUT}/sessions-seeded.png` });
  seen.push('seeded');

  const names = [...new Set(land.out.map(x => x.name))].filter(Boolean);
  console.log(`\n  SEEDED  ${land.out.length} nights  ${OUT}/sessions-seeded.png`);
  console.log(`    landmarks ${names.join(', ') || 'NONE'}`);
  const F = (m) => fail.push(`[seeded] ${m}`);
  if (!land.out.length) F('nine nights and no landmark medallions');
  if (land.out.some(x => !x.art)) F('a medallion carries no landmark artwork');
  if (land.out.some(x => x.radius !== '50%')) F('a medallion is not a circle');
  if (land.out.some(x => x.size < 36)) F('a medallion is smaller than its slot');
  // EVERY LANDMARK IN THE SEASON FILE SHOULD GET USED, or the cycle is not
  // cycling. Read from the file rather than typed: the set was four and is
  // six, and a hard-coded four failed for the right reason at the wrong time.
  const want = JSON.parse(fs.readFileSync('national-season.json', 'utf8')).landmarks.length;
  const expect = Math.min(want, land.out.length);
  if (names.length !== expect)
    F(`${names.length} distinct landmarks over ${land.out.length} nights, expected ${expect}`);
  if (!land.eyebrows.some(t => /·/.test(t) && names.some(n => t.includes(n.toUpperCase()))))
    F('no row eyebrow names its landmark');
  if (a.clipped.length) F(`${a.clipped.length} text run(s) clipped: ${a.clipped[0]}`);
  if (a.overlap.length) F(`${a.overlap.length} overlap(s): ${a.overlap[0]}`);
  if (a.past.length) F(`${a.past.length} element(s) past the right edge`);
  const badU2 = uniq(a.bad, x => x.text + x.px);
  if (badU2.length) {
    F(`${badU2.length} text run(s) under contrast`);
    for (const b of badU2.slice(0, 6))
      console.log(`    !! ${b.ratio}:1 (needs ${b.need}) ${b.px}px "${b.text}"`);
  }
}

await pg.close();
await browser.close();
srv.close();

if (errs.length) fail.push('page errors: ' + errs.slice(0, 3).join(' | '));
// A sweep that quietly covered one screen is the hole this harness was written
// to close, so the count is asserted rather than printed.
const want = SCREENS.filter(s => !ONLY || s.includes(ONLY)).length + (ONLY ? 0 : 1);
if (seen.length !== want) fail.push(`only ${seen.length} of ${want} screens were measured`);

if (fail.length) {
  console.error('\n' + fail.map(f => '  !! ' + f).join('\n'));
  process.exit(1);
}
console.log(`\nok — Vol.9 is wearing Vol.9 on all ${seen.length} screens`);
