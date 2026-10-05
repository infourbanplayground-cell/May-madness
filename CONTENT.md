# Blackout Series — what to post, and when

Nine nights is eighteen weeks of attention to hold with a WhatsApp group and an
Instagram account. The constraint is not ideas, it is **who is free to make
something at the moment it is worth making**: at 19:40 on a Wednesday the
organiser is scoring a match, not opening a design tool.

So everything here comes out of the app, on the phone that is already in the
organiser's hand, built from scores that have already been entered. Nothing on
this page needs a laptop, and nothing needs anyone to type a name twice.

---

## The one rule

**Post the thing while it is still a question.**

The champions card is the most-made post in this series and the least
interesting, because by the time it exists everyone at the club already knows
who won. The group table posted at 19:30 — *two teams can still go through, one
of them is yours* — is the same data an hour earlier and worth ten times more.

Every card below is placed by that rule.

---

## A night, hour by hour

| When | Post | Where it is |
|---|---|---|
| **2 days before** | Sign-up sheet | `python3 ops/signup-post.py <n>` → WhatsApp |
| **Morning of** | Reminder + waitlist | Session screen → **Remind** |
| **~17:30, groups made** | **THE DRAW** | Session → **Posts** → THE DRAW |
| **~19:15, groups done** | **GROUP TABLES** | Session → **Posts** → TABLES |
| **~19:45, bracket seeded** | **THE BRACKET** | Session → **Posts** → BRACKET |
| **before each semi** | **SEMI 1 / SEMI 2 line-up** | Session → **Line-up** |
| **before the final** | **THE FINAL line-up** | Session → **Line-up** |
| **the moment it ends** | **NIGHT CHAMPIONS** | Line-up → CHAMPS (needs the final locked) |
| **+30 min** | Photos | Session → Photos, or the KO strip |
| **next morning** | **TOP 5** | ME → Share to story → TOP 5 |

Ten posts a night, nine nights. That is the whole volume's feed, and none of it
is invented — every card is a picture of something that happened.

### The three that are new

**THE DRAW** goes out before a ball is hit, which is the only moment in the
evening when nobody has lost yet. That is why it gets shared: everyone in it is
still in it. It deliberately does not number the teams — an ordered list reads
as a seeding the organiser decided, and it isn't one.

**GROUP TABLES** is the cliffhanger. Lime means through to the knockout, and it
comes from the same function the bracket seeds from, so it cannot promise a spot
the bracket then takes away. Posted *before* the last group match it is a
genuine "who goes through" question; posted after, it is a result.

**THE BRACKET** is the shape of the rest of the night. Post it once, then let
the line-up cards carry each tie.

---

## Between nights

Four or five days with no padel in them. This is where series die, and it is
also where the app now has more to say than the scoreboard does.

- **The chase.** Open RANK — your row is pinned at the top with the player
  nearest you and how many points separate you. Screenshot it. "Three points
  between 4th and 5th with four nights left" is a post.
- **A player's season.** ME → the rank line, night by night. Someone who went
  #19 → #4 has a story and the chart tells it in one look.
- **A badge.** ME → Share to story → BADGE. Giant killer, Comeback, Iron man.
  Best used for someone who would never post about themselves.
- **Chemistry.** Open a player card from the roster: head-to-head against you,
  and the pair's record as partners. "10–2 together" is a caption on its own.
- **The countdown.** Home carries days to finals night and the 75 / 50 / 30.
  Worth one post a week, no more.

---

## Captions

Every card has one ready — **COPY CAPTION** next to SHARE/SAVE. They are
deliberately plain: the card is the content, the caption is there so the post
carries the link. Rewrite them in your own voice; just keep the URL.

## What not to post

- The same card twice in a night. The table at 19:30 and the table at 21:00 are
  the same picture and the second one spends the first one's credit.
- A result nobody was waiting for. If a tie was never in doubt, post the photo
  instead.
- The prize pool on a match card. It is the season's number, not that match's,
  and next to two names it reads as the prize for winning the night. (The
  line-up cards had it; it was removed for exactly this reason.)

---

## Still worth building

Named here rather than built, because each is a real feature and should be
chosen, not assumed:

1. **A rivalry card.** Two players, the head-to-head, the last three meetings.
   All the data exists (`h2hDetail`); it needs a card and a way to pick the
   pair. The strongest candidate for the between-nights gap.
2. **A milestone card.** "100 points", "10 nights", "first title" — fired by
   the engine when it happens rather than spotted by eye.
3. **A season-ladder card.** The top ten with movement arrows after each night,
   so the series has a running story and not just nine separate evenings.
