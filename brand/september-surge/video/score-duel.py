"""
Original score for the September Surge hype cut.

Everything here is synthesised from scratch — no samples, no library music — so
the track is ours and carries no licence or copyright-claim risk on Instagram.

A full bed -- drums, bass, arpeggio and chords on a Dm-Bb-F-C loop -- sits
under a layer of trailer impacts. The impacts are written against the cut's own beat map (BEATS in reel.html), so the hits
land on the frames that already punch. The contender countdown reveals at 0.24s
intervals, which is an eighth note at 125 BPM, so the whole score sits at 125
and the picture edit and the music share a grid rather than merely coinciding.
"""
import numpy as np, struct, math

SR   = 48000
DUR  = 23.20
BPM  = 125.0
BEAT = 60.0 / BPM          # 0.480 s
N    = int(SR * DUR)
T    = np.arange(N) / SR

rng = np.random.default_rng(7)

# ── the cut's beat map, lifted from reel.html ───────────────────────────────
BEATS = [
    (0.34,.34), (0.96,.74), (1.44,.94), (2.40,.22),
    (3.84,.50), (4.32,.62), (4.80,.62), (5.76,.88),
    (7.68,.66),
    (9.60,.50), (10.08,.26), (10.56,.26), (11.04,.26), (11.52,.26), (12.96,.34),
    (14.40,.55), (15.84,.95), (16.80,.30), (16.94,.30), (17.08,.30),
    (18.24,.48), (18.72,.30), (19.20,.30), (19.68,.30),
    (20.64,.60), (21.12,.92), (22.40,.40),
]

# ── helpers ────────────────────────────────────────────────────────────────
def buf():
    return np.zeros(N)

def place(dst, t0, sig, gain=1.0):
    i = int(t0 * SR)
    if i >= N: return
    if i < 0:
        sig = sig[-i:]; i = 0
    m = min(len(sig), N - i)
    dst[i:i+m] += sig[:m] * gain

def dec(n, tau):
    return np.exp(-np.arange(n) / (SR * tau))

def onepole_lp(x, cut):
    """cut may be a scalar or a per-sample array (a filter sweep)."""
    a = 1.0 - np.exp(-2.0 * np.pi * np.asarray(cut, dtype=float) / SR)
    a = np.broadcast_to(a, x.shape).copy()
    y = np.empty_like(x); z = 0.0
    for i in range(len(x)):
        z += a[i] * (x[i] - z); y[i] = z
    return y

def onepole_hp(x, cut):
    return x - onepole_lp(x, cut)

def sat(x, k=1.6):
    return np.tanh(x * k) / np.tanh(k)

# ── voices ─────────────────────────────────────────────────────────────────
def kick(f0=145, f1=44, d=0.42, click=0.5):
    n = int(SR * d); e = dec(n, d / 4.2)
    pitch = f1 + (f0 - f1) * np.exp(-np.arange(n) / (SR * 0.028))
    body = np.sin(2*np.pi*np.cumsum(pitch)/SR) * e
    tick = rng.normal(0, 1, n) * dec(n, 0.004) * click
    return sat(body * 0.95 + tick * 0.35, 2.0)

def impact(a=1.0, d=1.5):
    """Trailer hit: sub drop + a bright noise crack that decays into a tail."""
    n = int(SR * d); e = dec(n, d / 5.0)
    pitch = 38 + 120 * np.exp(-np.arange(n) / (SR * 0.05))
    sub = np.sin(2*np.pi*np.cumsum(pitch)/SR) * e
    crack = onepole_hp(rng.normal(0, 1, n) * dec(n, 0.05), 1400)
    tail = onepole_lp(rng.normal(0, 1, n) * dec(n, d / 3.0), 700)
    return sat(sub * 1.0 + crack * 0.34 + tail * 0.16, 1.8) * a

def riser(d=1.2, f_a=200, f_b=5200):
    """Noise sweep that tightens into the hit it precedes."""
    n = int(SR * d)
    x = np.linspace(0, 1, n) ** 2.2
    nz = rng.normal(0, 1, n)
    swept = onepole_hp(onepole_lp(nz, f_a + (f_b - f_a) * x), 300 + 2400 * x)
    return swept * (x * 0.9)

def sub(note, d, a=1.0, glide=0.0):
    n = int(SR * d)
    f = np.full(n, note)
    if glide:
        f = note * (1 + glide * np.exp(-np.arange(n) / (SR * 0.06)))
    env = np.minimum(1, np.arange(n) / (SR * 0.01)) * dec(n, d / 2.2)
    return np.sin(2*np.pi*np.cumsum(f)/SR) * env * a

def stab(note, d=0.26, a=1.0, cut=2600):
    """Detuned saw pluck — the ostinato that carries the countdown."""
    n = int(SR * d); ph = np.arange(n) / SR
    s = sum(2*((ph*note*r) % 1) - 1 for r in (0.995, 1.0, 1.006)) / 3
    env = np.minimum(1, np.arange(n) / (SR * 0.004)) * dec(n, d / 3.4)
    return onepole_lp(s * env, cut) * a

def pad(note, d, a=1.0, cut=900):
    n = int(SR * d); ph = np.arange(n) / SR
    s = sum(2*((ph*note*r) % 1) - 1 for r in (0.993, 1.0, 1.004, 1.497)) / 4
    att = np.minimum(1, np.arange(n) / (SR * 0.35))
    rel = np.minimum(1, (n - np.arange(n)) / (SR * 0.5))
    return onepole_lp(s * att * rel, cut) * a

# ── notes (D minor) ────────────────────────────────────────────────────────
D1, D2, A1, Bb1, F1, F2, A2, D3, F3, A3 = 36.71, 73.42, 55.0, 58.27, 43.65, 87.31, 110.0, 146.83, 174.61, 220.0

low, mid, hi = buf(), buf(), buf()

# ── the hit layer, scene by scene ──────────────────────────────────────────
# 1 · open (0.00–3.84) — drone, then the two title slams
place(low, 0.00, pad(D2, 4.2, 0.30)); place(low, 0.00, sub(D1, 4.0, 0.34))
place(mid, 0.10, riser(0.80) * 0.22)
place(hi,  0.34, impact(0.45, 1.1))
place(mid, 0.58, riser(0.38) * 0.30)
place(hi,  0.96, impact(0.80, 1.5)); place(low, 0.96, sub(D1, 1.0, 0.55, 0.9))
place(mid, 1.12, riser(0.32) * 0.34)
place(hi,  1.44, impact(1.00, 2.2)); place(low, 1.44, sub(D1, 1.6, 0.68, 1.2))
place(hi,  2.40, impact(0.24, 0.8))

# 2 · the duel (3.84–9.60) — one hit per fighter, then VS, then the totals
place(hi,  3.84, impact(0.52, 1.3)); place(low, 3.84, sub(D1, 1.4, 0.45))
place(hi,  4.32, impact(0.58, 1.2)); place(low, 4.32, sub(D2, 0.9, 0.34))
place(hi,  4.80, impact(0.58, 1.2)); place(low, 4.80, sub(Bb1, 0.9, 0.34))
place(mid, 5.30, riser(0.46) * 0.44)
place(hi,  5.76, impact(0.92, 2.3)); place(low, 5.76, sub(D1, 1.8, 0.70, 1.1))
place(mid, 7.20, riser(0.48) * 0.34)
place(hi,  7.68, impact(0.70, 1.7)); place(low, 7.68, sub(F1, 1.4, 0.50))

# 3 · tale of the tape (9.60–14.40) — a tick per row
place(hi,  9.60, impact(0.52, 1.4))
for k_ in range(4):
    place(mid, 10.08 + k_*0.48, stab([D3, F3, A3, D3*2][k_], 0.26, 0.20, 2800))
    place(hi,  10.08 + k_*0.48, impact(0.26, 0.7))
place(hi,  12.96, impact(0.34, 1.0))
place(mid, 13.70, riser(0.70) * 0.34)

# 4 · the swing (14.40–18.24) — the breath, then the perfect night
place(hi,  14.40, impact(0.56, 1.5))
place(mid, 15.10, riser(0.74) * 0.50)
place(hi,  15.84, impact(1.00, 2.6)); place(low, 15.84, sub(F1, 2.4, 0.76, 1.3))
place(low, 15.84, pad(F2, 3.2, 0.28))
for k_, tt in enumerate((16.80, 16.94, 17.08)):
    place(hi, tt, impact(0.30, 0.7))
    place(mid, tt, stab([D3, F3, A3][k_], 0.30, 0.18, 3000))

# 5 · the chasers (18.24–20.64)
place(hi,  18.24, impact(0.50, 1.3))
for k_ in range(3):
    place(mid, 18.72 + k_*0.48, stab([A2, D3, F3][k_], 0.24, 0.14, 2400))
    place(hi,  18.72 + k_*0.48, impact(0.30, 0.8))
place(mid, 20.10, riser(0.52) * 0.40)

# 6 · close (20.64–23.20)
place(hi,  20.64, impact(0.62, 1.6)); place(low, 20.64, sub(A1, 1.1, 0.48))
place(hi,  21.12, impact(1.00, 3.0)); place(low, 21.12, sub(D1, 3.0, 0.80, 1.0))
place(low, 21.12, pad(D2, 2.6, 0.34))
place(mid, 21.12, stab(D3, 1.0, 0.18, 2600))
place(hi,  22.40, impact(0.34, 1.6))

# ══════════════════════════════════════════════════════════════════════════
#  THE BED — drums, bass, arpeggio and chords on a Dm-Bb-F-C loop at 125 BPM.
#  One bar is 1.92s, one chord per bar, so the loop turns over every 7.68s.
#  ENERGY(t) is the arrangement in one function, and it follows the picture.
# ══════════════════════════════════════════════════════════════════════════

BAR = BEAT * 4                                   # 1.92 s

PROG = [
    (73.42,  [146.83, 174.61, 220.00, 293.66]),   # Dm : D F A D
    (58.27,  [116.54, 174.61, 220.00, 293.66]),   # Bb : Bb F A D
    (87.31,  [174.61, 220.00, 261.63, 349.23]),   # F  : F A C F
    (65.41,  [130.81, 164.81, 196.00, 261.63]),   # C  : C E G C
]
def chord_at(t):
    return PROG[int(t / BAR) % 4]

def ENERGY(t):
    if t < 1.30:  return 0.00                    # the title lands dry
    if t < 3.84:  return 0.34                    # a pulse under the open
    if t < 5.76:  return 0.66                    # the two fighters arrive
    if t < 9.60:  return 0.88                    # VS, and the totals
    if t < 14.40: return 1.00                    # tale of the tape, full bed
    if t < 15.84: return 0.10                    # the breath before the 60
    if t < 18.24: return 1.00                    # the perfect night
    if t < 20.64: return 0.86                    # the chasers
    if t < 22.60: return 0.94                    # the date
    return 0.30

# ── added voices ───────────────────────────────────────────────────────────
def hat(d=0.055, bright=7000, a=1.0):
    n = int(SR * d)
    return onepole_hp(rng.normal(0, 1, n) * dec(n, d / 4.5), bright) * a

def openhat(d=0.22, a=1.0):
    n = int(SR * d)
    return onepole_hp(rng.normal(0, 1, n) * dec(n, d / 3.0), 5600) * a

def clap(a=1.0):
    n = int(SR * 0.30)
    body = onepole_hp(rng.normal(0, 1, n), 1100)
    env = dec(n, 0.055)
    for off in (0.000, 0.011, 0.021):            # three taps -> a real clap
        i = int(off * SR)
        env[i:] = np.maximum(env[i:], dec(n - i, 0.05) * (1 - off * 12))
    tail = onepole_lp(rng.normal(0, 1, n) * dec(n, 0.12), 2600) * 0.25
    return (body * env + tail) * a

def bass(note, d, a=1.0, cut=520):
    """Square-ish bass with a fast filter env — the drive under the loop."""
    n = int(SR * d); ph = np.arange(n) / SR
    saw = 2 * ((ph * note) % 1) - 1
    sq = np.sign(np.sin(2 * np.pi * note * ph)) * 0.45
    env = np.minimum(1, np.arange(n) / (SR * 0.005)) * dec(n, d / 2.6)
    fenv = cut + 1500 * np.exp(-np.arange(n) / (SR * 0.05))
    return sat(onepole_lp((saw * 0.7 + sq) * env, fenv), 1.5) * a

def arp(note, d=0.13, a=1.0, cut=3200):
    n = int(SR * d); ph = np.arange(n) / SR
    s = (2 * ((ph * note) % 1) - 1) * 0.6 + np.sin(2 * np.pi * note * 2 * ph) * 0.4
    env = np.minimum(1, np.arange(n) / (SR * 0.002)) * dec(n, d / 4.0)
    return onepole_lp(s * env, cut) * a

def chordstab(notes, d=0.30, a=1.0, cut=2000):
    n = int(SR * d); ph = np.arange(n) / SR
    s = sum(2 * ((ph * f * r) % 1) - 1 for f in notes for r in (0.996, 1.004))
    s /= (len(notes) * 2)
    env = np.minimum(1, np.arange(n) / (SR * 0.010)) * dec(n, d / 2.8)
    return onepole_lp(s * env, cut) * a

# ── lay the bed, one sixteenth at a time ───────────────────────────────────
drums, bed = buf(), buf()
STEP = BEAT / 4                                  # 0.12 s — a sixteenth
nsteps = int(DUR / STEP)

for k in range(nsteps):
    t = k * STEP
    e = ENERGY(t)
    if e <= 0.02:
        continue
    beat16 = k % 16                               # position in the bar
    root, tones = chord_at(t)

    # hats — sixteenths once the bed is up, eighths below that
    if e >= 0.60 or beat16 % 2 == 0:
        acc = 1.0 if beat16 % 4 == 0 else (0.62 if beat16 % 2 == 0 else 0.42)
        place(drums, t, hat(a=0.090 * acc * e))
    if beat16 in (6, 14) and e >= 0.62:           # open hat, offbeat lift
        place(drums, t, openhat(a=0.075 * e))

    # clap on 2 and 4
    if beat16 in (4, 12) and e >= 0.55:
        place(drums, t, clap(0.115 * e))

    # bass — driving eighths, with a push on the offbeat before the bar
    if beat16 % 2 == 0 and e >= 0.30:
        note = root * (2 if beat16 == 8 and e >= 0.95 else 1)
        place(bed, t, bass(note, STEP * 1.85, 0.30 * e))
    elif beat16 == 15 and e >= 0.78:
        place(bed, t, bass(root, STEP * 0.9, 0.22 * e))

    # arpeggio — sixteenths, up and back down the chord
    if e >= 0.55:
        pat = [0, 1, 2, 3, 2, 1, 2, 3, 0, 1, 2, 3, 3, 2, 1, 2][beat16]
        oct_ = 2 if (e >= 0.95 and beat16 % 8 >= 4) else 1
        place(bed, t, arp(tones[pat] * oct_, 0.13,
                          (0.052 + 0.020 * (beat16 % 4 == 0)) * e))

    # chord stabs on the offbeats — the lift
    if beat16 in (2, 10) and e >= 0.62:
        place(bed, t, chordstab(tones[:3], 0.34, 0.085 * e))

# a sustained pad under the whole loop, so the harmony never drops out
tb = 0.0
while tb < DUR:
    e = ENERGY(tb + BAR * 0.5)
    if e > 0.25:
        _, tones = chord_at(tb)
        place(bed, tb, pad(tones[0] / 2, BAR * 1.02, 0.10 * e, 1100))
    tb += BAR

drums = onepole_hp(drums, 220)                   # keep the kit out of the sub
# The bed is built at conservative per-voice levels so nothing clips on its own,
# which leaves it ~20dB under the impact layer -- inaudible. These gains lift it
# into a real backing track, roughly 7dB under the hits: present the whole way
# through, still out of the way when something lands.
low += bed * 3.4
mid += drums * 9.0 + bed * 3.2
# ── mix ────────────────────────────────────────────────────────────────────
low = onepole_lp(low, 320)                 # keep the weight under the mids
mid = onepole_hp(mid, 140)
hi  = onepole_hp(hi, 45)

mono = low*0.92 + mid*0.85 + hi*0.62

# duck the bed a touch on every hit, so the impacts read
duck = np.ones(N)
for bt, a in BEATS:
    i = int(bt*SR); n = int(SR*0.28)
    if i >= N: continue
    n = min(n, N-i)
    duck[i:i+n] = np.minimum(duck[i:i+n], 1 - 0.22*a*np.exp(-np.arange(n)/(SR*0.055)))
mono *= duck

mono = sat(mono * 1.25, 1.1)               # glue

# gentle stereo: the mids widen, the low stays centred
delay = int(SR*0.011)
wide = np.concatenate([np.zeros(delay), mid[:-delay]]) * 0.40
L = mono + wide*0.5
R = mono - wide*0.5

# top and tail
fi, fo = int(SR*0.05), int(SR*0.55)
for ch in (L, R):
    ch[:fi]  *= np.linspace(0, 1, fi)
    ch[-fo:] *= np.linspace(1, 0, fo) ** 1.6

peak = max(np.abs(L).max(), np.abs(R).max())
L *= 0.89/peak; R *= 0.89/peak
rms = np.sqrt(np.mean((L**2 + R**2)/2))
print(f"peak {20*math.log10(max(abs(L).max(), abs(R).max())):.2f} dBFS · rms {20*math.log10(rms):.2f} dBFS")

stereo = np.empty(N*2, dtype=np.int16)
stereo[0::2] = np.clip(L, -1, 1) * 32767
stereo[1::2] = np.clip(R, -1, 1) * 32767
data = stereo.tobytes()
with open('score.wav', 'wb') as f:
    f.write(b'RIFF' + struct.pack('<I', 36+len(data)) + b'WAVEfmt ')
    f.write(struct.pack('<IHHIIHH', 16, 1, 2, SR, SR*4, 4, 16))
    f.write(b'data' + struct.pack('<I', len(data)) + data)
print(f"score.wav · {DUR}s · {BPM:g} BPM · {len(BEATS)} hits")
