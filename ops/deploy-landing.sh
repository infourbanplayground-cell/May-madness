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
# The RUNNING volume's stack is the hero. Blackout's stays on the server
# because the archive row still points at blackout.urbanpadel.om and that
# site loads its own art from here.
scp -q brand/national/national-stack.png brand/national/national-stack.webp \
       brand/blackout/blackout-stack.png brand/blackout/blackout-stack.webp \
       brand/blackout/blackout-lockup.png brand/blackout/blackout-lockup.webp \
       brand/landing/hero-court.jpg brand/landing/hero-court.webp \
       urbanpadel:/tmp/
ssh urbanpadel "cp /tmp/national-stack.png /tmp/national-stack.webp \
                   /tmp/blackout-stack.png /tmp/blackout-stack.webp \
                   /tmp/blackout-lockup.png /tmp/blackout-lockup.webp \
                   /tmp/hero-court.jpg /tmp/hero-court.webp $WEB/assets/"

echo "==> page"
scp -q landing/index.html urbanpadel:/tmp/landing.html
ssh urbanpadel "cp /tmp/landing.html $WEB/index.html && \
                echo '    ' \$(stat -c%s $WEB/index.html) bytes"

echo "==> verify"
# Cache-bust: Cloudflare sits in front and will serve a 404 it cached from
# before an asset existed.
V=$(date +%s)
for u in "/" "/assets/national-stack.webp?v=$V" "/assets/national-stack.png?v=$V"; do
  printf "    %-34s %s\n" "$u" "$(curl -s -o /dev/null -w '%{http_code} %{size_download}B' "https://urbanpadel.om$u")"
done
# Byte-for-byte, not just 200: Cloudflare happily serves a cached copy of the
# art from before it was fixed, which looks identical to a successful deploy.
for f in national-stack.webp national-stack.png hero-court.webp hero-court.jpg; do
  case "$f" in hero-*) D=brand/landing;; national-*) D=brand/national;; *) D=brand/blackout;; esac
  L=$(sha256sum "$D/$f" | cut -c1-16)
  R=$(curl -s "https://urbanpadel.om/assets/$f?v=$V" | sha256sum | cut -c1-16)
  printf "    %-34s %s\n" "$f served" "$([ "$L" = "$R" ] && echo "matches local" || echo "STALE ($R vs $L)")"
done

BODY=$(curl -s "https://urbanpadel.om/?v=$V")
# The strings that prove the ROLLOVER landed, not just that a page did:
# the running volume, its art, its tagline, and the volume that just
# finished sitting in the archive with the champion the engine gave.
for need in "national.urbanpadel.om" "ONE COURT." "national-stack.webp" \
            "BLACKOUT SERIES" "Muntaser Hasni" "hero-court.webp"; do
  printf "    %-34s %s\n" "contains '$need'" "$(grep -qF "$need" <<<"$BODY" && echo yes || echo "NO")"
done
grep -qF "blackout-stack" <<<"$BODY" && echo "    !! the old Blackout lockup is still in the live block" || \
  echo "    old Surge lockup gone from the hero  ok"
