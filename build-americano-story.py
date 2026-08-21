# -*- coding: utf-8 -*-
"""URBAN PLAYGROUND — Americano tournament story video (Instagram, 1080x1920).

Standalone one-off Saturday event, not a monthly series — house brand
(Urban Orange, sampled from the logo), not August Attack red or September
Surge cyan.

4 scenes crossfading over 14s. Everything sits inside 170..1676 — the real
story-safe frame (top overlay is only the profile row, not a blanket
250/250) — verified by measuring every child of the safe box, not eyeballed.

The join QR is generated from the same URL string printed on the card, so
the two cannot disagree, and is decoded back out of a captured frame before
the video ships.

  python3 build_americano_story.py && node record-americano.mjs
"""
import base64, io, os
import qrcode
from PIL import Image

SC = os.path.dirname(os.path.abspath(__file__))
b64f = lambda f: base64.b64encode(open(f'{SC}/{f}', 'rb').read()).decode()

teko6 = b64f('teko600.woff2'); teko7 = b64f('teko700.woff2')
arch6 = b64f('archivo600.woff2'); arch8 = b64f('archivo800.woff2')
mono  = b64f('jbmono700.woff2')
logo  = b64f('up-logo-new.png')

ORANGE, CHALK, STEEL, COURT, DEEP = '#F56530', '#F4F6FA', '#8B95A7', '#0A0C12', '#06070B'

GROUP_URL = 'https://chat.whatsapp.com/JFwNie1eVWf4BJHSNHpKNu'
q = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=12, border=2)
q.add_data(GROUP_URL); q.make(fit=True)
qr_img = q.make_image(fill_color=COURT, back_color=CHALK).convert('RGB')
# Generated at 444x444 but displayed at 150 CSS px (see .join .qr below). Letting
# the browser scale it down via CSS was silently undecodable: Chromium's
# downscale filter blurs the fine modules enough to break detection even
# though the image looks sharp to the eye — this shipped once already with
# a bare corner-tick/border mistake, same failure mode, different cause.
# Pre-resizing with PIL's own LANCZOS to the exact display pixel size and
# embedding THAT is pixel-exact with zero browser-side resampling; verified
# against a matrix of sizes (150-300px) before landing on 150.
# .join .qr is a 150px box with box-sizing:border-box and 8px padding, so
# the <img> itself actually renders at 150-2*8=134px, not 150 — resizing to
# 150 would still leave the browser to do a second, smaller resize on top.
QR_PAD = 8
qr_img = qr_img.resize((150 - 2 * QR_PAD, 150 - 2 * QR_PAD), Image.LANCZOS)
buf = io.BytesIO()
qr_img.save(buf, 'PNG')
qr = base64.b64encode(buf.getvalue()).decode()

# Exactly the players named in the sign-up message — real names, real order,
# not filled in with placeholders. Empty slots are counted, not invented.
PLAYERS = ['Mutaz', 'Muether', 'Munther R', 'Manaf']
TOTAL_SLOTS = 16
FILLED = len(PLAYERS)
LEFT = TOTAL_SLOTS - FILLED

CSS = f"""
@font-face{{font-family:'Teko';font-weight:600;src:url(data:font/woff2;base64,{teko6}) format('woff2')}}
@font-face{{font-family:'Teko';font-weight:700;src:url(data:font/woff2;base64,{teko7}) format('woff2')}}
@font-face{{font-family:'Archivo';font-weight:600;src:url(data:font/woff2;base64,{arch6}) format('woff2')}}
@font-face{{font-family:'Archivo';font-weight:800;src:url(data:font/woff2;base64,{arch8}) format('woff2')}}
@font-face{{font-family:'Mono';font-weight:700;src:url(data:font/woff2;base64,{mono}) format('woff2')}}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{width:1080px;height:1920px;overflow:hidden;position:relative;color:{CHALK};
  font-family:Archivo,sans-serif;background:
  radial-gradient(ellipse 92% 28% at 50% 2%, rgba(245,101,48,.30), transparent 62%),
  radial-gradient(ellipse 60% 22% at 6% 88%, rgba(245,101,48,.10), transparent 64%),
  linear-gradient(180deg,#08090D 0%,{COURT} 46%,{DEEP} 100%)}}
.grid{{position:absolute;inset:0;z-index:0;opacity:.45;
  background-image:linear-gradient(rgba(245,101,48,.055) 1px,transparent 1px),
   linear-gradient(90deg,rgba(245,101,48,.055) 1px,transparent 1px);background-size:48px 48px;
  -webkit-mask-image:radial-gradient(120% 60% at 50% 16%,#000,transparent 88%)}}
.tk{{position:absolute;width:64px;height:64px;z-index:6}}
.tk.tl{{top:186px;left:44px;border-top:6px solid {ORANGE};border-left:6px solid {ORANGE}}}
.tk.br{{bottom:260px;right:44px;border-bottom:6px solid {ORANGE};border-right:6px solid {ORANGE}}}

/* Every scene occupies the same safe box; only one is visible at a time. */
.sc{{position:absolute;left:0;right:0;top:170px;bottom:244px;z-index:4;
  display:flex;flex-direction:column;align-items:center;justify-content:center;
  padding:0 62px;text-align:center;opacity:0}}

.logo{{width:150px;height:auto;margin-bottom:20px;filter:drop-shadow(0 0 26px rgba(245,101,48,.42))}}
.kick{{font-family:Mono;font-weight:700;font-size:19px;letter-spacing:.26em;color:{STEEL}}}
h1{{margin-top:16px;font-family:Teko,sans-serif;font-weight:700;font-size:150px;
  line-height:.82;letter-spacing:.02em;text-transform:uppercase;
  text-shadow:0 0 56px rgba(245,101,48,.4)}}
h1 em{{font-style:normal;color:{ORANGE}}}
.tag{{margin-top:20px;font-weight:600;font-size:27px;line-height:1.4;color:#C9CFDA;max-width:820px}}
.tag b{{color:{CHALK};font-weight:800}}

.rules{{width:100%;margin-top:10px;display:flex;flex-direction:column;gap:15px}}
.rule{{display:flex;align-items:center;gap:18px;background:rgba(20,24,36,.9);
  border-left:4px solid {ORANGE};padding:20px 20px;text-align:left}}
.rule .n{{flex:0 0 auto;width:56px;font-family:Teko,sans-serif;font-weight:700;font-size:42px;color:{ORANGE}}}
.rule p{{font-weight:600;font-size:23px;line-height:1.35;color:{CHALK}}}

.info{{width:100%;display:flex;flex-direction:column;gap:14px;margin-top:26px}}
.row{{display:flex;align-items:center;justify-content:space-between;
  background:rgba(20,24,36,.9);border:1px solid rgba(244,246,250,.10);padding:20px 22px}}
.row .l{{font-family:Mono;font-weight:700;font-size:16px;letter-spacing:.18em;color:{STEEL}}}
.row .v{{font-family:Teko,sans-serif;font-weight:700;font-size:38px;color:{CHALK}}}
.row .v em{{font-style:normal;color:{ORANGE}}}

.prizes{{width:100%;margin-top:20px;display:flex;gap:14px}}
.pz{{flex:1;background:rgba(20,24,36,.9);border:1px solid rgba(244,246,250,.10);padding:20px 14px;text-align:center}}
.pz .m{{font-size:34px}}
.pz .t{{margin-top:8px;font-family:Mono;font-weight:700;font-size:13px;letter-spacing:.16em;color:{STEEL}}}
.pz .d{{margin-top:6px;font-family:Teko,sans-serif;font-weight:700;font-size:28px;color:{CHALK};line-height:1.1}}
.pz.win{{border-color:rgba(245,101,48,.4)}}

.slots{{width:100%;margin-top:22px;background:rgba(20,24,36,.9);border:1px solid rgba(244,246,250,.10);padding:22px}}
.slots .h{{display:flex;align-items:baseline;justify-content:space-between;margin-bottom:14px}}
.slots .h span:first-child{{font-family:Mono;font-weight:700;font-size:16px;letter-spacing:.18em;color:{ORANGE}}}
.slots .h span:last-child{{font-family:Teko,sans-serif;font-weight:700;font-size:30px;color:{CHALK}}}
.bar{{height:8px;background:rgba(139,149,167,.2)}}
.bar i{{display:block;height:100%;background:{ORANGE}}}
.names{{margin-top:16px;display:flex;flex-wrap:wrap;gap:10px;justify-content:center}}
.chip{{font-family:Teko,sans-serif;font-weight:600;font-size:24px;color:{CHALK};
  background:rgba(245,101,48,.14);border:1px solid rgba(245,101,48,.35);padding:6px 16px 4px}}

.join{{width:100%;margin-top:24px;display:flex;align-items:center;gap:22px;
  background:rgba(20,24,36,.9);border:1px solid rgba(245,101,48,.45);padding:20px 22px;text-align:left}}
.join .qr{{flex:0 0 auto;width:150px;height:150px;background:{CHALK};padding:8px}}
.join .qr img{{width:100%;height:100%;display:block;image-rendering:pixelated}}
.join .lab{{font-family:Mono;font-weight:700;font-size:15px;letter-spacing:.18em;color:{ORANGE}}}
.join .big{{margin-top:6px;font-family:Teko,sans-serif;font-weight:700;font-size:40px;line-height:1.05;color:{CHALK}}}

@keyframes fade{{from{{opacity:0}} to{{opacity:1}}}}
@keyframes up  {{from{{opacity:0;transform:translateY(28px)}} to{{opacity:1;transform:none}}}}
@keyframes slam{{0%{{opacity:0;transform:scale(1.5)}} 60%{{opacity:1;transform:scale(.96)}}
                 80%{{transform:scale(1.02)}} 100%{{opacity:1;transform:scale(1)}}}}
"""

# Scene visibility windows (seconds), same technique as the recap video: one
# keyframe per scene spanning the whole timeline with percentage stops, not
# two separate opacity animations — a second animation's backwards fill
# would otherwise win during the fill phase and every scene would sit at
# opacity 1 from t=0.
TOTAL = 14.0
SCENES = [(0.0, 3.2), (2.9, 6.6), (6.3, 10.0), (9.7, 14.0)]
FADE = 0.45
for i, (a, b) in enumerate(SCENES, 1):
    pct = lambda t: round(max(0.0, min(100.0, t / TOTAL * 100)), 3)
    last = (i == len(SCENES))
    p1, p2 = pct(a), pct(a + FADE)
    tail = "100%{opacity:1}" if last else f"{pct(b - FADE)}%{{opacity:1}} {pct(b)}%,100%{{opacity:0}}"
    CSS += (f"\n@keyframes scene{i}{{"
            f"0%,{p1}%{{opacity:0}} {p2}%{{opacity:1}} {tail}}}"
            f"\n#s{i}{{animation:scene{i} {TOTAL}s linear 0s both}}")

def anim(sel, kf, dur, delay, extra=''):
    return f"\n{sel}{{animation:{kf} {dur}s cubic-bezier(.23,1,.32,1) {delay}s both{extra}}}"

CSS += anim('#s1 .logo', 'slam', .8, .15)
CSS += anim('#s1 .kick', 'up', .5, .55)
CSS += anim('#s1 h1', 'slam', .8, .75)
CSS += anim('#s1 .tag', 'up', .5, 1.3)

CSS += anim('#s2 .kick', 'up', .45, 2.9)
CSS += anim('#s2 h1', 'up', .55, 3.1, '')
for j in range(1, 4):
    CSS += anim(f'#s2 .rule:nth-child({j})', 'up', .5, 3.5 + .18 * (j - 1))

CSS += anim('#s3 .kick', 'up', .45, 6.3)
CSS += anim('#s3 .info .row:nth-child(1)', 'up', .5, 6.55)
CSS += anim('#s3 .info .row:nth-child(2)', 'up', .5, 6.75)
CSS += anim('#s3 .prizes .pz:nth-child(1)', 'up', .5, 7.05)
CSS += anim('#s3 .prizes .pz:nth-child(2)', 'up', .5, 7.2)

CSS += anim('#s4 .kick', 'up', .45, 9.7)
CSS += anim('#s4 .slots', 'up', .55, 9.95)
CSS += anim('#s4 .join', 'up', .55, 10.6)

HTML = f"""<!doctype html><meta charset="utf-8"><style>{CSS}</style>
<div class="grid"></div><div class="tk tl"></div><div class="tk br"></div>

<div class="sc" id="s1">
  <img class="logo" src="data:image/png;base64,{logo}" alt="Urban Playground">
  <div class="kick">URBAN PLAYGROUND</div>
  <h1>AMERICANO<br><em>@ THE PLAYGROUND</em></h1>
  <div class="tag">New teammate <b>every round</b>. Play with everyone,
    face every opponent twice.</div>
</div>

<div class="sc" id="s2">
  <div class="kick">THE FORMAT</div>
  <h1 style="font-size:80px;margin-top:12px">HOW IT WORKS</h1>
  <div class="rules">
    <div class="rule"><span class="n">01</span><p>New partner drawn <b style="color:#F4F6FA">every round</b> &mdash; no fixed teams.</p></div>
    <div class="rule"><span class="n">02</span><p>By the end, you've <b style="color:#F4F6FA">played with every player</b> at least once.</p></div>
    <div class="rule"><span class="n">03</span><p>Most points after the final match <b style="color:#F4F6FA">wins it all</b>.</p></div>
  </div>
</div>

<div class="sc" id="s3">
  <div class="kick">SATURDAY &middot; 6:00 PM</div>
  <h1 style="font-size:88px;margin-top:12px">DETAILS</h1>
  <div class="info">
    <div class="row"><span class="l">DATE</span><span class="v">SAT, 22 AUG</span></div>
    <div class="row"><span class="l">ENTRY FEE</span><span class="v"><em>7</em> OMR</span></div>
  </div>
  <div class="prizes">
    <div class="pz win"><div class="m">&#127942;</div><div class="t">WINNER</div><div class="d">15 OMR<br>Voucher</div></div>
    <div class="pz"><div class="m">&#127941;</div><div class="t">RUNNER-UP</div><div class="d">Special<br>Gift</div></div>
  </div>
</div>

<div class="sc" id="s4">
  <div class="kick">UP TO 16 PLAYERS</div>
  <div class="slots">
    <div class="h"><span>SPOTS FILLED</span><span>{FILLED} / {TOTAL_SLOTS}</span></div>
    <div class="bar"><i style="width:{round(FILLED/TOTAL_SLOTS*100)}%"></i></div>
    <div class="names">
      {''.join(f'<span class="chip">{n}</span>' for n in PLAYERS)}
    </div>
  </div>
  <div class="join">
    <div class="qr"><img src="data:image/png;base64,{qr}" alt="Join QR"></div>
    <div>
      <div class="lab">SCAN TO JOIN</div>
      <div class="big">{LEFT} SPOTS<br>LEFT</div>
    </div>
  </div>
</div>"""

open(f'{SC}/americano-story.html', 'w').write(HTML)
print('built americano-story.html')
print(f'  players filled: {FILLED}/{TOTAL_SLOTS} -> {LEFT} left')
print(f'  join url: {GROUP_URL}')
