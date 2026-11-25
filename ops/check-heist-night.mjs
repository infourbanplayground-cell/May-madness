// Muscat Heist phase 3: drives the night screens in the preview — live scoring
// (+1 / serve / undo), the session tabs, and the recap slides (5s advance,
// arrows, tap thirds, hold to pause, reduced motion). node ops/check-heist-night.mjs
import { chromium } from 'playwright'; import fs from 'fs'; import http from 'http'; import path from 'path';
const ROOT='/home/user/May-madness', SC='/tmp/claude-0/-home-user-May-madness/0e44f0ad-a683-5f0d-9de6-9459ae328963/scratchpad';
const T={'.html':'text/html','.css':'text/css','.woff2':'font/woff2','.jpg':'image/jpeg','.png':'image/png'};
const srv=http.createServer((q,r)=>{const f=path.join(ROOT,decodeURIComponent(q.url.split('?')[0]));if(!fs.existsSync(f)||fs.statSync(f).isDirectory()){r.writeHead(404);return r.end()}r.writeHead(200,{'Content-Type':T[path.extname(f)]||'x'});r.end(fs.readFileSync(f))}).listen(0);
const b=await chromium.launch({executablePath:'/opt/pw-browsers/chromium'});
const fails=[]; const ok=(c,m)=>{console.log((c?'  ok   ':'  FAIL ')+m); if(!c) fails.push(m)};
async function page(hash, reduced){const ctx=await b.newContext({viewport:{width:375,height:812},reducedMotion:reduced?'reduce':'no-preference'});const pg=await ctx.newPage();
await pg.route('**/unpkg.com/**',r=>{const u=r.request().url();const f=/babel/.test(u)?'babel.js':/react-dom/.test(u)?'react-dom.js':'react.js';r.fulfill({status:200,contentType:'application/javascript',body:fs.readFileSync(path.join(SC,'vendor',f),'utf8')})});
await pg.goto(`http://127.0.0.1:${srv.address().port}/brand/heist/preview.html#${hash}`); await pg.waitForSelector('.mh-page, .mh-slides'); return pg;}
const score=pg=>pg.$$eval('[aria-live="polite"]',e=>e.map(x=>x.textContent).join('-'));
// live
let pg=await page('live');
ok(await score(pg)==='5-3','live opens at the fixture 5-3');
ok(await pg.isDisabled('.mh-undo'),'undo disabled with nothing to undo');
await pg.click('text=+1 MUNTHER'); ok(await score(pg)==='6-3','+1 MUNTHER -> 6-3');
ok(await pg.$eval('.mn-glass[data-accent="peach-50"] .mn-display', e=>e.textContent).then(t=>/HAMED/.test(t)),'serve passes to the other team after a game');
await pg.click('text=+1 HAMED'); ok(await score(pg)==='6-4','+1 HAMED -> 6-4');
await pg.click('.mh-undo'); ok(await score(pg)==='6-3','undo -> 6-3');
await pg.click('.mh-undo'); ok(await score(pg)==='5-3','undo again -> 5-3');
// session tabs
pg=await page('session/6');
await pg.click('.mn-pill:has-text("B")'); ok(await pg.isVisible('text=mossa & Ali'),'group B pill shows group B');
await pg.click('.mn-pill:has-text("Teams")'); ok(await pg.isVisible('text=Group A'),'Teams tab lists the draw');
await pg.click('.mn-pill:has-text("Knockout")'); ok(await pg.isVisible('text=drawn once the groups finish'),'Knockout empty state');
// with no votes the tab is POINTS and shows tonight's points (23 Nov rebuild), not an MVP empty state
await pg.click('.mn-pill:has-text("Points")'); ok(await pg.isVisible("text=Tonight's points"),'no votes -> the Points tab shows tonight\'s points');
await pg.click('.mn-pill:has-text("Groups")'); await pg.click('.mn-pill >> text="A"'); await pg.click('.mh-match:has-text("Salim")'); await pg.waitForTimeout(300);
ok(await pg.evaluate(()=>location.hash).then(h=>h.startsWith('#live')),'tapping the live match opens scoring');
// slides
pg=await page('slides/5/0');
const lab=()=>pg.$eval('.mh-slideshead .mn-label',e=>e.textContent);
ok((await lab()).includes('1 of 5'),'slides open on 1 of 5');
await pg.waitForTimeout(5400); ok((await lab()).includes('2 of 5'),'auto-advances after 5s');
await pg.keyboard.press('ArrowRight'); ok((await lab()).includes('3 of 5'),'→ advances');
await pg.keyboard.press('ArrowLeft'); ok((await lab()).includes('2 of 5'),'← goes back');
await pg.mouse.click(340,400); ok((await lab()).includes('3 of 5'),'tap right third -> next');
await pg.mouse.click(30,400); ok((await lab()).includes('2 of 5'),'tap left third -> previous');
await pg.mouse.move(187,400); await pg.mouse.down(); await pg.waitForTimeout(5600); ok((await lab()).includes('2 of 5'),'held = paused'); await pg.mouse.up();
pg=await page('slides/5/0',true); await pg.waitForTimeout(5600); ok((await lab()).includes('1 of 5'),'reduced motion: no auto-advance');
pg=await page('slides/5/4'); ok(await pg.isVisible('.mh-slide button:has-text("Share")'),'last slide carries Share');
await b.close(); srv.close(); if(fails.length) process.exit(1);
