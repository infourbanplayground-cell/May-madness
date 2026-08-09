import { chromium } from 'playwright';
import fs from 'fs';

// Deterministic capture, not a screen recording. Playwright's own video
// output ran ~3.2x slow on an earlier story and had to be rescued with
// setpts; pausing the animation timeline and scrubbing to an exact
// currentTime per frame means the file is right the first time.
const SC = '/tmp/claude-0/-home-user-May-madness/0e44f0ad-a683-5f0d-9de6-9459ae328963/scratchpad';
const NAME = process.argv[2] || 'session-story-anim';
const FPS = 30, SECONDS = 7;
const FRAMES = FPS * SECONDS;
const DIR = `${SC}/_frames`;

fs.rmSync(DIR, { recursive: true, force: true });
fs.mkdirSync(DIR, { recursive: true });

const b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
const p = await b.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
await p.goto('file://' + SC + '/' + NAME + '.html', { waitUntil: 'load' });
await p.waitForTimeout(1500);            // let the embedded fonts land

const n = await p.evaluate(() => document.getAnimations().length);
if (!n) { console.error('no animations found — is this the --anim build?'); process.exit(1); }
console.log('animations on the page:', n);

for (let f = 0; f < FRAMES; f++) {
  const t = (f / FPS) * 1000;
  await p.evaluate((ms) => {
    for (const a of document.getAnimations()) { a.pause(); a.currentTime = ms; }
  }, t);
  await p.screenshot({ path: `${DIR}/f${String(f).padStart(4, '0')}.png` });
}
console.log('captured', FRAMES, 'frames at', FPS, 'fps =', SECONDS, 's');
await b.close();
