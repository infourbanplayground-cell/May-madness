# -*- coding: utf-8 -*-
"""The score for the Muscat Heist launch film — a heist-trailer bed, all
synthesised (nothing to license).

It reads the picture's OWN cut table ($SP/heist-launch.cut.json, written by
build-heist-video.py), so the cuts, the montage hits and the stabs land on the
same beats the picture cuts on. Two media reading one table is the only way
they stay in step.

The shape is a CAPER, not a countdown and not an invitation:
  the open      a low D drone, a clock ticking on the beat, a muted pulse
  the crew      the kick arrives; a hit on every montage cut, the bass walks
  the job       claps on 2 and 4, the stabs turn minor and louder (2X)
  the take      everything, plus a rising filtered riser into the ask
  the ask       a 0.12s STOP, then the full groove to one last hit and a ring-out

Asserted at the foot: no clipping, the ask the loudest block, every block at
least as loud as the open, the stop really silent, and most of the energy
below 4kHz (white-noise percussion is mostly hiss unless it is filtered).

NUMPY IS ON python3.13 in this container, not the default python3.

  python3.13 build-heist-audio.py
"""
import json
import os
import wave

import numpy as np

SP = ("/tmp/claude-0/-home-user-May-madness/"
      "0e44f0ad-a683-5f0d-9de6-9459ae328963/scratchpad")
C = json.load(open(os.environ.get("CUT") or os.path.join(SP, "heist-launch.cut.json")))
DUR, SCENES, HERO, MONT = C["dur"], C["scenes"], C["hero"], C["montage"]
SPB = 60.0 / C["bpm"]
OUT = C["wav"]
SR = 44100
N = int(SR * DUR)
T = np.arange(N) / SR
rng = np.random.default_rng(10)          # the volume's number, so runs are identical

mix = np.zeros(N)


def at(t):
    return int(round(t * SR))


def add(sig, t, gain=1.0):
    i = at(t)
    if i >= N:
        return
    j = min(N, i + len(sig))
    mix[i:j] += gain * sig[: j - i]


def env(n, a=0.002, d=0.3):
    t = np.arange(n) / SR
    e = np.minimum(1, t / max(a, 1e-4)) * np.exp(-t / d)
    return e


def lp_fast(x, cut):
    # FFT brick-ish low-pass with a soft knee; fast enough for the whole mix
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    X *= 1 / np.sqrt(1 + (f / cut) ** 6)
    return np.fft.irfft(X, len(x))


def kick():
    n = int(0.45 * SR)
    t = np.arange(n) / SR
    f = 46 + 110 * np.exp(-t / 0.035)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * env(n, 0.001, 0.16)


def tick():
    n = int(0.05 * SR)
    t = np.arange(n) / SR
    return (np.sin(2 * np.pi * 2400 * t) + 0.5 * np.sin(2 * np.pi * 3700 * t)) * env(n, 0.0005, 0.008)


def clap():
    n = int(0.22 * SR)
    out = np.zeros(n)
    for k, off in enumerate([0, 0.011, 0.022]):
        m = int(0.18 * SR)
        b = rng.standard_normal(m) * env(m, 0.0008, 0.035 if k == 2 else 0.008)
        i = int(off * SR)
        out[i:i + m] += b[: n - i]
    return lp_fast(out, 2600)


def hat():
    n = int(0.06 * SR)
    return lp_fast(rng.standard_normal(n) * env(n, 0.0005, 0.012), 6000) * 0.5


def saw(f, n, det=0.0):
    t = np.arange(n) / SR
    s = np.zeros(n)
    for dd in (-det, 0, det):
        ph = (f * (1 + dd)) * t
        s += 2 * (ph - np.floor(ph + 0.5))
    return s / 3


def stab(freqs, dur=0.7, bright=2200):
    n = int(dur * SR)
    s = sum(saw(f, n, 0.006) for f in freqs) / len(freqs)
    return lp_fast(s, bright) * env(n, 0.004, dur / 3.2)


def bass(f, dur):
    n = int(dur * SR)
    t = np.arange(n) / SR
    s = np.sin(2 * np.pi * f * t) + 0.35 * np.sin(2 * np.pi * 2 * f * t) + 0.15 * saw(f, n)
    return s * env(n, 0.004, dur * 0.7)


def boom():
    n = int(1.4 * SR)
    t = np.arange(n) / SR
    f = 34 + 70 * np.exp(-t / 0.08)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * env(n, 0.002, 0.55)


D1, D2, F2, A2, C3, D3, F3, A3, Bb2, D4 = 36.71, 73.42, 87.31, 110.0, 130.81, 146.83, 174.61, 220.0, 116.54, 293.66
S1, S2, S3, S4, S5 = SCENES
STOP = (S5 - 0.12, S5)

# ── drone: D under everything, swelling a little scene by scene ────────────
drone = (np.sin(2 * np.pi * D2 * T) + 0.5 * np.sin(2 * np.pi * A2 * T * 1.001) + 0.3 * np.sin(2 * np.pi * D1 * T))
drone *= 0.10 + 0.05 * (T / DUR)
mix += drone

# ── the clock: a tick on every beat until the ask, every eighth in the take ─
b = 0.0
while b < S5 - 0.13:
    add(tick(), b, 0.20 if b < S4 else 0.26)
    if b >= S4:
        add(tick(), b + SPB / 2, 0.14)
    b += SPB

# ── kick and bass from the crew on; the bass walks D F A C under the montage ─
walk = [D2, D2, F2, F2, A2, A2, C3 / 2 * 2, Bb2]
b, k = S2, 0
while b < DUR - 0.5:
    if not (STOP[0] - 0.01 <= b < STOP[1]):
        add(kick(), b, 0.85 if b >= S3 else 0.7)
        add(bass(walk[k % len(walk)] / 2, SPB * 0.9), b, 0.32)
        if b >= S3:
            add(bass(walk[k % len(walk)] / 2, SPB * 0.4), b + SPB / 2, 0.18)
    b += SPB
    k += 1

# ── claps on 2 and 4 from the job; hats on the off-beats from the take ─────
b, k = S3, 0
while b < DUR - 0.5:
    if k % 2 == 1 and not (STOP[0] - 0.01 <= b < STOP[1]):
        add(clap(), b, 0.42)
    if b >= S4 and not (STOP[0] - 0.01 <= b + SPB / 2 < STOP[1]):
        add(hat(), b + SPB / 2, 0.30)
    b += SPB
    k += 1

# ── a hit on every montage cut: a short muted stab, climbing ───────────────
for k, m in enumerate(MONT):
    add(stab([D3 * (1.0595 ** (k % 3 * 2)), A3], 0.30, 1500), m, 0.20)

# ── the hero hits: a minor chord stab and a boom ───────────────────────────
for h, ch, g in [(S1, [D3, F3, A3], 0.30), (S2, [D3, F3, A3, D4], 0.34),
                 (S3, [Bb2 * 2, D3 * 2 * 0.944, F3], 0.42), (S4, [D3, F3, A3, D4], 0.44),
                 (S5, [D3, F3, A3, D4], 0.52)]:
    add(stab(ch, 0.9, 2400), h, g)
    add(boom(), h, 0.55 if h != S1 else 0.40)

# ── the riser into the ask, then the stop ──────────────────────────────────
r0 = S5 - 1.6
n = at(STOP[0]) - at(r0)
noise = rng.standard_normal(n)
ramp = np.linspace(0, 1, n) ** 2
riser = lp_fast(noise * ramp, 3000) * 0.35 + 0.18 * ramp * np.sin(2 * np.pi * np.cumsum(220 + 660 * ramp) / SR)
mix[at(r0):at(STOP[0])] += riser

# ── the last hit and the ring-out ──────────────────────────────────────────
last = DUR - 1.0
add(stab([D2 * 2, F3, A3, D4], 1.0, 2600), last, 0.55)
add(boom(), last, 0.7)

# silence the stop for real — everything, drone included
fade = int(0.006 * SR)
i0, i1 = at(STOP[0]), at(STOP[1])
mix[i0:i1] = 0
mix[i0 - fade:i0] *= np.linspace(1, 0, fade)

# ── mix bus: roll off the fizz, soft-clip, normalise, fade the very end ────
mix = lp_fast(mix, 5200)
mix = np.tanh(mix * 1.3) / np.tanh(1.3)
mix /= np.max(np.abs(mix)) / 0.89
tail = int(0.25 * SR)
mix[-tail:] *= np.linspace(1, 0, tail)

# ── the assertions ─────────────────────────────────────────────────────────
def rms(a, b):
    seg = mix[at(a):at(b)]
    return 20 * np.log10(np.sqrt(np.mean(seg ** 2)) + 1e-9)


blocks = SCENES + [DUR - 0.3]
lv = [rms(blocks[k] + 0.05, blocks[k + 1] - 0.15) for k in range(len(SCENES))]
assert np.max(np.abs(mix)) < 0.95, "clipping"
assert lv[-1] == max(lv), f"the ask must be the loudest block: {lv}"
assert all(x >= lv[0] - 0.5 for x in lv), f"a block quieter than the open: {lv}"
stop_lv = rms(STOP[0] + 0.01, STOP[1] - 0.005)
assert stop_lv < lv[3] - 30, f"the stop is not silent ({stop_lv:.1f} dB)"
spec = np.abs(np.fft.rfft(mix)) ** 2
f = np.fft.rfftfreq(N, 1 / SR)
low_share = spec[f < 4000].sum() / spec.sum()
assert low_share > 0.85, f"only {low_share:.0%} of the energy under 4kHz — hiss"

os.makedirs(os.path.dirname(OUT), exist_ok=True)
pcm = (mix * 32767).astype(np.int16)
with wave.open(OUT, "w") as w:
    w.setnchannels(1)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(pcm.tobytes())
print(f"{OUT}  {DUR:.1f}s")
print("  blocks dB  " + "  ".join(f"{x:.1f}" for x in lv) + f"   stop {stop_lv:.0f} dB   <4kHz {low_share:.0%}")
