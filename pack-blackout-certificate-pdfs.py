# -*- coding: utf-8 -*-
"""Wrap each 300 DPI Vol.8 certificate render into a print-ready A4 page.

The page is placed at exactly 297 x 210mm — A4 landscape, no margin. At 3508px
across 297mm that is 300 DPI, which is press standard. Text is not selectable,
which does not matter for something that gets printed and signed by hand.

img2pdf and Pillow are installed on **python3.13** in this container, not on the
default python3 (3.11), the same way numpy is for the video builders:

  python3.13 pack-blackout-certificate-pdfs.py
"""
import os
import img2pdf

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "brand", "certificates-blackout")
W_MM, H_MM = 297.0, 210.0
PLACES = (1, 2, 3, 4, 5)


def png_size(path):
    with open(path, "rb") as f:
        b = f.read(24)
    return int.from_bytes(b[16:20], "big"), int.from_bytes(b[20:24], "big")


def main():
    layout = img2pdf.get_layout_fun(
        (img2pdf.mm_to_pt(W_MM), img2pdf.mm_to_pt(H_MM)))
    made, pngs = 0, []
    for place in PLACES:
        png = os.path.join(OUT, f"bo-certificate-{place}.png")
        if not os.path.exists(png):
            print(f"skip {place}: no png")
            continue
        w, h = png_size(png)
        # A4 landscape is 1.4143:1. Anything off that would be letterboxed or
        # stretched on the page, so catch it here rather than at the print shop.
        ratio = w / h
        if abs(ratio - W_MM / H_MM) > 0.01:
            print(f"!! {place}: aspect {ratio:.4f} is not A4 landscape "
                  f"({W_MM/H_MM:.4f}) — the page would not fit")
            continue
        dpi = w / (W_MM / 25.4)
        if abs(dpi - 300) > 2:
            print(f"!! {place}: {dpi:.0f} DPI, expected 300 — re-render first")
            continue
        pdf = os.path.join(OUT, f"bo-certificate-{place}.pdf")
        with open(pdf, "wb") as f:
            f.write(img2pdf.convert(png, layout_fun=layout))
        print(f"{os.path.basename(pdf)}  {w}x{h}px  {dpi:.0f} DPI  "
              f"{os.path.getsize(pdf)/1024/1024:.1f}MB")
        pngs.append(png)
        made += 1

    # One combined file, because the print shop wants a single job.
    if len(pngs) > 1:
        allp = os.path.join(OUT, "bo-certificates-1-to-5.pdf")
        with open(allp, "wb") as f:
            f.write(img2pdf.convert(pngs, layout_fun=layout))
        print(f"\n{os.path.basename(allp)}  {len(pngs)} pages  "
              f"{os.path.getsize(allp)/1024/1024:.1f}MB")
    print(f"\n{made} certificate PDFs in {OUT}")


if __name__ == "__main__":
    main()
