# -*- coding: utf-8 -*-
"""The brand faces as one self-contained @font-face block, woff2 inlined.

Every print and social page here links `brand/fonts/` rather than Google Fonts,
because Chromium in this container does not trust the agent proxy's CA and a
webfont that fails to load is a silent fallback, not an error — the UPRISING
story series once rendered entirely in Times with every assertion green.

The certificate and medal builders used to read a bundle from
`/tmp/certs/fonts/bundle.css`, which a fresh container does not have, so they
could not be rebuilt at all. This reads the vendored copies out of the repo and
embeds them as data URLs, so the generated HTML renders identically with no
network and no font substitution at the print shop.
"""
import base64
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
FONT_DIR = os.path.join(os.path.dirname(HERE), "brand", "fonts")


def bundle(font_dir=FONT_DIR):
    """`brand/fonts/fonts.css` with every `url(./x.woff2)` turned into a data URL."""
    css_path = os.path.join(font_dir, "fonts.css")
    css = open(css_path).read()

    def inline(m):
        name = m.group(1)
        path = os.path.join(font_dir, name)
        if not os.path.exists(path):
            raise SystemExit(f"font-bundle: {css_path} references {name}, which is missing")
        with open(path, "rb") as f:
            b = base64.b64encode(f.read()).decode()
        return f"url(data:font/woff2;base64,{b}) format('woff2')"

    out, n = re.subn(r"url\(\./([^)]+\.woff2)\)\s*format\('woff2'\)", inline, css)
    if n == 0:
        raise SystemExit(f"font-bundle: no woff2 references found in {css_path}")
    # font-display:swap lets a page paint in the fallback face first. Every
    # consumer here is a headless screenshot that waits on document.fonts.ready,
    # but block is the honest setting for print artwork: nothing should ever be
    # captured in a substitute face.
    return out.replace("font-display: swap;", "font-display: block;")


if __name__ == "__main__":
    css = bundle()
    print(f"{len(css)/1024:.0f}KB, {css.count('@font-face')} faces, "
          f"{css.count('data:font/woff2')} inlined")
