// Renders the Vol.7 placement certificates to 300 DPI PNG, then pack-certificate
// PDFs turns each into a print-ready A4 landscape page.
//
// Why a raster and not Chromium's vector PDF export: the design leans on large
// soft glows (the placement numeral, the ripple, the accent rules). Chromium's
// PDF writer tiles big blurred shadows and the seams between tiles print as
// hard-edged rectangles, while a screenshot of the identical page is smooth.
// That is the same reason the Vol.6 deck rasterises — see pack-certificate-pdfs.py.
//
// A4 landscape is 297 x 210mm. At 96 CSS px/inch that is 1122.52 x 793.70 px, so
// deviceScaleFactor 3.125 gives 3508 x 2480 — exactly 300 DPI across 297mm.
import { chromium } from 'playwright';
import fs from 'fs';
import path from 'path';

const OUT = path.resolve('brand/certificates-surge');
const CSS_W = 297 / 25.4 * 96;     // 1122.52
const CSS_H = 210 / 25.4 * 96;     // 793.70
const DPR = 3508 / CSS_W;          // 3.125 -> 300 DPI
const places = process.argv.slice(2).length ? process.argv.slice(2) : ['1', '2', '3', '4', '5'];

const browser = await chromium.launch({
  executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome',
});

for (const n of places) {
  const src = path.join(OUT, `ss-certificate-${n}.html`);
  if (!fs.existsSync(src)) { console.log(`skip ${n}: no html`); continue; }

  const pg = await browser.newPage({
    viewport: { width: Math.round(CSS_W), height: Math.round(CSS_H) },
    deviceScaleFactor: DPR,
  });
  const errs = [];
  pg.on('pageerror', e => errs.push(e.message));
  await pg.goto('file://' + src, { waitUntil: 'load' });
  await pg.evaluate(() => document.fonts.ready);

  // Verify the page actually rendered as designed before we ship a PNG of it.
  // Checking Archivo 400 would report false purely because font-display:block
  // leaves unused faces lazy — check the weights the artboard really uses.
  const checks = await pg.evaluate(() => {
    const de = document.documentElement;
    const imgs = [...document.images].map(i => i.complete && i.naturalWidth > 0);
    return {
      fonts: {
        archivo900i: document.fonts.check('italic 900 40px Archivo'),
        archivo900:  document.fonts.check('900 16px Archivo'),
        mono700:     document.fonts.check('700 14px "JetBrains Mono"'),
        loaded: [...document.fonts].filter(f => f.status === 'loaded').length,
      },
      imagesLoaded: imgs.length > 0 && imgs.every(Boolean),
      imageCount: imgs.length,
      overflow: de.scrollWidth > de.clientWidth + 1 || de.scrollHeight > de.clientHeight + 1,
      place: document.querySelector('.place')?.textContent,
      label: document.querySelector('.label')?.textContent,
      name:  document.querySelector('.nameplate .typed')?.textContent || '(blank line)',
    };
  });

  const png = path.join(OUT, `ss-certificate-${n}.png`);
  await pg.screenshot({ path: png, type: 'png' });
  await pg.close();

  const kb = (fs.statSync(png).size / 1024).toFixed(0);
  const bad = [];
  if (!checks.fonts.archivo900i) bad.push('display face not loaded');
  if (!checks.fonts.mono700) bad.push('mono not loaded');
  if (!checks.imagesLoaded) bad.push('an image failed');
  if (checks.overflow) bad.push('content overflows the page');
  if (errs.length) bad.push('page errors: ' + errs.join('; '));
  console.log(`${path.basename(png)}  ${kb}KB  ${checks.place} / ${checks.label} / ${checks.name}`
    + (bad.length ? `\n  !! ${bad.join(' | ')}` : '  ok'));
}
await browser.close();
