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

### June Fury (Americano tournament)
- URL: https://americano.urbanpadel.om
- Frontend: `/var/www/americano.urbanpadel.om/public/`
- API: `/opt/june-fury-api/api.js` — systemd: `june-fury-api` — port 3001
- Deploy frontend: `scp -r frontend/* urbanpadel:/var/www/americano.urbanpadel.om/public/`
- Deploy API: `scp api.js urbanpadel:/opt/june-fury-api/ && ssh urbanpadel 'systemctl restart june-fury-api'`

### WC2026 Predictions
- URL: https://predictions.urbanpadel.om
- Frontend: `/var/www/predictions.urbanpadel.om/public/`
- API: `/opt/wc-predictions-api/predictions-api.js` — systemd: `wc-predictions` — port 3002
- Deploy same pattern as June Fury

## Common Commands

```bash
# Health check all services
ssh urbanpadel 'systemctl is-active nginx postfix dovecot cloudflared postgresql june-fury-api wc-predictions urbanpadel-sig chisel-ssh'

# Logs
ssh urbanpadel 'journalctl -u june-fury-api -n 50'
ssh urbanpadel 'journalctl -u wc-predictions -n 50'

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
