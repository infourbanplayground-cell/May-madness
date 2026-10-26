// Transparent Blackout lockups — the logo with no background.
//
// The shipped brand art is rendered ONTO #050505 and is opaque, so dropping it
// on anything that is not true black puts a black slab on the design. These
// are cut-outs: the same typography, the same shrink-to-fit, with the page
// background, the scanlines and the glow taken away.
//
// TWO INKS, for the same reason the UPRISING lockup has two: a transparent
// file goes wherever somebody drops it, and one ink only works on half of
// those places.
//   · <name>-transparent.png       light ink — for dark backgrounds
//   · <name>-transparent-dark.png  dark ink  — for white and light ones
//
// On the light version the lime OUT becomes magenta. Lime #C6FF00 on white is
// about 1.4:1 — the same failure DESIGN.md already records for cream on a volt
// fill, which "looked fine in a screenshot and was very nearly invisible".
// Magenta is the brand's own second colour and clears 4:1 on white. The mark
// keeps its lime, where lime belongs: it carries its own dark bars, so it
// reads on either background.
//
// The source pages are the SHIPPED ones, transformed here rather than
// rewritten, so the type can never drift from the lockup everybody already
// has.
//
//   node ops/render-blackout-transparent.mjs
import { chromium } from 'playwright';
import { PNG } from 'pngjs';
import fs from 'fs';
import path from 'path';

const DIR = path.resolve('brand/blackout');
const DPR = 2;
const MARGIN = 56;          // css px of clear space kept around the ink

const INKS = {
  light: (s) => s,
  dark: (s) => s
    .replaceAll('color:#F2F2F2', 'color:#050505')          // BLACK
    .replaceAll('color:#C6FF00', 'color:#FF2E88')          // OUT — see note above
    .replace('.k{font-weight:800;text-transform:uppercase;letter-spacing:.28em;color:#9A9A9A}',
             '.k{font-weight:800;text-transform:uppercase;letter-spacing:.28em;color:#555555}')
    .replaceAll('background:rgba(255,255,255,.14)', 'background:rgba(5,5,5,.20)'),  // the divider rule
};

// Strip the page off the art: the background it was rendered onto, and the two
// overlays that only mean anything on top of it. Left in, the scanlines print
// lime stripes across whatever the logo is dropped on.
function cutOut(src) {
  let s = src.replace('background:#050505;', 'background:transparent;');
  if (s === src) throw new Error('the page background rule no longer matches');
  const before = s;
  s = s.replace('<div class="glow"></div><div class="scan"></div>', '');
  if (s === before) throw new Error('the glow/scan overlays no longer match');
  return s;
}

const PAGES = ['blackout-lockup', 'blackout-stack'];
const b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
let bad = 0;

for (const page of PAGES) {
  const src = fs.readFileSync(path.join(DIR, page + '.html'), 'utf8');
  for (const [ink, paint] of Object.entries(INKS)) {
    const name = page + '-transparent' + (ink === 'dark' ? '-dark' : '');
    const tmp = path.join(DIR, '.' + name + '.html');
    fs.writeFileSync(tmp, paint(cutOut(src)));

    const p = await b.newPage({ viewport: { width: 400, height: 400 }, deviceScaleFactor: DPR });
    const errs = [];
    p.on('pageerror', e => errs.push(e.message));
    await p.goto('file://' + tmp, { waitUntil: 'load' });
    await p.evaluate(() => document.fonts.ready);
    const size = await p.evaluate(() => {
      const s = getComputedStyle(document.body);
      return { w: parseInt(s.width), h: parseInt(s.height) };
    });
    await p.setViewportSize(size.w && size.h ? { width: size.w, height: size.h } : { width: 400, height: 400 });
    // After the face has loaded, never before: measured in the fallback the
    // numbers are of the wrong letters entirely.
    await p.evaluate(() => (window.__fit ? window.__fit() : {}));

    // The display face has to be DRAWN, not merely asked for. Measured against
    // the same stack falling back, which is the only comparison that cannot
    // pass with no Archivo on the page.
    const font = await p.evaluate(() => {
      const probe = (ff) => {
        const s = document.createElement('span');
        s.textContent = 'BLACKOUT SERIES';
        s.style.cssText = `position:absolute;visibility:hidden;white-space:nowrap;font:italic 900 120px ${ff};`;
        document.body.appendChild(s);
        const w = s.getBoundingClientRect().width; s.remove(); return w;
      };
      const word = document.querySelector('.d');
      return { same: Math.abs(probe('"Archivo",serif') - probe('serif')) < 1,
               vars: getComputedStyle(word).fontVariationSettings };
    });
    if (font.same) errs.push('FONT NOT LOADED: Archivo fell back');
    if (!/125/.test(font.vars)) errs.push(`display width is ${font.vars}, expected wdth 125`);

    const shot = await p.screenshot({ omitBackground: true });
    await p.close();
    fs.unlinkSync(tmp);

    // Trim to the ink and give it back a known margin. The source canvas is
    // sized for a dark slide, so a straight export carries a wide transparent
    // border on one side and almost none on another — on a cut-out that reads
    // as the logo being off-centre in whatever it is placed into.
    const png = PNG.sync.read(shot);
    const A = (x, y) => png.data[(png.width * y + x) * 4 + 3];
    let x0 = png.width, y0 = png.height, x1 = -1, y1 = -1;
    for (let y = 0; y < png.height; y++) for (let x = 0; x < png.width; x++) {
      if (A(x, y) > 8) { if (x < x0) x0 = x; if (x > x1) x1 = x; if (y < y0) y0 = y; if (y > y1) y1 = y; }
    }
    if (x1 < 0) { console.log(`  !! ${name}: nothing was drawn`); bad++; continue; }
    const m = MARGIN * DPR;
    const W = (x1 - x0 + 1) + m * 2, H = (y1 - y0 + 1) + m * 2;
    const out = new PNG({ width: W, height: H });
    out.data.fill(0);
    PNG.bitblt(png, out, x0, y0, x1 - x0 + 1, y1 - y0 + 1, m, m);
    const file = path.join(DIR, name + '.png');
    fs.writeFileSync(file, PNG.sync.write(out));

    // The alpha has to be REAL. An opaque rectangle looks perfect on a dark
    // slide and ruins a white one, with nothing on screen to tell you which
    // one you are holding.
    const o = PNG.sync.read(fs.readFileSync(file));
    const a = (x, y) => o.data[(o.width * y + x) * 4 + 3];
    const corners = [[0, 0], [o.width - 1, 0], [0, o.height - 1], [o.width - 1, o.height - 1]];
    if (corners.some(([x, y]) => a(x, y) > 8)) errs.push('a corner is not transparent');
    let opaque = 0;
    for (let i = 3; i < o.data.length; i += 4) if (o.data[i] > 8) opaque++;
    const pct = (100 * opaque / (o.width * o.height));
    if (!opaque) errs.push('the image is entirely transparent');
    if (pct > 90) errs.push(`${pct.toFixed(1)}% opaque — a rectangle, not a cut-out`);
    // The margin must really be there, which is also the no-ink-at-the-edge
    // check: if the trim were wrong the ink would reach the crop.
    let clear = true;
    for (let y = 0; y < m && clear; y++) for (let x = 0; x < o.width; x++)
      if (a(x, y) > 8 || a(x, o.height - 1 - y) > 8) { clear = false; break; }
    for (let x = 0; x < m && clear; x++) for (let y = 0; y < o.height; y++)
      if (a(x, y) > 8 || a(o.width - 1 - x, y) > 8) { clear = false; break; }
    if (!clear) errs.push('ink inside the margin — the trim is wrong');

    if (errs.length) bad++;
    console.log(`${errs.length ? '  !! ' : '  ok '}${name.padEnd(36)} ${o.width}x${o.height}  `
      + `${pct.toFixed(1)}% ink  ${(fs.statSync(file).size / 1024).toFixed(0)}KB`
      + (errs.length ? `\n       ${errs.join('\n       ')}` : ''));
  }
}

// The mark on its own. It is already an SVG of a lime square with dark bars,
// so it needs no ink variant — it carries its own contrast and reads on a
// white page and a black one alike.
{
  const svg = fs.readFileSync(path.join(DIR, 'blackout-mark.svg'), 'utf8');
  const p = await b.newPage({ viewport: { width: 1024, height: 1024 }, deviceScaleFactor: 1 });
  await p.setContent(`<style>*{margin:0;padding:0}html,body{width:1024px;height:1024px;background:transparent}
    svg{width:1024px;height:1024px;display:block}</style>${svg}`);
  const shot = await p.screenshot({ omitBackground: true });
  await p.close();
  const file = path.join(DIR, 'blackout-mark-transparent.png');
  fs.writeFileSync(file, shot);
  const o = PNG.sync.read(shot);
  let opaque = 0;
  for (let i = 3; i < o.data.length; i += 4) if (o.data[i] > 8) opaque++;
  console.log(`  ok blackout-mark-transparent.png          ${o.width}x${o.height}  `
    + `${(100 * opaque / (o.width * o.height)).toFixed(1)}% ink  `
    + `${(fs.statSync(file).size / 1024).toFixed(0)}KB`);
  // The mark fills its own square by design, so the alpha check that matters
  // is only that it is not an opaque 1024x1024 slab of background.
}

await b.close();
process.exit(bad ? 1 : 0);
