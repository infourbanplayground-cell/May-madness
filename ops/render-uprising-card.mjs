// Render brand/uprising/format-card.html to a 1080x1350 PNG at 2x.
//
// It FAILS if any element runs off the canvas. DESIGN.md §: the stacked
// Blackout lockup once shipped with the B and the T sliced off by the edge of
// the bitmap and every assertion passed, because they were all about the font
// and none about where the ink landed.
//
//   node ops/render-uprising-card.mjs
import { chromium } from 'playwright';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const root = join(dirname(fileURLToPath(import.meta.url)), '..');
const src = join(root, 'brand/uprising/format-card.html');
const out = join(root, 'brand/uprising/format-card.png');

// This container pins Chromium at a fixed path and ships no headless-shell,
// so the default launch fails with "run npx playwright install".
const exe = process.env.PW_CHROMIUM || undefined;
const b = await chromium.launch(exe ? { executablePath: exe } : {});
const p = await b.newPage({ viewport: { width: 1080, height: 1350 }, deviceScaleFactor: 2 });
const errs = [];
p.on('pageerror', e => errs.push(e.message));
await p.goto('file://' + src, { waitUntil: 'load' });
await p.evaluate(() => document.fonts.ready);
await p.waitForTimeout(800);

const fit = await p.evaluate(() => {
  const over = [];
  document.querySelectorAll('.pad *').forEach(e => {
    const r = e.getBoundingClientRect();
    if (!r.width) return;
    if (r.right > 1080.5 || r.bottom > 1350.5 || r.left < -0.5 || r.top < -0.5)
      over.push(`${e.className || e.tagName}  ${Math.round(r.left)},${Math.round(r.top)} → ${Math.round(r.right)},${Math.round(r.bottom)}`);
    // A box can sit inside the canvas while the TEXT in it runs out the side.
    // UPRISING at 184px lost its G off the right edge of the announcement hero
    // and this checker passed, because it was measuring the element and not
    // where the ink landed. scrollWidth is the ink.
    if (e.scrollWidth > e.clientWidth + 1 && getComputedStyle(e).overflow === 'visible'
        && e.childElementCount === 0 && e.textContent.trim())
      over.push(`TEXT CLIPPED: "${e.textContent.trim().slice(0, 22)}" needs ${e.scrollWidth}px in ${e.clientWidth}px`);
  });
  const h1 = getComputedStyle(document.querySelector('h1'));
  // fontFamily reports what was ASKED for, so this passes while the card is
  // drawn in Times; document.fonts.check answers true with nothing loaded at
  // all. Measuring the same string against a face we know is not it is the
  // only test that notices. See ops/render-uprising-announce.mjs.
  const probe = (ff) => {
    const s = document.createElement('span');
    s.textContent = 'UPRISING 11-7 Court';
    s.style.cssText = `position:absolute;visibility:hidden;white-space:nowrap;font:900 100px ${ff};`;
    document.body.appendChild(s);
    const w = s.getBoundingClientRect().width;
    s.remove();
    return w;
  };
  const missing = ['Archivo', 'JetBrains Mono'].filter(f =>
    Math.abs(probe(`"${f}", monospace`) - probe('monospace')) < 1 &&
    Math.abs(probe(`"${f}", serif`) - probe('serif')) < 1);
  return { h: document.body.scrollHeight, over: [...new Set(over)], missing,
           face: h1.fontFamily.split(',')[0], vars: h1.fontVariationSettings };
});

console.log(`display face : ${fit.face}  ${fit.vars}`);
console.log(`content      : 1080x${fit.h} on a 1080x1350 canvas`);
console.log(`overflow     : ${fit.over.length ? fit.over.join('\n               ') : 'nothing runs off the canvas'}`);
if (fit.face !== 'Archivo' || !/125/.test(fit.vars))
  errs.push('the display face is not Archivo at wdth 125 — the font link is wrong or did not load');
if (fit.missing.length)
  errs.push(`FONT NOT LOADED: ${fit.missing.join(', ')} — the card rendered in a fallback `
    + `face. The stylesheet is brand/fonts/fonts.css; re-make it with ops/vendor-fonts.py`);
await p.screenshot({ path: out });
console.log(`wrote        : ${out}`);
console.log(`errors       : ${errs.length ? errs.join('; ') : 'none'}`);
await b.close();
process.exit(fit.over.length || fit.h > 1350 || errs.length ? 1 : 0);
