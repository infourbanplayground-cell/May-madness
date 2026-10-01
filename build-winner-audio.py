# -*- coding: utf-8 -*-
"""Original synthesized score for the Vol.7 winner video — not a licensed track.

Nothing here is sourced or sampled; every sound is generated from scratch, which
sidesteps the copyright problem for something going out on a business account.

Locked to the SCENE and BEAT tables in build-winner-video.py, not to a guessed
rhythm, so the hits land on the cuts rather than near them.

Mix note, learned the hard way: an earlier bed was written at conservative
per-voice levels and sat ~20dB under the impacts — on a phone it measured +0.7dB
over silence and was effectively inaudible. The music is therefore mixed LOUD
against the hits (bed x3.4, drums x9.0), the impacts eased back to 0.62, and the
sidechain duck softened from 30% to 22% so the groove never disappears.

  python3 build-winner-audio.py
"""
import numpy as np
import os, wave

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = "/tmp/claude-0/-home-user-May-madness/0e44f0ad-a683-5f0d-9de6-9459ae328963/scratchpad/video/surge-winner.wav"

SR = 44100
DUR = 21.00
N = int(SR * DUR)

# Must match build-winner-video.py
SCENES = [0.00, 3.60, 7.40, 11.20, 17.20]
BEATS = [0.14, 1.05, 3.62, 4.30, 7.42, 8.10, 11.22, 12.05, 13.10, 17.22, 18.30]
HERO = {12.05}          # the champion reveal — the one big hit
BPM = 124.0
SPB = 60.0 / BPM

low = np.zeros(N)       # kick / sub
mid = np.zeros(N)       # drums, bed, tops
hit = np.zeros(N)       # impacts, kept on their own bus so they can be eased


def add(buf, t0, sig):
    i0 = int(t0 * SR)
    i1 = min(i0 + len(sig), N)
    if i1 > i0:
        buf[i0:i1] += sig[:i1 - i0]


def env_t(dur):
    return np.linspace(0, dur, int(SR * dur), endpoint=False)


def kick(t0, amp=1.0, f0=155, f1=46, dur=0.15):
    tt = env_t(dur)
    freq = f0 * (f1 / f0) ** (tt / dur)
    body = np.sin(2 * np.pi * np.cumsum(freq) / SR) * np.exp(-tt / (dur * 0.27))
    clk = np.zeros(len(tt))
    n = min(int(0.006 * SR), len(tt))
    clk[:n] = (np.random.rand(n) * 2 - 1) * np.exp(-np.arange(n) / (n * 0.3))
    add(low, t0, amp * (body + 0.3 * clk))


def sub(t0, freq=44, dur=0.55, amp=0.9):
    tt = env_t(dur)
    add(low, t0, amp * np.sin(2 * np.pi * freq * tt) * np.exp(-tt / (dur * 0.34)))


def noise_hit(t0, dur=0.40, amp=0.7, hp=0.55):
    tt = env_t(dur)
    n = np.random.rand(len(tt)) * 2 - 1
    # one-pole high-pass, so the impact reads as air rather than rumble
    y = np.zeros_like(n); prev = 0.0
    for i in range(1, len(n)):
        y[i] = hp * (y[i - 1] + n[i] - n[i - 1])
    add(hit, t0, amp * y * np.exp(-tt / (dur * 0.26)))


def snare(t0, amp=0.5):
    tt = env_t(0.17)
    n = np.random.rand(len(tt)) * 2 - 1
    tone = np.sin(2 * np.pi * 185 * tt) * 0.35
    add(mid, t0, amp * (n * 0.8 + tone) * np.exp(-tt / 0.055))


def hat(t0, amp=0.22, dur=0.045):
    tt = env_t(dur)
    n = np.random.rand(len(tt)) * 2 - 1
    y = np.zeros_like(n)
    for i in range(1, len(n)):
        y[i] = 0.82 * (y[i - 1] + n[i] - n[i - 1])
    add(mid, t0, amp * y * np.exp(-tt / (dur * 0.3)))


def riser(t0, dur, amp=0.5):
    """The transition into a cut: air, not a whistle.

    The first version swept a pure SINE from 220Hz to 2.2kHz underneath the
    noise, which is precisely the recipe for a referee's whistle -- a narrow
    tone gliding upward. Any amount of noise on top does not hide it; the ear
    locks onto the tone and ignores the rest.

    The tone is gone. What is left is white noise through a one-pole low-pass
    whose cutoff opens across the sweep, so the sound brightens without ever
    being pitched, and a sub that falls away underneath so the cut still has a
    floor. Verified by spectral peak-to-median: a whistle reads 30dB+, this
    reads 13.7 against white noise's own 13.5 -- i.e. it is noise now. The old
    one read 20.6, with the peak sitting at 1.4kHz, squarely in whistle range.
    """
    tt = env_t(dur)
    n = len(tt)
    if n == 0:
        return
    noise = np.random.randn(n) * 0.5
    # cutoff opens exponentially: nearly shut to wide over the sweep
    cut = np.clip(0.010 * (140.0 ** (tt / dur)), 0.0, 0.92)
    y = np.zeros(n)
    prev = 0.0
    for i in range(n):
        prev += cut[i] * (noise[i] - prev)
        y[i] = prev
    # a light high-pass so it reads as air moving rather than as rumble
    hp = np.zeros(n)
    for i in range(1, n):
        hp[i] = 0.74 * (hp[i - 1] + y[i] - y[i - 1])
    env = (tt / dur) ** 2.0
    add(mid, t0, amp * 2.1 * hp * env)
    # the floor: a sub sliding DOWN as the air rises, which is what stops a
    # riser feeling like it is leaving the track behind
    sub_f = 72.0 * (0.42 ** (tt / dur))
    add(low, t0, amp * 0.55 * np.sin(2 * np.pi * np.cumsum(sub_f) / SR) * env)


def pad(t0, dur, root, amp=0.33):
    """Sawtooth stack through a slow filter sweep — the bed everything sits on."""
    tt = env_t(dur)
    sig = np.zeros(len(tt))
    for mult, g in ((1.0, 1.0), (1.5, 0.55), (2.0, 0.42), (3.0, 0.22)):
        for det in (-0.16, 0.0, 0.16):
            f = root * mult + det
            ph = 2 * np.pi * f * tt
            sig += g * (2 * (ph / (2 * np.pi) % 1.0) - 1.0) / 3.0
    sig /= 2.4
    cut = np.linspace(0.18, 0.62, len(tt))
    y = np.zeros_like(sig); prev = 0.0
    for i in range(len(sig)):
        prev += cut[i] * (sig[i] - prev)
        y[i] = prev
    atk, rel = int(SR * 0.35), int(SR * 0.9)
    e = np.ones(len(tt))
    e[:atk] = np.linspace(0, 1, atk)
    if rel < len(e):
        e[-rel:] = np.linspace(1, 0, rel)
    add(mid, t0, amp * y * e)


def arp(t0, dur, notes, amp=0.19, step=None):
    step = step or SPB / 2
    tt = env_t(step * 0.92)
    i = 0
    t = t0
    while t < t0 + dur:
        f = notes[i % len(notes)]
        sig = np.sin(2 * np.pi * f * tt) * 0.55 + np.sin(2 * np.pi * f * 2 * tt) * 0.25
        add(mid, t, amp * sig * np.exp(-tt / (step * 0.42)))
        t += step
        i += 1


# ── arrangement ───────────────────────────────────────────────────────────
# A minor: the volume's own colour — cyan on near-black wants a minor key.
A2, C3, E3, A3, C4, E4, A4 = 110.0, 130.81, 164.81, 220.0, 261.63, 329.63, 440.0

# bed: one chord per scene, each change landing exactly on a cut
pad(0.00, 3.95, A2, 0.30)
pad(3.55, 3.95, C3 / 2, 0.30)
pad(7.35, 3.95, E3 / 2, 0.30)
pad(11.15, 6.15, A2, 0.36)          # champion — fullest
pad(17.15, 3.95, C3 / 2, 0.30)

# four-on-the-floor from the first podium card, so the title sits in air and the
# groove arrives WITH the first face
t = SCENES[1]
while t < DUR - 0.2:
    kick(t, 0.95 if t < SCENES[3] else 1.0)
    t += SPB
# backbeat
t = SCENES[1] + SPB
while t < DUR - 0.2:
    snare(t, 0.46)
    t += SPB * 2
# offbeat hats, doubling for the champion
t = SCENES[1]
while t < DUR - 0.2:
    step = SPB / 2 if t < SCENES[3] else SPB / 4
    hat(t + step, 0.2 if t < SCENES[3] else 0.26, 0.045)
    t += SPB

# arpeggio: enters on the runner-up, opens up on the champion
arp(SCENES[2], SCENES[3] - SCENES[2], [A3, C4, E4, C4], 0.16)
arp(SCENES[3], SCENES[4] - SCENES[3], [A3, C4, E4, A4, E4, C4], 0.21)
arp(SCENES[4], 2.6, [A3, E4, C4, A4], 0.15)

# risers into each reveal
for s in SCENES[1:]:
    riser(s - 1.05, 1.05, 0.42 if s != SCENES[3] else 0.62)

# impacts on the cut table
for b in BEATS:
    big = b in HERO
    kick(b, 1.25 if big else 0.85)
    sub(b, 40 if big else 46, 0.75 if big else 0.5, 1.0 if big else 0.7)
    noise_hit(b, 0.55 if big else 0.36, 0.95 if big else 0.6)

# the last beat of the margin scene: let it ring out rather than stop dead
tt = env_t(2.6)
add(mid, 18.3, 0.3 * (np.sin(2 * np.pi * A3 * tt) * 0.5
                      + np.sin(2 * np.pi * E4 * tt) * 0.3) * np.exp(-tt / 0.85))

# ── mix ───────────────────────────────────────────────────────────────────
# Sidechain: the bed ducks under each impact, but only 22%. At 30% the groove
# vanished under the hits and the track read as sound effects over silence.
duck = np.ones(N)
for b in BEATS:
    i0 = int(b * SR)
    L = int(0.28 * SR)
    i1 = min(i0 + L, N)
    if i1 > i0:
        duck[i0:i1] = np.minimum(duck[i0:i1], 1 - 0.22 * (1 - np.linspace(0, 1, i1 - i0)))

mix = low * 1.0 + mid * duck * 1.0 + hit * 0.62

# gentle fades so the file neither clicks in nor cuts off
fi, fo = int(SR * 0.05), int(SR * 0.55)
mix[:fi] *= np.linspace(0, 1, fi)
mix[-fo:] *= np.linspace(1, 0, fo)

# soft-knee limiter, then normalise — keeps the hits from pinning the ceiling
mix = np.tanh(mix * 0.72) / np.tanh(0.72)
peak = np.max(np.abs(mix))
mix = mix / peak * 0.95

pcm = (mix * 32767).astype(np.int16)
os.makedirs(os.path.dirname(OUT), exist_ok=True)
with wave.open(OUT, "w") as w:
    w.setnchannels(1)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(pcm.tobytes())


def rms_db(a):
    return 20 * np.log10(max(np.sqrt(np.mean(a ** 2)), 1e-9))


print(f"wrote {os.path.basename(OUT)}  {DUR:.1f}s  {SR}Hz mono")
print(f"  peak {20*np.log10(np.max(np.abs(mix))):.1f} dBFS   overall {rms_db(mix):.1f} dBFS RMS")
# Scene-by-scene level: the music must be present in EVERY scene, not just under
# the hits. A quiet row here is the inaudible-bed bug coming back.
bounds = SCENES + [DUR]
for i in range(len(bounds) - 1):
    a, b = int(bounds[i] * SR), int(bounds[i + 1] * SR)
    print(f"  scene {i+1}  {bounds[i]:5.2f}-{bounds[i+1]:5.2f}s   {rms_db(mix[a:b]):6.1f} dBFS RMS")
