# -*- coding: utf-8 -*-
"""Score for the UPRISING night film — original, synthesized, not licensed.

Nothing here is sourced or sampled; every sound is generated from scratch,
which sidesteps the copyright problem for something going out on a business
account.

ONE HIT PER ROUND, ON THE CUT. The picture is a loop — chips move, scores land,
the table grows, twelve times — so the score is a loop too, and the only thing
that changes is what sits on top of it: nothing under the shuffle, a rising pad
through the middle, and everything on the doubled final. A score that developed
freely would fight a picture that deliberately does not.

The timing is READ OFF THE FILM rather than retyped: the intro length, the
round length and the round count come out of the built page, so moving a cut
moves the music with it instead of leaving the drop half a second late.

  python3.13 build-uprising-nightfilm-audio.py
"""
import json
import os
import re
import subprocess
import wave

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SP = os.environ.get("SP") or (
    "/tmp/claude-0/-home-user-May-madness/0e44f0ad-a683-5f0d-9de6-9459ae328963/scratchpad")
PAGE = os.path.join(SP, "uprising-night.html")
OUT = os.path.join(SP, "video", "uprising-night.wav")

if not os.path.exists(PAGE):
    raise SystemExit(f"no page at {PAGE} — run build-uprising-nightfilm.py first")
_src = open(PAGE).read()
_m = re.search(r"const D = (\{.*?\});\n", _src, re.S)
if not _m:
    raise SystemExit("could not read the film's own timing out of the page")
_D = json.loads(_m.group(1))

INTRO, RL = _D["intro"], _D["round"]
NR = len(_D["frames"])
DUR = _D["dur"]
# Every cut: the title, each round, and the finish.
CUTS = [0.0] + [INTRO + i * RL for i in range(NR)] + [INTRO + NR * RL]
SHUFFLE_UNTIL = INTRO + _D["shuffleRounds"] * RL
FINAL_AT = INTRO + (NR - 1) * RL
OUTRO_AT = INTRO + NR * RL

SR = 44100
N = int(SR * DUR)
BPM = 120.0
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

    # The pulse runs the whole way: the picture never stops, so neither does it.
    t = 0.0
    while t < DUR - 0.2:
        kick(t, 0.9 if (round(t / SPB) % 4 == 0) else 0.55)
        t += SPB

    # A pad per round, rising a semitone every three rounds. It is the only
    # thing in the mix that knows how far through the night we are.
    base = 110.0
    for i, c in enumerate(CUTS[:-1]):
        end = CUTS[i + 1]
        pad(c, max(0.5, end - c), base * 2 ** ((i // 3) / 12.0), 0.5)
        # The arp drops out under the shuffle, which scores nothing and should
        # feel like it is not counting yet.
        if c >= SHUFFLE_UNTIL and c < OUTRO_AT:
            arp(c + 0.06, max(0.3, end - c - 0.2), base * 2, 0.34)

    # A tick on every cut and a sub under it — the sound of the chips landing.
    for c in CUTS:
        tick(c, 1.0)
        sub(c, 0.75, 55.0, 0.55)

    # The two the film is built around: the doubled final, and the finish.
    for h in (FINAL_AT, OUTRO_AT):
        riser(max(0.0, h - 1.05), 1.0, 1.0)
        kick(h, 1.3)
        tick(h, 1.7)
        sub(h, 1.4, 41.2, 0.95)
        a, b = at(h - 0.14), at(h)
        for buf in (low, mid):
            buf[a:b] *= np.linspace(1.0, 0.05, max(1, b - a))

    mixbuf = low * 0.95 + mid + hit
    fade = int(1.1 * SR)
    mixbuf[-fade:] *= np.linspace(1, 0, fade)
    mixbuf[: int(0.05 * SR)] *= np.linspace(0, 1, int(0.05 * SR))

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
          f"{NR} rounds, cuts read off the film")


if __name__ == "__main__":
    main()
