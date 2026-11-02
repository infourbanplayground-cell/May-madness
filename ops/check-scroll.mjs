// Can the organiser actually SCROLL and reach the controls?
//
// Reported on the morning of night one: "cannot scroll and create a session".
// Every other harness here measures one screen at the top of itself — the skin
// audit scrolls once to prove the header stays put and nothing else looks at
// whether the page can scroll at all, or whether a control is reachable once
// it has. A floating nav, a fixed trim and a sticky header are three things
// that can each cover the bottom of a list, and none of them is a text run or
// a box in flow, so none of the existing checks can see them.
//
//   node ops/check-scroll.mjs                 # the live Vol.9 state
//   APP=<build> node ops/check-scroll.mjs
import { chromium } from 'playwright';
import fs from 'fs';
import http from 'http';
import path from 'path';

const SC = '/tmp/claude-0/-home-user-May-madness/0e44f0ad-a683-5f0d-9de6-9459ae328963/scratchpad';
const OUT = SC + '/vol9-scroll';
fs.mkdirSync(OUT, { recursive: true });

const APP = process.env.APP || 'national-index.html';
let app = fs.readFileSync(APP, 'utf8');

// THERE IS NO PULL-TO-REFRESH SABOTAGE HERE, and the reason is worth
// recording. The first version of this harness carried one, written to prove
// a patch that gated the gesture on the scrolling PANE rather than on
// `window.scrollY` — on the theory that the open-session screen scrolls inside
// a `fixed inset-0 overflow-y-auto` overlay, so scrollY is permanently 0 and
// every downward drag there was being read as a pull. The theory was wrong:
// `pullBlocked` already returns true whenever a session, a player card, ME or
// the login sheet is open, so the gesture was never armed on that screen at
// all. The patch was a no-op and was reverted rather than shipped, and a
// sabotage for a bug that does not exist is a check that cannot fail.
const PORT = 8132;
const ORIGIN = `http://127.0.0.1:${PORT}`;
const VENDOR = SC + '/vendor';
const FONTCSS = fs.readFileSync('brand/fonts/fonts.css', 'utf8')
  .replace(/url\(\.\//g, `url(${ORIGIN}/fonts/`);
const VERSION = fs.existsSync(APP + '.version')
  ? fs.readFileSync(APP + '.version', 'utf8').trim() : '';
// The LIVE state, so this is the screen the organiser is actually looking at.
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

const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
// hasTouch, or the page has no touch support: `new Touch()` and TouchEvent
// go nowhere and the gesture check passes against a handler it never
// reached — which is how it reported the same result with the bug present
// and with it fixed.
const pg = await browser.newPage({ viewport: { width: 430, height: 932 },
                                   hasTouch: true, isMobile: true });
await pg.route('**/unpkg.com/**', r => {
  const url = r.request().url();
  const f = /babel/.test(url) ? 'babel.js' : /react-dom/.test(url) ? 'react-dom.js' : 'react.js';
  r.fulfill({ status: 200, contentType: 'application/javascript',
              body: fs.readFileSync(path.join(VENDOR, f), 'utf8') });
});
await pg.route('**/fonts.googleapis.com/**', r =>
  r.fulfill({ status: 200, contentType: 'text/css', body: FONTCSS }));

// Signed in as admin before the first paint: the create-session control only
// exists for an admin, and a run that never signs in reports "no control" for
// the wrong reason.
await pg.addInitScript(() => {
  try {
    // ADMIN_KEY is "july-heat-admin" — a Vol.3 key carried through four
    // volumes. Guessing a per-volume name reported "no create control" for
    // entirely the wrong reason.
    localStorage.setItem('july-heat-admin', 'admin');
  } catch (e) {}
});
await pg.goto(ORIGIN + '/', { waitUntil: 'load' });
await pg.waitForSelector('nav.fixed.bottom-0', { timeout: 25000 });
await pg.evaluate(() => document.fonts.ready);
await pg.waitForTimeout(600);

const fail = [];
const F = m => fail.push(m);

// A MODAL IS MEANT TO COVER THE PAGE. The login sheet opens itself when there
// is no token, and then every control under it reports as blocked — six false
// positives that say nothing about the screen. Dismiss whatever is up before
// looking at what is reachable.
const closeModals = async () => {
  await pg.evaluate(() => {
    for (const m of document.querySelectorAll('.fixed.inset-0.z-50')) {
      const x = m.querySelector('button');
      if (x) x.click();
    }
  });
  await pg.waitForTimeout(250);
};
await closeModals();

for (const tab of ['HOME', 'SESSIONS', 'RANK', 'ME', 'PLAYERS']) {
  const hit = await pg.evaluate((t) => {
    const b = [...document.querySelectorAll('nav.fixed.bottom-0 button')]
      .find(x => (x.textContent || '').toUpperCase().includes(t));
    if (!b) return false;
    b.click();
    return true;
  }, tab);
  if (!hit) { F(`no ${tab} tab in the nav`); continue; }
  await pg.waitForTimeout(500);
  await closeModals();

  const r = await pg.evaluate(() => {
    const de = document.documentElement;
    const body = document.body;
    // 1 · CAN IT SCROLL AT ALL? An `overflow:hidden` on html or body, or a
    //     height that pins the document to the viewport, locks a list the
    //     organiser has to get to the bottom of.
    const cs = getComputedStyle(body), ds = getComputedStyle(de);
    const docH = Math.max(de.scrollHeight, body.scrollHeight);
    const viewH = window.innerHeight;
    return {
      docH, viewH,
      bodyOverflow: cs.overflowY, htmlOverflow: ds.overflowY,
      bodyPos: cs.position, bodyH: cs.height,
      needsScroll: docH > viewH + 4,
    };
  });

  let scrolled = 0;
  if (r.needsScroll) {
    scrolled = await pg.evaluate(async () => {
      window.scrollTo(0, 99999);
      await new Promise(x => requestAnimationFrame(x));
      return window.scrollY;
    });
    if (scrolled < 10) {
      F(`[${tab}] the page cannot scroll: ${r.docH}px of content in a `
        + `${r.viewH}px window, scrollY stays at ${scrolled} `
        + `(html overflow ${r.htmlOverflow}, body overflow ${r.bodyOverflow}, `
        + `body position ${r.bodyPos}, body height ${r.bodyH})`);
    }
  }

  // 2 · IS EVERY CONTROL REACHABLE? A button can be on the page, scrolled to,
  //     and still un-tappable because the floating nav or a fixed trim is
  //     drawn over it. elementFromPoint at the button's own centre is what the
  //     thumb actually hits.
  const blocked = await pg.evaluate(() => {
    const out = [];
    for (const b of document.querySelectorAll('button, a[href], [role="button"]')) {
      const q = b.getBoundingClientRect();
      if (q.width < 8 || q.height < 8) continue;
      if (q.bottom < 0 || q.top > window.innerHeight) continue;
      if (getComputedStyle(b).visibility === 'hidden') continue;
      if (b.closest('nav.fixed.bottom-0')) continue;     // the nav is itself
      const cx = q.left + q.width / 2, cy = q.top + q.height / 2;
      const hit = document.elementFromPoint(cx, cy);
      if (!hit) continue;
      if (hit === b || b.contains(hit) || hit.contains(b)) continue;
      const label = (b.textContent || '').trim().slice(0, 30) || b.className;
      const over = hit.className || hit.tagName;
      out.push(`"${label}" is covered by <${over}>`);
    }
    return [...new Set(out)];
  });
  for (const b of blocked) F(`[${tab}] ${b}`);

  await pg.screenshot({ path: `${OUT}/${tab.toLowerCase()}-bottom.png` });
  console.log(`  ${tab.padEnd(9)} ${r.docH}px in ${r.viewH}px  `
    + `scrolled to ${scrolled}  ${blocked.length ? blocked.length + ' blocked' : 'controls ok'}`);
}

// THE SCREEN INSIDE A SESSION is the long one — 16 teams, four groups, a
// bracket and a score pad — and it is the one the organiser spends the night
// on. The tab sweep above never opens it, so every check here had been
// measuring the five short screens and none of the deep one.
{
  const opened = await pg.evaluate(() => {
    const b = [...document.querySelectorAll('nav.fixed.bottom-0 button')]
      .find(x => (x.textContent || '').toUpperCase().includes('SESSIONS'));
    if (b) b.click();
    return true;
  });
  await pg.waitForTimeout(500);
  const got = await pg.evaluate(() => {
    const row = document.querySelector('.jh-mock-sess');
    if (!row) return false;
    row.click();
    return true;
  });
  if (!got) F('no session row to open on the SESSIONS screen');
  else {
    await pg.waitForTimeout(900);
    await closeModals();
    const r = await pg.evaluate(() => {
      const de = document.documentElement;
      return { docH: Math.max(de.scrollHeight, document.body.scrollHeight),
               viewH: window.innerHeight,
               bodyOverflow: getComputedStyle(document.body).overflowY,
               htmlOverflow: getComputedStyle(de).overflowY };
    });
    let scrolled = 0;
    if (r.docH > r.viewH + 4) {
      scrolled = await pg.evaluate(async () => {
        window.scrollTo(0, 99999);
        await new Promise(x => requestAnimationFrame(x));
        return window.scrollY;
      });
      if (scrolled < 10)
        F(`[SESSION] the open session cannot scroll: ${r.docH}px in ${r.viewH}px `
          + `(html ${r.htmlOverflow}, body ${r.bodyOverflow})`);
    }
    // NOT a fault: the open session is a fixed full-screen overlay with its
    // own scroll, so the DOCUMENT is legitimately one viewport tall. The first
    // version of this check called that "the screen is too short", which is
    // the wrong diagnosis for the right smell — what matters is whether the
    // inner pane scrolls, and whether a drag inside it scrolls or refreshes.

    // THE SCREEN SCROLLS INSIDE A FIXED OVERLAY, not in the window. That is a
    // legitimate pattern — but it is why `window.scrollY` is permanently 0
    // here, and the pull-to-refresh gesture arms on exactly that.
    const pane = await pg.evaluate(() => {
      const e = [...document.querySelectorAll('.fixed.inset-0')]
        .find(x => /auto|scroll/.test(getComputedStyle(x).overflowY)
                   && x.scrollHeight > x.clientHeight + 4);
      if (!e) return null;
      e.scrollTop = 99999;
      const got = e.scrollTop;
      e.scrollTop = 0;
      return { scrollH: e.scrollHeight, clientH: e.clientHeight, got };
    });
    if (pane) {
      console.log(`  ${'SESSION'.padEnd(9)} scrolls in a fixed pane: `
        + `${pane.scrollH}px in ${pane.clientH}px, scrolled to ${pane.got}`);
      if (pane.got < 10) F('[SESSION] the inner pane will not scroll either');

      // A TOUCH DRAG MUST SCROLL, NOT REFRESH. The gesture is armed when
      // `window.scrollY === 0`, which on this screen is always — so every
      // downward drag anywhere in the pane is read as a pull-to-refresh, the
      // indicator engages, and releasing re-fetches and snaps the list back
      // to the top. On a phone that is indistinguishable from "cannot scroll".
      await pg.evaluate(() => {
        const e = [...document.querySelectorAll('.fixed.inset-0')]
          .find(x => /auto|scroll/.test(getComputedStyle(x).overflowY));
        if (e) e.scrollTop = 400;         // part-way down the list
      });
      await pg.waitForTimeout(120);
      const armed = await pg.evaluate(async () => {
        // THE TOUCH MUST LAND ON WHAT A FINGER WOULD HIT. Dispatching on
        // document.body makes the walk for a scrolling ancestor find nothing
        // and fall back to the window — so the first version of this test
        // armed the gesture for entirely the wrong reason and kept reporting
        // the bug after it was fixed. elementFromPoint is the real target.
        const target = document.elementFromPoint(215, 300) || document.body;
        const t = (type, y) => {
          const touch = new Touch({ identifier: 1, target,
                                    clientX: 215, clientY: y });
          target.dispatchEvent(new TouchEvent(type, {
            bubbles: true, cancelable: true, touches: type === 'touchend' ? [] : [touch],
            changedTouches: [touch] }));
        };
        // MEASURE THE INDICATOR BEFORE AND AFTER. Its text is in the DOM at
        // rest, so "is the label present" reports armed on an untouched page
        // — the detector has to be the CHANGE in how much of it is showing.
        const strip = () => {
          const el = [...document.querySelectorAll('*')].find(x =>
            /^(PULL|RELEASE) TO REFRESH$/.test((x.textContent || '').trim()));
          if (!el) return { h: 0, missing: true };
          let e = el, h = 0;
          for (let i = 0; i < 4 && e; i++, e = e.parentElement)
            h = Math.max(h, e.getBoundingClientRect().height);
          return { h, top: el.getBoundingClientRect().top };
        };
        const before = strip();
        t('touchstart', 300);
        for (let y = 320; y <= 440; y += 20) { t('touchmove', y); }
        await new Promise(r => setTimeout(r, 150));
        const after = strip();
        t('touchend', 440);
        await new Promise(r => setTimeout(r, 100));
        return { before, after,
                 armed: !before.missing && (after.h - before.h) > 8 };
      });
      console.log(`  ${''.padEnd(9)} pull strip ${JSON.stringify(armed.before)} `
        + `-> ${JSON.stringify(armed.after)}`);
      if (armed.armed)
        F('[SESSION] a downward drag PART-WAY DOWN the list arms pull-to-refresh '
          + '— the gesture tests window.scrollY, which is always 0 on a screen '
          + 'that scrolls inside a fixed pane, so every drag is a refresh');
    }
    await pg.screenshot({ path: `${OUT}/session-bottom.png` });
  }
}

await browser.close();
srv.close();

if (fail.length) {
  console.error('\n' + fail.map(x => '  !! ' + x).join('\n'));
  console.error(`\n${fail.length} problem(s) — shots in ${OUT}`);
  process.exit(1);
}
console.log(`\nok — every screen scrolls and every control is reachable`);
