// Render the Vol.9 interim brand art, and prove it is what it claims to be.
//
// Three things are checked, all of them failures this repo has actually
// shipped before:
//
//   · the display face was really DRAWN, measured against the same stack
//     falling back — getComputedStyle reports what was asked for whether or
//     not it loaded, and document.fonts.check() answers true with zero faces
//     loaded. The whole UPRISING story series once rendered in Times with
//     every assertion green.
//   · nothing runs off the canvas, and no run of type is clipped inside its
//     own box. The Blackout stacked lockup shipped with the B and the T
//     sliced off by the edge of the bitmap and every assertion passed,
//     because they were all about the font and none about where the ink
//     landed.
//   · the tile and the band actually loaded. They are base64 in the page, so
//     a missing file is a silently plain red rectangle.
//
//   node render-national-brand.mjs
import { chromium } from 'playwright';
import fs from 'fs';
import path from 'path';

const DIR = path.resolve('brand/national');
const PIECES = {
  'national-lockup': [3100, 840],
  'national-mark': [1024, 1024],
  'national-og': [1200, 630],
  'national-icon': [512, 512],
};

const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
let failed = 0;

for (const [name, [w, h]] of Object.entries(PIECES)) {
  const src = path.join(DIR, name + '.html');
  if (!fs.existsSync(src)) { console.log(`skip ${name}: no html`); continue; }
  // Render at a sane device pixel count: a 3100px lockup at 2x is 6200px wide
  // for no benefit, and these go into an <img> at a fraction of their size.
  const pg = await browser.newPage({ viewport: { width: w, height: h }, deviceScaleFactor: 1 });
  const errs = [];
  pg.on('pageerror', e => errs.push(e.message));
  await pg.goto('file://' + src, { waitUntil: 'load' });
  await pg.evaluate(() => document.fonts.ready);

  // SHRINK TO FIT, AFTER THE FACE HAS LOADED. Sizing before that measures the
  // fallback, which is nothing like Archivo at wdth 125 — the same trap every
  // other brand builder here records. Done in the renderer rather than the
  // page so one rule covers all four pieces and a longer volume name cannot
  // push the wordmark off its own bitmap.
  const fit = await pg.evaluate(({ w, h }) => {
    const wrap = document.querySelector('.wrap');
    const margin = Math.round(h * 0.12);
    const sized = [...wrap.querySelectorAll('[style*="font-size"]')];
    let guard = 0, k = 1;
    const tooWide = () => wrap.getBoundingClientRect().width > w - margin
                       || wrap.getBoundingClientRect().height > h - margin;
    while (tooWide() && guard++ < 200) {
      k *= 0.98;
      for (const e of sized) {
        if (!e.dataset.fs0) e.dataset.fs0 = parseFloat(getComputedStyle(e).fontSize);
        e.style.fontSize = (Number(e.dataset.fs0) * k) + 'px';
      }
    }
    return { shrunk: +(k).toFixed(3), passes: guard };
  }, { w, h });

  const r = await pg.evaluate(({ w, h }) => {
    const probe = (stack, it) => {
      const s = document.createElement('span');
      s.textContent = '56 NATIONAL HAMBURGEFONS';
      s.style.cssText = 'position:absolute;visibility:hidden;white-space:nowrap;'
        + `font-size:100px;font-family:${stack};` + (it ? 'font-style:italic;font-weight:900;' : '');
      document.body.appendChild(s);
      const x = s.getBoundingClientRect().width;
      s.remove();
      return x;
    };
    const loaded = [...document.fonts].filter(f => f.status === 'loaded')
      .map(f => f.family.replace(/['"]/g, ''));
    const over = [];
    for (const e of document.querySelectorAll('.wrap *, .wrap')) {
      const b = e.getBoundingClientRect();
      if (!b.width) continue;
      if (b.right > w + 0.5 || b.bottom > h + 0.5 || b.left < -0.5 || b.top < -0.5)
        over.push(`${e.className || e.tagName} runs off: `
          + `${Math.round(b.left)},${Math.round(b.top)} -> ${Math.round(b.right)},${Math.round(b.bottom)}`);
      if (e.scrollWidth > e.clientWidth + 1 && e.childElementCount === 0 && e.textContent.trim())
        over.push(`clipped: "${e.textContent.trim().slice(0, 22)}" `
          + `needs ${e.scrollWidth}px in ${e.clientWidth}px`);
    }
    // The tile and the band are background-images on their own elements; if
    // the base64 is wrong the element is simply flat and nothing complains.
    const bg = el => getComputedStyle(el).backgroundImage;
    return {
      over,
      archivo: probe("'Archivo',serif", true) !== probe('serif', true),
      embedded: loaded.includes('Archivo'),
      tile: /url\(/.test(bg(document.querySelector('.tile'))),
      band: /url\(/.test(bg(document.querySelector('.band'))),
      text: (document.querySelector('.wrap')?.innerText || '').replace(/\s+/g, ' ').trim(),
    };
  }, { w, h });

  const png = path.join(DIR, name + '.png');
  await pg.screenshot({ path: png });
  await pg.close();

  const bad = [...r.over];
  if (!r.archivo) bad.push('Archivo was NOT drawn — it fell back');
  if (!r.embedded) bad.push('Archivo is not embedded');
  if (!r.tile) bad.push('the khanjar tile did not load');
  if (!r.band) bad.push('the masar band did not load');
  // Vol.8's name must not survive into Vol.9's art, which is the entire point
  // of making it.
  if (/blackout/i.test(r.text)) bad.push('the art still says BLACKOUT');
  if (errs.length) bad.push(errs.join('; '));

  if (bad.length) failed++;
  console.log(`${name}.png  ${w}x${h}  ${(fs.statSync(png).size / 1024).toFixed(0)}KB  `
    + `"${r.text.slice(0, 48)}"` + (fit.shrunk < 1 ? `  fit ${fit.shrunk}` : '')
    + (bad.length ? `\n  !! ${bad.join('\n  !! ')}` : '  ok'));
}
await browser.close();
if (failed) { console.error(`\n${failed} piece(s) failed their checks`); process.exit(1); }
