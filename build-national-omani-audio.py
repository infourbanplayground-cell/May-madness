# -*- coding: utf-8 -*-
"""An Omani bed for the National FINAL ROUND film (owner, 24 Nov 2026:
"better music or Omani music").

Not a sample and not a recording of anybody's song — every voice is
synthesised here, so there is nothing to license and nothing to take down:

  * FRAME DRUMS in a Khaleeji 2/4 — a low DOUM and a dry TEK on a sixteenth
    grid, the lilt that every wedding band in the Gulf plays, a little
    late on the off-beats the way people actually play it.
  * GROUP HANDCLAPS on the syncopations, several hands a few ms apart, which
    is what makes a clap sound like a room of people rather than a drum machine.
  * An OUD (Karplus-Strong plucks, a body resonance, risha tremolo on the
    long notes) playing in MAQAM HIJAZ on D — D Eb F# G A Bb C — the
    augmented second between Eb and F# is the sound people hear as "Arabic".
  * A NEY-like breathy lead over the opening and the ask.
  * A D/A drone and a big low TABL on every hero hit.

SHAPE, read from the picture's own cut table (CUT=<json>, written by the
film builder): the door opens on drone and ney, the drums arrive with the
contenders, the claps join for the chart, the money is fuller, the 2X stamp
is the PEAK, and the ask opens out — oud and ney over lighter drums, louder
than the opening, under 3dB below the peak. Asserted at the foot.

NUMPY IS ON python3.13 in this container.

  CUT=$SP/national-lastround.cut.json python3.13 build-national-omani-audio.py
"""
import json
import os
import wave

import numpy as np

SP = ("/tmp/claude-0/-home-user-May-madness/"
      "0e44f0ad-a683-5f0d-9de6-9459ae328963/scratchpad")
C = json.load(open(os.environ.get("CUT") or os.path.join(SP, "national-lastround.cut.json")))
DUR, SCENES, HERO, OUT = C["dur"], C["scenes"], C["hero"], C["wav"]
os.makedirs(os.path.dirname(OUT), exist_ok=True)

SR = 44100
N = int(SR * DUR) + SR          # a second of tail, trimmed at the end
BPM = 112.0
SIX = 60.0 / BPM / 4            # a sixteenth
rng = np.random.default_rng(56)

drums = np.zeros(N); claps = np.zeros(N); oud = np.zeros(N); ney = np.zeros(N); low = np.zeros(N)


def add(buf, t0, x):
    i = int(t0 * SR)
    if i >= N or i + len(x) <= 0:
        return
    if i < 0:
        x, i = x[-i:], 0
    j = min(N, i + len(x))
    buf[i:j] += x[:j - i]


def tt(d):
    return np.arange(int(SR * d)) / SR


def lp(x, a):                  # one-pole low-pass, a in (0,1): smaller is darker
    y = np.empty_like(x); s = 0.0
    for k in range(len(x)):
        s += a * (x[k] - s); y[k] = s
    return y


def scene_of(t):
    i = 0
    for k, s in enumerate(SCENES):
        if t >= s:
            i = k
    return i


# ── voices ───────────────────────────────────────────────────────────────────
def doum(t0, amp):
    t = tt(0.45)
    f = 62 + 55 * np.exp(-t / 0.03)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.16)
    skin = lp(rng.standard_normal(len(t)), 0.08) * np.exp(-t / 0.02) * 0.5
    add(drums, t0, amp * (body + skin))


def tek(t0, amp):
    t = tt(0.12)
    n = rng.standard_normal(len(t))
    hp = lp(n - lp(n, 0.25), 0.35)             # dry, papery rim
    ring = np.sin(2 * np.pi * 410 * t) * 0.35
    add(drums, t0, amp * (hp * 0.6 + ring) * np.exp(-t / 0.022))


def clap(t0, amp, hands=6):
    for h in range(hands):
        dt = rng.uniform(0, 0.024)
        t = tt(0.16)
        n = rng.standard_normal(len(t))
        bp = lp(lp(n - lp(n, 0.12), 0.3), 0.3)  # 1-2.5k body of a palm
        env = np.exp(-t / rng.uniform(0.03, 0.05))
        add(claps, t0 + dt, amp / np.sqrt(hands) * bp * env * rng.uniform(.7, 1.1))


def tabl(t0, amp):             # the big drum on a hero hit
    t = tt(1.4)
    f = 48 + 70 * np.exp(-t / 0.05)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.45)
    thud = lp(rng.standard_normal(len(t)), 0.05) * np.exp(-t / 0.05)
    add(low, t0, amp * (body + 0.6 * thud))


def pluck(t0, freq, amp, d=0.9, bright=0.5):
    """Karplus-Strong string with a short body resonance — an oud, near enough."""
    n = int(SR * d); L = max(2, int(SR / freq))
    buf = lp(rng.uniform(-1, 1, L), bright)
    out = np.empty(n)
    for k in range(n):
        v = buf[k % L]; out[k] = v
        buf[k % L] = 0.5 * (v + buf[(k + 1) % L]) * 0.996
    t = tt(d)[:n]
    body = np.sin(2 * np.pi * 180 * t) * np.exp(-t / 0.04) * 0.25 * amp
    add(oud, t0, amp * out + body)


def breath(t0, freq, d, amp):
    """A ney: a soft fundamental, a weak octave, breath noise, slow vibrato."""
    t = tt(d)
    vib = 1 + 0.006 * np.sin(2 * np.pi * 5.2 * t) * np.clip(t / 0.4, 0, 1)
    ph = 2 * np.pi * np.cumsum(freq * vib) / SR
    tone = np.sin(ph) + 0.18 * np.sin(2 * ph) + 0.06 * np.sin(3 * ph)
    air = lp(rng.standard_normal(len(t)), 0.3) * 0.22
    env = np.clip(t / 0.18, 0, 1) * np.clip((d - t) / 0.25, 0, 1)
    add(ney, t0, amp * (tone + air) * env)


# ── maqam Hijaz on D ─────────────────────────────────────────────────────────
D3 = 146.83
HIJAZ = [0, 1, 4, 5, 7, 8, 10, 12, 13, 16, 17, 19]   # D Eb F# G A Bb C D Eb F# G A
hz = lambda deg, base=D3: base * 2 ** (HIJAZ[deg] / 12)

# an oud phrase, two bars of 2/4 in sixteenths: (step, degree, length in sixteenths)
PHRASE_A = [(0, 4, 2), (2, 5, 1), (3, 4, 1), (4, 3, 2), (6, 2, 1), (7, 1, 1),
            (8, 2, 2), (10, 3, 2), (12, 1, 2), (14, 0, 2)]
PHRASE_B = [(0, 7, 2), (2, 6, 1), (3, 5, 1), (4, 4, 3), (7, 5, 1),
            (8, 4, 2), (10, 2, 2), (12, 1, 1), (13, 2, 1), (14, 0, 2)]

# ── arrangement ──────────────────────────────────────────────────────────────
# per scene: drums, claps, oud, ney, drone  (0..1)
ARR = [(0.00, 0.00, 0.55, 0.90, 1.0),    # 1 door
       (0.75, 0.00, 0.70, 0.00, 0.8),    # 2 contenders
       (0.80, 0.70, 0.75, 0.00, 0.7),    # 3 chart
       (0.90, 0.85, 0.85, 0.00, 0.7),    # 4 money
       (1.00, 1.00, 1.00, 0.00, 0.9),    # 5 2X — the peak
       (0.80, 0.75, 0.95, 0.70, 1.0)]    # 6 the ask opens out
if len(SCENES) != len(ARR):
    raise SystemExit(f"{len(SCENES)} scenes on the cut, the arrangement has {len(ARR)}")

DOUM = {0: 1.0, 4: 0.8}
TEK = {3: 0.55, 6: 0.7, 7: 0.35}
CLAP = {3: 1.0, 6: 1.0}

nsix = int(DUR / SIX) + 1
for k in range(nsix):
    t = k * SIX
    if t >= DUR:
        break
    s = scene_of(t)
    dr, cl = ARR[s][0], ARR[s][1]
    step = k % 8
    swing = 0.018 if step % 2 else 0.0          # the off-beats sit late
    if dr:
        if step in DOUM:
            doum(t + swing, 0.9 * dr * DOUM[step])
        if step in TEK:
            tek(t + swing, 0.55 * dr * TEK[step])
        if s == 4 and step in (1, 5):           # the 2X scene doubles up the tek
            tek(t + swing, 0.30)
    if cl and step in CLAP:
        clap(t + swing, 0.55 * cl * CLAP[step])

# the oud: phrase A and B alternating, tremolo on anything two sixteenths or longer
bar2 = 16 * SIX
k = 0
while k * bar2 < DUR:
    t0 = k * bar2
    s = scene_of(t0)
    g = ARR[s][2]
    phrase = PHRASE_A if k % 2 == 0 else PHRASE_B
    oct_ = 2.0 if s in (4,) else 1.0
    for st, deg, ln in phrase:
        t = t0 + st * SIX
        if t >= DUR:
            break
        f = hz(deg) * oct_
        if ln >= 2 and s >= 1:                   # risha: the tremolo
            for r in range(ln * 2):
                pluck(t + r * SIX / 2, f, 0.30 * g * (1 if r == 0 else 0.6), d=0.35, bright=0.6)
        else:
            pluck(t, f, 0.34 * g, d=0.9 if s == 0 else 0.6, bright=0.45)
    k += 1

# the ney over the opening and over the ask: long notes down the maqam
def ney_line(t0, t1, degs, amp):
    step = (t1 - t0) / len(degs)
    for i, dg in enumerate(degs):
        breath(t0 + i * step, hz(dg, D3 * 2), step * 1.08, amp)

ney_line(SCENES[0] + 0.05, SCENES[1], [4, 5, 4, 2] if DUR > 12 else [4, 2], 0.20 * ARR[0][3])
ney_line(SCENES[-1] + 0.1, DUR - 0.1, [7, 5, 4, 3, 2, 1, 0][:5 if DUR > 12 else 3], 0.20 * ARR[-1][3])

# the drone, D and A, breathing with the scenes
t = np.arange(N) / SR
gain = np.array([ARR[scene_of(x)][4] for x in np.arange(0, N) / SR])
gain = lp(gain, 0.0004)
drone = (np.sin(2 * np.pi * 73.42 * t) + 0.5 * np.sin(2 * np.pi * 110.0 * t)
         + 0.25 * np.sin(2 * np.pi * 146.83 * t + 0.3 * np.sin(2 * np.pi * 0.2 * t)))
low += 0.11 * drone * gain * np.clip(t / 0.6, 0, 1)

for h in sorted(set(HERO)):
    tabl(h, 0.85 if scene_of(h) == 4 or h == 0 else 0.6)

# ── room and mix ─────────────────────────────────────────────────────────────
def room(x, secs=1.3, wet=0.22):
    ir_t = np.arange(int(SR * secs)) / SR
    ir = rng.standard_normal(len(ir_t)) * np.exp(-ir_t / 0.32)
    ir = lp(ir, 0.35); ir /= np.sqrt(np.sum(ir ** 2))
    L = 1 << int(np.ceil(np.log2(len(x) + len(ir))))
    y = np.fft.irfft(np.fft.rfft(x, L) * np.fft.rfft(ir, L), L)[:len(x)]
    return x + wet * y

mix = (room(drums, wet=0.16) * 0.95 + room(claps, wet=0.30) * 0.9
       + room(oud, wet=0.28) * 1.0 + room(ney, wet=0.40) * 1.0 + low * 1.0)
mix = mix[:int(SR * DUR)]
mix = lp(lp(mix, 0.5), 0.5)                      # roll the hiss off, ~5kHz
# the build, as a master envelope across the scenes, eased so it swells
# rather than steps (the cuts already carry the hits)
LIFT = [0.50, 0.70, 0.80, 0.90, 1.00, 0.93]
env = np.array([LIFT[scene_of(x)] for x in np.arange(len(mix)) / SR])
mix *= lp(env, 0.0003)
fade = np.clip((DUR - np.arange(len(mix)) / SR) / 0.5, 0, 1)
mix *= fade
mix = np.tanh(mix * 1.1) / np.tanh(1.1)          # a gentle glue
mix /= np.max(np.abs(mix)) / 0.89

with wave.open(OUT, "w") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((mix * 32767).astype("<i2").tobytes())
print(f"wrote {OUT}  {DUR:.2f}s  {BPM:.0f}bpm  maqam hijaz on D")

# ── the shape, asserted ──────────────────────────────────────────────────────
def rms_db(x):
    return 20 * np.log10(np.sqrt(np.mean(x ** 2)) + 1e-9)

bounds = list(zip(SCENES, SCENES[1:] + [DUR]))
lev = [rms_db(mix[int(a * SR):int(b * SR)]) for a, b in bounds]
print("  scene levels dB: " + "  ".join(f"{v:.1f}" for v in lev))
pk = int(np.argmax(lev))
assert pk == 4, f"the peak should be the 2X scene, is scene {pk + 1}"
assert lev[0] < lev[1] < lev[3], "the opening must build into the money"
assert lev[4] - lev[5] < 3.0, f"the ask drops {lev[4] - lev[5]:.1f}dB — a release, not a collapse"
assert lev[5] > lev[0], "the ask must be fuller than the door"
F = np.fft.rfftfreq(len(mix), 1 / SR)
S = np.abs(np.fft.rfft(mix))
band = S[(F > 300) & (F < 3400)].sum() / S.sum()
print(f"  phone band 300-3400Hz: {band * 100:.0f}% of the energy  ·  centroid {np.sum(F * S) / np.sum(S):.0f} Hz")
assert band > 0.35, "too little in the band a phone speaker plays — it will be a thump and nothing else"
