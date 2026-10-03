# -*- coding: utf-8 -*-
"""Score for the Vol.8 announcement — original, synthesized, not licensed.

Nothing here is sourced or sampled; every sound is generated from scratch, which
sidesteps the copyright problem for something going out on a business account.

Same engine as the Surge recap (chords laid end to end with a short crossfade,
driven bass on eighths, a real kit, risers that are air rather than a whistle),
re-arranged for an announcement rather than a story: this one only climbs. The
recap had a champion to arrive at and could afford to fall away afterwards; this
has a sign-up link to arrive at, so the last scene is the loudest.

Two picture events it has to respect:
  - the pool reveal, which gets a drop — half a beat of nothing, so the number
    lands on silence turning back into everything;
  - the final cut to the link, which gets the second one.

  python3 build-announce-audio.py
"""
import numpy as np
import os, wave

OUT = ("/tmp/claude-0/-home-user-May-madness/0e44f0ad-a683-5f0d-9de6-9459ae328963"
       "/scratchpad/video/announce.wav")

SR = 44100
DUR = 28.20
N = int(SR * DUR)

# Must match build-announce-video.py
SCENES = [0.00, 4.00, 8.20, 13.40, 18.20, 21.60, 24.40]
BEATS = [0.14, 1.05, 4.02, 8.22, 13.42, 15.10, 18.22, 21.62, 24.42, 25.70]
HERO = {13.42, 24.42}

BPM = 126.0
SPB = 60.0 / BPM

low = np.zeros(N)     # kick, sub, bass
mid = np.zeros(N)     # drums, pads, arps, air
hit = np.zeros(N)     # impacts, on their own bus so they can be eased


def add(buf, t0, sig):
    i0 = int(t0 * SR)
    if i0 < 0:
        sig = sig[-i0:]
        i0 = 0
    i1 = min(i0 + len(sig), N)
    if i1 > i0:
        buf[i0:i1] += sig[:i1 - i0]


def env_t(dur):
    return np.linspace(0, dur, max(int(SR * dur), 1), endpoint=False)


def lowpass(x, cut):
    y = np.zeros(len(x))
    prev = 0.0
    c = cut if np.ndim(cut) else np.full(len(x), cut)
    for i in range(len(x)):
        prev += c[i] * (x[i] - prev)
        y[i] = prev
    return y


def highpass(x, k=0.75):
    y = np.zeros(len(x))
    for i in range(1, len(x)):
        y[i] = k * (y[i - 1] + x[i] - x[i - 1])
    return y


# ── voices ───────────────────────────────────────────────────────────────
def kick(t0, amp=1.0, f0=175, f1=44, dur=0.17):
    tt = env_t(dur)
    freq = f0 * (f1 / f0) ** (tt / dur)
    body = np.sin(2 * np.pi * np.cumsum(freq) / SR) * np.exp(-tt / (dur * 0.26))
    clk = np.zeros(len(tt))
    k = min(int(0.005 * SR), len(tt))
    clk[:k] = (np.random.rand(k) * 2 - 1) * np.exp(-np.arange(k) / (k * 0.3))
    add(low, t0, amp * (body * 1.15 + 0.32 * clk))


def snare(t0, amp=0.62):
    tt = env_t(0.19)
    n = np.random.randn(len(tt))
    tone = np.sin(2 * np.pi * 190 * tt) * 0.3 + np.sin(2 * np.pi * 278 * tt) * 0.18
    add(mid, t0, amp * (highpass(n, 0.62) * 0.9 + tone) * np.exp(-tt / 0.062))


def hat(t0, amp=0.22, dur=0.04, open_=False):
    d = 0.14 if open_ else dur
    tt = env_t(d)
    n = highpass(np.random.randn(len(tt)), 0.86)
    add(mid, t0, amp * n * np.exp(-tt / (d * (0.5 if open_ else 0.3))))


def tom(t0, f=150, amp=0.5, dur=0.16):
    tt = env_t(dur)
    freq = f * (0.62 ** (tt / dur))
    add(mid, t0, amp * np.sin(2 * np.pi * np.cumsum(freq) / SR) * np.exp(-tt / (dur * 0.33)))


def bass(t0, dur, root, amp=0.5, drive=1.0, step=None):
    """Driven sub-bass on eighths — what actually carries the intensity."""
    step = step or SPB / 2
    t, i = t0, 0
    while t < t0 + dur - 1e-6:
        L = min(step * 0.92, t0 + dur - t)
        if L <= 0.01:
            break
        tt = env_t(L)
        f = root * (1.5 if i % 4 == 2 else 1.0)
        ph = 2 * np.pi * f * tt
        saw = 2 * (ph / (2 * np.pi) % 1.0) - 1.0
        sig = np.tanh((lowpass(saw, 0.10 + 0.05 * drive) + np.sin(ph) * 0.9)
                      * (1.1 + 0.9 * drive))
        env = np.minimum(1.0, tt / 0.004) * np.exp(-tt / (L * 0.55))
        add(low, t, amp * (1.0 if i % 2 == 0 else 0.72) * sig * env)
        t += step
        i += 1


def pad(t0, dur, root, amp=0.30, bright=0.5):
    """A chord that fits inside its own slot — attack and release come OUT of
    dur, never get appended to it, or two roots ring together at every cut."""
    tt = env_t(dur)
    sig = np.zeros(len(tt))
    for mult, g in ((1.0, 1.0), (1.5, 0.52), (2.0, 0.40), (2.5, 0.20), (3.0, 0.18)):
        for det in (-0.19, 0.0, 0.19):
            ph = 2 * np.pi * (root * mult + det) * tt
            sig += g * (2 * (ph / (2 * np.pi) % 1.0) - 1.0) / 3.0
    sig /= 2.5
    y = lowpass(sig, np.linspace(0.14, 0.14 + 0.5 * bright, len(tt)))
    atk = min(int(SR * 0.10), len(tt) // 3)
    rel = min(int(SR * 0.22), len(tt) // 3)
    e = np.ones(len(tt))
    e[:atk] = np.linspace(0, 1, atk)
    e[-rel:] = np.linspace(1, 0, rel)
    add(mid, t0, amp * y * e)


def arp(t0, dur, notes, amp=0.19, step=None):
    step = step or SPB / 2
    tt = env_t(step * 0.9)
    t, i = t0, 0
    while t < t0 + dur - 1e-6:
        f = notes[i % len(notes)]
        sig = (np.sin(2 * np.pi * f * tt) * 0.5
               + np.sin(2 * np.pi * f * 2 * tt) * 0.26
               + np.sin(2 * np.pi * f * 3 * tt) * 0.10)
        add(mid, t, amp * sig * np.exp(-tt / (step * 0.38)))
        t += step
        i += 1


def riser(t0, dur, amp=0.5):
    """Air, not a whistle. A pure sine sweeping upward under noise IS a
    whistle — the ear locks onto the tone and ignores the noise. This is noise
    through a filter that opens, with a sub falling away underneath."""
    tt = env_t(dur)
    noise = np.random.randn(len(tt)) * 0.5
    cut = np.clip(0.010 * (140.0 ** (tt / dur)), 0.0, 0.92)
    env = (tt / dur) ** 2.0
    add(mid, t0, amp * 2.1 * highpass(lowpass(noise, cut), 0.74) * env)
    sub_f = 72.0 * (0.42 ** (tt / dur))
    add(low, t0, amp * 0.55 * np.sin(2 * np.pi * np.cumsum(sub_f) / SR) * env)


def impact(t0, big=False):
    kick(t0, 1.3 if big else 0.9, dur=0.19 if big else 0.16)
    tt = env_t(0.8 if big else 0.5)
    add(low, t0, (1.0 if big else 0.7)
        * np.sin(2 * np.pi * (38 if big else 46) * tt) * np.exp(-tt / (0.30 if big else 0.20)))
    tt2 = env_t(0.6 if big else 0.36)
    add(hit, t0, (1.0 if big else 0.62)
        * highpass(np.random.randn(len(tt2)), 0.55) * np.exp(-tt2 / (0.17 if big else 0.11)))


def fill(t0):
    for i, (dt, f) in enumerate(((0.00, 190), (0.11, 160), (0.20, 134), (0.27, 112))):
        tom(t0 + dt, f, 0.42 + i * 0.07, 0.15)


# ══ ARRANGEMENT ══════════════════════════════════════════════════════════
# A minor, i – VI – III – VII, home on the link. Unlike the recap this only
# climbs: an announcement has nowhere to come down to.
A2, F2, C2, G2 = 110.00, 87.31, 65.41, 98.00
A3, C4, E4, A4, G4 = 220.00, 261.63, 329.63, 440.00, 392.00

PLAN = [
    dict(root=A2, drive=0.0, bass=False, kick=False, snare=False, hats=0, arp=None,              bright=0.30),  # title
    dict(root=F2, drive=0.4, bass=True,  kick=True,  snare=False, hats=2, arp=None,              bright=0.42),  # Vol.7 done
    dict(root=C2, drive=0.6, bass=True,  kick=True,  snare=True,  hats=4, arp=[A3, C4, E4, C4],  bright=0.52),  # schedule
    dict(root=A2, drive=0.8, bass=True,  kick=True,  snare=True,  hats=4, arp=[A3, C4, E4, A4],  bright=0.66),  # the money
    dict(root=G2, drive=0.7, bass=True,  kick=True,  snare=True,  hats=4, arp=None,              bright=0.60),  # what changed
    dict(root=F2, drive=0.9, bass=True,  kick=True,  snare=True,  hats=4, arp=[C4, E4, A4, E4],  bright=0.72),  # entry
    dict(root=A2, drive=1.0, bass=True,  kick=True,  snare=True,  hats=4, arp=[A3, C4, E4, A4, G4, E4], bright=0.88),  # sign up
]
assert len(PLAN) == len(SCENES), "a scene has no part written for it"

bounds = [(SCENES[i], SCENES[i + 1] if i + 1 < len(SCENES) else DUR)
          for i in range(len(SCENES))]

XF = 0.12
for i, (a, b) in enumerate(bounds):
    p = PLAN[i]
    pad(a, (b - a) + XF, p["root"], 0.30 + 0.06 * p["drive"], p["bright"])

# Two drops: the pool reveal and the cut to the link.
DROPS = [(SCENES[3] - SPB * 0.5, SCENES[3]), (SCENES[6] - SPB * 0.5, SCENES[6])]


def muted(t):
    return any(a <= t < b for a, b in DROPS)


for i, (a, b) in enumerate(bounds):
    p = PLAN[i]
    if p["bass"]:
        bass(a, b - a, p["root"], 0.46 + 0.14 * p["drive"], p["drive"])
    t = a
    while t < b - 1e-6:
        if not muted(t):
            if p["kick"]:
                kick(t, 0.95 + 0.15 * p["drive"])
            if p["hats"]:
                for s in range(p["hats"]):
                    ht = t + SPB * s / p["hats"]
                    if ht < b and not muted(ht):
                        hat(ht, 0.16 + 0.10 * p["drive"], open_=(p["hats"] == 4 and s == 2))
        t += SPB
    if p["snare"]:
        t = a + SPB
        while t < b - 1e-6:
            if not muted(t):
                snare(t, 0.52 + 0.16 * p["drive"])
            t += SPB * 2
    if p["arp"]:
        arp(a, b - a, p["arp"], 0.15 + 0.08 * p["drive"], SPB / 2)

for i, s in enumerate(SCENES[1:], start=1):
    big = s in (SCENES[3], SCENES[6])
    riser(s - 1.15, 1.15, 0.70 if big else 0.46)
    if PLAN[i - 1]["kick"]:
        fill(s - 0.32)

for b in BEATS:
    if not muted(b):
        impact(b, big=b in HERO)

# Ring-out, so the file resolves rather than stopping.
tt = env_t(3.0)
add(mid, DUR - 3.2, 0.26 * (np.sin(2 * np.pi * A3 * tt) * 0.5
                            + np.sin(2 * np.pi * E4 * tt) * 0.3
                            + np.sin(2 * np.pi * A4 * tt) * 0.2) * np.exp(-tt / 1.05))

# ── mix ──────────────────────────────────────────────────────────────────
duck = np.ones(N)
for b in BEATS:
    i0 = int(b * SR)
    i1 = min(i0 + int(0.26 * SR), N)
    if i1 > i0:
        duck[i0:i1] = np.minimum(duck[i0:i1], 1 - 0.22 * (1 - np.linspace(0, 1, i1 - i0)))

mix = low * 1.0 + mid * duck * 1.0 + hit * 0.60

gate = np.ones(N)
for (g0s, g1s) in DROPS:
    g0, g1 = int(g0s * SR), int(g1s * SR)
    r = int(0.05 * SR)
    gate[g0:g1] = 0.10
    gate[max(0, g0 - r):g0] = np.linspace(1, 0.10, min(r, g0))
    gate[g1:g1 + r] = np.linspace(0.10, 1, r)
mix *= gate

fi, fo = int(SR * 0.05), int(SR * 0.6)
mix[:fi] *= np.linspace(0, 1, fi)
mix[-fo:] *= np.linspace(1, 0, fo)

mix = np.tanh(mix * 0.92) / np.tanh(0.92)
mix = mix / np.max(np.abs(mix)) * 0.96

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
print("\n  scene            level     drive")
levels = []
for i, (a, b) in enumerate(bounds):
    seg = mix[int(a * SR):int(b * SR)]
    levels.append(rms_db(seg))
    print(f"  {i+1:2d} {a:5.2f}-{b:5.2f}  {levels[-1]:6.1f}  {PLAN[i]['drive']:.1f} "
          + "#" * int(max(0, (levels[-1] + 26)) * 1.6))
for a, b in DROPS:
    print(f"  drop  {a:.2f}-{b:.2f}s  {rms_db(mix[int(a*SR):int(b*SR)]):.1f} dBFS")

# It only climbs. The last scene is the loudest, or the call to action arrives
# quieter than the thing before it.
assert levels[-1] >= max(levels) - 0.4, \
    f"the sign-up scene is not the peak ({levels[-1]:.1f} vs {max(levels):.1f} dBFS)"
assert levels[0] == min(levels), "the title should be the quietest moment"
print("\n  climbs to the sign-up  ok")
