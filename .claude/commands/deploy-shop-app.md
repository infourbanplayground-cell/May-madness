# Deploy Shop App

Deploy the shop from `/home/user/May-madness/shop-app/` to `shop.urbanpadel.om`.

## Steps

1. **Check the SSH tunnel** — `ssh urbanpadel 'echo ok'`. If it fails:
   ```
   /tmp/chisel client --keepalive 25s --auth mouther:ca4ac97f11f618067ca6564606a226d8 https://sshws.urbanpadel.om 2200:127.0.0.1:22 > /tmp/chisel.log 2>&1 &
   sleep 5 && grep Connected /tmp/chisel.log
   ```

2. **Sync the source.** There is no `rsync` in this container — use a tarball:
   ```
   cd /home/user/May-madness/shop-app
   tar czf /tmp/shop-app.tgz --exclude=node_modules --exclude=.next .
   scp /tmp/shop-app.tgz urbanpadel:/tmp/
   ssh urbanpadel 'cd /opt/shop-app && tar xzf /tmp/shop-app.tgz && rm /tmp/shop-app.tgz'
   ```
   The tarball excludes `.env.local`, which lives only on the server.

3. **Install** (only when `package.json` changed):
   ```
   ssh urbanpadel 'cd /opt/shop-app && npm install 2>&1 | tail -5'
   ```

4. **Build** — must be clean, no TypeScript errors:
   ```
   ssh urbanpadel 'cd /opt/shop-app && npm run build 2>&1 | tail -20'
   ```

5. **Restart**:
   ```
   ssh urbanpadel 'systemctl restart shop-app && sleep 4 && systemctl is-active shop-app'
   ```

6. **Smoke test**:
   ```
   ssh urbanpadel 'for p in / /cart /admin /api/products; do curl -s -o /dev/null -w "%{http_code} $p\n" http://127.0.0.1:3006$p; done'
   ```
   All four must be `200`.

## Layout

| Item | Value |
|---|---|
| URL | https://shop.urbanpadel.om |
| App dir | `/opt/shop-app` |
| systemd | `shop-app` |
| Port | 3006 |
| Env | `/opt/shop-app/.env.local` (chmod 600, server only) |
| Tables | `shop_products`, `shop_orders`, `shop_order_items` |
| Admin | `/admin`, password in `ADMIN_PASSWORD` |

## Gotchas

- **Money is stored as integer baisa, never a float.** OMR has three decimal
  places (1 rial = 1000 baisa), so `price_baisa` is an INTEGER and the only
  conversion happens at the edges: `Math.round(omr * 1000)` on input,
  `(baisa / 1000).toFixed(3)` on display.
- **The cart never carries prices.** It stores product ids and quantities in
  localStorage; `createOrder` re-reads every price from the database inside
  the transaction. A client that posts its own price is ignored — verified
  by posting `unitBaisa: 1` for a 12.500 OMR item and getting a 25.000 order.
- **Stock is decremented with a conditional UPDATE** (`WHERE stock >= qty`)
  inside the same transaction as the order, so two people buying the last
  item cannot both win.
- **Cancelling an order restocks it**, and is guarded against running twice —
  a double-click will not inflate stock.
- Values containing spaces in `.env.local` are quoted so the file can be
  both `source`d and read by systemd's `EnvironmentFile`.
- `PAY_MOBILE` and `SHOP_WHATSAPP` are intentionally empty until the owner
  confirms them; the order page only renders rows that are set.
