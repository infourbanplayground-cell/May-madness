// Renders the Blackout Series brand art.
//
// Each page declares its own pixel size, so the renderer reads it off the page
// rather than carrying a second copy of the dimensions that can drift from the
// builder's.
import { chromium } from 'playwright';
import fs from 'fs';
import path from 'path';

const OUT = path.resolve('brand/blackout');
const DPR = 2;

const browser = await chromium.launch({
  executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome',
});

const files = fs.readdirSync(OUT).filter(f => f.startsWith('blackout-') && f.endsWith('.html')).sort();
for (const f of files) {
  const src = path.join(OUT, f);
  const pg = await browser.newPage({ viewport: { width: 400, height: 400 }, deviceScaleFactor: DPR });
  const errs = [];
  pg.on('pageerror', e => errs.push(e.message));
  await pg.goto('file://' + src, { waitUntil: 'load' });
  await pg.evaluate(() => document.fonts.ready);

  const size = await pg.evaluate(() => {
    const s = getComputedStyle(document.body);
    return { w: parseInt(s.width), h: parseInt(s.height) };
  });
  await pg.setViewportSize({ width: size.w, height: size.h });

  const checks = await pg.evaluate(() => ({
    display: document.fonts.check('italic 900 40px Archivo'),
    // The mark is pure geometry and sets no type, so requiring the display face
    // there flags a correct file as broken.
    hasDisplay: !!document.querySelector('.d'),
    imgs: [...document.images].every(i => i.complete && i.naturalWidth > 0),
    // The width axis is the whole look. A static instance accepts the property
    // and renders ~20% narrow without erroring, so measure instead of trusting.
    wide: (() => {
      const el = document.querySelector('.d');
      if (!el) return null;
      const w0 = el.getBoundingClientRect().width;
      const keep = el.style.fontVariationSettings;
      el.style.fontVariationSettings = "'wdth' 62,'wght' 900";
      const w1 = el.getBoundingClientRect().width;
      el.style.fontVariationSettings = keep;
      return w0 / w1;
    })(),
  }));

  const png = path.join(OUT, f.replace('.html', '.png'));
  await pg.screenshot({ path: png, type: 'png', omitBackground: f.includes('-mark') });
  await pg.close();

  const b = fs.readFileSync(png);
  const px = { w: b.readUInt32BE(16), h: b.readUInt32BE(20) };
  const bad = [];
  if (checks.hasDisplay && !checks.display) bad.push('display face missing');
  if (!checks.imgs) bad.push('an image failed to decode');
  if (checks.wide !== null && checks.wide < 1.15) {
    bad.push(`width axis inert (${checks.wide.toFixed(2)}x vs condensed) — static font instance?`);
  }
  if (px.w !== size.w * DPR || px.h !== size.h * DPR) bad.push(`${px.w}x${px.h}, expected ${size.w * DPR}x${size.h * DPR}`);
  if (errs.length) bad.push(errs.join('; '));
  console.log(`${path.basename(png)}  ${px.w}x${px.h}  ${(b.length / 1024).toFixed(0)}KB`
    + (bad.length ? `\n  !! ${bad.join(' | ')}` : '  ok'));
}
await browser.close();
