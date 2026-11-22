# Kickoff prompts for Claude Code

Paste one prompt at a time. Wait for the phase report and review it before sending the next.

---

## Phase 0 · Read and plan (no code)
```
Read design_handoff_muscat_nights/ completely: README.md, CLAUDE.md, components.md, data.md, every file in screens/, the tokens, the fixtures, and look at every screenshot. Then look at the current app codebase.

Do not write any code yet. Reply with:
1. A list of every screen and every component you will build, mapped to existing files you will change or new files you will add.
2. Where each derived field in data.md will be computed (rep, tier, gap, rival, head-to-head, take meter, card stats, moments).
3. Anything in the handoff that is unclear, missing, or conflicts with the existing code.
4. Your plan for phases 1 to 5.
Copy CLAUDE.md to the repo root if it is not there already.
```

## Phase 1 · Foundation
```
Phase 1: add tokens (tokens.css and tokens.ts), fonts, and the shared components in components.md (TitleLockup, HeroCut, glass card, labels, pills, buttons, BottomNav, CrewCard, SceneTag, Billing, motion). Wire the fixtures so screens can render with sample data in development.
Build a simple /dev/components page that shows every component in every size and state.
Run the QA steps in QA.md for that page, then write the phase report and stop.
```

## Phase 2 · Season screens
```
Phase 2: build screens 01 Home, 02 Jobs, 03 Most Wanted, 04 ME, 05 The Crew, 06 Crew Card, 17 The Take, following each spec in screens/ exactly. Use the shared components only.
For each screen: screenshot at 375px, compare with the reference PNG, fix differences, then tick its acceptance checklist.
Write the phase report and stop.
```

## Phase 3 · Session night
```
Phase 3: restyle the session flow: 07 Session detail (Groups, plus Teams, Knockout and MVP tabs), 08 Live Scoring, 09 Episode Recap, and build 10 Recap Slides (new). Keep the existing scoring and session logic unchanged.
Same QA and report as before. Stop after the report.
```

## Phase 4 · Moments
```
Phase 4: build 11 Now Loading Muscat, 12 New Crew Card, 13 Rep Up, 14 Your Rival, 15 Score Settled, 16 The Big Score, including their triggers and once-per-device logic from data.md. Boss Kill bonus stays disabled.
Same QA and report. Stop after the report.
```

## Phase 5 · Stories and final pass
```
Phase 5: build the share exports 18 Campaign Poster and 19 Contenders (1080×1920) and add MY CARD to the share sheet. Then do a full pass: screenshot every screen at 375px and 360px, compare with references, and run the full QA checklist. Write the final report with every acceptance item ticked or explained.
```
