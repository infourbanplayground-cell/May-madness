import { chromium } from 'playwright';
const SC='/tmp/claude-0/-home-user-May-madness/0e44f0ad-a683-5f0d-9de6-9459ae328963/scratchpad';
const name = process.argv[2] || 'session-story';
const b=await chromium.launch({executablePath:'/opt/pw-browsers/chromium'});
const p=await b.newPage({viewport:{width:1080,height:1920},deviceScaleFactor:3});
await p.goto('file://'+SC+'/'+name+'.html',{waitUntil:'load'});
await p.waitForTimeout(1300);
const fit=await p.evaluate(()=>{const z=document.querySelector('.z');
  return {t:Math.round(z.firstElementChild.getBoundingClientRect().top),
          b:Math.round(z.lastElementChild.getBoundingClientRect().bottom)};});
console.log('content', fit.t+'..'+fit.b, 'of 1920 | inside 170..1676?',
  fit.t>=170 && fit.b<=1676 ? 'YES':'NO');
await p.screenshot({path:SC+'/'+name+'@3x.png'});
await b.close();
