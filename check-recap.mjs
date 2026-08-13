import { chromium } from 'playwright';
const SC = '/tmp/claude-0/-home-user-May-madness/0e44f0ad-a683-5f0d-9de6-9459ae328963/scratchpad';
const b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
const p = await b.newPage({ viewport: { width: 1080, height: 1920 } });
await p.goto('file://' + SC + '/recap.html', { waitUntil: 'load' });
await p.waitForTimeout(2000);

// Each scene must sit inside 170..1676 — the story frame that survives
// Instagram's profile row and reply bar.
const r = await p.evaluate(() => {
  document.getAnimations().forEach(a => { a.pause(); a.currentTime = 999999; });
  return [...document.querySelectorAll('.sc')].map(s => {
    const kids = [...s.children];
    const top = Math.min(...kids.map(k => k.getBoundingClientRect().top));
    const bot = Math.max(...kids.map(k => k.getBoundingClientRect().bottom));
    return { id: s.id, top: Math.round(top), bottom: Math.round(bot),
             fits: top >= 170 && bot <= 1676 };
  });
});
console.table(r);
console.log('all fit:', r.every(x => x.fits));
await b.close();
