#!/usr/bin/env bash
# TONIGHT'S WATCH. One pass over the things that go wrong on a match night,
# printed as a short report. Run it on a schedule during a session.
#
# What it actually looks for, and why each one is here:
#   · THE SAVE IS THE THING. The 17 Oct 2026 Americano night was lost to 32
#     POSTs that all returned 401 while the UI stayed editable — the scores
#     never left the phone and nobody knew until the next reload. So this
#     tracks the state's own version counter and the count of scored matches,
#     and says whether either MOVED since the last pass. A night in play that
#     is not moving is the loudest signal there is.
#   · The build id, because a visitor reloading onto a mismatched version.txt
#     reloads forever.
#   · The page served byte-for-byte against what we shipped, because
#     Cloudflare will serve a cached old copy with a 200 that looks exactly
#     like a healthy site.
#   · Services, disk and the API's recent errors.
set -uo pipefail
cd "$(dirname "$0")/.."
HOST=national.urbanpadel.om
MARK=${MARK:-/tmp/na-watch.last}
BID=$(cat national-index.html.version 2>/dev/null || echo '?')

echo "=== $(TZ=Asia/Muscat date '+%a %d %b %H:%M') Muscat ==="

code=$(curl -s -o /tmp/na-page.html -w '%{http_code}' "https://$HOST/")
scode=$(curl -s -o /tmp/na-state.json -w '%{http_code}' "https://$HOST/state")
echo "page $code   state $scode"

if [ "$code" = 200 ]; then
  if cmp -s national-index.html /tmp/na-page.html; then echo "page  byte-identical to build $BID"
  else echo "!! PAGE DIFFERS from the local build — a cache or a stray deploy"; fi
fi
served=$(curl -s "https://$HOST/version.txt" | tr -d '[:space:]')
[ "$served" = "$BID" ] && echo "version $served  ok" \
  || echo "!! version.txt says '$served', the page is '$BID' — visitors reload forever"

python3 - "$MARK" <<'PY'
import json, os, sys
mark = sys.argv[1]
try:
    d = json.load(open('/tmp/na-state.json'))
except Exception as e:
    print('!! /state did not parse:', e); raise SystemExit
st = d.get('state', d)
ver = d.get('version')
ss = st.get('sessions') or []
scored = 0
live = []
for s in ss:
    gm = s.get('groupMatches') or []
    br = s.get('bracket') or {}
    ko = (br.get('qf') or []) + (br.get('sf') or []) + ([br['final']] if br.get('final') else [])
    g = sum(1 for m in gm if m and m.get('winner'))
    k = sum(1 for m in ko if m and m.get('winner'))
    scored += g + k
    if not s.get('completed'):
        live.append(f"{s.get('name')} {s.get('date')}  group {g}/{len(gm)}  ko {k}/{len(ko)}")
print(f"sessions {len(ss)}   scored matches {scored}   state version {ver}")
for l in live: print('  IN PLAY  ' + l)
prev = {}
if os.path.exists(mark):
    try: prev = json.load(open(mark))
    except Exception: pass
if prev:
    dv = (ver != prev.get('ver'))
    ds = scored - prev.get('scored', 0)
    if ds or dv:
        print(f"moved: +{ds} scored match(es), version {prev.get('ver')} -> {ver}")
    else:
        print("NO CHANGE since the last pass"
              + ("  <-- a night in play that is not saving looks exactly like this" if live else ""))
json.dump({'ver': ver, 'scored': scored}, open(mark, 'w'))
PY

ssh -o ConnectTimeout=8 urbanpadel '
  echo "services $(systemctl is-active national-api nginx postgresql | tr "\n" " ")"
  echo "disk     $(df -h / | awk "NR==2{print \$5\" used, \"\$4\" free\"}")"
  n=$(journalctl -u national-api --since "-70 min" -p err --no-pager -q | wc -l)
  echo "api errors in the last 70 min: $n"
  [ "$n" -gt 0 ] && journalctl -u national-api --since "-70 min" -p err --no-pager -q | tail -5
  c=$(journalctl -u national-api --since "-70 min" --no-pager -q | grep -c " 401 " || true)
  [ "$c" -gt 0 ] && echo "!! $c x 401 in the last 70 min — scores may not be saving"
' 2>&1 | grep -v '^Warning: Permanently added'

exit 0
