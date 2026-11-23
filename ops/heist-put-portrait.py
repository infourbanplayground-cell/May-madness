#!/usr/bin/env python3.13
"""Put one finished Heist portrait live:  python3.13 ops/heist-put-portrait.py <image> <player id>

The owner generates each portrait from a reference that carries a name strip
(a navy bar under a coral rule, "04  Mutaz Zadjali / p_..."), and ChatGPT copies
the strip into the art — which is how we know who it is. So this:
  1. finds the coral rule and cuts everything below it (if there is one),
  2. finds the face (YuNet) and cuts 4:5 around it, face in the top third,
  3. writes 1080x1350 JPEG and refuses a source too small to stay sharp,
  4. uploads it the way the photos API does (old file to history, atomic
     rename, a line in uploads.log), and checks the served bytes are ours.
DRY=1 stops after writing the crop into the scratch dir.
"""
import os, sys, subprocess, tempfile, time, urllib.request
import cv2
from PIL import Image

src, pid = sys.argv[1], sys.argv[2]
im = Image.open(src).convert("RGB"); W, H = im.size
px = im.load()

# 1. the coral rule of the name strip, searched in the bottom 35%
bar = None
for y in range(int(H * .65), H):
    n = sum(1 for x in range(0, W, 8) if px[x, y][0] > 200 and 100 < px[x, y][1] < 190 and px[x, y][2] < 140)
    if n > (W / 8) * .8: bar = y; break
art = im.crop((0, 0, W, bar - 2)) if bar else im
aw, ah = art.size
print(f"source {W}x{H}" + (f", name strip cut at y={bar}" if bar else ", no name strip"))

# 2. the face
tmp = tempfile.mktemp(suffix=".png"); art.save(tmp)
img = cv2.imread(tmp); os.unlink(tmp)
det = cv2.FaceDetectorYN.create(os.path.join(os.path.dirname(__file__), "models/face_detection_yunet_2023mar.onnx"), "", (aw, ah), .7, .3, 50)
_, faces = det.detect(img)
if faces is None or not len(faces): sys.exit("no face found — crop it by hand")
x, y, fw, fh = max(faces, key=lambda f: f[2] * f[3])[:4]
cx, cy = x + fw / 2, y + fh / 2

# 4:5 box as large as the art allows, the face's centre at ~30% height
ch = min(ah, round(aw * 5 / 4)); cw = round(ch * 4 / 5)
x0 = int(min(max(0, cx - cw / 2), aw - cw)); y0 = int(min(max(0, cy - ch * .30), ah - ch))
crop = art.crop((x0, y0, x0 + cw, y0 + ch))
print(f"face {int(fw)}px at ({int(cx)},{int(cy)}) · crop {cw}x{ch} at ({x0},{y0}) · face at {round((cy - y0) / ch * 100)}% height")
MIN = int(os.environ.get("MIN", 700))   # MIN=250 when the owner accepts a soft one for now
if cw < MIN: sys.exit(f"source too small ({cw}px wide after the crop) — ask for a bigger render")
if cw < 1080: print(f"note: enlarged {1080 / cw:.2f}x")

out = os.path.join(os.environ.get("OUT", "/tmp"), pid + ".jpg")
big = crop.resize((1080, 1350), Image.LANCZOS)
if 1080 / cw > 1.6:   # a big enlargement goes soft; a light unsharp mask brings the line work back
    from PIL import ImageFilter
    big = big.filter(ImageFilter.UnsharpMask(radius=2.2, percent=90, threshold=2))
big.save(out, quality=90)
print("wrote", out)
if os.environ.get("DRY"): sys.exit(0)

# 3. upload, as the API would
# stdin=DEVNULL: ssh otherwise reads the caller's stdin, which ate the rest of a
# `while read` batch after the first upload
sh = lambda c: subprocess.run(c, shell=True, check=True, capture_output=True, text=True, stdin=subprocess.DEVNULL).stdout
sh(f"scp -q {out} urbanpadel:/tmp/{pid}.jpg")
print(sh(f"""ssh urbanpadel 'set -e; P=/var/www/heist.urbanpadel.om/public/players
  [ -f $P/{pid}.jpg ] && mv $P/{pid}.jpg /opt/heist-api/history/{pid}.$(date +%s%3N).replace.jpg || true
  cp /tmp/{pid}.jpg $P/{pid}.jpg.tmp; mv $P/{pid}.jpg.tmp $P/{pid}.jpg
  printf "%s\\tadmin-ssh\\tput\\t{pid}\\t\\t%s\\n" $(date -u +%Y-%m-%dT%H:%M:%S.000Z) $(stat -c%s $P/{pid}.jpg) >> /opt/heist-api/uploads.log
  tail -1 /opt/heist-api/uploads.log'""").strip())
req = urllib.request.Request(f"https://heist.urbanpadel.om/players/{pid}.jpg?v={int(time.time())}", headers={"User-Agent": "Mozilla/5.0"})
live = urllib.request.urlopen(req, timeout=30).read()
if live != open(out, "rb").read(): sys.exit("served file differs from the upload")
print("live = local")
