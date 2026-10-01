#!/usr/bin/env bash
# Freeze September Surge (Vol.7) at the end of its season.
#
# The volume stays readable at surge.urbanpadel.om forever -- the final table is
# the record of the season -- but it stops accepting writes, and its API process
# and port are released for the next volume.
#
# How the freeze works: the three read endpoints are snapshotted to static JSON
# next to the page and nginx serves those directly, so the app still renders the
# final standings with no backend at all. Every write route returns 403.
#
# Reversible: the old vhost is kept beside the new one, and the unit is only
# disabled, never removed.
set -euo pipefail

VOL=september-surge
SITE=/var/www/surge.urbanpadel.om/public
UNIT=september-surge-api
PORT=3008
VHOST=/etc/nginx/sites-available/surge.urbanpadel.om
BK=/opt/backups/$VOL
STAMP=$(date +%Y%m%d-%H%M%S)

mkdir -p "$BK"

echo "==> 1/6  database snapshot"
sudo -u postgres pg_dump urbanpadel \
  -t ss_tournament_state -t ss_state_history -t ss_player_photos \
  -t ss_session_photos -t ss_recovery_dumps \
  > "$BK/$VOL-$STAMP.sql"
gzip -f "$BK/$VOL-$STAMP.sql"
ls -la "$BK/$VOL-$STAMP.sql.gz"

echo "==> 2/6  freezing the read endpoints to static JSON"
# Taken from the live API while it is still up; this is what the page will read
# forever after.
for ep in state photos session-photos; do
  curl -fsS "http://127.0.0.1:$PORT/$ep" -o "$SITE/$ep.json"
  echo "    $ep.json  $(stat -c%s "$SITE/$ep.json") bytes"
done
# A frozen season has no pending writes, so an empty history is honest.
curl -fsS "http://127.0.0.1:$PORT/history" -o "$SITE/history.json" 2>/dev/null \
  || echo '{"ok":true,"history":[]}' > "$SITE/history.json"

echo "==> 3/6  new vhost"
cp "$VHOST" "$VHOST.bak-$STAMP"
python3 - "$VHOST" <<'PY'
import re, sys
p = sys.argv[1]
s = open(p).read()
# Replace the single proxy block that currently fronts every app route.
old = re.search(
    r'\n\s*location ~ \^/\(state\|login\|save\|photos\|session-photos\|jf-leaderboard\|'
    r'photo-upload\|recovery-dump\|history\|restore\)\$ \{.*?\n\s*\}\n',
    s, re.S)
assert old, "the proxy block is not where it was -- stopping rather than guessing"
new = '''
    # ── ARCHIVED. Vol.7 finished 30 September 2026. ──
    # The reads are served from static snapshots taken from the API on the day
    # it was frozen, so the final table renders with no backend running at all.
    location = /state          { default_type application/json; alias SITE/state.json; }
    location = /photos         { default_type application/json; alias SITE/photos.json; }
    location = /session-photos { default_type application/json; alias SITE/session-photos.json; }
    location = /history        { default_type application/json; alias SITE/history.json; }

    # Writes are refused in a shape the app can read, rather than hanging.
    location ~ ^/(login|save|photo-upload|recovery-dump|restore)$ {
        default_type application/json;
        return 403 '{"ok":false,"error":"September Surge is archived. Vol.7 ended 30 September 2026."}';
    }
'''.replace('SITE', '/var/www/surge.urbanpadel.om/public')
s = s[:old.start()] + new + s[old.end():]
open(p, 'w').write(s)
print("    vhost rewritten")
PY

echo "==> 4/6  nginx test"
nginx -t

echo "==> 5/6  reload + stop the API"
systemctl reload nginx
systemctl stop "$UNIT"
systemctl disable "$UNIT"

echo "==> 6/6  verify"
for ep in state photos session-photos; do
  printf "    GET /%-15s %s\n" "$ep" \
    "$(curl -s -o /dev/null -w '%{http_code} %{size_download}B' https://surge.urbanpadel.om/$ep)"
done
printf "    POST /%-14s %s\n" "save" \
  "$(curl -s -o /dev/null -w '%{http_code}' -X POST https://surge.urbanpadel.om/save)"
printf "    GET  /%-14s %s\n" "(page)" \
  "$(curl -s -o /dev/null -w '%{http_code}' https://surge.urbanpadel.om/)"
echo "    port $PORT now: $(ss -ltn | grep -c "127.0.0.1:$PORT") listener(s)"
echo "archived."
