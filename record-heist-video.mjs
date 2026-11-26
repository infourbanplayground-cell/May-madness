// Records the Muscat Heist launch film through the checks every film here
// carries. Deterministic: the page exposes window.__seek(t) and has no CSS
// animations, so each frame is scrubbed to an exact time.
//
//   python3 build-heist-video.py && python3.13 build-heist-audio.py
//   node record-heist-video.mjs          # CONTACT=1 writes a strip, no encode
//
// Checks: no CSS animations; Archivo and the mono face really DRAWN (measured
// against themselves falling back); every painting a real image and the logo
// decoded; no fitted headline at the floor; no text off the frame, clipped by
// its box (settled frames), or overlapping another block; everything inside
// Instagram's 170..1720 safe band; the pool count-up landing on its figure.
import { chromium } from 'playwright';
import { execFileSync } from 'child_process';
import fs from 'fs';
import path from 'path';

const SP = '/tmp/claude-0/-home-user-May-madness/0e44f0ad-a683-5f0d-9de6-9459ae328963/scratchpad';
const NAME = process.env.NAME || 'heist-launch';
const SRC = path.join(SP, process.env.PAGE || 'heist-launch.html');
const FRAMES = path.join(SP, '_heistframes');
const VID = path.join(SP, 'video');
const SILENT = path.join(VID, NAME + '-silent.mp4');
const FINAL = path.join(VID, NAME + '.mp4');
const WAV = path.join(VID, process.env.WAV || 'heist-launch.wav');
const SHEET = path.join(SP, 'heist-film', NAME.toUpperCase() + '.png');
const FFMPEG = '/usr/bin/ffmpeg';
const FPS = 30, W = 1080, H = 1920;
const CONTACT = !!process.env.CONTACT;

if (!fs.existsSync(SRC)) { console.error('no page — run: python3 build-heist-video.py'); process.exit(1); }
if (!fs.existsSync(FFMPEG)) { console.error('need the apt ffmpeg (H.264); the bundled one is VP8-only'); process.exit(1); }
fs.mkdirSync(VID, { recursive: true });

const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
const pg = await browser.newPage({ viewport: { width: W, height: H }, deviceScaleFactor: 1 });
const errs = [];
pg.on('pageerror', e => errs.push(e.message));
await pg.goto('file://' + SRC, { waitUntil: 'load' });
await pg.evaluate(() => document.fonts.ready);
await pg.waitForFunction(() => window.__ready === true, { timeout: 15000 });
if (errs.length) { console.error('page errors: ' + errs.join('; ')); process.exit(1); }

const pre = await pg.evaluate(() => ({
  dur: window.__dur, scenes: window.__scenes,
  seek: typeof window.__seek === 'function',
  css: document.getAnimations().length,
}));
if (!pre.seek) { console.error('page exposes no __seek'); process.exit(1); }
if (pre.css) { console.error(`${pre.css} CSS animations — capture would not be deterministic`); process.exit(1); }

const fonts = await pg.evaluate(() => {
  const probe = (stack, extra) => {
    const s = document.createElement('span');
    s.textContent = 'MUSCAT HEIST HAMBURGEFONS 412';
    s.style.cssText = 'position:absolute;visibility:hidden;white-space:nowrap;font-size:100px;font-family:' + stack + ';' + (extra || '');
    document.body.appendChild(s); const w = s.getBoundingClientRect().width; s.remove(); return w;
  };
  return {
    archivo: probe("'Archivo',serif", 'font-weight:800;font-stretch:112%') !== probe('serif', 'font-weight:800;font-stretch:112%'),
    // JetBrains Mono is installed system-wide here, so "drawn" cannot prove it
    // was embedded; require the bundled face to be in document.fonts, loaded.
    mono: [...document.fonts].some(f => /JetBrains/.test(f.family) && f.status === 'loaded'),
  };
});
const missing = Object.entries(fonts).filter(([, ok]) => !ok).map(([k]) => k);
if (missing.length) { console.error('FONT NOT DRAWN: ' + missing.join(', ')); process.exit(1); }

// THE PICTURES, BY NAME. A painting that failed to decode is a navy rectangle,
// which under a scrim looks exactly like a mood.
const art = await pg.evaluate(async () => {
  const bad = [];
  for (const p of document.querySelectorAll('.plate')) {
    const m = /url\("?(data:image\/[^")]+)/.exec(getComputedStyle(p).backgroundImage);
    if (!m) { bad.push(p.id + ' has no image'); continue; }
    const im = new Image(); im.src = m[1];
    try { await im.decode(); if (im.naturalWidth < 800) bad.push(p.id + ' only ' + im.naturalWidth + 'px'); } catch (e) { bad.push(p.id + ' does not decode'); }
  }
  for (const im of document.querySelectorAll('img.logo')) if (!im.complete || !im.naturalWidth) bad.push('logo not decoded');
  return bad;
});
if (art.length) { console.error('ART NOT DRAWN: ' + art.join(', ')); process.exit(1); }

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

// 5 · THE POOL MUST REACH ITS DERIVED TOTAL. It counts up, so a fit or an
// easing change could leave it resting one short — and a prize pool that is
// 411 in the film and 412 everywhere else is the exact class of drift every
// figure here is read from the config to prevent.
const pool = await pg.evaluate((scenes) => {
  const el = document.getElementById('s4n');
  if (!el) return 'n/a';
  // the END of #s4n's own scene, not a fixed index: a film may add scenes after it
  const k = [...document.querySelectorAll('.scene')].indexOf(el.closest('.scene'));
  const t1 = k + 1 < scenes.length ? scenes[k + 1] : window.__dur;
  window.__seek(t1 - 0.05);
  return el ? el.textContent.trim() : 'n/a';
}, pre.scenes);
// EVERY COUNT-UP MUST LAND ON ITS FIGURE before its scene cuts: the recap's
// +60 and the table's totals count up exactly as the pool does, and the same
// one-short drift would put a total on screen the app does not show.
const short = await pg.evaluate((scenes) => {
  const out = [];
  for (const el of document.querySelectorAll('[data-pts], [data-n]')) {
    const sc = el.closest('.scene'); if (!sc) continue;
    const k = [...document.querySelectorAll('.scene')].indexOf(sc);
    const end = k + 1 < scenes.length ? scenes[k + 1] : window.__dur;
    window.__seek(end - 0.20);
    const want = el.dataset.pts || el.dataset.n, got = el.textContent.replace(/[^0-9]/g, '');
    if (got !== want) out.push(`${el.id || el.className} shows ${got}, the figure is ${want}`);
  }
  return out;
}, pre.scenes);
if (short.length) { console.error('count-up short:\n  ' + short.join('\n  ')); process.exit(1); }

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
  console.log(`  pool reaches ${pool}  ·  fonts ok  ·  art ok  ·  no collisions`);
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
  console.log('  (no bed yet — run python3.13 build-heist-audio.py, then re-run)');
}

const mb = (fs.statSync(out).size / 1024 / 1024).toFixed(1);
console.log(`${path.basename(out)}  ${W}x${H}  ${FPS}fps  ${pre.dur}s  ${mb}MB`);
console.log(`  pool reaches ${pool}  ·  fonts ok  ·  art ok  ·  no collisions`);
