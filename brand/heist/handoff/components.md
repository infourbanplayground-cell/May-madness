# Shared components

Build these first (phase 1). Every screen uses them. Values come from `tokens/tokens.css`.

## TitleLockup
The Muscat Nights title. Sizes: S (Home, 76px base), M (loading / contenders, 84–92px), L (campaign poster, 104px).
1. Optional line: `Urban Playground presents` in serif italic, peach, between two 24px peach rules.
2. `MUSCAT`: display font, weight 900, size = base × 0.74, line-height .84, letter-spacing −.01em, text filled with `--mn-grad-title` (background-clip: text), shadow `--mn-shadow-title`.
3. `NIGHTS`: on a band with `--mn-grad-nights`, skewed −10deg (text counter-skewed +10deg), display 900, size = base × 0.42, letter-spacing .32em, navy text.
4. Meta line: `ليالي مسقط` (Reem Kufi 700) · peach dot · label `VOL.10 · MUSCAT · DEC 2026`.
5. Centred lockups get a soft radial sun glow behind MUSCAT (peach → coral → transparent).

## HeroCut
Image block with an angled bottom edge: `clip-path: var(--mn-cut-hero)`, a 3px sand keyline drawn along the cut edge (absolute div, rotated to the cut angle), and fades (top 35–50% navy for the status bar, bottom to navy). Used on Home, session header, Live, Recap, Loading, Score Settled, Big Score (gold keyline).

## Glass card
`.mn-glass`. Optional accent border colour for emphasis (peach = serving, teal = you, gold = finale/rival gap, coral = live).

## Label / Serif caption
`.mn-label` (JetBrains Mono 11px uppercase) and `.mn-serif` (Fraunces italic). Labels sit above values; serif lines sit below them.

## Pill
Filter and tab chips: 999px radius, active = sand background + navy text, inactive = 1px sand-25% border + mist text, Manrope 600 12px.

## Buttons
Primary `.mn-btn-primary` (coral gradient, navy text, display font). Ghost `.mn-btn-ghost`. Light: sand background, navy Manrope 700 (Lock result). Min height 48px (56px on Live Scoring).

## BottomNav
Floating pill bar 14px from the sides and 16px from the bottom, navy 78% + blur 16px, 1px sand-14% border, radius 20px. Tabs: Home · Jobs · Wanted · Me · Crew. Active tab = sand pill with navy text. Content needs ~84px bottom padding.

## CrewCard
Sizes: S 120px (ME), M 150px (Crew grid), L 240px (detail, card pull). Height = width × 1.42.
- Outer 4px frame with the tier gradient (`--mn-tier-*`), radius 14px, shadow `--mn-shadow-card`.
- Image area 62% of height, player art/photo, fade to `--mn-navy-2`, tier tag top-left (`LEGEND`), rank `#1` top-right.
- Body: name (display, uppercase), `REP · LEVEL` in rep colour, points right.
- L size adds 4 stat bars (SMASH, WALL, SPEED, CLUTCH) in the rep colour.
- Foil shine on Legend and Elite: diagonal light band sweeping across the image, 3.2s linear loop, `mix-blend-mode: overlay`.
- Legend L only: tilt loop rotateY ±9°, rotateX ±3°, 6s ease-in-out (use device orientation if permitted).

## SceneTag
Small caption chip on images: navy 72% background, 2px coral left border, display 800 12px, letter-spacing .18em, sand text (gold variant for finale).

## Billing (stories only)
Film-style credits block: display 700 12px, letter-spacing .08em, line-height 1.25, sand 72%, linking words (`presents a`, `starring`, `with`) at sand 45%.

## Motion
| Name | Spec | Used on |
|---|---|---|
| foil | background-position 120% → −120%, 3.2s linear infinite | Legend/Elite cards |
| tilt | rotateY −9°↔9°, rotateX 3°↔−3°, perspective 900px, 6s | Legend card L |
| ring | scale .6 → 2.2, opacity .9 → 0, 2.4s, 2 rings staggered .8s | Rep Up |
| slam | scale 2.4 → .94 → 1 with fade-in, ~700ms | Rep Up, Score Settled headlines |
| bar fill | width 0 → value after the slam, 600ms | Rep progress, The Take meter |
| slide | 5s per recap slide, progress segment fills linearly | Recap Slides |
All disabled under `prefers-reduced-motion: reduce`.
