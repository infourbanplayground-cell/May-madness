# -*- coding: utf-8 -*-
"""The Blackout photo grade, as code.

The palette is written down (blackout-season.json) and the type is written down
(DESIGN.md), but the way a PHOTO is supposed to look was only ever in the share
cards, mixed into a canvas draw call. So nobody could apply it to a photo
outside the app, and nobody could describe it to an image editor.

This is the grade on its own: in, out, and the numbers in between. The style
board renders a before/after with it, and the prompt on that board is a
plain-English reading of exactly these steps — so if one changes, the other is
wrong, and both come from here.

    from ops.blackout_grade import grade
    grade(Image.open("night.jpg")).save("night-blackout.jpg")

The look, in one line: a floodlit court at night, cooled and crushed, with the
volume's two neons doing the work the floodlights were doing — lime in the
highlights, UV in the shadows, magenta only on an edge.
"""
import numpy as np
from PIL import Image

# The three colours the grade is allowed to introduce. These are the season's,
# not a photographer's taste: lime leads, UV is the room, magenta is rare.
LIME = (0xC6, 0xFF, 0x00)
UV = (0x2E, 0x0B, 0x73)
MAGENTA = (0xFF, 0x2E, 0x88)
BLACK = 0x05 / 255.0  # #050505 — the volume's ground, and the grade's floor

# Every number the grade turns on, in one place, so the board can print them.
P = dict(
    lo_pct=2.0,       # the frame is levelled on its own distribution first —
    hi_pct=99.0,      # see the note in grade(); fixed bands do nothing here
    desat=0.70,       # how much colour comes out before the neons go in
    gamma=1.18,       # mid-tones down — a floodlit court reads too flat otherwise
    contrast=1.32,    # pivoted on 0.44, not 0.5: the frame is mostly night
    pivot=0.44,
    lime_hi=0.40,     # lime into the top end
    lime_from=0.50,   # where "the top end" starts, after levelling
    uv_lo=0.45,       # UV into the bottom end
    uv_from=0.60,     # where "the bottom end" ends, after levelling
    magenta_rim=0.26, # magenta only where the image is already an edge
    dark=0.80,        # the whole frame pushed back — see the note in grade()
    vignette=0.30,
    grain=0.020,
    floor=BLACK,
)


def _lum(a):
    return a[..., 0] * 0.2126 + a[..., 1] * 0.7152 + a[..., 2] * 0.0722


def grade(img, p=None, seed=8):
    """Apply the Blackout grade to a PIL image and return a new PIL image."""
    p = {**P, **(p or {})}
    a = np.asarray(img.convert("RGB"), dtype=np.float32) / 255.0

    # 0. Level the frame on its own distribution before anything else.
    #    A floodlit court at night lands almost entirely between 0.11 and 0.51
    #    — there are no highlights in the numeric sense at all. Split-toning
    #    against fixed thresholds therefore did nothing visible: the lime had
    #    no top end to ride and the UV sat under blacks that were already
    #    black. Stretching the frame's own 2nd-98th percentile to 0..1 first is
    #    what gives the two neons something to attach to, and it is why this
    #    grade looks the same on an overexposed phone shot and a dark one.
    L0 = _lum(a)
    lo = float(np.percentile(L0, p["lo_pct"]))
    hi = float(np.percentile(L0, p["hi_pct"]))
    if hi - lo > 1e-3:
        a = np.clip((a - lo) / (hi - lo), 0, 1)

    # 1. Pull the colour down before putting any back. Skin keeps enough to
    #    read as skin; the court's orange, which fights every colour in the
    #    palette, mostly goes.
    g = _lum(a)[..., None]
    a = a * (1 - p["desat"]) + g * p["desat"]

    # 2. Mid-tones down, then contrast pivoted low. A night frame is mostly
    #    shadow, so pivoting on 0.5 would lift the dark half of the picture —
    #    the opposite of the point.
    a = np.clip(a, 0, 1) ** p["gamma"]
    a = np.clip((a - p["pivot"]) * p["contrast"] + p["pivot"], 0, 1)

    # 3. Split tone. Lime rides the highlights, UV sits under the shadows, and
    #    each is weighted by how much of that end the pixel actually is — a
    #    flat overlay would tint the faces too.
    L = _lum(a)
    hiw = np.clip((L - p["lime_from"]) / max(1e-3, 1 - p["lime_from"]), 0, 1)
    low = np.clip((p["uv_from"] - L) / max(1e-3, p["uv_from"]), 0, 1)
    hi = (hiw ** 1.25)[..., None]
    lo = (low ** 1.15)[..., None]
    lime = np.array(LIME, np.float32) / 255.0
    uv = np.array(UV, np.float32) / 255.0
    a = a + (lime - a) * hi * p["lime_hi"]
    a = a + (uv - a) * lo * p["uv_lo"]

    # 4. The magenta rim. Magenta is the rare colour in this volume, so it is
    #    not allowed to wash anything — it goes only where the picture already
    #    has a hard edge against the dark, which on a night court is the
    #    players' outline.
    L2 = _lum(a)
    gy, gx = np.gradient(L2)
    edge = np.clip(np.hypot(gx, gy) * 7.0, 0, 1)
    edge *= np.clip((L2 - 0.18) / 0.4, 0, 1)      # not in the pure black
    mag = np.array(MAGENTA, np.float32) / 255.0
    a = a + (mag - a) * edge[..., None] * p["magenta_rim"]

    # 5. Push the whole frame back, vignette, then the floor.
    #
    #    The push-back is the part that makes this a BRAND treatment rather
    #    than a filter. In this volume a photograph is a ground, not the
    #    subject: the lime and the magenta on top of it are the subject, and
    #    they only read as neon if there is nothing else in the frame
    #    competing at that brightness. So the photo gives up its top end on
    #    purpose. Raise `dark` towards 1.0 and the picture gets its punch back
    #    — and the lockup sitting on it stops glowing.
    #
    #    The floor is last so nothing the grade did can end up darker than the
    #    volume's own black.
    a *= p["dark"]
    h, w = a.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w]
    r = np.hypot((xx - w / 2) / (w / 2), (yy - h / 2) / (h / 2)) / 1.414
    a *= (1 - p["vignette"] * np.clip(r, 0, 1) ** 2.2)[..., None]
    a = p["floor"] + a * (1 - p["floor"])

    # 6. Grain. Fine and monochrome — colour noise would read as a bad camera
    #    rather than as film, and this is the one thing that stops the flat
    #    areas of a crushed night frame from banding.
    rng = np.random.default_rng(seed)
    a += rng.normal(0, p["grain"], (h, w, 1)).astype(np.float32)

    return Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8))
