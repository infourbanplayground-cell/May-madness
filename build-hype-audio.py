# -*- coding: utf-8 -*-
"""An 18-second bed for the Blackout hype cut — WARM, not cyberpunk.

The Vol.8 films so far are scored with saw-wave arpeggios, a clicky kick and
open hi-hats: synthwave, which is what "too digital" means. Nothing here is
sourced or sampled either — every sound is still generated from scratch,
because the account is a business one — but the voices are chosen to sound
PLAYED rather than programmed:

  · KICK      sine thump, no click layer, longer decay — a drum, not a tick
  · BODY      a floor-tom-ish layer under the downbeat instead of a sub drop
  · CLAP      three noise bursts a few ms apart, which is what makes a clap
              read as hands rather than as a noise gate
  · SHAKER    soft filtered noise on offbeats, in place of hi-hats
  · PLUCK     stacked sines, fast attack and exponential decay, slightly
              detuned — closer to a muted guitar or kalimba than to a synth
  · SUB       pure sine, no saw, no drive
  · ROOM      a short multi-tap reverb across the whole mix, which is the
              single biggest difference: dry signals sound synthetic

Tempo is 96, not 126. Half the "digital" impression is just being fast.

  python3 build-hype-audio.py
"""
import numpy as np
import os, wave

OUT = ("/tmp/claude-0/-home-user-May-madness/0e44f0ad-a683-5f0d-9de6-9459ae328963"
       "/scratchpad/video/hype.wav")

SR = 44100
DUR = 18.00
N = int(SR * DUR)

# Must match the picture cut.
SCENES = [0.00, 4.20, 8.60, 12.40]
BEATS = [0.10, 4.22, 8.62, 10.50, 12.42, 14.30, 16.10]
HERO = {8.62, 12.42}

BPM = 96.0
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


# ── voices ────────────────────────────────────────────────────────────────
def kick(t0, amp=1.0):
    """No click layer. The click is exactly what makes a kick sound sampled."""
    tt = env_t(0.34)
    freq = 120 * (42 / 120) ** (tt / 0.34)
    body = np.sin(2 * np.pi * np.cumsum(freq) / SR) * np.exp(-tt / 0.10)
    add(low, t0, amp * body)


def floor_tom(t0, amp=0.5, f=96):
    tt = env_t(0.42)
    freq = f * (0.70 ** (tt / 0.42))
    sig = np.sin(2 * np.pi * np.cumsum(freq) / SR) * np.exp(-tt / 0.13)
    add(low, t0, amp * sig)


def clap(t0, amp=0.5):
    """Three bursts, 9ms apart. One burst is a noise gate; three are hands.

    BAND-limited, not just high-passed: hands in a room have very little above
    6kHz, and leaving that in is most of what reads as a drum machine."""
    for k, g in enumerate((0.55, 0.85, 1.0)):
        tt = env_t(0.10)
        n = lowpass(highpass(np.random.randn(len(tt)), 0.45), 0.34)
        add(mid, t0 + k * 0.009, amp * g * n * np.exp(-tt / (0.016 if k < 2 else 0.055)))


def shaker(t0, amp=0.16):
    """A shaker, not a hi-hat. The hat lives above 8kHz; this sits under it."""
    tt = env_t(0.07)
    n = lowpass(highpass(np.random.randn(len(tt)), 0.62), 0.42)
    add(mid, t0, amp * n * (np.exp(-tt / 0.020) * 0.8 + np.exp(-tt / 0.045) * 0.2))


def pluck(t0, f, amp=0.22, dur=0.9):
    """Stacked detuned sines, fast attack, exponential decay. Reads as struck."""
    tt = env_t(dur)
    env = np.exp(-tt / (dur * 0.30))
    atk = np.minimum(1.0, tt / 0.004)
    sig = np.zeros(len(tt))
    for mult, g, cents in ((1.0, 1.0, 0), (2.0, 0.34, 4), (3.0, 0.15, -5), (4.01, 0.07, 7)):
        fr = f * mult * (2 ** (cents / 1200.0))
        sig += g * np.sin(2 * np.pi * fr * tt)
    add(mid, t0, amp * sig * env * atk)


def sub(t0, dur, f, amp=0.42):
    """Pure sine. No saw, no drive — that pairing is the synthwave signature."""
    tt = env_t(dur)
    env = np.minimum(1.0, tt / 0.012) * np.minimum(1.0, (dur - tt) / 0.05)
    add(low, t0, amp * np.sin(2 * np.pi * f * tt) * env)


def swell(t0, dur=1.1, amp=0.20):
    """Air, not a riser: filtered noise that breathes in. No pitch sweep."""
    tt = env_t(dur)
    n = lowpass(np.random.randn(len(tt)), 0.06)
    add(mid, t0, amp * n * (tt / dur) ** 2)


def impact(t0, big=False):
    kick(t0, 1.15 if big else 0.9)
    floor_tom(t0, 0.58 if big else 0.34)
    tt = env_t(0.5 if big else 0.3)
    add(hit, t0, (0.5 if big else 0.3)
        * lowpass(np.random.randn(len(tt)), 0.25) * np.exp(-tt / (0.14 if big else 0.08)))


# ── arrangement ───────────────────────────────────────────────────────────
# A minor. Four bars a scene, and it only grows.
A1, F1, C2, G1 = 55.00, 43.65, 65.41, 49.00
A3, C4, E4, A4 = 220.00, 261.63, 329.63, 440.00

PLAN = [
    dict(root=A1, kick=True,  clap=False, shaker=1, pluck=[A3, E4],            gain=0.72),
    dict(root=F1, kick=True,  clap=True,  shaker=2, pluck=[C4, E4, A4],        gain=0.88),
    dict(root=C2, kick=True,  clap=True,  shaker=2, pluck=[E4, A4, E4, C4],    gain=1.00),
    dict(root=A1, kick=True,  clap=True,  shaker=2, pluck=[A3, C4, E4, A4],    gain=1.12),
]
assert len(PLAN) == len(SCENES)
bounds = [(SCENES[i], SCENES[i + 1] if i + 1 < len(SCENES) else DUR) for i in range(len(SCENES))]

for i, (a, b) in enumerate(bounds):
    p = PLAN[i]
    t = a
    while t < b - 1e-6:
        if p["kick"]:
            kick(t, 0.70 * p["gain"])
        if p["shaker"]:
            for s in range(p["shaker"]):
                st = t + SPB * (s + 0.5) / p["shaker"]
                if st < b:
                    shaker(st, 0.26 * p["gain"])
        t += SPB
    if p["clap"]:
        t = a + SPB
        while t < b - 1e-6:
            clap(t, 0.70 * p["gain"]); t += SPB * 2
    # sub holds the root for the bar rather than pumping on eighths
    t = a
    while t < b - 1e-6:
        L = min(SPB * 2, b - t)
        sub(t, L, p["root"], 0.26 * p["gain"]); t += SPB * 2
    # the plucks carry the tune, one per beat, which is what an arp was doing
    for k, f in enumerate(p["pluck"]):
        pt = a + k * SPB
        while pt < b - 1e-6:
            pluck(pt, f, 0.62 * p["gain"]); pt += SPB * len(p["pluck"])

for s in SCENES[1:]:
    swell(s - 1.0, 1.0, 0.22 if s in HERO else 0.14)

for bt in BEATS:
    impact(bt, big=bt in HERO)

# ring-out so the file resolves
tt = env_t(2.4)
for f, g in ((A3, 0.5), (E4, 0.3), (A4, 0.2)):
    add(mid, DUR - 2.5, 0.20 * g * np.sin(2 * np.pi * f * tt) * np.exp(-tt / 0.85))


# ── room ──────────────────────────────────────────────────────────────────
def room(x, taps=((0.017, .34), (0.029, .26), (0.047, .19), (0.071, .13), (0.103, .08))):
    """The single biggest difference between 'synth' and 'recorded'. A dry mix
    sounds like it was typed in; a few early reflections put it somewhere."""
    y = x.copy()
    for d, g in taps:
        s = int(d * SR)
        y[s:] += g * lowpass(x[:-s], 0.30)
    return y


mix = low * 0.70 + mid * 1.15 + hit * 0.7
mix = mix * 0.80 + room(mix) * 0.30
mix /= max(np.max(np.abs(mix)), 1e-9) / 0.95
# gentle soft-clip instead of hard limiting — no digital edge on the peaks
mix = np.tanh(mix * 1.18) / np.tanh(1.18)

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with wave.open(OUT, "w") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((mix * 32767).astype("<i2").tobytes())


def rms_db(a):
    return 20 * np.log10(max(np.sqrt(np.mean(a ** 2)), 1e-9))


print(f"wrote {os.path.basename(OUT)}  {DUR:.1f}s  {BPM:.0f}bpm  {SR}Hz mono")
print(f"  peak {20*np.log10(np.max(np.abs(mix))):.1f} dBFS   overall {rms_db(mix):.1f} dBFS RMS")
levels = [rms_db(mix[int(a * SR):int(b * SR)]) for a, b in bounds]
for i, (a, b) in enumerate(bounds):
    print(f"  scene {i+1}  {a:5.2f}-{b:5.2f}  {levels[i]:6.1f} dBFS  "
          + "#" * int(max(0, levels[i] + 26) * 1.6))
assert levels == sorted(levels), "the bed should only grow"

# "Not too digital" is a spectral claim, so it is measured against the bed it
# is replacing rather than against a number picked out of the air. A first
# attempt asserted "under 6% above 5kHz" — meaningless, since a linear FFT
# has most of its bins up there and a flat spectrum reads ~77%.
#
# Two things have to be true at once, and the first attempt failed the second:
#   · DARKER than the synthwave bed, by spectral centroid
#   · still AUDIBLE ON A PHONE, which rolls off hard below ~400Hz. A bed that
#     is 96% sub is not warm, it is inaudible — the first rebalance was.
S = np.abs(np.fft.rfft(mix * np.hanning(len(mix)))) ** 2
F = np.fft.rfftfreq(len(mix), 1 / SR)
centroid = (F * S).sum() / S.sum()
phone = 100 * S[(F >= 300) & (F < 5000)].sum() / S.sum()
print(f"  spectral centroid {centroid:.0f} Hz   (the synthwave bed measures 1784 Hz)")
print(f"  energy a phone can reproduce (300Hz-5kHz): {phone:.1f}%")
assert centroid < 1000, f"centroid {centroid:.0f} Hz — still bright"
assert phone > 6.0, f"only {phone:.1f}% in the phone band — this will not be heard"
print("\n  warm bed ok")
