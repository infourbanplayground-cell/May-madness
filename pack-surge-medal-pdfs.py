# -*- coding: utf-8 -*-
"""Wrap the medal-sticker renders into PDFs at exact physical size.

Only the bleed artboards are packed: a die-cut sticker needs the 3mm bleed, and
the trimmed disc PNGs are for digital use where a PDF adds nothing.

  python3 pack-surge-medal-pdfs.py
"""
import os, img2pdf
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "brand", "medal-stickers")
BLEED_MM = 3.0

def main():
    made = []
    for size in (50, 25):
        art = size + 2 * BLEED_MM
        layout = img2pdf.get_layout_fun((img2pdf.mm_to_pt(art), img2pdf.mm_to_pt(art)))
        pages = []
        for place in (1, 2, 3):
            png = os.path.join(OUT, f"ss-medal-{size}mm-{place}-bleed.png")
            if not os.path.exists(png):
                continue
            w, h = Image.open(png).size
            if w != h:
                print(f"!! {png}: {w}x{h} is not square — the die would not centre")
                continue
            pdf = os.path.join(OUT, f"ss-medal-{size}mm-{place}.pdf")
            with open(pdf, "wb") as f:
                f.write(img2pdf.convert(png, layout_fun=layout))
            dpi = w / (art / 25.4)
            print(f"{os.path.basename(pdf)}  {w}x{h}px  {dpi:.0f} DPI  "
                  f"{art:.0f}mm artboard ({size}mm trim + {BLEED_MM:.0f}mm bleed)")
            pages.append(png); made.append(pdf)
        if pages:
            allp = os.path.join(OUT, f"ss-medals-{size}mm-1-to-3.pdf")
            with open(allp, "wb") as f:
                f.write(img2pdf.convert(pages, layout_fun=layout))
            print(f"  -> {os.path.basename(allp)}  {len(pages)} pages\n")
    print(f"{len(made)} sticker PDFs in {OUT}")

if __name__ == "__main__":
    main()
