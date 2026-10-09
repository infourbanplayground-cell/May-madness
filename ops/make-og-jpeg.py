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
import os

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

print(f"og-card.jpg  1200x630  q{q}  {n // 1024}KB  "
      f"(from {os.path.getsize(SRC) // 1024}KB PNG)")
