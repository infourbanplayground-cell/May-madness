# Handoff: September Surge (Vol.7 re-skin)

## Overview

`attack.urbanpadel.om` is a single-file React app for Urban Playground's monthly padel
series. Each volume re-skins the same app: **structure and scoring stay, palette / type /
motif change.** Vol.6 was August Attack. This handoff covers Vol.7, September Surge.

Two separate pieces of work are bundled here. They are independent — do either, both, or
one then the other:

| | What | Status |
|---|---|---|
| **A** | UX fixes to HOME, RANK and SESSIONS | **already implemented** in `index-v2.html` — review and ship |
| **B** | The September Surge skin | **specified, not implemented** — this is the build |

---

## About the design files

The files in this bundle are **design references created in HTML** — prototypes showing
intended look and behaviour, not production code to paste in wholesale.

The one exception is `index-v2.html`, which **is** the real application file, already
patched. Treat it as the working baseline, not as a reference.

The target codebase is unusual and the constraint matters: the entire app is **one
self-contained `index.html`** — React, ReactDOM and Babel loaded from CDN, JSX compiled in
the browser, state in `localStorage`, styles in a stack of append-only `<style>` blocks at
the bottom of the file. There is no build step, no npm, no bundler. **Do not introduce
one.** Every change must land inside that single file. This is deliberate: the organiser
deploys by uploading one file.

## Fidelity

**High-fidelity.** Colours, type, spacing, easing curves and motif geometry are all final
and exact. `September Surge - Design Language.html` is the specification; match it.

The one thing that is *not* final: the **Surge wordmark and emblem PNGs do not exist yet.**
The August artwork (`assets/aa-wordmark.png`, `assets/aa-emblem.png`) is still in place.
See *Assets* below.

---

# Part A — UX changes already in `index-v2.html`

These are done. Listed so you know what changed and can review it, not so you can rebuild it.

1. **Payload: 1.63 MB → 807 KB.** The same 317 KB logo was base64-embedded three times.
   Now embedded once as `UP_LOGO_FULL`; `UP_LOGO_ICON` aliases it and the inline `<img>`
   references it. `'Rajdhani'` was named in three font stacks but never loaded — removed,
   so those rules now honestly declare the Archivo they were already rendering.

2. **HOME rebuilt in priority order.** Was: two logos, tagline, schedule chip, then the
   fold ended. Now: slim brand band → next session with the only red CTA on the screen →
   your standing → series progress + prize → top three → rules folded behind a toggle.
   The rules JSX is the original markup, moved and wrapped, not rewritten.

3. **"Who am I".** `MePickerModal` writes a player id to `localStorage` under `aa-me-player`.
   No account, no password, device-local. Drives the standing card on HOME and the pinned
   row on RANK. `useMe()` is the hook.

4. **`NEXT UP` fixed.** Was hardcoded to a session already marked done. Now targets the
   first non-completed session. Progress reads `done / max(9, sessions.length)` via
   `PLANNED_SESSIONS`.

5. **RANK.** Search field, your row pinned beneath it, `ThinRow` for ranks 4+ (rank, name,
   win %, points — no photo, no corner ticks, no pill strip), the 0–3 point tail collapsed
   behind a disclosure, biggest-climber demoted from a striped banner to a one-line note.

6. **SESSIONS.** Back arrow removed from a tab root. `ANNOUNCE` and `SIGNUP` gated behind
   `isAdmin`; `FORMAT` stays public.

### Two things Part A deliberately did not do

- **Publishing all nine session slots.** `NEXT UP` and the progress bar both resolve
  correctly the moment Session 3 is created. Pre-creating nine sessions is data entry for
  the organiser, not a code change.
- **The `/recovery-dump` script** at the top of the file POSTs the visitor's entire local
  state plus user agent to the server on every load, for every visitor. Left untouched
  because its ownership is unclear. **Raise this before shipping.**

---

# Part B — the September Surge skin

## The idea

Attack was a single hard strike: static plates, four corner ticks, a tactical grid, warm red
leading cool cyan. Surge is a rising current — the series restarting after summer, energy
building rather than exploding once. The language becomes **directional and kinetic**, and
the temperature **inverts**: cyan leads, amber supports, at the same roughly 3:1 ratio
August ran red over cyan.

Test of success: someone glancing at a screenshot can name the volume without reading a word.

## Design tokens

### Colour

| Token | Hex | Use |
|---|---|---|
| Deep Current | `#0A0F14` | Page base. Cooler and darker than Court Black, almost teal-black |
| Void | `#050709` | Nav bar, gradient floor, card plate |
| Surge Cyan | `#00E5FF` | **Primary accent — the lead colour now, not the supporting one** |
| Voltage White | `#F4F9FA` | Primary text. Cooler than Chalk, leaning toward the cyan |
| Deep Steel | `#5C6B78` | Labels, inactive states, letterspaced kickers |
| Steel Text | `#8A9BA8` | Prose-length secondary text — see note |
| Strike Amber | `#FF9E1B` | The single warm accent. Live-now and urgency states **only** |

**Contrast note.** Deep Steel on Deep Current is ~3.3:1 — fine for the bold letterspaced
kickers it is specified for, under the 4.5:1 floor for anything running as sentences.
`#8A9BA8` is the second steel for body-length secondary text. Everything else in the
palette clears comfortably. This is an addition to the original spec, not a deviation.

**Gold stays out of the palette**, same rule as August. Medal chips use the
cyan / `#C3D0D8` / steel ladder.

### Type

- **Display** — Archivo, `font-variation-settings:'wdth' 125,'wght' 900`, italic, uppercase,
  `letter-spacing:-.005em`. Anton is dropped entirely. Using Archivo's width and italic axes
  gives the forward lean without adding a font family — it is the same variable face the
  body text already loads.
- **Body / UI** — Archivo 400–800, normal width. Unchanged from August.
- **Numbers / data** — JetBrains Mono 400/500/700. Unchanged. This is infrastructure, not brand.
- **Kickers** — Archivo 800, `font-size:10px`, `letter-spacing:.34em`, uppercase, in Surge
  Cyan. August's glowing 3px red pip before each kicker is **removed** — the rising bar is
  the card marker now, and two markers on one card is one too many.

The `<head>` font link must be widened to carry the axes:

```
https://fonts.googleapis.com/css2?family=Archivo:ital,wdth,wght@0,62..125,400..900;1,62..125,400..900&family=JetBrains+Mono:wght@400;500;700&display=swap
```

Anton can then be removed from that URL.

### Motif — the part that is actually new

1. **Waveform, not grid.** The 46px tactical grid on `body::before` becomes a single
   low-opacity horizontal surge trace, drifting left at 26s per cycle. Same job, same cost:
   one repeating inline SVG instead of two linear-gradients.

2. **Rising bar, not corner ticks.** August marked a card with four L-shaped ticks drawn as
   four background-gradients (`16px 2px, 2px 16px` ×2). Surge marks it with **one vertical
   gradient bar on the left edge**, 3px wide, full height, bright at the top and fading down
   — it reads as charging up. Same technique, one gradient instead of four. Critically, the
   bar's colour carries state exactly as the tick colour did, so the existing
   `.jh-fill-*` / `.r1` / `.r2` / `.r3` ladder keeps working with only the hues changed.

3. **Glow, not shadow.** `0 0 14px rgba(255,46,67,.32)` becomes
   `0 0 40px rgba(0,229,255,.28), 0 0 90px rgba(0,229,255,.14)`. Wider, cooler, two layers.
   Less hot metal, more screen static.

4. **Left-to-right bias.** Everything that can imply direction does. Hero gradients sweep
   left-to-right rather than blooming top-down. Navigational and call-to-action arrows are
   `▶`, not `→` (rank movement arrows stay ▲▼). Cards and views enter from the left.

### Motion

Discipline is unchanged from August: nothing over 320ms, transform and opacity only,
`:active` on everything pressable, hover gated to hover-capable devices. The **character**
changes:

| | Vol.6 | Vol.7 |
|---|---|---|
| Easing | `cubic-bezier(.23,1,.32,1)` | `cubic-bezier(.34,1.56,.64,1)` |
| View transition | `translateY(6px)` up, 190ms | `translateX(-10px)` in, 200ms |
| Reveal | glitch with chroma split, 950ms | surge-in from left with overshoot, 520ms |
| Boot moment | glitch — a signal being cut | pulse and ripple — a signal being sent |

**The easing swap is the single highest-leverage change in the skin.** One custom property,
applied everywhere at once: every press and every panel goes from landing a hit to building
energy. If you do nothing else, do that.

The ripple is splash-only. It never appears inside the app.

**Reduced motion:** kill the trace drift and the ripple; keep opacity transitions. A panel
that appears with no transition at all reads as a bug.

### Tagline

`SERVE FIRST. STRIKE HARD.` → **`RIDE THE SURGE.`**

Attack's line is specific to Attack. Surge's keeps the established two-beat rhythm and is
the only candidate that uses the volume name itself. Replace every occurrence — there are
three on HOME in the original, one after the Part A rebuild.

---

## Substitution table

August value on the left, Surge value on the right.

| Token | Vol.6 | Vol.7 |
|---|---|---|
| `--red` / lead | `#FF2E43` | `#00E5FF` |
| `--ice` / support | `#3DE1FF` | `#FF9E1B` |
| `--paper` | `#0A0C12` | `#0A0F14` |
| nav / floor | `#06070B` | `#050709` |
| `--cream` | `#F4F6FA` | `#F4F9FA` |
| `--muted` | `#8B95A7` | `#5C6B78` · `#8A9BA8` for prose |
| `--glow` | `0 0 14px red/.32` | `0 0 40px cyan/.28, 0 0 90px cyan/.14` |
| `--ease-out` | `.23,1,.32,1` | `.34,1.56,.64,1` |
| display face | Anton | Archivo `wdth 125` `wght 900` italic |
| card signature | 4 corner ticks, `16×2px` | 1 rising bar, `3px × 100%` |
| page texture | 46px tactical grid | horizontal surge trace |
| view transition | `translateY(6px)` up | `translateX(-10px)` in |
| boot moment | glitch | pulse and ripple |
| tagline | Serve first. Strike hard. | Ride the surge. |
| green (`#27E08A`) | live / done | `#00E5FF` — cyan absorbs it |

---

## How to implement

The August skin is already a stack of commented, append-only override layers at the bottom
of `index.html`, each re-pointing a handful of custom properties and background-image rules.
**Surge is one more layer in exactly that shape.** Nothing above it needs deleting.

`surge-skin.css` in this bundle is that layer, written against the real selectors in the
file. Paste it into a new `<style>` block as the **last** style block in `index.html`.

### RANK is the screen that tests the skin

Section 06 of the design language file shows it in full. It is 48 rows deep and it is where
August's language broke down — every row carried corner ticks, a photo, a pill strip and a
large red total, so the accent marked nothing. Three rules to hold:

- Only the top three carry a rising bar; only first place carries the bloom. Ranks 4+ are a
  plain table.
- The pinned **YOU** row is the one place Strike Amber appears on that screen. Nothing else
  on RANK is amber.
- The active segment of the series toggle is a solid cyan fill, same as the primary button on
  HOME, so "the filled cyan thing is the live one" holds across the app.

### Landmarks in `index-v2.html`

Line numbers refer to `indexreadable.html` (the same file, formatted — the shipped
`index.html` is minified in places). Search for the comment banners, they are distinctive.

| What | Where |
|---|---|
| `:root` — panel/neon/glow tokens | ~686, banner `kill the comic halftone dot field` |
| `:root` — `--tick` / plate, corner-tick geometry | ~5599, banner `Accent colour of the ticks carries the meaning` |
| `:root` — easing curves | ~5683, banner `AUGUST ATTACK · MOTION + NAV PASS` |
| Brand lockup, glitch keyframes | ~5462, banner `GLITCH + BRAND LOCKUP` |
| Kicker rules | ~5539 |
| Splash / boot animations | ~5896 |
| `DashboardView` | search `function DashboardView({` |
| `LeaderboardView` | search `function LeaderboardView({` |

### Inline hex values that CSS cannot reach

Part A's rewritten `DashboardView` and `LeaderboardView` use inline `style={{}}` objects, so
those literals need a find-and-replace pass in the JSX. There are not many:

| Find | Replace |
|---|---|
| `#FF2E43` | `#00E5FF` |
| `#3DE1FF` | `#FF9E1B` |
| `#F4F6FA` | `#F4F9FA` |
| `#8B95A7` | `#5C6B78` |
| `#06070B` | `#050709` |
| `#1FD9C4`, `#27E08A` | `#00E5FF` |
| `rgba(255,46,67,` | `rgba(0,229,255,` |
| `rgba(244,246,250,` | `rgba(244,249,250,` |
| `"'Anton',cursive"` | `"'Archivo',sans-serif"` + `fontVariationSettings:"'wdth' 125,'wght' 900"`, `fontStyle:"italic"` |
| `→` | `▶` |

Watch two things while doing this. The `#FF2E43` → `#00E5FF` swap will also hit the
**signup-state pill**, which should become Strike Amber `#FF9E1B`, not cyan — that pill is
the clearest use of the warm accent in the whole app. And the *inverse* `#00E5FF` swap must
not be applied to the **"YOU" pinned row** on RANK, which is already cyan-bordered and would
lose its distinction; give that row the amber border instead.

### Suggested order

1. Font link + `:root` token block. Stop and look — most of the temperature shift lands here.
2. `--ease-out`. Stop and feel it. This is the one that changes the product's character.
3. Rising bar (section 2 of `surge-skin.css`). Biggest visual delta.
4. Waveform background.
5. Kickers, brand lockup, tagline copy.
6. Motion: view transition, surge-in, splash ripple.
7. JSX hex sweep and arrow glyphs.
8. Contrast pass — confirm nothing prose-length is still on `#5C6B78`.

---

## Assets

### Urban Playground mark — done, in `assets/surge/`

The club mark has been recoloured for Vol.7. Nothing was redrawn: the saturated orange
racket maps to the accent and the white type maps to Voltage White, each pixel keeping its
own luminance and alpha, so shading and antialiasing survive intact.

| File | Size | Use |
|---|---|---|
| `up-logo-cyan.png` | 384 × 565 | **Ship this one.** Trimmed to the artwork + 6% margin |
| `up-logo-cyan-2x.png` | 768 × 1130 | Retina and print |
| `up-logo-amber.png` | 384 × 565 | The alternate — see below |
| `up-logo-cyan-padded.png` | 940 × 788 | Original canvas, for a like-for-like swap with zero CSS changes |

**Take the cyan.** Strike Amber means *happening now* in this system; spending it on a mark
that sits in every header permanently drains it. The club identity travels across volumes by
its shape, which is untouched — the colour belongs to the volume.

**On the padding.** The source PNG was 940 × 788 with the artwork occupying only 324 × 505 of
it — about two thirds of the width was empty. That is why the app compensates by rendering it
at `height:64`. The trimmed files make a height value mean what it says; if you use one,
re-check the sizes at every placement. If you would rather not touch any CSS, use
`up-logo-cyan-padded.png` and change nothing else.

**Embedding.** The app carries this as a single base64 constant, `UP_LOGO_FULL` — swapping
volumes is replacing that one string. Keep it to one constant; it was duplicated three times
before Part A. The glow is CSS, never baked into the PNG.

### Still outstanding

| Asset | Status |
|---|---|
| `assets/aa-wordmark.png` | **Not needed if you follow the spec.** `Surge Logo.html` sets "September Surge" as live type in the display face instead of custom artwork — it needs no PNG, scales cleanly, and stays editable for Vol.8. Ask the organiser only if they want bespoke lettering |
| `assets/aa-emblem.png` | Same. The recoloured club mark covers this slot |
| Player photos | Unchanged, referenced from existing state |

---

## Files in this bundle

| File | What it is |
|---|---|
| `index-v2.html` | **The application.** Part A already applied. Rename to `index.html` to deploy. This is real code, not a reference |
| `surge-skin.css` | The Vol.7 skin as a drop-in override layer, written against the real selectors. Paste as the last `<style>` block |
| `September Surge - Design Language.html` | The visual specification: tokens, motif specimens, easing curves, a side-by-side of HOME in Vol.6 vs Vol.7 tokens, and the full RANK screen. Open in a browser. **This is the reference to match** |
| `Surge Logo.html` | The recoloured club mark, both candidates, shown in header and splash context |
| `assets/surge/` | The recoloured logo PNGs |
| `August Attack - Design Review.html` | The UX critique Part A came from. Context for *why* HOME and RANK are shaped the way they are — read before changing them back |
| `indexreadable.html` | The original pre-Part-A file, formatted, with base64 blobs stripped. Use for line-number orientation and for diffing against `index-v2.html` |

Both `.dc.html` design files open directly in a browser with no server.
