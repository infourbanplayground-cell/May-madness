// Record the BLACKOUT Vol.8 season recap to H.264.
//
// Deterministic capture: the page exposes `window.__seek(t)` and has no CSS
// animations, so every frame is a scrub rather than a race with a timeline.
//
// H.264 comes from the apt ffmpeg at /usr/bin/ffmpeg. Playwright's bundled one
// is VP8-only and silently yields an .mp4 nothing will play.
//
//   node record-blackout-recap-video.mjs
import { chromium } from 'playwright';
import { execFileSync } from 'child_process';
import fs from 'fs';
import path from 'path';

const SP = process.env.SP
  || '/tmp/claude-0/-home-user-May-madness/0e44f0ad-a683-5f0d-9de6-9459ae328963/scratchpad';
const SRC = path.join(SP, 'blackout-recap.html');
const FRAMES = path.join(SP, '_borecapframes');
const SILENT = path.join(SP, 'video', 'blackout-recap-silent.mp4');
const FINAL = path.join(SP, 'video', 'blackout-recap.mp4');
const WAV = path.join(SP, 'video', 'blackout-recap.wav');
const FFMPEG = '/usr/bin/ffmpeg';
const FPS = 30, W = 1080, H = 1920;

if (!fs.existsSync(SRC)) { console.error(`no page at ${SRC}`); process.exit(1); }
if (!fs.existsSync(FFMPEG)) {
  console.error('need the apt ffmpeg (H.264); the bundled one is VP8-only');
  process.exit(1);
}
fs.rmSync(FRAMES, { recursive: true, force: true });
fs.mkdirSync(FRAMES, { recursive: true });
fs.mkdirSync(path.dirname(FINAL), { recursive: true });

const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
const pg = await browser.newPage({ viewport: { width: W, height: H }, deviceScaleFactor: 1 });
const errs = [];
pg.on('pageerror', e => errs.push(e.message));
await pg.goto('file://' + SRC, { waitUntil: 'load' });
await pg.evaluate(() => document.fonts.ready);

const pre = await pg.evaluate(() => {
  // THE FACE MUST BE PROVED DRAWN. getComputedStyle reports what was asked for
  // whether or not it loaded, and document.fonts.check() answers true with
  // zero faces loaded — the whole UPRISING story series once rendered in Times
  // with every assertion green. Archivo is measured against the SAME STACK
  // FALLING BACK; JetBrains Mono is installed system-wide in this container so
  // a width probe cannot tell it from the embedded copy, and it is checked for
  // being in document.fonts instead.
  const probe = (stack, it) => {
    const s = document.createElement('span');
    s.textContent = 'BLACKOUT 258 Champion HAMBURGEFONS';
    s.style.cssText = 'position:absolute;visibility:hidden;white-space:nowrap;'
      + `font-size:100px;font-family:${stack};` + (it ? 'font-style:italic;font-weight:900;' : '');
    document.body.appendChild(s);
    const w = s.getBoundingClientRect().width;
    s.remove();
    return w;
  };
  const loaded = [...document.fonts].filter(f => f.status === 'loaded')
    .map(f => f.family.replace(/['"]/g, ''));
  return {
    seek: typeof window.__seek === 'function',
      dur: window.__dur, starts: window.__starts, scenes: window.__scenes,
    archivoDrawn: probe("'Archivo',serif", true) !== probe('serif', true),
    archivo: loaded.includes('Archivo'), mono: loaded.includes('JetBrains Mono'),
    vars: getComputedStyle(document.querySelector('.d')).fontVariationSettings,
  };
});
if (!pre.seek) { console.error('the page exposes no __seek'); process.exit(1); }
const fontBad = [];
if (!pre.archivoDrawn) fontBad.push('Archivo was not DRAWN');
if (!pre.archivo) fontBad.push('Archivo is not embedded');
if (!pre.mono) fontBad.push('JetBrains Mono is not embedded');
if (!/125/.test(pre.vars || '')) fontBad.push(`display type is at ${pre.vars || 'no width axis'}`);
if (fontBad.length) { console.error('!! ' + fontBad.join(' | ')); process.exit(1); }

// ── Layout, sampled across every scene ────────────────────────────────────
// Three samples per scene rather than one: the type is moving, and a block
// that fits at the cut can be mid-rise and overlapping 300ms later.
const marks = [];
for (let i = 0; i < pre.starts.length; i++) {
  const end = i + 1 < pre.starts.length ? pre.starts[i + 1] : pre.dur;
  for (const f of [0.22, 0.58, 0.92]) marks.push(pre.starts[i] + (end - pre.starts[i]) * f);
}
const layout = await pg.evaluate((marks) => {
  const bad = [];
  const blockOf = (n) => {
    for (let e = n.parentElement; e; e = e.parentElement)
      if (getComputedStyle(e).display !== 'inline') return e;
    return document.body;
  };
  for (const t of marks) {
    window.__seek(t);
    // A poster scene carries no type of ours at all, which is the point —
    // skip the type checks there rather than inventing something to measure.
    if (document.querySelector('.shot.on')) continue;
    const sc = document.querySelector('.scene.on');
    if (!sc) { bad.push(`t=${t.toFixed(2)}: nothing is on screen`); continue; }

    for (const e of sc.querySelectorAll('*')) {
      const b = e.getBoundingClientRect();
      if (!b.width || getComputedStyle(e).opacity < 0.08) continue;
      if (b.right > 1080.5 || b.left < -0.5 || b.top < -0.5 || b.bottom > 1920.5)
        bad.push(`t=${t.toFixed(2)} ${e.id || e.className} runs off the frame`);
      // A box can sit inside the frame while the TEXT in it runs out the side.
      if (e.scrollWidth > e.clientWidth + 1 && getComputedStyle(e).overflow === 'visible'
          && e.childElementCount === 0 && e.textContent.trim())
        bad.push(`t=${t.toFixed(2)} clipped: "${e.textContent.trim().slice(0, 22)}" `
          + `needs ${e.scrollWidth}px in ${e.clientWidth}px`);
    }

    // Two runs of type on top of each other — the check that catches a line
    // that WRAPPED, since a wrapped line never overflows anything. Per-line
    // boxes and only across different blocks: inline runs inside one paragraph
    // share line boxes by definition.
    const lines = [];
    const walk = document.createTreeWalker(sc, NodeFilter.SHOW_TEXT);
    for (let n = walk.nextNode(); n; n = walk.nextNode()) {
      if (!n.nodeValue.trim()) continue;
      const blk = blockOf(n);
      if (getComputedStyle(blk).opacity < 0.08) continue;
      const rg = document.createRange();
      rg.selectNodeContents(n);
      for (const b of rg.getClientRects()) {
        if (b.width < 0.5 || b.height < 0.5) continue;
        lines.push({ t: n.nodeValue.trim().slice(0, 22), blk,
                     c: blk.id || blk.className, x: b.x, y: b.y, w: b.width, h: b.height });
      }
    }
    for (let i = 0; i < lines.length; i++) for (let j = i + 1; j < lines.length; j++) {
      const a = lines[i], c = lines[j];
      if (a.blk === c.blk) continue;
      const ox = Math.min(a.x + a.w, c.x + c.w) - Math.max(a.x, c.x);
      const oy = Math.min(a.y + a.h, c.y + c.h) - Math.max(a.y, c.y);
      // A client rect is a line box, not the ink, so neighbouring blocks of
      // display type nearly touch by design.
      if (ox > 2 && oy > 14) {
        bad.push(`t=${t.toFixed(2)} overlap: ${a.c} "${a.t}" / ${c.c} "${c.t}" `
          + `${ox.toFixed(0)}x${oy.toFixed(0)}px`);
      }
    }
  }
  return [...new Set(bad)];
}, marks);

// ── The posters have to actually be there ─────────────────────────────────
// A missing or un-decoded poster is a BLACK FRAME, and every other assertion
// stays green through it: there is no type on those scenes to clip, to
// overflow or to overlap. The film is three photographs and a table — if a
// photograph does not load, there is no film.
const shots = await pg.evaluate(() =>
  [...document.querySelectorAll('.shot img')].map(i => ({
    src: i.getAttribute('src') || '',
    ok: i.complete && i.naturalWidth > 0,
    w: i.naturalWidth, h: i.naturalHeight,
  })));
if (shots.length !== 3) layout.push(`${shots.length} posters, expected 3`);
for (const sh of shots) {
  if (!sh.ok) { layout.push(`poster did not load: ${sh.src}`); continue; }
  // 9:16 within a percent. A poster at another aspect is cropped by
  // object-fit, and what it loses is the foot — the name and the points.
  if (Math.abs(sh.w / sh.h - 1080 / 1920) > 0.01)
    layout.push(`poster ${sh.src} is ${sh.w}x${sh.h}, not 9:16 — it will be cropped`);
}

if (layout.length) {
  console.error('!! ' + layout.join('\n!! '));
  await browser.close();
  process.exit(1);
}

// ── Capture ───────────────────────────────────────────────────────────────
const total = Math.round(pre.dur * FPS);
for (let i = 0; i < total; i++) {
  await pg.evaluate(t => window.__seek(t), i / FPS);
  await pg.screenshot({ path: path.join(FRAMES, String(i).padStart(5, '0') + '.png') });
  if (i % 120 === 0) process.stdout.write(`\r  ${i}/${total} frames`);
}
process.stdout.write(`\r  ${total}/${total} frames\n`);
await browser.close();
if (errs.length) { console.error('page errors: ' + errs.join('; ')); process.exit(1); }

execFileSync(FFMPEG, ['-y', '-framerate', String(FPS), '-i', path.join(FRAMES, '%05d.png'),
  '-c:v', 'libx264', '-preset', 'slow', '-crf', '19', '-pix_fmt', 'yuv420p', SILENT],
  { stdio: ['ignore', 'ignore', 'inherit'] });

if (fs.existsSync(WAV)) {
  execFileSync(FFMPEG, ['-y', '-i', SILENT, '-i', WAV, '-c:v', 'copy', '-c:a', 'aac',
    '-b:a', '192k', '-shortest', '-movflags', '+faststart', FINAL],
    { stdio: ['ignore', 'ignore', 'inherit'] });
} else {
  // A silent explainer is still a usable explainer; say so rather than failing.
  fs.copyFileSync(SILENT, FINAL);
  console.log('  (no wav — run python3.13 build-blackout-recap-audio.py for sound)');
}
fs.rmSync(FRAMES, { recursive: true, force: true });

const mb = (fs.statSync(FINAL).size / 1024 / 1024).toFixed(1);
console.log(`${path.basename(FINAL)}  ${W}x${H}  ${FPS}fps  ${pre.dur}s  ${mb}MB  `
  + `${shots.length} posters  ok`);
