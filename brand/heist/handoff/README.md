# Handoff: Muscat Nights · Urban Social Series Vol.10 (December 2026)

A full visual overhaul of the Urban Playground padel league app for December, plus new features: crew cards, rep levels, rivals, Now Loading Muscat, The Big Score finale, recap slides, gaps on the table and a prize meter. The league format, screens and **points engine stay the same** as the current production app.

## Start here
1. **`KICKOFF.md`**: paste the prompts into Claude Code one phase at a time. Phase 0 is planning only.
2. **`CLAUDE.md`**: rules for the build. Copy it to the repo root.
3. **`screens/`**: one spec per screen, each with a layout, data, states and an **acceptance checklist**.
4. **`components.md`**: shared components to build first.
5. **`data.md`**: derived fields, triggers, exact names, and what's not approved yet.
6. **`QA.md`**: checks to run after every phase, plus the phase report template.
7. **`tokens/`**: `tokens.css` and `tokens.ts`. All styling comes from here.
8. **`fixtures/`**: sample JSON matching every screenshot.
9. **`screenshots/`**: 2× references for all 19 screens.
10. **`design/Muscat Nights App.html`**: static HTML of all screens. Open in a browser; inline styles are the exact values.

Base app spec (shell, data model, points engine, share export): `design_handoff_blackout_app/README.md` in the same project.

## Screens
| # | Screen | Spec | Screenshot | Phase |
|---|---|---|---|---|
| 01 | Home | `screens/01-home.md` | `screenshots/01-home.png` | 2 |
| 02 | Jobs (sessions list) | `screens/02-jobs.md` | `screenshots/02-jobs.png` | 2 |
| 03 | Most Wanted (table) | `screens/03-most-wanted.md` | `screenshots/03-most-wanted.png` | 2 |
| 04 | ME | `screens/04-me.md` | `screenshots/04-me.png` | 2 |
| 05 | The Crew (players) | `screens/05-crew.md` | `screenshots/05-crew.png` | 2 |
| 06 | Crew Card (player detail) | `screens/06-crew-card.md` | `screenshots/06-crew-card.png` | 2 |
| 07 | Session detail · Groups | `screens/07-session-groups.md` | `screenshots/07-session-groups.png` | 3 |
| 08 | Live Scoring | `screens/08-live-scoring.md` | `screenshots/08-live-scoring.png` | 3 |
| 09 | Episode Recap | `screens/09-episode-recap.md` | `screenshots/09-episode-recap.png` | 3 |
| 10 | Recap Slides (new) | `screens/10-recap-slides.md` | `screenshots/10-recap-slides.png` | 3 |
| 11 | Now Loading Muscat (loading screen) | `screens/11-now-loading-muscat.md` | `screenshots/11-now-loading-muscat.png` | 4 |
| 12 | New Crew Card (card pull) | `screens/12-new-crew-card.md` | `screenshots/12-new-crew-card.png` | 4 |
| 13 | Rep Up | `screens/13-rep-up.md` | `screenshots/13-rep-up.png` | 4 |
| 14 | Your Rival | `screens/14-your-rival.md` | `screenshots/14-your-rival.png` | 4 |
| 15 | Score Settled | `screens/15-score-settled.md` | `screenshots/15-score-settled.png` | 4 |
| 16 | The Big Score (finale) | `screens/16-the-big-score.md` | `screenshots/16-the-big-score.png` | 4 |
| 17 | The Take (prizes) | `screens/17-the-take.md` | `screenshots/17-the-take.png` | 2 |
| 18 | Story · Campaign Poster | `screens/18-story-campaign-poster.md` | `screenshots/18-story-campaign-poster.png` | 5 |
| 19 | Story · Contenders | `screens/19-story-contenders.md` | `screenshots/19-story-contenders.png` | 5 |

## Season facts (confirm before launch)
- Nine sessions, Mon & Wed 17:30, Wed 2 Dec to Wed 30 Dec 2026. Session 9 is The Big Score (2× points).
- Prize pool 402 OMR: season top 3 get 75 / 50 / 30 OMR; each night's champions get 14 OMR each.

## Images
`design/assets/art-*.jpg` are **AI-generated stand-ins** of invented people. Real player portraits and session photos will replace them, so images must load from data (`player.photo`, `session.art`), never be hard-coded. Screenshots use a placeholder for the UP logo; use the real `assets/up-logo-tight.png` from the project.

## Not in scope
No mascot. No anime, comic or neon styling. Boss Kill +3 bonus stays off until approved.
