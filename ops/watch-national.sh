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

# THE TUNNEL DIES ON ITS OWN, so each pass brings it back rather than
# assuming it. The chisel client is capped at two hours of background time in
# this session, which is shorter than a match night — holding one open across
# the evening guarantees that the pass which matters most is the one that
# cannot reach the box. Reopening costs about ten seconds and is idempotent:
# if the tunnel is already up this is a no-op. Only the SSH half of the report
# needs it; the page, the state and the version checks go over HTTPS and are
# unaffected either way.
if ! ssh -o ConnectTimeout=5 urbanpadel 'true' 2>/dev/null; then
  echo "tunnel down — reopening"
  nohup /tmp/chisel client --keepalive 25s \
    --auth mouther:ca4ac97f11f618067ca6564606a226d8 \
    https://sshws.urbanpadel.om 2200:127.0.0.1:22 >/tmp/chisel-watch.log 2>&1 &
  for i in $(seq 1 10); do
    ssh -o ConnectTimeout=5 urbanpadel 'true' 2>/dev/null && break
    sleep 4
  done
  ssh -o ConnectTimeout=5 urbanpadel 'true' 2>/dev/null \
    && echo "tunnel back" || echo "!! tunnel would not come back — SSH checks skipped"
fi

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
live_scored = 0
live = []
for s in ss:
    gm = s.get('groupMatches') or []
    br = s.get('bracket') or {}
    ko = (br.get('qf') or []) + (br.get('sf') or []) + ([br['final']] if br.get('final') else [])
    g = sum(1 for m in gm if m and m.get('winner'))
    k = sum(1 for m in ko if m and m.get('winner'))
    scored += g + k
    if not s.get('completed'):
        live_scored += g + k
        # THE DENOMINATOR HAS TO BE DERIVED, NOT COUNTED. The app builds the
        # round robin client-side and only writes a match RECORD when a score
        # is locked, so `len(groupMatches)` is 0 all through check-in and the
        # first pass of this watch read "group 0/0" on a night that was
        # perfectly healthy. Each group of n owes n*(n-1)/2 fixtures.
        from collections import Counter
        sizes = Counter(t.get('group') for t in (s.get('teams') or []))
        owed = sum(n * (n - 1) // 2 for n in sizes.values())
        live.append(f"{s.get('name')} {s.get('date')}  "
                    f"teams {len(s.get('teams') or [])}  "
                    f"group {g}/{owed}  ko {k}/{len(ko) if ko else '-'}")
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
        # Alarming only once there is something that SHOULD be saving. A
        # night still checking people in is quiet by nature, and the first
        # pass of this watch called a perfectly healthy set-up a silent
        # save failure.
        if live and live_scored > 0:
            warn = ("  <-- a night with results in it and nothing moving is"
                    " what a silent save failure looks like")
        elif live:
            warn = "  (nothing played yet — fine if they are still checking in)"
        else:
            warn = ""
        print("NO CHANGE since the last pass" + warn)
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
