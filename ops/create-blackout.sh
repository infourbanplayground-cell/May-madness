#!/usr/bin/env bash
# Stand up Blackout Series (Vol.8): API, database, vhost, systemd unit.
#
# Each volume gets its own process, port, table prefix and vhost, and shares
# nothing with the one before it but the Postgres instance. That is what let
# Vol.7 be archived without touching Vol.6, and it is why this script never
# edits anything belonging to an earlier volume.
#
# Derived from September Surge: the API code is identical apart from the table
# prefix and the port, because the handoff is explicit that the scoring rules
# must not be re-implemented.
#
# Idempotent — safe to re-run. It will not overwrite an existing .env.
set -euo pipefail

SRC=/opt/september-surge-api
DST=/opt/blackout-api
UNIT=blackout-api
PORT=3009
HOST=blackout.urbanpadel.om
WEB=/var/www/$HOST/public
OLD=ss_
NEW=bo_

echo "==> 1/7  app directory"
mkdir -p "$DST"
# node_modules is large and identical; a hard-link copy keeps the disk cost at
# zero without making the two volumes share a mutable directory.
cp -rl "$SRC/node_modules" "$DST/" 2>/dev/null || cp -r "$SRC/node_modules" "$DST/"
cp "$SRC/package.json" "$DST/"
sed "s/\b$OLD/$NEW/g; s/September Surge API/Blackout Series API/; s/August Attack API/Blackout Series API/" \
  "$SRC/api.js" > "$DST/api.js"
sed "s/\b$OLD/$NEW/g" "$SRC/merge.js" > "$DST/merge.js" 2>/dev/null || true
echo "    tables referenced: $(grep -o "${NEW}[a-z_]*" "$DST/api.js" | sort -u | tr '\n' ' ')"
test "$(grep -c "${OLD}[a-z_]*" "$DST/api.js" || true)" = 0 \
  || { echo "    !! Vol.7 table names survived in api.js"; exit 1; }

echo "==> 2/7  environment"
if [ -f "$DST/.env" ]; then
  echo "    .env already present, left alone"
else
  # Same PINs as Vol.7 — the organiser and scorers are the same people — with a
  # fresh token secret so a Vol.7 session token cannot sign into Vol.8.
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

echo "==> 3/7  database"
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

echo "==> 4/7  systemd unit"
cat > /etc/systemd/system/$UNIT.service <<EOF
[Unit]
Description=Blackout Series API (Urban Social Series Vol.8)
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

echo "==> 5/7  web root"
mkdir -p "$WEB/assets"

echo "==> 6/7  vhost"
if [ -f /etc/nginx/sites-available/$HOST ]; then
  echo "    vhost already present, left alone"
else
  # up-subdomain provisions the TLS cert and the Cloudflare-fronted server
  # block, then we replace its body. Its --proxy form sends the WHOLE site to
  # the app port, which is right for an app that serves its own HTML -- but
  # these volumes are a static page plus a small JSON API, so index.html,
  # version.txt and the brand art would all be handed to an API that has no
  # route for them and the site would 404 while /state alone worked.
  up-subdomain blackout --proxy $PORT
  cat > /etc/nginx/sites-available/$HOST <<EOF
server {
    listen 80; listen [::]:80;
    server_name $HOST;
    return 301 https://\$host\$request_uri;
}
server {
    listen 443 ssl http2; listen [::]:443 ssl http2;
    server_name $HOST;
    ssl_certificate     /etc/ssl/urbanpadel.om/origin.crt;
    ssl_certificate_key /etc/ssl/urbanpadel.om/origin.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    real_ip_header CF-Connecting-IP;

    root $WEB;
    index index.html;

    location ~ ^/(state|login|save|photos|session-photos|jf-leaderboard|photo-upload|recovery-dump|history|restore)\$ {
        proxy_pass http://127.0.0.1:$PORT;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        client_max_body_size 25m;
    }

    # Brand art is immutable per build and can be cached hard.
    location ~* \.(png|webp|jpg|jpeg|svg|woff2)\$ {
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
    # The page and version.txt must NOT be cached, or the self-healing update
    # check never sees a new build.
    location = /version.txt { add_header Cache-Control "no-store"; }
    location = /index.html  { add_header Cache-Control "no-store"; }

    location / {
        try_files \$uri \$uri/ /index.html;
    }

    access_log /var/log/nginx/$HOST.access.log;
    error_log  /var/log/nginx/$HOST.error.log;
}
EOF
  ln -sf /etc/nginx/sites-available/$HOST /etc/nginx/sites-enabled/$HOST
  echo "    vhost written: static root + API routes"
fi
nginx -t && systemctl reload nginx

echo "==> 7/7  verify"
printf "    API direct    %s\n" "$(curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:$PORT/state)"
printf "    %-13s %s\n" "$HOST/state" "$(curl -s -o /dev/null -w '%{http_code}' https://$HOST/state)"
printf "    port $PORT      %s listener(s)\n" "$(ss -ltn | grep -c "127.0.0.1:$PORT")"
echo "created."
