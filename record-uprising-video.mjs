// Records the UPRISING night-before film.
//
// Deterministic capture: the page exposes `window.__seek(t)` and has no CSS
// animations at all, so each frame is scrubbed to an exact time rather than
// grabbed off a running clock. Playwright's own video capture ran 3.2x slow on
// an earlier story and had to be rescued with setpts — this cannot drift.
//
// Playwright's bundled ffmpeg is VP8-only, so H.264 comes from the apt build at
// /usr/bin/ffmpeg. Encoding through the bundled one silently yields a .mp4 that
// Instagram rejects.
import { chromium } from 'playwright';
import { execFileSync } from 'child_process';
import fs from 'fs';
import path from 'path';

const SP = '/tmp/claude-0/-home-user-May-madness/0e44f0ad-a683-5f0d-9de6-9459ae328963/scratchpad';
// SHORT=1 records the 15-second cut, and records it SILENT. A reel that
// short is posted with a track chosen in Instagram, from a library that is
// actually licensed for it — a bed of ours underneath only gets in the way,
// and nothing in this repo can supply real music.
const SHORT = !!process.env.SHORT;
const SRC = path.join(SP, SHORT ? 'uprising-short.html' : 'uprising.html');
const FRAMES = path.join(SP, SHORT ? '_upsframes' : '_upframes');
const SILENT = path.join(SP, 'video', SHORT ? 'uprising-tonight.mp4' : 'uprising-silent.mp4');
const FINAL = path.join(SP, 'video', 'uprising-night.mp4');
const WAV = SHORT ? '/nonexistent' : path.join(SP, 'video', 'uprising.wav');
const FFMPEG = '/usr/bin/ffmpeg';
const FPS = 30, W = 1080, H = 1920;

if (!fs.existsSync(SRC)) { console.error(`no page — run: ${SHORT ? 'SHORT=1 ' : ''}python3 build-uprising-video.py`); process.exit(1); }
if (!fs.existsSync(FFMPEG)) { console.error('need the apt ffmpeg (H.264); the bundled one is VP8-only'); process.exit(1); }

fs.rmSync(FRAMES, { recursive: true, force: true });
fs.mkdirSync(FRAMES, { recursive: true });

const browser = await chromium.launch({
  executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome',
});
const pg = await browser.newPage({ viewport: { width: W, height: H }, deviceScaleFactor: 1 });
const errs = [];
pg.on('pageerror', e => errs.push(e.message));
await pg.goto('file://' + SRC, { waitUntil: 'load' });
await pg.evaluate(() => document.fonts.ready);

const pre = await pg.evaluate(() => ({
  dur: window.__dur,
  seek: typeof window.__seek === 'function',
  // A CSS animation would make the capture non-deterministic: the scrub would
  // land on whatever phase the wall clock happened to be in.
  css: document.getAnimations().length,
  display: document.fonts.check('italic 900 40px Archivo'),
  mono: document.fonts.check('700 14px "JetBrains Mono"'),
  imgs: [...document.images].map(i => i.complete && i.naturalWidth > 0),
}));
if (!pre.seek) { console.error('page exposes no __seek'); process.exit(1); }
if (pre.css) { console.error(`${pre.css} CSS animations on the page — capture would not be deterministic`); process.exit(1); }
if (!pre.display) { console.error('Archivo did not load'); process.exit(1); }
if (!pre.mono) { console.error('JetBrains Mono did not load'); process.exit(1); }
if (pre.imgs.some(ok => !ok)) { console.error(`${pre.imgs.filter(o => !o).length} image(s) failed to decode`); process.exit(1); }

// The widen() entrance is silent when the font is a static instance: it sets
// 'wdth' and nothing moves. Measure it instead of trusting it.
// Measure the inner span, not the block: the headline blocks are full-bleed
// (left:0;right:0), so the block is 1080px wide at every instant and would
// report "no widening" however well the entrance works.
// The URL in the outro is the one line that must stay on one line, so it is
// the one the shrink-to-fit pass wraps -- and the only element whose widening
// can be measured. The headlines are deliberately multi-line and full-bleed, so
// their boxes are 1080px wide at every instant and say nothing.
const widths = await pg.evaluate(() => {
  const o = window.__outro;
  if (o === undefined) return null;
  window.__seek(o + 1.70);                  // lets the fit pass build the span
  const el = document.querySelector('#s8u .fitspan');
  if (!el) return null;
  const at = t => { window.__seek(t); return el.getBoundingClientRect().width; };
  return [at(o + 1.42), at(o + 1.58), at(o + 2.20)];
});
if (!widths) { console.error('no .fitspan — the shrink-to-fit pass never ran'); process.exit(1); }
if (!(widths[2] > widths[0] * 1.08)) {
  console.error(`headline never widened (${widths.map(w => w.toFixed(0)).join(' -> ')}px) — static font instance?`);
  process.exit(1);
}

// No TEXT may run off the 1080px frame. The brand art shipped a lockup with
// the first and last letters of BLACKOUT sliced off by the edge of its own
// bitmap and every assertion passed, because they were all about the font and
// none about where the ink landed.
//
// Measured with a Range over the text itself, not with the element box: the
// headlines are deliberately full-bleed (left:0;right:0) and centred, so their
// boxes are 1080px wide at every instant — and 1123px during the entrance,
// which scales them — while the letters inside may be nowhere near the edge.
const over = await pg.evaluate(() => {
  const dur = window.__dur;
  const scenes = [...document.querySelectorAll('.scene')];
  const out = [], seen = new Set();
  const marks = [];
  for (let i = 0; i < scenes.length; i++) {
    for (const f of [0.45, 0.72, 0.95]) marks.push(((i + f) / scenes.length) * dur);
  }
  for (const t of marks) {
    window.__seek(t);
    for (const el of scenes) {
      if (el.style.display === 'none') continue;
      for (const n of el.querySelectorAll('*')) {
        if (![...n.childNodes].some(c => c.nodeType === 3 && c.textContent.trim())) continue;
        const r = document.createRange();
        r.selectNodeContents(n);
        const b = r.getBoundingClientRect();
        if (!b.width) continue;
        if (b.left < 6 || b.right > 1074) {
          const key = n.id || n.className;
          if (seen.has(key)) continue;
          seen.add(key);
          out.push(`${key}: ${Math.round(b.left)}..${Math.round(b.right)} at ${t.toFixed(1)}s`);
        }
      }
    }
  }
  return out;
});
if (over.length) {
  console.error('text runs off the frame:\n  ' + over.join('\n  '));
  process.exit(1);
}

// Nothing may be clipped by its own container either. Frame-overflow and
// container-clipping are different failures: the first cut of the earners scene
// lost the last letter of a name to the money column beside it, which is well
// inside the 1080px frame and invisible to the check above.
const clipped = await pg.evaluate(() => {
  const dur = window.__dur;
  const scenes = [...document.querySelectorAll('.scene')];
  const out = [], seen = new Set();
  for (let i = 0; i < scenes.length; i++) {
    window.__seek(((i + 0.85) / scenes.length) * dur);
    for (const el of scenes) {
      if (el.style.display === 'none') continue;
      for (const n of el.querySelectorAll('*')) {
        if (n.scrollWidth > n.clientWidth + 1 && n.clientWidth > 0) {
          const key = n.id || n.className;
          if (seen.has(key)) continue;
          seen.add(key);
          out.push(`${key} "${n.textContent.trim().slice(0, 24)}": needs ${n.scrollWidth}px, has ${n.clientWidth}px`);
        }
      }
    }
  }
  return out;
});
if (clipped.length) {
  console.error('text clipped by its container:\n  ' + clipped.join('\n  '));
  process.exit(1);
}

// Nor may two blocks in the same scene sit ON TOP of each other. The two
// checks above are both about width; this is the one that catches a headline
// that WRAPPED to a second line and landed on the line positioned beneath it.
// Everything here is absolutely positioned at a fixed `top`, so an overlap is
// always a mistake — and it is invisible to a scrollWidth test, because a
// wrapped line never overflows anything.
//
// Leaf text only, measured with a Range, and only while both blocks are
// actually up (opacity > 0.6): the entrances rise about 14px, so a few pixels
// of transient overlap during a cross-fade is motion, not a collision.
//
// The tolerance is 14px rather than 1 because a Range box is a LINE box, not
// the ink: display type at 300px carries far more leading above its caps than
// the glyphs use, so a kicker sitting comfortably clear of a huge number still
// intersects its box by about ten pixels. The failure this exists to catch —
// a headline wrapping onto the line beneath it — overlaps by ninety.
const collide = await pg.evaluate(() => {
  const dur = window.__dur;
  const scenes = [...document.querySelectorAll('.scene')];
  const out = [], seen = new Set();
  const marks = [];
  for (let i = 0; i < scenes.length; i++)
    for (const f of [0.55, 0.80, 0.97]) marks.push(((i + f) / scenes.length) * dur);
  for (const t of marks) {
    window.__seek(t);
    for (const el of scenes) {
      if (el.style.display === 'none') continue;
      const boxes = [];
      for (const n of el.querySelectorAll('*')) {
        if (![...n.childNodes].some(c => c.nodeType === 3 && c.textContent.trim())) continue;
        let o = 1, p = n;
        while (p && p !== el) { o *= parseFloat(getComputedStyle(p).opacity || 1); p = p.parentElement; }
        if (o < 0.6) continue;
        const r = document.createRange();
        r.selectNodeContents(n);
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
        if (seen.has(key)) continue;
        seen.add(key);
        out.push(`${key} overlap ${Math.round(ox)}x${Math.round(oy)}px at ${t.toFixed(1)}s`);
      }
    }
  }
  return out;
});
if (collide.length) {
  console.error('blocks overlap each other:\n  ' + collide.join('\n  '));
  process.exit(1);
}

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
  if (!SHORT) console.log('  (no audio bed yet — run python3 build-uprising-audio.py, then re-run)');
}

const mb = (fs.statSync(out).size / 1024 / 1024).toFixed(1);
console.log(`${path.basename(out)}  ${W}x${H}  ${FPS}fps  ${pre.dur}s  ${mb}MB`
  + `  headline ${widths.map(w => w.toFixed(0)).join('->')}px  ok`);
