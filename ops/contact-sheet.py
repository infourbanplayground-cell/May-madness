# -*- coding: utf-8 -*-
"""Contact sheet from a rendered film, for reviewing it without playing it.

Pulls a frame from the settled part of each scene — not the cut, where the
entrance is still running and every frame looks half-finished — and tiles them.
Takes the scene table from the film's own builder so the sheet cannot drift out
of step with the cuts.

  python3 ops/contact-sheet.py announce
"""
import importlib.util, os, sys
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SP = "/tmp/claude-0/-home-user-May-madness/0e44f0ad-a683-5f0d-9de6-9459ae328963/scratchpad"

name = sys.argv[1] if len(sys.argv) > 1 else "announce"
# The recorders abbreviate their frame directories differently (_annframes,
# _featframes), so match on a prefix rather than guessing a fixed truncation —
# a wrong guess here silently produces a sheet of missing tiles.
cands = [d for d in os.listdir(SP)
         if d.startswith("_") and d.endswith("frames") and name.startswith(d[1:-6])]
if not cands:
    sys.exit(f"no frame directory in {SP} for '{name}'")
frames = os.path.join(SP, sorted(cands, key=len)[-1])

spec = importlib.util.spec_from_file_location(
    "film", os.path.join(HERE, f"build-{name}-video.py"))
film = importlib.util.module_from_spec(spec)
spec.loader.exec_module(film)

FPS = 30
ends = list(film.SCENES[1:]) + [film.DUR]
# 72% into each scene: the entrance has landed, the exit has not started.
picks = [a + (b - a) * 0.72 for a, b in zip(film.SCENES, ends)]

cols = 4
rows = (len(picks) + cols - 1) // cols
tw = 300
th = int(tw * film.H / film.W)
sheet = Image.new("RGB", (cols * tw + (cols + 1) * 12, rows * (th + 30) + 12), (12, 12, 12))
d = ImageDraw.Draw(sheet)

for i, t in enumerate(picks):
    f = os.path.join(frames, f"f{round(t * FPS):05d}.png")
    if not os.path.exists(f):
        print(f"  missing {f}")
        continue
    im = Image.open(f).convert("RGB").resize((tw, th), Image.LANCZOS)
    x = 12 + (i % cols) * (tw + 12)
    y = 12 + (i // cols) * (th + 30)
    sheet.paste(im, (x, y))
    d.text((x + 2, y + th + 8), f"scene {i+1}  {t:.1f}s", fill=(160, 160, 160))

out = os.path.join(SP, f"{name}-sheet.png")
sheet.save(out)
print(f"wrote {out}  {len(picks)} scenes")
