// CAN THE ORGANISER REACH EVERY CONTROL, ON THE PHONE THEY ACTUALLY HOLD?
//
// Reported twice: "cannot scroll and create a session", then "there is a lot
// of issues with scrolling, buttons are not reachable in some pages". The
// first version of this harness reported everything fine, and the reason it
// was wrong is the whole lesson here:
//
//   · IT RAN AT ONE VIEWPORT, 430x932 — the largest phone sold. The chrome on
//     this app is a FIXED cost: a 128px header and a 68px floating nav, 196px
//     whatever the screen. On a 932px phone that is 21% of the glass; on a
//     667px iPhone SE it is 29%, and the layouts that fit on the big one stop
//     fitting. Every fault found here is invisible at 430x932.
//   · IT ASKED "is this control covered RIGHT NOW", at one scroll position.
//     The honest question is whether a control can be BROUGHT INTO VIEW and
//     tapped at all — so each one is scrolled into the free band between the
//     chrome and then hit-tested where a thumb would land.
//   · IT NEVER OPENED A SHEET. Every modal in this app is `maxHeight:<n>vh`
//     over `overflowY:auto`, and that is exactly the shape that puts an action
//     button under the fold on a short screen. The five tab screens were
//     measured and the dozen sheets over them were not.
//   · IT NEVER CHECKED THE BOTTOM OF A LIST CLEARS THE NAV. The nav is
//     `fixed bottom-0`, so it is not in flow and nothing about it widens the
//     document — a list whose last row ends under it scrolls to its end with
//     the last row permanently half-hidden, and no overflow check sees that.
//
//   node ops/check-scroll.mjs
//   APP=<build> node ops/check-scroll.mjs      # another build
//   ONLY=SESSIONS node ops/check-scroll.mjs    # one screen
//   VP=375x667 node ops/check-scroll.mjs       # one size
//   SABOTAGE=nopad|navcover|shortsheet         # proofs that it can fail
import { chromium } from 'playwright';
import fs from 'fs';
import http from 'http';
import path from 'path';

const SC = '/tmp/claude-0/-home-user-May-madness/0e44f0ad-a683-5f0d-9de6-9459ae328963/scratchpad';
const APP = process.env.APP || 'national-index.html';
const SAB = process.env.SABOTAGE || '';
const ONLY = (process.env.ONLY || '').toUpperCase();
const OUT = SC + (APP !== 'national-index.html' || SAB
                  ? '/vol9-scroll-sabotage' : '/vol9-scroll');
fs.mkdirSync(OUT, { recursive: true });

let app = fs.readFileSync(APP, 'utf8');

// ── sabotages, each reproducing a fault this harness exists to catch ────────
// EVERY SABOTAGE HERE IS A MARKUP EDIT, NOT A STYLE RULE, and that is the
// lesson of the first set: all three were written as CSS appended to the skin
// and all three were silently lost — Tailwind's runtime utilities won, and
// three checks reported a clean page against a build that was supposed to be
// broken. A sabotage that does not apply is worse than no sabotage: it is a
// green tick over an untested assertion. Each one below changes a class or an
// inline style the app itself wrote, so it cannot be overridden by anything.
const sab = (what, from, to) => {
  if (!app.includes(from)) throw new Error(`sabotage anchor gone: ${what} (${from})`);
  const before = app;
  app = app.split(from).join(to);
  if (app === before) throw new Error(`sabotage ${what} changed nothing`);
};
if (/nopad/.test(SAB)) {
  // Take the bottom padding off the scrolling screens, so the last row of
  // every list ends underneath the floating nav with nowhere left to scroll.
  sab('nopad', 'max-w-3xl mx-auto px-4 py-4 pb-24', 'max-w-3xl mx-auto px-4 py-4');
}
if (/navcover/.test(SAB)) {
  // Make the floating nav far taller without giving the content any more
  // room — what any change to the nav does when the clearance is a number
  // written somewhere else.
  // THROUGH THE INLINE STYLE, not a class: the skin sets `padding: 5px
  // !important` on the nav, so a Tailwind padding utility is thrown away and
  // the first version of this sabotage changed the page by exactly nothing
  // while reporting a clean run. min-height is not set anywhere, so nothing
  // can override it.
  sab('navcover',
      '<nav className="fixed bottom-0 inset-x-0 z-30 border-t border-stone-800/80 backdrop-blur-xl" style={{ background: "rgba(158,21,32,0.96)" }}>',
      '<nav className="fixed bottom-0 inset-x-0 z-30 border-t border-stone-800/80 backdrop-blur-xl" style={{ background: "rgba(158,21,32,0.96)", minHeight: 210 }}>');
}
if (/shortsheet/.test(SAB)) {
  // A sheet that does not scroll: the classic way an action button ends up
  // under the fold on a short phone.
  app = app.replace(/maxHeight: "94vh", overflowY: "auto"/g,
                    'maxHeight: "none", overflowY: "visible"');
  app = app.replace(/maxHeight:"90vh",overflowY:"auto"/g,
                    'maxHeight:"none",overflowY:"visible"');
}

const PORT = 8132;
const ORIGIN = `http://127.0.0.1:${PORT}`;
const VENDOR = SC + '/vendor';
const FONTCSS = fs.readFileSync('brand/fonts/fonts.css', 'utf8')
  .replace(/url\(\.\//g, `url(${ORIGIN}/fonts/`);
const VERSION = fs.existsSync(APP + '.version')
  ? fs.readFileSync(APP + '.version', 'utf8').trim() : '';
// THE LIVE STATE. Vol.9 has a played night in it now — 16 teams, 24 group
// matches, a finished bracket — and the long screens only exist when there is
// something on them. Against an empty season every list is three rows and
// every check passes having seen nothing.
const stateFile = fs.existsSync(SC + '/na-live.json') ? '/na-live.json' : '/na.json';
const state = fs.readFileSync(SC + stateFile, 'utf8');
const photos = fs.existsSync(SC + '/na-photos.json')
  ? fs.readFileSync(SC + '/na-photos.json', 'utf8') : '{"ok":true,"photos":{}}';

const srv = http.createServer({ maxHeaderSize: 1 << 20 }, (req, res) => {
  const u = (req.url || '/').split('?')[0];
  const json = b => { res.writeHead(200, { 'Content-Type': 'application/json' }); res.end(b); };
  if (u === '/version.txt') { res.writeHead(200); return res.end(VERSION); }
  if (u === '/state') return json(state);
  if (u === '/photos') return json(photos);
  if (u === '/session-photos' || u === '/history') return json('{"ok":true,"photos":{}}');
  if (u.startsWith('/fonts/')) {
    const f = path.join('brand/fonts', path.basename(u));
    if (fs.existsSync(f)) { res.writeHead(200, { 'Content-Type': 'font/woff2' });
                            return res.end(fs.readFileSync(f)); }
  }
  const bn = path.basename(u);
  if (/\.(png|webp|jpe?g|svg)$/.test(bn)) {
    for (const d of ['brand/national', 'brand/blackout', 'assets']) {
      const f = path.join(d, bn);
      if (fs.existsSync(f)) {
        res.writeHead(200, { 'Content-Type': 'image/' + bn.split('.').pop() });
        return res.end(fs.readFileSync(f));
      }
    }
    res.writeHead(404); return res.end();
  }
  res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
  res.end(app);
}).listen(PORT);

// ── the page-side audit ─────────────────────────────────────────────────────
// Serialised into the browser once and reused, because it is the substance of
// this file and having two copies of it is how two checks drift apart.
const AUDIT = function () {
  const vh = window.innerHeight, vw = window.innerWidth;

  // What is permanently drawn over the page. A full-screen layer is NOT
  // chrome — it is a sheet, and the things under it are meant to be covered.
  const chrome = [];
  for (const e of document.querySelectorAll('*')) {
    const cs = getComputedStyle(e);
    if (cs.position !== 'fixed' && cs.position !== 'sticky') continue;
    if (cs.visibility === 'hidden' || Number(cs.opacity) < 0.05) continue;
    if (cs.pointerEvents === 'none') continue;
    const q = e.getBoundingClientRect();
    if (q.height <= 0 || q.width <= 0) continue;
    if (q.height > vh * 0.7) continue;
    chrome.push({ e, q, cls: String(e.className || e.tagName).slice(0, 34) });
  }
  // The free band between anything pinned at the top and anything at the
  // bottom. This is the only part of the glass a control can be tapped in.
  let safeTop = 0, safeBottom = vh;
  for (const c of chrome) {
    if (c.q.top <= 2 && c.q.bottom < vh * 0.5) safeTop = Math.max(safeTop, c.q.bottom);
    // THE NAV IS NOT FLUSH WITH THE BOTTOM OF THE GLASS. It floats, with a
    // gap under it — its box ends 14px short of the viewport. A test for
    // `bottom >= vh - 4` therefore does not see it at all, which is how the
    // first run of this check reported a free band reaching the foot of the
    // screen while the nav sat in the middle of it and the last row of every
    // list was hidden behind it.
    if (c.q.top > vh * 0.5 && c.q.bottom > vh - 90) safeBottom = Math.min(safeBottom, c.q.top);
  }
  const inChrome = (el) => chrome.some(c => c.e === el || c.e.contains(el));

  // THE TOPMOST FULL-SCREEN LAYER OWNS THE SCREEN. When a sheet is open the
  // controls behind it are MEANT to be covered, and reporting each of them is
  // a page of false positives that buries the one real finding. Audit only
  // what is inside the layer that is actually on top.
  let layer = null, layerZ = -1;
  for (const e of document.querySelectorAll('*')) {
    const cs = getComputedStyle(e);
    if (cs.position !== 'fixed') continue;
    const q = e.getBoundingClientRect();
    if (q.height < vh * 0.5 || q.width < vw * 0.8) continue;
    if (cs.visibility === 'hidden' || Number(cs.opacity) < 0.05) continue;
    if (cs.pointerEvents === 'none') continue;
    const z = Number(cs.zIndex) || 0;
    if (z >= layerZ) { layerZ = z; layer = e; }
  }

  // AND IT SITS ABOVE THE CHROME, so the chrome stops bounding anything. The
  // sheets are z-80 to z-95 and the nav is z-30: an action button at y=622 is
  // over the nav, not under it, and perfectly tappable. Measuring it against
  // the page's free band reported every sheet's own footer as unreachable.
  const chromeZ = Math.max(0, ...chrome.map(c => Number(getComputedStyle(c.e).zIndex) || 0));
  const sheetOwnsScreen = !!layer && layerZ > chromeZ;
  if (sheetOwnsScreen) {
    const lq = layer.getBoundingClientRect();
    safeTop = Math.max(0, lq.top);
    safeBottom = Math.min(vh, lq.bottom);
    // ...except anything the SHEET itself pins inside its own box.
    for (const c of chrome) {
      if (!layer.contains(c.e)) continue;
      if (c.q.top <= safeTop + 2 && c.q.bottom < safeBottom * 0.6)
        safeTop = Math.max(safeTop, c.q.bottom);
    }
  }

  const scrollerOf = (el) => {
    for (let e = el.parentElement; e; e = e.parentElement) {
      const cs = getComputedStyle(e);
      if (/auto|scroll/.test(cs.overflowY) && e.scrollHeight > e.clientHeight + 2) return e;
    }
    return null;
  };

  // 1 · EVERY SCROLLING REGION MUST REACH ITS OWN END. A pane whose content
  //     is taller than it is and which will not move is a dead screen.
  const panes = [];
  for (const e of document.querySelectorAll('*')) {
    const cs = getComputedStyle(e);
    if (!/auto|scroll/.test(cs.overflowY)) continue;
    if (e.scrollHeight <= e.clientHeight + 4) continue;
    const before = e.scrollTop;
    e.scrollTop = e.scrollHeight;
    const got = e.scrollTop;
    e.scrollTop = before;
    panes.push({ cls: String(e.className || e.tagName).slice(0, 34),
                 scrollH: e.scrollHeight, clientH: e.clientHeight,
                 reached: got >= e.scrollHeight - e.clientHeight - 3 });
  }

  // 2 · THE CONTENT MUST CLEAR THE FLOATING NAV. The nav is fixed, so it adds
  //     nothing to the document height — a list whose last row ends beneath it
  //     scrolls all the way to its end with that row still half-hidden, and no
  //     overflow or clipping check in this repo can see it.
  window.scrollTo(0, 999999);
  for (const e of document.querySelectorAll('*')) {
    const cs = getComputedStyle(e);
    if (/auto|scroll/.test(cs.overflowY) && e.scrollHeight > e.clientHeight + 4)
      e.scrollTop = e.scrollHeight;
  }
  const scroller = document.scrollingElement;
  const atBottom = scroller.scrollTop >= scroller.scrollHeight - vh - 3;
  let lowest = null, lowestCls = '';
  for (const e of document.querySelectorAll('div,section,article,li,button,p,h1,h2,h3,span,img,table')) {
    if (inChrome(e)) continue;
    const cs = getComputedStyle(e);
    if (cs.visibility === 'hidden' || cs.display === 'none' || Number(cs.opacity) < 0.05) continue;
    const q = e.getBoundingClientRect();
    if (q.height < 4 || q.width < 4) continue;
    if (q.top > vh || q.bottom < 0) continue;
    // Only things that carry ink of their own: a wrapper's box often ends
    // exactly at the document's end and says nothing about what is visible.
    const hasInk = e.childElementCount === 0
      || cs.backgroundColor !== 'rgba(0, 0, 0, 0)'
      || cs.borderBottomWidth !== '0px';
    if (!hasInk) continue;
    if (!lowest || q.bottom > lowest) { lowest = q.bottom; lowestCls = String(e.className || e.tagName).slice(0, 34); }
  }

  // ...and whether the NAV is what is painted over that lowest ink. The nav
  // floats with a gap beneath it, so a list can end in that gap and look
  // clipped; and a sheet can run to the foot of the glass and be perfectly
  // clear, because it paints above. Only a hit test tells the two apart.
  let navCovers = null, navProbeY = 0, navCoverDepth = 0;
  {
    const navEl = document.querySelector('nav.fixed.bottom-0');
    if (navEl) {
      const nq = navEl.getBoundingClientRect();
      // elementsFromPoint gives the WHOLE PAINT STACK at a point, which is the
      // only way to ask "is the nav on top, and is there page content directly
      // under it". elementFromPoint alone answers the first half and a box
      // comparison answers neither — a sheet legitimately runs to the foot of
      // the glass ABOVE the nav, and that is not a fault.
      for (const fy of [0.18, 0.5, 0.82]) {
        for (const fx of [0.5, 0.25, 0.75]) {
          const y = Math.round(nq.top + nq.height * fy);
          const x = Math.round(vw * fx);
          if (y < 1 || y > vh - 1) continue;
          const stack = document.elementsFromPoint(x, y);
          const iNav = stack.findIndex(e => e === navEl || navEl.contains(e));
          if (iNav < 0) continue;                       // nav is not on top here
          for (const e of stack.slice(iNav + 1)) {
            if (e === document.body || e === document.documentElement) break;
            if (navEl.contains(e)) continue;
            if (inChrome(e)) continue;
            const cs2 = getComputedStyle(e);
            // Something with ink of its own, not a transparent wrapper.
            const inked = e.childElementCount === 0
              || cs2.backgroundColor !== 'rgba(0, 0, 0, 0)'
              || cs2.backgroundImage !== 'none';
            if (!inked) continue;
            navCovers = String(e.className || e.tagName).slice(0, 34);
            navProbeY = y;
            navCoverDepth = Math.round(e.getBoundingClientRect().bottom - nq.top);
            break;
          }
          if (navCovers) break;
        }
        if (navCovers) break;
      }
    }
  }

  // 3 · EVERY CONTROL MUST BE REACHABLE. Scroll it into the middle of the free
  //     band, then hit-test where a thumb lands. A control that cannot be put
  //     in the band at all is the real "button not reachable".
  // THE THING UNDER THE THUMB ONLY HAS TO ROUTE TO THE SAME CONTROL. An icon
  // inside a button is what elementFromPoint returns, and a label drawn over
  // its own input still activates it — reporting those is a page of noise
  // that buries the one real finding.
  const same = (b, hit) => {
    if (hit === b || b.contains(hit) || hit.contains(b)) return true;
    const c = hit.closest && hit.closest('button, a[href], label, [role="button"]');
    if (c && (c === b || b.contains(c) || c.contains(b))) return true;
    if (hit.tagName === 'LABEL' && hit.control === b) return true;
    return false;
  };

  const unreachable = [];
  const controls = [];
  for (const b of document.querySelectorAll('button, a[href], input, select, textarea, [role="button"]')) {
    const cs = getComputedStyle(b);
    if (cs.visibility === 'hidden' || cs.display === 'none' || Number(cs.opacity) < 0.05) continue;
    if (b.disabled) continue;
    const q0 = b.getBoundingClientRect();
    if (q0.width < 8 || q0.height < 8) continue;
    // Behind the open sheet, and so legitimately covered.
    if (layer && !layer.contains(b) && !inChrome(b)) continue;
    if (layer && inChrome(b) && layerZ > 40) continue;
    controls.push(b);
  }
  // NO Z-ORDER ARITHMETIC. The first version of this decided whether a sheet
  // "owned the screen" by comparing z-indexes and then suppressed the chrome —
  // and it was wrong, because a stacking context three ancestors up can put a
  // z-30 nav over a z-80 sheet. The only thing that settles it is the question
  // the thumb asks: at this point on the glass, which element gets the tap?
  //
  // So: scroll it as far into the clear as its own scroller allows, then probe
  // NINE points across its box. A control is reachable if any of them routes
  // back to it — which is also the honest standard, since a half-covered
  // button is still tappable on the half that shows.
  const probe = (b) => {
    const q = b.getBoundingClientRect();
    if (q.width < 1 || q.height < 1) return null;
    for (const fy of [0.5, 0.25, 0.75]) {
      for (const fx of [0.5, 0.2, 0.8]) {
        const x = Math.min(Math.max(q.left + q.width * fx, 1), vw - 1);
        const y = q.top + q.height * fy;
        if (y < 1 || y > vh - 1) continue;
        const hit = document.elementFromPoint(x, y);
        if (hit && same(b, hit)) return { ok: true };
      }
    }
    const cx = Math.min(Math.max(q.left + q.width / 2, 1), vw - 1);
    const cy = Math.min(Math.max(q.top + q.height / 2, 1), vh - 1);
    const hit = document.elementFromPoint(cx, cy);
    return { ok: false, q, hit };
  };

  for (const b of controls) {
    const label = ((b.textContent || '').trim() || b.getAttribute('aria-label')
                   || b.getAttribute('placeholder') || String(b.className) || b.tagName)
                  .replace(/\s+/g, ' ').slice(0, 32);
    let r = probe(b);
    if (r && r.ok) continue;
    // Not reachable where it sits. Try bringing it into the clear — the middle
    // of the free band, then the band's top and bottom edges, through whatever
    // scrolls it.
    const sc = scrollerOf(b);
    for (const want of [(safeTop + safeBottom) / 2, safeTop + 30, safeBottom - 30]) {
      const q = b.getBoundingClientRect();
      const delta = (q.top + q.height / 2) - want;
      if (sc) sc.scrollTop += delta; else window.scrollBy(0, delta);
      r = probe(b);
      if (r && r.ok) break;
    }
    if (r && r.ok) continue;
    const q = b.getBoundingClientRect();
    const where = `its box is y=${Math.round(q.top)}..${Math.round(q.bottom)} of ${vh}`;
    if (!r || !r.hit) {
      unreachable.push({ label, why: `cannot be brought onto the screen — ${where}` });
    } else if (q.bottom < 1 || q.top > vh - 1) {
      unreachable.push({ label, why: `will not scroll into view — ${where}`,
                         scroller: sc ? String(sc.className).slice(0, 28) : 'the window' });
    } else {
      unreachable.push({ label, why: `is covered everywhere a thumb can land, by `
        + `<${String(r.hit.className || r.hit.tagName).slice(0, 34)}> — ${where}` });
    }
  }

  return {
    vh, sheetOwnsScreen,
    safeTop: Math.round(safeTop), safeBottom: Math.round(safeBottom),
    chrome: chrome.map(c => `${c.cls} ${Math.round(c.q.top)}..${Math.round(c.q.bottom)}`),
    panes, nControls: controls.length, unreachable,
    atBottom, lowest: lowest == null ? null : Math.round(lowest), lowestCls,
    navCovers, navProbeY, navCoverDepth,
    navTop: Math.round(safeBottom),
    docH: scroller.scrollHeight,
  };
};

const VIEWPORTS = process.env.VP
  ? [process.env.VP.split('x').map(Number)]
  : [[360, 640], [375, 667], [390, 844]];

// THE ORGANISER'S SCREEN IS A DIFFERENT SCREEN. A visitor sees five read-only
// tabs; the person running the night sees + NEW, ANNOUNCE, SIGNUP, the score
// pads and the admin sheets — which is most of the controls in the app and all
// of the ones the complaint was about. The role is held in local storage under
// a Vol.3 key that four volumes have carried; setting it renders the admin UI.
// It also raises the "not saving" banner, because there is no token behind it
// — which is a real state the app is designed for, and the banner opens the
// sign-in sheet over the nav. The sheet is dismissed before the audit, exactly
// as the organiser would dismiss it.
const ADMIN_KEY = 'july-heat-admin';
const ROLES = (process.env.ROLE ? [process.env.ROLE] : ['visitor', 'admin']);

const fail = [];
const F = m => fail.push(m);

for (const [width, height] of VIEWPORTS) {
for (const role of ROLES) {
  const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
  const pg = await browser.newPage({ viewport: { width, height },
                                     hasTouch: true, isMobile: true });
  await pg.route('**/unpkg.com/**', r => {
    const url = r.request().url();
    const f = /babel/.test(url) ? 'babel.js' : /react-dom/.test(url) ? 'react-dom.js' : 'react.js';
    r.fulfill({ status: 200, contentType: 'application/javascript',
                body: fs.readFileSync(path.join(VENDOR, f), 'utf8') });
  });
  await pg.route('**/fonts.googleapis.com/**', r =>
    r.fulfill({ status: 200, contentType: 'text/css', body: FONTCSS }));
  if (role === 'admin')
    await pg.addInitScript((k) => { try { localStorage.setItem(k, 'admin'); } catch (e) {} }, ADMIN_KEY);
  await pg.goto(ORIGIN + '/', { waitUntil: 'load' });
  await pg.waitForSelector('nav.fixed.bottom-0', { timeout: 25000 });
  await pg.evaluate(() => document.fonts.ready);
  await pg.waitForTimeout(700);

  // Dismiss the sign-in sheet the way the organiser does — its own × — and
  // check it CAN be dismissed. A sheet that opens itself over the nav and
  // cannot be closed is a trapped app, which is indistinguishable from
  // "nothing is reachable".
  const dismiss = async () => {
    for (let i = 0; i < 4; i++) {
      const closed = await pg.evaluate(() => {
        const ov = [...document.querySelectorAll('*')].find(e => {
          const cs = getComputedStyle(e);
          return cs.position === 'fixed'
            && e.getBoundingClientRect().height > window.innerHeight * 0.5
            && /sign|pin|unlock/i.test(e.textContent || '');
        });
        if (!ov) return 'none';
        const x = [...ov.querySelectorAll('button')].find(b => {
          const t = (b.textContent || '').trim();
          return t === '' || /^[×✕✖x]$/i.test(t) || /close/i.test(b.getAttribute('aria-label') || '');
        });
        if (!x) return 'no-close';
        x.click();
        return 'clicked';
      });
      if (closed === 'none') return true;
      if (closed === 'no-close') {
        F(`[${width}px ${role}] the sign-in sheet covers the screen and has no way to close it`);
        return false;
      }
      await pg.waitForTimeout(350);
    }
    F(`[${width}px ${role}] the sign-in sheet will not close`);
    return false;
  };
  await dismiss();

  console.log(`\n── ${width}x${height} · ${role} ──`);

  const look = async (name) => {
    if (ONLY && !name.toUpperCase().includes(ONLY)) return null;
    // THE SIGN-IN SHEET RE-OPENS ITSELF. With a role in local storage and no
    // token behind it every save fails, the banner fires and the banner opens
    // the sheet — so it is back over the screen a second after it was closed.
    // That is the app behaving as designed (CLAUDE.md records why the banner
    // opens it), but it means the screen underneath is only measurable with
    // the sheet dismissed, and dismissing it once at start-up is not enough.
    // Opening a SHEET deliberately is the one case where it must stay.
    if (!/^SHEET /.test(name)) await dismiss();
    await pg.evaluate(() => window.scrollTo(0, 0));
    await pg.waitForTimeout(220);
    const r = await pg.evaluate(AUDIT);
    const shot = `${OUT}/${role}-${name.toLowerCase().replace(/[^a-z0-9]+/g, '-')}-${width}.png`;
    await pg.screenshot({ path: shot });

    const bad = [];
    for (const p of r.panes)
      if (!p.reached) bad.push(`the pane <${p.cls}> will not scroll to its end `
        + `(${p.scrollH}px of content in ${p.clientH}px)`);
    // The last ink on the screen, at the very bottom of the scroll, must clear
    // the floating nav.
    // NOT GEOMETRY. A sheet legitimately runs to the foot of the glass and
    // sits ABOVE the nav, so "its box ends below the nav's top" says nothing —
    // it reported the announcement sheet, whose Copy button is plainly clear,
    // on every size. What matters is what is actually painted there, so the
    // page asks elementFromPoint just under the nav's top edge and reports
    // only when the NAV is what answers.
    if (r.navCovers)
      bad.push(`at the very bottom of the scroll the content is still behind the `
        + `floating nav — <${r.navCovers}> answers at y=${r.navProbeY}, `
        + `${r.navCoverDepth}px down into the content`);
    for (const u of r.unreachable) bad.push(`"${u.label}" ${u.why}`);

    console.log(`  ${name.padEnd(18)} ${r.nControls} controls  band ${r.safeTop}..${r.safeBottom}`
      + `  doc ${r.docH}  ${bad.length ? bad.length + ' PROBLEM(S)' : 'ok'}`);
    for (const b of bad) { console.log(`     !! ${b}`); F(`[${width}px ${role} ${name}] ${b}`); }
    return r;
  };

  const tab = async (t) => {
    const ok = await pg.evaluate((t) => {
      const b = [...document.querySelectorAll('nav.fixed.bottom-0 button')]
        .find(x => (x.textContent || '').trim().toUpperCase() === t);
      if (!b) return false;
      b.click();
      return true;
    }, t);
    if (!ok) F(`[${width}px ${role}] there is no ${t} tab in the nav`);
    await pg.waitForTimeout(550);
    return ok;
  };

  for (const t of ['HOME', 'SESSIONS', 'RANK', 'ME', 'PLAYERS']) {
    if (await tab(t)) await look(t);
  }

  // ── the sheets ────────────────────────────────────────────────────────────
  // Every one is `maxHeight:<n>vh` over `overflowY:auto`, which is the shape
  // that hides an action button under the fold on a short phone. None had ever
  // been opened by a harness.
  await tab('SESSIONS');
  for (const label of ['ANNOUNCE', 'SIGNUP', 'FORMAT']) {
    const opened = await pg.evaluate((l) => {
      const b = [...document.querySelectorAll('button')]
        .find(x => (x.textContent || '').trim().toUpperCase() === l);
      if (!b) return false;
      b.click();
      return true;
    }, label);
    if (!opened) continue;
    await pg.waitForTimeout(600);
    await look('SHEET ' + label);
    await pg.keyboard.press('Escape').catch(() => {});
    await pg.evaluate(() => {
      const ov = [...document.querySelectorAll('*')].find(e => {
        const cs = getComputedStyle(e);
        return cs.position === 'fixed' && e.getBoundingClientRect().height > window.innerHeight * 0.5;
      });
      if (ov) ov.click();
    });
    await pg.waitForTimeout(450);
  }

  // ── the night ─────────────────────────────────────────────────────────────
  // The screen the organiser spends the whole evening on, and the only long
  // one that scrolls inside a fixed pane rather than in the window.
  await tab('SESSIONS');
  const opened = await pg.evaluate(() => {
    const r = document.querySelector('.jh-mock-sess');
    if (!r) return false;
    r.click();
    return true;
  });
  if (!opened) F(`[${width}px ${role}] there is no session row to open on SESSIONS`);
  else {
    await pg.waitForTimeout(1000);
    await look('SESSION');
    // its own sub-screens
    const subs = await pg.evaluate(() => [...new Set([...document.querySelectorAll('button')]
      .map(b => (b.textContent || '').trim())
      .filter(t => /^(GROUPS|TEAMS|BRACKET|RECAP|PHOTOS|MVP|KNOCKOUT|TABLE)$/i.test(t)))]);
    for (const s of subs) {
      await pg.evaluate((s) => {
        const b = [...document.querySelectorAll('button')]
          .find(x => (x.textContent || '').trim().toUpperCase() === s.toUpperCase());
        if (b) b.click();
      }, s);
      await pg.waitForTimeout(600);
      await look('SESSION/' + s.toUpperCase());
    }
  }

  await browser.close();
}
}

srv.close();

if (fail.length) {
  console.error(`\n${fail.length} problem(s):`);
  for (const f of fail) console.error('  !! ' + f);
  console.error(`\nshots in ${OUT}`);
  process.exit(1);
}
console.log(`\nok — every screen scrolls and every control is reachable  (${OUT})`);
