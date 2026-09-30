// Renders the July-September attendance table to a shareable PNG.
//
// 2x device scale factor, so the 1200x1560 layout lands at 2400x3120 — sharp on
// a phone, and still small enough to send over WhatsApp without recompression
// mangling the mono digits.
import { chromium } from 'playwright';
import fs from 'fs';
import path from 'path';

const OUT = path.resolve('brand/reports');
const SRC = path.join(OUT, 'attendance-jul-sep.html');
const PNG = path.join(OUT, 'attendance-jul-sep.png');
const W = 1200, H = 1220;

if (!fs.existsSync(SRC)) {
  console.error('no html — run: python3 build-attendance-table.py');
  process.exit(1);
}

const browser = await chromium.launch({
  executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome',
});
const pg = await browser.newPage({
  viewport: { width: W, height: H },
  deviceScaleFactor: 2,
});
const errs = [];
pg.on('pageerror', e => errs.push(e.message));
await pg.goto('file://' + SRC, { waitUntil: 'load' });
await pg.evaluate(() => document.fonts.ready);

const checks = await pg.evaluate(() => {
  const body = document.body;
  return {
    display: document.fonts.check('italic 900 40px Archivo'),
    mono: document.fonts.check('700 14px "JetBrains Mono"'),
    emblem: [...document.images].every(i => i.complete && i.naturalWidth > 0),
    rows: document.querySelectorAll('tbody tr').length,
    // The layout is a fixed canvas with overflow hidden: anything taller than
    // the viewport is silently cropped, which would cut the last player off the
    // bottom of a file that otherwise looks finished.
    overflow: body.scrollHeight - window.innerHeight,
    // The footer is absolutely positioned; if the table grows into it they
    // collide instead of pushing apart.
    clash: (() => {
      const t = document.querySelector('table').getBoundingClientRect();
      const f = document.querySelector('footer').getBoundingClientRect();
      return Math.round(t.bottom - f.top);
    })(),
    widest: Math.max(...[...document.querySelectorAll('.nm')]
      .map(e => e.getBoundingClientRect().width)),
  };
});

await pg.screenshot({ path: PNG, type: 'png' });
await pg.close();
await browser.close();

const b = fs.readFileSync(PNG);
const px = { w: b.readUInt32BE(16), h: b.readUInt32BE(20) };
const kb = (b.length / 1024).toFixed(0);

const bad = [];
if (!checks.display) bad.push('display face missing');
if (!checks.mono) bad.push('mono missing');
if (!checks.emblem) bad.push('emblem failed');
if (checks.rows !== 9) bad.push(`${checks.rows} rows, expected 9`);
if (checks.overflow > 0) bad.push(`${checks.overflow}px cropped off the bottom`);
if (checks.clash > -12) bad.push(`table overlaps footer by ${checks.clash}px`);
if (px.w !== W * 2 || px.h !== H * 2) bad.push(`${px.w}x${px.h}, expected ${W*2}x${H*2}`);
if (errs.length) bad.push(errs.join('; '));

console.log(`attendance-jul-sep.png  ${px.w}x${px.h}  ${kb}KB  ${checks.rows} players`
  + `  widest name ${checks.widest.toFixed(0)}px  footer gap ${-checks.clash}px`
  + (bad.length ? `\n  !! ${bad.join(' | ')}` : '  ok'));
