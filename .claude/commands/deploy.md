# Deploy to urbanpadel.om

Use this skill for any deployment to the Urban Padel VPS — static sites, Node/Express APIs, Next.js apps, nginx changes, DB migrations, or just running a command on the server.

---

## Step 0 — Establish SSH tunnel (every new session)

The session-start hook should have done this automatically. Verify:
```bash
ssh urbanpadel 'echo ok'
```

If it fails (Connection refused), re-run the tunnel:
```bash
/tmp/chisel client --keepalive 25s --auth mouther:ca4ac97f11f618067ca6564606a226d8 https://sshws.urbanpadel.om 2200:127.0.0.1:22 > /tmp/chisel.log 2>&1 &
sleep 5 && grep Connected /tmp/chisel.log
```

SSH alias is pre-configured in `~/.ssh/config` as `urbanpadel` (root@127.0.0.1:2200 with the private key). All `ssh urbanpadel` and `scp`/`rsync` to `urbanpadel:` use it automatically.

---

## VPS quick reference

| Item | Value |
|---|---|
| OS | Ubuntu 24.04, root access |
| IP | 76.13.221.95 (Hostinger KVM1) |
| SSL | Wildcard Cloudflare Origin cert — `/etc/ssl/urbanpadel.om/origin.crt` + `.key` — valid to 2041, covers every `*.urbanpadel.om` subdomain |
| DNS | Cloudflare wildcard `*.urbanpadel.om` — **no DNS change needed for new subdomains** |
| nginx | 1.24 — use `listen 443 ssl http2;` (NOT standalone `http2 on;`) |
| DB | PostgreSQL 16, database `urbanpadel`, app user `urbanpadel_app` |
| App user password | `FeaihAJAIUEL8c9BjCY4BPGj` (used in connection strings) |

### Running services
| Service | Systemd unit | Port | Path |
|---|---|---|---|
| Booking app (Next.js) | `booking-app` | 3003 | `/opt/booking-app` |
| June Fury API | `june-fury-api` | 3001 | `/opt/june-fury-api` |
| WC2026 Predictions API | `wc-predictions` | 3002 | `/opt/wc-predictions-api` |
| nginx | `nginx` | 80/443 | — |
| PostgreSQL | `postgresql` | 5432 | — |

### Subdomain → web root mapping
| Subdomain | Type | Web root / upstream |
|---|---|---|
| urbanpadel.om | static | `/var/www/urbanpadel.om/public` |
| bookings.urbanpadel.om | Next.js proxy | port 3003 |
| americano.urbanpadel.om | static | `/var/www/americano.urbanpadel.om/public` |
| predictions.urbanpadel.om | static + API proxy | `/var/www/predictions.urbanpadel.om/public` |

---

## Deploying a static site

```bash
# One-time: create the subdomain (if new)
ssh urbanpadel 'up-subdomain <name>'
# => creates /var/www/<name>.urbanpadel.om/public with a placeholder index.html

# Upload your files
rsync -avz -e 'ssh -i /root/.ssh/urbanpadel-owner-key -p 2200 -o StrictHostKeyChecking=no' \
  ./dist/   root@127.0.0.1:/var/www/<name>.urbanpadel.om/public/
# or with scp:
scp -r ./dist/* urbanpadel:/var/www/<name>.urbanpadel.om/public/
```

The wildcard nginx vhost serves static files from `/var/www/<subdomain>/public` automatically — no nginx reload needed for existing subdomains.

---

## Deploying a Node.js / Express API

### First-time setup for a new API

1. **Create subdomain** (proxied to your port, e.g. 3005):
   ```bash
   ssh urbanpadel 'up-subdomain myapp --proxy 3005'
   ```

2. **Upload app files**:
   ```bash
   scp api.js urbanpadel:/opt/myapp-api/
   scp package.json urbanpadel:/opt/myapp-api/
   ssh urbanpadel 'cd /opt/myapp-api && npm install --omit=dev'
   ```

3. **Create env file on server** (never copy .env files off server):
   ```bash
   ssh urbanpadel 'cat > /opt/myapp-api/.env << EOF
   PORT=3005
   NODE_ENV=production
   DATABASE_URL=postgresql://urbanpadel_app:FeaihAJAIUEL8c9BjCY4BPGj@127.0.0.1:5432/urbanpadel
   EOF'
   ```

4. **Create systemd service**:
   ```bash
   ssh urbanpadel 'cat > /etc/systemd/system/myapp-api.service << EOF
   [Unit]
   Description=My App API
   After=network.target postgresql.service

   [Service]
   Type=simple
   User=root
   WorkingDirectory=/opt/myapp-api
   ExecStart=/usr/bin/node api.js
   Restart=always
   RestartSec=5
   EnvironmentFile=/opt/myapp-api/.env
   StandardOutput=journal
   StandardError=journal

   [Install]
   WantedBy=multi-user.target
   EOF
   systemctl daemon-reload && systemctl enable myapp-api && systemctl start myapp-api'
   ```

5. **Verify**:
   ```bash
   ssh urbanpadel 'systemctl is-active myapp-api && curl -s http://localhost:3005/health'
   ```

### Updating an existing API

```bash
scp api.js urbanpadel:/opt/myapp-api/
ssh urbanpadel 'systemctl restart myapp-api'
# NEVER: node api.js & — always use systemctl restart
```

---

## Deploying a Next.js app

### First-time setup

1. **Create subdomain**:
   ```bash
   ssh urbanpadel 'up-subdomain myapp --proxy 3004'
   ```

2. **Upload source and build on server**:
   ```bash
   # Sync source
   rsync -avz -e 'ssh -i /root/.ssh/urbanpadel-owner-key -p 2200 -o StrictHostKeyChecking=no' \
     ./   root@127.0.0.1:/opt/myapp/ \
     --exclude node_modules --exclude .next --exclude .git

   # Install and build on server
   ssh urbanpadel 'cd /opt/myapp && npm install && npm run build'
   ```

3. **Create env file**:
   ```bash
   ssh urbanpadel 'cat > /opt/myapp/.env.local << EOF
   DATABASE_URL=postgresql://urbanpadel_app:FeaihAJAIUEL8c9BjCY4BPGj@127.0.0.1:5432/urbanpadel
   NODE_ENV=production
   PORT=3004
   SESSION_SECRET=$(openssl rand -hex 32)
   EOF'
   ```

4. **Create systemd service**:
   ```bash
   ssh urbanpadel 'cat > /etc/systemd/system/myapp.service << EOF
   [Unit]
   Description=My Next.js App
   After=network.target postgresql.service

   [Service]
   Type=simple
   User=www-data
   WorkingDirectory=/opt/myapp
   ExecStart=/usr/bin/node node_modules/.bin/next start -p 3004
   Restart=always
   RestartSec=5
   EnvironmentFile=/opt/myapp/.env.local
   StandardOutput=journal
   StandardError=journal

   [Install]
   WantedBy=multi-user.target
   EOF
   systemctl daemon-reload && systemctl enable myapp && systemctl start myapp'
   ```

### Updating a Next.js app (standard update cycle)

```bash
# Sync changed source files
rsync -avz -e 'ssh -i /root/.ssh/urbanpadel-owner-key -p 2200 -o StrictHostKeyChecking=no' \
  ./src/   root@127.0.0.1:/opt/myapp/src/

# If package.json changed, also sync it and re-install
scp package.json urbanpadel:/opt/myapp/
ssh urbanpadel 'cd /opt/myapp && npm install 2>&1 | tail -3'

# Build and restart
ssh urbanpadel 'cd /opt/myapp && npm run build 2>&1 && systemctl restart myapp && sleep 3 && systemctl is-active myapp'
```

---

## Database operations

### Run a query or migration

```bash
# As app user (SELECT/INSERT/UPDATE on tables it has access to)
ssh urbanpadel "psql 'postgresql://urbanpadel_app:FeaihAJAIUEL8c9BjCY4BPGj@127.0.0.1:5432/urbanpadel' -c 'SELECT count(*) FROM bookings'"

# As superuser (for DDL: CREATE TABLE, ALTER TABLE, GRANT)
ssh urbanpadel "sudo -u postgres psql urbanpadel -c 'CREATE TABLE IF NOT EXISTS ...'"
```

### Adding columns to existing tables

The `urbanpadel_app` user is NOT the owner of the `bookings` table. Always run `ALTER TABLE bookings` as superuser:
```bash
ssh urbanpadel "sudo -u postgres psql urbanpadel << 'SQL'
ALTER TABLE bookings ADD COLUMN IF NOT EXISTS new_col TEXT;
SQL"
```

### Granting access to new tables

After creating a new table (whether via the app or directly), grant access to the app user:
```bash
ssh urbanpadel "sudo -u postgres psql urbanpadel -c 'GRANT SELECT, INSERT, UPDATE ON TABLE new_table TO urbanpadel_app'"
```

---

## nginx operations

```bash
# Test config before applying
ssh urbanpadel 'nginx -t'

# Reload (zero-downtime config reload)
ssh urbanpadel 'nginx -t && systemctl reload nginx'

# View a vhost config
ssh urbanpadel 'cat /etc/nginx/sites-available/<name>.urbanpadel.om'

# Logs
ssh urbanpadel 'tail -50 /var/log/nginx/<name>.urbanpadel.om.error.log'
```

**nginx 1.24 gotcha**: Use `listen 443 ssl http2;` — NOT `listen 443 ssl; http2 on;`. The standalone `http2 on;` directive does not exist in this version.

---

## Health checks & troubleshooting

```bash
# All services at a glance
ssh urbanpadel 'systemctl is-active nginx postgresql june-fury-api wc-predictions booking-app'

# Tail logs for any service
ssh urbanpadel 'journalctl -u booking-app -n 50 --no-pager'
ssh urbanpadel 'journalctl -u june-fury-api -n 50 --no-pager'

# Server resources
ssh urbanpadel 'df -h / ; free -h ; uptime'

# Quick HTTP check
ssh urbanpadel 'curl -s -o /dev/null -w "%{http_code}" http://localhost:<port>/<path>'
```

---

## Known gotchas (learned the hard way)

- **Dates on UTC+4 server**: Never use `new Date().toISOString().split('T')[0]` for date strings — it returns the UTC date which is behind local Oman time (UTC+4). Use `getFullYear()/getMonth()/getDate()` (local methods) instead. In `pg`, configure `types.setTypeParser(types.builtins.DATE, val => val)` so DATE columns come back as plain strings, not Date objects that get shifted by timezone.

- **SESSION_SECRET**: Any app using HMAC-signed cookies needs `SESSION_SECRET` in its `.env.local`. Generate with `openssl rand -hex 32`. Without it, the app crashes on first auth request.

- **`server-only` in Next.js**: Files that import `pg` or other Node-only modules must have `import 'server-only'` at the top. Client components must never import from those files — put shared constants in a separate file.

- **Next.js 16 middleware**: The middleware file is named `proxy.ts` (not `middleware.ts`). Public routes (no auth) must be listed explicitly at the top of the `proxy()` function, including auth API endpoints like `/api/auth/*`.

- **Never start Node processes with `&`**: Always `systemctl restart <service>`. The `&` approach bypasses restart-on-crash, logging, and env file loading.

- **Never `nginx -t` skip**: Always test config before reloading. A bad config with immediate reload will take down all sites.

- **rsync path to alias**: rsync doesn't use `~/.ssh/config` aliases by default — pass the key/port explicitly: `rsync -e 'ssh -i /root/.ssh/urbanpadel-owner-key -p 2200 -o StrictHostKeyChecking=no'`. `scp` and plain `ssh` do use the config alias normally.
