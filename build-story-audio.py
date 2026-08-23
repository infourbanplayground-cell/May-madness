# -*- coding: utf-8 -*-
"""Original, synthesized audio bed for the session-story video — not a
licensed track. Nothing here is sourced or sampled; every sound is generated
from scratch in Python, which sidesteps the copyright problem entirely for
something that's about to be posted publicly on a business account.

Synced to the EXACT animation delays already in build-session-story.py's
ANIM_CSS, not to a guessed rhythm:
  0.15s  wordmark slam        -> soft low thud
  1.15s  "07" slam (the hero beat) -> the one big hit, kick+sub+noise
  1.15-6.3s                   -> steady pulse under the reveals
  2.20 / 2.33 / 2.46s  tiles cascading      -> three ticks
  2.95 / 3.10 / 3.25s  chase rows cascading -> three ticks
  3.60s  CTA panel            -> a secondary whoosh/hit
  6.3-7.0s                    -> fade to silence, matches the video's hold

  python3 build_story_audio.py
"""
import numpy as np
import wave, os

SC = os.path.dirname(os.path.abspath(__file__))
SR = 44100
DUR = 7.0
N = int(SR * DUR)
out = np.zeros(N)

def t_range(t0, t1):
    i0, i1 = int(t0 * SR), min(int(t1 * SR), N)
    return i0, i1, np.linspace(0, t1 - t0, max(i1 - i0, 0), endpoint=False)

def add(t0, sig):
    i0 = int(t0 * SR)
    i1 = min(i0 + len(sig), N)
    if i1 > i0:
        out[i0:i1] += sig[:i1 - i0]

def kick(t0, freq0=150, freq1=45, dur=0.14, amp=1.0, click=0.35):
    i0, i1, tt = t_range(t0, t0 + dur)
    if len(tt) == 0: return
    freq = freq0 * (freq1 / freq0) ** (tt / dur)
    phase = 2 * np.pi * np.cumsum(freq) / SR
    env = np.exp(-tt / (dur * 0.28))
    body = np.sin(phase) * env
    # transient click so the hit reads as an impact, not just a pitched tone
    click_n = min(int(0.006 * SR), len(tt))
    clk = np.zeros(len(tt)); clk[:click_n] = (np.random.rand(click_n) * 2 - 1) * np.exp(-np.arange(click_n) / (click_n * 0.3))
    add(t0, amp * (body + click * clk))

def sub_hit(t0, freq=42, dur=0.5, amp=0.9):
    i0, i1, tt = t_range(t0, t0 + dur)
    if len(tt) == 0: return
    env = np.exp(-tt / (dur * 0.35))
    add(t0, amp * np.sin(2 * np.pi * freq * tt) * env)

def tick(t0, hp=True, dur=0.045, amp=0.5):
    i0, i1, tt = t_range(t0, t0 + dur)
    if len(tt) == 0: return
    n = np.random.rand(len(tt)) * 2 - 1
    if hp:
        n = np.diff(n, prepend=0)  # crude high-pass — differencing kills the low end
    env = np.exp(-tt / (dur * 0.22))
    add(t0, amp * n * env)

def whoosh(t0, dur=0.32, amp=0.45, up=True):
    i0, i1, tt = t_range(t0, t0 + dur)
    if len(tt) == 0: return
    n = np.random.rand(len(tt)) * 2 - 1
    sweep = np.linspace(0.15, 1.0, len(tt)) if up else np.linspace(1.0, 0.15, len(tt))
    # band-limit crudely by smoothing (a cheap low-pass), amount rides the sweep
    kernel = 9
    sm = np.convolve(n, np.ones(kernel) / kernel, mode='same')
    n = n * sweep + sm * (1 - sweep)
    env = np.sin(np.pi * tt / dur)  # in-out envelope, no click at either end
    add(t0, amp * n * env)

def riser(t0, t1, amp0=0.02, amp1=0.5):
    i0, i1, tt = t_range(t0, t1)
    if len(tt) == 0: return
    dur = t1 - t0
    freq = 90 * (5.0) ** (tt / dur)          # sweeps up ~5 octaves-ish, tension build
    phase = 2 * np.pi * np.cumsum(freq) / SR
    amp = amp0 + (amp1 - amp0) * (tt / dur) ** 1.6
    add(t0, np.sin(phase) * amp)

def pulse_bed(t0, t1, bpm=128, amp=0.28):
    beat = 60 / bpm
    t = t0
    i = 0
    while t < t1:
        kick(t, freq0=110, freq1=55, dur=beat * 0.55, amp=amp, click=0.15)
        # off-beat tick for a bit of groove, not a flat metronome
        if i % 2 == 1:
            tick(t + beat * 0.5, dur=0.03, amp=0.12)
        t += beat
        i += 1

# ── Build, beat for beat against the real animation timeline ──────────────
riser(0.02, 1.13, amp0=0.015, amp1=0.55)          # tension into the hero reveal
kick(0.15, freq0=120, freq1=60, dur=0.10, amp=0.35, click=0.2)  # wordmark — soft, not the hero hit
kick(1.15, freq0=170, freq1=45, dur=0.20, amp=1.0, click=0.5)   # "07" — THE hit
sub_hit(1.15, freq=42, dur=0.55, amp=0.85)
pulse_bed(1.55, 6.3, bpm=128, amp=0.22)            # steady pulse under the reveals

for tt_ in (2.20, 2.33, 2.46, 2.95, 3.10, 3.25):    # tiles, then chase rows
    tick(tt_, dur=0.04, amp=0.4)
whoosh(3.58, dur=0.30, amp=0.4, up=True)            # CTA panel lands

# ── Master: normalise, then fade out matching the video's hold ────────────
peak = np.max(np.abs(out))
if peak > 0:
    out = out / peak * 0.85   # headroom, no clipping
fade_start = int(6.3 * SR)
fade = np.linspace(1, 0, N - fade_start) ** 1.5
out[fade_start:] *= fade

rms = np.sqrt(np.mean(out ** 2))
print(f'peak={np.max(np.abs(out)):.3f}  rms={rms:.3f}  duration={DUR}s  sr={SR}')

pcm = (out * 32767).astype(np.int16)
with wave.open(f'{SC}/story-audio.wav', 'wb') as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes(pcm.tobytes())
print('wrote story-audio.wav')
