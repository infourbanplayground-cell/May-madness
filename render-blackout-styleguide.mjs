// Renders the design-language sheet to PNG.
//
// Same overflow check as the rest of the brand art: a sheet whose prompt block
// runs off the bottom of the canvas is a sheet whose prompt cannot be read,
// and that is the one thing on it that has to survive.
import { chromium } from 'playwright';
import fs from 'fs';
import path from 'path';

const BRAND = path.resolve('brand/blackout');
const SRC = path.join(BRAND, 'blackout-styleguide.html');
if (!fs.existsSync(SRC)) {
  console.error('no sheet — run: python3 build-blackout-styleguide.py');
  process.exit(1);
}

const browser = await chromium.launch({
  executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome',
});
const pg = await browser.newPage({ viewport: { width: 1500, height: 1740 } });
const errs = [];
pg.on('pageerror', e => errs.push(e.message));
await pg.goto('file://' + SRC, { waitUntil: 'load' });
await pg.evaluate(() => document.fonts.ready);

const checks = await pg.evaluate(() => {
  const H = document.body.clientHeight, W = document.body.clientWidth;
  const over = [];
  for (const el of document.querySelectorAll('body *')) {
    if (el.ownerSVGElement) continue;
    const r = el.getBoundingClientRect();
    if (!r.width || !r.height) continue;
    if (r.bottom > H + 0.5 || r.right > W + 0.5) {
      over.push(`${el.className || el.tagName} `
        + `${r.bottom > H + 0.5 ? `bottom ${Math.round(r.bottom)}/${H}` : ''}`
        + `${r.right > W + 0.5 ? ` right ${Math.round(r.right)}/${W}` : ''}`);
    }
  }
  const p = document.querySelector('.prompt p');
  return {
    over: over.slice(0, 5),
    bottom: Math.round(document.querySelector('.foot').getBoundingClientRect().bottom),
    promptChars: p ? p.textContent.length : 0,
    display: document.fonts.check('italic 900 40px Archivo'),
    mono: document.fonts.check('700 14px "JetBrains Mono"'),
    imgs: [...document.images].every(i => i.complete && i.naturalWidth > 0),
    swatches: document.querySelectorAll('.sw').length,
    steps: document.querySelectorAll('.st').length,
  };
});

const out = path.join(BRAND, 'blackout-styleguide.png');
await pg.screenshot({ path: out });
await browser.close();

const bad = [];
if (!checks.display) bad.push('display face missing');
if (!checks.mono) bad.push('mono missing');
if (!checks.imgs) bad.push('an image failed to decode');
if (!checks.promptChars) bad.push('the prompt block is empty');
if (checks.over.length) bad.push('runs off the canvas: ' + checks.over.join(' ; '));
if (errs.length) bad.push(errs.join('; '));

console.log(`blackout-styleguide.png  1500x1740  ${(fs.statSync(out).size / 1024).toFixed(0)}KB`);
console.log(`  ${checks.swatches} swatches, ${checks.steps} grade steps, `
  + `${checks.promptChars}-char prompt, content ends at ${checks.bottom}px`);
console.log(bad.length ? '  !! ' + bad.join(' | ') : '  ok');
process.exit(bad.length ? 1 : 0);
