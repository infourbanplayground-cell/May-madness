# -*- coding: utf-8 -*-
"""URBAN PLAYGROUND — court camera poster ("Capture your best moments").

1080x1528, i.e. A4 proportions (1:1.414). This is wall signage read from a
few metres away, not a social post, so it is sized for print and the type is
set for distance rather than for a thumbnail.

  python3 build_capture_poster.py --url "https://savemyplay.com/session-start/..."
  python3 build_capture_poster.py --qr court-1.png --court "COURT 1"
  python3 build_capture_poster.py                      # blank QR placeholder

The Save My Play link is PER SESSION/COURT and acts as a key — anyone
holding it can start a recording — so it is passed in at build time and
deliberately not stored here. If there is more than one court, each needs
its own poster; that is what --court labels.

QR rules carried over from build_pay_card.py, for the same reasons:
  · chalk panel, never dark-on-dark — inverted codes fail on many scanners
  · a real quiet zone. Regenerating this poster's code at border=0 made it
    undecodable in testing; border=2 inside the panel padding is the floor.

Verify the finished art, not the source image:
  cv2.QRCodeDetector().detectAndDecode(<the final png>)
"""
import argparse, base64, os, sys

SC = os.path.dirname(os.path.abspath(__file__))
b64f = lambda f: base64.b64encode(open(f'{SC}/{f}', 'rb').read()).decode()

ap = argparse.ArgumentParser()
ap.add_argument('--url',   default=None, help='encode this URL as the QR')
ap.add_argument('--qr',    default=None, help='or supply a QR image directly')
ap.add_argument('--court', default=None, help='court label, e.g. "COURT 1"')
ap.add_argument('--out',   default='capture-poster')
A = ap.parse_args()

anton = b64f('anton.woff2');      mono  = b64f('jbmono700.woff2')
arch8 = b64f('archivo800.woff2'); arch6 = b64f('archivo600.woff2')
logo  = b64f('up-logo-clean.png')

ORANGE, CHALK, STEEL = '#F56530', '#F4F6FA', '#8B95A7'

# Step 3 in the original reads: raise your hands to "Save it. Your last point
# will be saved automatically — an unclosed quote and a missing full stop.
# Rewritten rather than reproduced.
CAMERA_SVG = f'''<svg class="cam" viewBox="0 0 132 84" fill="none"
  xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
  <rect x="4" y="26" width="80" height="54" fill="{ORANGE}"/>
  <path d="M92 44 L128 26 L128 80 L92 62 Z" fill="{ORANGE}"/>
  <circle cx="30" cy="16" r="14" stroke="{ORANGE}" stroke-width="7"/>
  <circle cx="64" cy="16" r="10" stroke="{ORANGE}" stroke-width="7"/>
  <rect x="18" y="46" width="26" height="8" fill="{CHALK}"/>
</svg>'''

STEPS = [
    ('SCAN THE QR',      'Pick your court and how long you are playing for.'),
    ('START RECORDING',  'Tap <em>REC</em>. The court camera does the rest.'),
    ('HANDS UP TO SAVE', 'Won a point worth keeping? Look at the camera and '
                         'raise both hands &mdash; it saves that rally automatically.'),
    ('WATCH AND SHARE',  'Your highlights arrive by email. Watch, download, send them on.'),
]

if A.url:
    import qrcode
    from qrcode.constants import ERROR_CORRECT_M
    q = qrcode.QRCode(error_correction=ERROR_CORRECT_M, box_size=20, border=2)
    q.add_data(A.url); q.make(fit=True)
    q.make_image(fill_color='black', back_color='white').convert('L').save(f'{SC}/_poster_qr.png')
    qr_src = 'data:image/png;base64,' + b64f('_poster_qr.png')
elif A.qr:
    p = A.qr if os.path.isabs(A.qr) else f'{SC}/{A.qr}'
    if not os.path.exists(p):
        sys.exit(f'no such QR file: {p}')
    mime = 'image/svg+xml' if p.lower().endswith('.svg') else 'image/png'
    qr_src = f'data:{mime};base64,' + base64.b64encode(open(p, 'rb').read()).decode()
else:
    qr_src = None

qr_block = (f'<img class="qr" src="{qr_src}" alt="Scan to start recording">'
            if qr_src else
            '<div class="qr ph"><div class="phi">QR</div>'
            '<div class="pht">COURT QR HERE</div></div>')

steps_html = ''.join(
    f'''<div class="st">
      <div class="n">{i:02d}</div>
      <div class="tx"><h3>{title}</h3><p>{body}</p></div>
    </div>''' for i, (title, body) in enumerate(STEPS, 1))

CSS = f"""
@font-face{{font-family:'Anton';src:url(data:font/woff2;base64,{anton}) format('woff2');font-display:block}}
@font-face{{font-family:'Mono';font-weight:700;src:url(data:font/woff2;base64,{mono}) format('woff2')}}
@font-face{{font-family:'Archivo';font-weight:800;src:url(data:font/woff2;base64,{arch8}) format('woff2')}}
@font-face{{font-family:'Archivo';font-weight:600;src:url(data:font/woff2;base64,{arch6}) format('woff2')}}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{width:1080px;height:1528px;overflow:hidden;position:relative;color:{CHALK};
  font-family:Archivo,sans-serif;background:
  radial-gradient(ellipse 92% 34% at 50% 0%, rgba(245,101,48,.24), transparent 62%),
  radial-gradient(ellipse 62% 26% at 6% 76%, rgba(245,101,48,.08), transparent 64%),
  linear-gradient(180deg,#0A0B0F 0%,#0E0F13 44%,#08090C 100%)}}
.grid{{position:absolute;inset:0;z-index:0;opacity:.5;
  background-image:linear-gradient(rgba(245,101,48,.05) 1px,transparent 1px),
   linear-gradient(90deg,rgba(245,101,48,.05) 1px,transparent 1px);background-size:46px 46px;
  -webkit-mask-image:radial-gradient(120% 70% at 50% 20%,#000,transparent 88%)}}
.tk{{position:absolute;width:62px;height:62px;z-index:5}}
.tk.tl{{top:38px;left:38px;border-top:5px solid {ORANGE};border-left:5px solid {ORANGE}}}
.tk.br{{bottom:38px;right:38px;border-bottom:5px solid {ORANGE};border-right:5px solid {ORANGE}}}
.z{{position:relative;z-index:4;height:100%;display:flex;flex-direction:column;
  align-items:center;padding:66px 76px 58px}}

.top{{display:flex;align-items:center;gap:18px;align-self:flex-start}}
.top img{{height:88px;filter:drop-shadow(0 0 22px rgba(245,101,48,.4))}}
.top .wm{{font-family:Mono;font-weight:700;font-size:15px;letter-spacing:.24em;color:{STEEL};
  line-height:1.9}}
.top .wm b{{display:block;font-family:Anton;font-size:26px;letter-spacing:.05em;color:{CHALK}}}

h1{{align-self:flex-start;margin-top:26px;font-family:Anton;font-size:96px;line-height:.92;
  letter-spacing:.01em;text-transform:uppercase}}
h1 em{{font-style:normal;color:{ORANGE};text-shadow:0 0 44px rgba(245,101,48,.5)}}
.cam{{height:74px;width:auto;margin-left:26px;vertical-align:-6px;
  filter:drop-shadow(0 0 26px rgba(245,101,48,.55))}}
.by{{align-self:flex-start;margin-top:16px;display:inline-flex;align-items:center;gap:12px;
  padding:10px 20px 8px;background:{ORANGE}}}
.by b{{font-family:Anton;font-size:25px;letter-spacing:.05em;color:#fff}}
.by span{{font-family:Mono;font-weight:700;font-size:13px;letter-spacing:.2em;
  color:rgba(255,255,255,.82)}}

.steps{{width:100%;margin-top:30px}}
.st{{display:flex;gap:24px;align-items:flex-start;padding:20px 0;
  border-bottom:1px solid rgba(244,246,250,.10)}}
.st:last-child{{border-bottom:none}}
.n{{flex:none;width:78px;font-family:Anton;font-size:56px;line-height:.9;color:{ORANGE};
  font-variant-numeric:tabular-nums}}
.tx{{min-width:0}}
.tx h3{{font-family:Anton;font-size:40px;letter-spacing:.02em;line-height:1}}
.tx p{{margin-top:9px;font-weight:600;font-size:24px;line-height:1.4;color:#C3CAD6}}
.tx p em{{font-style:normal;color:{CHALK};font-weight:800}}

.scan{{margin-top:auto;width:100%;display:flex;align-items:center;gap:32px;
  background:rgba(20,22,28,.92);padding:26px 30px;
  background-image:linear-gradient({ORANGE},{ORANGE}),linear-gradient({ORANGE},{ORANGE});
  background-size:26px 3px,3px 26px;background-position:0 0,0 0;background-repeat:no-repeat}}
.panel{{position:relative;width:276px;height:276px;background:{CHALK};padding:26px;flex:none}}
.qr{{width:100%;height:100%;display:block;object-fit:contain;image-rendering:pixelated}}
.qr.ph{{display:flex;flex-direction:column;align-items:center;justify-content:center;
  border:4px dashed rgba(10,12,18,.22)}}
.qr.ph .phi{{font-family:Anton;font-size:64px;color:rgba(10,12,18,.16);line-height:1}}
.qr.ph .pht{{margin-top:10px;font-family:Mono;font-weight:700;font-size:13px;
  letter-spacing:.14em;color:rgba(10,12,18,.45);text-align:center}}
.scan .say{{min-width:0}}
.scan .say b{{display:block;font-family:Anton;font-size:52px;line-height:1;letter-spacing:.02em}}
.scan .say b em{{font-style:normal;color:{ORANGE}}}
.scan .say p{{margin-top:11px;font-weight:600;font-size:22px;line-height:1.4;color:#C3CAD6}}
.scan .say .court{{margin-top:13px;display:inline-block;padding:8px 16px 6px;
  background:{ORANGE};font-family:Mono;font-weight:700;font-size:16px;letter-spacing:.18em;
  color:#fff}}

.foot{{margin-top:26px;width:100%;border-top:1px solid rgba(244,246,250,.14);
  padding:20px 84px 0 0;display:flex;align-items:baseline;justify-content:space-between}}
.foot .u{{font-family:Anton;font-size:30px;letter-spacing:.04em}}
.foot .u em{{font-style:normal;color:{ORANGE}}}
.foot .s{{font-family:Mono;font-weight:700;font-size:14px;letter-spacing:.2em;color:{STEEL}}}
"""

court_html = f'<div class="court">{A.court}</div>' if A.court else ''

HTML = f"""<!doctype html><meta charset="utf-8"><style>{CSS}</style>
<div class="grid"></div><div class="tk tl"></div><div class="tk br"></div>
<div class="z">
  <div class="top">
    <img src="data:image/png;base64,{logo}" alt="Urban Playground">
    <div class="wm"><b>URBAN PLAYGROUND</b>COURT CAMERA</div>
  </div>

  <h1>CAPTURE{CAMERA_SVG}<br>YOUR <em>BEST</em><br>MOMENTS</h1>
  <div class="by"><span>POWERED BY</span><b>SAVE MY PLAY</b></div>

  <div class="steps">{steps_html}</div>

  <div class="scan">
    <div class="panel">{qr_block}</div>
    <div class="say">
      <b>SCAN TO<br><em>START</em></b>
      <p>Point your camera at the code. No app to install.</p>
      {court_html}
    </div>
  </div>

  <div class="foot">
    <div class="u">URBANPADEL<em>.</em>OM</div>
    <div class="s">URBAN PLAYGROUND &middot; OMAN</div>
  </div>
</div>"""

open(f'{SC}/{A.out}.html', 'w').write(HTML)
print(f'built {A.out}.html', f'(url)' if A.url else (f'(qr {A.qr})' if A.qr else '(placeholder)'))
