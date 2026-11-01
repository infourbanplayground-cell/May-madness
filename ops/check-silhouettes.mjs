// A proof sheet for the landmark silhouettes: every one on the medallion it
// will actually be drawn in, at the three sizes the app and the posts use.
//
// A silhouette only has to do one thing — be recognisable as its building at
// 48px on a phone — and the only way to know is to look at it there. The
// handoff's four are placeholders it asks to have replaced; the four drawn in
// brand/national/silhouettes are originals offered as replacements.
//
//   node ops/check-silhouettes.mjs
import { chromium } from 'playwright';
import { execFileSync } from 'child_process';
import fs from 'fs';

const A = JSON.parse(execFileSync('python3', ['-I', '-c', `
import sys, json; sys.path.insert(0, 'ops')
from national_assets import assets, SVGS, OURS, LANDMARK_PNG
a = assets()
names = [k for k in list(SVGS) + list(LANDMARK_PNG) if k.startswith("mon-")]
print(json.dumps({k: {"url": a[k + "@white"],
                      "kind": "SUPPLIED" if k in LANDMARK_PNG
                              else ("drawn here" if k in OURS else "handoff")}
                  for k in names}))`]).toString());

const SIZES = [48, 74, 150];
const ORDER = { SUPPLIED: 0, 'drawn here': 1, handoff: 2 };
const names = Object.keys(A).sort((x, y) =>
  (ORDER[A[x].kind] - ORDER[A[y].kind]) || x.localeCompare(y));
const cell = (n) => `
  <div style="text-align:center">
    ${SIZES.map(s => `<div style="width:${s}px;height:${s}px;border-radius:50%;
       background:#B8141F url(${A[n].url}) no-repeat center 54%/62% auto;
       box-shadow:0 0 0 3px #F7F1E6,0 0 0 6px #D7202E;margin:0 auto 14px"></div>`).join('')}
    <div style="font:700 15px/1.3 monospace;color:#F7F1E6;letter-spacing:.08em">
      ${n.replace('mon-', '').toUpperCase()}</div>
    <div style="font:700 12px monospace;margin-top:4px;color:${
      A[n].kind === 'SUPPLIED' ? '#087A3F'
      : A[n].kind === 'drawn here' ? '#F2B8BC' : '#8a6a6a'}">
      ${A[n].kind.toUpperCase()}</div>
  </div>`;

const html = `<!doctype html><meta charset="utf-8">
<body style="margin:0;background:#9E1520;padding:40px;display:flex;gap:34px;
  align-items:flex-start;font-family:system-ui">
${names.map(cell).join('')}</body>`;

const b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
const pg = await b.newPage({ viewport: { width: 1700, height: 400 }, deviceScaleFactor: 2 });
await pg.setContent(html, { waitUntil: 'load' });
// EVERY DISC MUST HAVE INK IN IT. A silhouette whose path failed to parse
// renders as an empty red circle, which looks exactly like a design choice.
const empty = await pg.evaluate(() => {
  const out = [];
  for (const d of document.querySelectorAll('div[style*="border-radius:50%"]'))
    if (!/url\(["']?data:image\//.test(getComputedStyle(d).backgroundImage))
      out.push(d.parentElement.innerText.trim().split('\n')[0]);
  return out;
});
await pg.screenshot({ path: 'brand/national/silhouettes/PROOF.png', fullPage: true });
await b.close();
if (empty.length) { console.error('no artwork: ' + empty.join(', ')); process.exit(1); }
console.log(`ok — ${names.length} silhouettes, brand/national/silhouettes/PROOF.png`);
