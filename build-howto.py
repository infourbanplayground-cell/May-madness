# -*- coding: utf-8 -*-
"""AUGUST ATTACK — "see your own rank" explainer card for the players' group.

1080x1350 (4:5) — the tallest ratio WhatsApp will show in a chat without
cropping the ends off, so nobody has to tap to read it.

The three panels are real screenshots of the shipped app, cropped to the part
each step is about. A mocked-up diagram would drift from the app the first time
anything changed; these cannot.

  python3 build_howto.py
"""
import base64, os

SC = os.path.dirname(os.path.abspath(__file__))
b64 = lambda f: base64.b64encode(open(f'{SC}/{f}', 'rb').read()).decode()

anton = b64('anton.woff2')
arch6 = b64('archivo600.woff2'); arch8 = b64('archivo800.woff2')
mono  = b64('jbmono700.woff2')
word  = b64('aa-wordmark-clean.png')

RED, ICE, CHALK, STEEL, COURT = '#FF2E43', '#3DE1FF', '#F4F6FA', '#8B95A7', '#0A0C12'

STEPS = [
    ('01', 'OPEN THE APP',   'Tap <b>&ldquo;Which one are you?&rdquo;</b> at the top of the Home screen.', 'step1-c.png'),
    ('02', 'PICK YOUR NAME', 'Search the list and tap yourself. Saved on your phone only.',                'step2-c.png'),
    ('03', 'THAT&rsquo;S IT',      'Home now opens on <b>your</b> rank, points and movement.',             'step3-c.png'),
]

CSS = f"""
@font-face{{font-family:'Anton';src:url(data:font/woff2;base64,{anton}) format('woff2')}}
@font-face{{font-family:'Mono';font-weight:700;src:url(data:font/woff2;base64,{mono}) format('woff2')}}
@font-face{{font-family:'Archivo';font-weight:600;src:url(data:font/woff2;base64,{arch6}) format('woff2')}}
@font-face{{font-family:'Archivo';font-weight:800;src:url(data:font/woff2;base64,{arch8}) format('woff2')}}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{width:1080px;height:1350px;overflow:hidden;position:relative;color:{CHALK};
  font-family:Archivo,sans-serif;background:
  radial-gradient(ellipse 92% 34% at 50% 0%, rgba(255,46,67,.30), transparent 62%),
  radial-gradient(ellipse 62% 26% at 6% 86%, rgba(61,225,255,.10), transparent 64%),
  linear-gradient(180deg,#08090D 0%,{COURT} 46%,#06070B 100%)}}
.grid{{position:absolute;inset:0;z-index:0;opacity:.45;
  background-image:linear-gradient(rgba(255,46,67,.055) 1px,transparent 1px),
   linear-gradient(90deg,rgba(255,46,67,.055) 1px,transparent 1px);background-size:48px 48px;
  -webkit-mask-image:radial-gradient(120% 62% at 50% 14%,#000,transparent 88%)}}
.tk{{position:absolute;width:60px;height:60px;z-index:6}}
.tk.tl{{top:40px;left:40px;border-top:5px solid {ICE};border-left:5px solid {ICE}}}
.tk.br{{bottom:40px;right:40px;border-bottom:5px solid {RED};border-right:5px solid {RED}}}

.wrap{{position:relative;z-index:2;padding:64px 60px 54px;
  height:100%;display:flex;flex-direction:column}}

.top{{display:flex;align-items:center;justify-content:space-between;gap:20px}}
.top img{{height:52px;width:auto;filter:drop-shadow(0 0 22px rgba(255,46,67,.45))}}
.new{{font-family:Mono;font-weight:700;font-size:17px;letter-spacing:.22em;
  color:#0A0C12;background:{RED};padding:9px 14px 8px}}

h1{{margin-top:30px;font-family:Anton;font-size:112px;line-height:.9;
  letter-spacing:.02em;text-shadow:0 0 56px rgba(255,46,67,.42)}}
h1 em{{font-style:normal;color:{RED}}}
.sub{{margin-top:20px;font-weight:600;font-size:27px;line-height:1.42;color:#C9CFDA;max-width:900px}}
.sub b{{color:{CHALK};font-weight:800}}

.steps{{display:flex;gap:24px;margin-top:44px}}
.st{{flex:1;min-width:0;display:flex;flex-direction:column}}
.shot{{width:100%;aspect-ratio:860/1250;overflow:hidden;background:#06070B;
  border:1px solid rgba(244,246,250,.14);
  background-size:cover;background-position:top center}}
.no{{margin-top:18px;font-family:Mono;font-weight:700;font-size:16px;
  letter-spacing:.2em;color:{RED}}}
.hd{{margin-top:8px;font-family:Anton;font-size:36px;line-height:1.02;letter-spacing:.02em}}
.tx{{margin-top:9px;font-weight:600;font-size:20px;line-height:1.4;color:{STEEL}}}
.tx b{{color:#C9CFDA;font-weight:800}}

.foot{{margin-top:auto;border-top:1px solid rgba(255,46,67,.42);padding-top:24px;
  display:flex;align-items:baseline;justify-content:space-between;gap:20px}}
.foot .url{{font-family:Anton;font-size:40px;letter-spacing:.03em}}
.foot .url em{{font-style:normal;color:{RED}}}
.foot .note{{font-family:Mono;font-weight:700;font-size:16px;letter-spacing:.13em;
  color:{STEEL};text-align:right;line-height:1.7}}
"""

HTML = f"""<!doctype html><meta charset="utf-8"><style>{CSS}</style>
<div class="grid"></div><div class="tk tl"></div><div class="tk br"></div>
<div class="wrap">

  <div class="top">
    <img src="data:image/png;base64,{word}" alt="August Attack">
    <span class="new">NEW</span>
  </div>

  <h1>SEE YOUR<br><em>OWN RANK</em></h1>
  <div class="sub">The app can now follow <b>you</b> &mdash; your points, your movement,
    your place in the table. <b>One tap to set up.</b> No account, no password.</div>

  <div class="steps">
    {''.join(f'''<div class="st">
      <div class="shot" style="background-image:url(data:image/png;base64,{b64(img)})"></div>
      <div class="no">{n}</div>
      <div class="hd">{hd}</div>
      <div class="tx">{tx}</div>
    </div>''' for n, hd, tx, img in STEPS)}
  </div>

  <div class="foot">
    <span class="url">ATTACK<em>.</em>URBANPADEL<em>.</em>OM</span>
    <span class="note">SAVED ON YOUR PHONE ONLY<br>SHARING A PHONE? TAP &ldquo;NOT YOU?&rdquo;</span>
  </div>

</div>"""

open(f'{SC}/howto.html', 'w').write(HTML)
print('built howto.html')
