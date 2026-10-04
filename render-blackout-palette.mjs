// Renders the palette board. Reads its size off the page, like the rest of the
// brand art, so the renderer carries no second copy of the dimensions.
import { chromium } from 'playwright';
import fs from 'fs';
import path from 'path';

const OUT = path.resolve('brand/blackout');
const src = path.join(OUT, 'blackout-palette.html');
if (!fs.existsSync(src)) { console.error('run: python3 build-blackout-palette.py'); process.exit(1); }

const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome' });
const pg = await browser.newPage({ viewport: { width: 400, height: 400 }, deviceScaleFactor: 2 });
const errs = [];
pg.on('pageerror', e => errs.push(e.message));
await pg.goto('file://' + src, { waitUntil: 'load' });
await pg.evaluate(() => document.fonts.ready);
const size = await pg.evaluate(() => {
  const s = getComputedStyle(document.body);
  return { w: parseInt(s.width), h: parseInt(s.height) };
});
await pg.setViewportSize({ width: size.w, height: size.h });

const spill = await pg.evaluate(() => {
  const W = document.body.clientWidth, H = document.body.clientHeight, out = [];
  for (const el of document.querySelectorAll('body *')) {
    if (el.classList.contains('wash')) continue;
    const r = el.getBoundingClientRect();
    if (!r.width || !r.height) continue;
    if (r.bottom > H + 0.5 || r.right > W + 0.5) out.push(`${el.className || el.tagName} ${Math.round(r.right)},${Math.round(r.bottom)} of ${W}x${H}`);
  }
  return out.slice(0, 4);
});

const png = path.join(OUT, 'blackout-palette.png');
await pg.screenshot({ path: png });
await pg.close();
await browser.close();

const bad = [];
if (spill.length) bad.push('runs off the board: ' + spill.join(' ; '));
if (errs.length) bad.push(errs.join('; '));
console.log(`blackout-palette.png  ${size.w * 2}x${size.h * 2}  ${(fs.statSync(png).size / 1024).toFixed(0)}KB`
  + (bad.length ? `\n  !! ${bad.join(' | ')}` : '  ok'));
process.exit(bad.length ? 1 : 0);
