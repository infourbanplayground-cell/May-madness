# -*- coding: utf-8 -*-
"""WebP copies of the Blackout lockups, for the <picture> tags that serve them.

The lockup PNGs are ~490KB each because they are 2200px wide and almost entirely
flat colour over a gradient; as WebP they are ~50KB. Both the app header and the
club's front door ask for the WebP first and keep the PNG as the fallback, so the
two must be regenerated together — a stale WebP beside a fixed PNG ships the old
art to every browser made in the last decade.

Run it after the renderer:

  python3 build-blackout-brand.py && node render-blackout-brand.mjs \
    && python3 ops/make-brand-webp.py
"""
import os
from PIL import Image

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BRAND = os.path.join(HERE, "brand", "blackout")

# Only the lockups are served as WebP. The icon and the mark are small already,
# and the OG image is read by scrapers that are not all WebP-aware.
NAMES = ["blackout-lockup", "blackout-stack"]

for n in NAMES:
    png = os.path.join(BRAND, n + ".png")
    webp = os.path.join(BRAND, n + ".webp")
    im = Image.open(png).convert("RGB")
    im.save(webp, "WEBP", quality=88, method=6)
    a, b = os.path.getsize(png), os.path.getsize(webp)
    print(f"{n}.webp  {im.width}x{im.height}  {b/1024:.0f}KB  (PNG {a/1024:.0f}KB)")
