// Side-by-side mock of a re-theme for the Heist app, matching the owner's logo
// (25 Nov 2026: "match the font type and colors, it feels off now").
// Loads the preview page, injects a THEME layer (fonts + tokens only, no
// layout change) and shoots home / take / wanted / me for each option.
//   node ops/mock-heist-theme.mjs        -> <scratch>/theme-mock/<opt>-<screen>.png + sheet
import { chromium } from 'playwright';
import http from 'http'; import fs from 'fs'; import path from 'path';
const ROOT = path.resolve(path.dirname(new URL(import.meta.url).pathname), '..');
const SC = '/tmp/claude-0/-home-user-May-madness/0e44f0ad-a683-5f0d-9de6-9459ae328963/scratchpad';
const FC = path.join(SC, 'fontcand'); const OUT = path.join(SC, 'theme-mock'); fs.mkdirSync(OUT, { recursive: true });
const TYPES = { '.html': 'text/html; charset=utf-8', '.css': 'text/css', '.woff2': 'font/woff2', '.png': 'image/png', '.webp': 'image/webp', '.jpg': 'image/jpeg' };
const srv = http.createServer((req, res) => {
  const u = decodeURIComponent((req.url || '/').split('?')[0]);
  const f = u.startsWith('/fc/') ? path.join(FC, u.slice(4)) : path.join(ROOT, u);
  if (!fs.existsSync(f) || fs.statSync(f).isDirectory()) { res.writeHead(404); return res.end(); }
  res.writeHead(200, { 'Content-Type': TYPES[path.extname(f)] || 'application/octet-stream' }); res.end(fs.readFileSync(f));
}).listen(0);
const PORT = srv.address().port;
const vendor = f => fs.readFileSync(path.join(SC, 'vendor', f), 'utf8');
const base = (display, ground) => `
@font-face{font-family:'HX Display';src:url(/fc/${display}.woff2) format('woff2')}
@font-face{font-family:'HX Script';src:url(/fc/KaushanScript.woff2) format('woff2')}
:root{
  --mn-font-display:'HX Display',Impact,sans-serif; --mn-display-axes:normal;
  --mn-font-serif:'HX Script',cursive; --mn-serif-axes:normal;
  --mn-coral:#FF2D78; --mn-rose:#FF5C9A; --mn-peach:#FFB36B; --mn-gold:#FFC36B; --mn-sand:#F6EAD3;
  --mn-navy:${ground};
  --mn-sky:linear-gradient(180deg,#2A1650 0%,#6B2C8F 32%,#D2357E 56%,#FF7A3D 78%,#FFC36B 95%);
  --mn-grad-nights:linear-gradient(90deg,#FF2D78,#FF7A3D);
  --mn-grad-title:linear-gradient(180deg,#F6EAD3,#F6EAD3);
}
html,body,#root{background:${ground} !important}
.mn-display,.mn-name,.mn-rank,.mn-pts,.mn-l1{font-weight:400 !important;letter-spacing:.01em;
  -webkit-text-stroke:.07em #0b0b10;paint-order:stroke fill;text-shadow:.05em .07em 0 #0b0b10}
.mn-serif{font-style:normal !important;color:#FF2D78;-webkit-text-stroke:.05em #0b0b10;paint-order:stroke fill}
`;
const BOLD = base('BowlbyOne', '#1A0B2E') + `
:root{ --mn-teal:#FF2D78; --mn-mist:#E7C8FF; --mn-dim:#B79BD6; --mn-gold:#FFB347;
  --mn-line:rgba(255,45,120,.28); }
/* the logo's block face is LOWERCASE and fat, outlined and dropped */
.mn-display,.mn-name,.mn-l1{ text-transform:lowercase !important; letter-spacing:-.005em !important;
  -webkit-text-stroke:.09em #07040d; text-shadow:.06em .08em 0 #07040d, .06em .08em 0 #FF2D78; }
.mn-pts,.mn-rank{ -webkit-text-stroke:.07em #07040d; text-shadow:.05em .06em 0 #07040d }
/* kickers and labels go hot pink / orange instead of teal and sand */
.mn-label{ color:#FFB347 !important; }
[class*="mn-card"],[class*="mh-row"],.mn-glass,.mh-take-row,.mh-wrow{ background:linear-gradient(180deg,rgba(74,22,110,.55),rgba(30,10,50,.75)) !important;
  border-color:rgba(255,45,120,.45) !important; }
.mn-serif{ font-size:1.12em }
`;
const OPTS = process.env.ONLYBOLD ? { BOLD } : { A: base('LilitaOne', '#120D22'), B: base('BowlbyOne', '#1B0F2E'), BOLD };
const SCREENS = (process.env.SCREENS || 'home,take,wanted,me').split(',');
const b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
for (const [opt, css] of [...(process.env.ONLYBOLD ? [] : [['now', '']]), ...Object.entries(OPTS)]) {
  for (const s of SCREENS) {
    const ctx = await b.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 2 });
    const pg = await ctx.newPage();
    await pg.route('**/unpkg.com/**', r => { const u = r.request().url();
      r.fulfill({ status: 200, contentType: 'application/javascript', body: vendor(/html-to-image/.test(u) ? 'h2i.js' : /babel/.test(u) ? 'babel.js' : /react-dom/.test(u) ? 'react-dom.js' : 'react.js') }); });
    await pg.goto(`http://127.0.0.1:${PORT}/brand/heist/preview.html#${s}`, { waitUntil: 'load' });
    await pg.waitForSelector('.mh-tabbar, .mn-tabbar, nav', { timeout: 30000 }).catch(() => {});
    if (css) await pg.addStyleTag({ content: css });
    await pg.evaluate(() => document.fonts.ready); await pg.waitForTimeout(1600);
    await pg.screenshot({ path: path.join(OUT, `${opt}-${s}.png`) });
    await ctx.close();
  }
}
await b.close(); srv.close(); console.log('ok', OUT);
