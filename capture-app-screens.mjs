// Captures the real app screens the feature video is built from.
//
// Real captures, not mockups: a promo made of drawings of an app is a promise,
// and a promo made of the app is a demonstration. It runs against the local
// preview rather than the live site because the live Vol.8 has no sessions yet,
// so ME, the receipt and the badges would all be empty — the screens carry last
// season's data and the video labels them as such.
import { chromium } from 'playwright';
import fs from 'fs';

const URL = process.env.APP_URL || 'http://127.0.0.1:8899/';
const OUT = '/tmp/shots';
const ME = process.env.ME_ID || 'p_mptqpbkf_ixqzu';   // Hamed Amri — a full season

fs.mkdirSync(OUT, { recursive: true });
const browser = await chromium.launch({
  executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome',
  args: ['--ignore-certificate-errors'],
});
const ctx = await browser.newContext({
  viewport: { width: 430, height: 900 }, deviceScaleFactor: 2,
  ignoreHTTPSErrors: true, hasTouch: true,
});
await ctx.addInitScript(id => localStorage.setItem('aa-me', id), ME);
const pg = await ctx.newPage();
const errs = [];
pg.on('pageerror', e => errs.push(e.message));

const settle = ms => pg.waitForTimeout(ms);
const tab = async name => {
  for (const b of await pg.$$('nav button')) {
    if ((await b.innerText()).trim() === name) { await b.click(); return; }
  }
  throw new Error(`no ${name} tab`);
};
// Click by coordinates: a React re-render between locating and clicking detaches
// the handle, and these screens re-render constantly.
const tap = async match => {
  const box = await pg.evaluate(m => {
    const b = [...document.querySelectorAll('button')].find(e => new RegExp(m).test(e.innerText || ''));
    if (!b) return null;
    b.scrollIntoView({ block: 'center' });
    const r = b.getBoundingClientRect();
    return { x: r.x + r.width / 2, y: r.y + r.height / 2 };
  }, match);
  if (!box) throw new Error(`no button matching ${match}`);
  await settle(300);
  const box2 = await pg.evaluate(m => {
    const b = [...document.querySelectorAll('button')].find(e => new RegExp(m).test(e.innerText || ''));
    const r = b.getBoundingClientRect();
    return { x: r.x + r.width / 2, y: r.y + r.height / 2 };
  }, match);
  await pg.mouse.click(box2.x, box2.y);
};
const closeSheet = async () => {
  const all = await pg.$$('button');
  for (let i = all.length - 1; i >= 0; i--) {
    if ((await all[i].innerText().catch(() => '')).trim() === 'CLOSE') { await all[i].click(); return; }
  }
};
const shoot = async name => { await pg.screenshot({ path: `${OUT}/${name}.png` }); console.log(`  ${name}.png`); };

await pg.goto(URL, { waitUntil: 'load' });
await settle(7000);
await shoot('home');

await tab('ME');            await settle(2200); await shoot('me');
await tap('Session champion[\\s\\S]*\\+60'); await settle(1900); await shoot('receipt');
await closeSheet();         await settle(700);
await pg.evaluate(() => window.scrollTo(0, 1500)); await settle(900); await shoot('badges');
await pg.evaluate(() => window.scrollTo(0, 0));    await settle(500);
await tap('^MY NIGHT$');    await settle(2800); await shoot('share');
await closeSheet();         await settle(700);
await tab('PLAYERS');       await settle(2200); await shoot('roster');

if (errs.length) console.error('  !! page errors: ' + errs.slice(0, 3).join(' | '));
const missing = ['home','me','receipt','badges','share','roster']
  .filter(n => !fs.existsSync(`${OUT}/${n}.png`) || fs.statSync(`${OUT}/${n}.png`).size < 20000);
console.log(missing.length ? `  !! thin or missing: ${missing.join(', ')}` : '  all six captured');
await browser.close();
