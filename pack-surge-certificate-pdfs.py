# -*- coding: utf-8 -*-
"""Wrap each 300 DPI Vol.7 certificate render into a print-ready A4 page.

Why the page is a raster and not Chromium's vector PDF export: the design leans
on large soft glows — the placement numeral carries a 4mm and an 18mm shadow,
and the accent rules and ripple are soft too. Chromium's PDF writer tiles big
blurred shadows, and the seams between tiles print as hard-edged rectangular
blocks, while a screenshot of the identical page is perfectly smooth. The same
reasoning applies here as to the Vol.6 deck; see pack-certificate-pdfs.py.

The page is placed at exactly 297 x 210mm — A4 landscape, no margin. At 3508px
across 297mm that is 300 DPI, which is press standard. Text is not selectable,
which does not matter for something that gets printed and signed by hand.

  python3 pack-surge-certificate-pdfs.py
"""
import os
import img2pdf
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "brand", "certificates-surge")
W_MM, H_MM = 297.0, 210.0


def main():
    layout = img2pdf.get_layout_fun(
        (img2pdf.mm_to_pt(W_MM), img2pdf.mm_to_pt(H_MM)))
    made = 0
    for place in (1, 2, 3, 4, 5):
        png = os.path.join(OUT, f"ss-certificate-{place}.png")
        if not os.path.exists(png):
            print(f"skip {place}: no png")
            continue
        w, h = Image.open(png).size
        # A4 landscape is 1.4143:1. Anything off that would be letterboxed or
        # stretched on the page, so catch it here rather than at the print shop.
        ratio = w / h
        if abs(ratio - W_MM / H_MM) > 0.01:
            print(f"!! {place}: aspect {ratio:.4f} is not A4 landscape "
                  f"({W_MM/H_MM:.4f}) — page would not fit")
            continue
        dpi = w / (W_MM / 25.4)
        pdf = os.path.join(OUT, f"ss-certificate-{place}.pdf")
        with open(pdf, "wb") as f:
            f.write(img2pdf.convert(png, layout_fun=layout))
        print(f"{os.path.basename(pdf)}  {w}x{h}px  {dpi:.0f} DPI  "
              f"{os.path.getsize(pdf)/1024/1024:.1f}MB")
        made += 1

    # One combined file, because the print shop wants a single job.
    pngs = [os.path.join(OUT, f"ss-certificate-{p}.png") for p in (1, 2, 3, 4, 5)]
    pngs = [p for p in pngs if os.path.exists(p)]
    if len(pngs) > 1:
        allp = os.path.join(OUT, "ss-certificates-1-to-5.pdf")
        with open(allp, "wb") as f:
            f.write(img2pdf.convert(pngs, layout_fun=layout))
        print(f"\n{os.path.basename(allp)}  {len(pngs)} pages  "
              f"{os.path.getsize(allp)/1024/1024:.1f}MB")
    print(f"\n{made} certificate PDFs in {OUT}")


if __name__ == "__main__":
    main()
