#!/usr/bin/env bash
# Deploy the Americano app (classic Americano + UPRISING) to
# americano.urbanpadel.om.
#
# This app had NO copy in the repo until Oct 2026 — it lived only on the server,
# the same way the landing page did. americano-index.html is now the source and
# the server is the copy.
#
# version.txt is just the page's own hash: this app's update check fetches
# version.txt and compares it with what the browser stored last time, so the
# file only has to CHANGE when the page does. Deploying identical bytes reloads
# nobody.
#
#   node --test uprising-engine.test.js
#   python3 build-americano-app.py
#   bash ops/deploy-americano.sh
set -euo pipefail

cd "$(dirname "$0")/.."
HOST=americano.urbanpadel.om
WEB=/var/www/americano-app/public
PAGE=americano-index.html

test -f "$PAGE" || { echo "no $PAGE"; exit 1; }
test -f "$PAGE.version" || { echo "no $PAGE.version — run: python3 build-americano-app.py"; exit 1; }
BID=$(cat "$PAGE.version")

# The engine is inlined into the page; if the two have drifted, the tests are
# proving something the browser is not running.
python3 - <<'PY'
import sys
app = open("americano-index.html").read()
eng = open("uprising-engine.js").read().split('if (typeof module !== "undefined"')[0].rstrip()
if eng not in app:
    sys.exit("!! uprising-engine.js is not what is inlined in the page — run build-americano-app.py")
print("    engine inlined and current  ok")
PY

echo "==> uploading  build $BID"
scp -q "$PAGE" urbanpadel:/tmp/am.html
scp -q "$PAGE.version" urbanpadel:/tmp/am.version
ssh urbanpadel "set -e
  cp $WEB/index.html $WEB/index.html.bak-\$(date +%Y%m%d-%H%M%S)
  cp /tmp/am.html    $WEB/index.html
  cp /tmp/am.version $WEB/version.txt
  echo '    page    ' \$(stat -c%s $WEB/index.html) bytes
  echo '    version ' \$(cat $WEB/version.txt)"

echo "==> verify"
printf "    %-24s %s\n" "page"  "$(curl -s -o /dev/null -w '%{http_code}' https://$HOST/)"
printf "    %-24s %s\n" "state" "$(curl -s -o /dev/null -w '%{http_code}' https://$HOST/state)"
SERVED=$(curl -s "https://$HOST/version.txt?_=$(date +%s)" | tr -d '[:space:]')
printf "    %-24s %s\n" "version.txt served" "$SERVED"
[ "$SERVED" = "$BID" ] && echo "    version matches the build  ok" \
  || { echo "    !! version.txt says $SERVED, the build is $BID"; exit 1; }
