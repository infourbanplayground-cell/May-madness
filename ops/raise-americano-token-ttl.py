# Raise the americano API's token lifetime.
#
# 12 hours is shorter than the gap between club nights, so a scorer who logged
# in on Friday to set the night up was signed out before the first serve on
# Saturday — with a role still in local storage saying otherwise. That is the
# mechanism behind the 17 Oct loss. 30 days spans a month of Saturdays.
#
# The PIN is a shared club code on a scoring phone, not a bank credential; the
# cost of a longer token is a phone that stays signed in, which is the point.
import re, sys, shutil, datetime
P = "/opt/americano-api/api.js"
s = open(P).read()
old = "const TOKEN_TTL = 60 * 60 * 12; // 12 h"
new = "const TOKEN_TTL = 60 * 60 * 24 * 30; // 30 d — longer than the gap between nights"
if new in s:
    print("already patched"); sys.exit(0)
if s.count(old) != 1:
    sys.exit("!! TOKEN_TTL line not found exactly once — not touching it")
stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
shutil.copy(P, f"/root/api.js.bak-{stamp}")
open(P, "w").write(s.replace(old, new))
print(f"patched, backup /root/api.js.bak-{stamp}")
