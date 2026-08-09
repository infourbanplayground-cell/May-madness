import { chromium } from 'playwright';
const SC='/tmp/claude-0/-home-user-May-madness/0e44f0ad-a683-5f0d-9de6-9459ae328963/scratchpad';
const name = process.argv[2] || 'pay-card';
const b=await chromium.launch({executablePath:'/opt/pw-browsers/chromium'});
const p=await b.newPage({viewport:{width:1080,height:1350},deviceScaleFactor:3});
await p.goto('file://'+SC+'/'+name+'.html',{waitUntil:'load'});
await p.waitForTimeout(1200);
const fit=await p.evaluate(()=>{const z=document.querySelector('.z');
  const l=z.lastElementChild, pn=document.querySelector('.panel').getBoundingClientRect();
  return {bottom:Math.round(l.getBoundingClientRect().bottom), h:innerHeight,
          quiet:getComputedStyle(document.querySelector('.panel')).padding,
          panel:Math.round(pn.width)+'x'+Math.round(pn.height)};});
console.log('content bottom', fit.bottom, 'of', fit.h, '| fits?', fit.bottom<=fit.h-40?'YES':'NO',
            '| panel', fit.panel, '| quiet zone', fit.quiet);
await p.screenshot({path:SC+'/'+name+'@3x.png'});
await b.close();
