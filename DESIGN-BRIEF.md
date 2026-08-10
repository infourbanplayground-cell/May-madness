# August Attack — design review pack

Everything here was captured from the **live site** (`attack.urbanpadel.om`,
fetched 10 Aug 2026) and rendered in a real browser with the real fonts and
real tournament data. You do not need to visit the site — and you can't
usefully, see "Why the URL is unreadable" at the bottom.

## What it is

A social padel series in Muscat, Oman. Volume 6 of the "Urban Social
Series", running nine sessions across August. Sixteen teams a night, group
stage into knockouts, points follow the **player** rather than the team, so
partners change every session. 245 players registered, 48 currently ranked,
62 matches played.

Audience: players on phones, mostly checking it between games at the venue
or after a session. It is not a desktop product — assume a 390–430pt
viewport is the design target and the desktop view is incidental.

## Screens

Three tabs, bottom nav, no routing.

| File | Screen |
|---|---|
| `fold-01-home.png` / `01-home.png` | HOME — hero, standings snapshot, prize pool, photo wall |
| `fold-02-sessions.png` / `02-sessions.png` | SESSIONS — session list, admin actions, session detail |
| `fold-03-rank.png` / `03-rank.png` | RANK — the full ranked table |

`fold-*` are above-the-fold at 430×932 @2x. The unprefixed ones are the
whole scrolling page — HOME is ~3000pt tall and RANK ~4400pt, which is
itself worth an opinion.

## The design system as built

Dark "neon night" skin. Every surface is square — `border-radius: 0` is
enforced globally with a `*:not(.rounded-full)` rule.

| Token | Hex | Role |
|---|---|---|
| Court Black | `#0A0C12` | page base, plates |
| Deep Black | `#06070B` | nav bar, gradient floor |
| **Attack Red** | `#FF2E43` | primary accent — active states, rank 1 |
| Ice / Cyan | `#3DE1FF` | second voice, never competes with red |
| Chalk | `#F4F6FA` | primary text |
| Steel | `#8B95A7` | secondary text, inactive |
| Green | `#27E08A` | live / success only |

Intended ratio is roughly **3:1 red to cyan**. If a screen reads cyan-first
it is wrong. There is deliberately **no gold** — medals run red →
light-steel → steel.

Type: **Anton** (display, `letter-spacing:.06em`), **Archivo** 400–900
(body/UI), **JetBrains Mono** 500/700 (all numbers and labels).

Signature motif: corner ticks drawn as four stacked `linear-gradient`
backgrounds on a plate — cyan opens top-left, red closes bottom-right.

Motion: `--ease-out: cubic-bezier(.23,1,.32,1)`, nothing over 320ms.

## Known defects — verified in source, not guesses

These are counted occurrences in the shipped file, so they are real. Fixing
them is probably a better first pass than restyling anything.

1. **Off-palette colours survive from the previous volume.** The series is a
   re-skin of July Heat and some values were never converted:
   - `#1B8EE0` ×6 — the blue session-number chips, clearly visible in
     `fold-02-sessions.png`. Should be Attack Red or Ice.
   - `#1F8A24` ×7 — a dull green where the token is `#27E08A`.
   - `#44403C` ×6 — a warm stone grey, wrong temperature for this palette.
2. **`Rajdhani` is referenced in 3 CSS rules but never loaded** — it is not
   in the Google Fonts request, so those rules silently fall back to
   Archivo. Either load it or delete the references.
3. **The same 0.41MB PNG is embedded three times** as base64. Total embedded
   images are 1.24MB of a 1.67MB file — roughly **half the payload is a
   duplicated logo**.
4. **Class names lie.** `.jh-*` classes (July Heat) are all over this
   volume, `--orange` holds `#FF2E43`, `--gold` and `--yellow` both hold
   cyan. Read computed values, never names.
5. **Specificity trap.** A global rule
   `[class*="bg-stone-9"]:not(nav):not(header):not(.sticky)` scores (0,2,2)
   and beats most later single-class rules. New rules may need an
   `html:not(.light)` prefix to land. Verify with `getComputedStyle`, not by
   reading the source.

## Constraints any proposal has to respect

- **Single file.** The whole app is one 1.67MB `index.html` — React 18 UMD +
  Tailwind CDN + JSX compiled in the browser by Babel. No build step, no
  bundler, no npm. Proposals requiring a toolchain are out.
- **Babel must stay pinned to `@7`.** An unpinned `@babel/standalone` went
  to v8 and blanked every site simultaneously.
- **CSS is append-only.** New rules go at the end of the last `<style>`
  block; existing blocks are not edited.
- **localStorage keys `july-heat-state-v1` / `-admin` / `-token` must not be
  renamed** — renaming orphans every user's device state.
- Server is UTC+4. Never build date strings with `toISOString().split('T')`.

## Why the URL is unreadable to a tool

`https://attack.urbanpadel.om` returns **HTTP 200** — nothing is blocking
you. The problem is what arrives: 1.67MB of HTML whose entire UI lives
inside a single `<script type="text/babel">` tag. Without executing JS *and*
transpiling JSX in the browser, the only visible text on the page is the
word `LOADING...`.

So any tool that fetches HTML sees an empty page and reasonably concludes
the site is inaccessible. It isn't; it's just unrendered. That is what these
screenshots are for.
