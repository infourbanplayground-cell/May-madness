// Records the Vol.9 season-opening film.
//
// Deterministic capture: the page exposes `window.__seek(t)` and has no CSS
// animations at all, so each frame is scrubbed to an exact time rather than
// grabbed off a running clock. Playwright's own video capture ran 3.2x slow on
// an earlier story and had to be rescued with setpts — this cannot drift.
//
// Playwright's bundled ffmpeg is VP8-only, so H.264 comes from the apt build
// at /usr/bin/ffmpeg. Encoding through the bundled one silently yields a .mp4
// that Instagram rejects.
//
//   python3 build-national-video.py
//   python3.13 build-national-audio.py
//   node record-national-video.mjs
//
// CONTACT=1 writes a strip of one frame per scene instead of encoding, which
// is the only way to actually look at the thing.
import { chromium } from 'playwright';
import { execFileSync } from 'child_process';
import fs from 'fs';
import path from 'path';

const SP = '/tmp/claude-0/-home-user-May-madness/0e44f0ad-a683-5f0d-9de6-9459ae328963/scratchpad';
const SRC = path.join(SP, 'national.html');
const FRAMES = path.join(SP, '_nationalframes');
const VID = path.join(SP, 'video');
const SILENT = path.join(VID, 'national-opening-silent.mp4');
const FINAL = path.join(VID, 'national-opening.mp4');
const WAV = path.join(VID, 'national.wav');
const SHEET = path.join(SP, 'vol9-cards', 'OPENING-FILM.png');
const FFMPEG = '/usr/bin/ffmpeg';
const FPS = 30, W = 1080, H = 1920;
const CONTACT = !!process.env.CONTACT;

if (!fs.existsSync(SRC)) { console.error('no page — run: python3 build-national-video.py'); process.exit(1); }
if (!fs.existsSync(FFMPEG)) { console.error('need the apt ffmpeg (H.264); the bundled one is VP8-only'); process.exit(1); }
fs.mkdirSync(VID, { recursive: true });

const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
const pg = await browser.newPage({ viewport: { width: W, height: H }, deviceScaleFactor: 1 });
const errs = [];
pg.on('pageerror', e => errs.push(e.message));
await pg.goto('file://' + SRC, { waitUntil: 'load' });
await pg.evaluate(() => document.fonts.ready);
await pg.waitForFunction(() => window.__ready === true, { timeout: 15000 });

const pre = await pg.evaluate(() => ({
  dur: window.__dur,
  scenes: window.__scenes,
  seek: typeof window.__seek === 'function',
  // A CSS animation would make the capture non-deterministic: the scrub would
  // land on whatever phase the wall clock happened to be in.
  css: document.getAnimations().length,
  display: document.fonts.check('italic 900 40px Archivo'),
  mono: document.fonts.check('700 14px "JetBrains Mono"'),
  kufi: document.fonts.check('700 20px "Noto Kufi Arabic"'),
}));
if (!pre.seek) { console.error('page exposes no __seek'); process.exit(1); }
if (pre.css) { console.error(`${pre.css} CSS animations — capture would not be deterministic`); process.exit(1); }

// THE FACES, MEASURED RATHER THAN ASKED FOR. getComputedStyle reports the
// family in the stylesheet whether or not it loaded, and document.fonts.check
// answers true with zero faces loaded — so the only honest test is to measure
// a probe in the face and in one it cannot be, and fail if they match.
//
// Archivo is measured against ITSELF FALLING BACK ('Archivo',serif vs serif):
// with the webfont gone the stack resolves to the body's sans-serif, which is
// wider than serif and narrower than mono, so comparing against mono passes
// with no Archivo on the page at all.
//
// The Arabic probe must be an ARABIC string. Noto Kufi carries no Latin, so a
// Latin probe measures the fallback either way and reports a failure when
// nothing is wrong — the mirror of the bug the UPRISING winner renderer had
// when it probed a style the page never drew.
const fonts = await pg.evaluate(() => {
  const probe = (stack, text, extra) => {
    const s = document.createElement('span');
    s.textContent = text;
    s.style.cssText = 'position:absolute;visibility:hidden;white-space:nowrap;'
      + 'font-size:100px;font-family:' + stack + ';' + (extra || '');
    document.body.appendChild(s);
    const w = s.getBoundingClientRect().width; s.remove(); return w;
  };
  const LAT = 'NATIONAL HAMBURGEFONS 56';
  const AR = 'السلسلة الوطنية';
  return {
    archivo: probe("'Archivo',serif", LAT, "font-style:italic;font-weight:900")
           !== probe('serif', LAT, "font-style:italic;font-weight:900"),
    mono: probe("'JetBrains Mono',serif", LAT, 'font-weight:700')
        !== probe('serif', LAT, 'font-weight:700'),
    kufi: probe("'Noto Kufi Arabic',serif", AR, 'font-weight:700')
        !== probe('serif', AR, 'font-weight:700'),
  };
});
const missing = Object.entries(fonts).filter(([, ok]) => !ok).map(([k]) => k);
if (missing.length) { console.error('FONT NOT DRAWN: ' + missing.join(', ')); process.exit(1); }

// THE MOTIFS, BY NAME. They are all background-images, and a missing one is a
// flat rectangle in the right colour — which is exactly what the first Vol.9
// re-skin shipped while every other check passed.
const motifs = await pg.evaluate(() => {
  const real = el => el && /url\("?data:image\/[a-z+]+[;,]/.test(getComputedStyle(el).backgroundImage);
  return {
    khanjar: real(document.getElementById('tile')),
    masar: [...document.querySelectorAll('.band')].every(real),
    medallion: real(document.getElementById('s3med')),
    flag: !!document.querySelector('.flag'),
  };
});
const noart = Object.entries(motifs).filter(([, ok]) => !ok).map(([k]) => k);
if (noart.length) { console.error('MOTIF NOT DRAWN: ' + noart.join(', ')); process.exit(1); }

// The entrance WIDENS the display face. On a static font instance setting
// 'wdth' moves nothing, and the whole entrance is then a plain fade with no
// error anywhere — so measure the span, not the block. The blocks are
// full-bleed (left:0;right:0), so their boxes are 1080px wide at every
// instant and would report "no widening" however well it works.
const widths = await pg.evaluate(() => {
  const el = document.querySelector('#s5b .fitspan');
  if (!el) return null;
  const t0 = window.__scenes[4];
  const at = t => { window.__seek(t); return el.getBoundingClientRect().width; };
  return [at(t0 + 0.06), at(t0 + 0.20), at(t0 + 0.80)];
});
if (!widths) { console.error('no .fitspan in the outro — the fit pass never ran'); process.exit(1); }

// NO FITTED HEADLINE MAY HAVE RUN TO THE FLOOR. The shrink loop measures a
// box, and a box that is display:none measures 0 — so when fitAll() ran after
// __seek(0) had already hidden scenes 2-5, every headline in them shrank to
// 10px and simply was not in the film. Nothing else here could see it: no
// text had overflowed, nothing was clipped, nothing collided. A display line
// that ends up smaller than the body copy around it is the failure.
const tiny = await pg.evaluate(() => {
  const out = [];
  for (const s of document.querySelectorAll('.fitspan')) {
    const px = parseFloat(getComputedStyle(s.parentElement).fontSize);
    if (px < 40) out.push(`${s.parentElement.id}: ${px.toFixed(0)}px "${s.textContent.trim().slice(0, 20)}"`);
  }
  return out;
});
if (tiny.length) { console.error('headline shrank to nothing:\n  ' + tiny.join('\n  ')); process.exit(1); }
if (!(widths[2] > widths[0] * 1.08)) {
  console.error(`display type never widened (${widths.map(w => w.toFixed(0)).join(' -> ')}px) — static instance?`);
  process.exit(1);
}

// Sample times: several points inside every scene, so a block that only
// collides mid-entrance is still seen.
const marks = [];
for (let i = 0; i < pre.scenes.length; i++) {
  const t0 = pre.scenes[i];
  const t1 = (i + 1 < pre.scenes.length) ? pre.scenes[i + 1] : pre.dur;
  for (const f of [0.30, 0.55, 0.80, 0.97]) marks.push(t0 + (t1 - t0) * f);
}

// 1 · NO TEXT MAY RUN OFF THE 1080px FRAME. Measured with a Range over the
// text itself, not the element box: the headline blocks are deliberately
// full-bleed and centred, so their boxes are 1080px wide at every instant
// while the letters inside may be nowhere near the edge.
const over = await pg.evaluate((marks) => {
  const out = [], seen = new Set();
  for (const t of marks) {
    window.__seek(t);
    for (const el of document.querySelectorAll('.scene')) {
      if (el.style.display === 'none') continue;
      for (const n of el.querySelectorAll('*')) {
        if (![...n.childNodes].some(c => c.nodeType === 3 && c.textContent.trim())) continue;
        const r = document.createRange(); r.selectNodeContents(n);
        const b = r.getBoundingClientRect();
        if (!b.width) continue;
        if (b.left < 6 || b.right > 1074) {
          const key = n.id || n.className;
          if (seen.has(key)) continue; seen.add(key);
          out.push(`${key}: ${Math.round(b.left)}..${Math.round(b.right)} at ${t.toFixed(1)}s`);
        }
      }
    }
  }
  return out;
}, marks);
if (over.length) { console.error('text runs off the frame:\n  ' + over.join('\n  ')); process.exit(1); }

// 2 · NOR MAY ANYTHING BE CLIPPED BY ITS OWN CONTAINER. Frame-overflow and
// container-clipping are different failures: a name losing its last letter to
// the column beside it is well inside the frame and invisible to the check
// above. An ellipsis is the same fault wearing a nicer hat — clipping is what
// text-overflow does INSTEAD of overflowing, so nothing runs past any edge.
//
// SETTLED FRAMES ONLY. scrollWidth counts a child's TRANSFORM, and the money
// rows slide in from translateX(44px) — so mid-entrance the column honestly
// reports 932px of content in an 888px box, every scene, for ever. That is
// motion, not a layout fault. The other two checks take the whole mark list:
// they measure Range boxes and gate on opacity, so they read motion correctly.
const settled = marks.filter((_, k) => k % 4 >= 2);
const clipped = await pg.evaluate((marks) => {
  const out = [], seen = new Set();
  for (const t of marks) {
    window.__seek(t);
    for (const el of document.querySelectorAll('.scene')) {
      if (el.style.display === 'none') continue;
      for (const n of el.querySelectorAll('*')) {
        if (n.scrollWidth > n.clientWidth + 1 && n.clientWidth > 0) {
          const key = n.id || n.className;
          if (seen.has(key)) continue; seen.add(key);
          out.push(`${key} "${n.textContent.trim().slice(0, 24)}": needs ${n.scrollWidth}px, has ${n.clientWidth}px`);
        }
      }
    }
  }
  return out;
}, settled);
if (clipped.length) { console.error('text clipped by its container:\n  ' + clipped.join('\n  ')); process.exit(1); }

// 3 · NOR MAY TWO BLOCKS IN A SCENE SIT ON TOP OF EACH OTHER. The two checks
// above are both about WIDTH; this is the one that catches a headline that
// WRAPPED onto the line positioned beneath it — invisible to a scrollWidth
// test, because a wrapped line never overflows anything.
//
// Leaf text only, by Range, and only while both are actually up (opacity >
// 0.6): the entrances rise ~34px, so transient overlap during a cross-fade is
// motion, not a collision. Tolerance 14px because a Range box is a LINE box,
// not the ink — display type at 150px carries far more leading above its caps
// than the glyphs use. The failure this exists to catch overlaps by ninety.
const collide = await pg.evaluate((marks) => {
  const out = [], seen = new Set();
  for (const t of marks) {
    window.__seek(t);
    for (const el of document.querySelectorAll('.scene')) {
      if (el.style.display === 'none') continue;
      const boxes = [];
      for (const n of el.querySelectorAll('*')) {
        if (![...n.childNodes].some(c => c.nodeType === 3 && c.textContent.trim())) continue;
        let o = 1, p = n;
        while (p && p !== el) { o *= parseFloat(getComputedStyle(p).opacity || 1); p = p.parentElement; }
        if (o < 0.6) continue;
        const r = document.createRange(); r.selectNodeContents(n);
        const b = r.getBoundingClientRect();
        if (b.width > 0 && b.height > 0) boxes.push([n, b]);
      }
      for (let i = 0; i < boxes.length; i++) for (let j = i + 1; j < boxes.length; j++) {
        const [a, A] = boxes[i], [b, B] = boxes[j];
        if (a.contains(b) || b.contains(a)) continue;
        const ox = Math.min(A.right, B.right) - Math.max(A.left, B.left);
        const oy = Math.min(A.bottom, B.bottom) - Math.max(A.top, B.top);
        if (ox <= 14 || oy <= 14) continue;
        const key = (a.id || a.className) + '|' + (b.id || b.className);
        if (seen.has(key)) continue; seen.add(key);
        out.push(`${key} overlap ${Math.round(ox)}x${Math.round(oy)}px at ${t.toFixed(1)}s`);
      }
    }
  }
  return out;
}, marks);
if (collide.length) { console.error('blocks overlap each other:\n  ' + collide.join('\n  ')); process.exit(1); }

// 3b · AND IT ALL HAS TO SIT IN THE STORY SAFE AREA. Instagram draws its own
// chrome over roughly the top 170px and the reply bar over the bottom 200px,
// so copy outside 170..1720 is copy somebody will not read — the exact fault
// that put the Vol.8 standings story's address and club line under the reply
// bar. This also catches the other way round: every scene first came out
// top-heavy, with the content centred around y=800 and 600px of dead ground
// beneath it, which no check about overflow or collision can see.
const safe = await pg.evaluate((marks) => {
  const out = [], seen = new Set(), band = [];
  for (const t of marks) {
    window.__seek(t);
    for (const el of document.querySelectorAll('.scene')) {
      if (el.style.display === 'none') continue;
      let lo = 1e9, hi = -1e9;
      for (const n of el.querySelectorAll('*')) {
        if (![...n.childNodes].some(c => c.nodeType === 3 && c.textContent.trim())) continue;
        let o = 1, p = n;
        while (p && p !== el) { o *= parseFloat(getComputedStyle(p).opacity || 1); p = p.parentElement; }
        if (o < 0.6) continue;
        const r = document.createRange(); r.selectNodeContents(n);
        const b = r.getBoundingClientRect();
        if (!b.height) continue;
        lo = Math.min(lo, b.top); hi = Math.max(hi, b.bottom);
        if (b.top < 170 || b.bottom > 1720) {
          const key = el.id + '/' + (n.id || n.className);
          if (seen.has(key)) continue; seen.add(key);
          out.push(`${key} at ${Math.round(b.top)}..${Math.round(b.bottom)} — outside the 170..1720 safe area`);
        }
      }
      if (hi > lo) band.push([el.id, lo, hi]);
    }
  }
  return { out, band };
}, marks);
if (safe.out.length) { console.error('outside the story safe area:\n  ' + safe.out.join('\n  ')); process.exit(1); }

// 4 · NOTHING MAY SIT UNDER THE MASAR TRIM. The trim is a decorative box, not
// a text run and not in flow, so all three checks above are blind to it —
// which is exactly how the weave came to lie across the app header's Arabic
// line. Measured against the trim's own box.
const underband = await pg.evaluate((marks) => {
  const out = [], seen = new Set();
  const bands = [...document.querySelectorAll('.band')].map(b => b.getBoundingClientRect());
  for (const t of marks) {
    window.__seek(t);
    for (const el of document.querySelectorAll('.scene')) {
      if (el.style.display === 'none') continue;
      for (const n of el.querySelectorAll('*')) {
        if (![...n.childNodes].some(c => c.nodeType === 3 && c.textContent.trim())) continue;
        let o = 1, p = n;
        while (p && p !== el) { o *= parseFloat(getComputedStyle(p).opacity || 1); p = p.parentElement; }
        if (o < 0.6) continue;
        const r = document.createRange(); r.selectNodeContents(n);
        const b = r.getBoundingClientRect();
        if (!b.height) continue;
        for (const bd of bands) {
          const oy = Math.min(b.bottom, bd.bottom) - Math.max(b.top, bd.top);
          const ox = Math.min(b.right, bd.right) - Math.max(b.left, bd.left);
          if (oy > 4 && ox > 4) {
            const key = n.id || n.className;
            if (seen.has(key)) continue; seen.add(key);
            out.push(`${key} under the masar trim by ${Math.round(oy)}px at ${t.toFixed(1)}s`);
          }
        }
      }
    }
  }
  return out;
}, marks);
if (underband.length) { console.error('copy under the trim:\n  ' + underband.join('\n  ')); process.exit(1); }

// 5 · THE POOL MUST REACH ITS DERIVED TOTAL. It counts up, so a fit or an
// easing change could leave it resting one short — and a prize pool that is
// 411 in the film and 412 everywhere else is the exact class of drift every
// figure here is read from the config to prevent.
const pool = await pg.evaluate((scenes) => {
  const t1 = scenes[4];
  window.__seek(t1 - 0.05);
  return document.getElementById('s4n').textContent.trim();
}, pre.scenes);

if (CONTACT) {
  // A strip of one frame per scene. Everything above is structure; a film is
  // judged by looking at it.
  const shots = [];
  for (let i = 0; i < pre.scenes.length; i++) {
    const t0 = pre.scenes[i];
    const t1 = (i + 1 < pre.scenes.length) ? pre.scenes[i + 1] : pre.dur;
    await pg.evaluate(t => window.__seek(t), t0 + (t1 - t0) * 0.88);
    shots.push((await pg.screenshot()).toString('base64'));
  }
  const sheet = `<!doctype html><meta charset="utf-8">
  <body style="margin:0;background:#141414;padding:28px;display:flex;gap:16px;
               font-family:system-ui">
  ${shots.map((s, i) => `<div>
    <div style="color:#F2B8BC;font:700 12px monospace;margin-bottom:7px;
                letter-spacing:.12em">${(i + 1)} · ${pre.scenes[i].toFixed(2)}s</div>
    <img src="data:image/png;base64,${s}" style="width:250px;display:block;border-radius:8px">
  </div>`).join('')}</body>`;
  const sp = await browser.newPage({ viewport: { width: 1420, height: 520 } });
  await sp.setContent(sheet, { waitUntil: 'load' });
  fs.mkdirSync(path.dirname(SHEET), { recursive: true });
  await sp.screenshot({ path: SHEET, fullPage: true });
  await sp.close();
  await browser.close();
  console.log(`contact sheet  ${SHEET}`);
  console.log(`  pool reaches ${pool}  ·  fonts ok  ·  motifs ok  ·  no collisions`);
  // Where each scene's copy actually sits, so "top-heavy" is a number rather
  // than an impression. The safe band is 170..1720, so its middle is 945.
  const mid = {};
  for (const [id, lo, hi] of safe.band) mid[id] = [(lo + hi) / 2, lo, hi];
  for (const id of Object.keys(mid))
    console.log(`  ${id}  ${Math.round(mid[id][1])}..${Math.round(mid[id][2])}  centre ${Math.round(mid[id][0])} (safe centre 945)`);
  process.exit(0);
}

fs.rmSync(FRAMES, { recursive: true, force: true });
fs.mkdirSync(FRAMES, { recursive: true });
const N = Math.round(pre.dur * FPS);
for (let f = 0; f < N; f++) {
  await pg.evaluate(t => window.__seek(t), f / FPS);
  await pg.screenshot({ path: path.join(FRAMES, `f${String(f).padStart(5, '0')}.png`) });
  if (f % 60 === 0) process.stdout.write(`\r  frame ${f}/${N}`);
}
process.stdout.write(`\r  frame ${N}/${N}\n`);
if (errs.length) console.error('  !! page errors: ' + errs.join('; '));
await browser.close();

// yuv420p + even dimensions, or Instagram and QuickTime both refuse it
execFileSync(FFMPEG, ['-y', '-framerate', String(FPS), '-i', path.join(FRAMES, 'f%05d.png'),
  '-c:v', 'libx264', '-preset', 'slow', '-crf', '18', '-pix_fmt', 'yuv420p',
  '-movflags', '+faststart', SILENT], { stdio: ['ignore', 'ignore', 'inherit'] });

let out = SILENT;
if (fs.existsSync(WAV)) {
  execFileSync(FFMPEG, ['-y', '-i', SILENT, '-i', WAV,
    '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-shortest',
    '-movflags', '+faststart', FINAL], { stdio: ['ignore', 'ignore', 'inherit'] });
  out = FINAL;
} else {
  console.log('  (no bed yet — run python3.13 build-national-audio.py, then re-run)');
}

const mb = (fs.statSync(out).size / 1024 / 1024).toFixed(1);
console.log(`${path.basename(out)}  ${W}x${H}  ${FPS}fps  ${pre.dur}s  ${mb}MB`);
console.log(`  pool reaches ${pool}  ·  display ${widths.map(w => w.toFixed(0)).join('->')}px`
  + `  ·  fonts ok  ·  motifs ok`);
