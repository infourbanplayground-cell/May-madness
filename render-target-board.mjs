// Renders the DEAD EYE board to 1:1 vector PDF plus a raster preview.
//
// The PDF is the deliverable a sign shop or CNC wants: 1200 x 2000mm at actual
// size, vector, so it scales to whatever substrate without resampling. The
// artwork is deliberately built from flat shapes and crisp strokes — no large
// soft glows — because Chromium's PDF writer tiles blurred shadows and the
// seams print as hard-edged rectangles. At 2m viewed across a court a glow
// would be wasted anyway.
//
// The preview PNG is capped at a sane pixel size: 1:1 at 300 DPI would be
// 14173 x 23622, which is 335 megapixels and useless for sending to anyone.
import { chromium } from 'playwright';
import fs from 'fs';
import path from 'path';

const OUT = path.resolve('brand/target-board');
const MM = 96 / 25.4;
const W_MM = 1200, H_MM = 2000;
const PREVIEW_W = 1400;            // px on the long edge of the preview

const browser = await chromium.launch({
  executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome',
});

for (const name of ['deadeye-board', 'deadeye-cutfile']) {
  const src = path.join(OUT, `${name}.html`);
  if (!fs.existsSync(src)) { console.log(`skip ${name}: no html`); continue; }

  const pg = await browser.newPage({
    viewport: { width: Math.round(W_MM * MM), height: Math.round(H_MM * MM) },
  });
  const errs = [];
  pg.on('pageerror', e => errs.push(e.message));
  await pg.goto('file://' + src, { waitUntil: 'load' });
  await pg.evaluate(() => document.fonts.ready);

  const checks = await pg.evaluate(() => ({
    display: document.fonts.check('italic 900 40px Archivo'),
    mono: document.fonts.check('700 14px "JetBrains Mono"'),
    images: [...document.images].every(i => i.complete && i.naturalWidth > 0),
    holes: document.querySelectorAll('circle').length,
  }));

  await pg.pdf({
    path: path.join(OUT, `${name}.pdf`),
    width: `${W_MM}mm`, height: `${H_MM}mm`,
    printBackground: true, pageRanges: '1',
  });

  // preview, scaled down so the file is shareable
  await pg.setViewportSize({
    width: Math.round(PREVIEW_W),
    height: Math.round(PREVIEW_W * H_MM / W_MM),
  });
  await pg.addStyleTag({ content:
    `html,body{width:${PREVIEW_W}px!important;height:${Math.round(PREVIEW_W*H_MM/W_MM)}px!important}
     svg{width:${PREVIEW_W}px!important;height:${Math.round(PREVIEW_W*H_MM/W_MM)}px!important}` });
  await pg.screenshot({ path: path.join(OUT, `${name}.png`), type: 'png' });
  await pg.close();

  const pdfMb = (fs.statSync(path.join(OUT, `${name}.pdf`)).size / 1024 / 1024).toFixed(1);
  const bad = [];
  // The cut file is geometry and mono dimensions only — it has no display
  // type, so requiring Archivo there flags a correct file as broken.
  if (name !== 'deadeye-cutfile' && !checks.display) bad.push('display face missing');
  if (!checks.mono) bad.push('mono missing');
  if (name === 'deadeye-board' && !checks.images) bad.push('lockup failed');
  if (errs.length) bad.push(errs.join('; '));
  console.log(`${name}.pdf  ${W_MM}x${H_MM}mm  ${pdfMb}MB  ${checks.holes} circles`
    + (bad.length ? `\n  !! ${bad.join(' | ')}` : '  ok'));
}
await browser.close();
