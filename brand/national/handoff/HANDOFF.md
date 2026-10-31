# Handoff: 56 National Series — Direction 3a (Masar · Arches · Red)

## Overview
The November theme for the Blackout padel app's 56 National Series, built around Oman's National Day. Direction 3a has a flag-red base, a woven masar (turban) band, Omani door-arch hero cards, round landmark medallions, and pill-shaped controls. Two screens are designed: **Sessions** and **Night Recap** (bottom sheet). The other 12 screens in the series (`56 National Series App v2.dc.html` in the source project) should be restyled to match this system.

## About the Design Files
The files in this bundle are **design references created in HTML**. They are prototypes showing the intended look, not production code to copy. Recreate them in the target codebase's existing environment (React Native, SwiftUI, Flutter, etc.) using its own patterns and libraries. If there is no environment yet, pick the most suitable framework.

Open `56 Omani Directions.dc.html` in a browser and go to the section badged **3a** (the top section). The sections below it (2a, 2b, 1a–1c) are earlier explorations; use them for context only.

## Fidelity
**High-fidelity.** Colors, type, radii and spacing are final. Landmark silhouettes and pattern tiles are placeholder vector drawings. Replace them with commissioned artwork in the same slots and proportions.

Rule: **no mosques** in any landmark artwork.

## Global
- Frame: 375 × 812 (iPhone). Status-bar spacer is 44px at the top.
- Base background `#B8141F`, overlaid with the khanjar tile (`khanjar-tile-red.png`, 132×132 repeat, opacity 0.14).
- Side padding: 20px. Vertical gap between blocks: 14px.
- Shape language: no square blocks. Hero cards use an **arch** (`border-radius: 168px 168px 28px 28px`). Rows, chips, buttons and the tab bar are **pills** (`border-radius: 999px`). Icons sit in **circles**.
- Arch frame "double line": `box-shadow: 0 0 0 4px #B8141F, 0 0 0 6px #F7F1E6` (4px red gap, then a 2px ivory hairline).
- Content below the fold fades out with a 56px gradient (`#B8141F` 0% → 100%) placed directly above the tab bar.

## Screens

### 1. Sessions
Top to bottom:

1. **Masar band**: 24px tall, 14px side inset, pill radius, bg `#9E1520` + `masar-band-white.svg` tiled at 40×24.
2. **Header** (padding 16 / 20 / 12, column, gap 14):
   - Logo lockup: "56" mark (28px Archivo Expanded Black Italic, white fill, 1.2px `#1A0A0C` stroke, two offset shadows: `#1A0A0C` at +1.5px and `#087A3F` at +3px), then two lines: "56 NATIONAL SERIES" (11px/800, tracking .16em, white) and "السلسلة الوطنية" (Noto Kufi Arabic 11px/700, white).
   - Eyebrow "NOVEMBER · MON & WED · 5:30 PM" (11px/800, .16em, white).
   - Title "SESSIONS" (Archivo, width 125, weight 900, italic, 46px, line-height .84, white).
   - Arabic "الجلسات" on its own line under the title (Noto Kufi 13px/700, white).
3. **Live session arch card** (bg `#F7F1E6`, arch radius, double-line frame, padding 30 / 22 / 20, centered column, gap 8):
   - Medallion: 64px circle `#B8141F`, Nizwa Fort silhouette (white, 44px wide), ring `0 0 0 3px #F7F1E6, 0 0 0 5px #D7202E`.
   - Row: pill "● LIVE NOW" (`#D7202E`, white, 11px/900, .12em, padding 5×11) and "NIZWA FORT" (11px/800, .16em, `#9E1520`).
   - "SESSION 6" (44px Expanded Black Italic, `#1A0A0C`, lh .86).
   - "WED 18 NOV · COURTS 1–4" (11px/800, .16em, `#6B5A52`).
   - Progress: 8px pill track `rgba(215,32,46,.15)`, fill `#D7202E` at 58%. Caption "14 of 24 matches played · Group stage" (13px/700, `#1A0A0C`).
   - CTA: full-width pill `#1A0A0C`, "OPEN SESSION ▶" (13px/900, .18em, white, padding 15 vertical).
4. **National Day pill** (bg `#087A3F`, pill, padding 12 12 12 22): "FRI 20 NOV · 5:30 PM" (11px/800, white), "NATIONAL DAY NIGHT" (18px/900 italic uppercase, nowrap), "العيد الوطني" (Noto Kufi 11px). On the right, a 52px white circle with "2X" (22px Expanded Black Italic, `#087A3F`).
5. **Coming up** (label 11px/800 white; rows gap 8). Each row is a pill on `#9E1520`, padding 6 8 6 6:
   - 44px circle `#B8141F` holding a white landmark icon.
   - Eyebrow "DATE · LANDMARK" (11px/800, .16em, `#F2B8BC`) and title (15px/800, white).
   - Optional pill "SIGN UP" (white bg, `#B8141F` text, 11px/900, padding 7×12).
   - Data: Session 8 · Mon 23 Nov · Riyam (incense burner), with SIGN UP. Session 9 · Wed 25 Nov · Al Alam (palace). Grand Finale · Mon 30 Nov · Bahla (watchtower).
   - **Landmark-per-session assignments are placeholders.** The product owner must confirm the mapping.
6. **Tab bar**: absolute, 12px from the sides, 14px from the bottom. Pill `#1A0A0C`, padding 5, gap 3. Items: HOME, SESSIONS, RANK, ME, PLAYERS (11px/900, .04em, inactive `#CBBDB6`). The active item is a white pill with `#B8141F` text.

### 2. Night Recap (bottom sheet over Sessions)
- Scrim `rgba(0,0,0,.4)`. Sheet starts at y=56, bg `#B8141F` + khanjar tile, top radius 28. Grabber 48×5, `rgba(255,255,255,.35)`.
- Content padding 12 / 20 / 24, gap 14:
  1. Row: "SESSION 5 RECAP · MON 16 NOV" (11px/800, white) and "ملخص الليلة" on the right.
  2. **Champions arch card**: `#F7F1E6`, arch radius, double-line frame, padding 8 8 0. Photo is 200px tall, clipped to `border-radius: 160px 160px 0 0`. Under the photo, a full-bleed masar strip (12px, `masar-band-red.svg` at 20×12). Then a centered block: pill "CHAMPIONS · +8 EACH" (`#D7202E`), "BARAA & MOSSA" (24px/900 italic uppercase, `#1A0A0C`), "Beat Munther & Khalid in the final · 6–4" (12px, `#6B5A52`).
  3. **Stat pills** (gap 6): `#9E1520` pill, padding 9×16, space-between. Label 11px/800 `#F2B8BC`; value 14px/800 white.
     - MVP — Baraa · 6 votes
     - BIGGEST WIN — Hamed & Nooh · 6–0
     - UPSET — Ali & Omar beat the #1
     - BIGGEST CLIMBER — Salim K. ▲4
  4. **Your night pill**: `#F7F1E6`, padding 12×18. "YOUR NIGHT" (11px/800, `#9E1520`) and "+11 · Semi-final ▶" (14px/800, `#1A0A0C`).
  5. **Buttons** (2-col grid, gap 10, both pills, padding 15 vertical, 13px/900 .18em): SHARE is white bg with `#B8141F` text; FULL RESULTS is transparent with a 2px white border and white text.

## Interactions & Behavior
- OPEN SESSION opens the live session (Teams / Groups / KO / MVP tabs, already specified in the v2 app).
- SIGN UP opens the session sign-up flow.
- The recap sheet opens after a session ends or from the session history. Drag down to dismiss. SHARE opens the share-card flow. FULL RESULTS opens the session results.
- The recap carries over the v2 MY NIGHT / EVERYONE toggle (`design_handoff_blackout_social_recaps`).
- Pressed state for pills and buttons: scale 0.97 and darken 8%, 120ms ease-out.
- The live dot may pulse (opacity 1 → .4, 1.2s loop).
- RTL: Arabic labels are secondary and should stay where they are; don't mirror the layout.

## State
- `sessions[]`: `{ id, number, date, time, landmarkId, status: upcoming|live|done, signedUp, multiplier }`
- live progress: `{ played, total, stage }`
- recap: `{ champions[], finalScore, mvp, biggestWin, upset, biggestClimber, myNight: { points, finish } }`
- `landmarks[]`: `{ id, nameEn, nameAr, iconAsset }`

## Design Tokens
Colors:
- `#B8141F` red base
- `#9E1520` deep red (rows, bands)
- `#D7202E` flag red (live, accents)
- `#F7F1E6` ivory (hero cards)
- `#1A0A0C` ink (text, CTA, tab bar)
- `#6B5A52` muted text on ivory
- `#F2B8BC` rose (labels on red)
- `#087A3F` flag green (National Day only)
- `#CBBDB6` inactive tab text
- `#FFFFFF`

Type:
- Archivo variable (width 62–125, weight 400–900). Display = width 125, weight 900, italic.
- Noto Kufi Arabic 500/700.
- Scale: 46 / 44 / 24 / 22 / 18 / 15 / 14 / 13 / 12 / 11. Minimum size is 11px.
- Labels use uppercase with tracking .16em; buttons use .18em.

Radii: 999 (pill), 168/28 (arch), 160 (photo arch), 28 (sheet), 50% (medallions).

Spacing: 4, 6, 8, 10, 12, 14, 16, 20, 22, 30.

Shadows: there are no drop shadows, only the double-line ring `0 0 0 4px <bg>, 0 0 0 2px #F7F1E6` (stacked).

## Assets (`assets/`)
- `khanjar-tile-red.png`: background tile.
- `masar-band-white.svg`, `masar-band-red.svg`: woven band tiles (40×24 and 20×12).
- `mon-nizwa-*`, `mon-burner-*`, `mon-alam-*`, `mon-tower-*` (white/red): landmark silhouettes for Nizwa Fort, the Riyam incense burner, Al Alam Palace and a watchtower (Bahla).
- All SVGs are placeholder drawings. Replace them with final artwork. No mosques.
- The champions photo is user-supplied (an image slot in the prototype).

## Files
- `56 Omani Directions.dc.html`: the design. See section **#3a**.
- `support.js`, `image-slot.js`: needed to open the prototype in a browser.
