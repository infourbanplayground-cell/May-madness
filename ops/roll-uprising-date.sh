#!/usr/bin/env bash
# ROLL THE UPRISING NIGHT FORWARD AND REPUBLISH. Run weekly, after the night.
#
# `date` in uprising-social.json is the NEXT night. On a weekly cadence that
# is a fact about the calendar, and build-uprising-announce.py now rolls it
# forward in cadence-sized steps from the stored anchor — so the BUILD is
# always right without anybody retyping anything.
#
# THAT IS NOT ENOUGH ON ITS OWN, and this script is why. The link preview is
# `og:` tags baked into the deployed HTML: a crawler reads the source, so no
# amount of client-side cleverness can refresh it and the page has to be
# rebuilt and redeployed for the date to change. It went twelve days stale
# and WhatsApp was still unfurling "Sat 24 Oct" in November.
#
# It is idempotent and quiet: if the rebuild produces the same bytes it
# deploys nothing and says so, so running it more often than necessary costs
# nothing.
#
#   bash ops/roll-uprising-date.sh          # build, and deploy if it changed
#                                           # (run the morning AFTER the night)
#   DRY=1 bash ops/roll-uprising-date.sh    # build and report, never deploy
set -uo pipefail
cd "$(dirname "$0")/.."
DRY=${DRY:-}

echo "=== UPRISING date roll · $(TZ=Asia/Muscat date '+%a %d %b %H:%M') Muscat ==="

# NEVER REPUBLISH INTO A NIGHT. UPRISING is played on FRIDAY evenings — it
# was Saturday until 9 Nov 2026 — and the app being redeployed is the one the
# scorer is holding. This is meant to run on a Saturday; if it is ever fired
# on a Friday afternoon or evening it stops rather than taking the chance.
#
# The night of the week is read from `date` in uprising-social.json, not
# written down here: the whole point of that field being the anchor is that
# the weekday lives in one place. A guard that hard-codes the day is a second
# place, and it is the one nobody remembers when the night moves.
night_dow=$(python3 -c "
import datetime,json
s=json.load(open('uprising-social.json'))
print(datetime.date(*(int(x) for x in s['date'].split('-'))).isoweekday())")
dow=$(TZ=Asia/Muscat date '+%u')
hour=$(TZ=Asia/Muscat date '+%-H')
if [ "$dow" = "$night_dow" ] && [ "$hour" -ge 14 ]; then
  echo "!! it is $(TZ=Asia/Muscat date '+%A') afternoon in Muscat, which is a night — not deploying."
  exit 0
fi

before=$(md5sum americano-index.html landing/index.html 2>/dev/null | md5sum)

python3 build-uprising-announce.py || { echo "!! announce build failed"; exit 1; }
PW_CHROMIUM=/opt/pw-browsers/chromium node ops/render-uprising-announce.mjs >/dev/null \
  || { echo "!! card render failed"; exit 1; }
# Pillow lives on python3.13 in this container, not the default python3.
python3.13 ops/make-og-jpeg.py || { echo "!! og jpeg failed"; exit 1; }

after=$(md5sum americano-index.html landing/index.html 2>/dev/null | md5sum)
if [ "$before" = "$after" ]; then
  echo "nothing changed — the stored date is still the next night. Not deploying."
  exit 0
fi

echo "the pages changed; publishing"
[ -n "$DRY" ] && { echo "DRY=1 — stopping before the deploy"; exit 0; }

# The tunnel dies on its own; bring it back rather than assuming it.
if ! ssh -o ConnectTimeout=5 urbanpadel 'true' 2>/dev/null; then
  nohup /tmp/chisel client --keepalive 25s \
    --auth mouther:ca4ac97f11f618067ca6564606a226d8 \
    https://sshws.urbanpadel.om 2200:127.0.0.1:22 >/tmp/chisel-roll.log 2>&1 &
  for i in $(seq 1 10); do ssh -o ConnectTimeout=5 urbanpadel 'true' 2>/dev/null && break; sleep 4; done
fi
ssh -o ConnectTimeout=8 urbanpadel 'true' 2>/dev/null \
  || { echo "!! no tunnel — cannot deploy"; exit 1; }

# THE IMAGE IS A SEPARATE FILE ON THE VPS, so deploying the app alone does not
# ship it — and `og:image` carries the image's own content hash, so a stale
# picture under a new URL is a 404 rather than a quiet miss.
scp -q brand/uprising/posts/og-card.jpg urbanpadel:/tmp/og-card.jpg || exit 1
ssh urbanpadel 'cp /tmp/og-card.jpg /var/www/americano-app/public/og-card.jpg' || exit 1

python3 build-americano-app.py >/dev/null || { echo "!! app build failed"; exit 1; }
bash ops/deploy-americano.sh >/dev/null 2>&1 || { echo "!! app deploy failed"; exit 1; }
bash ops/deploy-landing.sh   >/dev/null 2>&1 || { echo "!! landing deploy failed"; exit 1; }

# VERIFY WITH THE CRAWLER'S OWN EYES, not the browser's, and check the image
# the crawler is actually GIVEN rather than the bare path.
echo "--- verify ---"
tags=$(curl -s -A "WhatsApp/2.23" https://americano.urbanpadel.om/)
desc=$(printf '%s' "$tags" | grep -o '<meta property="og:description"[^>]*>')
img=$(printf '%s' "$tags" | grep -o 'og-card.jpg?v=[0-9a-f]*')
echo "  $desc"
code=$(curl -s -o /tmp/roll-og.jpg -w '%{http_code}' "https://americano.urbanpadel.om/$img")
if [ "$code" = 200 ] && cmp -s brand/uprising/posts/og-card.jpg /tmp/roll-og.jpg; then
  echo "  image $img  200, byte-identical"
else
  echo "  !! image $img returned $code or differs from the local card"
  exit 1
fi
want=$(python3 -c "
import datetime,json
s=json.load(open('uprising-social.json'))
y,m,d=(int(x) for x in s['date'].split('-'))
dt=datetime.date(y,m,d); t=datetime.date.today()
if s.get('cadence')=='weekly':
    while dt<t: dt+=datetime.timedelta(days=7)
print(f\"{dt.strftime('%a')} {dt.day} {dt.strftime('%b')}\")")
printf '%s' "$desc" | grep -q "$want" \
  && echo "  the live description names $want  ok" \
  || { echo "  !! the live description does not name $want"; exit 1; }
echo "done"
