# Urban Playground — Design Context

Companion to `CLAUDE.md`. That file covers servers and deploys; this one covers
how things should look and move. Read it before changing any UI in
`august-attack-index.html`, `july-heat-index.html`, or the landing pages.

Values here were read out of the shipped files, not remembered. When you change
a token in the app, change it here in the same commit.

---

## 1. The series

Each series (volume) is a re-skin of the same React app, not a new app. The
structure, scoring engine and component classes stay; the palette, type and
motif change.

| Vol | Series | Theme | Status |
|---|---|---|---|
| 5 | July Heat | Comic book — halftone, hard offset shadows, cream paper | Archived (banner on `heat.urbanpadel.om`) |
| 6 | August Attack | Neon night — court black, glitch, tactical grid | **Live** at `attack.urbanpadel.om` |

Because a new series inherits the previous one's markup, **class names lie**.
`.jh-*` classes (July Heat) are all over the August app. `--yellow` holds cyan.
Don't rename them — a lot of CSS keys off those exact strings. Read the computed
value, not the name.

---

## 2. August Attack tokens

### Colour

| Token | Hex | Use |
|---|---|---|
| Court Black | `#0A0C12` | Page base, plates |
| Deep Black | `#06070B` | Nav bar, gradient floor |
| **Attack Red** | `#FF2E43` | Primary accent. Active states, kickers, rank 1 |
| Ice / Cyan | `#3DE1FF` | Second voice. Never competes with red |
| Chalk | `#F4F6FA` | Primary text |
| Steel | `#8B95A7` | Secondary text, inactive states |
| Green | `#27E08A` | Live / success only |

Plates and hairlines:

```css
--panel: rgba(20,24,36,.82);
--panel-2: rgba(30,36,50,.9);
--hair:  rgba(244,246,250,.12);
--glow:  0 0 14px rgba(255,46,67,.32);
```

**Red dominates, cyan supports.** If a screen reads as cyan-first, it's wrong.
Ratio target is roughly 3:1 red to cyan.

Gold is not in this palette. Medal chips use a red → light-steel → steel ladder
(`#FF2E43` / `#C9CFDA` / `#8B95A7`), not gold/silver/bronze.

### CSS variables that mislead

These are aliased for backwards compatibility with the July Heat markup:

```css
--orange:    #FF2E43   /* not orange */
--orange-br: #FF2E43   /* the active-nav sentinel — see §6 */
--gold:      #3DE1FF   /* not gold */
--yellow:    #3DE1FF   /* not yellow */
--blue:      #3DE1FF
--cream:     #F4F6FA
--ink:       #0A0C12
```

### Type

Loaded from Google Fonts: **Anton**, **Archivo** (400–900), **JetBrains Mono** (500/700).

| Role | Font | Treatment |
|---|---|---|
| Display / headings | Anton | `letter-spacing: .06em` |
| Body / UI | Archivo | 400–800 |
| Numbers, data, nav labels | JetBrains Mono | 700, tight tracking |
| Kickers | Archivo 800 | `letter-spacing: .34em`, uppercase, red, 11px |

> **Trap:** three rules reference `'Rajdhani'` (`.aa-presents`, `.aa-tag`,
> `.jh-sec-kicker`). Rajdhani is **not loaded** — those silently render as
> Archivo via the fallback. Either add it to the font link or drop the
> reference; don't add new uses expecting Rajdhani.

### Surfaces — corner ticks, not borders

The box language is a flat dark plate marked by two L-shaped corner ticks
(top-left, bottom-right), drawn with **background gradients** so they never
collide with a pseudo-element:

```css
background-image:
  linear-gradient(var(--tick),var(--tick)), linear-gradient(var(--tick),var(--tick)),
  linear-gradient(var(--tick),var(--tick)), linear-gradient(var(--tick),var(--tick));
background-size: 16px 2px, 2px 16px, 16px 2px, 2px 16px;
background-position: 0 0, 0 0, 100% 100%, 100% 100%;
background-repeat: no-repeat;
```

Tick colour carries the meaning: red = primary/leader, cyan = qualified/info,
green = live, steel = quiet. **No rounded corners anywhere.** `border-radius: 0`.

Long list rows are *not* cards — they get a plate plus a hairline bottom rule,
no ticks. Ticks are for cards only, or the page turns into noise.

---

## 3. Brand assets

Served from `/assets/` on every host (`/var/www/<host>/public/assets/`).
Not in the repo — the server is the only copy, so back up before overwriting.

| File | Size | What it is | Notes |
|---|---|---|---|
| `aa-emblem.png` | 432×583, RGBA | Urban Playground neon emblem | The August-era mark. Identical on all hosts |
| `aa-wordmark.png` | 728×278 (attack) / 610×254 (elsewhere) | AUGUST ATTACK lockup | **Two different files under one name** — see below |
| `up-logo.png` | 940×788, RGBA | Original Urban Playground logo | **Overwritten on `attack` with the emblem** — see below |
| `up-logo-new.png` | 940×788, RGBA | Same as `up-logo.png` elsewhere | Consistent across hosts |
| `july-heat-logo.png` | 500×621, palette, **no alpha** | July Heat mark | Palette PNG — will show a box on non-white backgrounds |
| `july-heat-logo-black.png` | — | Dark-background variant | |
| `jh-watermark.png` | — | July Heat photo-frame watermark | **Also overwritten on `attack`** |
| `june-fury-lockup.png` | — | Vol.4 lockup | Legacy |
| `sig-logo.png` / `sig-logo-dark.png` | 108×170 | Signature mark | Light / dark pair. Not referenced by the August app |
| `aa-burst.svg` | 8KB | Attack burst motif | On `attack` only. **Currently unreferenced** |

### Same filename, different image per host

Verified by checksum:

| File | `attack` | `heat` / `urbanpadel.om` |
|---|---|---|
| `up-logo.png` | `61261c02` (the AA emblem) | `da50f2fa` (real UP logo) |
| `jh-watermark.png` | `61261c02` (the AA emblem) | `7682c92c` (July Heat mark) |
| `aa-wordmark.png` | `28666b9d` | `45b3b52a` (the trimmed "clean" one) |

Two files on `attack` were overwritten in place with the emblem rather than
having their references updated. It renders correctly today, which is exactly
what makes it dangerous: **markup shared between hosts shows a different logo
depending on where it's served.** If you copy a component from the landing page
into the app, or the reverse, check the logo it renders — don't assume the path
means the same thing. `assets/jh-watermark` is still referenced 4× in the August
app and only looks right because of this overwrite.

Fixing it means pointing those references at `aa-emblem.png` and restoring the
two files. Worth doing before Vol.7 inherits the confusion.

### Logos embedded in the app

The August app also carries logos inline as base64, not just by URL:

- `UP_LOGO_FULL` — the emblem
- `UP_LOGO_ICON` — the emblem again
- one inline `<img src="data:image/png;base64,…">` in the header — the emblem again

All three are **byte-identical** (md5 `555a85e8`, ~316KB each): **949KB of a
1613KB file is three copies of one image.** Collapsing them to a single constant
would cut roughly 630KB — about 39% of the page — off every cold load. Not yet
done; it touches JSX, so it wants its own change and its own verification.

When adding a logo, prefer `/assets/` over embedding. Embedding is only worth it
for the splash mark, which must paint before any network request resolves.

### Usage rules

- The emblem is the app mark; the wordmark is the series mark. Don't substitute
  one for the other — the wordmark carries the volume identity.
- Clear space around the emblem: at least 25% of its width on all sides.
- Never recolour either mark. The neon glow is baked into the PNG; a CSS filter
  will fight it.
- On dark surfaces use `july-heat-logo-black.png` / `sig-logo-dark.png`. The
  plain `july-heat-logo.png` has **no alpha channel** and will show a box.
- Header lockup is emblem-only at 26px; the splash uses the wordmark at 260px
  (`max-width: 70vw`).

---

## 4. Motion system

Full rationale in the `emil-design-eng` skill; these are the values in the app.

```css
--ease-out:    cubic-bezier(.23,1,.32,1);    /* enter, feedback */
--ease-in-out: cubic-bezier(.77,0,.175,1);   /* on-screen movement */
--ease-drawer: cubic-bezier(.32,.72,0,1);    /* sheets */
```

| Thing | Duration | Curve |
|---|---|---|
| Press feedback (`scale(.94–.985)`) | 160ms | ease-out |
| Colour / hover | 160ms | ease |
| Tab content enter (6px rise) | 190ms | ease-out |
| Scrim fade | 180ms | ease |
| Nav rule travel | 260ms | ease-in-out |
| Row cascade (opacity only) | 260ms, 30ms stagger, capped 360ms | ease-out |
| Sheet rise from bottom | 300ms | ease-drawer |

Rules that hold:

- **Nothing over 320ms.** This is a scoreboard, not a title sequence.
- **Animate `transform` and `opacity` only.**
- Everything pressable gets an `:active` scale. Everything.
- Hover effects go inside `@media (hover:hover)`, or a tap leaves rows stuck.
- `prefers-reduced-motion` keeps opacity, drops movement. Not zero animation —
  a panel that appears with no transition reads as a bug.
- **Glitch is for rare moments.** Boot, splash, card treatment. Never on a tab
  switch — something pressed fifty times a day stops reading as style and starts
  reading as a defect.

---

## 5. CSS architecture (read this before editing styles)

The app is a **single HTML file** with three `<style>` blocks, and each series
re-skin was appended to the end rather than editing what came before. The last
block is ~600 lines of overrides stacked in historical order.

Consequences:

1. **Append, don't edit.** Add a new commented section at the end of the last
   `<style>`. Editing mid-file breaks something four sections down that was
   compensating for it.
2. **`!important` is the ambient pressure level.** Nearly every override rule
   carries it. Yours will need it too.
3. **Specificity ties are broken by source order — but only on ties.** Several
   dark-mode rules are written `html:not(.light) nav.fixed { … }` (0,2,2). A
   later `nav.fixed.bottom-0 { … }` (0,2,1) **loses** despite being last. This
   cost real time this session: the nav background and corner ticks silently
   didn't apply. Match or exceed the `html:not(.light)` prefix when overriding
   anything themed.
4. Always verify a style landed by reading `getComputedStyle`, not by looking
   at the source.

### Vendoring for local testing

The app loads React/Babel/Tailwind from CDN. To test headlessly, copy it to
`aasrv/index.html` with the four CDN URLs rewritten to `/vendor/*.js`, serve on
`:8125`, and mock the API with Playwright `page.route()` on `**/state`,
`**/photos`, `**/session-photos*`. Without this the app hangs on `LOADING…`.

---

## 6. Component gotchas

**Bottom nav.** React renders it; the active tab is identifiable *only* by the
inline `color: var(--orange-br)` it carries. The travelling indicator measures
the DOM and re-measures via `MutationObserver` — it deliberately doesn't touch
React state. If you change how the active tab is marked, update that selector.

It must not have `backdrop-filter`. The page sets `viewport-fit=cover`, and the
bar needs `padding-bottom: env(safe-area-inset-bottom,0px)` plus
`transform: translateZ(0)` or it drifts while Safari's toolbar collapses. The
plate must be **fully opaque** — with the blur gone, any alpha lets the hero
type ghost through.

**Leaderboard rows carry an inline `rotate(±.35deg)` tilt.** Any keyframe that
animates `transform` with `both` fill lands on `transform: none` and flattens
that tilt permanently. This is why the row entry animation is opacity-only.
If you need a rise, guard it: `:not([style*="rotate"])`.

**Never leave a transform animation *filling* on an element that can contain
`position: fixed` children.** `animation-fill-mode: both/forwards` keeps the
last keyframe applied forever, and a filling transform animation computes to
`matrix(1,0,0,1,0,0)` even when that keyframe says `transform: none`. Any
computed transform other than `none` makes the element the containing block
for its fixed descendants — so `inset: 0` stops meaning "the viewport" and
every modal inside it lands somewhere absurd. This shipped once: the
tab-transition on `main > div` captured every modal in the app and pushed the
sign-up sheet 435px above the top of the screen. Drop the fill; if you need a
backwards fill because of a delay, put the animation on a wrapper that never
contains fixed children.

**Modals.** Never fade the container — it drags the panel's opacity down and you
see the page through the sheet mid-rise. Put the scrim on a `::before` and keep
the panel opaque while it travels.

**Two photo pipelines, two very different caps.** Player avatars go through
`resizeToBase64(file, size = 200)` — 200px, so avatar treatments must survive
that. Session/wall photos go through `resizePhotoToBase64` (900px) and
`watermarkPhotoToBase64` (1080px, server-enhanced up to 1600px). Don't design
for 200px on the wall; that cap belongs to avatars only.

**`drawComicPhotoFrame` is still July Heat** — halftone, "MEANWHILE, AT URBAN
PLAYGROUND…", `jh-watermark.png`. Known debt; it needs an August Attack rewrite.

---

## 7. Print & social assets

Built with Python + Playwright, in the session scratchpad, not committed:

| Script | Output |
|---|---|
| `build_certs.py` | Top-5 certificates, A4 landscape |
| `build_stickers.py` | 10 die-cut milestone stickers + A4 sheet |
| `build_vouchers.py` | Milestone recognition cards, 1080×1350 |
| `build_final_story.py` | Series-conclusion Instagram story |

**Never use `page.pdf()` for these.** A 3508 CSS px layout maps to ~2631pt and
`page.pdf({width:'297mm'})` captures only the top-left corner — this shipped
blank PDFs once. Screenshot at 300 DPI and wrap with Pillow:

```python
im.save(f'{name}.pdf', 'PDF', resolution=300.0)
```

Die-cut stickers need **three stacked clipped layers** (white contour → accent
ring → dark face). An inset `box-shadow` does not follow a `clip-path`, so the
ring breaks on polygon shapes.

Google Fonts subsetting: match `/* latin */`, not `latin-ext` — the ext subset
is missing common glyphs and produces visibly uneven lettering.

---

## 8. Before you ship a UI change

- [ ] Verified with `getComputedStyle`, not by reading source
- [ ] Checked at 430px wide — that's the real device
- [ ] `:active` state on anything pressable
- [ ] Hover gated behind `@media (hover:hover)`
- [ ] `prefers-reduced-motion` path exercised
- [ ] Reviewed in slow motion (8× duration, step frames) — full speed hides
      transform regressions and crossfade ghosting
- [ ] No `transform` keyframe landing on an element with an inline transform
- [ ] Long list scrolled with a `longtask` PerformanceObserver — target zero
- [ ] Backup on the server (`index.html.pre-<change>`) and `version.txt` bumped
