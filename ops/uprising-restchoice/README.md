# Choosing who rests — prototype, NOT shipped

Problem (seen live on 24 Oct): with a field that is not a multiple of four,
returners hold their court, a court gets more claims than seats, and a player
who just WON is held on their court instead of climbing. At 15 on 3 courts:
3.5 a night, on 98% of nights. 12 and 16 players: never.

`engine-fair-seated.js` is the shipped engine plus `upChooseResters`:
- rests in CYCLES — nobody rests twice until everyone has rested once, so
  rests stay exactly equal;
- among those still owed a rest, every possible set is SEATED (`upSeatFor`)
  and scored: no back-to-back rest, then fewest 2-court jumps, then fewest
  held winners, then fewest losers spared; the random rota breaks ties.

Measured (equal skill unless said), 15 on 3 courts, 10 scoring rounds:

| | today | fair-seated |
|---|---|---|
| winners held | 3.5/night | 0.6/night |
| 2-court jumps | 0.34/night | 0.03/night |
| rests | 2 each | 2 each |
| halfway leader wins | 45.7% | 43.5% |
| bottom half reaches top 3 | 0.9% | 1.5% |
| who is rested (top/mid/bottom third, 1st half) | 39/36/25 | 38/38/25 |
| best player wins (real skill) | 29.6% | 30.5% |

It does not entrench leaders and does not target anyone by standing. The
"first rest round predicts the title" spread grows (1.6x -> 2.9x) but that is
selection, not advantage: who gets rested, by table position, is the same as
the random rota's.

Before it can ship: unit tests, ops/uprising-stress.js, uprising-courtchange.js
and uprising-fairness.js against it; check every app screen that PREVIEWS who
rests next (the rota is no longer the schedule); re-deal after a correction may
change an unscored round's resters. Never on the day of a night.

    node compare.js <engine.js> 15 3 10 3000
    node restwhen.js <engine.js> 15 3 10 6000
    node entrench.js <engine.js> 15 3 10 4000
