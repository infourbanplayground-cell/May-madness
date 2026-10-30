// Proof sheet for the Vol.8 medal cut-outs.
//
// Two things the renderer cannot tell you. First, WHERE the numeral landed:
// it is centred by a measurement the page makes after the font loads, and a
// pass that silently did nothing looks exactly like a pass that worked.
// Second, what the cut-outs look like ON SOMETHING. A transparent file goes
// wherever somebody drops it, and the whole reason it exists is that the
// opaque version only works on black — so it is composited on black, white,
// cream and a mid-tone, which is where a dark halo or a stray ground shows up.
//
//   node ops/check-blackout-medals.mjs            -> brand/medals-blackout/PROOF.png
import { chromium } from 'playwright';
import fs from 'fs';
import path from 'path';

const OUT = path.resolve('brand/medals-blackout');
const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
let bad = 0;

// ── 1. Where did the numeral actually land? ───────────────────────────────
for (const size of [50, 25]) for (const p of [1, 2, 3]) {
  const src = path.join(OUT, `bo-medal-${size}mm-${p}-bleed.html`);
  if (!fs.existsSync(src)) continue;
  const pg = await browser.newPage({ viewport: { width: 400, height: 400 } });
  await pg.goto('file://' + src);
  await pg.evaluate(() => document.fonts.ready);
  await pg.waitForFunction(() => document.querySelector('svg')?.dataset.centred === '1');
  const r = await pg.evaluate(() => {
    const n = document.getElementById('num'), s = document.getElementById('suf');
    const vb = document.querySelector('svg').viewBox.baseVal;
    const nb = n.getBBox(), sb = s.getBBox();
    const C = vb.width / 2;
    return {
      off: (nb.x + nb.width / 2) - C,
      pct: ((nb.x + nb.width / 2) - C) / vb.width * 100,
      gap: sb.x - (nb.x + nb.width),
      // the suffix must not run past the hairline ring
      sufRight: sb.x + sb.width, limit: C + vb.width * 0.5 * 0.876,
    };
  });
  const flags = [];
  if (Math.abs(r.pct) > 0.15) flags.push(`numeral ${r.pct.toFixed(2)}% off centre`);
  if (r.gap < 0) flags.push('suffix overlaps the numeral');
  if (r.sufRight > r.limit) flags.push('suffix runs past the ring');
  if (flags.length) bad++;
  console.log(`${size}mm ${p}: centre off ${r.off.toFixed(2)} units `
    + `(${r.pct.toFixed(3)}%) · suffix gap ${r.gap.toFixed(1)}`
    + (flags.length ? `  !! ${flags.join(' | ')}` : '  ok'));
  await pg.close();
}

// ── 2. The cut-outs, on four grounds ──────────────────────────────────────
const discs = [50, 25].flatMap(s => [1, 2, 3]
  .map(p => path.join(OUT, `bo-medal-${s}mm-${p}-disc.png`)))
  .filter(fs.existsSync);
const grounds = [['#050505', 'TRUE BLACK'], ['#FFFFFF', 'WHITE'],
                 ['#EFE7D8', 'CREAM'], ['#6E7B86', 'MID-TONE']];
const rows = grounds.map(([bg, label]) => `
  <div style="background:${bg};padding:22px 26px;display:flex;align-items:center;gap:26px">
    <div style="width:118px;font:700 12px/1.4 monospace;letter-spacing:.14em;
      color:${bg === '#FFFFFF' || bg === '#EFE7D8' ? '#111' : '#fff'}">${label}</div>
    ${discs.map(d => {
      const big = d.includes('50mm');
      // Embedded as data URLs, not file:// — a page built with setContent has
      // no base URL, so a file:// <img> is blocked and every cut-out renders
      // as a broken-image glyph while the screenshot still succeeds.
      const b64 = fs.readFileSync(d).toString('base64');
      return `<img src="data:image/png;base64,${b64}" `
        + `style="width:${big ? 132 : 66}px;height:auto;display:block">`;
    }).join('')}
  </div>`).join('');

const pg = await browser.newPage({ viewport: { width: 1180, height: 420 },
                                   deviceScaleFactor: 2 });
await pg.setContent(`<!doctype html><body style="margin:0;background:#222">${rows}</body>`);
await pg.waitForLoadState('load');
const drawn = await pg.evaluate(() =>
  [...document.images].every(i => i.complete && i.naturalWidth > 0));
if (!drawn) { console.error('!! a cut-out did not render on the proof sheet'); bad++; }
const proof = path.join(OUT, 'PROOF.png');
await pg.screenshot({ path: proof, fullPage: true });
await pg.close();
await browser.close();

console.log(`\n${path.basename(proof)}  ${discs.length} cut-outs on ${grounds.length} grounds`);
if (bad) { console.error(`${bad} cut-out(s) failed centring`); process.exit(1); }
