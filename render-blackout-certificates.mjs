// Renders the Vol.8 placement certificates to 300 DPI PNG, which
// pack-blackout-certificate-pdfs.py then wraps into print-ready A4 pages.
//
// Why a raster and not Chromium's vector PDF export: the same reason Vol.6 and
// Vol.7 rasterise. Vol.8's sheet carries no blurred shadows at all — the brand
// art records that Chromium tiles those and the seams print as hard-edged
// rectangles — but it does carry full-bleed repeating gradients and a violet
// wash, and a screenshot of the page is the one artefact that is certain to
// print as what was designed.
//
// A4 landscape is 297 x 210mm. At 96 CSS px/inch that is 1122.52 x 793.70 px, so
// deviceScaleFactor 3.125 gives 3508 x 2480 — exactly 300 DPI across 297mm.
import { chromium } from 'playwright';
import fs from 'fs';
import path from 'path';

const OUT = path.resolve('brand/certificates-blackout');
const CSS_W = 297 / 25.4 * 96;     // 1122.52
const CSS_H = 210 / 25.4 * 96;     // 793.70
const DPR = 3508 / CSS_W;          // 3.125 -> 300 DPI
const MM = 96 / 25.4;              // CSS px per mm
const places = process.argv.slice(2).length ? process.argv.slice(2) : ['1', '2', '3', '4', '5'];
const SABOTAGE = process.env.SABOTAGE || '';

const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
let failed = 0;

for (const n of places) {
  const src = path.join(OUT, `bo-certificate-${n}.html`);
  if (!fs.existsSync(src)) { console.log(`skip ${n}: no html`); continue; }

  const pg = await browser.newPage({
    viewport: { width: Math.round(CSS_W), height: Math.round(CSS_H) },
    deviceScaleFactor: DPR,
  });
  const errs = [];
  pg.on('pageerror', e => errs.push(e.message));
  await pg.goto('file://' + src, { waitUntil: 'load' });

  // SABOTAGE=nofont|long proves these checks can go red. A harness whose
  // assertions have never failed is a harness nobody has tested.
  if (SABOTAGE === 'nofont') {
    await pg.evaluate(() => {
      for (const s of document.querySelectorAll('style'))
        s.textContent = s.textContent.replace(/@font-face\s*\{[^}]*\}/g, '');
    });
  } else if (SABOTAGE === 'long') {
    await pg.evaluate(() => {
      const t = document.querySelector('.typed');
      if (t) t.textContent = 'Almuntaser Hasni & Muatasim Sabri Al Wahaibi';
    });
  }
  await pg.evaluate(() => document.fonts.ready);

  const checks = await pg.evaluate((mm) => {
    // THE FACE MUST BE PROVED DRAWN, NOT ASKED FOR. getComputedStyle reports
    // the family in the stylesheet whether or not it loaded, and
    // document.fonts.check() answers true with zero faces loaded. The only
    // honest test is to measure a probe string in the face and in the SAME
    // STACK FALLING BACK, and fail if the widths match — measuring against
    // bare serif or mono is what let the wall harness pass with no Archivo on
    // the page at all, because the fallback sans sits between the two.
    const probe = (stack, variation) => {
      const s = document.createElement('span');
      s.textContent = 'HAMBURGEFONSTIV 1890 WWWiii';
      s.style.cssText = `position:absolute;left:-9999px;top:0;white-space:pre;`
        + `font-size:100px;font-family:${stack};`
        + (variation ? `font-style:italic;font-weight:900;` : '');
      document.body.appendChild(s);
      const w = s.getBoundingClientRect().width;
      s.remove();
      return w;
    };
    //
    // The width probe works for Archivo, which is not installed anywhere in
    // this container. It does NOT work for JetBrains Mono, which IS installed
    // system-wide here (fc-match resolves it) — so the stack resolves to the
    // system copy with the bundle stripped and the probe passes with nothing
    // embedded. That is exactly the failure that ships an HTML artboard to a
    // print shop which does not have the face. So mono is checked the other
    // way: the embedded face must actually be in document.fonts and loaded.
    const loaded = [...document.fonts].filter(f => f.status === 'loaded')
      .map(f => f.family.replace(/['"]/g, ''));
    const fonts = {
      'archivo drawn': probe("'Archivo',serif", true) !== probe('serif', true),
      'archivo embedded': loaded.includes('Archivo'),
      'mono embedded': loaded.includes('JetBrains Mono'),
    };

    // Leaf text boxes, measured with a Range so the box is the line box of the
    // actual run rather than the element's padding box.
    const leaves = [];
    const walk = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
    for (let t = walk.nextNode(); t; t = walk.nextNode()) {
      if (!t.nodeValue.trim()) continue;
      const r = document.createRange();
      r.selectNodeContents(t);
      const b = r.getBoundingClientRect();
      if (b.width < 0.5 || b.height < 0.5) continue;
      const el = t.parentElement;
      leaves.push({
        text: t.nodeValue.trim().slice(0, 34),
        cls: el?.getAttribute('class') || el?.tagName || '?',
        svg: !!el?.closest('svg'),
        x: b.x, y: b.y, w: b.width, h: b.height,
      });
    }

    // Anything that runs out of its own container is clipped on the sheet even
    // though nothing overflows the page — the long-name case.
    const clipped = [...document.querySelectorAll('.typed,.label,.kicker,.body,.cell .num')]
      .filter(e => e.scrollWidth > e.clientWidth + 1)
      .map(e => (e.getAttribute('class') || e.tagName) + ': ' + e.textContent.trim().slice(0, 30));

    return {
      fonts,
      leaves,
      clipped,
      images: [...document.images].map(i => i.complete && i.naturalWidth > 0),
      page: { w: document.documentElement.clientWidth, h: document.documentElement.clientHeight },
      frame: mm * 7,
      place: document.querySelector('.place')?.textContent,
      label: document.querySelector('.label')?.textContent,
      name: document.querySelector('.nameplate .typed')?.textContent || '(blank name line)',
      pts: document.querySelector('.cell .num')?.textContent || '-',
      provisional: (document.querySelector('.kicker')?.textContent || '').includes('PROVISIONAL'),
    };
  }, MM);

  // A sabotaged page must never overwrite shippable artwork.
  const png = path.join(OUT, `bo-certificate-${n}${SABOTAGE ? '-sabotage' : ''}.png`);
  await pg.screenshot({ path: png, type: 'png' });
  await pg.close();

  const bad = [];
  const missing = Object.entries(checks.fonts).filter(([, ok]) => !ok).map(([k]) => k);
  if (missing.length) bad.push(`FONT NOT LOADED: ${missing.join(', ')}`);
  if (!checks.images.length || !checks.images.every(Boolean)) bad.push('an image failed to load');
  if (checks.clipped.length) bad.push('clipped: ' + checks.clipped.join(' | '));

  // Every run of type has to sit inside the printed frame. The page is
  // overflow:hidden at a fixed mm size, so scrollHeight can never exceed
  // clientHeight — a scroll check here is vacuous and would pass a sheet whose
  // body copy had run under the seal.
  const tol = 1.0 * MM;
  for (const L of checks.leaves) {
    if (L.x < checks.frame - tol || L.y < checks.frame - tol
        || L.x + L.w > checks.page.w - checks.frame + tol
        || L.y + L.h > checks.page.h - checks.frame + tol) {
      bad.push(`outside the frame: ${L.cls} "${L.text}"`);
    }
  }
  // Two runs of type on top of each other. This is the check that catches a
  // block that grew — a wrapped line never overflows anything, so width
  // assertions all stay green while it sits on the one below it. SVG arc text
  // is excluded: a textPath's box legitimately spans the whole seal.
  const flow = checks.leaves.filter(L => !L.svg);
  for (let i = 0; i < flow.length; i++) {
    for (let j = i + 1; j < flow.length; j++) {
      const a = flow[i], b = flow[j];
      const ox = Math.min(a.x + a.w, b.x + b.w) - Math.max(a.x, b.x);
      const oy = Math.min(a.y + a.h, b.y + b.h) - Math.max(a.y, b.y);
      // A Range box is a line box, not the ink, so display type with a
      // line-height under 1 nearly touches its neighbour by design.
      if (ox > 2 && oy > 0.6 * MM) {
        bad.push(`overlap: ${a.cls} "${a.text}" / ${b.cls} "${b.text}" `
          + `${ox.toFixed(0)}x${oy.toFixed(0)}px`);
      }
    }
  }
  if (errs.length) bad.push('page errors: ' + errs.join('; '));

  const { width, height } = sizeOf(png);
  const dpi = Math.round(width / (297 / 25.4));
  if (Math.abs(dpi - 300) > 2) bad.push(`${dpi} DPI, expected 300`);

  if (bad.length) failed++;
  console.log(`${path.basename(png)}  ${width}x${height}  ${dpi} DPI  `
    + `${(fs.statSync(png).size / 1024).toFixed(0)}KB  `
    + `${checks.place} / ${checks.label} / ${checks.name} / ${checks.pts}pts`
    + (checks.provisional ? ' [PROVISIONAL]' : '')
    + (bad.length ? `\n  !! ${bad.join('\n  !! ')}` : '  ok'));
}
await browser.close();
if (failed) { console.error(`\n${failed} certificate(s) failed their checks`); process.exit(1); }

function sizeOf(p) {
  const b = fs.readFileSync(p);
  return { width: b.readUInt32BE(16), height: b.readUInt32BE(20) };
}
