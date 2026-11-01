# -*- coding: utf-8 -*-
"""Turn the owner's supplied landmark images into medallion silhouettes.

They arrive as dark ink on a white background at five different sizes and
five different amounts of padding. A medallion needs the opposite of all of
that: one ink, transparent everywhere else, trimmed to its own drawing and
padded by a known fraction, so nine discs on a screen look like one set
rather than five pictures that happen to be round.

THE ALPHA COMES FROM THE DARKNESS, not from a threshold. A hard cut turns
every antialiased edge into a staircase, which at 48px on a phone is the
difference between a building and a smudge. Luminance maps to alpha on a ramp:
white is clear, anything at or below INK_AT is solid, and the slope between
keeps the edge.

THE RAMP ALSO DROPS WATERMARKS. A faint grey mark sits well above the ramp's
floor and lands at an alpha low enough to disappear, which is why the cut is
set from the PAPER end rather than the ink end.

  python3.13 ops/national-landmarks.py        # convert, write a proof sheet
  python3.13 ops/national-landmarks.py --raw  # ...and keep the trimmed masters

Pillow is on python3.13 in this container, not the default python3 (3.11).
"""
import argparse
import os

from PIL import Image

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(HERE, "brand", "national", "silhouettes")

# Where the owner's files land in this session.
SRC_DIR = ("/tmp/claude-0/-home-user-May-madness/"
           "0e44f0ad-a683-5f0d-9de6-9459ae328963/images")

# file -> the asset name the season file and the app use.
# The MAPPING IS A GUESS AT THE SUBJECT, not at which night it goes on; the
# per-session assignment stays the owner's, in national-season.json.
SUPPLIED = {
    "2.png": "mon-fort",      # crenellated fort gate with a clock face
    "3.png": "mon-gatehouse",  # three arches under a deep cornice
    "4.png": "mon-burner",     # the incense burner
    "5.png": "mon-sail",       # the sail-form museum
    "6.png": "mon-palace",     # three arches with a flagstaff
}

PAPER = 238      # at or above this, fully transparent
INK_AT = 96      # at or below this, fully opaque
# The handoff's own silhouettes are 60 units of drawing inside a 68-unit box,
# so the drawing fills about 88% of its square. Matching that is what makes a
# supplied image sit on the disc like the drawn ones do.
FILL = 0.88


def silhouette(path, ink=(255, 255, 255)):
    im = Image.open(path).convert("RGBA")
    w, h = im.size
    src = im.load()
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    dst = out.load()
    for y in range(h):
        for x in range(w):
            r, g, b, a = src[x, y]
            if a == 0:
                continue
            lum = (r * 299 + g * 587 + b * 114) // 1000
            if lum >= PAPER:
                continue
            k = 255 if lum <= INK_AT else int(255 * (PAPER - lum) / (PAPER - INK_AT))
            # The source's own alpha still counts, for a file that arrives
            # already cut out.
            dst[x, y] = (ink[0], ink[1], ink[2], min(255, k * a // 255))
    return out


def trim_and_pad(im):
    """Trim to the ink, then centre it in a square at a known fill fraction.

    Each file arrives with its own idea of margin — one is tight to the
    drawing, another floats in white space — and a medallion draws its art at
    a fixed percentage of the disc. Without this, the same background-size
    gives five different apparent sizes.
    """
    box = im.getbbox()
    if not box:
        raise AssertionError("nothing survived the ramp — check PAPER/INK_AT")
    art = im.crop(box)
    side = int(max(art.size) / FILL)
    sq = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    sq.alpha_composite(art, ((side - art.width) // 2, (side - art.height) // 2))
    return sq


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=SRC_DIR)
    args = ap.parse_args()

    os.makedirs(OUT, exist_ok=True)
    made = []
    for f, name in SUPPLIED.items():
        p = os.path.join(args.src, f)
        if not os.path.exists(p):
            raise SystemExit(f"missing {p} — the owner's files are not in this session")
        sq = trim_and_pad(silhouette(p))
        dest = os.path.join(OUT, f"{name}-white.png")
        sq.save(dest)
        # A SILHOUETTE MUST ACTUALLY HAVE INK IN IT. A ramp set wrong gives a
        # blank square, which on a red disc looks exactly like a design choice.
        alpha = sq.split()[3]
        covered = sum(1 for v in alpha.getdata() if v > 128) / (sq.width * sq.height)
        assert 0.05 < covered < 0.80, f"{name}: ink covers {covered:.0%} of its square"
        made.append((name, sq.size, covered))
        print(f"  {name}-white.png  {sq.size[0]}x{sq.size[1]}  ink {covered:.0%}")
    print(f"\n{len(made)} silhouettes in {OUT}")


if __name__ == "__main__":
    main()
