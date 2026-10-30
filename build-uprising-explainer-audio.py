# -*- coding: utf-8 -*-
"""Score for the UPRISING explainer — original, synthesized, not licensed.

Nothing here is sourced or sampled; every sound is generated from scratch,
which sidesteps the copyright problem for something going out on a business
account.

DIFFERENT JOB FROM THE NIGHT-BEFORE FILM'S SCORE. That one climbs and drops
and is trying to make you want a place. This one is under somebody being TOLD
something, so it stays out of the way: a steady pulse, a pad that moves once a
scene, and a tick on each cut. The only two places it opens up are the moment
the chip first climbs and the last line — the same two the picture is built
around.

Numbers are imported from build-uprising-explainer.py rather than retyped. The
older films keep their own copy of the scene table, and a copy is a thing that
can disagree with the picture after somebody moves a cut by 200ms.

  python3.13 build-uprising-explainer-audio.py     # numpy is on 3.13 here
"""
import os
import sys
import wave

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from build_uprising_explainer_consts import SCENES, BEATS, HERO, DUR, SP  # noqa: E402

OUT = os.path.join(SP, "video", "uprising-explainer.wav")

SR = 44100
N = int(SR * DUR)
BPM = 112.0
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

    # The pulse. Every bar through the whole film, so the thing never stops
    # moving under somebody reading.
    t = 0.0
    while t < DUR - 0.2:
        kick(t, 0.9 if (round(t / SPB) % 4 == 0) else 0.6)
        t += SPB

    # The pad changes root once a scene. Minor, rising a tone across the film,
    # which is the only "climb" the score does — the picture does the rest.
    roots = [110.0, 110.0, 123.47, 110.0, 130.81, 123.47, 130.81, 146.83]
    for i, s in enumerate(SCENES):
        end = SCENES[i + 1] if i + 1 < len(SCENES) else DUR
        pad(s, end - s, roots[i % len(roots)], 0.5)
        # The arp drops out under the ladder and under the points table, where
        # rows are landing one after another and a running pulse fights them.
        if i not in (4, 5):
            arp(s + 0.1, max(0.4, end - s - 0.3), roots[i % len(roots)] * 2, 0.4)

    # A tick on every cut, and a sub under the scene it opens.
    for s in SCENES:
        tick(s, 1.0)
        sub(s, 0.9, 55.0, 0.6)

    # The two the film is built around get a riser into them and a drop out of
    # it: half a beat of nothing, so the moment lands on silence turning back
    # into everything.
    for h in HERO:
        riser(max(0.0, h - 1.1), 1.05, 1.0)
        kick(h, 1.25)
        tick(h, 1.6)
        sub(h, 1.4, 41.2, 0.9)
        a, b = at(h - 0.14), at(h)
        for buf in (low, mid):
            buf[a:b] *= np.linspace(1.0, 0.05, max(1, b - a))

    # Beats that are not cuts get a light tick, so the type lands on something.
    cuts = set(round(s, 2) for s in SCENES)
    for b in BEATS:
        if round(b, 2) not in cuts:
            tick(b, 0.45)

    mixbuf = low * 0.95 + mid + hit
    # Four seconds of tail-off at the end rather than a cliff.
    fade = int(0.9 * SR)
    mixbuf[-fade:] *= np.linspace(1, 0, fade)
    mixbuf[:int(0.05 * SR)] *= np.linspace(0, 1, int(0.05 * SR))

    peak = np.max(np.abs(mixbuf))
    if peak == 0:
        raise SystemExit("the mix is silent — nothing was written into it")
    mixbuf = np.tanh(mixbuf / peak * 1.3) * 0.90

    pcm = (mixbuf * 32767).astype(np.int16)
    with wave.open(OUT, "w") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    print(f"wrote {OUT}  {DUR:.1f}s  {os.path.getsize(OUT)/1024:.0f}KB  "
          f"peak {peak:.2f} -> normalised")


if __name__ == "__main__":
    main()
