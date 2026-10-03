#!/usr/bin/env bash
# Deploy the club's front door, urbanpadel.om.
#
# The page lives in the repo at landing/index.html. It used to live only on the
# server, which meant the one page every visitor sees first had no history and
# no way to review a change before it went out.
set -euo pipefail

cd "$(dirname "$0")/.."
WEB=/var/www/urbanpadel.om/public

test -f landing/index.html || { echo "no landing/index.html"; exit 1; }

echo "==> assets"
scp -q brand/blackout/blackout-stack.png brand/blackout/blackout-stack.webp \
       brand/blackout/blackout-lockup.png brand/blackout/blackout-lockup.webp \
       urbanpadel:/tmp/
ssh urbanpadel "cp /tmp/blackout-stack.png /tmp/blackout-stack.webp \
                   /tmp/blackout-lockup.png /tmp/blackout-lockup.webp $WEB/assets/"

echo "==> page"
scp -q landing/index.html urbanpadel:/tmp/landing.html
ssh urbanpadel "cp /tmp/landing.html $WEB/index.html && \
                echo '    ' \$(stat -c%s $WEB/index.html) bytes"

echo "==> verify"
# Cache-bust: Cloudflare sits in front and will serve a 404 it cached from
# before an asset existed.
V=$(date +%s)
for u in "/" "/assets/blackout-stack.webp?v=$V" "/assets/blackout-stack.png?v=$V"; do
  printf "    %-34s %s\n" "$u" "$(curl -s -o /dev/null -w '%{http_code} %{size_download}B' "https://urbanpadel.om$u")"
done
# Byte-for-byte, not just 200: Cloudflare happily serves a cached copy of the
# art from before it was fixed, which looks identical to a successful deploy.
for f in blackout-stack.webp blackout-stack.png; do
  L=$(sha256sum "brand/blackout/$f" | cut -c1-16)
  R=$(curl -s "https://urbanpadel.om/assets/$f?v=$V" | sha256sum | cut -c1-16)
  printf "    %-34s %s\n" "$f served" "$([ "$L" = "$R" ] && echo "matches local" || echo "STALE ($R vs $L)")"
done

BODY=$(curl -s "https://urbanpadel.om/?v=$V")
for need in "blackout.urbanpadel.om" "LIGHTS" "blackout-stack.webp" "SEPTEMBER SURGE" "Hamed Amri"; do
  printf "    %-34s %s\n" "contains '$need'" "$(grep -qF "$need" <<<"$BODY" && echo yes || echo "NO")"
done
grep -qF "surge-lockup" <<<"$BODY" && echo "    !! the old Surge lockup is still in the live block" || \
  echo "    old Surge lockup gone from the hero  ok"
