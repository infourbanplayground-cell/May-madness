// Renders the medal stickers at 300 DPI.
//
// The artboard is sized in millimetres, so the device scale factor is whatever
// turns its CSS pixel size into 300 DPI: 1mm is 96/25.4 CSS px, and 300 DPI is
// 300/25.4 device px per mm, so the factor is 300/96 = 3.125 at any size.
import { chromium } from 'playwright';
import fs from 'fs';
import path from 'path';

const OUT = path.resolve('brand/medal-stickers');
const DPR = 300 / 96;
const PX_PER_MM = 96 / 25.4;

const browser = await chromium.launch({
  executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome',
});

const files = fs.readdirSync(OUT).filter(f => f.endsWith('.html')).sort();
for (const f of files) {
  const m = f.match(/ss-medal-(\d+)mm-(\d)-(bleed|disc)\.html/);
  if (!m) continue;
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
  await pg.evaluate(() => document.fonts.ready);

  const checks = await pg.evaluate(() => ({
    // The numeral is the whole design at 25mm — if the display face has not
    // loaded, the sticker is wrong in a way that is easy to miss on a thumbnail.
    display: document.fonts.check('italic 900 40px Archivo'),
    mono: document.fonts.check('700 14px "JetBrains Mono"'),
    images: [...document.images].every(i => i.complete && i.naturalWidth > 0),
    svg: !!document.querySelector('svg'),
  }));

  const png = path.join(OUT, f.replace('.html', '.png'));
  await pg.screenshot({
    path: png,
    type: 'png',
    omitBackground: kind === 'disc',    // transparency outside the disc
  });
  await pg.close();

  const { width, height } = await sizeOf(png);
  const dpi = Math.round(width / (artMm / 25.4));
  const bad = [];
  if (!checks.display) bad.push('display face missing');
  if (!checks.mono) bad.push('mono missing');
  if (!checks.images) bad.push('emblem failed');
  if (!checks.svg) bad.push('no svg');
  if (Math.abs(dpi - 300) > 4) bad.push(`${dpi} DPI, expected 300`);
  if (errs.length) bad.push(errs.join('; '));
  console.log(`${path.basename(png)}  ${width}x${height}  ${dpi} DPI`
    + (bad.length ? `\n  !! ${bad.join(' | ')}` : '  ok'));
}
await browser.close();

async function sizeOf(p) {
  const b = fs.readFileSync(p);
  return { width: b.readUInt32BE(16), height: b.readUInt32BE(20) };
}
