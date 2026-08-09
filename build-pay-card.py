# -*- coding: utf-8 -*-
"""URBAN PLAYGROUND — bank transfer / QR card.

1080x1350. Renders a placeholder by default; pass --qr <file.png> once you
have the real code and the same card comes out ready to print or post.

  python3 build_pay_card.py
  python3 build_pay_card.py --qr bank-qr.png --bank "Bank Muscat" \
      --account "Urban Playground LLC" --iban "OM00 0000 0000 0000 0000 00"
  python3 build_pay_card.py --amount 7 --unit "PER PLAYER, PER SESSION"
  python3 build_pay_card.py --brand attack --out pay-card-attack

Two brands, because this card outlives any one series:

  up      (default) the house mark. White + Urban orange #F56530, sampled
          out of up-logo-new.png rather than guessed. Good for any payment.
  attack  the Vol.6 skin — AUGUST ATTACK wordmark, Attack Red, cyan support.

Two things about the QR panel are not decoration and should not be restyled:

  · it is CHALK on a dark card, not dark-on-dark. A scanner needs real
    contrast, and inverted QR codes are unsupported by some readers outright.
  · the panel carries 48px of blank margin on every side. That is the
    "quiet zone" the QR spec requires; art that crowds it breaks scanning
    even when the code itself is perfect.

The corner ticks INSIDE the panel are drawn in the margin, clear of the code
area, so they read as registration marks without eating the quiet zone.

Verify a real code survives the render — don't eyeball it:
  cv2.QRCodeDetector().detectAndDecodeMulti(<the final 1080x1350 png>)

Brand assets live on the server, not in this repo (DESIGN.md §3). Fetch and
trim the house mark before the first run — the shipped file carries 250px of
transparent padding that would otherwise throw off every width set below:

  scp urbanpadel:/var/www/urbanpadel.om/public/assets/up-logo-new.png .
  python3 -c "from PIL import Image; im=Image.open('up-logo-new.png').convert('RGBA'); \
    im.crop(im.split()[3].getbbox()).save('up-logo-clean.png')"
"""
import argparse, base64, os, sys

SC = os.path.dirname(os.path.abspath(__file__))
b64f = lambda f: base64.b64encode(open(f'{SC}/{f}', 'rb').read()).decode()

ap = argparse.ArgumentParser()
ap.add_argument('--brand',   default='up', choices=('up', 'attack'))
ap.add_argument('--qr',      default=None, help='PNG/SVG of the real QR code')
ap.add_argument('--amount',  default=None, help='omit for a card with no price')
ap.add_argument('--unit',    default='PER PLAYER, PER SESSION')
ap.add_argument('--bank',    default=None)
ap.add_argument('--account', default=None)
ap.add_argument('--mobile',  default=None, help='mobile-transfer number')
ap.add_argument('--alias',   default=None, help='bank alias, e.g. name@BANK')
ap.add_argument('--iban',    default=None)
ap.add_argument('--out',     default='pay-card')
A = ap.parse_args()

anton  = b64f('anton.woff2');      mono  = b64f('jbmono700.woff2')
arch8  = b64f('archivo800.woff2'); arch6 = b64f('archivo600.woff2')

CHALK, STEEL = '#F4F6FA', '#8B95A7'

if A.brand == 'up':
    ACCENT, SUPPORT = '#F56530', '#F56530'   # house brand runs on one colour
    COURT, DEEP     = '#0E0F13', '#08090C'
    LOGO, LOGO_W    = b64f('up-logo-clean.png'), 190
    URL, STRAP      = 'URBANPADEL<em>.</em>OM', 'URBAN PLAYGROUND &middot; OMAN'
else:
    ACCENT, SUPPORT = '#FF2E43', '#3DE1FF'
    COURT, DEEP     = '#0A0C12', '#06070B'
    LOGO, LOGO_W    = b64f('aa-wordmark-clean.png'), 360
    URL, STRAP      = 'ATTACK<em>.</em>URBANPADEL<em>.</em>OM', 'URBAN SOCIAL SERIES &middot; VOL.6'

# Only the routes you actually supply get a row. With nothing supplied the
# card falls back to a blank form -- dotted rules you can write on -- which is
# what makes the placeholder useful before any details exist.
ROUTES = [('BANK', A.bank), ('ACCOUNT NAME', A.account), ('MOBILE', A.mobile),
          ('ALIAS', A.alias), ('IBAN', A.iban)]
BLANK_FORM = [l for l, _ in ROUTES if l != 'IBAN']

def field(label, value):
    inner = f'<span class="v">{value}</span>' if value else '<span class="blank"></span>'
    return f'<div class="fr"><span class="l">{label}</span>{inner}</div>'

if any(v for _, v in ROUTES):
    rows_html = ''.join(field(l, v) for l, v in ROUTES if v)
else:
    rows_html = ''.join(field(l, None) for l in BLANK_FORM)

if A.qr:
    p = A.qr if os.path.isabs(A.qr) else f'{SC}/{A.qr}'
    if not os.path.exists(p):
        sys.exit(f'no such QR file: {p}')
    mime = 'image/svg+xml' if p.lower().endswith('.svg') else 'image/png'
    src  = f'data:{mime};base64,' + base64.b64encode(open(p, 'rb').read()).decode()
    qr_block = f'<img class="qr" src="{src}" alt="Bank transfer QR">'
else:
    qr_block = ('<div class="qr ph"><div class="phi">QR</div>'
                '<div class="pht">DROP THE BANK QR HERE</div>'
                '<div class="phs">1024 &times; 1024 PNG &middot; KEEP IT SQUARE</div></div>')

hexrgb = lambda h: ','.join(str(int(h[i:i+2], 16)) for i in (1, 3, 5))
AGLOW, SGLOW = hexrgb(ACCENT), hexrgb(SUPPORT)

CSS = f"""
@font-face{{font-family:'Anton';src:url(data:font/woff2;base64,{anton}) format('woff2');font-display:block}}
@font-face{{font-family:'Mono';font-weight:700;src:url(data:font/woff2;base64,{mono}) format('woff2')}}
@font-face{{font-family:'Archivo';font-weight:800;src:url(data:font/woff2;base64,{arch8}) format('woff2')}}
@font-face{{font-family:'Archivo';font-weight:600;src:url(data:font/woff2;base64,{arch6}) format('woff2')}}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{width:1080px;height:1350px;overflow:hidden;position:relative;color:{CHALK};
  font-family:Archivo,sans-serif;background:
  radial-gradient(ellipse 90% 40% at 50% 0%, rgba({AGLOW},.22), transparent 62%),
  radial-gradient(ellipse 60% 30% at 8% 72%, rgba({SGLOW},.09), transparent 64%),
  linear-gradient(180deg,#0A0B0F 0%,{COURT} 46%,{DEEP} 100%)}}
.grid{{position:absolute;inset:0;z-index:0;opacity:.5;
  background-image:linear-gradient(rgba({AGLOW},.05) 1px,transparent 1px),
   linear-gradient(90deg,rgba({AGLOW},.05) 1px,transparent 1px);background-size:46px 46px;
  -webkit-mask-image:radial-gradient(120% 74% at 50% 22%,#000,transparent 88%)}}
.tk{{position:absolute;width:60px;height:60px;z-index:5}}
.tk.tl{{top:36px;left:36px;border-top:5px solid {SUPPORT};border-left:5px solid {SUPPORT}}}
.tk.br{{bottom:36px;right:36px;border-bottom:5px solid {ACCENT};border-right:5px solid {ACCENT}}}
.z{{position:relative;z-index:4;height:100%;display:flex;flex-direction:column;
  align-items:center;padding:44px 70px 46px}}

.logo{{width:{LOGO_W}px;filter:drop-shadow(0 0 30px rgba({AGLOW},.38))}}
.kick{{margin-top:16px;display:inline-flex;align-items:center;gap:13px;
  padding:12px 26px 10px;background:{ACCENT};box-shadow:0 0 44px rgba({AGLOW},.5)}}
.kick b{{font-family:Anton;font-size:34px;letter-spacing:.07em;color:#fff}}
.kick i{{width:10px;height:10px;background:#fff;border-radius:50%;display:block}}

.amt{{margin-top:16px;text-align:center;line-height:.85}}
.amt b{{font-family:Anton;font-size:82px;color:{CHALK};
  text-shadow:0 0 40px rgba({AGLOW},.45);font-variant-numeric:tabular-nums}}
.amt b em{{font-style:normal;font-size:.42em;color:{ACCENT};margin-left:10px}}
.amt span{{display:block;margin-top:12px;font-family:Mono;font-weight:700;font-size:16px;
  letter-spacing:.2em;color:{STEEL}}}

/* QR panel — chalk ground and a real quiet zone, see the module docstring */
.panel{{position:relative;margin-top:16px;width:430px;height:430px;background:{CHALK};
  padding:48px;flex:none;box-shadow:0 0 70px rgba({SGLOW},.16)}}
.panel .rt{{position:absolute;width:26px;height:26px;z-index:2}}
.panel .rt.a{{top:12px;left:12px;border-top:4px solid {ACCENT};border-left:4px solid {ACCENT}}}
.panel .rt.b{{top:12px;right:12px;border-top:4px solid {ACCENT};border-right:4px solid {ACCENT}}}
.panel .rt.c{{bottom:12px;left:12px;border-bottom:4px solid {ACCENT};border-left:4px solid {ACCENT}}}
.panel .rt.d{{bottom:12px;right:12px;border-bottom:4px solid {ACCENT};border-right:4px solid {ACCENT}}}
.qr{{width:100%;height:100%;display:block;object-fit:contain;image-rendering:pixelated}}
.qr.ph{{display:flex;flex-direction:column;align-items:center;justify-content:center;
  border:4px dashed rgba(10,12,18,.22);background:rgba(10,12,18,.03)}}
.qr.ph .phi{{font-family:Anton;font-size:104px;color:rgba(10,12,18,.16);line-height:1}}
.qr.ph .pht{{margin-top:16px;font-family:Mono;font-weight:700;font-size:19px;
  letter-spacing:.16em;color:rgba(10,12,18,.5);text-align:center}}
.qr.ph .phs{{margin-top:9px;font-family:Mono;font-weight:700;font-size:13px;
  letter-spacing:.13em;color:rgba(10,12,18,.32);text-align:center}}

.or{{display:flex;align-items:center;gap:14px;width:100%;margin:22px 0 12px}}
.or b{{font-family:Mono;font-weight:700;font-size:13px;letter-spacing:.3em;color:{ACCENT};
  white-space:nowrap}}
.or i{{flex:1;height:1px;background:rgba(244,246,250,.14)}}

.fields{{width:100%;background:rgba(20,22,28,.92);padding:8px 24px 10px;
  background-image:linear-gradient({SUPPORT},{SUPPORT}),linear-gradient({SUPPORT},{SUPPORT});
  background-size:24px 3px,3px 24px;background-position:0 0,0 0;background-repeat:no-repeat}}
.fr{{display:flex;align-items:baseline;gap:18px;padding:9px 0;
  border-bottom:1px solid rgba(244,246,250,.07)}}
.fr:last-child{{border-bottom:none}}
.fr .l{{flex:none;width:190px;font-family:Mono;font-weight:700;font-size:14px;
  letter-spacing:.16em;color:{STEEL}}}
.fr .v{{flex:1;height:28px;line-height:28px;font-family:Mono;font-weight:700;font-size:22px;letter-spacing:.04em;
  color:{CHALK};overflow:hidden;text-overflow:ellipsis;white-space:nowrap}}
.fr .blank{{flex:1;height:28px;border-bottom:2px dotted rgba(244,246,250,.26)}}

.ref{{width:100%;margin-top:14px;margin-bottom:auto;text-align:center;font-family:Mono;
  font-weight:700;font-size:16px;letter-spacing:.11em;color:{CHALK}}}
.ref em{{font-style:normal;color:{ACCENT}}}

.foot{{margin-top:20px;width:100%;border-top:1px solid rgba(244,246,250,.14);
  padding-top:18px;text-align:center}}
.foot .u{{font-family:Anton;font-size:34px;letter-spacing:.04em}}
.foot .u em{{font-style:normal;color:{ACCENT}}}
.foot .s{{margin-top:7px;font-family:Mono;font-weight:700;font-size:13px;
  letter-spacing:.2em;color:{STEEL}}}
"""

amount_html = (f'<div class="amt"><b>{A.amount}<em>OMR</em></b><span>{A.unit}</span></div>'
               if A.amount else '')

HTML = f"""<!doctype html><meta charset="utf-8"><style>{CSS}</style>
<div class="grid"></div><div class="tk tl"></div><div class="tk br"></div>
<div class="z">
  <img class="logo" src="data:image/png;base64,{LOGO}" alt="Urban Playground">
  <div class="kick"><i></i><b>SCAN TO PAY</b></div>
  {amount_html}

  <div class="panel">
    <div class="rt a"></div><div class="rt b"></div>
    <div class="rt c"></div><div class="rt d"></div>
    {qr_block}
  </div>

  <div class="or"><b>OR TRANSFER TO</b><i></i></div>
  <div class="fields">{rows_html}</div>
  <div class="ref">SEND YOUR <em>NAME</em> WITH THE TRANSFER</div>

  <div class="foot">
    <div class="u">{URL}</div>
    <div class="s">{STRAP}</div>
  </div>
</div>"""

open(f'{SC}/{A.out}.html', 'w').write(HTML)
print(f'built {A.out}.html  brand={A.brand}',
      '(placeholder)' if not A.qr else f'(QR: {A.qr})')
