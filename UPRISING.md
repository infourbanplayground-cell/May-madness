# UPRISING

*Urban Playground · a social format, not a volume*

**Come alone. Climb to Court One.**

---

## Why this exists

Vol.7's eight nights, measured from the archive:

| | |
|---|---|
| Players per night | 16–31 (median ~19) |
| Distinct players across the volume | 60 |
| **Played once or twice** | **35 of 60 — 58%** |
| Played 7+ nights | 4 |
| Pairs who played together more than once | 9 of 74 |

And across the series: **314 have signed up, 199 have ever played.** 115 people put
their name down and never made it onto a court.

The reason is printed on the sign-up sheet: *"Drop name + partner."* The series
asks a stranger to arrive with a friend, and most strangers don't have one yet.

So UPRISING is not a second tournament competing for the same Monday. It is the
**top of the funnel**: you arrive alone, you play with eight different people in
one evening, and you leave with eight people you could enter Blackout with.

The thing to measure after the first three nights is not attendance. It is **how
many new Blackout pairs came out of it.** That is what this is for.

---

## The format

**16 players. 4 courts. 9 rounds. Nobody sits out. Individual scoring.**

Courts are a **ladder**: Court 1 at the top, Court 4 at the bottom. Four players
on each court, playing 2 v 2.

### Each round

1. The four players on a court play one match to **16 points**, straight points,
   no games or sets. About 11 minutes.
2. **The winning pair moves up a court. The losing pair moves down.** Court 1
   winners stay on Court 1; Court 4 losers stay on Court 4.
3. Everyone re-pairs on their new court for the next round.

Nobody has to follow a table to know where they stand. They can see it — it is
the court they are standing on. That is the whole design.

### How partners are chosen

On each court the four players are ranked by their running total, and paired
**1 + 4 against 2 + 3**. Closest possible match, every round.

There are exactly three ways to split four players into two pairs, so when that
rule would repeat a partnership the engine takes the next-closest split that
does not.

Simulated over 120 nights of 16 mixed-ability players, that gives each player
**seven different partners in nine rounds** (median; worst case five). Not nine
— once a group settles on a court, three rounds exhausts the three possible
splits. Seven is still the product, and it is what the marketing should say.

A "one up, one down, two stay" ladder was tested as a way to churn court
membership faster and is **worse on both counts**: five distinct partners
instead of seven, and it picks a less deserving winner (true-skill rank as bad
as 14th, against 8th for pair movement). Pairs travelling together is the
better rule.

### Scoring — the court is the multiplier

Raw points cannot be the score. A player on Court 4 beating weaker opponents
scores more points than a player on Court 1 losing to the best in the room, so
ranking on raw points would reward staying at the bottom — the exact opposite of
the format.

So **points are worth more higher up the ladder:**

| | Win | Loss |
|---|---|---|
| **Court 1** | 8 | 4 |
| **Court 2** | 6 | 3 |
| **Court 3** | 4 | 2 |
| **Court 4** | 2 | 1 |

Losing on Court 1 is worth the same as winning on Court 3. That is deliberate:
it says *where you got to matters as much as what you did when you got there*,
and it keeps the climb worth attempting instead of farming wins at the bottom.

Maximum for a perfect night is 72. Ties break on **total match points scored**,
then on head-to-head. In simulation a real night spreads roughly 13 to 58, which
is wide enough for a table to mean something.

The format identifies a strong player without being a ranking tournament: across
120 simulated nights the winner was the strongest or second-strongest player in
the room about half the time, and occasionally someone from the middle has a
night. That is the correct amount of luck for a social.

### If the field isn't 16

**16 is a hard cap**, with a waitlist, like the series. Below that:

| Players | Courts | Note |
|---|---|---|
| 16 | 4 | the format as designed |
| 12 | 3 | identical, one rung shorter |
| 8 | 2 | a 90-minute version, 7 rounds |

Anything that is not a multiple of four drops to the next one down and the extras
take the waitlist. A rotating sit-out was considered and rejected: it makes the
scoring unfair (fewer rounds, fewer points) and it makes one person per round
the unlucky one, which is precisely the feeling this format exists to remove.

If more than 16 want in, run two sessions in an evening rather than stretching
one.

---

## The night

| | |
|---|---|
| Rounds | 9 |
| Match | first to 16 points |
| Per round | ~11 min play + ~2 min change |
| Total | ~2 hours |
| Start | 17:30 → finish ~19:40 |
| Matches per player | **9** |

For comparison, a Blackout night gives a player three group matches. This is
three times the padel in less time, with a different partner each time.

---

## What gets posted

The ladder is the content, and it changes every eleven minutes.

- **THE LADDER** — four courts stacked, who is on each, after every round. The
  card to post repeatedly through the night.
- **COURT ONE** — who is on the top court right now. Short, repeatable, and the
  one people screenshot.
- **THE CLIMB** — per player, their court across the nine rounds as a line going
  up. Personal, and the reason someone posts their own result.
- **PODIUM** — the top three at the end, with their totals.
- **TONIGHT'S PARTNERS** — the nine people you played with. This is the one that
  does the funnel's work: it is a list of names someone can act on.

---

## Why it needs its own app

It cannot be a mode inside the Blackout app. That engine assumes **one team per
player per session** — `getPlayerTeam()` returns a single team and every scoring
path is built on it. In UPRISING a player has a different partner every round.
That is not a setting, it is a different data model.

What carries over unchanged: the brand system, the share-card machinery, the
photo pipeline (cut-outs and all), the deploy scripts, the sign-up sheet
generator, and the roster of 314 people who already exist.

What is new: rounds instead of groups, a ladder instead of a bracket, individual
scores instead of team points.

**Home:** `americano.urbanpadel.om` already exists carrying Vol.1 and is the
natural place, or a fresh `uprising.urbanpadel.om`.

### Data model

```
round:   { no, courts: [ { court: 1..4, pairA: [pid,pid], pairB: [pid,pid],
                           scoreA, scoreB } ] }
player:  { id, name, photoUrl, courtPath: [1..4 per round],
           total, matchPoints, partners: [pid...] }
```

A night is `{ id, date, players: [...], rounds: [...], completed }`. Everything
else — the ladder, the leaderboard, the climb chart, who you partnered — derives
from that. Nothing is stored twice.

### The all-time question

UPRISING results should feed the **all-time** table and stay out of the series
table. The app already draws that line (`prevSeriesPts` vs the live series), so
it is a question of which bucket the night writes to, not new machinery.

---

## Open decisions

1. **Does a night count toward all-time points?** I would say yes — it is how
   the format earns its place for regulars — but at a lower weight than a series
   night, or the once-a-month crowd out-earns the people who turn up weekly.
2. **Entry fee and prize.** The series is 7 OMR with a 14 OMR voucher per winning
   player. A one-night individual format probably wants a smaller entry and a
   single winner's prize.
3. **Cadence.** Monthly reads as an event. Weekly reads as an alternative to
   Blackout and will split the regulars. I would start monthly, on a night the
   series does not use.
