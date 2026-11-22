# Data and rules

**Do not change the points engine or scoring rules.** Every number comes from the existing production engine (see `design_handoff_blackout_app/README.md` › Points model, which this app already implements). Only presentation and the derived fields below are new.

## Fixtures (`fixtures/`)
Sample data that matches every screenshot. Load these in development and Storybook-style previews so each screen renders realistic data on day one.
- `season.json`: season info, prize pool, all 9 sessions (dates, EP codes, titles, art, states).
- `players.json`: players with points, rank, movement, win rate, stats.
- `rivals-and-moments.json`: rival pairs and example moments (rep up, tier up, score settled).
- `session-night.json`: group A standings, live match, session 5 recap.

## Derived fields (client or server)
| Field | Rule |
|---|---|
| rep level | `repFor(points)` in `tokens.ts`: Rookie 0, Rising 80, Known 90, Legend 100. Never goes down in a season. Thresholds are config. |
| card tier | `tierFor(rank)`: #1 Legend, #2–3 Elite, #4–8 Pro, #9+ Street. Follows current rank. |
| gap (Most Wanted) | points of the player one rank above minus own points. |
| rival | the player directly above you on the table (existing tiebreak order). #1 has no rival; show `#2 chasing`. |
| head to head | matches where the two players were on opposing teams this season: W–L, plus the last 3 meetings (include same-team nights as "same team"). |
| bounty | season prize for ranks 1–3 if the season ended now (75 / 50 / 30 OMR). |
| take meter | `paidOMR / prizePoolOMR`; paid = finished sessions × 28 OMR. |
| card stats | SMASH = group-stage win rate · WALL = share of losses that were close or tiebreak · SPEED = knockout win rate · CLUTCH = tiebreak and comeback wins ÷ those matches. Scale 0–99; fewer than 3 matches → `—`. Proposal: confirm before building. |

## Moments (event triggers)
Fire on result lock, store "seen" per device so each shows once.
| Moment | Trigger |
|---|---|
| Rep Up | a player's rep level increases |
| New Crew Card | after a session finishes, once per player |
| Score Settled | your rank passes your rival's |
| Now Loading Muscat | app load; full sequence once per device per session day |

## Names (exact copy)
League: **Muscat Nights** (Arabic **ليالي مسقط**). Sessions: **EP.0N · TITLE**. Table: **Most Wanted**. Players: **The Crew** / **Crew Card**. Prizes: **The Take**. Loading: **Now Loading Muscat**. Finale: **The Big Score**. Passing your rival: **Score Settled**.

## Episode titles (editable placeholders)
EP.01 The Corniche · EP.02 The Arrival · EP.03 The Heat · EP.04 The Knockout · EP.05 The Smash · EP.06 The Grudge · EP.07 The Rematch · EP.08 The Crew · EP.09 The Big Score.

## Tips for Now Loading Muscat
- A tiebreak loss still earns 2 points. Never give up a set.
- Passing your rival on the table unlocks a share card. {rival} is {gap} points ahead of you.
- You're {n} points from {nextRep}.
- The Big Score on Wed 30 Dec is double points.
- Session champions get a 14 OMR voucher each.

## Not approved yet
- **Boss Kill +3** on the finale: keep `SEASON.bossKillBonus.enabled = false` and hide its row until the organiser approves. If approved, it must be a separate receipt line (`kind: BONUS`) so receipts still sum to series points.
