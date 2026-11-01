// The announcement set, laid out as it will be seen: four feed cards in
// carousel order and the story beside them, on the dark ground an Instagram
// grid actually shows them against.
//
//   node ops/post-lineup.mjs
import { chromium } from 'playwright';
import fs from 'fs';
import path from 'path';

const DIR = path.resolve('brand/national/posts');
const feed = fs.readdirSync(DIR).filter(f => /^post-\d/.test(f) && f.endsWith('.png')).sort();
const story = 'post-story.png';
const b64 = f => 'data:image/png;base64,' + fs.readFileSync(path.join(DIR, f)).toString('base64');

const html = `<!doctype html><meta charset="utf-8">
<body style="margin:0;background:#141414;padding:34px;font-family:system-ui">
  <div style="color:#F7F1E6;font:700 20px/1 monospace;letter-spacing:.18em;
       margin-bottom:6px">56 NATIONAL SERIES — ANNOUNCEMENT SET</div>
  <div style="color:#F2B8BC;font:700 13px/1.6 monospace;margin-bottom:22px">
    ${feed.length} feed cards (1080&times;1350, carousel order) &middot; 1 story (1080&times;1920)</div>
  <div style="display:flex;gap:20px;align-items:flex-start">
    <div style="display:flex;gap:16px">
      ${feed.map((f, i) => `<div>
        <div style="color:#CBBDB6;font:700 12px monospace;margin-bottom:7px;letter-spacing:.1em">
          ${i + 1} &middot; ${f.replace(/^post-\d-|\.png$/g, '').toUpperCase()}</div>
        <img src="${b64(f)}" style="width:300px;display:block;border-radius:8px">
      </div>`).join('')}
    </div>
    <div style="border-left:1px solid #333;padding-left:20px">
      <div style="color:#CBBDB6;font:700 12px monospace;margin-bottom:7px;letter-spacing:.1em">
        STORY</div>
      <img src="${b64(story)}" style="width:264px;display:block;border-radius:8px">
    </div>
  </div>
</body>`;

const br = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
const pg = await br.newPage({ viewport: { width: 1660, height: 560 } });
await pg.setContent(html, { waitUntil: 'load' });
const out = path.join(DIR, 'LINEUP.png');
await pg.screenshot({ path: out, fullPage: true });
await br.close();
console.log(`ok — ${feed.length} feed + 1 story  ${out}`);
