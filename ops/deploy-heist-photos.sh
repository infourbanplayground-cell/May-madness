#!/usr/bin/env bash
# Muscat Heist — stand up heist.urbanpadel.om with the player-photos page and
# the first piece of its API (heist-api, port 3012). Idempotent.
#
#   bash ops/deploy-heist-photos.sh
#
# Touches nothing any other volume runs: its own service, its own vhost, its
# own folder. The .env is built ON THE SERVER from National's (the club's
# PINs and token secret) and never leaves it. A Heist photo replaced or
# removed is moved to /opt/heist-api/history/, never deleted.
set -euo pipefail
cd "$(dirname "$0")/.."
WEB=/var/www/heist.urbanpadel.om/public
H=heist.urbanpadel.om

ssh urbanpadel "mkdir -p /opt/heist-api/history $WEB/photos $WEB/fonts/brand $WEB/fonts/heist $WEB/players"
scp -q heist-api/api.js urbanpadel:/opt/heist-api/api.js
scp -q heist-photos/index.html heist-photos/style.txt urbanpadel:$WEB/photos/
scp -q brand/fonts/*.woff2 brand/fonts/fonts.css urbanpadel:$WEB/fonts/brand/
scp -q brand/heist/fonts/*.woff2 brand/heist/fonts/fonts.css urbanpadel:$WEB/fonts/heist/

ssh urbanpadel bash -s <<'REMOTE'
set -euo pipefail
WEB=/var/www/heist.urbanpadel.om/public
cd /opt/heist-api
# express comes from National's install: same major, already audited on this box
[ -d node_modules/express ] || cp -r /opt/national-api/node_modules .
if [ ! -f .env ]; then
  grep -E '^(ADMIN_PIN|PHOTOGRAPHER_PIN|TOKEN_SECRET)=' /opt/national-api/.env > .env
  echo "PORT=3012" >> .env
  chmod 600 .env
fi
cat > /etc/systemd/system/heist-api.service <<'UNIT'
[Unit]
Description=Muscat Heist API (player photos)
After=network.target national-api.service
[Service]
WorkingDirectory=/opt/heist-api
EnvironmentFile=/opt/heist-api/.env
ExecStart=/usr/bin/node api.js
Restart=always
RestartSec=3
[Install]
WantedBy=multi-user.target
UNIT
systemctl daemon-reload
systemctl enable heist-api >/dev/null 2>&1
systemctl restart heist-api

# the front page until the app ships
[ -f $WEB/index.html ] || cat > $WEB/index.html <<'HTML'
<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Muscat Heist</title><meta name="robots" content="noindex">
<style>body{margin:0;min-height:100vh;display:grid;place-items:center;background:#0F1B2B;color:#FFF4E8;font:16px system-ui;text-align:center}
b{display:block;font-size:40px;letter-spacing:.06em}a{color:#FFC9A3}</style>
<div><b>MUSCAT HEIST</b><p>Vol.10 · Mon &amp; Wed from Wed 2 Dec · 17:30 · Al Hail North</p><p><a href="/photos/">Player photos</a></p></div>
HTML

VH=/etc/nginx/sites-available/heist.urbanpadel.om
cat > $VH <<'NGX'
server {
    listen 80; listen [::]:80;
    server_name heist.urbanpadel.om;
    return 301 https://$host$request_uri;
}
server {
    listen 443 ssl http2; listen [::]:443 ssl http2;
    server_name heist.urbanpadel.om;
    ssl_certificate     /etc/ssl/urbanpadel.om/origin.crt;
    ssl_certificate_key /etc/ssl/urbanpadel.om/origin.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    real_ip_header CF-Connecting-IP;
    root /var/www/heist.urbanpadel.om/public;
    client_max_body_size 12m;

    location /api/ {
        proxy_pass http://127.0.0.1:3012;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_read_timeout 60s;
        add_header Cache-Control "no-store" always;
    }
    # every Heist photo URL carries ?v=<mtime>, so a replaced photo is a new URL
    location /players/ { add_header Cache-Control "public, max-age=31536000, immutable"; try_files $uri =404; }
    location /photos/ { add_header Cache-Control "no-cache"; try_files $uri $uri/ =404; }
    location / { try_files $uri $uri/ =404; }
}
NGX
ln -sf $VH /etc/nginx/sites-enabled/heist.urbanpadel.om
nginx -t && systemctl reload nginx
sleep 1
systemctl is-active heist-api
curl -s localhost:3012/api/roster | head -c 120; echo
REMOTE

# through Cloudflare, as a visitor sees it
for u in /photos/ /api/roster /fonts/brand/fonts.css; do
  printf '%-24s %s\n' "$u" "$(curl -s -o /dev/null --max-time 20 -w '%{http_code} %{content_type}' https://$H$u || echo unreachable)"
done
