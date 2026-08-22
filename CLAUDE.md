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
| Main site | https://urbanpadel.om (Coming Soon placeholder) |

## Owner's Apps

### Americano (standalone classic-format app)
- URL: https://americano.urbanpadel.om — **its own app**, independent of the monthly tournament clones below. Do not point this domain at any of them again.
- Format: classic Americano — individual players, partners rotate every round (circle-method round-robin scheduling), points accumulate per-player, not per fixed team. Modeled on padelution.com's Americano format page.
- Frontend: `/var/www/americano-app/public/` — local copy: `americano-index.html`
- API: `/opt/americano-api/api.js` — systemd: `americano-api` — port 3007 — local copy: `americano-api.js`
- DB tables: `americano_state`, `americano_photos` (own tables, not shared with the monthly apps)
- Deploy frontend: `scp americano-index.html urbanpadel:/var/www/americano-app/public/index.html` (then bump `/var/www/americano-app/public/version.txt` for cache-busting)
- Deploy API: `scp americano-api.js urbanpadel:/opt/americano-api/api.js && ssh urbanpadel 'systemctl restart americano-api'`
- Player roster was seeded once from June Fury's existing player list (names/photos only, no stats) — the two rosters are independent from that point on.
- nginx vhost: `/etc/nginx/sites-available/americano.urbanpadel.om` — serves the static root directly and proxies `/state /login /save /photos` to port 3007 (same pattern as the monthly apps below, just its own root/port).

### Monthly tournament apps (groups + knockout bracket format)
Each month gets its own clone of the same tournament-tracker codebase (Teams/Groups/Bracket tabs, not the Americano rotation format). `americano.urbanpadel.om` used to redirect to whichever one was "current" — that redirect has been removed; Americano is now separate and permanent.

| App | Domain | Port | systemd | DB table prefix |
|---|---|---|---|---|
| June Fury | june.urbanpadel.om | 3001 | `june-fury-api` | (default: `tournament_state`, `player_photos`) |
| July Heat | heat.urbanpadel.om | 3004 | `july-heat-api` | `jh_` |
| August Attack | attack.urbanpadel.om | 3005 | `august-attack-api` | `aa_` |

- June Fury frontend root: `/var/www/americano.urbanpadel.om/public/` (legacy path, kept as-is — do not repurpose this directory) — local copy: `june-fury-index.html`
- Deploy June Fury frontend: `scp june-fury-index.html urbanpadel:/var/www/americano.urbanpadel.om/public/index.html`
- Deploy June Fury API: `scp api.js urbanpadel:/opt/june-fury-api/ && ssh urbanpadel 'systemctl restart june-fury-api'`
- **Known leftover bug (not yet fixed, left alone on request):** `surge.urbanpadel.om` proxies to port 3005 (August Attack's backend) with no dedicated `surge` service or DB prefix of its own — looks like a stray/incomplete config, not intentional. Investigate before touching August Attack's port or before standing up a real "surge" app.

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

### Booking App (Court reservations)
- URL: https://bookings.urbanpadel.om
- Source: `/home/user/May-madness/booking-app/`
- App dir on VPS: `/opt/booking-app` — systemd: `booking-app` — port 3003
- See `.claude/commands/deploy-booking-app.md` for full deploy steps

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
