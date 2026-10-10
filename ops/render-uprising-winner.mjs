// Render the UPRISING champion's sticker, and the feed card it goes out on.
//
// Two outputs, in this order, because the second one uses the first:
//   brand/uprising/winner-sticker.png   TRANSPARENT seal — drop it on a photo
//   brand/uprising/winner-post.png      1080x1350 feed card built around it
//
// A template, not a one-off: the name, the points and the night are arguments,
// so the night it is actually used on does not need a code change.
//
//   node ops/render-uprising-winner.mjs
//   node ops/render-uprising-winner.mjs --name "Munther Rahbi" --points 104
//   node ops/render-uprising-winner.mjs --name "..." --points 104 --date 2026-11-14 --vol "Night Two"
//
// It checks the same three things render-uprising-lockup.mjs checks, for the
// same reasons (DESIGN.md):
//   · the alpha is REAL — corners transparent, not the whole file, and not an
//     opaque rectangle that looks right on a dark post and ruins a light one
//   · the INK is inside the crop — scrollWidth, plus a pixel sweep of the
//     outermost rows and columns, because text can run out of a box that
//     itself fits the canvas
//   · Archivo was really DRAWN, measured against a face it cannot be, since
//     a webfont that fails to load is a silent fallback and not an error
import { chromium } from 'playwright';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import { PNG } from 'pngjs';
import { readFileSync, existsSync } from 'fs';

const root = join(dirname(fileURLToPath(import.meta.url)), '..');
const dir = join(root, 'brand/uprising');
const social = JSON.parse(readFileSync(join(root, 'uprising-social.json'), 'utf8'));

const argv = process.argv.slice(2);
const arg = (k, d) => { const i = argv.indexOf('--' + k); return i >= 0 && argv[i + 1] ? argv[i + 1] : d; };

// The placeholder name is deliberately not a real past champion's: a card
// that says somebody won a night they did not is worse than an obvious blank.
const NAME = arg('name', 'WINNER NAME');
const PTS = arg('points', '');
const DATE = arg('date', social.date);
const VOL = arg('vol', 'Night One');
// Not "Climbed to Court One" — the seal's own rim already says that, and the
// card read as a stutter. The prize instead, and it says VOUCHER, because
// "takes 15 OMR" reads as cash and somebody would turn up expecting notes.
const LINE = arg('line',
  `Takes the ${social.championPrize} ${social.currency} ${social.championPrizeKind}`);

const MONTHS = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC'];
const [Y, M, D] = DATE.split('-').map(Number);
const WHEN = `${social.name} · ${D} ${MONTHS[M - 1]} ${Y}`;
// No score, no line. The first version defaulted this to "CHAMPION", which
// the kicker above the name already says — the card went out saying it twice.
const POINTS = PTS ? `${PTS} POINTS` : '';

const exe = process.env.PW_CHROMIUM || undefined;
const b = await chromium.launch(exe ? { executablePath: exe } : {});

// Display type that must fill a width is shrunk AFTER document.fonts.ready:
// the fallback face measures narrower than Archivo at wdth 125, so sizing
// before the face is in sizes against the wrong letters.
const fitAll = () => {
  document.querySelectorAll('[data-fit]').forEach(el => {
    const box = el.parentElement;
    const room = box.clientWidth - parseFloat(getComputedStyle(box).paddingLeft || 0)
      - parseFloat(getComputedStyle(box).paddingRight || 0);
    let px = parseFloat(getComputedStyle(el).fontSize);
    let guard = 60;
    while (el.scrollWidth > room && px > 18 && guard--) { px -= 2; el.style.fontSize = px + 'px'; }
  });
};

// getComputedStyle reports the family in the stylesheet whether or not it
// loaded, and document.fonts.check() answers true with zero faces loaded, so
// the only honest test measures a probe string in the face and in one it
// cannot be. Injected into every page so both renders run the same check.
const HELPERS = `
window.probeFn = function () {
  const w = (ff, style) => {
    const s = document.createElement('span');
    s.textContent = 'CHAMPIONapg';
    s.style.cssText = 'position:absolute;visibility:hidden;white-space:nowrap;font:'
      + (style || '') + ' 700 100px ' + ff + ';';
    document.body.appendChild(s);
    const x = s.getBoundingClientRect().width; s.remove(); return x;
  };
  // The probe has to ask for the face the PAGE asks for. The display type here
  // is Archivo ITALIC; a face nothing on the page uses is never fetched, stays
  // unloaded, and measures as the fallback — which reads as a failure when
  // nothing is actually wrong.
  const missing = [];
  if (Math.abs(w('"Archivo", serif', 'italic') - w('serif', 'italic')) < 1) missing.push('Archivo italic');
  if (Math.abs(w('"JetBrains Mono", serif') - w('serif')) < 1) missing.push('JetBrains Mono');
  return missing;
};
window.clipFn = function (sel) {
  const over = [];
  document.querySelectorAll(sel).forEach(e => {
    if (e.scrollWidth > e.clientWidth + 1 && e.childElementCount === 0 && e.textContent.trim())
      over.push('"' + e.textContent.trim().slice(0, 18) + '" ' + e.scrollWidth + '>' + e.clientWidth);
  });
  return over;
};`;

const newPage = async opts => {
  const p = await b.newPage(opts);
  await p.addInitScript(HELPERS);
  return p;
};

let bad = 0;
const report = (name, errs, extra) => {
  if (errs.length) bad++;
  console.log(`${errs.length ? '  !! ' : '  ok '}${name.padEnd(22)} ${extra}`
    + (errs.length ? `\n       ${errs.join('\n       ')}` : ''));
};

// ---- 1. the sticker ------------------------------------------------------
const stickerOut = join(dir, 'winner-sticker.png');
{
  const p = await newPage({ viewport: { width: 1600, height: 1600 }, deviceScaleFactor: 2 });
  const errs = [];
  p.on('pageerror', e => errs.push(e.message));
  await p.goto('file://' + join(dir, 'winner-sticker.html'), { waitUntil: 'load' });
  await p.evaluate(v => {
    document.getElementById('name').textContent = v.name.toUpperCase();
    document.getElementById('pts').textContent = v.points;
    document.getElementById('when').textContent = v.when;
  }, { name: NAME, points: POINTS, when: WHEN });
  await p.evaluate(() => document.fonts.ready);
  await p.evaluate(fitAll);
  await p.waitForTimeout(250);

  const info = await p.evaluate(() => ({ miss: probeFn(), over: clipFn('#seal *') }));
  if (info.miss.length) errs.push('FONT NOT LOADED: ' + info.miss.join(', '));
  if (info.over.length) errs.push('TEXT CLIPPED: ' + info.over.join('; '));
  const vars = await p.evaluate(() => getComputedStyle(document.getElementById('name')).fontVariationSettings);
  if (!/125/.test(vars)) errs.push(`display width is ${vars}, expected wdth 125`);

  await p.locator('#seal').screenshot({ path: stickerOut, omitBackground: true });
  await p.close();

  const png = PNG.sync.read(readFileSync(stickerOut));
  const at = (x, y) => png.data[(png.width * y + x) * 4 + 3];
  const corners = [[0, 0], [png.width - 1, 0], [0, png.height - 1], [png.width - 1, png.height - 1]];
  const oc = corners.filter(([x, y]) => at(x, y) > 8).length;
  if (oc) errs.push(`${oc} corner(s) are not transparent`);
  let opaque = 0;
  for (let i = 3; i < png.data.length; i += 4) if (png.data[i] > 8) opaque++;
  const pct = (100 * opaque / (png.width * png.height));
  if (!opaque) errs.push('the image is entirely transparent');
  if (pct > 90) errs.push(`${pct.toFixed(1)}% opaque — a rectangle, not a cut-out`);
  const edge = [];
  for (let x = 0; x < png.width; x++) if (at(x, 0) > 8 || at(x, png.height - 1) > 8) { edge.push('top/bottom'); break; }
  for (let y = 0; y < png.height; y++) if (at(0, y) > 8 || at(png.width - 1, y) > 8) { edge.push('left/right'); break; }
  if (edge.length) errs.push('ink touches the crop edge: ' + [...new Set(edge)].join(', '));

  report('winner-sticker.png', errs, `${png.width}x${png.height}  ${pct.toFixed(1)}% ink  transparent`);
}

// ---- 2. the feed card ----------------------------------------------------
{
  if (!existsSync(stickerOut)) { console.log('  !! no sticker to build the post from'); process.exit(1); }
  const p = await newPage({ viewport: { width: 1080, height: 1350 }, deviceScaleFactor: 2 });
  const errs = [];
  p.on('pageerror', e => errs.push(e.message));
  await p.goto('file://' + join(dir, 'winner-post.html'), { waitUntil: 'load' });
  await p.evaluate(v => {
    document.getElementById('vol').textContent = v.vol + ' · Urban Playground';
    document.getElementById('line').textContent = v.line;
    document.getElementById('next').textContent = v.next;
  }, { vol: VOL, line: LINE, next: social.cadenceLine });
  await p.evaluate(() => document.fonts.ready);
  await p.evaluate(() => new Promise(r => {
    const i = document.getElementById('sealimg');
    if (i.complete && i.naturalWidth) return r();
    i.onload = r; i.onerror = r;
  }));
  await p.evaluate(fitAll);
  await p.waitForTimeout(250);

  const info = await p.evaluate(() => ({
    miss: probeFn(), over: clipFn('body *'),
    seal: (() => { const i = document.getElementById('sealimg'); return i.naturalWidth; })(),
    // Anything running off the canvas is a bad export, not a design choice.
    off: [...document.querySelectorAll('body > *')].filter(e => {
      const r = e.getBoundingClientRect();
      return r.left < -1 || r.top < -1 || r.right > 1081 || r.bottom > 1351;
    }).map(e => e.className || e.tagName),
  }));
  if (info.miss.length) errs.push('FONT NOT LOADED: ' + info.miss.join(', '));
  if (info.over.length) errs.push('TEXT CLIPPED: ' + info.over.join('; '));
  if (!info.seal) errs.push('the seal image did not load — the post is empty where the seal goes');
  if (info.off.length) errs.push('OFF CANVAS: ' + info.off.join(', '));

  const out = join(dir, 'winner-post.png');
  await p.screenshot({ path: out, clip: { x: 0, y: 0, width: 1080, height: 1350 } });
  await p.close();
  const png = PNG.sync.read(readFileSync(out));
  report('winner-post.png', errs, `${png.width}x${png.height}  seal ${info.seal}px source`);
}

await b.close();
console.log(`\n  ${NAME} — ${POINTS} — ${WHEN}`);
process.exit(bad ? 1 : 0);
