"""
Original score for the September Surge hype cut.

Everything here is synthesised from scratch — no samples, no library music — so
the track is ours and carries no licence or copyright-claim risk on Instagram.

It is written against the cut's own beat map (BEATS in reel.html), so the hits
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
S3 = 7.60
RT = {9:0.60, 8:0.84, 7:1.08, 6:1.32, 5:1.56, 4:1.80, 3:2.08, 2:2.40, 1:2.80, 0:3.38}
BEATS = [
    (0.34,.34), (0.98,.72), (1.34,.92), (2.26,.22),
    (4.22,.46), (4.70,.52), (5.36,.52), (6.10,.44),
    (7.62,.50),
    (15.82,.42), (16.62,.95), (17.62,.26), (17.76,.26), (17.90,.26),
    (20.22,.48), (20.52,.62), (20.86,.92), (22.16,.40),
] + [(S3 + v, .80 if k == 0 else .20) for k, v in RT.items()]

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

# ── 1 · open (0.0–4.2): drone, then the two title hits ─────────────────────
place(low, 0.00, pad(D2, 4.6, 0.30))
place(low, 0.00, sub(D1, 4.4, 0.34))
place(mid, 0.10, riser(0.85) * 0.22)
place(hi,  0.34, impact(0.45, 1.1))
place(mid, 0.60, riser(0.40) * 0.30)
place(hi,  0.98, impact(0.78, 1.5)); place(low, 0.98, sub(D1, 1.0, 0.55, 0.9))
place(mid, 1.05, riser(0.30) * 0.34)
place(hi,  1.34, impact(1.00, 2.2)); place(low, 1.34, sub(D1, 1.6, 0.68, 1.2))
place(hi,  2.26, impact(0.24, 0.8))
# heartbeat under the sub-line, half-time
for i in range(4):
    place(low, 2.30 + i*BEAT*2, kick() * 0.40)

# ── 2 · dates (4.2–7.6): pulse enters ──────────────────────────────────────
place(low, 4.20, pad(D2, 3.6, 0.26))
for i in range(8):                                   # four-on-the-floor
    tt = 4.22 + i*BEAT
    if tt < 7.55: place(low, tt, kick() * (0.62 if i % 2 == 0 else 0.44))
for i, nt in enumerate([D3, A2, D3, F3, A2, D3, F3, A2]):
    tt = 4.22 + i*BEAT
    if tt < 7.55: place(mid, tt, stab(nt, 0.30, 0.16))
place(hi,  4.22, impact(0.50, 1.3)); place(low, 4.22, sub(D1, 1.4, 0.45))
place(hi,  4.70, impact(0.40, 0.9))
place(hi,  5.36, impact(0.40, 0.9))
place(mid, 5.70, riser(0.40) * 0.26)
place(hi,  6.10, impact(0.52, 1.4)); place(low, 6.10, sub(Bb1, 1.4, 0.46))
place(mid, 6.90, riser(0.70) * 0.34)

# ── 3 · the chase (7.6–15.8): the countdown ────────────────────────────────
place(hi,  7.62, impact(0.55, 1.5))
place(low, 7.60, pad(D2, 8.4, 0.24))
# driving pulse, whole scene
i = 0
while 7.62 + i*BEAT < 15.70:
    tt = 7.62 + i*BEAT
    place(low, tt, kick() * (0.70 if i % 2 == 0 else 0.46))
    i += 1
# a tick on every contender landing — rank 10 up to the leader
ranks = sorted(RT.items(), key=lambda kv: kv[1])
SCALE = [D3, F3, A3, D3*2, F3*2]
for idx, (rank, off) in enumerate(ranks):
    tt = S3 + off
    if rank == 0:                                     # the leader
        place(mid, tt - 0.55, riser(0.55) * 0.52)
        place(hi,  tt, impact(0.92, 2.4))
        place(low, tt, sub(D1, 2.2, 0.72, 1.1))
        place(mid, tt, stab(D3*2, 0.7, 0.20, 3400))
    else:
        note = SCALE[min(4, idx // 2)] * (1 + 0.0 )
        place(mid, tt, stab(note, 0.22, 0.10 + 0.012*idx, 2200 + 180*idx))
# the podium focus-rack: pull the pulse back, let the pad breathe
place(mid, 11.30, pad(F2, 2.0, 0.20, 700))
place(mid, 13.40, riser(1.10) * 0.30)
place(low, 13.40, sub(Bb1, 2.2, 0.40))
place(mid, 15.10, riser(0.70) * 0.42)

# ── 4 · the 60 (15.8–20.2) ─────────────────────────────────────────────────
place(hi,  15.82, impact(0.46, 1.2))
place(mid, 15.90, riser(0.70) * 0.46)
place(hi,  16.62, impact(1.00, 2.6)); place(low, 16.62, sub(F1, 2.4, 0.74, 1.3))
place(low, 16.62, pad(F2, 3.4, 0.28))
for i in range(7):
    tt = 16.66 + i*BEAT
    if tt < 20.10: place(low, tt, kick() * (0.66 if i % 2 == 0 else 0.44))
for j, tt in enumerate((17.62, 17.76, 17.90)):        # 75 / 50 / 30
    place(hi, tt, impact(0.30, 0.7))
    place(mid, tt, stab([D3, F3, A3][j], 0.30, 0.18, 3000))
place(mid, 19.40, riser(0.80) * 0.40)

# ── 5 · close (20.2–23.2) ──────────────────────────────────────────────────
place(hi,  20.22, impact(0.52, 1.4))
place(hi,  20.52, impact(0.66, 1.7)); place(low, 20.52, sub(A1, 1.2, 0.50))
place(hi,  20.86, impact(1.00, 3.0)); place(low, 20.86, sub(D1, 3.0, 0.80, 1.0))
place(low, 20.86, pad(D2, 2.9, 0.34))
place(mid, 20.86, stab(D3, 1.0, 0.18, 2600))
place(hi,  22.16, impact(0.34, 1.6))

# ── mix ────────────────────────────────────────────────────────────────────
low = onepole_lp(low, 320)                 # keep the weight under the mids
mid = onepole_hp(mid, 140)
hi  = onepole_hp(hi, 45)

mono = low*1.00 + mid*0.85 + hi*0.80

# duck the bed a touch on every hit, so the impacts read
duck = np.ones(N)
for bt, a in BEATS:
    i = int(bt*SR); n = int(SR*0.28)
    if i >= N: continue
    n = min(n, N-i)
    duck[i:i+n] = np.minimum(duck[i:i+n], 1 - 0.30*a*np.exp(-np.arange(n)/(SR*0.055)))
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
