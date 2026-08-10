import { chromium } from 'playwright';
import fs from 'fs';
const SC='/tmp/claude-0/-home-user-May-madness/0e44f0ad-a683-5f0d-9de6-9459ae328963/scratchpad';
const OUT=SC+'/design-pack'; fs.mkdirSync(OUT,{recursive:true});
const state=fs.readFileSync(SC+'/aa_live2.json','utf8');
const photos=fs.readFileSync(SC+'/aa_photos.json','utf8');

const b=await chromium.launch({executablePath:'/opt/pw-browsers/chromium'});
const p=await b.newPage({viewport:{width:430,height:932}, deviceScaleFactor:2});
// The app talks to its own origin; serve the real saved payloads so the
// screens show real content rather than empty states.
await p.route('**/state',   r=>r.fulfill({status:200,contentType:'application/json',body:state}));
await p.route('**/photos',  r=>r.fulfill({status:200,contentType:'application/json',body:photos}));
await p.route('**/session-photos*', r=>r.fulfill({status:200,contentType:'application/json',body:'[]'}));
await p.route('**/history', r=>r.fulfill({status:200,contentType:'application/json',body:'[]'}));

await p.goto('http://127.0.0.1:8099/index.html',{waitUntil:'load',timeout:60000});
await p.waitForTimeout(6000);
const tabs=await p.evaluate(()=>{
  const nav=document.querySelector('nav'); if(!nav) return [];
  return [...nav.querySelectorAll('button')].map(e=>e.innerText.trim().replace(/\s+/g,' '));
});
console.log('tabs:', JSON.stringify(tabs));
console.log('rendered text length:', await p.evaluate(()=>document.body.innerText.length));
for (let i=0;i<tabs.length;i++){
  await p.evaluate(i=>document.querySelectorAll('nav button')[i].click(), i);
  await p.waitForTimeout(1600);
  const slug=(tabs[i]||('tab'+i)).toLowerCase().replace(/[^a-z0-9]+/g,'-').replace(/^-|-$/g,'')||('tab'+i);
  await p.screenshot({path:`${OUT}/0${i+1}-${slug}.png`, fullPage:true});
  console.log('  shot', slug);
}
await b.close();
