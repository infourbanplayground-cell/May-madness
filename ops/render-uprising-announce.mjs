// Render the UPRISING announcement pages to PNGs.
// Fails if anything runs off its own canvas, or if the display face is not
// Archivo at wdth 125 — the Blackout lockup shipped once with letters sliced
// off while every assertion passed, because they were all about the font.
//
//   python3 build-uprising-announce.py && node ops/render-uprising-announce.mjs
import { chromium } from 'playwright';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import { readdirSync } from 'fs';

const root = join(dirname(fileURLToPath(import.meta.url)), '..');
const dir = join(root, 'brand/uprising/posts');
// Feed cards are 1080x1350 (the tallest crop the feed will show); anything
// named story-* is a 1080x1920 full-screen story. Keyed off the name rather
// than a list, so adding a sixth story card needs no edit here — a story
// rendered at 1350 would be silently letterboxed, not fail.
const size = n => n.startsWith('story-') ? [1080, 1920] : [1080, 1350];
const base = process.env.UP_BASE || ('file://' + dir + '/');

// This container pins Chromium at a fixed path and has no headless-shell, so
// Playwright's default launch fails with "run npx playwright install".
//
// It must NOT be launched with --no-proxy-server. That flag was added while
// these pages were being tested against a local mirror on 127.0.0.1, and it
// cuts Chromium off from the agent proxy — which is the only route to
// fonts.googleapis.com. The pages then render in Times, the assertion below
// is what catches it, and every card has to be re-rendered.
const exe = process.env.PW_CHROMIUM || undefined;
const b = await chromium.launch(exe ? { executablePath: exe } : {});
let bad = 0;
for (const f of readdirSync(dir).filter(x => x.endsWith('.html')).sort()) {
  const name = f.replace(/\.html$/, '');
  const [w, h] = size(name);
  const p = await b.newPage({ viewport: { width: w, height: h }, deviceScaleFactor: 2 });
  const errs = [];
  p.on('pageerror', e => errs.push(e.message));
  await p.goto(base + f, { waitUntil: 'load' });
  await p.evaluate(() => document.fonts.ready);
  await p.waitForTimeout(700);

  // Shrink-to-fit, applied AFTER the fonts load — the fallback face measures
  // narrower than Archivo at wdth 125, so anything sized before fonts.ready is
  // sized against the wrong letters. Same mechanism as the Blackout brand
  // renderer, and for the same reason: UPRISING at 184px lost its G off the
  // right edge of the card.
  const shrunk = await p.evaluate(() => {
    const out = [];
    document.querySelectorAll('[data-fit]').forEach(e => {
      const start = parseFloat(getComputedStyle(e).fontSize);
      let size = start;
      while (size > 8 && e.scrollWidth > e.clientWidth) {
        size -= 1; e.style.fontSize = size + 'px';
      }
      if (size !== start) out.push(`${e.className.toString().slice(0,24)} ${start}→${size}px`);
    });
    return out;
  });
  const fit = await p.evaluate(([w, h]) => {
    const over = [];
    document.querySelectorAll('.pad *').forEach(e => {
      const r = e.getBoundingClientRect();
      if (!r.width) return;
      if (r.right > w + .5 || r.bottom > h + .5 || r.left < -.5 || r.top < -.5)
        over.push(`${(e.className || e.tagName).toString().slice(0, 28)} ${Math.round(r.left)},${Math.round(r.top)}→${Math.round(r.right)},${Math.round(r.bottom)}`);
      // A box can sit inside the canvas while the TEXT in it runs out the side.
      // That is how the Blackout lockup shipped with letters sliced off and
      // every assertion passed: they were all about the element, none about
      // where the ink landed. scrollWidth is the ink.
      if (e.scrollWidth > e.clientWidth + 1 && getComputedStyle(e).overflow === 'visible'
          && e.childElementCount === 0 && e.textContent.trim())
        over.push(`TEXT CLIPPED: "${e.textContent.trim().slice(0, 22)}" needs ${e.scrollWidth}px in ${e.clientWidth}px`);
    });
    const d = document.querySelector('.disp');
    return { h: document.body.scrollHeight, over: [...new Set(over)],
             face: getComputedStyle(d).fontFamily.split(',')[0],
             vars: getComputedStyle(d).fontVariationSettings,
             // getComputedStyle reports the family that was ASKED for, loaded
             // or not, so the check above passes happily while the card is
             // drawn in Times. document.fonts.check is no better: with no
             // @font-face loaded at all it answers true. The only honest test
             // is to measure the same string in the face and in a face we know
             // is NOT it — if the widths match, the real one never arrived.
             missing: ['Archivo', 'JetBrains Mono'].filter(f => {
               const probe = (ff) => {
                 const s = document.createElement('span');
                 s.textContent = 'UPRISING 11-7 Court';
                 s.style.cssText = `position:absolute;visibility:hidden;white-space:nowrap;`
                   + `font:900 100px ${ff};`;
                 document.body.appendChild(s);
                 const w = s.getBoundingClientRect().width;
                 s.remove();
                 return w;
               };
               return Math.abs(probe(`"${f}", monospace`) - probe('monospace')) < 1
                   && Math.abs(probe(`"${f}", serif`) - probe('serif')) < 1;
             }),
             faces: document.fonts.size };
  }, [w, h]);
  if (fit.face !== 'Archivo' || !/125/.test(fit.vars))
    errs.push(`display face is ${fit.face} ${fit.vars}, expected Archivo wdth 125`);
  if (fit.missing.length)
    errs.push(`FONT NOT LOADED: ${fit.missing.join(', ')} — the page rendered in a `
      + `fallback face (${fit.faces} faces loaded). The stylesheet is `
      + `brand/fonts/fonts.css; re-make it with ops/vendor-fonts.py.`);
  await p.screenshot({ path: join(dir, name + '.png') });
  const ok = !fit.over.length && fit.h <= h && !errs.length;
  if (!ok) bad++;
  console.log(`${ok ? '  ok ' : '  !! '}${name}  ${w}x${h}  content ${fit.h}px` +
    (shrunk.length ? `  [fit: ${shrunk.join(', ')}]` : '') +
    (fit.over.length ? `\n       overflow: ${fit.over.join('\n                 ')}` : '') +
    (errs.length ? `\n       ${errs.join('; ')}` : ''));
  await p.close();
}
await b.close();
process.exit(bad ? 1 : 0);
