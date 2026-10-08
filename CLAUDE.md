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
