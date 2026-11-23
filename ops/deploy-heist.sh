#!/usr/bin/env bash
# Deploy the Muscat Heist app (heist-index.html) and the assets it reads.
#
#   python3 build-heist-app.py && bash ops/deploy-heist.sh          -> /preview/
#   python3 build-heist-app.py && ROOT=1 bash ops/deploy-heist.sh   -> the front page (from Tue 1 Dec)
#
# version.txt must carry the build id the page was STAMPED with (every volume's
# rule): the update check fetches /version.txt from the SITE ROOT, so it is
# written there in both modes, or a preview build would reload itself forever.
# Never on a night being played — check the clock against heist-season.json.
set -euo pipefail
cd "$(dirname "$0")/.."
HOST=heist.urbanpadel.om
WEB=/var/www/$HOST/public
DIR=$WEB/preview; [ "${ROOT:-}" = 1 ] && DIR=$WEB
PAGE=heist-index.html
test -f "$PAGE" || { echo "no $PAGE — run: python3 build-heist-app.py"; exit 1; }
BID=$(cat "$PAGE.version")
grep -q "\"$BID\"" "$PAGE" || { echo "!! the page is not stamped with $BID — rebuild"; exit 1; }

# a night being played: 17:00-23:00 Muscat on any date in the season's nights
NOW=$(TZ=Asia/Muscat date +%Y-%m-%dT%H)
python3 - "$NOW" <<'PY' || { echo "!! a Heist night is being played right now — not deploying"; exit 1; }
import json, sys
d, h = sys.argv[1].split("T")
nights = json.load(open("heist-season.json"))["nights"]
sys.exit(1 if d in nights and 17 <= int(h) < 23 else 0)
PY

echo "==> build $BID -> $DIR"
ssh urbanpadel "mkdir -p $DIR/assets/art $DIR/assets/fonts/brand $DIR/assets/fonts/heist"
scp -q "$PAGE" urbanpadel:$DIR/index.html.new
scp -q brand/heist/art/*.jpg urbanpadel:$DIR/assets/art/
scp -q brand/heist/up-logo-tight.png brand/national/history.json urbanpadel:$DIR/assets/
# the inherited all-time plate fetches /assets/history.json from the SITE ROOT
ssh urbanpadel "mkdir -p $WEB/assets"; scp -q brand/national/history.json urbanpadel:$WEB/assets/
scp -q brand/fonts/*.woff2 brand/fonts/fonts.css urbanpadel:$DIR/assets/fonts/brand/
scp -q brand/heist/fonts/*.woff2 brand/heist/fonts/fonts.css urbanpadel:$DIR/assets/fonts/heist/
ssh urbanpadel "set -e
  mv $DIR/index.html.new $DIR/index.html
  echo $BID > $WEB/version.txt
  chmod 644 $DIR/index.html $WEB/version.txt"

# as a visitor sees it, through Cloudflare
PATHP=/; [ "${ROOT:-}" = 1 ] || PATHP=/preview/
for u in "$PATHP" /version.txt /state "${PATHP}assets/up-logo-tight.png" "${PATHP}assets/fonts/heist/fonts.css"; do
  printf '%-40s %s\n' "$u" "$(curl -s -o /dev/null --max-time 20 -w '%{http_code} %{content_type}' "https://$HOST$u" || echo unreachable)"
done
LIVE=$(curl -s --max-time 20 "https://$HOST/version.txt" | tr -d '\n')
[ "$LIVE" = "$BID" ] && echo "version.txt matches the page: $BID" || { echo "!! version.txt says '$LIVE', the page is $BID"; exit 1; }
