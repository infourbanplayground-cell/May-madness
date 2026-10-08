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

1. The four players on a court play one match, **first to 16 points**, straight
   points, no games or sets. About 11 minutes. The target is set at check-in and
   can be anything — 11 for a short night, 21 for a long one. Nothing in the
   ladder depends on it: the court you are standing on decides the points you
   earn, and the scoreline only breaks ties. A round takes roughly
   `0.68 x target + 2` minutes including the change, which is the number the
   setup screen uses to tell you when the night will finish.
2. **The winning pair moves up a court. The losing pair moves down.** Court 1
   winners stay on Court 1; Court 4 losers stay on Court 4.
3. Everyone re-pairs on their new court for the next round.

Nobody has to follow a table to know where they stand. They can see it — it is
the court they are standing on. That is the whole design.

### Round one: the shuffle

> **Round 1 is the shuffle. Random courts, one match, no points. It decides where you start.**
> **From then on: win and you go up, lose and you go down.**

On night one nobody has form, so the opening ladder would be a draw — and a draw
decides far too much. Measured over 30,000 nights with a random opening ladder:

| Scoring rounds | Started C1 | C2 | C3 | C4 | Gap |
|---|---|---|---|---|---|
| 9 | **45%** | 31% | 17% | **6%** | **7.3×** |
| 15 | 40% | 29% | 20% | 11% | 3.7× |
| 25 | 35% | 28% | 22% | 14% | 2.4× |

Even would be 25% each. Two equally good players have a **seven times**
difference in their chance of winning, settled before a ball is hit, and a
longer night barely dilutes it — the advantage compounds rather than washes out.

A shuffle round fixes most of it:

| | Gap |
|---|---|
| Random draw, 9 scoring rounds | 7.3× |
| **Shuffle + 9 scoring rounds** | **2.7×** |
| **Shuffle + 15 scoring rounds** | **2.1×** |

What is left is *earned* — you are on Court 1 because you won a match, not
because of a hat. It costs one round of time, it is one sentence to explain, and
it needs no data, which is why it beats every seeding scheme for a room of
strangers. Behind the scenes the shuffle's own courts can still be seeded from
form where we have it; players never need to know, because the shuffle decides
the real start either way.

One detail that is not optional: **the shuffle is taken off the rest rota.** If
it consumed a normal slot, the player who happened to rest during it would spend
their rest on a round that pays nothing and so play every scoring round, while
everyone else played one fewer — 9 players over 9 scoring rounds came out 9
matches for one person and 8 for the other eight. Off the rota, the scoring
rounds divide evenly again.

The seeding note below therefore applies only when the shuffle is switched off.

### How partners are chosen

The **opening ladder is seeded by form** — a player's average from previous
UPRISINGs, their all-time points on a first appearance, newcomers in the middle.
Not drawn at random: see "where you start" below, where a random draw is shown to
be worth a five-fold swing in who wins.

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

**Players can see all of it, round by round.** The price of every rung is
printed on the ladder (`8/4`, `6/3`, `4/2`, `2/1`), every court card carries its
own stake before anyone serves (`WIN 8 · LOSE 4`), and the moment a result is
locked both pairs see what they earned and where they are going (`+8 HOLD COURT
1`, `+4 DOWN TO COURT 2`). Tapping any name in the table opens that player's
round-by-round receipt: court, scoreline, partner, which way they moved, what it
paid and the running total. A table that only shows a number at the end is a
result; this is feedback, and it is what lets someone play the ladder rather
than just play padel.

The receipt walks the same rounds the table walks and records each award as it
is made, so the two cannot disagree — there is a test that checks every player's
receipt ends on exactly their table total.


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

**Four to a court is padel, not a rule we chose. The FIELD does not have to be
a multiple of four.** It just means somebody sits out every round, and the whole
question is whether that can be made fair. Measured, it can:

| Players | Courts | Rest each round | Rounds | Everyone plays | Finish |
|---|---|---|---|---|---|
| 8 | 2 | nobody | 7 | 7 | ~1h45 |
| **9** | 2 | 1 | **9** | 8 | ~2h |
| **10** | 2 | 2 | **10** (or 5) | 8 (or 4) | ~2h15 |
| **11** | 2 | 3 | **11** | 8 | ~2h30 |
| 12 | 3 | nobody | 9 | 9 | ~2h |
| 16 | 4 | nobody | 9 | 9 | ~2h |
| **20** | 4 | 4 | **10** | 8 | ~2h25 |
| 24 | 4 | 8 | 5 or 10 | 3 or 6 | ~1h20 / 2h25 |

With P players and R resting each round, N rounds deal N×R rests, so they share
out exactly when **P divides N×R**. That is where each round count above comes
from. The app works it out and picks it for you.

**Four courts is the ceiling**, because the points table has exactly four rungs.
20 players would otherwise ask for a fifth court that has no points defined for
it. The club has four anyway — the ladder is as tall as the venue.

Rest goes on **a rota drawn at the start of the night and walked in order**, so
when your turn comes it has nothing to do with how you are playing. The first
attempt broke rest ties by ladder position, which quietly handed the early
rounds off to the weak players and the double final off to the strong ones.

#### The double final is off whenever anybody sits out

Measured over 20,000 nights of 9 players: with the 2× final on, whoever draws
the final-round rest takes **3.6%** of the wins against the **11.1%** that would
be their fair share. They cannot win the night, for a reason they had no say in.
With a flat final it is 13.6% — slightly generous, which is the right direction
for a social. So the multiplier is a property of the field, not of the format:
**16 or 12 players, the last round doubles. 9, 10, 11 or 20, it does not.**

#### Where it stops working

Every field from 8 to 40 was played through the engine at the defaults. **None
of them crash and none fail the validator** — but there are three different
ways a size stops being a good night.

**1. Under 8 — refused.** One court is not a ladder. Four to seven people
should run classic Americano, which the same app does.

**2. Sizes that cannot divide evenly in an evening.** 25, 27, 29, 31, 33, 35,
37, 39 — each has exactly one even round count and it is 25 to 39 scoring
rounds, five hours or more. These always rank on points per round. That is
fair, just less tidy, and the setup screen says so rather than offering a
number nobody can play.

**3. Too many people standing still.** Four courts seat sixteen, so everyone
past that is in a queue:

| Players | Off court every round | Matches each over 15 rounds |
|---|---|---|
| 16 | **nobody** | 15 |
| 20 | 20% | 12 |
| 24 | 33% | 10 |
| 28 | 43% | 8 |
| 32 | **50%** | 7 |
| 40 | 60% | 6 |

Past about **21** the format is a queue with a scoreboard. The setup screen
warns from 30% and suggests two shorter sessions instead. **24 is the practical
ceiling** — it is still even, and ten matches each is a real night.

**The sizes that come out exactly even at the default 15 scoring rounds:**
**8, 10, 12, 15, 16, 20, 24, 30, 40.** Of those, 8, 12 and 16 are perfect —
nobody rests at all.

#### If you run a different number of rounds

You can. The rests then come out uneven — some play one more match than others —
and the table **must** switch to points per round played. This is not a nicety.
Over 20,000 nights of 11 players across 9 rounds:

| Ranked on | Players who rested twice | Players who rested three times |
|---|---|---|
| **Raw points** | 55% of the field took **94% of the wins** | 45% took 6% |
| **Points per round played** | 55% took 58% | 45% took 42% |

One extra match decided the night. The app detects uneven rests and switches the
table automatically, and says on screen that it has.

A rotating sit-out was once rejected here on the grounds that it "makes the
scoring unfair and makes one person per round the unlucky one". The first half
was right and is fixed by the two rules above. The second half was wrong: at 9
players you sit out **one round in nine**, and the alternative was turning
people away at the door.

---

---

## The night, as it is set up today

The app opens on these, so the organiser types nothing:

| | |
|---|---|
| Players | 16, four courts |
| Round 1 | **the shuffle** — sets the courts, scores nothing |
| Scoring rounds | **15** |
| Match | **first to 13** |
| Matches each | **16** |
| Finish | about **2h53** from the first serve |
| Last round | **double** |

`Scoring rounds` means rounds that count. The shuffle sits on top of it, not
inside it — ask for 15 and you get 15 that score, plus the shuffle, 16 matches.

Measured on a full night played through the app: everybody plays all 15 scoring
rounds, 960 points are awarded in total (14 normal rounds at 60 plus 120 for the
doubled final), the table spreads about 25 to 80, and players meet 10 to 13
different partners out of a possible 15.

## The night

| | |
|---|---|
| Rounds | **the organiser's**, 2 to 40. 9 is the default because it fits two hours, not because anything counts to nine. The last round is worth double |
| Match | first to 16 points — **the organiser sets the target**, any number from 4 to 99 |
| Per round | ~11 min play + ~2 min change |
| Total | ~2 hours |
| Start | 17:30 → finish ~19:40 |
| Matches per player | **9** |

For comparison, a Blackout night gives a player three group matches. This is
three times the padel in less time, with a different partner each time.

---

### How long, and how many rounds

Nine was a **time budget**, not a rule — nothing in the ladder or the points
table counts to nine. A longer night is a measurably better competition, run on
the real engine over 3,000 nights of 16 players:

| Rounds | Distinct partners (min/median/max) | Winner is a true top-3 player | Table vs true skill | Finish, first to 16 |
|---|---|---|---|---|
| 7 | 4 / 7 / 7 | 56% | 0.56 | 1h30 |
| **9** | 5 / 8 / 9 | 61% | 0.62 | **1h56** |
| 11 | 5 / 9 / 11 | 64% | 0.67 | 2h22 |
| 12 | 5 / 9 / 12 | 67% | 0.69 | 2h35 |
| **15** | **6 / 11 / 14** | **69%** | **0.73** | 3h13 |
| 19 | 6 / 12 / 15 | 73% | 0.76 | 4h05 |

A round takes about `0.68 x target + 2` minutes including the change, so the
target is the lever that makes a long night fit: **15 rounds at first to 13 is
2h43**, where 15 at first to 16 is 3h13.

Two things flatten off. **Partners**: a court of four has only three ways to
split, so past about round 11 you start meeting the same partner again — 15
rounds gives a median of 11 different partners, not 15. **Fairness**: each extra
round is worth less than the one before, and the 9 → 12 step buys more than the
12 → 15 step.

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

## Can someone come back and still win?

Measured over 3,000 simulated nights.

| | |
|---|---|
| Nights where the **last round changed the winner** | **20%** |
| Winner was outside the top 3 at halfway (round 5) | 13%, from as low as **8th** |
| Winner was outside the top 3 a third of the way in (round 3) | 28%, from as low as **11th** |
| Biggest points deficit overturned in the final round | **6** — one Court 1 win against a Court 3 win |
| Won from the **bottom court at halfway** | **0 of 3,000** |

So: yes, and often. One night in five comes down to the final round, and a
player sitting eighth at halfway can still take it. What cannot happen is a
comeback from the bottom court after round 5 — by then you need to already be
climbing. That is the right shape for a two-hour format: live to the end, but
not a lottery.

### Make the last round double

Weighting the ninth round at 2× takes "the last round decided it" from **20% of
nights to 31%** — one in three. It costs nothing, it is one line in the engine,
and it is worth announcing out loud before the round starts. Everyone on every
court still has something to play for at 19:30, which is the hour a social
normally dies.

### The thing that actually needs fixing: where you start

Starting court is worth more than it should be if it is drawn at random:

| Started on | Share of wins |
|---|---|
| Court 1 | **40%** |
| Court 2 | 31% |
| Court 3 | 20% |
| Court 4 | **8%** |

Even money would be 25% each. A random draw therefore hands one player a
**five times** better chance than another before a ball is hit — and that is
luck deciding who takes a voucher.

**So seed the opening ladder by form**, not at random: previous UPRISING average,
or all-time points for a first appearance, with newcomers placed in the middle.
Then Court 1 at 40% is not luck, it is the reigning form player starting where
they earned, and the ladder is doing its job from round one instead of spending
three rounds sorting itself out.

That makes the CHAMPION prize *more* merit-based, which is the point of it. The
openness lives in the second prize, below — not in randomising the start.

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
