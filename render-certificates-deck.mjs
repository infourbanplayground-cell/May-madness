// Renders the handoff certificate artboards to print-ready PDF + 300 DPI PNG.
//
// The design is 1920x1080 (16:9), which is not A4's 1.414 ratio. Rather than
// crop or letterbox it, the PDF page is set to 297 x 167.06mm — full A4
// landscape width at the design's own aspect — so it prints on A4 with an even
// margin top and bottom and every proportion is exactly as designed.
//
// page.pdf does NOT scale content to fit the page: it lays the document out at
// its CSS size and paginates. A 1920px-wide artboard is 1440pt = 508mm, so on a
// 297mm page it silently spills off the right edge and pageRanges:'1' keeps only
// the cropped first page. The `scale` below maps 1920 CSS px onto the page width
// so the whole artboard lands on one page.
import { chromium } from 'playwright';
import fs from 'fs';
import path from 'path';

const OUT = path.resolve('brand/certificates-deck');
const W_MM = 297, H_MM = +(297 * 1080 / 1920).toFixed(2);   // 167.06
const CSS_PX_PER_MM = 96 / 25.4;
const PDF_SCALE = (W_MM * CSS_PX_PER_MM) / 1920;            // ~0.5846
const names = process.argv.slice(2).length ? process.argv.slice(2) : ['1st','2nd','3rd','4th','5th'];

const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
for (const n of names) {
  const src = path.join(OUT, `aa-certificate-${n}.html`);
  if (!fs.existsSync(src)) { console.log(`skip ${n}: no html`); continue; }

  const pg = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
  const errs = [];
  pg.on('pageerror', e => errs.push(e.message));
  await pg.goto('file://' + src, { waitUntil: 'load' });
  await pg.evaluate(() => document.fonts.ready);

  const checks = await pg.evaluate(() => {
    const de = document.documentElement;
    const imgs = [...document.images].map(i => ({ ok: i.complete && i.naturalWidth > 0, src: i.src.slice(0, 30) }));
    return {
      // Check the weights the artboards actually use. Checking Archivo 400
      // reports false purely because font-display:block leaves unused faces
      // lazy — it says nothing about whether the page rendered correctly.
      fonts: { anton: document.fonts.check('40px Anton'),
               archivo500: document.fonts.check('500 16px Archivo'),
               archivo800: document.fonts.check('800 18px Archivo'),
               mono700: document.fonts.check('700 14px "JetBrains Mono"'),
               loaded: [...document.fonts].filter(f => f.status === 'loaded').length },
      imagesLoaded: imgs.every(i => i.ok), imageCount: imgs.length,
      overflow: de.scrollWidth > 1920 || de.scrollHeight > 1080,
      headline: (document.querySelector('section') || {}).innerText?.split('\n').filter(Boolean).slice(0, 8),
    };
  });

  await pg.pdf({ path: path.join(OUT, `aa-certificate-${n}.pdf`),
                 width: `${W_MM}mm`, height: `${H_MM}mm`, printBackground: true,
                 scale: PDF_SCALE, pageRanges: '1' });
  await pg.close();

  // 300 DPI raster: 1920 CSS px across 297mm => scale so 297mm lands at 300dpi.
  const pg2 = await browser.newPage({ viewport: { width: 1920, height: 1080 },
                                      deviceScaleFactor: (297 / 25.4 * 300) / 1920 });
  await pg2.goto('file://' + src, { waitUntil: 'load' });
  await pg2.evaluate(() => document.fonts.ready);
  await pg2.screenshot({ path: path.join(OUT, `aa-certificate-${n}.png`) });
  await pg2.close();

  const pdf = fs.statSync(path.join(OUT, `aa-certificate-${n}.pdf`));
  console.log(`${n}: pdf ${(pdf.size/1024).toFixed(0)}KB  fonts ${JSON.stringify(checks.fonts)}  ` +
              `imgs ${checks.imagesLoaded ? checks.imageCount + ' ok' : 'MISSING'}  ` +
              `overflow ${checks.overflow}` + (errs.length ? `  ERRORS ${errs.slice(0,2)}` : ''));
}
await browser.close();
