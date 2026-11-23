#!/usr/bin/env python3.13
"""MUSCAT HEIST — portraits WITHOUT an image API: the Heist treatment.

    python3.13 ops/heist-treatment.py --limit 3          a sample batch
    python3.13 ops/heist-treatment.py                    everyone the brief lists
    python3.13 ops/heist-treatment.py --only "Hamed Amri"
    then:  npm run heist -- --upload-only               upload + verify (SSH or HEIST_PIN)
    (npm run heist:treat -- --limit 3 is the same thing)

Needs: python3.13 -m pip install opencv-python-headless numpy pillow (the face
finder, YuNet, is committed at ops/models/face_detection_yunet_2023mar.onnx).

No new picture is invented: each player's OWN photo is graded into the Heist
palette, so the likeness is exact by construction. Same brief, same file names,
same progress.json and the same upload step as the generated route — this only
replaces the "generate" stage.

  1. crop 4:5 around the centre, a little high (faces sit in the top half of
     almost every source), and upscale to 1080x1350 with Lanczos
  2. GRADIENT MAP on luminance: navy shadows -> deep blue -> coral -> peach ->
     sand. Every source has different light; mapping them all through one ramp
     is what makes 36 phone photos read as ONE set, and it is far more
     forgiving of a 200px thumbnail than a natural-colour upscale
  3. light: a teal floodlight from the left, coral sunset from the right
     (screen blend, low), like the style prompt
  4. a navy vignette and a heavier fade at the foot, where the app sets type
  5. film grain, which also hides the upscale's softness
"""
import argparse, json, os, re, sys, urllib.request
from datetime import datetime, timezone
import numpy as np
from PIL import Image, ImageFilter, ImageOps

HOST = os.environ.get("HEIST_HOST", "https://heist.urbanpadel.om")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.environ.get("HEIST_OUT", os.path.join(ROOT, "brand/heist/portraits"))
PROG = os.path.join(OUT, "progress.json")
W, H = 1080, 1350

# the Heist tokens (brand/heist/heist.css), shadow -> highlight
RAMP = [(0.00, "#0B1522"), (0.22, "#13202F"), (0.42, "#24456E"), (0.62, "#F26B5B"),
        (0.80, "#F59A62"), (0.92, "#FFC9A3"), (1.00, "#FFF4E8")]
TEAL, CORAL, NAVY = "#2FB7B0", "#F26B5B", "#0F1B2B"
rgb = lambda h: np.array([int(h[i:i + 2], 16) for i in (1, 3, 5)], dtype=np.float32)

def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "heist-treatment"}), timeout=30) as r:
        return r.read()

def brief(all_=False):
    text = get(f"{HOST}/api/brief{'?all' if all_ else ''}").decode()
    out = []
    for line in text.splitlines():
        m = re.match(r"^\d+\.\s+(.+?)\s+—\s+photo:\s+(\S+/api/ref/([\w-]+))\s+—\s+save as:\s+(.+?)\s*$", line)
        if m: out.append({"name": m[1], "ref": m[2], "id": m[3], "file": m[4]})
    head = re.search(r"^## To do — (\d+) players", text, re.M)
    if head and int(head[1]) != len(out):
        sys.exit(f"!! brief header says {head[1]} players, parsed {len(out)} — the format changed")
    return out

def crop45(im):
    w, h = im.size
    if w / h > W / H:                      # too wide: trim the sides
        nw = round(h * W / H); x = (w - nw) // 2
        return im.crop((x, 0, x + nw, h))
    nh = round(w * H / W); y = round((h - nh) * 0.25)   # too tall: keep the head
    return im.crop((0, y, w, y + nh))

# ── the face decides the crop ───────────────────────────────────────────────
# A centre crop of "7up"'s photo was the club logo with him as a speck at the
# foot. YuNet (OpenCV's own face model, ops/models/, 230KB) finds the face and
# the frame is built round it: head and shoulders, face centre at 36% height.
MIN_FACE = 32                              # source pixels; under this it is a smudge at 1080
_det = None
def find_face(im):
    global _det
    import cv2
    if _det is None:
        _det = cv2.FaceDetectorYN.create(os.path.join(ROOT, "ops/models/face_detection_yunet_2023mar.onnx"), "", (320, 320), 0.6)
    a = cv2.cvtColor(np.asarray(im), cv2.COLOR_RGB2BGR)
    s = max(1, round(640 / max(a.shape[:2])))  # thumbnails are too small for the detector as they are
    big = cv2.resize(a, None, fx=s, fy=s, interpolation=cv2.INTER_CUBIC) if s > 1 else a
    _det.setInputSize((big.shape[1], big.shape[0])); _, faces = _det.detect(big)
    if faces is None or not len(faces): return None
    x, y, w, h = (float(v) / s for v in max(faces, key=lambda f: f[2] * f[3])[:4])
    return x, y, w, h

def crop_face(im, face):
    iw, ih = im.size; x, y, fw, fh = face
    cw = min(fw * 3.0, iw, ih * W / H); ch = cw * H / W
    cx, cy = x + fw / 2, y + fh / 2
    left = min(max(cx - cw / 2, 0), iw - cw); top = min(max(cy - ch * 0.36, 0), ih - ch)
    return im.crop((round(left), round(top), round(left + cw), round(top + ch)))

class TooSmall(Exception): pass

def treat(src_bytes, seed):
    from io import BytesIO
    im = ImageOps.exif_transpose(Image.open(BytesIO(src_bytes))).convert("RGB")
    face = find_face(im)
    if face and face[2] < MIN_FACE:
        raise TooSmall(f"face is only {face[2]:.0f}px wide in the source — needs a closer photo")
    small = min(im.size) < 600
    im = (crop_face(im, face) if face else crop45(im)).resize((W, H), Image.LANCZOS)
    if small: im = im.filter(ImageFilter.GaussianBlur(1.2))   # melt the upscale's stair-steps
    a = np.asarray(im, dtype=np.float32) / 255
    lum = a @ np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)
    # stretch each photo to the full range first, so dark and bright sources land alike
    lo, hi = np.percentile(lum, 2), np.percentile(lum, 98)
    lum = np.clip((lum - lo) / max(hi - lo, 1e-3), 0, 1)
    lum = lum ** 0.9
    xs = np.array([p for p, _ in RAMP]); cs = np.stack([rgb(c) for _, c in RAMP])
    out = np.stack([np.interp(lum, xs, cs[:, k]) for k in range(3)], -1) / 255
    # keep a little of the real colour in skin, so faces are not flat orange
    out = out * 0.82 + a * 0.18
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    def screen(base, colour, mask):
        c = rgb(colour) / 255
        return 1 - (1 - base) * (1 - c * mask[..., None])
    out = screen(out, TEAL, np.clip(1 - xx / (W * 0.55), 0, 1) ** 2 * 0.34)
    out = screen(out, CORAL, np.clip((xx - W * 0.45) / (W * 0.55), 0, 1) ** 2 * 0.28)
    # vignette + a heavier navy fade over the bottom fifth
    d = np.sqrt(((xx - W / 2) / (W * 0.62)) ** 2 + ((yy - H * 0.42) / (H * 0.66)) ** 2)
    v = np.clip((d - 0.55) / 0.6, 0, 1) ** 1.6 * 0.75 + np.clip((yy - H * 0.78) / (H * 0.22), 0, 1) ** 1.4 * 0.55
    out = out * (1 - np.clip(v, 0, 0.9)[..., None]) + rgb(NAVY) / 255 * np.clip(v, 0, 0.9)[..., None]
    # grain
    rng = np.random.default_rng(seed)
    g = rng.normal(0, 0.035 if small else 0.022, (H, W)).astype(np.float32)
    out = np.clip(out + g[..., None], 0, 1)
    return Image.fromarray((out * 255 + 0.5).astype(np.uint8))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int); ap.add_argument("--only", default="")
    ap.add_argument("--force", action="store_true"); ap.add_argument("--all", action="store_true")
    A = ap.parse_args()
    os.makedirs(os.path.join(OUT, "sources"), exist_ok=True)
    prog = json.load(open(PROG)) if os.path.exists(PROG) else {}
    people = brief(A.all)
    if A.only:
        want = {s.strip().lower() for s in A.only.split(",") if s.strip()}
        people = [p for p in people if p["id"].lower() in want or p["name"].lower() in want]
    if not A.force:
        people = [p for p in people if prog.get(p["id"], {}).get("status") not in ("generated", "uploaded")]
    people = people[:A.limit] if A.limit else people
    print(f"brief -> {len(people)} to treat · out {os.path.relpath(OUT, ROOT)}")
    for p in people:
        try:
            src = get(p["ref"])
            open(os.path.join(OUT, "sources", p["id"] + ".png"), "wb").write(src)  # raw source, for the review sheet
            img = treat(src, seed=sum(map(ord, p["id"])))
            img.save(os.path.join(OUT, p["file"]))                                  # the brief's exact file name
            prog[p["id"]] = {**prog.get(p["id"], {}), "name": p["name"], "file": p["file"], "status": "generated",
                             "model": "heist-treatment", "at": datetime.now(timezone.utc).isoformat()}
            prog[p["id"]].pop("error", None)
            print(f"  [generated] {p['name']} -> {p['file']}  ({Image.open(__import__('io').BytesIO(src)).size[0]}px source)")
        except TooSmall as e:
            prog[p["id"]] = {**prog.get(p["id"], {}), "name": p["name"], "file": p["file"], "status": "failed",
                             "error": str(e), "at": datetime.now(timezone.utc).isoformat()}
            print(f"  [failed] {p['name']} — {e}")
        except Exception as e:
            prog[p["id"]] = {**prog.get(p["id"], {}), "name": p["name"], "file": p["file"], "status": "failed",
                             "error": str(e), "at": datetime.now(timezone.utc).isoformat()}
            print(f"  [failed] {p['name']} — {e}")
        tmp = PROG + ".tmp"; json.dump(prog, open(tmp, "w"), indent=2); os.replace(tmp, PROG)

if __name__ == "__main__":
    main()
