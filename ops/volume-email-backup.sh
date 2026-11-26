#!/bin/bash
# Off-site backup of a volume's state, emailed to the owner — one email per
# completed night. The same job aa-email-backup.sh does for August Attack,
# for any volume built on the same API (one row, id=1, in <prefix>_tournament_state).
#
#   volume-email-backup.sh na "56 National Series"
#   volume-email-backup.sh he "Muscat Heist"
#
# Installed by ops/install-volume-backups.sh as /usr/local/bin/volume-email-backup.sh
# with one hourly cron line per volume. Runs hourly, sends only when the count of
# completed sessions rises, and advances its marker only after sendmail accepted
# the message, so a failed send retries next hour instead of skipping a night.
set -u
P="${1:?prefix (na, he)}"; NAME="${2:?volume name}"
case "$P" in *[!a-z]*) exit 2 ;; esac

TO="almuatharalwahaibi@gmail.com"
FROM="bookings@urbanpadel.om"
MARK=/var/lib/volume-backup/$P-last-completed
TS=$(date +%Y%m%d_%H%M%S)
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
FILE="$TMP/$P-backup-$TS.json"

mkdir -p "$(dirname "$MARK")"
[ -f "$MARK" ] || echo 0 > "$MARK"

sudo -u postgres psql urbanpadel -t -A -c "SELECT data FROM ${P}_tournament_state WHERE id=1" > "$FILE"
SIZE=$(wc -c < "$FILE")
# never email an empty or truncated dump, and never let one advance the marker
[ "$SIZE" -lt 3000 ] && exit 0

read -r DONE PLAYERS SESSIONS <<EOF
$(python3 - "$FILE" <<'PY'
import json, sys
d = json.load(open(sys.argv[1]))
s = d.get("sessions", [])
print(sum(1 for x in s if x.get("completed")), len(d.get("players", [])), len(s))
PY
)
EOF
case "$DONE" in ''|*[!0-9]*) exit 0 ;; esac
LAST=$(cat "$MARK"); case "$LAST" in ''|*[!0-9]*) LAST=0 ;; esac
[ "$DONE" -le "$LAST" ] && exit 0

SLUG=$(echo "$NAME" | tr 'A-Z ' 'a-z-' | tr -cd 'a-z0-9-')
B="vbackup$(date +%s)"; ATT="$SLUG-backup-night${DONE}-$TS.json"
{
  echo "From: $FROM"
  echo "To: $TO"
  echo "Subject: $NAME backup — night $DONE complete ($PLAYERS players)"
  echo "MIME-Version: 1.0"
  echo "Content-Type: multipart/mixed; boundary=\"$B\""
  echo
  echo "--$B"
  echo "Content-Type: text/plain; charset=utf-8"
  echo
  echo "Night $DONE of $NAME is complete — here is the backup."
  echo
  echo "Players: $PLAYERS   Nights on record: $SESSIONS   Completed: $DONE   Size: $SIZE bytes"
  echo
  echo "Keep this email. The attached .json restores players, scores and every"
  echo "night through the app's Restore function. One email per night, not per day."
  echo
  echo "--$B"
  echo "Content-Type: application/json; name=\"$ATT\""
  echo "Content-Transfer-Encoding: base64"
  echo "Content-Disposition: attachment; filename=\"$ATT\""
  echo
  base64 "$FILE"
  echo "--$B--"
} | sendmail -f "$FROM" "$TO" || exit 1

echo "$DONE" > "$MARK"
logger -t volume-email-backup "$P: sent backup for night $DONE ($SIZE bytes)"
