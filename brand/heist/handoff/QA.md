# QA steps (run at the end of every phase)

1. **Visual compare.** With Playwright, open each screen you touched at a 375×812 viewport (deviceScaleFactor 2), using fixture data. Save to `qa/<phase>/<screen>.png`. Put it next to the reference in `screenshots/` and list every visible difference (layout, order, spacing, colour, font, copy). Fix them, then re-shoot.
2. **Narrow phone.** Repeat at 360px wide. No horizontal scroll, no clipped text.
3. **Tokens.** Search the changed files for hex colours (`#[0-9a-fA-F]{3,6}`) outside the tokens files. There should be none.
4. **Copy.** Search for old names: `Gulf Nights`, `The Payout`, `Neo Muscat`. There should be none in the UI.
5. **Data.** Change a fixture value (e.g. a player's points) and confirm rank, rep colour, gap, rival and the take meter update correctly.
6. **Scoring untouched.** `git diff` must show no changes to the points engine or scoring files.
7. **Motion.** Turn on reduced motion and confirm all animations stop.
8. **Accessibility.** Tab through each screen; every action is reachable and labelled.

## Phase report template
```
Phase N report
Screens/components done: ...
Acceptance checklists: (paste each checklist with [x] / [ ])
Differences from the reference I could not fix, and why: ...
Assumptions I made: ...
Questions for you: ...
Files changed: ...
```
