#!/bin/bash
# Off-site backup of the August Attack state, emailed to the owner.
#
# Runs HOURLY but sends only when a session has just been completed, so the
# owner gets exactly one backup per session night instead of a daily email
# they stop opening. "Completed" is the `completed:true` flag the app writes
# on each session; we track how many have it and send when that count rises.
#
# Replaces jh-email-backup.sh, which mailed July Heat daily. July Heat is
# finished, so that state no longer changes and the mail was pure noise.
set -u

TO="almuatharalwahaibi@gmail.com"
FROM="bookings@urbanpadel.om"
MARK=/var/lib/aa-backup/last-completed
TS=$(date +%Y%m%d_%H%M%S)
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
FILE="$TMP/august-attack-backup-$TS.json"

mkdir -p "$(dirname "$MARK")"
[ -f "$MARK" ] || echo 0 > "$MARK"

sudo -u postgres psql urbanpadel -t -A \
  -c "SELECT data FROM aa_tournament_state WHERE id=1" > "$FILE"

SIZE=$(wc -c < "$FILE")
# Guard: never email an empty or truncated dump, and never let a bad dump
# advance the marker (that would silently skip a real session's backup).
if [ "$SIZE" -lt 3000 ]; then exit 0; fi

read -r DONE PLAYERS SESSIONS <<EOF
$(python3 - "$FILE" <<'PY'
import json, sys
d = json.load(open(sys.argv[1]))
s = d.get("sessions", [])
print(sum(1 for x in s if x.get("completed")), len(d.get("players", [])), len(s))
PY
)
EOF

# A parse failure leaves DONE empty; treat that as "do nothing" rather than
# risking a wrong send or a corrupted marker.
case "$DONE" in ''|*[!0-9]*) exit 0 ;; esac

LAST=$(cat "$MARK")
case "$LAST" in ''|*[!0-9]*) LAST=0 ;; esac
[ "$DONE" -le "$LAST" ] && exit 0

BOUNDARY="aabackup$(date +%s)"
NAME="august-attack-backup-s${DONE}-$TS.json"
{
  echo "From: $FROM"
  echo "To: $TO"
  echo "Subject: August Attack backup — Session $DONE complete ($PLAYERS players)"
  echo "MIME-Version: 1.0"
  echo "Content-Type: multipart/mixed; boundary=\"$BOUNDARY\""
  echo
  echo "--$BOUNDARY"
  echo "Content-Type: text/plain"
  echo
  echo "Session $DONE of the August Attack series is complete — here is the backup."
  echo
  echo "Players: $PLAYERS   Sessions on record: $SESSIONS   Completed: $DONE   Size: $SIZE bytes"
  echo
  echo "Keep this email. The attached .json fully restores players, scores and"
  echo "session history via the app's Restore function."
  echo
  echo "You get one of these per session night, not one a day."
  echo
  echo "--$BOUNDARY"
  echo "Content-Type: application/json; name=\"$NAME\""
  echo "Content-Transfer-Encoding: base64"
  echo "Content-Disposition: attachment; filename=\"$NAME\""
  echo
  base64 "$FILE"
  echo "--$BOUNDARY--"
} | sendmail -f "$FROM" "$TO"

# Only advance the marker once the mail has actually been handed to sendmail.
echo "$DONE" > "$MARK"
logger -t aa-email-backup "sent backup for session $DONE ($SIZE bytes)"
