// Records the Vol.7 winner video.
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
const SRC = path.join(SP, 'winner.html');
const FRAMES = path.join(SP, '_winframes');
const SILENT = path.join(SP, 'video', 'surge-winner-silent.mp4');
const FINAL = path.join(SP, 'video', 'surge-winner.mp4');
const WAV = path.join(SP, 'video', 'surge-winner.wav');
const FFMPEG = '/usr/bin/ffmpeg';
const FPS = 30, W = 1080, H = 1920;

if (!fs.existsSync(SRC)) { console.error('no page — run: python3 build-winner-video.py'); process.exit(1); }
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
const widths = await pg.evaluate(() => {
  window.__seek(0.9);                       // lets the fit pass build the spans
  const el = document.querySelector('#s1t .fitspan');
  if (!el) return null;
  const at = t => { window.__seek(t); return el.getBoundingClientRect().width; };
  return [at(0.90), at(1.15), at(1.80)];
});
if (!widths) { console.error('no .fitspan — the shrink-to-fit pass never ran'); process.exit(1); }
if (!(widths[2] > widths[0] * 1.08)) {
  console.error(`headline never widened (${widths.map(w => w.toFixed(0)).join(' -> ')}px) — static font instance?`);
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
  console.log('  (no audio bed yet — run python3 build-winner-audio.py, then re-run)');
}

const mb = (fs.statSync(out).size / 1024 / 1024).toFixed(1);
console.log(`${path.basename(out)}  ${W}x${H}  ${FPS}fps  ${pre.dur}s  ${mb}MB`
  + `  headline ${widths.map(w => w.toFixed(0)).join('->')}px  ok`);
