// Renders the certificate HTML to a print-ready PDF (vector type, A4 landscape)
// and a 300 DPI PNG. Waits on document.fonts.ready before capturing — without
// it Anton can still be swapping and the placement line renders in a fallback.
import { chromium } from 'playwright';
import fs from 'fs';
import path from 'path';

const OUT = path.resolve('brand/certificates');
const MM_PER_IN = 25.4, DPI = 300;
const W_MM = 297, H_MM = 210;
const pxW = Math.round(W_MM / MM_PER_IN * DPI);   // 3508
const pxH = Math.round(H_MM / MM_PER_IN * DPI);   // 2480

const places = process.argv.slice(2).length ? process.argv.slice(2) : ['1', '2', '3', '4', '5'];
const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });

for (const p of places) {
  const src = path.join(OUT, `aa-certificate-${p}.html`);
  if (!fs.existsSync(src)) { console.log(`skip ${p}: no html`); continue; }

  // PDF: CSS px at 96dpi maps to the A4 box; type stays vector.
  const pg = await browser.newPage();
  const errs = [];
  pg.on('pageerror', e => errs.push(e.message));
  await pg.goto('file://' + src, { waitUntil: 'load' });
  await pg.evaluate(() => document.fonts.ready);
  await pg.pdf({ path: path.join(OUT, `aa-certificate-${p}.pdf`),
                 width: `${W_MM}mm`, height: `${H_MM}mm`, printBackground: true, pageRanges: '1' });
  await pg.close();

  // PNG at 300 DPI: scale the viewport rather than upscaling afterwards.
  const scale = pxW / (W_MM / MM_PER_IN * 96);
  const pg2 = await browser.newPage({ viewport: { width: Math.round(W_MM / MM_PER_IN * 96),
                                                  height: Math.round(H_MM / MM_PER_IN * 96) },
                                      deviceScaleFactor: scale });
  await pg2.goto('file://' + src, { waitUntil: 'load' });
  await pg2.evaluate(() => document.fonts.ready);

  const fontsOk = await pg2.evaluate(() => ({
    anton: document.fonts.check("40px Anton"),
    archivo: document.fonts.check("16px Archivo"),
    mono: document.fonts.check("12px Mono"),
  }));
  const overflow = await pg2.evaluate(() => ({
    h: document.documentElement.scrollWidth > document.documentElement.clientWidth,
    v: document.documentElement.scrollHeight > document.documentElement.clientHeight,
  }));

  await pg2.screenshot({ path: path.join(OUT, `aa-certificate-${p}.png`) });
  await pg2.close();

  const png = fs.statSync(path.join(OUT, `aa-certificate-${p}.png`));
  const pdf = fs.statSync(path.join(OUT, `aa-certificate-${p}.pdf`));
  console.log(`place ${p}: png ${(png.size/1024/1024).toFixed(1)}MB  pdf ${(pdf.size/1024).toFixed(0)}KB  ` +
              `fonts ${JSON.stringify(fontsOk)}  overflow ${JSON.stringify(overflow)}` +
              (errs.length ? `  ERRORS ${errs.slice(0,2)}` : ''));
}
await browser.close();
