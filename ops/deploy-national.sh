#!/usr/bin/env bash
# Deploy the 56 National Series (Vol.9) app and its brand art.
#
# version.txt must carry the build id the page was STAMPED with, not a
# timestamp: the app's update check compares the two, and a mismatch makes every
# visitor reload once, forever. build-blackout-app.py writes the id to
# national-index.html.version — this ships that file verbatim and verifies the
# two agree after upload.
#
#   python3 build-national-app.py
#   bash ops/deploy-national.sh
set -euo pipefail

cd "$(dirname "$0")/.."
HOST=national.urbanpadel.om
WEB=/var/www/$HOST/public
PAGE=national-index.html

test -f "$PAGE" || { echo "no $PAGE — run: python3 build-national-app.py"; exit 1; }
BID=$(cat "$PAGE.version")
grep -q "\"$BID\"" "$PAGE" || { echo "!! the page is not stamped with $BID — rebuild"; exit 1; }

echo "==> uploading  build $BID"
scp -q "$PAGE" urbanpadel:/tmp/na.html
scp -q "$PAGE.version" urbanpadel:/tmp/na.version
# Vol.9's own art. up-logo-tight is the club mark and is not volume-specific,
# so it still comes from Vol.8's directory.
scp -q brand/national/national-lockup.png brand/national/national-lockup.webp \
       brand/national/national-og.png brand/national/national-icon.png \
       brand/national/national-mark.png brand/blackout/up-logo-tight.png \
       urbanpadel:/tmp/

ssh urbanpadel "set -e
  mkdir -p $WEB/assets
  cp /tmp/na.html    $WEB/index.html
  cp /tmp/na.version $WEB/version.txt
  for f in national-lockup.png national-lockup.webp national-og.png \
           national-icon.png national-mark.png up-logo-tight.png; do
    cp /tmp/\$f $WEB/assets/\$f
  done
  echo '    page    ' \$(stat -c%s $WEB/index.html) bytes
  echo '    version ' \$(cat $WEB/version.txt)
  echo '    assets  ' \$(ls $WEB/assets | wc -l) files"

echo "==> verify"
printf "    %-28s %s\n" "page"    "$(curl -s -o /dev/null -w '%{http_code}' https://$HOST/)"
printf "    %-28s %s\n" "state"   "$(curl -s -o /dev/null -w '%{http_code}' https://$HOST/state)"
# Cache-bust the asset check. Cloudflare sits in front and will happily serve a
# 404 it cached from before the vhost had a root -- which is exactly what this
# check reported on the first deploy while the origin was serving the file fine.
printf "    %-28s %s\n" "lockup (cache-busted)" "$(curl -s -o /dev/null -w '%{http_code}' "https://$HOST/assets/national-lockup.webp?v=$BID")"
SERVED=$(curl -s "https://$HOST/version.txt" | tr -d '[:space:]')
printf "    %-28s %s\n" "version.txt served" "$SERVED"
[ "$SERVED" = "$BID" ] && echo "    build id matches the page  ok" \
  || { echo "    !! version.txt says $SERVED, the page says $BID — every visitor would reload forever"; exit 1; }
