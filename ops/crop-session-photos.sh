#!/usr/bin/env bash
# Strip the Blackout frame and footer the session photos already wear.
#
# /session-photos hands back images with a border, a footer bar and a URL
# burned in — and one of them still reads attack.urbanpadel.om from Vol.6.
# Dropped into a film as-is that is a frame inside a frame with two different
# URLs on screen, so the branding is cropped off and the film puts its own on.
set -euo pipefail
SP="/tmp/claude-0/-home-user-May-madness/0e44f0ad-a683-5f0d-9de6-9459ae328963/scratchpad"
IN="$SP/bophotos"; OUT="$SP/bocrop"
mkdir -p "$OUT"
# 3% off each side, 3.5% off the top, and enough off the foot to lose the bar.
for f in "$IN"/*.jpg; do
  b=$(basename "$f")
  /usr/bin/ffmpeg -y -loglevel error -i "$f" \
    -vf "crop=iw*0.94:ih*0.84:iw*0.03:ih*0.035,scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920" \
    -q:v 4 "$OUT/$b"
done
echo "cropped $(ls "$OUT" | wc -l) photos to 1080x1920 in $OUT"
