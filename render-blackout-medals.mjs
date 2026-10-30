// Renders the Vol.8 medal cut-outs at 300 DPI.
//
// The artboard is sized in millimetres, so the device scale factor is whatever
// turns its CSS pixel size into 300 DPI: 1mm is 96/25.4 CSS px and 300 DPI is
// 300/25.4 device px per mm, so the factor is 300/96 = 3.125 at any size.
//
// The `-disc` files are CUT-OUTS, and a cut-out is checked the way the UPRISING
// lockup and the Blackout transparent logos are checked: the alpha has to be
// REAL. An opaque dark square looks perfect on a dark slide and ruins a white
// one, with nothing on screen to tell you which you have.
import { chromium } from 'playwright';
import { PNG } from 'pngjs';
import fs from 'fs';
import path from 'path';

const OUT = path.resolve('brand/medals-blackout');
const DPR = 300 / 96;
const PX_PER_MM = 96 / 25.4;
const SABOTAGE = process.env.SABOTAGE || '';
const ONLY = process.env.ONLY || '';

const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
let failed = 0;

const files = fs.readdirSync(OUT).filter(f => f.endsWith('.html')).sort();
for (const f of files) {
  const m = f.match(/bo-medal-(\d+)mm-(\d)-(bleed|disc)\.html/);
  if (!m) continue;
  if (ONLY && !f.includes(ONLY)) continue;
  const [, size, place, kind] = m;
  const artMm = Number(size) + (kind === 'bleed' ? 6 : 0);
  const cssPx = Math.round(artMm * PX_PER_MM);

  const pg = await browser.newPage({
    viewport: { width: cssPx, height: cssPx },
    deviceScaleFactor: DPR,
  });
  const errs = [];
  pg.on('pageerror', e => errs.push(e.message));
  await pg.goto('file://' + path.join(OUT, f), { waitUntil: 'load' });
  if (SABOTAGE === 'nofont') {
    await pg.evaluate(() => {
      for (const s of document.querySelectorAll('style'))
        s.textContent = s.textContent.replace(/@font-face\s*\{[^}]*\}/g, '');
    });
  } else if (SABOTAGE === 'opaque') {
    // What a cut-out looks like when somebody forgets omitBackground.
    await pg.evaluate(() => { document.body.style.background = '#050505'; });
  }
  await pg.evaluate(() => document.fonts.ready);
  await pg.waitForFunction(() => document.querySelector('svg')?.dataset.centred === '1',
                           null, { timeout: 5000 });

  const checks = await pg.evaluate(() => {
    const probe = (stack, it) => {
      const e = document.createElement('span');
      e.textContent = 'HAMBURGEFONSTIV 1890 WWWiii';
      e.style.cssText = 'position:absolute;left:-9999px;font-size:100px;'
        + `font-family:${stack};` + (it ? 'font-style:italic;font-weight:900;' : '');
      document.body.appendChild(e);
      const w = e.getBoundingClientRect().width;
      e.remove();
      return w;
    };
    // The numeral IS the design here, so a substituted face is not a subtle
    // flaw. Archivo is measured against the same stack falling back; mono is
    // checked for being embedded, because JetBrains Mono is installed
    // system-wide in this container and a width probe cannot tell the two
    // apart — see render-blackout-certificates.mjs.
    const loaded = [...document.fonts].filter(x => x.status === 'loaded')
      .map(x => x.family.replace(/['"]/g, ''));
    return {
      'archivo drawn': probe("'Archivo',serif", true) !== probe('serif', true),
      'archivo embedded': loaded.includes('Archivo'),
      'mono embedded': loaded.includes('JetBrains Mono'),
      images: [...document.images].every(i => i.complete && i.naturalWidth > 0),
      centred: document.querySelector('svg')?.dataset.centred === '1',
    };
  });

  const png = path.join(OUT, f.replace('.html', SABOTAGE ? '-sabotage.png' : '.png'));
  const shot = await pg.screenshot({
    type: 'png',
    omitBackground: kind === 'disc',    // transparency outside the disc
  });
  fs.writeFileSync(png, shot);
  await pg.close();

  const img = PNG.sync.read(shot);
  const A = (x, y) => img.data[(img.width * y + x) * 4 + 3];
  const dpi = Math.round(img.width / (artMm / 25.4));

  const bad = [];
  for (const [k, ok] of Object.entries(checks)) {
    if (ok !== false || k === 'images') continue;
    // Only the 50mm cut sets arc text; at 25mm the arc is deliberately dropped,
    // so the mono face never loads there and requiring it flags every small
    // cut-out as broken.
    if (k === 'mono embedded' && artMm < 40) continue;
    bad.push(k === 'centred' ? 'numeral not centred' : `FONT: ${k}`);
  }
  if (!checks.images) bad.push('the mark failed to load');
  if (Math.abs(dpi - 300) > 4) bad.push(`${dpi} DPI, expected 300`);
  if (errs.length) bad.push(errs.join('; '));

  let alpha = '';
  if (kind === 'disc') {
    // The four corners sit outside the circle and must be clear; the file as a
    // whole must not be wholly transparent (an empty render) and must not be
    // near-opaque (a square that only looks like a cut-out on a dark page).
    const corners = [[0, 0], [img.width - 1, 0], [0, img.height - 1],
                     [img.width - 1, img.height - 1]].map(([x, y]) => A(x, y));
    let opaque = 0, any = 0;
    for (let i = 3; i < img.data.length; i += 4) {
      if (img.data[i] > 250) opaque++;
      if (img.data[i] > 8) any++;
    }
    const total = img.width * img.height;
    if (corners.some(a => a > 8)) bad.push(`corner alpha ${corners.join('/')} — not cut out`);
    if (any === 0) bad.push('wholly transparent — nothing rendered');
    if (opaque / total > 0.90) bad.push(`${(opaque / total * 100).toFixed(0)}% opaque — a square, not a disc`);
    // A disc inscribed in its square covers pi/4 = 78.5% of it. Much less and
    // the artwork is not filling the die; much more and it is past the cut.
    if (any / total < 0.70 || any / total > 0.85) {
      bad.push(`ink covers ${(any / total * 100).toFixed(1)}% of the square, expected ~78.5%`);
    }
    alpha = `  ink ${(any / total * 100).toFixed(1)}%`;
  } else {
    // The bleed artboard is the printer's, and must be solid to its edge.
    const edge = [A(0, 0), A(img.width - 1, img.height - 1), A(Math.floor(img.width / 2), 0)];
    if (edge.some(a => a < 250)) bad.push(`bleed is not solid to the edge (${edge.join('/')})`);
  }

  if (bad.length) failed++;
  console.log(`${path.basename(png)}  ${img.width}x${img.height}  ${dpi} DPI`
    + `  ${(shot.length / 1024).toFixed(0)}KB${alpha}`
    + (bad.length ? `\n  !! ${bad.join('\n  !! ')}` : '  ok'));
}
await browser.close();
if (failed) { console.error(`\n${failed} cut-out(s) failed their checks`); process.exit(1); }
