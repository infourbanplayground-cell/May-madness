// Render the Vol.9 announcement cards, and prove they are what they claim.
//
// Every check here is a failure this repo has actually shipped:
//
//   · THE FACE WAS REALLY DRAWN, measured against the same stack falling
//     back. getComputedStyle reports the family in the stylesheet whether or
//     not it loaded and document.fonts.check() answers true with zero faces
//     loaded — the whole UPRISING story series once rendered in Times with
//     every assertion green.
//   · NOTHING RUNS PAST THE CARD'S OWN PADDING. The padding IS the design: an
//     UPRISING footer ran 59px past its 64px padding and stopped 5px short of
//     the crop, so every assertion that watched the bitmap edge was green.
//   · NO INK IS CLIPPED inside its own box. An element can sit inside the
//     canvas while the text in it runs out the side.
//   · NO TWO TEXT RUNS OVERLAP, per LINE BOX and only across BLOCKS.
//     getBoundingClientRect on a wrapped run spans the paragraph and overlaps
//     every sibling in it, and inline runs in one paragraph share line boxes
//     by definition.
//   · THE ARTWORK LOADED. The tile, the band and the landmarks are all
//     background-images carrying base64; a missing one is a flat rectangle in
//     the right colour and nothing complains.
//
//   node render-national-post.mjs
//   SABOTAGE=nofont   drop the embedded faces
//   SABOTAGE=noart    blank the artwork
//   SABOTAGE=long     a landmark name long enough to break the night rows
//   SABOTAGE=squeeze  shorten the arches, so they cut their own content
//   ONLY=hero         narrow the run
import { chromium } from 'playwright';
import fs from 'fs';
import path from 'path';

const DIR = path.resolve('brand/national/posts');
const SABOTAGE = process.env.SABOTAGE || '';
const ONLY = process.env.ONLY || '';

const SIZES = { 'post-story': [1080, 1920] };   // everything else is 1080x1350

const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
let failed = 0, done = 0;

for (const f of fs.readdirSync(DIR).filter(x => x.endsWith('.html')).sort()) {
  const name = f.replace(/\.html$/, '');
  if (ONLY && !name.includes(ONLY)) continue;
  const [w, h] = SIZES[name] || [1080, 1350];

  let html = fs.readFileSync(path.join(DIR, f), 'utf8');
  if (SABOTAGE === 'nofont') {
    const n = html.length;
    html = html.replace(/url\(data:font\/woff2;base64,[^)]*\)/g, 'url(about:invalid)');
    if (html.length === n) throw new Error('sabotage anchor (nofont) no longer matches');
  }
  if (SABOTAGE === 'squeeze') {
    // Take height away from the arches, which is the fault the clipped check
    // exists for: a door too short for what is standing in it swallows the
    // bottom of its own content, and NOTHING runs past any edge — there is no
    // overflow to see, because overflow:hidden is what the arch does instead.
    const n = html.length;
    html = html.replace('</style>',
      '.arch,.archframe{max-height:360px !important}</style>');
    if (html.length === n) throw new Error('sabotage anchor (squeeze) no longer matches');
  }
  if (SABOTAGE === 'noart') {
    const n = (html.match(/data:image\//g) || []).length;
    // Two on every card (the tile and the band); more where there are
    // medallions. The threshold was three, which threw on the two cards
    // that legitimately carry no landmark.
    if (n < 2) throw new Error('sabotage anchor (noart) no longer matches');
    // The URLs are fully percent-encoded and therefore UNQUOTED, which the
    // first version of this sabotage did not match — it threw rather than
    // going red, which at least fails loudly.
    html = html.replace(/url\(["']?data:image\/[^)]*\)/g, 'none');
  }
  if (SABOTAGE === 'long') {
    // SQUEEZE THE CELL, do not lengthen the text. A longer landmark name
    // proved nothing: at 41 characters it still needed 517px of the 780 the
    // row actually has, so the run went green for the honest reason that the
    // design has room. Narrowing the cell with the wrap off is the real
    // risk — a name clipped to an ellipsis in a row nobody re-reads — and it
    // is what the clipped check exists for.
    const a = '<div style="flex:1;min-width:0">';
    if (html.includes(a))
      html = html.replace(new RegExp(a.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'g'),
                          '<div style="flex:1;min-width:0;max-width:150px">');
    else if (name === 'post-2-nights')
      throw new Error('sabotage anchor (long) no longer matches');
  }

  const pg = await browser.newPage({ viewport: { width: w, height: h }, deviceScaleFactor: 1 });
  const errs = [];
  pg.on('pageerror', e => errs.push(e.message));
  await pg.setContent(html, { waitUntil: 'load' });
  await pg.evaluate(() => document.fonts.ready);
  await pg.waitForTimeout(120);

  const r = await pg.evaluate(({ w, h }) => {
    const probe = (stack, cls) => {
      const s = document.createElement('span');
      s.textContent = 'NATIONAL 56 HAMBURGEFONS';
      s.style.cssText = 'position:absolute;visibility:hidden;white-space:nowrap;'
        + `font-size:100px;font-family:${stack};`
        + (cls === 'disp' ? 'font-style:italic;font-weight:900;' : '');
      document.body.appendChild(s);
      const x = s.getBoundingClientRect().width; s.remove(); return x;
    };

    // THE PADDING BOX IS THE FRAME, not the bitmap. A card has a declared
    // padding and that padding is the design.
    const pad = document.querySelector('.pad');
    const cs = getComputedStyle(pad);
    const pb = pad.getBoundingClientRect();
    const frame = {
      l: pb.left + parseFloat(cs.paddingLeft),
      r: pb.right - parseFloat(cs.paddingRight),
      t: pb.top + parseFloat(cs.paddingTop),
      b: pb.bottom - parseFloat(cs.paddingBottom),
    };

    const vis = [...document.querySelectorAll('.pad *')].filter(e => {
      const s = getComputedStyle(e);
      if (s.display === 'none' || s.visibility === 'hidden' || +s.opacity === 0) return false;
      const b = e.getBoundingClientRect();
      return b.width > 0 && b.height > 0;
    });

    const past = [], clipped = [];
    for (const e of vis) {
      const b = e.getBoundingClientRect();
      // A shadow-ringed arch sits proud of its own box by design, so the
      // tolerance is the ring, not zero.
      if (b.right > frame.r + 12 || b.left < frame.l - 12
          || b.bottom > frame.b + 12 || b.top < frame.t - 12)
        past.push(`${(e.className || e.tagName).toString().slice(0, 26)} `
          + `${Math.round(b.left)},${Math.round(b.top)}→${Math.round(b.right)},${Math.round(b.bottom)}`);
      if (e.childElementCount === 0 && (e.textContent || '').trim()
          && e.scrollWidth > e.clientWidth + 1)
        clipped.push(`"${e.textContent.trim().slice(0, 28)}" `
          + `needs ${e.scrollWidth} in ${e.clientWidth}`);
    }

    const blockOf = (el) => {
      for (let e = el; e; e = e.parentElement)
        if (!/^(inline|contents)$/.test(getComputedStyle(e).display)) return e;
      return null;
    };
    const runs = [];
    for (const e of vis) {
      if (e.childElementCount) continue;
      if (!(e.textContent || '').trim()) continue;
      // A GHOST IS MEANT TO BE UNDER THE COPY. The volume numeral behind the
      // arch is a 360px tint at 26% whose entire job is to sit behind the
      // words — so it collides with every one of them, correctly, and that is
      // not a layout fault. It carries aria-hidden and data-ghost; the skin
      // harness excludes the app's own watermark the same way.
      if (e.closest('[data-ghost]')) continue;
      const rg = document.createRange(); rg.selectNodeContents(e);
      for (const q of rg.getClientRects())
        if (q.width > 1 && q.height > 1) runs.push({ e, q, b: blockOf(e) });
    }
    // A CONTAINER WITH overflow:hidden SWALLOWS ITS OWN CONTENT SILENTLY.
    // The clipped check above is horizontal (scrollWidth) and the padding
    // check is about boxes running past the FRAME — so an arch too short for
    // what is inside it fails neither, and the hero shipped with the bottom
    // of its own plate sliced off.
    //
    // MEASURED AS TEXT, NOT AS scrollHeight. scrollHeight counts absolutely
    // positioned decoration: the 360px volume ghost inside the arch put it 5px
    // over on a card whose copy stopped 44px clear of the bottom, every time,
    // whatever was removed. What matters is whether a WORD is being cut, so
    // the test is whether a leaf text run's own box falls outside the
    // clipping box.
    for (const e of vis) {
      const cs = getComputedStyle(e);
      if (!/hidden|clip/.test(cs.overflowY)) continue;
      const box = e.getBoundingClientRect();
      if (box.height < 4) continue;
      for (const n of e.querySelectorAll('*')) {
        if (n.childElementCount) continue;
        if (!(n.textContent || '').trim()) continue;
        if (n.closest('[data-ghost]')) continue;
        const rg = document.createRange(); rg.selectNodeContents(n);
        const q = rg.getBoundingClientRect();
        if (!q.height) continue;
        if (q.bottom > box.bottom - 2 || q.top < box.top - 2) {
          clipped.push(`<${e.className || e.tagName}> cuts `
            + `"${n.textContent.trim().slice(0, 22)}" `
            + `(${Math.round(q.top - box.top)}..${Math.round(q.bottom - box.top)} `
            + `in ${Math.round(box.height)})`);
          break;
        }
      }
    }

    const overlap = [];
    for (let i = 0; i < runs.length; i++) for (let j = i + 1; j < runs.length; j++) {
      const a = runs[i], c = runs[j];
      if (a.b === c.b) continue;
      if (a.b && c.b && (a.b.contains(c.b) || c.b.contains(a.b))) continue;
      const ow = Math.min(a.q.right, c.q.right) - Math.max(a.q.left, c.q.left);
      const oh = Math.min(a.q.bottom, c.q.bottom) - Math.max(a.q.top, c.q.top);
      if (ow > 6 && oh > 6) overlap.push(
        `"${a.e.textContent.trim().slice(0, 18)}" over "${c.e.textContent.trim().slice(0, 18)}"`);
    }

    // `url("")` starts with url( and draws nothing, so the test is for a real
    // image rather than for the syntax of one.
    const drawn = (el) => /url\(["']?data:image\//.test(getComputedStyle(el).backgroundImage);
    const meds = [...document.querySelectorAll('.med')];

    return {
      past, clipped, overlap: [...new Set(overlap)],
      archivo: probe("'Archivo',serif", 'disp') !== probe('serif', 'disp'),
      kufi: [...document.fonts].some(x => /Kufi/.test(x.family) && x.status === 'loaded'),
      tile: drawn(document.querySelector('.tile')),
      band: drawn(document.querySelector('.band')),
      meds: meds.filter(drawn).length, medTotal: meds.length,
      text: (pad.innerText || '').replace(/\s+/g, ' ').trim(),
    };
  }, { w, h });

  const png = path.join(DIR, name + '.png');
  await pg.screenshot({ path: png });
  await pg.close();
  done++;

  const bad = [];
  if (!r.archivo) bad.push('Archivo was NOT drawn — it fell back');
  if (!r.tile) bad.push('the khanjar tile is not drawn');
  if (!r.band) bad.push('the masar band is not drawn');
  if (r.medTotal !== r.meds)
    bad.push(`${r.medTotal - r.meds} landmark medallion(s) carry no artwork`);
  // Arabic is only on two of the cards, so it is asserted where it appears.
  if (/[؀-ۿ]/.test(r.text) && !r.kufi)
    bad.push('Arabic is set but Noto Kufi did not load — it fell back');
  for (const p of r.past.slice(0, 4)) bad.push('past the padding: ' + p);
  for (const c of r.clipped.slice(0, 4)) bad.push('clipped: ' + c);
  for (const o of r.overlap.slice(0, 4)) bad.push('overlap: ' + o);
  // Vol.8's name must never appear on Vol.9's art.
  if (/blackout|lights out/i.test(r.text)) bad.push('the card still says BLACKOUT');
  if (errs.length) bad.push(errs.join('; '));

  if (bad.length) failed++;
  console.log(`${name}.png  ${w}x${h}  ${(fs.statSync(png).size / 1024).toFixed(0)}KB  `
    + `med ${r.meds}/${r.medTotal}`
    + (bad.length ? `\n  !! ${bad.join('\n  !! ')}` : '  ok'));
}

await browser.close();
if (!done) { console.error('no cards rendered — run build-national-post.py first'); process.exit(1); }
if (failed) { console.error(`\n${failed} card(s) failed their checks`); process.exit(1); }
console.log(`\nok — ${done} cards`);
