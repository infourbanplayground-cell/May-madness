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

## The prize, and whether anyone else can win it

One voucher for one winner does not survive contact with a mixed field. Simulated
over 200 seasons of twelve monthly nights, with a pool of 24 regulars of whom 16
turn up each time:

| Prize rule | Nights won by a top-3 player |
|---|---|
| **Scratch** — most points | **70%** (78% if the ladder is seeded by form) |
| **Handicap** — most above your own average | **21%** |
| **The Rise** — biggest climb from your starting court | 37% random ladder, **6%** seeded |

The top 3 of 24 are 12.5% of the room, so that is the number a genuinely open
prize should sit near.

**Scratch alone means three people take three quarters of the vouchers.** That is
the problem, confirmed. But removing it is worse: a prize nobody good can win is
a prize the good players stop turning up for, and they are the ones who make the
top court worth climbing to.

### So: two vouchers, same budget

| | |
|---|---|
| **CHAMPION** | Most points. Won on merit, by whoever was best on the night. |
| **THE CLIMB** | Most points above **your own running average**. Open to anyone. |

At 21% the handicap prize still rewards playing well — it is not a raffle — but
it is winnable by anyone in the room on a good night. And it self-corrects: win
it by overperforming and your average rises, so next month the bar is higher.
Nobody can farm it.

The series already pays 14 OMR to each of two winning players per night. Two
vouchers here is the same spend, and the same shape: one for the best, one for
the best against themselves.

**A first-timer's baseline is the field average**, which is deliberately
generous. A newcomer can win THE CLIMB on their first night. For a format whose
whole job is converting people who have never played, that is a feature.

### What not to award

**Do not make "biggest climb up the ladder" a prize if the opening ladder is
seeded by form.** At 6% it is not an open prize, it is an inverted one — a strong
player starts on Court 1 and mathematically cannot win it. Keep the climb as a
story and a share card, not as money.

### The one thing to watch

A handicap built from your own history can be gamed by losing on purpose one
month to lower the bar for the next. Three things make it not worth doing: the
voucher is small, the average is computed from recorded results rather than
anything self-declared, and tanking a night in front of fifteen people who can
see which court you are on carries its own cost. If it ever does happen, the fix
is to compute the baseline from a player's **best four of their last six nights**
rather than a plain average, which makes a deliberate bad night worthless.

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
