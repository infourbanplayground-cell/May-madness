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
# THE SECOND PASS (owner, 24 Nov 2026: "more hyped, gets intense, to show we
# are reaching the end"). The first bed peaked on 2X and then RELEASED, which
# is the shape of an invitation. This one is a countdown and never lets go:
#   * the tempo ACCELERATES, 104 -> 138 bpm, across the whole film;
#   * a CLOCK ticks on every beat from the first frame — the end is coming;
#   * each cut is approached by a tek ROLL that tightens into it;
#   * before 2X: a RISER, then a STOP (a breath of silence), then the tabl;
#   * the 2X scene and the ask are both full: doubled claps, doum on the
#     eighths, oud in octaves, Hijaz STABS on the downbeats, and it ends on
#     one last hit rather than a fade-out.
# per scene: drums, claps, oud, ney, drone, stabs  (0..1)
ARR = [(0.00, 0.00, 0.60, 0.80, 1.0, 0.0),    # 1 door — clock, drone, ney
       (0.70, 0.00, 0.70, 0.00, 0.8, 0.0),    # 2 contenders — the drums arrive
       (0.80, 0.70, 0.75, 0.00, 0.8, 0.0),    # 3 chart — the claps join
       (0.90, 0.90, 0.85, 0.00, 0.8, 0.4),    # 4 money
       (1.00, 1.00, 1.00, 0.00, 1.0, 1.0),    # 5 2X
       (1.00, 1.00, 1.00, 0.45, 1.0, 1.0)]    # 6 the ask — full to the last hit
if len(SCENES) != len(ARR):
    raise SystemExit(f"{len(SCENES)} scenes on the cut, the arrangement has {len(ARR)}")

BPM0, BPM1 = 104.0, 138.0
bpm = lambda t: BPM0 + (BPM1 - BPM0) * (t / DUR) ** 1.4
grid = []                                         # every sixteenth, accelerating
t = 0.0
while t < DUR:
    grid.append(t); t += 60.0 / bpm(t) / 4
X2, ASK = SCENES[4], SCENES[5]
GAP = (X2 - 0.16, X2)                             # the STOP before the stamp
quiet = lambda t: GAP[0] <= t < GAP[1]


def tick(t0, amp):             # the clock: a short, woody, high click
    tt_ = tt(0.05)
    add(drums, t0, amp * np.sin(2 * np.pi * 1850 * tt_) * np.exp(-tt_ / 0.008))


def stab(t0, amp, d=0.32):     # a Hijaz chord stab — D, F#, A, Eb on top for the bite
    tt_ = tt(d)
    x = np.zeros(len(tt_))
    for f in (hz(0), hz(2), hz(4), hz(8) / 2):
        ph = 2 * np.pi * f * tt_
        x += sum(np.sin(ph * h) / h for h in range(1, 7))      # a bright, reedy saw
    env = np.minimum(tt_ / 0.006, 1) * np.exp(-tt_ / (d * 0.45))
    add(oud, t0, amp * 0.22 * lp(x, 0.35) * env)


def riser(t0, t1, amp):        # noise and a tone climbing into the stop
    tt_ = tt(t1 - t0); u = tt_ / (t1 - t0)
    n = rng.standard_normal(len(tt_))
    a = 0.02 + 0.5 * u ** 2                           # the filter opens as it climbs
    y = np.empty_like(n); s_ = 0.0
    for k_ in range(len(n)):
        s_ += a[k_] * (n[k_] - s_); y[k_] = s_
    f = 220 * 2 ** (u * 2.2)
    tone = np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.35
    add(claps, t0, amp * (y * 1.6 + tone) * u ** 1.6)


DOUM = {0: 1.0, 4: 0.8}
TEK = {3: 0.55, 6: 0.7, 7: 0.35}
CLAP = {3: 1.0, 6: 1.0}
for k, t in enumerate(grid):
    if quiet(t):
        continue
    s = scene_of(t)
    dr, cl = ARR[s][0], ARR[s][1]
    step = k % 8
    swing = 0.014 if step % 2 else 0.0           # the off-beats sit late
    if step % 4 == 0 and t < X2:                 # the clock, until 2X takes over
        tick(t, 0.16 + 0.14 * t / X2)
    if dr:
        if step in DOUM:
            doum(t + swing, 0.9 * dr * DOUM[step])
        if s >= 4 and step in (2, 6):            # the doum on every eighth at the top
            doum(t + swing, 0.55)
        if step in TEK:
            tek(t + swing, 0.55 * dr * TEK[step])
        if s >= 3 and step in (1, 5):
            tek(t + swing, 0.32)
    if cl and step in CLAP:
        clap(t + swing, 0.55 * cl * CLAP[step])
    if s >= 4 and step in (0, 4):                # a second hand-clap line, on the beat
        clap(t, 0.38)
    if ARR[s][5] and step == 0 and (k // 8) % 2 == 0:
        stab(t, ARR[s][5])

# the ROLLS: a run of teks tightening into every cut after the first
for c in SCENES[1:]:
    if c == X2:
        continue
    L_ = 0.55 if DUR > 12 else 0.35
    n_ = 10
    for i in range(n_):
        u = i / n_
        tek(c - L_ * (1 - u) ** 1.3, 0.25 + 0.4 * u)
# into 2X: the longest roll and the riser, then the stop
L_ = 1.2 if DUR > 12 else 0.7
for i in range(18):
    u = i / 18
    tt0 = X2 - 0.16 - L_ * (1 - u) ** 1.4
    tek(tt0, 0.25 + 0.5 * u); doum(tt0, 0.2 + 0.4 * u) if i % 3 == 0 else None
riser(X2 - L_ - 0.16, X2 - 0.16, 0.55)

# the oud: the phrases on the accelerating grid, octaves once it is 2X
k = 0
while k * 16 < len(grid):
    phrase = PHRASE_A if (k // 1) % 2 == 0 else PHRASE_B
    for st, deg, ln in phrase:
        i = k * 16 + st
        if i >= len(grid):
            break
        t = grid[i]
        if quiet(t):
            continue
        s = scene_of(t); g = ARR[s][2]
        six = grid[min(i + 1, len(grid) - 1)] - t or 0.03
        for o in ((1.0, 2.0) if s >= 4 else (1.0,)):
            f = hz(deg) * o
            amp = (0.30 if o == 1 else 0.20) * g
            if ln >= 2 and s >= 1:               # risha: the tremolo
                for r in range(ln * 2):
                    pluck(t + r * six / 2, f, amp * (1 if r == 0 else 0.6), d=0.3, bright=0.6)
            else:
                pluck(t, f, amp * 1.1, d=0.9 if s == 0 else 0.5, bright=0.45)
    k += 1

# the ney: over the door, and a high held line over the ask
def ney_line(t0, t1, degs, amp, base=D3 * 2):
    step = (t1 - t0) / len(degs)
    for i, dg in enumerate(degs):
        breath(t0 + i * step, hz(dg, base), step * 1.08, amp)

ney_line(SCENES[0] + 0.05, SCENES[1], [4, 5, 4, 2] if DUR > 12 else [4, 2], 0.20 * ARR[0][3])
ney_line(ASK + 0.05, DUR - 0.4, [7, 8, 9, 10] if DUR > 12 else [7, 9], 0.16 * ARR[-1][3])

# the drone, D and A, opening up toward the end
t = np.arange(N) / SR
gain = np.array([ARR[scene_of(x)][4] for x in t])
gain = lp(gain, 0.0004) * (1 - np.where((t >= GAP[0]) & (t < GAP[1]), 1, 0))
drone = (np.sin(2 * np.pi * 73.42 * t) + 0.5 * np.sin(2 * np.pi * 110.0 * t)
         + 0.25 * np.sin(2 * np.pi * 146.83 * t + 0.3 * np.sin(2 * np.pi * 0.2 * t)))
low += 0.11 * drone * gain * np.clip(t / 0.6, 0, 1)

for h in sorted(set(HERO)):
    tabl(h, 1.0 if h >= X2 or h == 0 else 0.7)
tabl(DUR - 0.55, 1.0)                              # the last hit
stab(DUR - 0.55, 1.4, d=0.5)

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
LIFT = [0.45, 0.62, 0.74, 0.86, 1.00, 1.00]
tm = np.arange(len(mix)) / SR
env = np.array([LIFT[scene_of(x)] for x in tm])
env = lp(env, 0.0003) * np.where((tm >= GAP[0]) & (tm < GAP[1]), 0.08, 1.0)
mix *= env
fade = np.clip((DUR - tm) / 0.12, 0, 1)            # ends ON the last hit, not a fade
mix *= fade
mix = np.tanh(mix * 1.6) / np.tanh(1.6)          # harder glue: it is meant to push
mix /= np.max(np.abs(mix)) / 0.89

with wave.open(OUT, "w") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((mix * 32767).astype("<i2").tobytes())
print(f"wrote {OUT}  {DUR:.2f}s  {BPM0:.0f}->{BPM1:.0f}bpm  maqam hijaz on D")

# ── the shape, asserted ──────────────────────────────────────────────────────
def rms_db(x):
    return 20 * np.log10(np.sqrt(np.mean(x ** 2)) + 1e-9)

bounds = list(zip(SCENES, SCENES[1:] + [DUR]))
lev = [rms_db(mix[int(a * SR):int(b * SR)]) for a, b in bounds]
print("  scene levels dB: " + "  ".join(f"{v:.1f}" for v in lev))
# a countdown: every scene at least as loud as the one before, the last two
# the loudest, and the stop before 2X really silent
for i in range(1, len(lev)):
    assert lev[i] >= lev[i - 1] - 0.3, f"scene {i + 1} drops {lev[i - 1] - lev[i]:.1f}dB — it must keep building"
assert min(lev[4], lev[5]) >= max(lev[:4]), "2X and the ask must be the loudest"
assert lev[5] - lev[0] >= 6, f"only {lev[5] - lev[0]:.1f}dB from the door to the end — not enough build"
stop = rms_db(mix[int((GAP[0] + .03) * SR):int((GAP[1] - .01) * SR)])
print(f"  the stop before 2X: {stop:.1f} dB")
assert stop < lev[4] - 15, "the stop before 2X is not a stop"
F = np.fft.rfftfreq(len(mix), 1 / SR)
S = np.abs(np.fft.rfft(mix))
band = S[(F > 300) & (F < 3400)].sum() / S.sum()
print(f"  phone band 300-3400Hz: {band * 100:.0f}% of the energy  ·  centroid {np.sum(F * S) / np.sum(S):.0f} Hz")
assert band > 0.35, "too little in the band a phone speaker plays — it will be a thump and nothing else"
