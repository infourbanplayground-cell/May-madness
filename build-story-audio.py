# -*- coding: utf-8 -*-
"""A 15-second bed for the Instagram story cut.

Same voices as the 18-second hype bed — sine kick with no click layer, a floor
tom under the downbeat, three-burst claps, shaker instead of hi-hats, plucked
stacked sines, a room — because "not too digital" was settled once and does not
need re-deciding.

Fifteen seconds has room for a shape the seven did not: it opens, states the
table, drops hardest on the fact and the double, then LIFTS rather than peaks
for the two asks at the end. A call to action under a bed that is still
climbing reads as urgent; under one that has already resolved it reads as an
afterthought, which is exactly what a CTA must not be.

  python3 build-lastround-audio.py
"""
import numpy as np
import os, wave

SP = ("/tmp/claude-0/-home-user-May-madness/"
      "0e44f0ad-a683-5f0d-9de6-9459ae328963/scratchpad")
OUT = os.path.join(SP, "video", "story.wav")

SR = 44100
DUR = 15.00
N = int(SR * DUR)

# Must match the picture cut exactly — one table, two media.
SCENES = [0.00, 2.40, 5.40, 7.60, 9.80, 12.20]
BEATS = [0.00, 1.20, 2.40, 3.60, 4.50, 5.40, 6.50, 7.60,
         8.70, 9.80, 11.00, 12.20, 13.40, 14.30]
HERO = {0.00, 5.40, 7.60, 9.80, 12.20}

BPM = 100.0
SPB = 60.0 / BPM

low = np.zeros(N)
mid = np.zeros(N)
hit = np.zeros(N)


def add(buf, t0, sig):
    i0 = int(t0 * SR)
    if i0 < 0:
        sig = sig[-i0:]; i0 = 0
    i1 = min(i0 + len(sig), N)
    if i1 > i0:
        buf[i0:i1] += sig[:i1 - i0]


def env_t(d):
    return np.linspace(0, d, max(int(SR * d), 1), endpoint=False)


def highpass(x, k=0.75):
    y = np.zeros(len(x))
    for i in range(1, len(x)):
        y[i] = k * (y[i - 1] + x[i] - x[i - 1])
    return y


def lowpass(x, c):
    y = np.zeros(len(x)); prev = 0.0
    for i in range(len(x)):
        prev += c * (x[i] - prev); y[i] = prev
    return y


def kick(t0, amp=1.0):
    tt = env_t(0.34)
    freq = 120 * (42 / 120) ** (tt / 0.34)
    add(low, t0, amp * np.sin(2 * np.pi * np.cumsum(freq) / SR) * np.exp(-tt / 0.10))


def floor_tom(t0, amp=0.5, f=96):
    tt = env_t(0.42)
    freq = f * (0.70 ** (tt / 0.42))
    add(low, t0, amp * np.sin(2 * np.pi * np.cumsum(freq) / SR) * np.exp(-tt / 0.13))


def clap(t0, amp=0.5):
    for k, gn in enumerate((0.55, 0.85, 1.0)):
        tt = env_t(0.10)
        n = lowpass(highpass(np.random.randn(len(tt)), 0.45), 0.34)
        add(mid, t0 + k * 0.009, amp * gn * n * np.exp(-tt / (0.016 if k < 2 else 0.055)))


def shaker(t0, amp=0.16):
    tt = env_t(0.07)
    n = lowpass(highpass(np.random.randn(len(tt)), 0.62), 0.42)
    add(mid, t0, amp * n * (np.exp(-tt / 0.020) * 0.8 + np.exp(-tt / 0.045) * 0.2))


def pluck(t0, f, amp=0.22, dur=0.9):
    tt = env_t(dur)
    env = np.exp(-tt / (dur * 0.30))
    atk = np.minimum(1.0, tt / 0.004)
    sig = np.zeros(len(tt))
    for mult, gn, cents in ((1.0, 1.0, 0), (2.0, 0.34, 4), (3.0, 0.15, -5), (4.01, 0.07, 7)):
        sig += gn * np.sin(2 * np.pi * f * mult * (2 ** (cents / 1200.0)) * tt)
    add(mid, t0, amp * sig * env * atk)


def sub(t0, dur, f, amp=0.42):
    tt = env_t(dur)
    env = np.minimum(1.0, tt / 0.012) * np.minimum(1.0, (dur - tt) / 0.05)
    add(low, t0, amp * np.sin(2 * np.pi * f * tt) * env)


def swell(t0, dur=0.7, amp=0.20):
    tt = env_t(dur)
    n = lowpass(np.random.randn(len(tt)), 0.06)
    add(mid, t0, amp * n * (tt / dur) ** 2)


def impact(t0, big=False):
    kick(t0, 1.18 if big else 0.92)
    floor_tom(t0, 0.62 if big else 0.34)
    tt = env_t(0.55 if big else 0.30)
    add(hit, t0, (0.55 if big else 0.30)
        * lowpass(np.random.randn(len(tt)), 0.25) * np.exp(-tt / (0.16 if big else 0.08)))


# ── arrangement ───────────────────────────────────────────────────────────
# A minor, and it only grows. Four blocks, one per scene.
A1, F1, C2 = 55.00, 43.65, 65.41
A3, C4, E4, A4 = 220.00, 261.63, 329.63, 440.00

PLAN = [
    dict(root=A1, shaker=1, pluck=[A3, E4],         gain=0.70),
    dict(root=F1, shaker=2, pluck=[C4, E4, A4],     gain=0.84),
    dict(root=C2, shaker=2, pluck=[E4, A4, E4],     gain=0.96),
    dict(root=F1, shaker=2, pluck=[C4, A4, E4, C4], gain=1.06),
    dict(root=C2, shaker=2, pluck=[E4, A4, E4, A4], gain=1.14),
    dict(root=A1, shaker=2, pluck=[A3, C4, E4, A4], gain=1.22),
]
assert len(PLAN) == len(SCENES)
bounds = [(SCENES[i], SCENES[i + 1] if i + 1 < len(SCENES) else DUR)
          for i in range(len(SCENES))]

for i, (a, b) in enumerate(bounds):
    p = PLAN[i]
    t = a
    while t < b - 1e-6:
        kick(t, 0.70 * p["gain"])
        for s in range(p["shaker"]):
            st = t + SPB * (s + 0.5) / p["shaker"]
            if st < b:
                shaker(st, 0.26 * p["gain"])
        t += SPB
    t = a + SPB
    while t < b - 1e-6:
        clap(t, 0.70 * p["gain"]); t += SPB * 2
    t = a
    while t < b - 1e-6:
        sub(t, min(SPB * 2, b - t), p["root"], 0.26 * p["gain"]); t += SPB * 2
    for k, f in enumerate(p["pluck"]):
        pt = a + k * SPB
        while pt < b - 1e-6:
            pluck(pt, f, 0.62 * p["gain"]); pt += SPB * len(p["pluck"])

for s in SCENES[1:]:
    swell(s - 0.6, 0.6, 0.22 if s in HERO else 0.14)
for bt in BEATS:
    impact(bt, big=bt in HERO)

# Ring-out under the date, not after it: at seven seconds a tail that resolves
# in silence reads as the file having ended early.
tt = env_t(2.8)
for f, gn in ((A3, 0.5), (E4, 0.3), (A4, 0.2)):
    add(mid, DUR - 2.9, 0.22 * gn * np.sin(2 * np.pi * f * tt) * np.exp(-tt / 1.05))


def room(x, taps=((0.017, .34), (0.029, .26), (0.047, .19), (0.071, .13), (0.103, .08))):
    y = x.copy()
    for d, gn in taps:
        s = int(d * SR)
        y[s:] += gn * lowpass(x[:-s], 0.30)
    return y


mix = low * 0.70 + mid * 1.15 + hit * 0.7
mix = mix * 0.80 + room(mix) * 0.30
mix /= max(np.max(np.abs(mix)), 1e-9) / 0.95
mix = np.tanh(mix * 1.18) / np.tanh(1.18)

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with wave.open(OUT, "w") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((mix * 32767).astype("<i2").tobytes())


def rms_db(a):
    return 20 * np.log10(max(np.sqrt(np.mean(a ** 2)), 1e-9))


print(f"wrote {OUT}  {DUR:.2f}s  {BPM:.0f}bpm  {SR}Hz mono")
print(f"  peak {20*np.log10(np.max(np.abs(mix))):.1f} dBFS   overall {rms_db(mix):.1f} dBFS RMS")
levels = [rms_db(mix[int(a * SR):int(b * SR)]) for a, b in bounds]
for i, (a, b) in enumerate(bounds):
    print(f"  scene {i+1}  {a:4.2f}-{b:4.2f}  {levels[i]:6.1f} dBFS  "
          + "#" * int(max(0, levels[i] + 26) * 1.6))
assert levels == sorted(levels), "the bed should only grow"

# The same two claims the hype bed makes, for the same reasons: darker than the
# synthwave bed it replaced, and still audible on a phone, which rolls off hard
# below ~400Hz. A bed that is 96% sub is not warm, it is inaudible.
S = np.abs(np.fft.rfft(mix * np.hanning(len(mix)))) ** 2
F = np.fft.rfftfreq(len(mix), 1 / SR)
centroid = (F * S).sum() / S.sum()
phone = 100 * S[(F >= 300) & (F < 5000)].sum() / S.sum()
print(f"  spectral centroid {centroid:.0f} Hz   (the synthwave bed measures 1784 Hz)")
print(f"  energy a phone can reproduce (300Hz-5kHz): {phone:.1f}%")
assert centroid < 1000, f"centroid {centroid:.0f} Hz — still bright"
assert phone > 6.0, f"only {phone:.1f}% in the phone band — this will not be heard"
print("\n  bed ok")
