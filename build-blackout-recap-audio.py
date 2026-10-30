# -*- coding: utf-8 -*-
"""Score for the BLACKOUT Vol.8 season recap — original, synthesized.

Nothing here is sourced or sampled; every sound is generated from scratch,
which sidesteps the copyright problem for something going out on a business
account.

It is built around the SHAPE of the cut rather than running freely: the three
podium posters are the payoff, so the bed thins out under each data card and
opens up the instant the picture lands. The champion's poster gets the loudest
bar and the only real drop.

The cuts are READ OFF THE BUILT PAGE, not retyped here, so moving a scene moves
the music with it instead of leaving a hit half a second late.

  python3.13 build-blackout-recap-audio.py
"""
import json
import os
import re
import wave

import numpy as np

SP = os.environ.get("SP") or (
    "/tmp/claude-0/-home-user-May-madness/0e44f0ad-a683-5f0d-9de6-9459ae328963/scratchpad")
PAGE = os.path.join(SP, "blackout-recap.html")
OUT = os.path.join(SP, "video", "blackout-recap.wav")

if not os.path.exists(PAGE):
    raise SystemExit(f"no page at {PAGE} — run build-blackout-recap-video.py first")
_m = re.search(r"const D = (\{.*?\});\n", open(PAGE).read(), re.S)
if not _m:
    raise SystemExit("could not read the film's own timing out of the page")
_D = json.loads(_m.group(1))

CUTS = _D["starts"]
NAMES = _D["scenes"]
DUR = _D["dur"]
# The three posters, and the champion's among them.
SHOTS = [CUTS[i] for i, n in enumerate(NAMES) if n.startswith("shot")]
CHAMP = CUTS[NAMES.index("shot1")]
OUTRO = CUTS[NAMES.index("outro")]

SR = 44100
N = int(SR * DUR)
BPM = 118.0
SPB = 60.0 / BPM

low = np.zeros(N)
mid = np.zeros(N)
hit = np.zeros(N)


def at(t):
    return int(t * SR)


def env(n, a, d, curve=2.0):
    """Attack/decay envelope, n samples long."""
    e = np.zeros(n)
    na = max(1, int(a * SR))
    nd = max(1, min(n - na, int(d * SR)))
    e[:na] = np.linspace(0, 1, na)
    e[na:na + nd] = np.linspace(1, 0, nd) ** curve
    return e


def add(buf, t, sig):
    i = at(t)
    j = min(N, i + len(sig))
    if i < N:
        buf[i:j] += sig[: j - i]


def kick(t, g=1.0):
    n = int(0.30 * SR)
    k = np.arange(n) / SR
    f = 118 * np.exp(-k * 26) + 42
    add(low, t, g * 0.85 * np.sin(2 * np.pi * np.cumsum(f) / SR) * env(n, 0.001, 0.28, 2.4))


def tick(t, g=1.0):
    n = int(0.09 * SR)
    noise = np.random.default_rng(int(t * 1000) + 7).standard_normal(n)
    # A short, bright transient — the sound of a cut, not of a drum.
    add(hit, t, g * 0.22 * noise * env(n, 0.0008, 0.085, 3.0))


def sub(t, dur, hz, g=0.5):
    n = int(dur * SR)
    k = np.arange(n) / SR
    add(low, t, g * 0.5 * np.sin(2 * np.pi * hz * k) * env(n, 0.02, dur - 0.02, 1.1))


def pad(t, dur, root, g=0.5):
    """A quiet third-and-fifth bed. It moves once a scene and never on a beat,
    so it reads as the room rather than as part of the rhythm."""
    n = int(dur * SR)
    k = np.arange(n) / SR
    v = np.zeros(n)
    for mult, amp in ((1.0, 1.0), (1.5, 0.55), (2.0, 0.40), (2.5, 0.22)):
        v += amp * np.sin(2 * np.pi * root * mult * k + mult)
    v *= env(n, 0.55, dur - 0.55, 1.0)
    add(mid, t, g * 0.085 * v)


def arp(t, dur, root, g=0.4):
    """Eighth-note blips, the one thing that keeps time under the type."""
    steps = [0, 7, 12, 7, 3, 10, 12, 7]
    i = 0
    x = t
    while x < t + dur:
        hz = root * 2 ** (steps[i % len(steps)] / 12)
        n = int(0.10 * SR)
        k = np.arange(n) / SR
        v = np.sin(2 * np.pi * hz * k) + 0.3 * np.sin(2 * np.pi * hz * 2 * k)
        add(mid, x, g * 0.045 * v * env(n, 0.004, 0.09, 2.2))
        x += SPB / 2
        i += 1


def riser(t, dur, g=1.0):
    n = int(dur * SR)
    k = np.arange(n) / SR
    noise = np.random.default_rng(int(t * 100)).standard_normal(n)
    sweep = noise * (k / dur) ** 2
    add(mid, t, g * 0.10 * sweep)


def main():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)

    t = 0.0
    while t < DUR - 0.2:
        kick(t, 0.9 if (round(t / SPB) % 4 == 0) else 0.55)
        t += SPB

    # A pad per scene, climbing in thirds across the film.
    base = 110.0
    for i, c in enumerate(CUTS):
        end = CUTS[i + 1] if i + 1 < len(CUTS) else DUR
        pad(c, max(0.5, end - c), base * 2 ** ((i // 3) / 12.0), 0.5)
        # The arp carries the data cards and gets OUT of the way of the
        # posters: those are the payoff and the picture should carry them.
        if not NAMES[i].startswith("shot"):
            arp(c + 0.06, max(0.3, end - c - 0.2), base * 2, 0.36)

    for c in CUTS:
        tick(c, 1.0)
        sub(c, 0.75, 55.0, 0.55)

    # Each poster lands on a riser; the champion's gets the drop as well.
    for s in SHOTS:
        riser(max(0.0, s - 0.85), 0.8, 0.9)
        kick(s, 1.15)
        tick(s, 1.4)
    for h in (CHAMP, OUTRO):
        sub(h, 1.4, 41.2, 0.95)
        a, b = at(h - 0.14), at(h)
        for buf in (low, mid):
            buf[a:b] *= np.linspace(1.0, 0.05, max(1, b - a))

    mixbuf = low * 0.95 + mid + hit
    fade = int(1.2 * SR)
    mixbuf[-fade:] *= np.linspace(1, 0, fade)
    mixbuf[: int(0.05 * SR)] *= np.linspace(0, 1, int(0.05 * SR))

    peak = np.max(np.abs(mixbuf))
    if peak == 0:
        raise SystemExit("the mix is silent — nothing was written into it")
    mixbuf = np.tanh(mixbuf / peak * 1.3) * 0.90

    pcm = (mixbuf * 32767).astype(np.int16)
    with wave.open(OUT, "w") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    print(f"wrote {OUT}  {DUR:.1f}s  {os.path.getsize(OUT)/1024:.0f}KB  "
          f"{len(CUTS)} cuts read off the film")


if __name__ == "__main__":
    main()
