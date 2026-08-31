# -*- coding: utf-8 -*-
"""Wrap each 300 DPI certificate render into a print-ready PDF page.

Why not just print to PDF from the browser: Chromium's vector PDF export tiles
large blurred shadows, and the seams between tiles show as hard-edged
rectangular blocks. On these artboards that is glaringly visible around the
giant placement numeral, which carries a 90px text-shadow — while a screenshot
of the exact same page is perfectly smooth. The design leans on glow
everywhere (headline, chip, corner brackets, name rule), so there is no
targeted fix that leaves the design intact.

So the page is the raster, placed at exactly 297 x 167.06mm. At 3508px across
297mm that is 300 DPI, which is press-standard for artwork. Text is no longer
selectable, which does not matter for a certificate that gets printed and
signed.

  python3 pack-certificate-pdfs.py
"""
import img2pdf, os, sys
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "brand", "certificates-deck")
W_MM = 297.0
H_MM = round(W_MM * 1080 / 1920, 2)      # 167.06 — the design's own 16:9

def mm(v):
    return img2pdf.mm_to_pt(v)

layout = img2pdf.get_layout_fun(pagesize=(mm(W_MM), mm(H_MM)),
                                border=(0, 0), fit=img2pdf.FitMode.into)

made = []
for n in ["1st", "2nd", "3rd", "4th", "5th"]:
    png = os.path.join(OUT, f"aa-certificate-{n}.png")
    if not os.path.exists(png):
        sys.exit(f"missing {png} — run: node render-certificates-deck.mjs")
    im = Image.open(png)
    dpi = im.width / (W_MM / 25.4)
    if dpi < 290:
        sys.exit(f"{n}: raster is only {dpi:.0f} DPI across {W_MM}mm — too low for print")
    pdf = os.path.join(OUT, f"aa-certificate-{n}.pdf")
    with open(pdf, "wb") as f:
        f.write(img2pdf.convert(png, layout_fun=layout))
    made.append((n, im.size, dpi, os.path.getsize(pdf)))

for n, size, dpi, sz in made:
    print(f"{n}: {size[0]}x{size[1]}px  {dpi:.0f} DPI  ->  {W_MM}x{H_MM}mm  {sz/1024/1024:.1f}MB")

# The vector attempts are kept out of the delivered set.
for n in ["1st", "2nd", "3rd", "4th", "5th"]:
    v = os.path.join(OUT, f"_vector-{n}.pdf")
    if os.path.exists(v):
        os.remove(v)
