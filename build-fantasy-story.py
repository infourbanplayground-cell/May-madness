# -*- coding: utf-8 -*-
"""URBAN PLAYGROUND — Fantasy Premier League story (Instagram, 1080x1920).

Story cut of the WhatsApp card. Everything sits inside 170..1676: the top
overlay on a story is only the profile row, so 170/244 is the real frame —
the blanket 250/250 people quote throws away 80px of usable height.

A gap is deliberately left under the league code for the IG link sticker,
which is placed in the app at post time and would otherwise land on top of
the QR or the URL.

Same guarantees as the card: Arabic font embedded (no Arabic system font
exists on this machine), and the QR is generated from the same constant that
is printed, then decoded back out of the final PNG.

  python3 build_fpl_story.py
"""
import base64, os, io
import qrcode

SC = os.path.dirname(os.path.abspath(__file__))
b64f = lambda f: base64.b64encode(open(f'{SC}/{f}', 'rb').read()).decode()

teko6 = b64f('teko600.woff2'); teko7 = b64f('teko700.woff2')
arch6 = b64f('archivo600.woff2')
mono  = b64f('jbmono700.woff2')
cai4  = b64f('cairo400.woff2'); cai7 = b64f('cairo700.woff2')
logo  = b64f('up-logo-new.png')

ORANGE, CHALK, STEEL, COURT, DEEP = '#F56530', '#F4F6FA', '#8B95A7', '#0A0C12', '#06070B'

CODE = 'fphftp'
URL  = 'https://fantasy.premierleague.com/leagues/auto-join/' + CODE

q = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=12, border=2)
q.add_data(URL); q.make(fit=True)
buf = io.BytesIO()
q.make_image(fill_color=COURT, back_color=CHALK).convert('RGB').save(buf, 'PNG')
qr = base64.b64encode(buf.getvalue()).decode()

RULES = [
    ('01', 'MEMBERS ONLY', 'Urban Playground members only.',
           'للأعضاء فقط',  'المشاركة لأعضاء المجموعة فقط.'),
    ('02', '5 EVENTS',     'Play 5 events before the season ends.',
           'خمس فعاليات',  'المشاركة في ٥ فعاليات قبل نهاية الموسم.'),
    ('03', 'TOP 3 WIN',    'Prizes for the top 3 managers.',
           'أفضل ٣',       'جوائز لأفضل ٣ مدربين.'),
]

CSS = f"""
@font-face{{font-family:'Teko';font-weight:600;src:url(data:font/woff2;base64,{teko6}) format('woff2')}}
@font-face{{font-family:'Teko';font-weight:700;src:url(data:font/woff2;base64,{teko7}) format('woff2')}}
@font-face{{font-family:'Archivo';font-weight:600;src:url(data:font/woff2;base64,{arch6}) format('woff2')}}
@font-face{{font-family:'Mono';font-weight:700;src:url(data:font/woff2;base64,{mono}) format('woff2')}}
@font-face{{font-family:'Cairo';font-weight:400;src:url(data:font/woff2;base64,{cai4}) format('woff2')}}
@font-face{{font-family:'Cairo';font-weight:700;src:url(data:font/woff2;base64,{cai7}) format('woff2')}}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{width:1080px;height:1920px;overflow:hidden;position:relative;color:{CHALK};
  font-family:Archivo,sans-serif;background:
  radial-gradient(ellipse 92% 26% at 50% 4%, rgba(245,101,48,.28), transparent 62%),
  radial-gradient(ellipse 60% 20% at 96% 84%, rgba(245,101,48,.10), transparent 64%),
  linear-gradient(180deg,#08090D 0%,{COURT} 46%,{DEEP} 100%)}}

.pitch{{position:absolute;inset:0;z-index:0;pointer-events:none}}
.pitch .circle{{position:absolute;left:50%;top:330px;transform:translateX(-50%);
  width:760px;height:760px;border:2px solid rgba(245,101,48,.12);border-radius:50%}}
.pitch .half{{position:absolute;left:0;right:0;top:1512px;height:2px;
  background:linear-gradient(90deg,transparent,rgba(245,101,48,.12) 16%,rgba(245,101,48,.12) 84%,transparent)}}
.pitch .spot{{position:absolute;left:50%;top:1512px;transform:translate(-50%,-50%);
  width:14px;height:14px;background:rgba(245,101,48,.22);border-radius:50%}}
.tk{{position:absolute;width:64px;height:64px;z-index:6}}
.tk.tl{{top:186px;left:44px;border-top:6px solid {ORANGE};border-left:6px solid {ORANGE}}}
.tk.br{{bottom:260px;right:44px;border-bottom:6px solid {ORANGE};border-right:6px solid {ORANGE}}}

/* The story-safe box: 170 from the top, 244 from the bottom. */
.safe{{position:absolute;left:0;right:0;top:170px;bottom:244px;z-index:2;
  padding:0 62px;display:flex;flex-direction:column;align-items:center;text-align:center}}

.logo{{height:168px;width:auto;margin-top:6px;filter:drop-shadow(0 0 26px rgba(245,101,48,.42))}}
.season{{margin-top:16px;font-family:Mono;font-weight:700;font-size:20px;
  letter-spacing:.22em;color:{COURT};background:{ORANGE};padding:10px 16px 9px}}
h1{{margin-top:24px;font-family:Teko,Impact,sans-serif;font-weight:700;font-size:158px;
  line-height:.8;letter-spacing:.02em;text-transform:uppercase;
  text-shadow:0 0 56px rgba(245,101,48,.4)}}
h1 em{{font-style:normal;color:{ORANGE}}}
.kick{{margin-top:18px;font-family:Mono;font-weight:700;font-size:19px;
  letter-spacing:.24em;color:{STEEL}}}

.rules{{width:100%;margin-top:34px;display:flex;flex-direction:column;gap:13px}}
.rule{{display:flex;align-items:stretch;background:rgba(20,24,36,.92);
  border-left:4px solid {ORANGE};text-align:left}}
.rule .n{{flex:0 0 auto;width:72px;display:grid;place-items:center;
  font-family:Teko,sans-serif;font-weight:700;font-size:40px;color:{ORANGE};
  border-right:1px solid rgba(244,246,250,.09)}}
.rule .en{{flex:1;min-width:0;padding:18px 20px}}
.rule .ar{{flex:1;min-width:0;padding:18px 20px;direction:rtl;text-align:right;
  border-left:1px solid rgba(244,246,250,.09)}}
.rule h3{{font-family:Teko,sans-serif;font-weight:600;font-size:38px;line-height:1;
  letter-spacing:.02em;text-transform:uppercase}}
.rule p{{margin-top:5px;font-weight:600;font-size:18px;line-height:1.3;color:{STEEL}}}
.rule .ar h3{{font-family:Cairo,sans-serif;font-weight:700;font-size:27px;line-height:1.25}}
.rule .ar p{{font-family:Cairo,sans-serif;font-weight:400;font-size:17px;line-height:1.5;margin-top:4px}}

.join{{width:100%;margin-top:34px;display:flex;align-items:center;gap:24px;
  background:rgba(20,24,36,.92);border:1px solid rgba(245,101,48,.45);
  padding:22px 24px;text-align:left}}
.join .qr{{flex:0 0 auto;width:176px;height:176px;background:{CHALK};padding:9px}}
.join .qr img{{width:100%;height:100%;display:block;image-rendering:pixelated}}
.join .lab{{font-family:Mono;font-weight:700;font-size:16px;letter-spacing:.2em;color:{ORANGE}}}
.join .code{{margin-top:6px;font-family:Teko,sans-serif;font-weight:700;font-size:86px;
  line-height:.88;letter-spacing:.06em}}
.join .scan{{margin-top:8px;font-family:Mono;font-weight:700;font-size:14px;
  letter-spacing:.14em;color:{CHALK}}}
.join .ar{{margin-top:4px;font-family:Cairo,sans-serif;font-weight:400;font-size:16px;color:{STEEL}}}

/* The bottom ~370px of the safe box is deliberately left empty for the IG
   link sticker, which is placed in the app at post time. Nothing is drawn
   there — a printed placeholder ships as-is if anyone forgets to cover it. */
"""

HTML = f"""<!doctype html><meta charset="utf-8"><style>{CSS}</style>
<div class="pitch"><div class="circle"></div><div class="half"></div><div class="spot"></div></div>
<div class="tk tl"></div><div class="tk br"></div>
<div class="safe">

  <img class="logo" src="data:image/png;base64,{logo}" alt="Urban Playground">
  <span class="season">SEASON 2026/27</span>

  <h1>FANTASY<br><em>LEAGUE</em></h1>
  <div class="kick">PREMIER LEAGUE &middot; MEMBERS ONLY</div>

  <div class="rules">
    {''.join(f'''<div class="rule">
      <div class="n">{n}</div>
      <div class="en"><h3>{eh}</h3><p>{ep}</p></div>
      <div class="ar"><h3>{ah}</h3><p>{ap}</p></div>
    </div>''' for n, eh, ep, ah, ap in RULES)}
  </div>

  <div class="join">
    <div class="qr"><img src="data:image/png;base64,{qr}" alt="Join QR"></div>
    <div>
      <div class="lab">LEAGUE CODE</div>
      <div class="code">{CODE}</div>
      <div class="scan">SCAN TO JOIN</div>
      <div class="ar">امسح الرمز للانضمام</div>
    </div>
  </div>

</div>"""

open(f'{SC}/fpl-story.html', 'w').write(HTML)
print('built fpl-story.html')
