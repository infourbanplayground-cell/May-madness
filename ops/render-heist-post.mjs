// Muscat Heist launch posts -> PNG, with the checks every renderer here carries.
//   python3 build-heist-post.py && node ops/render-heist-post.mjs     SABOTAGE=nofont|wide
//
// Per card: exact size; Archivo really DRAWN (measured against itself falling
// back — fonts.check() answers true with nothing loaded) and the mono face
// loaded; every leaf text run inside the .pad box (the margin is the design,
// not the bitmap edge); no two text runs from different blocks overlapping
// (per line box, getClientRects); no fitted headline left wider than its box;
// on the story, every run inside Instagram's safe band 170..1720.
import { chromium } from 'playwright';
import fs from 'fs';
import path from 'path';

const ROOT = path.resolve(path.dirname(new URL(import.meta.url).pathname), '..');
const DIR = path.join(ROOT, 'brand/heist/posts');
const OUTD = process.env.SABOTAGE ? path.join(DIR, 'sabotage') : DIR;
fs.mkdirSync(OUTD, { recursive: true });
const cards = fs.readdirSync(DIR).filter(f => f.endsWith('.html')).sort();
const b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
let fails = 0;
for (const f of cards) {
  const story = f.startsWith('story');
  const W = 1080, H = story ? 1920 : 1350;
  const pg = await (await b.newContext({ viewport: { width: W, height: H }, deviceScaleFactor: 1 })).newPage();
  let src = fs.readFileSync(path.join(DIR, f), 'utf8');
  const was = src;
  if (process.env.SABOTAGE === 'nofont') src = src.replace(/<style>[\s\S]*?@font-face[\s\S]*?<\/style>/, '<style></style>');
  if (process.env.SABOTAGE === 'wide') src = src.replace('.row .v{', '.row .v{min-width:900px;');
  if (process.env.SABOTAGE && src === was) throw new Error('sabotage changed nothing');
  await pg.setContent(src, { waitUntil: 'load' });
  await pg.waitForFunction(() => document.body.dataset.ready === '1', null, { timeout: 20000 });
  const r = await pg.evaluate(({ story }) => {
    const bad = [];
    const card = document.querySelector('[data-card]').getBoundingClientRect();
    const pad = document.querySelector('.pad').getBoundingClientRect();
    // the face, drawn
    const probe = (fam) => { const s = document.createElement('span'); s.textContent = 'NINE NIGHTS ONE TAKE 407';
      s.style.cssText = `position:absolute;font:800 60px ${fam};font-stretch:112%;white-space:nowrap`; document.body.appendChild(s);
      const w = s.getBoundingClientRect().width; s.remove(); return w; };
    if (Math.abs(probe("'Archivo',serif") - probe('serif')) < 2) bad.push('Archivo not drawn');
    if (![...document.fonts].some(f => /JetBrains/.test(f.family) && f.status === 'loaded')) bad.push('mono not loaded');
    // leaf text runs
    const runs = [];
    const tw = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
    while (tw.nextNode()) { const n = tw.currentNode; if (!n.textContent.trim()) continue;
      const el = n.parentElement; if (el.closest('script,style')) continue;
      const rg = document.createRange(); rg.selectNodeContents(n);
      for (const q of rg.getClientRects()) if (q.width > 1) runs.push({ q, el, t: n.textContent.trim().slice(0, 30) }); }
    const blk = el => { let a = el; while (a && getComputedStyle(a).display.startsWith('inline')) a = a.parentElement; return a; };
    for (const { q, t } of runs) {
      if (q.left < pad.left - 1 || q.right > pad.right + 1 || q.top < pad.top - 1 || q.bottom > pad.bottom + 1) bad.push(`outside the margin: "${t}"`);
      if (story && (q.top < 170 || q.bottom > 1720)) bad.push(`outside the story safe band: "${t}" ${Math.round(q.top)}..${Math.round(q.bottom)}`);
    }
    for (let i = 0; i < runs.length; i++) for (let j = i + 1; j < runs.length; j++) {
      const a = runs[i], c = runs[j]; if (blk(a.el) === blk(c.el)) continue;
      if (blk(a.el).contains(blk(c.el)) || blk(c.el).contains(blk(a.el))) continue;
      const ox = Math.min(a.q.right, c.q.right) - Math.max(a.q.left, c.q.left), oy = Math.min(a.q.bottom, c.q.bottom) - Math.max(a.q.top, c.q.top);
      // a Range box is the line box, not the ink: display caps set tight (.92) share
      // ~30% of an em of empty ascent/descent with their neighbour by design
      const caps = el => el.closest('.h, .big') ? parseFloat(getComputedStyle(el).fontSize) * .3 : 6;
      if (ox > 4 && oy > Math.max(caps(a.el), caps(c.el))) bad.push(`overlap "${a.t}" / "${c.t}" (${Math.round(oy)}px)`);
    }
    for (const el of document.querySelectorAll('[data-fit], .row .v, .h')) if (el.scrollWidth > el.parentElement.clientWidth + 1) bad.push(`too wide: "${el.textContent.slice(0, 24)}"`);
    for (const el of document.querySelectorAll('.row')) if (el.scrollWidth > el.clientWidth + 1) bad.push(`row overflows: "${el.textContent.trim().slice(0, 24)}"`);
    return { size: [Math.round(card.width), Math.round(card.height)], bad: [...new Set(bad)] };
  }, { story });
  if (r.size[0] !== W || r.size[1] !== H) r.bad.push(`size ${r.size}`);
  await pg.locator('[data-card]').screenshot({ path: path.join(OUTD, f.replace('.html', '.png')) });
  console.log(`${r.bad.length ? 'FAIL' : 'ok  '} ${f.padEnd(22)} ${W}x${H}  ${r.bad.slice(0, 4).join(' | ')}`);
  fails += r.bad.length ? 1 : 0;
  await pg.close();
}
await b.close();
console.log(fails ? `FAIL ${fails}` : `ok — ${cards.length} cards in ${path.relative(ROOT, OUTD)}`);
process.exit(fails ? 1 : 0);
