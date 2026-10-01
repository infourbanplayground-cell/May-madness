# September Surge — Vol.7, archived

Ran 7–30 September 2026, eight nights. Frozen 1 October 2026.

**Champion: Hamed Amri, 189 points. Munther Rahbi finished on 188** — one point
over eight nights, and the point itself came from the streak bonus rather than
from play on the final night: Hamed had been at the +5 cap since session 7 and
could not earn more, while Rahbi still had headroom and took the last +1. See
`final-standings.json`.

## What archiving did

`ops/archive-surge.sh`, run once on the server:

- dumped the five `ss_*` tables to `/opt/backups/september-surge/`
- snapshotted `/state`, `/photos`, `/session-photos` and `/history` to static
  JSON in the site's public directory
- rewrote the vhost so those four reads are served from the snapshots and every
  write route returns 403 with a JSON body the app can read
- stopped and **disabled** `september-surge-api`, releasing port 3008

surge.urbanpadel.om still renders the full app and the final table, with no
backend process behind it.

## Reversing it

The original vhost is kept on the server as
`/etc/nginx/sites-available/surge.urbanpadel.om.bak-<stamp>`, and the unit is
disabled rather than removed. Restore the vhost, `systemctl enable --now
september-surge-api`, `nginx -t && systemctl reload nginx`.

## Files here

| File | What it is |
|---|---|
| `final-state.json` | the exact `/state` response at freeze time — the whole season |
| `final-standings.json` | computed from it with the app's own engine, via `make-winner-data.mjs` |
