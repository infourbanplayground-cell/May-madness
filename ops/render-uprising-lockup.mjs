// Render the UPRISING lockup to transparent PNGs.
//
// Two inks: volt for dark backgrounds, near-black for light. A transparent
// file goes wherever somebody drops it, and one colour only works on half of
// those places.
//
// It CHECKS the three things that silently ruin a logo export:
//   · the alpha is real — corners fully transparent, and the file is not just
//     a dark rectangle that happens to look right on a dark page
//   · the ink is not clipped by the crop (scrollWidth, and a pixel sweep of
//     the outermost columns and rows)
//   · the face is Archivo, really drawn, not a fallback that merely answers to
//     the name — see DESIGN.md
//
//   node ops/render-uprising-lockup.mjs
import { chromium } from 'playwright';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import { PNG } from 'pngjs';
import { readFileSync } from 'fs';

const root = join(dirname(fileURLToPath(import.meta.url)), '..');
const src = 'file://' + join(root, 'brand/uprising/lockup.html');
const exe = process.env.PW_CHROMIUM || undefined;
const b = await chromium.launch(exe ? { executablePath: exe } : {});

let bad = 0;
for (const [ink, name] of [['light', 'uprising-lockup.png'], ['dark', 'uprising-lockup-dark.png']]) {
  const out = join(root, 'brand/uprising', name);
  const p = await b.newPage({ viewport: { width: 1600, height: 900 }, deviceScaleFactor: 2 });
  const errs = [];
  p.on('pageerror', e => errs.push(e.message));
  await p.goto(src, { waitUntil: 'load' });
  await p.evaluate(i => document.documentElement.dataset.ink = i, ink);
  await p.evaluate(() => document.fonts.ready);
  await p.waitForTimeout(400);

  // Track the tagline out to the wordmark's exact width — a lockup reads as
  // one object only when its lines share an edge. Done here, after the fonts
  // are in, because the fallback face measures nothing like Archivo.
  const fit = await p.evaluate(() => {
    const w = document.getElementById('word');
    const t = document.getElementById('tag');
    const target = w.getBoundingClientRect().width;
    const n = t.textContent.length;
    let ls = 0;
    t.style.letterSpacing = '0px';
    const base = t.getBoundingClientRect().width;
    ls = (target - base) / n;
    if (ls > 0) { t.style.letterSpacing = ls + 'px'; t.style.marginRight = -ls + 'px'; }
    return { wordW: Math.round(target), tagW: Math.round(t.getBoundingClientRect().width), ls: +ls.toFixed(2) };
  });

  const info = await p.evaluate(() => {
    const probe = (ff) => {
      const s = document.createElement('span');
      s.textContent = 'UPRISING';
      s.style.cssText = `position:absolute;visibility:hidden;white-space:nowrap;font:900 100px ${ff};`;
      document.body.appendChild(s);
      const w = s.getBoundingClientRect().width; s.remove(); return w;
    };
    const missing = Math.abs(probe('"Archivo", serif') - probe('serif')) < 1;
    const over = [];
    document.querySelectorAll('#lock *').forEach(e => {
      if (e.scrollWidth > e.clientWidth + 1 && e.childElementCount === 0 && e.textContent.trim())
        over.push(`${e.textContent.trim().slice(0, 14)} ${e.scrollWidth}>${e.clientWidth}`);
    });
    const r = document.body.getBoundingClientRect();
    return { missing, over, w: Math.ceil(r.width), h: Math.ceil(r.height),
             vars: getComputedStyle(document.getElementById('word')).fontVariationSettings };
  });
  if (info.missing) errs.push('FONT NOT LOADED: Archivo fell back');
  if (!/125/.test(info.vars)) errs.push(`display width is ${info.vars}, expected wdth 125`);
  if (info.over.length) errs.push('TEXT CLIPPED: ' + info.over.join('; '));

  await p.locator('#lock').screenshot({ path: out, omitBackground: true });
  await p.close();

  // The alpha has to be REAL. A PNG with an opaque dark rectangle looks
  // perfect on a dark slide and ruins a white one, and nothing on screen
  // tells you which you have.
  const png = PNG.sync.read(readFileSync(out));
  const at = (x, y) => png.data[(png.width * y + x) * 4 + 3];
  const corners = [[0, 0], [png.width - 1, 0], [0, png.height - 1], [png.width - 1, png.height - 1]];
  const opaqueCorners = corners.filter(([x, y]) => at(x, y) > 8).length;
  if (opaqueCorners) errs.push(`${opaqueCorners} corner(s) are not transparent`);
  let opaque = 0;
  for (let i = 3; i < png.data.length; i += 4) if (png.data[i] > 8) opaque++;
  const pct = (100 * opaque / (png.width * png.height)).toFixed(1);
  if (opaque === 0) errs.push('the image is entirely transparent');
  if (pct > 90) errs.push(`${pct}% opaque — this is a rectangle, not a cut-out`);
  // Ink touching the very edge means the crop ate some of it.
  const edge = [];
  for (let x = 0; x < png.width; x++) { if (at(x, 0) > 8 || at(x, png.height - 1) > 8) { edge.push('top/bottom'); break; } }
  for (let y = 0; y < png.height; y++) { if (at(0, y) > 8 || at(png.width - 1, y) > 8) { edge.push('left/right'); break; } }
  if (edge.length) errs.push('ink touches the crop edge: ' + [...new Set(edge)].join(', '));

  const ok = !errs.length;
  if (!ok) bad++;
  console.log(`${ok ? '  ok ' : '  !! '}${name.padEnd(28)} ${png.width}x${png.height}  `
    + `${pct}% ink  wordmark ${fit.wordW}px, tagline tracked ${fit.ls}px to match`
    + (errs.length ? `\n       ${errs.join('\n       ')}` : ''));
}
await b.close();
process.exit(bad ? 1 : 0);
