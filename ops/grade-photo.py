# -*- coding: utf-8 -*-
"""Apply the Blackout grade to photos, without an image editor in the loop.

The style board tells a person (or a model) how to do it. This just does it —
same code the board's before/after is rendered with, so a batch run and the
reference picture cannot disagree.

  python3 ops/grade-photo.py night.jpg                  -> night-blackout.jpg
  python3 ops/grade-photo.py shots/*.jpg -o graded/
  python3 ops/grade-photo.py night.jpg --dark 1.0       -> keep its punch

--dark is the one knob worth touching: the grade deliberately pushes a photo
back so neon sits on top of it. At 1.0 you get the colour without the retreat,
which is what you want for a photo that is going out on its own.
"""
import argparse, os, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from PIL import Image
from ops.blackout_grade import P, grade


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("photos", nargs="+")
    ap.add_argument("-o", "--out-dir")
    ap.add_argument("--dark", type=float, default=P["dark"],
                    help="1.0 keeps the photo's punch; lower pushes it back (default %(default)s)")
    ap.add_argument("-q", "--quality", type=int, default=92)
    a = ap.parse_args()

    if a.out_dir:
        os.makedirs(a.out_dir, exist_ok=True)

    for src in a.photos:
        im = Image.open(src)
        out = grade(im, {"dark": a.dark})
        stem = os.path.splitext(os.path.basename(src))[0]
        dst = (os.path.join(a.out_dir, stem + ".jpg") if a.out_dir
               else os.path.join(os.path.dirname(src), stem + "-blackout.jpg"))
        out.save(dst, quality=a.quality)
        print(f"{os.path.basename(src):<34} -> {dst}   {out.width}x{out.height}")


if __name__ == "__main__":
    main()
