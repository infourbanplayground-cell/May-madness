# Deploy Booking App

Deploy the booking app from `/home/user/May-madness/booking-app/` to the VPS at `bookings.urbanpadel.om`.

## Steps

1. **Check SSH tunnel** — verify `ssh urbanpadel 'echo ok'` works. If it fails, reconnect:
   ```
   /tmp/chisel client --keepalive 25s --auth mouther:ca4ac97f11f618067ca6564606a226d8 https://sshws.urbanpadel.om 2200:127.0.0.1:22 > /tmp/chisel.log 2>&1 &
   sleep 5 && grep Connected /tmp/chisel.log
   ```

2. **Sync source files** to the VPS:
   ```
   rsync -avz -e 'ssh -i /root/.ssh/urbanpadel-owner-key -p 2200 -o StrictHostKeyChecking=no' \
     /home/user/May-madness/booking-app/src/ \
     root@127.0.0.1:/opt/booking-app/src/
   ```
   Also sync `package.json` if dependencies changed:
   ```
   scp /home/user/May-madness/booking-app/package.json urbanpadel:/opt/booking-app/package.json
   ```

3. **Install dependencies** (only needed if package.json changed):
   ```
   ssh urbanpadel 'cd /opt/booking-app && npm install 2>&1 | tail -5'
   ```

4. **Build**:
   ```
   ssh urbanpadel 'cd /opt/booking-app && npm run build 2>&1'
   ```
   Build must succeed cleanly — no TypeScript errors allowed.

5. **Restart the service**:
   ```
   ssh urbanpadel 'systemctl restart booking-app && sleep 3 && systemctl is-active booking-app'
   ```

6. **Smoke test** key endpoints:
   ```
   ssh urbanpadel 'curl -s -o /dev/null -w "%{http_code}" http://localhost:3003/book'
   ssh urbanpadel 'curl -s -o /dev/null -w "%{http_code}" http://localhost:3003/api/courts/prices'
   ```
   Both should return `200`.

7. **Commit and push** the changes to git.

## Known gotchas

- **DB migrations**: The `urbanpadel_app` user does NOT own the `bookings` table, so `ALTER TABLE bookings` must be run as postgres superuser:
  ```
  ssh urbanpadel "sudo -u postgres psql urbanpadel -c 'ALTER TABLE bookings ADD COLUMN IF NOT EXISTS new_col TEXT'"
  ```
  New tables created by the app (`members`, `court_prices`) need explicit grants:
  ```
  ssh urbanpadel "sudo -u postgres psql urbanpadel -c 'GRANT ALL ON TABLE new_table TO urbanpadel_app'"
  ```
  Also grant SELECT/INSERT/UPDATE on `bookings` if not already done:
  ```
  ssh urbanpadel "sudo -u postgres psql urbanpadel -c 'GRANT SELECT, INSERT, UPDATE ON TABLE bookings TO urbanpadel_app'"
  ```

- **Timezone / dates**: The VPS is UTC+4. Always use local date methods (`getFullYear()`, `getMonth()`, `getDate()`) instead of `toISOString().split('T')[0]` for date strings. In `store.ts`, `pg` is configured to return `DATE` columns as plain strings via `types.setTypeParser(types.builtins.DATE, val => val)` — do not remove this.

- **Proxy / middleware**: Next.js 16 uses `proxy.ts` (not `middleware.ts`). Public routes (accessible without auth) must be listed in the first `if` block in `proxy.ts`. Always add new public API routes there, especially auth endpoints like `/api/auth/*`.

- **`server-only` imports**: `store.ts` has `import 'server-only'`. Client components must never import from `store.ts`. Put shared constants (COURTS, TIME_SLOTS) in `constants.ts` and import from there.

- **SESSION_SECRET**: Required in `/opt/booking-app/.env.local`. If missing, member login/register will throw `SESSION_SECRET env var is not set`. Generate with `openssl rand -hex 32`.

- **Stale files**: If a file was previously deployed to a wrong path, remove it manually: `ssh urbanpadel 'rm /opt/booking-app/src/lib/SomeFile.tsx'`

## VPS quick reference

| Item | Value |
|---|---|
| App dir | `/opt/booking-app` |
| Env file | `/opt/booking-app/.env.local` |
| Service | `booking-app` (systemd) |
| Port | `3003` |
| DB | `postgresql://urbanpadel_app:...@127.0.0.1:5432/urbanpadel` |
| Nginx vhost | `/etc/nginx/sites-available/bookings.urbanpadel.om` |
