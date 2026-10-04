// Renders the printable sign-up sheets to A4 PDF plus a PNG preview.
//
// A4 at actual size, one page, printBackground on — a sheet that prints the
// lines but not the ground is a sheet nobody can read in a dark clubhouse.
import { chromium } from 'playwright';
import fs from 'fs';
import path from 'path';

const OUT = path.resolve('brand/blackout/posts');
const MM = 96 / 25.4;

const files = fs.readdirSync(OUT).filter(f => /^signup-sheet-\d+(-light)?\.html$/.test(f)).sort();
if (!files.length) { console.error('no sheets — run: python3 build-signup-sheet.py 1'); process.exit(1); }

const browser = await chromium.launch({
  executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome',
});

let failed = 0;
for (const f of files) {
  const pg = await browser.newPage({
    viewport: { width: Math.round(210 * MM), height: Math.round(297 * MM) },
  });
  const errs = [];
  pg.on('pageerror', e => errs.push(e.message));
  await pg.goto('file://' + path.join(OUT, f), { waitUntil: 'load' });
  await pg.evaluate(() => document.fonts.ready);

  const checks = await pg.evaluate(() => {
    const H = document.body.clientHeight, W = document.body.clientWidth;
    const over = [];
    for (const el of document.querySelectorAll('body *')) {
      const r = el.getBoundingClientRect();
      if (!r.width || !r.height) continue;
      // A sheet that runs past the bottom of the page silently loses its last
      // rows — which on a sign-up sheet means losing the waitlist.
      if (r.bottom > H + 0.5 || r.right > W + 0.5) {
        const axis = r.bottom > H + 0.5 ? `bottom ${Math.round(r.bottom)}/${H}` : '';
        const axis2 = r.right > W + 0.5 ? `right ${Math.round(r.right)}/${W}` : '';
        over.push(`${el.className || el.tagName} ${[axis, axis2].filter(Boolean).join(' ')}`);
      }
    }
    return {
      over: over.slice(0, 4),
      rows: document.querySelectorAll('.row').length,
      display: document.fonts.check('italic 900 40px Archivo'),
      mono: document.fonts.check('700 14px "JetBrains Mono"'),
      imgs: [...document.images].every(i => i.complete && i.naturalWidth > 0),
    };
  });

  const pdf = path.join(OUT, f.replace('.html', '.pdf'));
  await pg.pdf({ path: pdf, format: 'A4', printBackground: true, pageRanges: '1' });
  await pg.screenshot({ path: path.join(OUT, f.replace('.html', '.png')) });
  await pg.close();

  const bad = [];
  if (!checks.display) bad.push('display face missing');
  if (!checks.mono) bad.push('mono missing');
  if (!checks.imgs) bad.push('the mark failed to decode');
  if (checks.over.length) bad.push('runs off the page: ' + checks.over.join(' ; '));
  if (errs.length) bad.push(errs.join('; '));
  if (bad.length) failed++;
  console.log(`${path.basename(pdf)}  A4  ${(fs.statSync(pdf).size / 1024).toFixed(0)}KB  `
    + `${checks.rows} rows` + (bad.length ? `\n  !! ${bad.join(' | ')}` : '  ok'));
}
await browser.close();
process.exit(failed ? 1 : 0);
