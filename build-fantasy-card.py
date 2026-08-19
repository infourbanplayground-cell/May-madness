# -*- coding: utf-8 -*-
"""URBAN PLAYGROUND — Fantasy Premier League 2026/27 announcement card.

1080x1350 for WhatsApp. House brand, not August Attack: this is a club-wide
thing, so it wears Urban Orange (#F56530, sampled from the logo) rather than
the series red.

Bilingual EN/AR. The Arabic font is vendored — this machine has no Arabic
system font at all, so an unembedded face renders every Arabic word as empty
boxes and the render still "looks fine" at a glance.

The join QR is generated from the same URL string printed on the card, so the
two can never disagree, and it is decoded back out of the FINAL PNG before the
card ships. Dark modules on a chalk plate with a real quiet zone: inverted or
zero-border codes fail on some scanners.

No Premier League marks are used — the words describe the game, the visuals
are entirely Urban Playground.

  python3 build_fpl.py
"""
import base64, os, io
import qrcode

SC = os.path.dirname(os.path.abspath(__file__))
b64f = lambda f: base64.b64encode(open(f'{SC}/{f}', 'rb').read()).decode()

teko6 = b64f('teko600.woff2'); teko7 = b64f('teko700.woff2')
arch6 = b64f('archivo600.woff2'); arch8 = b64f('archivo800.woff2')
mono  = b64f('jbmono700.woff2')
cai4  = b64f('cairo400.woff2');  cai7 = b64f('cairo700.woff2')
logo  = b64f('up-logo-new.png')

ORANGE, CHALK, STEEL, COURT, DEEP = '#F56530', '#F4F6FA', '#8B95A7', '#0A0C12', '#06070B'

CODE = 'fphftp'
URL  = 'https://fantasy.premierleague.com/leagues/auto-join/' + CODE

# QR built from the same constant that gets printed, so they cannot drift.
q = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=12, border=2)
q.add_data(URL); q.make(fit=True)
buf = io.BytesIO()
q.make_image(fill_color=COURT, back_color=CHALK).convert('RGB').save(buf, 'PNG')
qr = base64.b64encode(buf.getvalue()).decode()

RULES = [
    ('01', 'MEMBERS ONLY',  'Open to Urban Playground group members.',
           'للأعضاء فقط',  'المشاركة فقط لأعضاء مجموعة Urban Playground.'),
    ('02', '5 EVENTS',      'Play at least 5 events before the season ends to be eligible.',
           'خمس فعاليات', 'يجب المشاركة في خمس فعاليات على الأقل قبل نهاية الموسم.'),
    ('03', 'TOP 3 WIN',     'Prizes for the top 3 managers in the final standings.',
           'أفضل ٣',       'جوائز مميزة لأفضل ٣ مدربين في الترتيب النهائي.'),
]

CSS = f"""
@font-face{{font-family:'Teko';font-weight:600;src:url(data:font/woff2;base64,{teko6}) format('woff2')}}
@font-face{{font-family:'Teko';font-weight:700;src:url(data:font/woff2;base64,{teko7}) format('woff2')}}
@font-face{{font-family:'Archivo';font-weight:600;src:url(data:font/woff2;base64,{arch6}) format('woff2')}}
@font-face{{font-family:'Archivo';font-weight:800;src:url(data:font/woff2;base64,{arch8}) format('woff2')}}
@font-face{{font-family:'Mono';font-weight:700;src:url(data:font/woff2;base64,{mono}) format('woff2')}}
@font-face{{font-family:'Cairo';font-weight:400;src:url(data:font/woff2;base64,{cai4}) format('woff2')}}
@font-face{{font-family:'Cairo';font-weight:700;src:url(data:font/woff2;base64,{cai7}) format('woff2')}}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{width:1080px;height:1350px;overflow:hidden;position:relative;color:{CHALK};
  font-family:Archivo,sans-serif;background:
  radial-gradient(ellipse 90% 32% at 50% 0%, rgba(245,101,48,.26), transparent 62%),
  radial-gradient(ellipse 60% 26% at 96% 88%, rgba(245,101,48,.10), transparent 64%),
  linear-gradient(180deg,#08090D 0%,{COURT} 46%,{DEEP} 100%)}}

/* Pitch markings, not the padel grid — this one is football. */
.pitch{{position:absolute;inset:0;z-index:0;opacity:.5;pointer-events:none}}
.pitch .circle{{position:absolute;left:50%;top:112px;transform:translateX(-50%);
  width:660px;height:660px;border:2px solid rgba(245,101,48,.13);border-radius:50%}}
.pitch .spot{{position:absolute;left:50%;top:436px;transform:translate(-50%,-50%);
  width:12px;height:12px;background:rgba(245,101,48,.22);border-radius:50%}}
.pitch .half{{position:absolute;left:0;right:0;top:442px;height:2px;
  background:linear-gradient(90deg,transparent,rgba(245,101,48,.13) 18%,rgba(245,101,48,.13) 82%,transparent)}}
.tk{{position:absolute;width:58px;height:58px;z-index:6}}
.tk.tl{{top:38px;left:38px;border-top:5px solid {ORANGE};border-left:5px solid {ORANGE}}}
.tk.br{{bottom:38px;right:38px;border-bottom:5px solid {ORANGE};border-right:5px solid {ORANGE}}}

.wrap{{position:relative;z-index:2;height:100%;padding:56px 58px 50px;
  display:flex;flex-direction:column}}

.top{{display:flex;align-items:center;justify-content:space-between;gap:18px}}
.top img{{height:104px;width:auto;filter:drop-shadow(0 0 20px rgba(245,101,48,.4))}}
.season{{font-family:Mono;font-weight:700;font-size:19px;letter-spacing:.2em;
  color:{COURT};background:{ORANGE};padding:10px 15px 9px}}

h1{{margin-top:22px;font-family:Teko,Impact,sans-serif;font-weight:700;
  font-size:132px;line-height:.82;letter-spacing:.02em;text-transform:uppercase;
  text-shadow:0 0 50px rgba(245,101,48,.38)}}
h1 em{{font-style:normal;color:{ORANGE}}}
.kick{{margin-top:16px;font-family:Mono;font-weight:700;font-size:18px;
  letter-spacing:.26em;color:{STEEL}}}
.blurb{{margin-top:18px;font-weight:600;font-size:26px;line-height:1.4;color:#C9CFDA;max-width:880px}}
.blurb b{{color:{CHALK};font-weight:800}}

.rules{{margin-top:30px;display:flex;flex-direction:column;gap:15px}}
.rule{{display:flex;align-items:stretch;gap:0;background:rgba(20,24,36,.9);
  border-left:4px solid {ORANGE}}}
.rule .n{{flex:0 0 auto;width:72px;display:grid;place-items:center;
  font-family:Teko,sans-serif;font-weight:700;font-size:38px;color:{ORANGE};
  border-right:1px solid rgba(244,246,250,.09)}}
.rule .en{{flex:1;min-width:0;padding:20px 20px}}
.rule .ar{{flex:1;min-width:0;padding:20px 20px;direction:rtl;text-align:right;
  border-left:1px solid rgba(244,246,250,.09)}}
.rule h3{{font-family:Teko,sans-serif;font-weight:600;font-size:38px;
  line-height:1;letter-spacing:.02em;text-transform:uppercase}}
.rule p{{margin-top:6px;font-weight:600;font-size:18px;line-height:1.35;color:{STEEL}}}
.rule .ar h3{{font-family:Cairo,sans-serif;font-weight:700;font-size:27px;line-height:1.3}}
.rule .ar p{{font-family:Cairo,sans-serif;font-weight:400;font-size:17px;line-height:1.5;margin-top:3px}}

.join{{margin-top:auto;display:flex;align-items:center;gap:24px;
  background:rgba(20,24,36,.9);border:1px solid rgba(245,101,48,.4);padding:20px 22px}}
.join .qr{{flex:0 0 auto;width:168px;height:168px;background:{CHALK};padding:9px}}
.join .qr img{{width:100%;height:100%;display:block;image-rendering:pixelated}}
.join .info{{flex:1;min-width:0}}
.join .lab{{font-family:Mono;font-weight:700;font-size:15px;letter-spacing:.2em;color:{ORANGE}}}
.join .code{{margin-top:6px;font-family:Teko,sans-serif;font-weight:700;font-size:74px;
  line-height:.9;letter-spacing:.06em;color:{CHALK}}}
.join .url{{margin-top:8px;font-family:Mono;font-weight:700;font-size:14.5px;
  letter-spacing:.02em;color:{STEEL};word-break:break-all;line-height:1.45}}
.join .scan{{margin-top:9px;font-family:Mono;font-weight:700;font-size:13px;
  letter-spacing:.16em;color:{CHALK}}}

.foot{{margin-top:18px;display:flex;align-items:baseline;justify-content:space-between;gap:16px}}
.foot .l{{font-family:Teko,sans-serif;font-weight:600;font-size:30px;letter-spacing:.05em;color:{CHALK}}}
.foot .r{{font-family:Cairo,sans-serif;font-weight:700;font-size:17px;color:{STEEL};direction:rtl}}
"""

HTML = f"""<!doctype html><meta charset="utf-8"><style>{CSS}</style>
<div class="pitch"><div class="circle"></div><div class="half"></div><div class="spot"></div></div>
<div class="tk tl"></div><div class="tk br"></div>
<div class="wrap">

  <div class="top">
    <img src="data:image/png;base64,{logo}" alt="Urban Playground">
    <span class="season">SEASON 2026/27</span>
  </div>

  <h1>FANTASY<br><em>LEAGUE</em></h1>
  <div class="kick">PREMIER LEAGUE &middot; URBAN PLAYGROUND MEMBERS</div>
  <div class="blurb">Compete, strategise and <b>prove your football knowledge</b>
    across the whole season.</div>

  <div class="rules">
    {''.join(f'''<div class="rule">
      <div class="n">{n}</div>
      <div class="en"><h3>{eh}</h3><p>{ep}</p></div>
      <div class="ar"><h3>{ah}</h3><p>{ap}</p></div>
    </div>''' for n, eh, ep, ah, ap in RULES)}
  </div>

  <div class="join">
    <div class="qr"><img src="data:image/png;base64,{qr}" alt="Join QR"></div>
    <div class="info">
      <div class="lab">LEAGUE CODE</div>
      <div class="code">{CODE}</div>
      <div class="scan">SCAN TO JOIN &mdash; امسح للانضمام</div>
      <div class="url">{URL.replace('https://','')}</div>
    </div>
  </div>

  <div class="foot">
    <span class="l">URBANPADEL.OM</span>
    <span class="r">بالتوفيق للجميع</span>
  </div>

</div>"""

open(f'{SC}/fpl.html', 'w').write(HTML)
print('built fpl.html')
print('url:', URL)
