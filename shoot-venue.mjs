import { chromium } from 'playwright';
const SC='/tmp/claude-0/-home-user-May-madness/0e44f0ad-a683-5f0d-9de6-9459ae328963/scratchpad';
const b=await chromium.launch({executablePath:'/opt/pw-browsers/chromium'});
for (const name of process.argv.slice(2)) {
  const p=await b.newPage({viewport:{width:1080,height:1528},deviceScaleFactor:3});
  await p.goto('file://'+SC+'/'+name+'.html',{waitUntil:'load'});
  await p.waitForTimeout(900);
  const fit=await p.evaluate(()=>{const z=document.querySelector('.z');
    return Math.round(z.lastElementChild.getBoundingClientRect().bottom);});
  console.log(name.padEnd(22), 'bottom', fit, 'of 1528', fit<=1478?'OK':'OVERFLOW');
  await p.screenshot({path:SC+'/'+name+'@3x.png'});
  await p.close();
}
await b.close();
