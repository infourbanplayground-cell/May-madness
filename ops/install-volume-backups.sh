#!/bin/bash
# Install the per-night emailed backup for National (na) and Muscat Heist (he).
# Idempotent. Minute 17 so it does not land on the hour with everything else.
#   bash ops/install-volume-backups.sh
set -euo pipefail
cd "$(dirname "$0")/.."
bash -n ops/volume-email-backup.sh
scp -q ops/volume-email-backup.sh urbanpadel:/usr/local/bin/volume-email-backup.sh
ssh urbanpadel 'set -e
chmod 755 /usr/local/bin/volume-email-backup.sh
cat > /etc/cron.d/volume-email-backup <<CRON
# one email per completed night (ops/volume-email-backup.sh in the repo)
17 * * * * root /usr/local/bin/volume-email-backup.sh na "56 National Series"
17 * * * * root /usr/local/bin/volume-email-backup.sh he "Muscat Heist"
CRON
chmod 644 /etc/cron.d/volume-email-backup
echo installed; cat /etc/cron.d/volume-email-backup'
