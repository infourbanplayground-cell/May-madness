// Muscat Heist phase 5: the share exports.
//   node ops/render-heist-stories.mjs          writes brand/heist/stories/*.png
//   SABOTAGE=nofont | spill | exportfont       must go red (exportfont: the in-app
//   export skips embedding the faces, the render is untouched)
// For the poster, the contenders and MY CARD it:
//   1. renders the 416x740 frame at 1080/416 and saves EXACTLY 1080x1920;
//   2. checks the face is really drawn on the frame's own text, nothing is
//      clipped or under 11px, no text leaves the frame, every image loaded;
//   3. checks the words are the data's: HEIST, the derived pool, no NIGHTS,
//      no 402, no Arabic, the contenders' gap in words;
//   4. lays the poster and the contenders beside their reference PNGs;
//   5. drives the IN-APP export (share sheet -> Share image) and checks the
//      file it makes is 1080x1920 and agrees with the render — a library that
//      silently dropped the webfont or an image would make a file that looks
//      like a poster and differs from this one.
import { chromium } from 'playwright';
import fs from 'fs';
import http from 'http';
import path from 'path';
import { execFileSync } from 'child_process';

const ROOT = path.resolve(path.dirname(new URL(import.meta.url).pathname), '..');
const SC = '/tmp/claude-0/-home-user-May-madness/0e44f0ad-a683-5f0d-9de6-9459ae328963/scratchpad';
const SAB = process.env.SABOTAGE || '';
const OUT = SAB ? path.join(SC, 'heist-qa', 'stories-sabotage') : path.join(ROOT, 'brand', 'heist', 'stories');
const QA = path.join(SC, 'heist-qa', SAB ? 'stories-sabotage' : 'stories');
fs.mkdirSync(OUT, { recursive: true }); fs.mkdirSync(QA, { recursive: true });
const K = 1080 / 416;
const STORIES = [['campaign-poster', 'story/poster', '18-story-campaign-poster'],
                 ['contenders', 'story/contenders', '19-story-contenders'],
                 ['my-card', 'story/card/p05', null]];
const TYPES = { '.html': 'text/html; charset=utf-8', '.css': 'text/css', '.woff2': 'font/woff2', '.png': 'image/png', '.webp': 'image/webp', '.jpg': 'image/jpeg' };
const srv = http.createServer((req, res) => {
  const f = path.join(ROOT, decodeURIComponent((req.url || '/').split('?')[0]));
  if (!f.startsWith(ROOT) || !fs.existsSync(f) || fs.statSync(f).isDirectory()) { res.writeHead(404); return res.end(); }
  let body = fs.readFileSync(f);
  if (f.endsWith('.html')) {
    let s = body.toString();
    if (SAB === 'nofont') s = s.replace(/<link rel="stylesheet"[^>]*>/g, '');
    if (SAB === 'exportfont') s = s.replace('cacheBust: false', 'cacheBust: false, skipFonts: true');
    if (SAB === 'spill') s = s.replace('.mh-storybill { position: absolute; left: 22px; right: 22px; }', '.mh-storybill { position: absolute; left: 22px; right: -160px; white-space: nowrap; }');
    body = Buffer.from(s);
  }
  res.writeHead(200, { 'Content-Type': TYPES[path.extname(f)] || 'application/octet-stream' }); res.end(body);
}).listen(0);
const PORT = srv.address().port;
const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
const fails = [];
const vendor = f => fs.readFileSync(path.join(SC, 'vendor', f), 'utf8');

async function open(hash, vp, dsf) {
  const ctx = await browser.newContext({ viewport: vp, deviceScaleFactor: dsf, acceptDownloads: true });
  const pg = await ctx.newPage();
  const errs = []; pg.on('pageerror', e => errs.push(e.message));
  await pg.route('**/unpkg.com/**', r => {
    const u = r.request().url();
    const f = /html-to-image/.test(u) ? 'h2i.js' : /babel/.test(u) ? 'babel.js' : /react-dom/.test(u) ? 'react-dom.js' : 'react.js';
    r.fulfill({ status: 200, contentType: 'application/javascript', body: vendor(f) });
  });
  await pg.goto(`http://127.0.0.1:${PORT}/brand/heist/preview.html#${hash}`, { waitUntil: 'load' });
  await pg.waitForSelector('.mh-story', { timeout: 30000 });
  await pg.evaluate(() => Promise.all(["italic 40px Fraunces", "900 40px Archivo", "600 40px Manrope", "500 40px 'JetBrains Mono'"]
    .map(f => document.fonts.load(f).catch(() => 0))));
  await pg.evaluate(() => document.fonts.ready);
  await pg.waitForFunction(() => [...document.fonts].every(f => f.status !== 'loading'), null, { timeout: 15000 });
  await pg.evaluate(() => Promise.all([...document.images].map(i => { i.loading = 'eager';
    return i.complete ? 0 : new Promise(r => { i.onload = i.onerror = r; }); })));
  await pg.waitForTimeout(400);
  return { ctx, pg, errs };
}

const audit = () => {
  const frame = document.querySelector('.mh-story'), F = frame.getBoundingClientRect();
  const out = { text: frame.innerText, undrawn: [], small: [], clipped: [], outside: [], broken: [] };
  const ownText = e => [...e.childNodes].find(n => n.nodeType === 3 && n.textContent.trim());
  for (const e of frame.querySelectorAll('*')) {
    const t = ownText(e); if (!t) continue;
    const cs = getComputedStyle(e);
    if (parseFloat(cs.fontSize) < 11) out.small.push(`"${t.textContent.trim().slice(0, 20)}" ${cs.fontSize}`);
    if (e.scrollWidth > e.clientWidth + 1 && cs.overflow !== 'visible') out.clipped.push(t.textContent.trim().slice(0, 24));
    const r = document.createRange(); r.selectNodeContents(t);
    for (const b of r.getClientRects()) if (b.left < F.left - .5 || b.right > F.right + .5 || b.top < F.top - .5 || b.bottom > F.bottom + .5)
      out.outside.push(`"${t.textContent.trim().slice(0, 24)}" ${Math.round(b.left - F.left)}..${Math.round(b.right - F.left)} in 416`);
    // drawn in its own face, not the fallback: forcing the fallback must move it
    const w0 = r.getBoundingClientRect().width, was = e.style.fontFamily;
    // JetBrains Mono is installed system-wide in this container, so the mono
    // fallback resolves to the same face and no width can tell them apart;
    // it is checked below as a face the page really loaded instead
    if (/mono/i.test(cs.fontFamily)) continue;
    // the stack minus its first face IS what draws when that face is missing
    e.style.fontFamily = cs.fontFamily.split(',').slice(1).join(',') || 'serif';
    const w1 = r.getBoundingClientRect().width; e.style.fontFamily = was;
    if (Math.abs(w0 - w1) < .5) out.undrawn.push(`${cs.fontFamily.split(',')[0]} "${t.textContent.trim().slice(0, 16)}"`);
  }
  if (frame.querySelector('.mn-label') && ![...document.fonts].some(f => /JetBrains/.test(f.family) && f.status === 'loaded'))
    out.undrawn.push('JetBrains Mono never loaded');
  out.broken = [...frame.querySelectorAll('img')].filter(i => !i.naturalWidth).map(i => i.getAttribute('src'));
  return out;
};

for (const [name, hash, ref] of STORIES) {
  const { ctx, pg, errs } = await open(hash, { width: 416, height: 740 }, K);
  const r = await pg.evaluate(audit);
  const tag = name;
  if (errs.length) fails.push(`${tag}: page error ${errs[0]}`);
  if (r.undrawn.length) fails.push(`${tag}: FACE NOT DRAWN: ${r.undrawn.slice(0, 3).join(' | ')}`);
  if (r.small.length) fails.push(`${tag}: text under 11px: ${r.small.slice(0, 3).join(' | ')}`);
  if (r.clipped.length) fails.push(`${tag}: clipped: ${r.clipped.slice(0, 3).join(' | ')}`);
  if (r.outside.length) fails.push(`${tag}: text leaves the frame: ${r.outside.slice(0, 3).join(' | ')}`);
  if (r.broken.length) fails.push(`${tag}: images not loaded: ${r.broken.join(', ')}`);
  // the words are the data's
  const T = r.text.replace(/\s+/g, ' ');
  if (/NIGHTS/.test(T) || /\b402\b/.test(T) || /[؀-ۿ]/.test(T)) fails.push(`${tag}: old design's copy on the frame`);
  if (name !== 'my-card' && !/407 OMR/.test(T)) fails.push(`${tag}: pool is not the derived 407`);
  // the lockup is the owner's logo image since 25 Nov, not typeset HEIST: it must be there AND decoded
  const logo = await pg.evaluate(() => { const i = document.querySelector('.mn-logo img'); return i ? i.naturalWidth : -1; });
  // an image is invisible to the text checks, so a logo lying over the billing passed them all
  const hits = await pg.evaluate(() => {
    const L = document.querySelector('.mn-logo img'); if (!L) return [];
    const a = L.getBoundingClientRect(), out = [];
    const w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
    for (let n; (n = w.nextNode());) {
      if (!n.textContent.trim() || L.closest('.mn-lockup').contains(n.parentElement)) continue;
      const cs = getComputedStyle(n.parentElement); if (cs.visibility === 'hidden' || +cs.opacity === 0) continue;
      const rg = document.createRange(); rg.selectNodeContents(n);
      for (const b of rg.getClientRects()) {
        const ov = Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top), oh = Math.min(a.right, b.right) - Math.max(a.left, b.left);
        if (ov > 3 && oh > 3) { out.push(n.textContent.trim().slice(0, 30)); break; }
      }
    }
    return out;
  });
  if (hits.length) fails.push(`${tag}: the logo lies over text: ${hits.slice(0, 3).join(' | ')}`);
  if (logo <= 0) fails.push(`${tag}: the Muscat Heist logo ${logo < 0 ? 'is missing' : 'did not load'}`);
  if (name === 'contenders' && !/Eleven points/.test(T)) fails.push(`${tag}: tagline gap is not #1 - #2 in words`);
  if (name === 'campaign-poster' && !(/Every Mon & Wed · 17:30/i.test(T) && /From Wed 2 Dec/i.test(T))) fails.push(`${tag}: schedule line not from the nights: ${T.slice(-90)}`);
  const file = path.join(OUT, `${name}.png`);
  // 740 x 1080/416 is 1921.2 px; render the whole frame, keep the top 1920
  await pg.screenshot({ path: file, clip: { x: 0, y: 0, width: 416, height: 740 } });
  execFileSync('python3.13', ['-c', `from PIL import Image; i=Image.open(${JSON.stringify(file)}); i.crop((0,0,1080,1920)).save(${JSON.stringify(file)})`]);
  const size = execFileSync('python3.13', ['-c', `from PIL import Image; print(*Image.open(${JSON.stringify(file)}).size)`]).toString().trim();
  if (size !== '1080 1920') fails.push(`${tag}: exported ${size}, not 1080 1920`);
  console.log(`  ${name.padEnd(16)} ${size}  undrawn ${r.undrawn.length}  small ${r.small.length}  clipped ${r.clipped.length}  outside ${r.outside.length}  imgs-broken ${r.broken.length}`);
  if (ref) execFileSync('python3.13', ['-c', `
from PIL import Image
a=Image.open(${JSON.stringify(path.join(ROOT, 'brand/heist/handoff/screenshots', ref + '.png'))}).convert('RGB').resize((416,740))
b=Image.open(${JSON.stringify(file)}).convert('RGB').resize((416,740))
o=Image.new('RGB',(416*2+30,760),'#333'); o.paste(a,(10,10)); o.paste(b,(436,10)); o.save(${JSON.stringify(path.join(QA, name + '-compare.png'))})`]);
  await ctx.close();
}

// the in-app export, through the real share sheet
for (const [what, file] of [['poster', 'campaign-poster'], ['contenders', 'contenders'], ['card/p05', 'my-card']]) {
  const { ctx, pg, errs } = await open(`share/${what}`, { width: 375, height: 812 }, 2);
  const dl = pg.waitForEvent('download', { timeout: 30000 }).catch(() => null);
  await pg.click('text=Share image');
  const d = await dl;
  const tag = `export ${file}`;
  if (!d) { fails.push(`${tag}: no file came out` + (errs.length ? ` (${errs[0]})` : '')); await ctx.close(); continue; }
  const got = path.join(QA, `${file}-inapp.png`); await d.saveAs(got);
  const res = execFileSync('python3.13', ['-c', `
from PIL import Image, ImageChops, ImageStat
a=Image.open(${JSON.stringify(got)}).convert('RGB'); b=Image.open(${JSON.stringify(path.join(OUT, file + '.png'))}).convert('RGB')
from PIL import ImageFilter
# blurred first: the grain is noise in both and swamps the signal; a face or an
# image the export dropped is a change of SHAPE and survives a 3px blur
bl = lambda i: i.filter(ImageFilter.GaussianBlur(3))
print(*a.size, round(sum(ImageStat.Stat(ImageChops.difference(bl(a.resize(b.size)), bl(b))).mean)/3, 2))`]).toString().trim().split(' ');
  const diff = +res[2];
  // a dropped webfont or image moves the mean far past this; the grain is
  // random per render, which is most of what remains
  if (`${res[0]} ${res[1]}` !== '1080 1920') fails.push(`${tag}: ${res[0]}x${res[1]}, not 1080x1920`);
  // measured: clean exports 0.7-1.6, the same exports with their faces dropped 3.8-9.5
  if (diff > 3) fails.push(`${tag}: differs from the render by ${diff} per channel — the export lost something`);
  console.log(`  ${tag.padEnd(22)} ${res[0]}x${res[1]}  mean diff ${diff}`);
  await ctx.close();
}
await browser.close(); srv.close();
if (fails.length) { console.error('\n' + fails.join('\n')); process.exit(1); }
console.log(`ok — ${OUT}`);
