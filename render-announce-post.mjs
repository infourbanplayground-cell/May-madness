// Renders the Vol.8 announcement post cards to PNG.
//
// Each page declares its own pixel size, so the renderer reads it off the page
// rather than carrying a second copy of the dimensions that can drift from the
// builder's.
//
// The checks are the ones the brand art and the film learned the hard way: the
// display face must actually be the variable instance, nothing may run off the
// canvas, and nothing may be clipped by its own container. A lockup shipped with
// the B and the T of BLACKOUT sliced off and every assertion passed, because
// they were all about the font and none about where the ink landed.
import { chromium } from 'playwright';
import fs from 'fs';
import path from 'path';

const OUT = path.resolve('brand/blackout/posts');
const DPR = 2;

const browser = await chromium.launch({
  executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome',
});

const files = fs.readdirSync(OUT).filter(f => f.startsWith('post-') && f.endsWith('.html')).sort();
if (!files.length) { console.error('no pages — run: python3 build-announce-post.py'); process.exit(1); }

let failed = 0;
for (const f of files) {
  const pg = await browser.newPage({ viewport: { width: 400, height: 400 }, deviceScaleFactor: DPR });
  const errs = [];
  pg.on('pageerror', e => errs.push(e.message));
  await pg.goto('file://' + path.join(OUT, f), { waitUntil: 'load' });
  await pg.evaluate(() => document.fonts.ready);

  const size = await pg.evaluate(() => {
    const s = getComputedStyle(document.body);
    return { w: parseInt(s.width), h: parseInt(s.height) };
  });
  await pg.setViewportSize({ width: size.w, height: size.h });

  // Shrink-to-fit runs here, not on parse: before the display face has loaded
  // every measurement is of the fallback, which is narrower than Archivo at
  // 'wdth' 125 and would leave the real type overflowing anyway.
  const fitted = await pg.evaluate(() => (window.__fit ? window.__fit() : {}));

  const checks = await pg.evaluate(() => {
    const W = document.body.clientWidth, H = document.body.clientHeight;
    const spill = [], clipped = [];
    for (const el of document.querySelectorAll('body *')) {
      if (el.classList.contains('wash') || el.classList.contains('scan')) continue;
      const r = el.getBoundingClientRect();
      if (r.width && r.height && (r.left < -0.5 || r.top < -0.5 || r.right > W + 0.5 || r.bottom > H + 0.5)) {
        spill.push(`${el.id || el.className || el.tagName} [${Math.round(r.left)},${Math.round(r.top)} ${Math.round(r.right)},${Math.round(r.bottom)}]`);
      }
      if (el.clientWidth > 0 && el.scrollWidth > el.clientWidth + 1) {
        clipped.push(`${el.id || el.className} "${el.textContent.trim().slice(0, 22)}" needs ${el.scrollWidth}px, has ${el.clientWidth}px`);
      }
    }
    return {
      spill, clipped,
      display: document.fonts.check('italic 900 40px Archivo'),
      mono: document.fonts.check('700 14px "JetBrains Mono"'),
      imgs: [...document.images].every(i => i.complete && i.naturalWidth > 0),
      // The width axis is the whole look. A static instance accepts the property
      // and renders ~20% narrow without erroring, so measure instead of trusting.
      //
      // Measured with a Range over the text, not the element box: most of these
      // headlines are full-bleed and centred, so their boxes are the card's full
      // width at any axis setting and would report the axis dead on a page where
      // it works perfectly.
      wide: (() => {
        const el = [...document.querySelectorAll('.d')]
          .find(n => [...n.childNodes].some(c => c.nodeType === 3 && c.textContent.trim()));
        if (!el) return null;
        const ink = () => {
          const r = document.createRange();
          r.selectNodeContents(el);
          return r.getBoundingClientRect().width;
        };
        const w0 = ink();
        const keep = el.style.fontVariationSettings;
        el.style.fontVariationSettings = "'wdth' 62,'wght' 900";
        const w1 = ink();
        el.style.fontVariationSettings = keep;
        return w1 > 0 ? w0 / w1 : null;
      })(),
    };
  });

  const png = path.join(OUT, f.replace('.html', '.png'));
  await pg.screenshot({ path: png, type: 'png' });
  await pg.close();

  const b = fs.readFileSync(png);
  const px = { w: b.readUInt32BE(16), h: b.readUInt32BE(20) };
  const bad = [];
  if (!checks.display) bad.push('display face missing');
  if (!checks.mono) bad.push('mono missing');
  if (!checks.imgs) bad.push('an image failed to decode');
  if (checks.wide !== null && checks.wide < 1.15) {
    bad.push(`width axis inert (${checks.wide.toFixed(2)}x vs condensed) — static font instance?`);
  }
  if (checks.spill.length) bad.push('runs off the canvas: ' + checks.spill.join(' ; '));
  if (checks.clipped.length) bad.push('clipped by its container: ' + checks.clipped.join(' ; '));
  if (px.w !== size.w * DPR || px.h !== size.h * DPR) bad.push(`${px.w}x${px.h}, expected ${size.w * DPR}x${size.h * DPR}`);
  if (errs.length) bad.push(errs.join('; '));
  if (bad.length) failed++;

  const fit = Object.entries(fitted).map(([k, v]) => `${k.split('#')[0]} ${v}px`).join(', ');
  console.log(`${path.basename(png)}  ${px.w}x${px.h}  ${(b.length / 1024).toFixed(0)}KB`
    + (fit ? `  fit: ${fit}` : '')
    + (bad.length ? `\n  !! ${bad.join('\n     ')}` : '  ok'));
}
await browser.close();
process.exit(failed ? 1 : 0);
