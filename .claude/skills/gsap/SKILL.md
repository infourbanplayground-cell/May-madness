---
name: gsap
description: GSAP (GreenSock) animation for this repo — timelines, eases, SplitText, CustomEase, ScrollTrigger — and how to use it in the two places it fits here: the hype films (scrubbed frame by frame through window.__seek, never played on a clock) and the live apps (UI motion, pinned CDN versions). Use when building or reworking an animation, a film cut, a reveal, or anything the user calls "better animation" or "GSAP".
---

# GSAP in this repo

GSAP **3.15.1** (released 4 Nov 2026). All of it is free under GreenSock's
standard licence, plugins included — SplitText, CustomEase, ScrollTrigger,
MorphSVG. **4.0 is in beta: do not use it** (`4.0.0-beta.*`).

Vendored copies live in `brand/vendor/gsap-3.15.1/`:
`gsap.min.js`, `ScrollTrigger.min.js`, `SplitText.min.js`, `CustomEase.min.js`.

## Rule 0 — where the files come from

- **Renderers and films (headless Chromium here): inline the vendored files.**
  Chromium in this container does not trust the agent proxy's CA, so a CDN
  `<script>` fails and the page silently has no `gsap` — the same trap that
  rendered a whole story series in Times (CLAUDE.md, the fonts). Read the
  files and inline them, the way `ops/font_bundle.py` inlines the faces.
- **Live apps (served to phones): pin the EXACT version on a CDN**, e.g.
  `https://cdn.jsdelivr.net/npm/gsap@3.15.1/dist/gsap.min.js`. Never `gsap@3`
  or bare `gsap` — the Babel @8 outage (CLAUDE.md, Critical Lessons) blanked
  every site at once because a major moved under an unpinned URL.

## Rule 1 — films are SCRUBBED, never played

Every film here is recorded by seeking each frame to an exact time
(`record-*.mjs` calls `window.__seek(t)` 30 times a second and screenshots).
A GSAP timeline must therefore be **paused** and driven by that seek. Proved
in this container: no CSS animations, identical frames on every run.

```js
gsap.registerPlugin(SplitText, CustomEase);
const tl = gsap.timeline({ paused: true, defaults: { ease: 'expo.out' } });
// ...build the whole film on tl, scenes as labels...
window.__dur = tl.duration();
window.__seek = t => tl.seek(t, false);   // false = do not suppress callbacks
```

- Build the timeline **after `document.fonts.ready`** and after any fit pass:
  SplitText measures lines and characters, and measured against the fallback
  face the splits land on the wrong letters.
- No `repeat: -1`, no `yoyo` on the master timeline, no `gsap.ticker` logic, no
  `Date.now()` — anything off the timeline is off the recording.
- `onUpdate` that writes text (count-ups) is fine: it runs on seek.
- Each scene is a label: `tl.addLabel('s2', 2.4)`. Export the scene starts
  (`tl.labels`) as `window.__scenes` so the recorder and the audio bed read
  ONE table — the same rule `build-national-double-video.py` follows.
- The recorder's checks still apply (overlap, safe area 170..1720, nothing
  under the masar trim, fonts drawn). They read the DOM at each mark, so a
  GSAP film passes or fails them exactly like a hand-written one.

## Rule 2 — the motion language (what "not like a child made it" meant)

The owner rejected a cut whose background pulsed on every beat and where every
element faded up the same way. Hold to this:

- **The ground never moves.** Pattern tiles, trims and backgrounds are a wall.
  No scaling or brightening on the beat.
- **Display type is revealed, not faded**: SplitText into lines or words,
  each inside a mask, `yPercent: 100 → 0`, stagger 0.04–0.08, `expo.out`
  0.6–0.8s. Set `mask: 'lines'` on the split.
- **Surfaces open**: `clipPath` from `inset(0 100% 0 0 round 999px)` to
  `inset(0 0% 0 0 round 999px)` for pills; from the bottom for arches.
  Keep negative insets once open, or a box-shadow ring gets clipped.
- **Small type fades** (opacity + 10px), nothing more.
- **One flourish per scene**, played once (`back.out(1.6)` on a badge).
- **Every scene clears out** before the next lands: 0.12–0.16s, up and away.
- Eases: `expo.out` arrivals, `power2.in` exits, `none` for slow drift.
  A custom ease belongs in CustomEase, named once and reused.

## Rule 3 — in the live apps

- The apps are React via Babel standalone. Use `gsap.context()` inside a
  `useEffect` and `ctx.revert()` in its cleanup, or animations leak across
  screens:
  ```js
  React.useEffect(() => {
    const ctx = gsap.context(() => { gsap.from('.row', { y: 12, opacity: 0, stagger: .03 }); }, ref);
    return () => ctx.revert();
  }, []);
  ```
- Respect `prefers-reduced-motion` with `gsap.matchMedia()`.
- **Never animate the court-side scoring tools** (score pad, lock button, the
  night's tabs) — the scorer needs them still. Motion belongs on arrivals:
  a result locking, the champions plate, the clips sheet.
- **Do not ship motion into a live night** (CLAUDE.md: no deploys while a
  session is being played).
- ScrollTrigger inside the night pane must set `scroller:` to the pane
  (`.fixed.inset-0`) — the deep screens scroll inside it, not the window,
  the same reason the header-fold listener runs in capture phase.

## Quick reference

```js
gsap.to(el, { x: 100, duration: .6, ease: 'expo.out' });
gsap.from(el, { opacity: 0, y: 20 });
gsap.fromTo(el, { scale: .6 }, { scale: 1, ease: 'back.out(1.6)' });
tl.to(a, {...}, '<')        // with the previous
tl.to(b, {...}, '<0.1')     // 0.1s after the previous starts
tl.to(c, {...}, '-=0.2')    // overlap the previous end by 0.2s
tl.to(d, {...}, 's3+=0.4')  // relative to a label
gsap.set(el, { clipPath: 'inset(0 100% 0 0)' });
const s = SplitText.create(el, { type: 'lines,words', mask: 'lines' });
CustomEase.create('settle', 'M0,0 C0.16,1 0.3,1 1,1');
gsap.utils.toArray('.row').forEach((r, i) => tl.from(r, { x: -40, opacity: 0 }, i * 0.08));
```
