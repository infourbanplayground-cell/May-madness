// Render the UPRISING infographic to PNG at 2x.
//
// `infographic-story.html` is sized at 1920 and everything else at 1350, the
// same convention ops/render-uprising-announce.mjs uses.
//
// It FAILS if anything runs off the canvas, if any run of type is clipped
// inside its own box, if two runs of type sit on top of each other, or if the
// display face was not really drawn. The first of those is the one DESIGN.md
// records: the stacked Blackout lockup shipped with the B and the T sliced off
// by the edge of the bitmap while every assertion passed, because they were all
// about the font and none about where the ink landed.
//
//   node ops/render-uprising-infographic.mjs
//   SABOTAGE=nofont|wide node ops/render-uprising-infographic.mjs
import { chromium } from 'playwright';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import fs from 'fs';

const root = join(dirname(fileURLToPath(import.meta.url)), '..');
const DIR = join(root, 'brand/uprising');
const SABOTAGE = process.env.SABOTAGE || '';

const exe = process.env.PW_CHROMIUM || '/opt/pw-browsers/chromium';
const browser = await chromium.launch(fs.existsSync(exe) ? { executablePath: exe } : {});
let failed = 0;

for (const name of ['infographic-feed', 'infographic-story']) {
  const src = join(DIR, `${name}.html`);
  if (!fs.existsSync(src)) { console.log(`skip ${name}: no html`); continue; }
  const H = name.endsWith('-story') ? 1920 : 1350;

  const p = await browser.newPage({ viewport: { width: 1080, height: H }, deviceScaleFactor: 2 });
  const errs = [];
  p.on('pageerror', e => errs.push(e.message));
  await p.goto('file://' + src, { waitUntil: 'load' });
  await p.evaluate(() => document.fonts.ready);

  if (SABOTAGE === 'nofont') {
    await p.evaluate(() => { for (const l of document.querySelectorAll('link[rel=stylesheet]')) l.remove(); });
    await p.waitForTimeout(200);
  } else if (SABOTAGE === 'wide') {
    // A fixed-width cell too narrow for what the engine put in it. Lengthening
    // the text alone proves nothing — it WRAPS, the rung grows taller and
    // nothing overflows, which is a legitimate pass. Squeezing the cell with
    // the wrap off is the failure worth catching: the label runs out over the
    // column beside it, which no width assertion on the box would notice.
    await p.evaluate(() => {
      const s = document.createElement('style');
      s.textContent = '.rung .cn{width:40px;white-space:nowrap}';
      document.head.appendChild(s);
    });
  }

  const r = await p.evaluate((H) => {
    const over = [];
    // THE MARGIN IS THE TEST, NOT THE BITMAP EDGE. A card has a declared
    // padding and that padding is the design; checking only against 1080
    // passes anything that eats the margin and stops just short of the crop.
    // The footer's host line did exactly that — 59px past the 64px padding on
    // both sizes, 5px short of the canvas, and every assertion was green.
    const pad = document.querySelector('.pad');
    const cs = getComputedStyle(pad);
    const box = pad.getBoundingClientRect();
    const safe = {
      l: box.left + parseFloat(cs.paddingLeft), r: box.right - parseFloat(cs.paddingRight),
      t: box.top + parseFloat(cs.paddingTop), b: box.bottom - parseFloat(cs.paddingBottom),
    };
    document.querySelectorAll('.pad *').forEach(e => {
      const b = e.getBoundingClientRect();
      if (!b.width) return;
      if (b.right > 1080.5 || b.bottom > H + 0.5 || b.left < -0.5 || b.top < -0.5)
        over.push(`${e.className || e.tagName} runs off: ${Math.round(b.left)},${Math.round(b.top)}`
          + ` -> ${Math.round(b.right)},${Math.round(b.bottom)}`);
      else if (b.right > safe.r + 0.5 || b.left < safe.l - 0.5)
        over.push(`${e.className || e.tagName} eats the margin: ${Math.round(b.left)}..`
          + `${Math.round(b.right)} outside ${Math.round(safe.l)}..${Math.round(safe.r)}`);
      // A box can sit inside the canvas while the TEXT in it runs out the side.
      if (e.scrollWidth > e.clientWidth + 1 && getComputedStyle(e).overflow === 'visible'
          && e.childElementCount === 0 && e.textContent.trim())
        over.push(`clipped: "${e.textContent.trim().slice(0, 24)}" needs ${e.scrollWidth}px`
          + ` in ${e.clientWidth}px`);
    });

    // Two runs of type on top of each other. A wrapped line never overflows
    // anything, so every width assertion stays green while it sits on the one
    // below it — this is the check that notices.
    //
    // TWO THINGS THIS HAS TO GET RIGHT OR IT IS ALL FALSE POSITIVES.
    //
    // Use getClientRects(), the per-LINE boxes, not getBoundingClientRect():
    // the union box of a run that wraps over three lines spans the whole
    // paragraph and overlaps every sibling run in it.
    //
    // And only compare runs in DIFFERENT blocks. Inline runs inside one
    // paragraph share its line boxes by definition — `<b>` sitting on the
    // text around it is how prose works, and h1's two lines at line-height
    // .86 overlap each other on purpose. What is worth knowing is one block
    // sitting on another.
    const blockOf = (n) => {
      for (let e = n.parentElement; e; e = e.parentElement)
        if (getComputedStyle(e).display !== 'inline') return e;
      return document.body;
    };
    const lines = [];
    const walk = document.createTreeWalker(document.querySelector('.pad'), NodeFilter.SHOW_TEXT);
    for (let t = walk.nextNode(); t; t = walk.nextNode()) {
      if (!t.nodeValue.trim()) continue;
      const rg = document.createRange();
      rg.selectNodeContents(t);
      const blk = blockOf(t);
      for (const b of rg.getClientRects()) {
        if (b.width < 0.5 || b.height < 0.5) continue;
        lines.push({ t: t.nodeValue.trim().slice(0, 26), blk,
                     c: blk.getAttribute('class') || blk.tagName,
                     x: b.x, y: b.y, w: b.width, h: b.height });
      }
    }
    for (let i = 0; i < lines.length; i++) for (let j = i + 1; j < lines.length; j++) {
      const a = lines[i], c = lines[j];
      if (a.blk === c.blk) continue;
      const ox = Math.min(a.x + a.w, c.x + c.w) - Math.max(a.x, c.x);
      const oy = Math.min(a.y + a.h, c.y + c.h) - Math.max(a.y, c.y);
      // A client rect is a line box, not the ink, so neighbouring blocks of
      // display type nearly touch by design.
      if (ox > 2 && oy > 9) over.push(`overlap: ${a.c} "${a.t}" / ${c.c} "${c.t}"`);
    }

    // THE FACE MUST BE PROVED DRAWN. getComputedStyle reports what was ASKED
    // for whether or not it loaded, and document.fonts.check() answers true
    // with zero faces loaded. Archivo is measured against the SAME STACK
    // FALLING BACK; JetBrains Mono cannot be width-probed here because it is
    // installed system-wide in this container, so the stack resolves to the
    // system copy with the stylesheet gone and the probe passes with nothing
    // loaded — it is checked for being in document.fonts instead.
    const probe = (stack, it) => {
      const s = document.createElement('span');
      s.textContent = 'UPRISING 11-7 Court HAMBURGEFONS';
      s.style.cssText = 'position:absolute;visibility:hidden;white-space:nowrap;'
        + `font-size:100px;font-family:${stack};` + (it ? 'font-style:italic;font-weight:900;' : '');
      document.body.appendChild(s);
      const w = s.getBoundingClientRect().width;
      s.remove();
      return w;
    };
    const loaded = [...document.fonts].filter(f => f.status === 'loaded')
      .map(f => f.family.replace(/['"]/g, ''));
    const h1 = getComputedStyle(document.querySelector('h1'));
    return {
      over: [...new Set(over)],
      height: document.body.scrollHeight,
      fonts: {
        'archivo drawn': probe("'Archivo',serif", true) !== probe('serif', true),
        'archivo embedded': loaded.includes('Archivo'),
        'mono embedded': loaded.includes('JetBrains Mono'),
      },
      vars: h1.fontVariationSettings,
      pips: document.querySelectorAll('.pip').length,
      rungs: document.querySelectorAll('.rung').length,
    };
  }, H);

  const png = join(DIR, `${name}${SABOTAGE ? '-sabotage' : ''}.png`);
  await p.screenshot({ path: png });
  await p.close();

  const bad = [...r.over];
  const missing = Object.entries(r.fonts).filter(([, ok]) => !ok).map(([k]) => k);
  if (missing.length) bad.push(`FONT NOT LOADED: ${missing.join(', ')} — the stylesheet is `
    + `brand/fonts/fonts.css; re-make it with ops/vendor-fonts.py`);
  if (!/125/.test(r.vars || '')) bad.push(`display type is at ${r.vars || 'no width axis'}, not wdth 125`);
  if (r.height > H + 1) bad.push(`content is ${r.height}px tall on a ${H}px canvas`);
  if (!r.pips) bad.push('the night strip drew no rounds');
  if (r.rungs < 2) bad.push(`the ladder drew ${r.rungs} rungs`);
  if (errs.length) bad.push('page errors: ' + errs.join('; '));

  if (bad.length) failed++;
  console.log(`${name}.png  1080x${H}@2x  ${(fs.statSync(png).size / 1024).toFixed(0)}KB  `
    + `${r.rungs} courts, ${r.pips} rounds`
    + (bad.length ? `\n  !! ${bad.join('\n  !! ')}` : '  ok'));
}
await browser.close();
if (failed) { console.error(`\n${failed} card(s) failed their checks`); process.exit(1); }
