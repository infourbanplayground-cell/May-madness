import { chromium } from 'playwright';
import fs from 'fs';

// Deterministic capture: pause the animation timeline and set currentTime per
// frame. Screen-recording this drifts (an earlier story came out 3.2x slow);
// scrubbing lands on exact frame times with no retiming afterwards.
const SC = '/tmp/claude-0/-home-user-May-madness/0e44f0ad-a683-5f0d-9de6-9459ae328963/scratchpad';
const FPS = 30, SECONDS = 13;
const FRAMES = FPS * SECONDS;
const DIR = `${SC}/_recap_frames`;

fs.rmSync(DIR, { recursive: true, force: true });
fs.mkdirSync(DIR, { recursive: true });

const b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
const p = await b.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
await p.goto('file://' + SC + '/recap.html', { waitUntil: 'load' });
await p.waitForTimeout(2000);   // embedded fonts and base64 photos

const n = await p.evaluate(() => document.getAnimations().length);
console.log('animations:', n);
if (!n) { console.error('no animations found'); process.exit(1); }

for (let f = 0; f < FRAMES; f++) {
  await p.evaluate((ms) => {
    for (const a of document.getAnimations()) { a.pause(); a.currentTime = ms; }
  }, (f / FPS) * 1000);
  await p.screenshot({ path: `${DIR}/f${String(f).padStart(4, '0')}.png` });
}
console.log('captured', FRAMES, 'frames =', SECONDS, 's');
await b.close();
