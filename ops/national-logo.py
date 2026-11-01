# -*- coding: utf-8 -*-
"""Recolour the Urban Playground mark into the Vol.9 palette, as variations.

The shipped mark is white with an ORANGE ball (#F56530) — a Blackout-era
accent that belongs to no colour in this volume. On the red ground it reads as
a fifth hue nobody chose, and it is the first thing on every screen.

WHY THIS IS A SCRIPT AND NOT A HAND EDIT. The source is a 324x505 PNG with
antialiased edges, so a flood fill leaves an orange fringe around every
recoloured shape and a white fringe around every dark one — which is exactly
what "it looks fine at 100%" hides. Each pixel is classified and re-inked with
its own luminance and alpha preserved, so the edges stay clean at any size.

  python3.13 ops/national-logo.py            # write every variation
  python3.13 ops/national-logo.py --sheet    # ...and a contact sheet to look at

Pillow is on python3.13 in this container, not the default python3 (3.11).
"""
import argparse
import os

from PIL import Image

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(HERE, "brand", "national", "up-logo-tight.png")
OUT = os.path.join(HERE, "brand", "national", "logo")

# national-season.json's palette, repeated here rather than imported so the
# script runs standalone on python3.13 (the json is read when it is wired into
# a build; this is a one-off art step).
RED = (184, 20, 31)
FLAG = (215, 32, 46)
IVORY = (247, 241, 230)
INK = (26, 10, 12)
GREEN = (8, 122, 63)
WHITE = (255, 255, 255)

# name: (ink for the mark, ink for the ball, what it is for)
VARIANTS = {
    "a-ivory-red":    (IVORY, FLAG,  "ivory mark, flag-red ball — the default, for the red ground"),
    "b-white-green":  (WHITE, GREEN, "white mark, green ball — National Day, and the greenest cut"),
    "c-ivory-green":  (IVORY, GREEN, "ivory mark, green ball — warmer than (b) against the tile"),
    "d-ink-red":      (INK,   FLAG,  "ink mark, flag-red ball — for ivory cards and light print"),
    "e-ivory-mono":   (IVORY, IVORY, "one ink, no accent — the quietest, for busy grounds"),
    "f-white-red":    (WHITE, FLAG,  "pure white mark, flag-red ball — the loudest on red"),
}


def classify(px):
    """Is this pixel part of the MARK or part of the BALL?

    The source is white plus one orange. Grey-family pixels (r, g and b within
    a short distance of each other) are the mark; anything with real chroma is
    the accent. Done on the pixel rather than on a flood fill, so the
    antialiased boundary between the two is re-inked correctly instead of
    keeping a one-pixel orange halo.
    """
    r, g, b, _ = px
    return "ball" if (max(r, g, b) - min(r, g, b)) > 28 else "mark"


def recolour(im, mark, ball):
    out = Image.new("RGBA", im.size)
    src, dst = im.load(), out.load()
    w, h = im.size
    for y in range(h):
        for x in range(w):
            r, g, b, a = src[x, y]
            if a == 0:
                dst[x, y] = (0, 0, 0, 0)
                continue
            ink = ball if classify((r, g, b, a)) == "ball" else mark
            # KEEP THE PIXEL'S OWN BRIGHTNESS. The mark carries soft shading;
            # flattening every pixel to one colour loses it and the logo comes
            # back looking like a sticker. Luminance is taken against the
            # source's own peak (white / the orange) so a mid-tone stays a
            # mid-tone of the NEW ink.
            peak = max(r, g, b) or 1
            k = peak / 255
            dst[x, y] = (round(ink[0] * k), round(ink[1] * k), round(ink[2] * k), a)
    return out


def contact_sheet(paths):
    """Composite every variation on every ground it will actually meet.

    A transparent mark looks perfect on the one background it was made for and
    ruins the others with nothing on screen to tell you which you have — the
    lesson the UPRISING and Blackout cut-outs both record. So: the red ground,
    the deep red of a row, an ivory card, white, and black.
    """
    grounds = [("red", RED), ("deep", (158, 21, 32)), ("ivory", IVORY),
               ("white", WHITE), ("black", (5, 5, 5))]
    cell_w, cell_h, pad = 150, 220, 18
    sheet = Image.new("RGB", (pad + len(grounds) * (cell_w + pad),
                              pad + len(paths) * (cell_h + pad)), (40, 40, 40))
    for row, (name, path) in enumerate(paths):
        logo = Image.open(path).convert("RGBA")
        logo.thumbnail((cell_w - 36, cell_h - 36))
        for col, (_, bg) in enumerate(grounds):
            cell = Image.new("RGBA", (cell_w, cell_h), bg + (255,))
            cell.alpha_composite(logo, ((cell_w - logo.width) // 2,
                                        (cell_h - logo.height) // 2))
            sheet.paste(cell.convert("RGB"),
                        (pad + col * (cell_w + pad), pad + row * (cell_h + pad)))
    return sheet


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sheet", action="store_true", help="also write a contact sheet")
    args = ap.parse_args()

    os.makedirs(OUT, exist_ok=True)
    im = Image.open(SRC).convert("RGBA")
    made = []
    for name, (mark, ball, what) in VARIANTS.items():
        path = os.path.join(OUT, f"up-logo-{name}.png")
        recolour(im, mark, ball).save(path)
        made.append((name, path))
        print(f"  up-logo-{name}.png   {what}")

    # THE ORANGE MUST BE GONE. The whole point of the exercise, and a
    # classifier that quietly matched nothing would leave it and look like a
    # successful run.
    for name, path in made:
        px = Image.open(path).convert("RGBA")
        bad = sum(1 for p in px.getdata()
                  if p[3] > 128 and p[0] > 200 and 60 < p[1] < 160 and p[2] < 90)
        assert bad < 20, f"{name}: {bad} Blackout-orange pixels survived"
    print(f"\n{len(made)} variations in {OUT}")

    if args.sheet:
        sh = contact_sheet(made)
        p = os.path.join(OUT, "CONTACT-SHEET.png")
        sh.save(p)
        print(f"contact sheet: {p}  (rows = variations, columns = grounds)")


if __name__ == "__main__":
    main()
