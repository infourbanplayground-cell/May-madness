// Prove the wall (?tv=) actually renders on a giant portrait screen.
//
// Every check here exists because a layout assertion that only looks at the
// ELEMENT box passes while the text inside it is clipped — the same failure
// DESIGN.md records for the Blackout lockup and the FINAL WEEK headline. So:
//
//   · the page must not scroll in either axis (a wall has no scrollbar, so
//     anything past the fold is simply not on the screen)
//   · no panel may fall outside the wall's own box
//   · NO TEXT MAY BE ELLIPSISED. Every name on this screen carries
//     text-overflow:ellipsis as a backstop; if the backstop is firing, a
//     player is reading half of somebody's name from across the court.
//   · the display face must really be DRAWN, measured against a face it
//     cannot be — getComputedStyle reports the stylesheet, not the paint
//   · the group letters, the tables and the figures must actually be there,
//     so a blank panel cannot pass as a clean layout
//
//   node ops/check-wall.mjs
import { chromium } from 'playwright';
import fs from 'fs';
import http from 'http';
import path from 'path';

const SC = '/tmp/claude-0/-home-user-May-madness/0e44f0ad-a683-5f0d-9de6-9459ae328963/scratchpad';
const OUT = SC + '/wall';
fs.mkdirSync(OUT, { recursive: true });

const state = fs.readFileSync(SC + '/bo-now.json', 'utf8');
const photos = fs.readFileSync(SC + '/bo-photos.json', 'utf8');
// A check nobody has watched fail is not a check. SABOTAGE breaks one thing on
// purpose and the run must go red:
//   SABOTAGE=narrow  squeezes the team column, so names are clipped
//   SABOTAGE=nofont  drops the webfont, so the display face falls back
const SABOTAGE = process.env.SABOTAGE || '';
let app = fs.readFileSync('blackout-index.html', 'utf8');
if (SABOTAGE === 'narrow') {
  const a = 'gridTemplateColumns: `${wu(1.9)} 1fr ${wu(3)} ${wu(3.4)} ${wu(4.2)}`,';
  if (!app.includes(a)) throw new Error('sabotage anchor (narrow) no longer matches');
  app = app.replace(a, 'gridTemplateColumns: `${wu(1.9)} ${wu(6)} ${wu(3)} ${wu(3.4)} ${wu(4.2)}`,');
}
if (SABOTAGE === 'nofont') {
  const a = '<link href="https://fonts.googleapis.com/css2?family=Archivo';
  if (!app.includes(a)) throw new Error('sabotage anchor (nofont) no longer matches');
  app = app.replace(a, '<link href="https://fonts.example.invalid/none?family=Archivo');
}

// Chromium in this container does NOT trust the agent proxy's CA, so React,
// Babel and the Google Fonts stylesheet all fail with
// ERR_CERT_AUTHORITY_INVALID — and with no React there is no page at all to
// check. Everything the app loads is therefore served locally: the three CDN
// scripts fetched up front with curl (which does trust the CA), and the fonts
// already vendored in brand/fonts for exactly this reason.
const PORT = 8111;
const ORIGIN = `http://127.0.0.1:${PORT}`;
const VENDOR = SC + '/vendor';
for (const f of ['babel.js', 'react.js', 'react-dom.js'])
  if (!fs.existsSync(path.join(VENDOR, f))) throw new Error(`missing ${VENDOR}/${f} — fetch it with curl first`);

// The stylesheet is fulfilled for a fonts.googleapis.com URL, so its own
// relative src urls would resolve against that origin. Absolute local ones
// instead.
const FONTCSS = fs.readFileSync('brand/fonts/fonts.css', 'utf8')
  .replace(/url\(\.\//g, `url(${ORIGIN}/fonts/`);

// maxHeaderSize is raised because the default 16KB makes node answer 431 to a
// request it cannot parse, and Chromium then paints its own error page — which
// looks exactly like the app failing to render.
const VERSION = fs.existsSync('blackout-index.html.version')
  ? fs.readFileSync('blackout-index.html.version', 'utf8').trim() : '';

const srv = http.createServer({ maxHeaderSize: 1 << 20 }, (req, res) => {
  const u = (req.url || '/').split('?')[0];
  // The app polls version.txt and reloads when it differs from the build id it
  // was stamped with. Served wrong, the page reloads forever.
  if (u === '/version.txt') {
    res.writeHead(200, { 'Content-Type': 'text/plain' });
    return res.end(VERSION);
  }
  if (u.startsWith('/fonts/') && u.endsWith('.woff2')) {
    const f = path.join('brand/fonts', path.basename(u));
    if (fs.existsSync(f)) {
      res.writeHead(200, { 'Content-Type': 'font/woff2' });
      return res.end(fs.readFileSync(f));
    }
  }
  res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
  res.end(app);
}).listen(PORT);

const vendorRoutes = async (p) => {
  await p.route('**/unpkg.com/**', r => {
    const url = r.request().url();
    const f = /babel/.test(url) ? 'babel.js' : /react-dom/.test(url) ? 'react-dom.js' : 'react.js';
    r.fulfill({ status: 200, contentType: 'application/javascript',
                body: fs.readFileSync(path.join(VENDOR, f), 'utf8') });
  });
  await p.route('**/fonts.googleapis.com/**', r =>
    r.fulfill({ status: 200, contentType: 'text/css', body: FONTCSS }));
};

const sessions = JSON.parse(state).state.sessions;
const byDate = (d) => sessions.find(s => s.date === d);

const CASES = [
  { name: 'tonight-groups', date: '2026-10-26', tv: 'groups' },   // 4 groups, nothing scored
  { name: 'tonight-teams',  date: '2026-10-26', tv: 'teams'  },
  { name: 'full-groups',    date: '2026-10-14', tv: 'groups' },   // 4 groups, all 24 played
  { name: 'full-teams',     date: '2026-10-14', tv: 'teams'  },
  { name: 'uneven-groups',  date: '2026-10-21', tv: 'groups' },   // 3 groups, 3/4/4, byes
  { name: 'cycle',          date: '2026-10-26', tv: '1'      },
];

// ONLY narrows the sweep to the cases whose name matches, for a quick pass
// or a sabotage run.
const ONLY = process.env.ONLY || '';

const SIZES = [
  { label: '1080x1920', width: 1080, height: 1920 },
  { label: '2160x3840', width: 2160, height: 3840 },
  // A 16:9 TV that somebody forgot to rotate. It must degrade, not overflow.
  { label: '1920x1080', width: 1920, height: 1080 },
];

const b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
let fails = 0;

for (const size of SIZES) {
  if (ONLY && !size.label.includes(ONLY) && !CASES.some(c => c.name.includes(ONLY))) continue;
  for (const c of CASES) {
    if (ONLY && !c.name.includes(ONLY) && !size.label.includes(ONLY)) continue;
    const sess = byDate(c.date);
    const p = await b.newPage({ viewport: { width: size.width, height: size.height } });
    await vendorRoutes(p);
    await p.route('**/state', r => r.fulfill({ status: 200, contentType: 'application/json', body: state }));
    await p.route('**/photos', r => r.fulfill({ status: 200, contentType: 'application/json', body: photos }));
    await p.route('**/session-photos*', r => r.fulfill({ status: 200, contentType: 'application/json', body: '[]' }));
    await p.route('**/history', r => r.fulfill({ status: 200, contentType: 'application/json', body: '[]' }));
    const errs = [];
    p.on('pageerror', e => errs.push(String(e)));
    await p.goto(`${ORIGIN}/index.html?tv=${c.tv}&s=${sess.id}`,
                 { waitUntil: 'load', timeout: 60000 });
    await p.waitForTimeout(5000);
    await p.evaluate(() => document.fonts.ready);
    await p.waitForTimeout(400);

    const r = await p.evaluate(() => {
      const wall = document.querySelector('.wall');
      if (!wall) return { missing: true };
      const wb = wall.getBoundingClientRect();
      const out = {
        scroll: [document.documentElement.scrollWidth - window.innerWidth,
                 document.documentElement.scrollHeight - window.innerHeight],
        panels: [], clipped: [], overlap: [], letters: [], text: wall.innerText,
        wallBox: [wb.width, wb.height],
      };
      // A panel is a direct grid child of the body grid.
      const body = wall.children[1];
      for (const el of body ? body.children : []) {
        const r2 = el.getBoundingClientRect();
        out.panels.push([Math.round(r2.left), Math.round(r2.top), Math.round(r2.width), Math.round(r2.height),
                         r2.bottom <= wb.bottom + 1 && r2.right <= wb.right + 1]);
      }
      // Clipping, measured on the INK: scrollWidth past clientWidth means the
      // text inside is wider than the box drawing it, ellipsis or not.
      for (const el of wall.querySelectorAll('*')) {
        if (el.children.length) continue;
        const t = (el.textContent || '').trim();
        if (!t) continue;
        if (el.scrollWidth > el.clientWidth + 1 && el.clientWidth > 0)
          out.clipped.push([t.slice(0, 40), el.scrollWidth, el.clientWidth]);
        // Vertically, only a box that actually CLIPS counts. Display type is
        // set with a line-height under 1, so its line box is routinely taller
        // than the element and nothing is lost — flagging that is noise, and
        // noise is how a real failure gets scrolled past.
        const ov = getComputedStyle(el).overflowY;
        if ((ov === 'hidden' || ov === 'clip' || ov === 'auto')
            && el.scrollHeight > el.clientHeight + 2 && el.clientHeight > 0)
          out.clipped.push([t.slice(0, 40) + ' (height)', el.scrollHeight, el.clientHeight]);
      }
      // OVERLAP. The clipping check above only fires when a box actually
      // clips its text; a grid cell with no overflow rule simply lets the name
      // run out over the W column instead, which looks like two things printed
      // on top of each other and passes every width assertion. Leaf text boxes
      // must not intersect. The oversized ghost letter behind each table is
      // deliberate and carries data-ghost.
      {
        const leaves = [...wall.querySelectorAll('*')].filter(el =>
          !el.children.length && (el.textContent || '').trim()
          && !el.closest('[data-ghost]'));
        const boxes = leaves.map(el => [el.getBoundingClientRect(), (el.textContent || '').trim()]);
        for (let i = 0; i < boxes.length; i++) for (let j = i + 1; j < boxes.length; j++) {
          const [a2, t1] = boxes[i], [b2, t2] = boxes[j];
          const ox = Math.min(a2.right, b2.right) - Math.max(a2.left, b2.left);
          const oy = Math.min(a2.bottom, b2.bottom) - Math.max(a2.top, b2.top);
          if (ox > 2 && oy > 2) out.overlap.push([t1.slice(0, 24), t2.slice(0, 24), Math.round(ox)]);
        }
      }

      // The display face, proved by measurement. Archivo at wdth 125 is far
      // wider than any fallback, so equal widths mean it never loaded.
      // The probe must NOT carry font-variation-settings. The skin contains
      //   [style*="wdth"] { font-family:'Archivo' !important }
      // so any inline style mentioning the width axis has Archivo forced onto
      // it — which made all three probes measure the same face and report
      // "FONT NOT LOADED" while Archivo was loaded and drawn. Found by asking
      // the browser which important rule matched the probe, not by reading the
      // stylesheet. Archivo at its default width is still plainly wider than
      // serif or monospace, which is all the comparison needs.
      const probe = (fam) => {
        const s = document.createElement('span');
        s.textContent = 'URBAN PLAYGROUND BLACKOUT';
        for (const [k, v] of [['position', 'absolute'], ['visibility', 'hidden'],
                              ['white-space', 'nowrap'], ['font-size', '120px'],
                              ['font-style', 'italic'], ['font-weight', '900'],
                              ['font-family', fam]])
          s.style.setProperty(k, v);
        document.body.appendChild(s);
        const got = getComputedStyle(s).fontFamily;
        const w = s.getBoundingClientRect().width;
        s.remove();
        if (!got.toLowerCase().startsWith(fam.split(',')[0].replace(/'/g, '').toLowerCase()))
          return -1;   // the probe itself was overridden; the measurement is meaningless
        return w;
      };
      // Archivo is compared against ITSELF FALLING BACK, not against some
      // other face: with the webfont gone the stack resolves to the body's
      // sans-serif, which is still wider than serif and narrower than mono, so
      // "archivo vs serif" passed with no Archivo on the page at all (proved
      // by deleting the stylesheet link). "'Archivo',serif" and plain "serif"
      // can only measure the same if Archivo is not there.
      out.font = { aSerif: probe("'Archivo',serif"), serif: probe('serif'),
                   aMono: probe("'Archivo',monospace"), mono: probe('monospace') };
      return out;
    });

    const tag = `${size.label} ${c.name}`;
    const bad = [];
    if (r.missing) bad.push('no .wall rendered');
    if (errs.length) bad.push('page errors: ' + errs.slice(0, 2).join(' | '));
    if (!r.missing) {
      if (r.scroll[0] > 1 || r.scroll[1] > 1) bad.push(`page scrolls by ${r.scroll.join('x')}`);
      const expect = (sess.groupCount || 4);
      if (r.panels.length !== expect) bad.push(`${r.panels.length} panels, expected ${expect}`);
      const spill = r.panels.filter(x => !x[4]);
      if (spill.length) bad.push(`${spill.length} panel(s) outside the wall`);
      if (r.overlap.length) bad.push('OVERLAP: ' + r.overlap.slice(0, 4)
        .map(x => `"${x[0]}" over "${x[1]}" by ${x[2]}px`).join(', ')
        + (r.overlap.length > 4 ? ` (+${r.overlap.length - 4} more)` : ''));
      if (r.clipped.length) bad.push('CLIPPED: ' + r.clipped.map(x => `"${x[0]}" ${x[1]}>${x[2]}`).join(', '));
      if (Object.values(r.font).some(v => v < 0))
        bad.push('font probe overridden by the page — the measurement proves nothing');
      else if (Math.abs(r.font.aSerif - r.font.serif) < 2 || Math.abs(r.font.aMono - r.font.mono) < 2)
        bad.push(`ARCHIVO NOT DRAWN (Archivo/serif ${r.font.aSerif|0} vs serif ${r.font.serif|0}; `
               + `Archivo/mono ${r.font.aMono|0} vs mono ${r.font.mono|0})`);
      // Content, not just geometry.
      const groups = 'ABCDEFGH'.slice(0, expect).split('');
      const absent = groups.filter(g => !r.text.includes(`GROUP ${g}`));
      if (absent.length) bad.push('no table for group ' + absent.join(','));
      if (!/BLACKOUT/.test(r.text)) bad.push('no wordmark');
      if (r.text.length < 200) bad.push(`only ${r.text.length} chars of text on screen`);
    }

    if (bad.length) { fails++; console.log(`FAIL  ${tag}\n        ${bad.join('\n        ')}`); }
    else console.log(`ok    ${tag}  ${r.panels.length} panels  ${r.text.length} chars`);

    if (size.label === '1080x1920' || c.name === 'full-groups')
      await p.screenshot({ path: `${OUT}/${size.label}-${c.name}${SABOTAGE ? '-sabotage-' + SABOTAGE : ''}.png` });
    await p.close();
  }
}

await b.close();
srv.close();
console.log(fails ? `\n${fails} failing case(s)` : '\nwall ok');
process.exit(fails ? 1 : 0);
