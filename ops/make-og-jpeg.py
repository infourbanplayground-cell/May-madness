# -*- coding: utf-8 -*-
"""Shrink the rendered link-preview card to a JPEG an unfurler will actually use.

The renderer draws og-card at 2x for sharpness, which lands around 2MB of PNG.
WhatsApp fetches a preview image inline while you are typing and drops anything
much over ~300KB — and when it drops the image it shows the link as a bare grey
row, which is worse than no preview at all. iMessage and Slack are more generous
but not unlimited.

So: down to exactly 1200x630, JPEG, quality stepped down until it fits the
budget. The card is flat colour on near-black with one soft glow, which is the
easiest thing in the world for JPEG — it lands near q82 at well under the cap.

    python3 ops/make-og-jpeg.py
"""
import hashlib
import os
import re

from PIL import Image

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(HERE, "brand", "uprising", "posts", "og-card.png")
OUT = os.path.join(HERE, "brand", "uprising", "posts", "og-card.jpg")
BUDGET = 280 * 1024

im = Image.open(SRC).convert("RGB").resize((1200, 630), Image.LANCZOS)
for q in (88, 84, 80, 74, 68, 60):
    im.save(OUT, "JPEG", quality=q, optimize=True, progressive=True)
    n = os.path.getsize(OUT)
    if n <= BUDGET:
        break
else:
    raise SystemExit(f"og-card.jpg is {n // 1024}KB even at q60 — the card has "
                     "gained a photograph, or the budget needs revisiting")

# Stamp the og:image URL with the image's own content hash.
#
# Cloudflare caches og-card.jpg for four hours, so re-uploading it is NOT
# enough: the crawler asks for the same URL and gets the old picture, with
# cf-cache-status: HIT and a 200 that looks exactly like success. It bit this
# repo once already — a new card went up advertising a new date and WhatsApp
# kept unfurling the old one, same byte COUNT, different bytes. A hash in the
# query makes a changed image a changed URL, which no cache can get wrong,
# and leaves an unchanged image on its existing cached copy.
digest = hashlib.sha256(open(OUT, "rb").read()).hexdigest()[:10]
APP = os.path.join(HERE, "americano-index.html")
app = open(APP).read()
pat = re.compile(r'(<meta property="og:image" content="https://[^"?]+\.jpg)(\?v=[0-9a-f]+)?(")')
app2, hits = pat.subn(lambda m: m.group(1) + "?v=" + digest + m.group(3), app)
if not hits:
    raise SystemExit("!! no og:image tag in americano-index.html to stamp")
if app2 != app:
    open(APP, "w").write(app2)
    print(f"  og:image stamped ?v={digest} — rebuild and deploy the app")

print(f"og-card.jpg  1200x630  q{q}  {n // 1024}KB  "
      f"(from {os.path.getsize(SRC) // 1024}KB PNG)")
