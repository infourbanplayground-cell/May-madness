import { chromium } from 'playwright';
import path from 'path';
const OUT = path.resolve('brand/medal-stickers');
const b = await chromium.launch({ executablePath:'/opt/pw-browsers/chromium-1194/chrome-linux/chrome' });
for (const size of [50,25]) for (const p of [1,2,3]) {
  const pg = await b.newPage({ viewport:{width:400,height:400} });
  await pg.goto('file://'+path.join(OUT, `ss-medal-${size}mm-${p}-bleed.html`));
  await pg.evaluate(()=>document.fonts.ready);
  await pg.waitForFunction(()=>document.querySelector('svg')?.dataset.centred==='1');
  const r = await pg.evaluate(() => {
    const n=document.getElementById('num'), s=document.getElementById('suf');
    const vb=document.querySelector('svg').viewBox.baseVal;
    const nb=n.getBBox(), sb=s.getBBox();
    const C=vb.width/2;
    return { C, numCentre:nb.x+nb.width/2, off:(nb.x+nb.width/2)-C,
             pct:(((nb.x+nb.width/2)-C)/vb.width*100),
             sufLeft:sb.x, numRight:nb.x+nb.width };
  });
  console.log(`${size}mm ${p}: numeral centre off ${r.off.toFixed(2)} units (${r.pct.toFixed(3)}% of disc) · suffix gap ${(r.sufLeft-r.numRight).toFixed(1)}`);
  await pg.close();
}
await b.close();
