# -*- coding: utf-8 -*-
"""Vendor the brand faces into brand/fonts/ so the renderers never need Google.

Why this exists. Every UPRISING and Blackout card is drawn by headless Chromium
and the display type is Archivo at wdth 125. Chromium in this container does
NOT trust the agent proxy's CA, so a <link> to fonts.googleapis.com fails with
ERR_CERT_AUTHORITY_INVALID — and a failed webfont is not an error, it is a
silent fallback. The whole five-card story series rendered in Times once and
every assertion passed, because they were all about the family that was ASKED
for and none about the glyphs that were drawn.

curl does trust the CA, so the files come down here, once, and get committed.
After that the renderers read file:// and the network is out of the loop.

Latin and latin-ext subsets only — these cards are Latin, and the Cyrillic,
Greek and Vietnamese cuts are four fifths of the bytes.

    python3 ops/vendor-fonts.py          # refresh brand/fonts/
"""
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(HERE, "brand", "fonts")
os.makedirs(OUT, exist_ok=True)

# Chrome's UA, because Google serves woff2 only to browsers that admit to
# supporting it; with curl's own UA you get truetype, four times the size.
UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/120.0.0.0 Safari/537.36")
CSS_URL = ("https://fonts.googleapis.com/css2?"
           "family=Archivo:ital,wdth,wght@0,62..125,400..900;1,62..125,400..900"
           "&family=JetBrains+Mono:wght@500;700&display=swap")

# The Latin subsets. Google does not name them in the CSS, so they are
# identified by the first range of the unicode-range it ships them with.
LATIN = ("U+0000-00FF", "U+0100-02BA")

# NOTO KUFI ARABIC, for the Arabic second line the Vol.9 handoff sets under
# every title. There is no Arabic display face installed in this container and
# the Arabic that IS present (DejaVu, FreeSerif) is a text face — so without
# this the brand's Arabic ships in a fallback, which is the same silent failure
# the Latin faces are vendored to prevent, only harder to notice because fewer
# of us read it. Arabic subset only; the Latin cut of Kufi is not used here.
# SUBSETTED TO THE WORDS THE APP ACTUALLY SETS. The full Arabic cut is 120KB
# a weight and the app sets about ten short phrases; Google returns a cut-down
# woff2 for a `text=` request, which brings the pair under 10KB. Vendoring
# 240KB to draw six words is how a brand face ends up being dropped again.
# The strings come from national-season.json so there is one list, and the
# codepoints are written back out so the app build can refuse to ship a word
# this face cannot draw.
import json
import urllib.parse

CFG = json.load(open(os.path.join(HERE, "national-season.json"), encoding="utf-8"))
KUFI_TEXT = "".join(sorted({c for k, v in CFG["arabic"].items()
                            if k != "_note" for c in v}))
KUFI_URL = ("https://fonts.googleapis.com/css2?family=Noto+Kufi+Arabic:wght@500;700"
            "&text=" + urllib.parse.quote(KUFI_TEXT) + "&display=swap")
ARABIC = "U+0600-06FF"


def get(url, binary=False):
    r = subprocess.run(["curl", "-sfL", "-A", UA, url],
                       stdout=subprocess.PIPE, check=True)
    return r.stdout if binary else r.stdout.decode()


css = get(CSS_URL)
blocks = re.findall(r"@font-face\s*\{.*?\}", css, re.S)
kept, n = [], 0
for b in blocks:
    rng = re.search(r"unicode-range:\s*([^;,]+)", b)
    if not rng or not rng.group(1).strip().startswith(LATIN):
        continue
    url = re.search(r"url\((https://[^)]+)\)", b).group(1)
    fam = re.search(r"font-family:\s*'([^']+)'", b).group(1)
    ital = "italic" in b
    sub = "latin" if rng.group(1).strip().startswith(LATIN[0]) else "latin-ext"
    name = f"{fam.replace(' ', '')}{'-italic' if ital else ''}-{sub}"
    # Several weights of JetBrains Mono share one subset, so disambiguate.
    w = re.search(r"font-weight:\s*([\d ]+)", b)
    if w and " " not in w.group(1).strip():
        name += "-" + w.group(1).strip()
    name += ".woff2"
    data = get(url, binary=True)
    open(os.path.join(OUT, name), "wb").write(data)
    n += len(data)
    kept.append(b.replace(url, name).replace("url(", "url(./"))
    print(f"  {name}  {len(data) // 1024}KB")

# The Arabic face, selected by its own subset rather than by position: Google
# ships Kufi's Latin cut in the same stylesheet and it is not wanted.
kufi = re.findall(r"@font-face\s*\{.*?\}", get(KUFI_URL), re.S)
nk = 0
for b in kufi:
    # A `text=` response carries ONE face per weight and NO unicode-range at
    # all — the subset is the range. Selecting on unicode-range (which is what
    # the Latin loop above does) therefore matched nothing and silently
    # vendored no Arabic.
    url = re.search(r"url\((https://[^)]+)\)", b).group(1)
    w = re.search(r"font-weight:\s*([\d ]+)", b)
    name = f"NotoKufiArabic-arabic-{w.group(1).strip() if w else '400'}.woff2"
    data = get(url, binary=True)
    open(os.path.join(OUT, name), "wb").write(data)
    n += len(data); nk += 1
    kept.append(b.replace(url, name).replace("url(", "url(./"))
    print(f"  {name}  {len(data) // 1024}KB")
if nk < 2:
    sys.exit(f"only {nk} Noto Kufi Arabic faces found — the CSS format has changed")

if len(kept) < 4:
    sys.exit(f"only {len(kept)} Latin faces found — the CSS format has changed")

open(os.path.join(OUT, "kufi-coverage.txt"), "w", encoding="utf-8").write(KUFI_TEXT)
print(f"  kufi covers {len(KUFI_TEXT)} characters: {KUFI_TEXT}")

open(os.path.join(OUT, "fonts.css"), "w").write(
    "/* Generated by ops/vendor-fonts.py — do not edit.\n"
    "   Archivo and JetBrains Mono (Latin subsets) and Noto Kufi Arabic (Arabic\n"
    "   subset), SIL Open Font License 1.1.\n"
    "   Local copies so headless Chromium never has to reach the network to\n"
    "   draw a card; a webfont that fails to load is a silent fallback, not an\n"
    "   error. */\n" + "\n".join(kept) + "\n")
print(f"wrote {len(kept)} faces + fonts.css ({n // 1024}KB) to {OUT}")
