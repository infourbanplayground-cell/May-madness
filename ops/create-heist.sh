#!/usr/bin/env bash
# Stand up the Muscat Heist season (Vol.10): API, database, systemd unit.
# RUN ON THE SERVER: scp it over and `bash create-heist.sh`.
#
# Derived from National exactly the way National was derived from the volume
# before it: the API code is identical apart from the table prefix and the
# port, so the save history, the recovery dumps, the merge-on-save and the
# 30-day token all come with it. The scoring rules are not re-implemented —
# they live in the app, inherited from Vol.9.
#
# Port 3013: 3012 is the Heist PHOTOS service (heist-api, /api/*), which stays
# its own process. The vhost for heist.urbanpadel.om is written by
# ops/deploy-heist-photos.sh and routes both.
#
# Idempotent — safe to re-run. It will not overwrite an existing .env.
set -euo pipefail

SRC=/opt/national-api
DST=/opt/heist-season-api
UNIT=heist-season-api
PORT=3013
HOST=heist.urbanpadel.om
OLD=na_
NEW=he_

echo "==> 1/5  app directory"
mkdir -p "$DST"
# node_modules is large and identical; a hard-link copy keeps the disk cost at
# zero without making the two volumes share a mutable directory.
cp -rl "$SRC/node_modules" "$DST/" 2>/dev/null || cp -r "$SRC/node_modules" "$DST/"
cp "$SRC/package.json" "$DST/"
# "July Heat DB ready" has been printed on startup by every volume since
# July — the string was never renamed and each volume inherited it. It is
# log-only, and it is also the first line anyone reads when an API will not
# come up, which is the worst moment to be told the wrong volume name.
sed "s/\b$OLD/$NEW/g; s/56 National Series API/Muscat Heist API/; s/56 National Series DB ready/Muscat Heist DB ready/" \
  "$SRC/api.js" > "$DST/api.js"
sed "s/\b$OLD/$NEW/g" "$SRC/merge.js" > "$DST/merge.js" 2>/dev/null || true
echo "    tables referenced: $(grep -o "${NEW}[a-z_]*" "$DST/api.js" | sort -u | tr '\n' ' ')"
test "$(grep -c "${OLD}[a-z_]*" "$DST/api.js" || true)" = 0 \
  || { echo "    !! Vol.9 table names survived in api.js"; exit 1; }

echo "==> 2/5  environment"
if [ -f "$DST/.env" ]; then
  echo "    .env already present, left alone"
else
  # Same PINs as Vol.9 — the organiser and scorers are the same people — with a
  # fresh token secret so a Vol.9 session token cannot sign into Vol.10.
  sed "s/^PORT=.*/PORT=$PORT/" "$SRC/.env" > "$DST/.env"
  grep -q "^PORT=$PORT" "$DST/.env" || echo "PORT=$PORT" >> "$DST/.env"
  python3 - "$DST/.env" <<'PY'
import re, secrets, sys
p = sys.argv[1]
s = open(p).read()
s = re.sub(r'^TOKEN_SECRET=.*$', 'TOKEN_SECRET=' + secrets.token_hex(32), s, flags=re.M)
open(p, 'w').write(s)
PY
  chmod 600 "$DST/.env"
  echo "    .env written, PORT=$PORT, fresh TOKEN_SECRET"
fi

echo "==> 3/5  database"
# urbanpadel_app is not the owner of these tables, so they are created as
# superuser and the app role is granted explicitly.
# Mirror the previous volume's schema instead of restating it. Hand-written
# CREATE TABLE statements got three of the five tables subtly wrong -- a
# session_photos with photo_data TEXT instead of photos JSONB, a recovery_dumps
# missing its meta column, a state_history missing player_ct/match_ct/role --
# and each one only surfaced as a 500 from a live endpoint. LIKE ... INCLUDING
# ALL cannot drift from what the API actually expects.
sudo -u postgres psql urbanpadel -v ON_ERROR_STOP=1 <<SQL
CREATE TABLE IF NOT EXISTS ${NEW}tournament_state (LIKE ${OLD}tournament_state INCLUDING ALL);
CREATE TABLE IF NOT EXISTS ${NEW}state_history    (LIKE ${OLD}state_history    INCLUDING ALL);
CREATE TABLE IF NOT EXISTS ${NEW}player_photos    (LIKE ${OLD}player_photos    INCLUDING ALL);
CREATE TABLE IF NOT EXISTS ${NEW}session_photos   (LIKE ${OLD}session_photos   INCLUDING ALL);
CREATE TABLE IF NOT EXISTS ${NEW}recovery_dumps   (LIKE ${OLD}recovery_dumps   INCLUDING ALL);

-- LIKE copies defaults but not sequence ownership, so the serial ids need their
-- own sequences in the new volume.
CREATE SEQUENCE IF NOT EXISTS ${NEW}state_history_id_seq  OWNED BY ${NEW}state_history.id;
CREATE SEQUENCE IF NOT EXISTS ${NEW}recovery_dumps_id_seq OWNED BY ${NEW}recovery_dumps.id;
ALTER TABLE ${NEW}state_history  ALTER COLUMN id SET DEFAULT nextval('${NEW}state_history_id_seq');
ALTER TABLE ${NEW}recovery_dumps ALTER COLUMN id SET DEFAULT nextval('${NEW}recovery_dumps_id_seq');

-- The API runs its own idempotent migrations (ALTER TABLE ... ADD COLUMN IF NOT
-- EXISTS) on every start, and ALTER requires ownership, not privileges. Older
-- volumes left these owned by postgres and had to be patched by hand each time
-- a column was added; this volume hands ownership over up front.
ALTER TABLE ${NEW}tournament_state OWNER TO urbanpadel_app;
ALTER TABLE ${NEW}state_history    OWNER TO urbanpadel_app;
ALTER TABLE ${NEW}player_photos    OWNER TO urbanpadel_app;
ALTER TABLE ${NEW}session_photos   OWNER TO urbanpadel_app;
ALTER TABLE ${NEW}recovery_dumps   OWNER TO urbanpadel_app;
ALTER SEQUENCE ${NEW}state_history_id_seq  OWNER TO urbanpadel_app;
ALTER SEQUENCE ${NEW}recovery_dumps_id_seq OWNER TO urbanpadel_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON
  ${NEW}tournament_state, ${NEW}state_history, ${NEW}player_photos,
  ${NEW}session_photos, ${NEW}recovery_dumps TO urbanpadel_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO urbanpadel_app;
SQL
echo "    $(sudo -u postgres psql urbanpadel -At -c "SELECT count(*) FROM information_schema.tables WHERE table_name LIKE '${NEW}%'") tables with the ${NEW} prefix"

echo "==> 4/5  systemd unit"
cat > /etc/systemd/system/$UNIT.service <<EOF
[Unit]
Description=Muscat Heist season API (Urban Social Series Vol.10)
After=network.target postgresql.service

[Service]
Type=simple
WorkingDirectory=$DST
EnvironmentFile=$DST/.env
ExecStart=/usr/bin/node $DST/api.js
Restart=always
RestartSec=3
User=root

[Install]
WantedBy=multi-user.target
EOF
systemctl daemon-reload
systemctl enable --now $UNIT
# Wait for it to settle rather than sampling once: a unit in its RestartSec
# backoff reports "activating", which under set -e aborts the script mid-way.
for i in $(seq 1 15); do
  st=$(systemctl is-active $UNIT || true)
  [ "$st" = active ] && break
  sleep 1
done
echo "    $UNIT: $st"
[ "$st" = active ] || { journalctl -u $UNIT -n 20 --no-pager | tail -8; exit 1; }

echo "==> 5/5  verify"
# systemd reports "active" as soon as node is EXEC'd, which is before it has
# bound the port — so curling straight away reported 000 and a 502 on an API
# that was in fact seconds from being fine. Wait for the listener, not the
# unit.
for i in $(seq 1 20); do
  ss -ltn | grep -q "127.0.0.1:$PORT" && break
  sleep 1
done
printf "    API direct    %s\n" "$(curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:$PORT/state)"
printf "    %-13s %s\n" "$HOST/state" "$(curl -s -o /dev/null -w '%{http_code}' https://$HOST/state)"
printf "    port $PORT      %s listener(s)\n" "$(ss -ltn | grep -c "127.0.0.1:$PORT")"
echo "created."
