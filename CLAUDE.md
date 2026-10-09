# Urban Padel — Claude Operations Context

This repo is the working base for managing **urbanpadel.om** and its associated VPS.

## Server Access

The session-start hook (`.claude/hooks/session-start.sh`) automatically:
- Installs `openssh-client` if missing
- Extracts the SSH key from the uploaded kit zip
- Downloads the chisel binary
- Opens an SSH-over-HTTPS tunnel to the VPS via `sshws.urbanpadel.om`
- Writes the `urbanpadel` SSH alias to `~/.ssh/config`

After the hook runs, connect with: `ssh urbanpadel 'echo ok'`

**If the tunnel drops mid-session**, re-run:
```bash
/tmp/chisel client --keepalive 25s --auth mouther:ca4ac97f11f618067ca6564606a226d8 https://sshws.urbanpadel.om 2200:127.0.0.1:22 > /tmp/chisel.log 2>&1 &
sleep 4 && grep Connected /tmp/chisel.log
```

## Server Quick Reference

| Item | Value |
|---|---|
| IP | 76.13.221.95 (Hostinger KVM1, Ubuntu 24.04, KL) |
| SSH user | root |
| Web root | `/var/www/urbanpadel.om/public` |
| Main site | https://urbanpadel.om (the club's front door — see below) |

## The Front Door (urbanpadel.om)

- Source: **`landing/index.html`** — deploy with `bash ops/deploy-landing.sh`.
  It lived only on the server until Oct 2026, so the one page every visitor sees
  first had no history; edit the repo copy, never the file on the VPS.
- Shape: NOW PLAYING (the running volume, as a hero panel) → THE CLUB (book /
  shop, both Coming Soon) → THE ARCHIVE (every finished volume, newest first).
- **Rolling a volume over** means three edits: point the NOW PLAYING block at the
  new app, add the finished one to the top of THE ARCHIVE with its champion, and
  move the `--live` token to the new volume's accent. `--live` covers everything
  except a few `rgba()` glows that need the colour as components — search for the
  old accent's `rgba(` triple and move those too, or the panel glows stay the
  previous volume's colour around the new one's lockup.
- The hero wants the **stacked** lockup (`brand/<vol>/*-stack.*`), not the
  horizontal one: at `max-width:430px` a 3.7:1 lockup stands 117px high and reads
  as an afterthought in the one place it is the hero. Stacked it stands 242.
- The deploy script verifies the live art is **byte-identical** to the local
  file, not merely 200: Cloudflare will happily serve a cached copy of the old
  art, which looks exactly like a successful deploy.

## Owner's Apps

### June Fury (Americano tournament)
- URL: https://americano.urbanpadel.om
- Frontend: `/var/www/americano.urbanpadel.om/public/` — local copy: `june-fury-index.html`
- API: `/opt/june-fury-api/api.js` — systemd: `june-fury-api` — port 3001
- Deploy frontend: `scp june-fury-index.html urbanpadel:/var/www/americano.urbanpadel.om/public/index.html`
- Deploy API: `scp api.js urbanpadel:/opt/june-fury-api/ && ssh urbanpadel 'systemctl restart june-fury-api'`

### WC2026 Predictions
- URL: https://predictions.urbanpadel.om
- Frontend: `/var/www/predictions.urbanpadel.om/public/index.html` — no local copy (edit live or scp down first)
- API: `/opt/wc-predictions-api/predictions-api.js` — systemd: `wc-predictions` — port 3002
- Backup: `/opt/wc-predictions-api/predictions-api.js.bak`
- Deploy: `scp predictions-api.js urbanpadel:/opt/wc-predictions-api/ && ssh urbanpadel 'systemctl restart wc-predictions'`
- Deploy frontend: `scp index.html urbanpadel:/var/www/predictions.urbanpadel.om/public/index.html`

#### WC Predictions DB Schema (PostgreSQL)
Table `wc_matches`:
```
id, home_team, away_team, home_flag, away_flag,
home_odds NUMERIC(6,3), draw_odds NUMERIC(6,3), away_odds NUMERIC(6,3),
odds_1x NUMERIC(6,3),   -- double chance Home/Draw (optional, falls back to harmonic)
odds_x2 NUMERIC(6,3),   -- double chance Draw/Away (optional, falls back to harmonic)
kickoff TIMESTAMPTZ, venue TEXT, result TEXT, group_name TEXT, stage TEXT
```

Table `wc_predictions`:
```
id, player_id, match_id, prediction TEXT,  -- '1','X','2','1X','X2','12'
odds_locked NUMERIC(10,4),  -- odds at bet placement time (locked forever)
stake NUMERIC(10,2), payout NUMERIC(10,2), settled BOOLEAN
```

Key migrations (idempotent, run in initDB every restart):
```sql
ALTER TABLE wc_predictions ADD COLUMN IF NOT EXISTS odds_locked NUMERIC(10,4);
ALTER TABLE wc_matches ADD COLUMN IF NOT EXISTS odds_1x NUMERIC(6,3);
ALTER TABLE wc_matches ADD COLUMN IF NOT EXISTS odds_x2 NUMERIC(6,3);
-- Backfill odds_locked for any bets placed before the column existed
UPDATE wc_predictions p SET odds_locked = CASE p.prediction
  WHEN '1'  THEN m.home_odds  WHEN 'X' THEN m.draw_odds  WHEN '2' THEN m.away_odds
  WHEN '1X' THEN COALESCE(m.odds_1x, ROUND((m.home_odds*m.draw_odds)/NULLIF(m.home_odds+m.draw_odds,0),4))
  WHEN 'X2' THEN COALESCE(m.odds_x2, ROUND((m.draw_odds*m.away_odds)/NULLIF(m.draw_odds+m.away_odds,0),4))
  WHEN '12' THEN ROUND((m.home_odds*m.away_odds)/NULLIF(m.home_odds+m.away_odds,0),4)
  ELSE m.home_odds END
FROM wc_matches m WHERE p.match_id=m.id AND p.odds_locked IS NULL;
```

#### WC Predictions Features
- **Odds locking**: odds captured at bet placement (`/wc/predict`), stored in `odds_locked`, used for settlement and display forever
- **Double chance**: `1X` (Home/Draw) and `X2` (Draw/Away) bet options; stored explicitly in `odds_1x`/`odds_x2`, fallback is harmonic mean: `(h*d)/(h+d)` and `(d*a)/(d+a)`
- **Auto-recalculate on odds edit**: `PUT /wc/admin/match/:id` — if match is settled and has a result, diffs old vs new payout per prediction and adjusts player balance automatically; also updates `odds_locked` on each prediction to corrected odds
- **Admin DC odds editing**: admin panel has two rows in odds form — row 1: 1/X/2, row 2: 1X/X2 (optional)
- **My Picks auto-expand**: in Fixtures tab, switching to "My Picks" filter auto-shows finished matches

### Americano + UPRISING
- URL: https://americano.urbanpadel.om — local copy: `americano-index.html`
  (it had **no copy in the repo until Oct 2026** and lived only on the server,
  the same way the landing page did; the repo is the source now)
- API: `/opt/americano-api/api.js` — systemd: `americano-api` — port 3007
- Tables: `americano_state`, `americano_photos`. The API stores the whole state
  as one JSON blob and never validates its shape, which is why UPRISING needed
  **no new API, no new port and no new tables** — it is another entry in
  `state.tournaments`.
- The API serves players live out of August Attack's DB and deletes
  `state.players` on save, so the roster is shared and never forked.
- Two formats in one app, chosen at setup:
  - **AMERICANO** — the circle method, so everyone partners everyone exactly
    once. Courts can be capped; sit-outs rotate; if the schedule cannot give
    everyone the same number of matches the table switches to points per match.
  - **UPRISING** — a court ladder. 4 courts, 9 rounds, nobody sits out, winners
    up and losers down, points worth more higher up, last round double. The
    reasoning and the simulations behind every number are in `UPRISING.md`.
- **The UPRISING rules live in `uprising-engine.js` and nowhere else.**
  `build-americano-app.py` inlines that file into the page between two markers
  and refuses to build if the engine declares a name the app already has — the
  engine's helper was once called `pairKey`, which the app also defines, and a
  duplicate declaration is a SyntaxError that blanks the **entire** page rather
  than breaking one screen.
- Deploy: `node --test uprising-engine.test.js && python3 build-americano-app.py && bash ops/deploy-americano.sh`
- **`ops/uprising-stress.js` is the one that finds real bugs.** `node ops/uprising-stress.js 25000`
  builds that many randomised nights against the shipped engine — random field
  8–32, courts, target, shuffle on/off, planner-chosen or hand-set round counts —
  and asserts every invariant: four to a court, nobody in two places, rests
  balanced within one, each player's receipt reconstructing their table total,
  points conserved against what the courts owe, the double final applying iff
  nobody rests, the table sorted by the mode it claims, and the climb path never
  visiting a court that does not exist. It also replays a scorer correcting a
  typo three rounds back, which the unit tests never covered. The unit tests
  check cases somebody thought of; this checks the ones nobody did — it is what
  caught upClimbPath clamping to four courts on a two-court night.
- **RULES is a screen in the app**, not a document — a fifth nav tab. Every
  number on it is read from the engine (`UP.WIN`, `upCourts`, `upScoringRounds`,
  `upPlanRounds`), never typed, and it describes the ACTIVE night when there is
  one and the current setup when there is not. A rules page that can disagree
  with the scoring is worse than none: players trust it, and the first time it
  is wrong they stop trusting the table too.
- The shareable format graphic is `brand/uprising/format-card.html`, rendered by
  `node ops/render-uprising-card.mjs` to a 1080x1350 PNG. The renderer **fails if
  any element runs off the canvas** and if the display face is not Archivo at
  `wdth` 125 — the Blackout lockup once shipped with letters sliced off by the
  edge of the bitmap while every assertion passed, because they were all about
  the font and none about where the ink landed. Its numbers are hand-written, so
  re-check them against the RULES screen when the defaults move.
- **The announcement lives in `uprising-social.json`** — date, time, entry,
  prizes, cap. The FORMAT numbers are deliberately NOT in it: `ops/uprising-facts.mjs`
  reads courts, rounds, target, running time and the points table out of the
  shipped engine, so a post cannot advertise a figure the app contradicts (the
  same discipline as `blackout-season.json`). Build with
  `python3 build-uprising-announce.py && node ops/render-uprising-announce.mjs` —
  **four 1080x1350 feed cards, five 1080x1920 stories** (`story-1-name`,
  `-2-ladder`, `-3-match`, `-4-prizes`, `-5-claim`) and `CAPTIONS.txt`, which
  carries four WhatsApp posts (announcement, short, day-of reminder, "what even
  is it?"), the Instagram carousel caption and a sticker plan per story. The
  renderer sizes anything named `story-*` at 1920 and everything else at 1350,
  and fails on any element that runs off its canvas; pass `PW_CHROMIUM` in a
  container where Playwright has no headless shell.
- **The sign-up list is `ops/uprising-signup.py`** — the WhatsApp numbered sheet
  people reply into, the sibling of `ops/signup-post.py` for Blackout. Two
  differences that matter: it counts 16 **people**, not teams (Blackout asks for
  "name + partner", and assuming you need to find one first is the single most
  likely reason somebody does not reply), and the cap is `min(cap, engine
  players)` rather than a typed 16, so it cannot take names for places that do
  not exist. `--full` prepends the format block for a group that has not seen
  the cards; the two write different files so a run of one does not take the
  other away. Palette is 🟩/🟪 and nothing else — WhatsApp has no colour, and a
  post wearing six unrelated emoji reads as spam rather than as a series.
- **The short list does not explain the format — the LINK does.** The default
  post is four lines, the link, and the numbered list. The explaining moved to
  the **link preview**: `americano-index.html` carries `og:` tags between
  generated markers and serves `og-card.jpg` beside it, so the unfurl under the
  post is the format. The link sits *above* the list, where the preview renders,
  not at the bottom as a footnote.
  - The tags are **generated by `build-uprising-announce.py`**, not typed: the
    description carries the date, which is right for a month and quietly wrong
    after that, on the one surface nobody re-reads. The builder refuses if the
    markers are missing and warns if the description passes 150 characters,
    which is roughly where WhatsApp cuts it.
  - `og:image` must be an **absolute** URL (a relative one is silently ignored)
    and small: WhatsApp fetches it inline while you type and drops anything
    much over ~300KB, showing a bare grey row instead. `ops/make-og-jpeg.py`
    takes the 2x render down to 1200x630 JPEG and steps quality until it fits
    — currently **68KB at q88**.
  - The image is a separate file on the VPS, so deploying the app alone does
    not ship it:
    ```bash
    python3 build-uprising-announce.py && \
      PW_CHROMIUM=... node ops/render-uprising-announce.mjs && \
      python3 ops/make-og-jpeg.py
    scp brand/uprising/posts/og-card.jpg urbanpadel:/tmp/og-card.jpg
    ssh urbanpadel 'cp /tmp/og-card.jpg /var/www/americano-app/public/og-card.jpg'
    python3 build-americano-app.py && bash ops/deploy-americano.sh
    ```
    Verify with the crawler's own eyes, not the browser's:
    `curl -s -A "WhatsApp/2.23" https://americano.urbanpadel.om/ | grep og:`
    and check the served image is **byte-identical** to the local one.
- Each story card repeats the name and the date, because a story is watched one
  frame at a time and most people see one of the five. The deep top/bottom
  padding is not whitespace for its own sake — Instagram draws its own chrome
  over roughly the top 170px and the reply bar over the bottom 200px.
- **The champion's prize is a voucher and every line says so.** `championPrizeKind`
  in the JSON prints under the figure on the cards and inside the sentence in the
  copy. "Champion takes 15 OMR" reads as cash, and somebody arriving expecting
  notes was misled by our own poster.
- **The brand faces are vendored in `brand/fonts/`** (`ops/vendor-fonts.py`,
  Archivo + JetBrains Mono, Latin subsets, ~446KB). Chromium in this container
  does **not** trust the agent proxy's CA, so a `<link>` to fonts.googleapis.com
  fails with `ERR_CERT_AUTHORITY_INVALID` — and a webfont that fails to load is
  not an error, it is a silent fallback. The whole five-card story series once
  rendered in **Times** with every assertion green.
- Both renderers now prove the face was really **drawn**, not merely asked for.
  `getComputedStyle().fontFamily` reports the family in the stylesheet whether or
  not it loaded, and `document.fonts.check()` answers *true* with zero faces
  loaded — so the only honest test is to measure a probe string in the face and
  in one it cannot be (`monospace`, `serif`) and fail if the widths match.
  Proved by deleting the stylesheet link: `FONT NOT LOADED: Archivo,
  JetBrains Mono`, exit 1.
- **Both renderers check the INK, not just the box.** An element can sit inside
  the canvas while the text in it runs out the side — `scrollWidth > clientWidth`
  is the test. UPRISING at 184px lost its G off the right edge of the hero and
  the old box-only check passed it, which is the same failure DESIGN.md records
  for the Blackout lockup. Display type that must fill a width carries
  `data-fit` and is shrunk after `document.fonts.ready` (the fallback face
  measures narrower than Archivo at `wdth` 125, so sizing before that sizes
  against the wrong letters).
- **The shuffle SETS the ladder, it does not nudge it.** `upShuffleLadder`
  ranks everyone by their shuffle **margin** and deals the courts from that:
  biggest win on Court 1, biggest loss on the bottom. Anyone who rested the
  shuffle has no margin and goes to the middle, the same way `upSeedLadder`
  treats a player with no form.
  - It used to be an ordinary round — you moved one court from wherever the
    draw put you — so the draw still decided most of your start. Measured over
    3,000 equal-skill nights at 16 players on 4 courts, check-in order was
    worth **1.20x** in final points (61.7 against 51.2). It is **1.00x** now,
    at every field size from 9 to 24, and competition is unchanged: the best
    player wins 24.1% of nights, top-3 56.2%, rank error 3.18 (was 3.26).
  - **Ties are broken by the rest rota, never by id.** `upSeedLadder` ties by
    id too, so on night one the draw IS id order — breaking the margin ties the
    same way quietly rebuilt the very order the shuffle exists to destroy. Each
    seat averaged identical points while grouping by seeded court still showed
    1.25x at 24 players. The rota is a random permutation drawn once and stored,
    so it is stable across reloads and owes the draw nothing.
  - **`upLadderOrder` had the same fault**, and it is the one that compounds:
    level on court and on points, it seated the earlier id higher every round
    for the whole night. That was the residual 1.16x at 20 players. Both now
    tie-break on the rota. If you add another tie-break anywhere in this engine,
    do not reach for the id.
  - The shuffle ladder is computed against the courts the **shuffle round** was
    played on, not the night's current count, so a mid-night court change does
    not re-deal it.
  - Both the RULES screen and the home page say the margin decides it, because
    it changes how people play that match — a 11-2 shuffle win from the bottom
    of the draw opens on Court 1.
- **The shuffle can be 0, 1 or 2 rounds.** `night.shuffle` is a COUNT, read by
  `upShuffleRounds` — `true` still means 1, so nights created before this keep
  working. Chosen on the setup screen; margins SUM across the shuffle rounds,
  and round 2 is itself seated from round 1's margin ladder.
  - One shuffle round is one data point per player, and a single 11-1
    thrashing can put a good player on the bottom court for the night. Measured
    at 16 players on 4 courts over 3,000 nights, the opening ladder separates
    the strongest quarter from the weakest by **0.60 courts after one shuffle
    and 0.83 after two**; the best player then takes the night 24.4% of the
    time against 23.6%, with the same clock, because the second shuffle costs a
    scoring round.
  - The shuffle rounds come off the TAIL of the rest rota, walking backwards,
    so they never consume a scoring round's rest slot and nobody sits out both.
  - `upPlanRounds` subtracts the real count; planning for one would overrun the
    finish time by a round.
- **Margin is for the shuffle and nothing else.** Scoring stays flat 8/6/4/2 and
  ignores the score; pairing within a court still ranks on running court-points.
  Measured over 104,000 courts, ranking the pairing on point difference instead
  cuts the mean skill gap between the two pairs from 0.3328 to 0.3269 — 1.8%,
  against 0.1550 for perfect knowledge and 0.5982 for the worst split. The
  bottleneck is which court you are on, not how the four of you are divided, so
  it is not worth a rule players would have to be told about.
- **Courts can change MID-NIGHT**, which they could not before — a court frees
  up or is taken away at 7pm and the alternative used to be abandoning the
  session. `Change courts` is live on an UPRISING board and does NOT call
  `rebuildTail` (that is the classic Americano circle method and would overwrite
  the ladder); it sets `courtCount` and the next round is dealt on it.
  - **Every round carries its own court count** — `upRoundCourts(r)` is
    `r.courts.length`, a fact about history. `upCurrentCourts`, `upValidate`
    and `upClimbPath` all resolve each round against the count IT was played
    on, so gaining a court at round 7 cannot reach back and drop somebody into
    a Court 4 that did not exist in round 2. The final court map is then
    clamped to the current count, which is what brings down anyone left
    standing on a court that has gone — including whoever was resting when it
    went, since no round moves them.
  - The app deals the next round the instant the last score is locked, so by
    the time the organiser opens the sheet the round on the board is already
    drawn on the OLD count. If it has **no scores in it** it is re-dealt; a
    round with so much as one score is history and is left alone. Without this
    the change lands a round later than it was made — the round the court
    actually became free.
  - `upDoubleFinal` reads the LAST ROUND'S OWN sitOuts once it has been played,
    not the night's current setting, so taking a court away afterwards cannot
    retroactively un-double the decider and move every total on the table.
  - Rests cannot come out even across a change — the rota stops part-way — so
    `upValidate` drops the within-one rest check when the count changed, and
    `upUneven` goes true, which puts the table on **points per round played**.
    Nobody wins on extra court time. That is the existing safety net doing the
    job it was built for.
  - **`ops/uprising-courtchange.js` is the harness for this** (`node
    ops/uprising-courtchange.js 6000`): random field, random count before and
    after, random round to change at, asserting played rounds never move,
    points on the board never move, nobody stands on a court that does not
    exist, the night still finishes, receipts still reconstruct the table and
    points stay conserved. Neither the unit tests nor `uprising-stress.js`
    covered this — both fix the court count at setup.
- **The first night advertises ONE prize**: `"secondPrize": false` in the JSON.
  The prize cards carry a single CHAMPION block and a LAST ROUND DOUBLES note
  in place of the runner-up, and no caption mentions a second prize — a prize
  that is advertised and then not handed out is worse than never offering one.
  `upPrizes()` still computes a second one (the stress harness asserts on it)
  and nothing reads it. Set `secondPrize` true to put THE CLIMB back and every
  card and caption re-renders with the second block.
- **THE CLIMB is per scoring round, and cannot be awarded on night one.**
  Baselines are points per round — nights are sized to the clock, so comparing
  a 14-round total with a 10-round total made 14 of 16 players look worse and
  handed the prize to the champion. And with no history at all every baseline
  is the field average, the same number for everyone, so the rule collapses
  into "most points": the champion won both in 2000 of 2000 simulated first
  nights. `upPrizes` now returns `climb: null, secondRule: "finisher"` in that
  case and the second prize is the STRONGEST FINISH (second half minus first),
  which is the champion only 7% of the time. Flip `firstNight` in
  `uprising-social.json` to false after the first night.
- **First UPRISING: Saturday 10 Oct 2026, 7 OMR, 16 places.**
  Champion takes a 15 OMR **voucher** and that is the only prize advertised.
  Change the date
  in the JSON and every card and caption re-renders, including the date block,
  which reads TOMORROW or TONIGHT while that is true and the date otherwise.
  **The posts carry no clock times and no durations** — the start is fixed when
  the court is confirmed, and a poster reshot because the time moved is worse
  than one that never claimed it. The app's RULES screen still carries both.
- June Fury (Vol.1) used to share this directory. It now has its own at
  `/var/www/june.urbanpadel.om/public`, still on port 3001, so the landing
  page's archive link survives.

### Booking App (Court reservations)
- URL: https://bookings.urbanpadel.om
- Source: `/home/user/May-madness/booking-app/`
- App dir on VPS: `/opt/booking-app` — systemd: `booking-app` — port 3003
- See `.claude/commands/deploy-booking-app.md` for full deploy steps

### Blackout Series (Vol.8 — LIVE APP)
- URL: https://blackout.urbanpadel.om — October 2026, nine nights
- Local copy: `blackout-index.html`, **generated** by `build-blackout-app.py`
  from `september-surge-index.html`. Do not hand-edit it: fix Vol.7 and re-run
  the script, which is how a volume inherits the previous one's markup
  (July Heat → August Attack → September Surge → Blackout). Every rename is
  asserted, so a string that stops matching fails the build rather than shipping
  a half-rebranded app.
- Season numbers live in **`blackout-season.json`** — the app, the brand art and
  the signup posts all read it, so none of them can advertise a figure the others
  contradict. Nine nights, 2X from session 8, season 75/50/30, 14 OMR vouchers,
  7 OMR entry, **no finals cut** (session 9 is open like any other night).
- **Prize pool is derived, not typed: 14 × 2 × 9 + 155 = 407 OMR.** The handover
  said 402, which does not add up from its own parts. If 402 is the real budget,
  change a part in the JSON (8 paying nights, or a 70/50/30 split), not the total.
- API: `/opt/blackout-api/api.js` — systemd: `blackout-api` — port **3009**
- Tables: **`bo_*`**, created by mirroring Vol.7's schema
  (`CREATE TABLE ... LIKE ss_* INCLUDING ALL`) and **owned by `urbanpadel_app`**
  so the API's own migrations can ALTER them without a superuser.
- Brand art: `brand/blackout/` — lime `#C6FF00` leads, magenta `#FF2E88` accents,
  true black `#050505`, **radius 0 everywhere** except deliberate circles. The
  lockup is served WebP-first (45KB vs 481KB as PNG). Rebuild all of it with
  `python3 build-blackout-brand.py && node render-blackout-brand.mjs && python3 ops/make-brand-webp.py`
  — the WebP step is not optional, a stale WebP beside a fixed PNG ships the old
  art to every browser made in the last decade.
- Display type in the brand art is **shrink-to-fit** (`data-fit="<px>"`, applied
  by the renderer *after* `document.fonts.ready`, since the fallback face
  measures narrower than Archivo at `wdth` 125). The renderer also fails any page
  whose content runs off its own canvas — the stacked lockup first shipped with
  the B and the T of BLACKOUT sliced off by the edge of the bitmap, and every
  assertion passed, because they were all about the font and none about where the
  ink landed.
- Build + deploy:
  ```bash
  python3 build-blackout-app.py && bash ops/deploy-blackout.sh
  ```
- Stand it all up from scratch (idempotent): `ops/create-blackout.sh`
- Carry-over (all-time only, series starts at zero):
  ```bash
  python3 ops/build-carryover.py surge blackout
  scp ops/sync-surge-to-blackout.js urbanpadel:/opt/blackout-api/
  ssh urbanpadel 'cd /opt/blackout-api && DRY=1 node sync-surge-to-blackout.js'
  ssh urbanpadel 'cd /opt/blackout-api && node sync-surge-to-blackout.js'
  ```
  Already run: 60 players and 22 photos carried, Vol.8 series table empty.
- **Full roster merge** — `build-carryover.py` carries ONE volume and only the
  people who played in it, which opened Blackout with 60 names. 199 people have
  played a night since July and 314 have ever signed up, so the rest would have
  needed re-adding by hand before they could be picked for a session:
  ```bash
  python3 ops/build-roster-merge.py blackout
  scp ops/sync-roster-to-blackout.js urbanpadel:/opt/blackout-api/
  ssh urbanpadel 'cd /opt/blackout-api && DRY=1 node sync-roster-to-blackout.js'
  ssh urbanpadel 'cd /opt/blackout-api && node sync-roster-to-blackout.js'
  ```
  A player's base record comes from the latest volume they appear in (so they
  keep their photo and the pre-July volumes that exist only as stored
  prevSeriesPts), then every volume they actually played is **recomputed with
  that volume's own engine** — the volumes do not share one, so each is scored
  by its own rules. `ONLY_PLAYED=1` restricts it to the 199.
  Already run: **314 players, 17 more photos, 245 holding all-time points.**
- The PLAYERS roster ranks on **all-time** until the first Vol.8 match is played,
  because ordering 314 people by a series total that is zero for everyone is no
  order at all.
- **Vol.8's own screens** live in `blackout_screens.py` and are spliced in by the
  builder: the per-event engine (`calcPlayerNights`, `rankByNight`, `calcBadges`),
  ME + points receipt, badges, the four share-to-story cards, the public roster,
  the finals countdown, the prize tracker and night-recap sheets, pull-to-refresh
  and skeleton loading, and the 5-tab nav.
- **`calcPlayerNights` never re-scores anything.** It walks the same path
  `calcPlayerStats` walks, records each award as it is made, then checks its own
  total against `calcPlayerStats` and shows a warning on screen if they disagree.
  If you change scoring, change it in one place and this follows.
- Share cards are drawn once at 1080x1920 on a canvas and that same bitmap is the
  preview, so what people see is the file they post. Canvas cannot set
  `font-variation-settings`, so the display type on those cards is at Archivo's
  default width, not `wdth` 125.
- The schedule is in `blackout-season.json` (`nights`, `finalsDate`): 8 Mon/Wed
  nights plus Friday 30 Oct. The countdown reads `FINALS_DATE` until the
  organiser has created the nine sessions, so it works during signup.
- MVP voting is open to players whenever voting is open (Vol.7 showed it to
  scorers only, so the "player vote" was whoever held the scoring phone).
- **Court-side score sheet** is Vol.8's: one `ScorePanel` (4-wide pad of 64px
  buttons) shared by the group editor and the knockout editor, a `LossReadout`,
  a points preview and a `LockButton` that says why it is disabled. The loss type
  stays DERIVED from the score — the handover draws it as three buttons the
  scorer picks, but buttons that can contradict the score would be a scoring
  change, so the three are a read-out with the derived one lit. The group pad
  also goes to 7 now; a 7-5 could not be recorded at all before.
- Locking a result fires `celebrate()` (two rings + the winning team's name).
- Header carries the Blackout mark, wordmark and VOL.8, and a SYNCED pill that
  anyone can tap to refresh (it used to be scorer-only).
- A finished night's row in SESSIONS opens its **recap**, not the scorer's view
  of a night nobody is scoring; the session screen is one tap further in.
- Player card gains where-the-points-came-from, the last five nights as tiles
  that open each receipt, and head-to-head against you.
- Roster cards carry a photo slot, a streak chip and form bars.
- Worth watching runs four axes, de-duplicated against the podium.
- Still carried from Vol.7 and NOT rebuilt: the KO bracket layout, the teams and
  groups screens, and the photo wall. **Court assignment was never built** — the
  owner said it is not needed.
- Known: the RANK screen gates every tab, including ALL-TIME, behind "first match
  played", so the carried all-time ladder is invisible until the first Vol.8
  result is entered.

### September Surge (Vol.7 — ARCHIVED 1 Oct 2026)
- **Champion: Hamed Amri, 189. Munther Rahbi 188** — one point, and it came from
  the streak bonus cap, not from play on the night. See `archive/september-surge/`.
- Frozen by `ops/archive-surge.sh`: `/state`, `/photos`, `/session-photos` and
  `/history` are served from static JSON snapshots, every write route returns 403,
  and `september-surge-api` is **stopped and disabled** — port 3008 is free.
  surge.urbanpadel.om still renders the full app and the final table.
- Reverse it by restoring `/etc/nginx/sites-available/surge.urbanpadel.om.bak-*`
  and `systemctl enable --now september-surge-api`.
- Details below describe the volume as it ran.
- URL: https://surge.urbanpadel.om — the full tournament app, at the root
- Local copy: `september-surge-index.html`, **generated** by
  `build-september-surge-app.py` from `august-attack-index.html`. Do not hand-edit
  it: fix Vol.6 and re-run the script, which is how a volume inherits the previous
  one's markup (July Heat → August Attack → September Surge). Every rename is
  asserted, so a string that stops matching fails the build rather than shipping
  a half-rebranded app.
- API: `/opt/september-surge-api/api.js` — systemd: `september-surge-api` — port **3008**
- Tables: **`ss_*`** (`ss_tournament_state`, `ss_state_history`, `ss_player_photos`,
  `ss_session_photos`, `ss_recovery_dumps`) — same database, own rows. Vol.6's
  `aa_*` tables and port 3005 are completely separate and untouched.
- Same admin/scorer/photographer PINs as August Attack (`.env` copied, port changed).
- Deploy app: version.txt must carry the build id the page was stamped with,
  not a timestamp — the update check compares the two, so a mismatch makes every
  visitor reload once, forever:
  ```bash
  scp september-surge-index.html urbanpadel:/tmp/ss.html
  scp september-surge-index.html.version urbanpadel:/tmp/ss.version
  ssh urbanpadel 'cp /tmp/ss.html /var/www/surge.urbanpadel.om/public/index.html && \
                  cp /tmp/ss.version /var/www/surge.urbanpadel.om/public/version.txt'
  ```
- Deploy API: `scp api.js urbanpadel:/opt/september-surge-api/ && ssh urbanpadel 'systemctl restart september-surge-api'`
- Brand art: `brand/september-surge/` — the lockup carries SEPTEMBER / SURGE /
  URBAN PLAYGROUND, served WebP-first (233KB vs 1.1MB as PNG). The Vol.6 app
  carried its emblem inline as base64 three times; Vol.7 points at
  `assets/up-logo-cyan.png` instead, which halves the page (0.79MB → 0.38MB).
- The old read-only landing page is kept at
  `/var/www/surge.urbanpadel.om/public/index.html.landing-preview-20260901`.
  The vhost no longer proxies read-only into 3005 — it proxies the full route
  set into 3008, because Surge now writes its own scores.

**All-time carry-over.** Only the all-time total crosses volumes; the Vol.7
series table starts at zero. `ops/build-surge-carryover.py` generates
`ops/sync-aa-to-surge.js` (engine lifted verbatim from the Vol.6 app, so totals
match attack.urbanpadel.om), which writes each player's final Vol.6 points into
`prevSeriesPts["August Attack"]` on the Surge state, carries the roster and
profile photos, and refuses to touch Vol.7 sessions. It is idempotent —
**re-run it once Session 9's knockouts finish**, because it was first run while
Vol.6 was still in play and those totals are provisional:

```bash
scp ops/sync-aa-to-surge.js urbanpadel:/opt/september-surge-api/
ssh urbanpadel 'cd /opt/september-surge-api && DRY=1 node sync-aa-to-surge.js'   # preview
ssh urbanpadel 'cd /opt/september-surge-api && node sync-aa-to-surge.js'
```

**Carried over from Vol.6 and NOT yet reviewed for Vol.7:** the 402 OMR prize
pool, `sessionsTotal = 9`, the `[75, 45, 30]` season prizes, 7 OMR entry, and
`DOUBLE_FROM_SESSION = 8`. These ship as Vol.6's numbers — confirm before the
signup post goes out.

## Common Commands

```bash
# Health check all services
ssh urbanpadel 'systemctl is-active nginx postfix dovecot cloudflared postgresql june-fury-api wc-predictions booking-app'

# Logs
ssh urbanpadel 'journalctl -u june-fury-api -n 50'
ssh urbanpadel 'journalctl -u wc-predictions -n 50'
ssh urbanpadel 'journalctl -u booking-app -n 50'

# Disk / memory
ssh urbanpadel 'df -h / ; free -h ; uptime'

# New subdomain (static)
ssh urbanpadel 'up-subdomain <name>'

# New subdomain (proxied app on a port)
ssh urbanpadel 'up-subdomain <name> --proxy <port>'

# nginx test + reload
ssh urbanpadel 'nginx -t && systemctl reload nginx'
```

## Email

- Mailboxes: mouther@ (owner), info@, bookings@, ali@urbanpadel.om
- IMAP: `mail.urbanpadel.om:993` (SSL)
- SMTP: `mail.urbanpadel.om:465` (SSL) or `:587` (STARTTLS)
- Logs: `ssh urbanpadel 'tail -20 /var/log/mail.log'`

## Backups

| What | Where | Schedule |
|---|---|---|
| August Attack, emailed off-site | `/usr/local/bin/aa-email-backup.sh` (repo: `ops/`) | `/etc/cron.d/aa-email-backup` — hourly, **sends only when a session completes** |
| July Heat, hourly local snapshot | `/usr/local/bin/jh-backup.sh` → `/opt/backups/july-heat` | `/etc/cron.d/jh-backup` — hourly |
| ~~July Heat, emailed daily~~ | script still at `/usr/local/bin/jh-email-backup.sh` | **retired** — cron moved to `/root/jh-email-backup.cron.disabled` |

The August Attack job runs hourly but only mails when the count of sessions
with `completed:true` in `aa_tournament_state` exceeds the marker in
`/var/lib/aa-backup/last-completed` — so it is one email per session night,
not one a day. The marker is advanced **only after** sendmail accepts the
message, so a failed send retries on the next hour rather than silently
skipping that session's backup.

To re-send the most recent session's backup by hand:

```bash
ssh urbanpadel 'echo $(( $(cat /var/lib/aa-backup/last-completed) - 1 )) \
  > /var/lib/aa-backup/last-completed && /usr/local/bin/aa-email-backup.sh'
```

**Known gap:** `jh-backup` still snapshots the *finished* July Heat hourly,
while August Attack has no local snapshots at all — its only off-site copy
is the per-session email. Worth adding an `aa-backup.sh` mirror.

## Design

Anything touching how the apps look or move — palette, type, motion, print
assets — is in **`DESIGN.md`**. Read it before editing UI.

## Rules

- Never copy `.env` files off the server
- Never start APIs with `node api.js &` — always `systemctl restart <service>`
- Always `nginx -t` before `systemctl reload nginx`
- Use `listen 443 ssl http2;` (nginx 1.24 — standalone `http2 on;` does not exist)
- DNS is on Cloudflare under Ali's account — new subdomains need no DNS change (wildcard in place)

## Critical Lessons (Learned the Hard Way)

### Babel CDN — ALWAYS pin to @7
`@babel/standalone` v8.0.0 was released and broke every page using `<script type="text/babel">` — unpkg served v8 automatically (no version pinned). **All three sites went blank simultaneously.**

Fix applied to all sites:
```html
<!-- WRONG — will break when babel releases a new major -->
<script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>

<!-- CORRECT — pin to @7 forever -->
<script src="https://unpkg.com/@babel/standalone@7/babel.min.js"></script>
```
Sites affected: `urbanpadel.om`, `americano.urbanpadel.om`, `predictions.urbanpadel.om`, local `june-fury-index.html`.

Diagnostic: `curl -sI https://unpkg.com/@babel/standalone/babel.min.js | grep location` — if it shows `@8` or higher, that's the culprit.

### Dates on UTC+4 server
Never use `new Date().toISOString().split('T')[0]` for date strings — UTC date is behind Oman local time (UTC+4). Use `getFullYear()/getMonth()/getDate()` (local methods). In `pg`, configure `types.setTypeParser(types.builtins.DATE, val => val)` so DATE columns return plain strings.

### Shell heredoc + backtick SQL
When patching API files via `ssh urbanpadel 'cat > file << EOF ... EOF'`, backtick template literals inside the heredoc cause shell variable expansion and break the patch. Workaround: write the patch as a Python script, `scp` it to the server, run with `python3`.

### PostgreSQL table ownership
`urbanpadel_app` is NOT the owner of `bookings` or other tables. Always run `ALTER TABLE` as superuser:
```bash
ssh urbanpadel "sudo -u postgres psql urbanpadel -c 'ALTER TABLE bookings ADD COLUMN IF NOT EXISTS col TEXT'"
```
New tables need explicit grants:
```bash
ssh urbanpadel "sudo -u postgres psql urbanpadel -c 'GRANT SELECT,INSERT,UPDATE ON TABLE newtable TO urbanpadel_app'"
```
