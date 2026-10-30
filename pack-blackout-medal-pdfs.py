# -*- coding: utf-8 -*-
"""Wrap each Vol.8 medal BLEED render into a PDF at exact physical size.

Only the bleed artboards are packed. The `-disc` files are the cut-outs — they
are transparent outside the circle and belong in a design, not on a press sheet,
and PDF has no good answer for page transparency anyway.

The page is the trim size plus 3mm bleed on every side: a 50mm insert is a
56 x 56mm page with the disc centred in it, so the die has room to wander.

img2pdf is installed on **python3.13** in this container, not on the default
python3 (3.11):

  python3.13 pack-blackout-medal-pdfs.py
"""
import os
import re
import img2pdf

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "brand", "medals-blackout")
BLEED_MM = 3.0


def png_size(path):
    with open(path, "rb") as f:
        b = f.read(24)
    return int.from_bytes(b[16:20], "big"), int.from_bytes(b[20:24], "big")


def main():
    made = 0
    by_size = {}
    for f in sorted(os.listdir(OUT)):
        m = re.match(r"bo-medal-(\d+)mm-(\d)-bleed\.png$", f)
        if not m:
            continue
        size, place = int(m.group(1)), m.group(2)
        art = size + 2 * BLEED_MM
        png = os.path.join(OUT, f)
        w, h = png_size(png)
        if w != h:
            print(f"!! {f}: {w}x{h} is not square — the die would not fit")
            continue
        dpi = w / (art / 25.4)
        if abs(dpi - 300) > 4:
            print(f"!! {f}: {dpi:.0f} DPI, expected 300 — re-render first")
            continue
        layout = img2pdf.get_layout_fun(
            (img2pdf.mm_to_pt(art), img2pdf.mm_to_pt(art)))
        pdf = os.path.join(OUT, f.replace(".png", ".pdf"))
        with open(pdf, "wb") as fh:
            fh.write(img2pdf.convert(png, layout_fun=layout))
        print(f"{os.path.basename(pdf)}  {w}x{h}px  {dpi:.0f} DPI  "
              f"{art:.0f}x{art:.0f}mm (trim {size}mm + {BLEED_MM:.0f}mm bleed)")
        by_size.setdefault(size, []).append(png)
        made += 1

    # One file per size, because the printer wants one job per die.
    for size, pngs in sorted(by_size.items()):
        if len(pngs) < 2:
            continue
        art = size + 2 * BLEED_MM
        layout = img2pdf.get_layout_fun(
            (img2pdf.mm_to_pt(art), img2pdf.mm_to_pt(art)))
        allp = os.path.join(OUT, f"bo-medals-{size}mm-1-to-3.pdf")
        with open(allp, "wb") as fh:
            fh.write(img2pdf.convert(pngs, layout_fun=layout))
        print(f"\n{os.path.basename(allp)}  {len(pngs)} pages  "
              f"{os.path.getsize(allp)/1024:.0f}KB")
    print(f"\n{made} medal PDFs in {OUT}")


if __name__ == "__main__":
    main()
