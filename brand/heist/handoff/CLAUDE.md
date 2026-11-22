# Rules for this build (Muscat Nights, Urban Social Series Vol.10)

1. **Read before you edit.** Before touching a screen, re-read its spec in `design_handoff_muscat_nights/screens/` and look at its screenshot. Do not work from memory.
2. **Never change scoring.** The points engine, scoring rules and backend data model stay as they are. New fields are derived only (see `data.md`).
3. **Tokens only.** All colours, fonts, radii, shadows and spacing come from `tokens/tokens.css` / `tokens.ts`. No new hex values in components.
4. **Reuse components.** Build and use the shared components in `components.md`. Do not restyle a one-off copy.
5. **Exact copy.** Use the names and copy in the specs exactly (Muscat Nights, The Take, Now Loading Muscat, Most Wanted, Score Settled, The Big Score).
6. **One phase at a time.** Finish a phase, run the QA steps, write the phase report, then stop and wait.
7. **Check against the design.** For every screen you touch, take a 375px Playwright screenshot and compare it side by side with the reference PNG. Fix differences before calling it done.
8. **Report honestly.** In each phase report, tick every acceptance checklist item. List anything not done, guessed, or different from the spec, with the reason. Never mark an item done without checking it.
9. **Ask, don't guess.** If a spec is unclear or conflicts with the existing code, stop and ask.
10. **Images are placeholders.** Paintings in `design/assets/` are AI stand-ins. Load player and session images from data (`player.photo`, `session.art`) so real images can be swapped in without code changes.
11. **Boss Kill bonus is off.** Do not implement it in scoring unless `SEASON.bossKillBonus.enabled` is true.
12. **Accessibility.** Real buttons and links, 44px minimum targets, 11px minimum text, honour `prefers-reduced-motion`.
