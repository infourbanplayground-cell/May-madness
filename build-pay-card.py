# -*- coding: utf-8 -*-
"""AUGUST ATTACK — bank transfer / QR card.

1080x1350. Renders a placeholder by default; pass --qr <file.png> once you
have the real code and the same card comes out ready to print or post.

  python3 build_pay_card.py
  python3 build_pay_card.py --qr bank-qr.png --bank "Bank Muscat" \
      --account "Urban Playground LLC" --iban "OM00 0000 0000 0000 0000 00"

Two things about the QR panel are not decoration and should not be restyled:

  · it is CHALK on a court-black card, not black-on-black. A scanner needs
    real contrast, and dark-on-dark QR codes fail on cheap phone cameras.
  · the panel carries ~48px of blank margin on every side. That is the
    "quiet zone" the QR spec requires; art that crowds it breaks scanning
    even when the code itself is perfect.

The corner ticks INSIDE the panel are drawn in the margin, clear of the
code area, so they read as registration marks without eating the quiet zone.
"""
import argparse, base64, os, sys

SC = os.path.dirname(os.path.abspath(__file__))
b64f = lambda f: base64.b64encode(open(f'{SC}/{f}', 'rb').read()).decode()

ap = argparse.ArgumentParser()
ap.add_argument('--qr',      default=None, help='PNG/SVG of the real QR code')
ap.add_argument('--amount',  default='7',  help='empty string hides the amount block')
ap.add_argument('--unit',    default='PER PLAYER, PER SESSION')
ap.add_argument('--bank',    default=None)
ap.add_argument('--account', default=None)
ap.add_argument('--iban',    default=None)
ap.add_argument('--out',     default='pay-card')
A = ap.parse_args()

anton  = b64f('anton.woff2');     mono  = b64f('jbmono700.woff2')
arch8  = b64f('archivo800.woff2'); arch6 = b64f('archivo600.woff2')
word   = b64f('aa-wordmark-clean.png'); emblem = b64f('aa-emblem.png')

RED, ICE, CHALK, STEEL, COURT = '#FF2E43', '#3DE1FF', '#F4F6FA', '#8B95A7', '#0A0C12'

# Unset fields render as a dotted rule you can write on — the card is useful
# as a printed form before anybody has typed the details in.
def field(label, value):
    inner = (f'<span class="v">{value}</span>' if value
             else '<span class="blank"></span>')
    return f'<div class="fr"><span class="l">{label}</span>{inner}</div>'

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

CSS = f"""
@font-face{{font-family:'Anton';src:url(data:font/woff2;base64,{anton}) format('woff2');font-display:block}}
@font-face{{font-family:'Mono';font-weight:700;src:url(data:font/woff2;base64,{mono}) format('woff2')}}
@font-face{{font-family:'Archivo';font-weight:800;src:url(data:font/woff2;base64,{arch8}) format('woff2')}}
@font-face{{font-family:'Archivo';font-weight:600;src:url(data:font/woff2;base64,{arch6}) format('woff2')}}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{width:1080px;height:1350px;overflow:hidden;position:relative;color:{CHALK};
  font-family:Archivo,sans-serif;background:
  radial-gradient(ellipse 90% 40% at 50% 0%, rgba(255,46,67,.26), transparent 62%),
  radial-gradient(ellipse 60% 30% at 8% 72%, rgba(61,225,255,.10), transparent 64%),
  linear-gradient(180deg,#08090D 0%,{COURT} 46%,#06070B 100%)}}
.grid{{position:absolute;inset:0;z-index:0;opacity:.5;
  background-image:linear-gradient(rgba(255,46,67,.055) 1px,transparent 1px),
   linear-gradient(90deg,rgba(255,46,67,.055) 1px,transparent 1px);background-size:46px 46px;
  -webkit-mask-image:radial-gradient(120% 74% at 50% 22%,#000,transparent 88%)}}
.tk{{position:absolute;width:60px;height:60px;z-index:5}}
.tk.tl{{top:36px;left:36px;border-top:5px solid {ICE};border-left:5px solid {ICE}}}
.tk.br{{bottom:36px;right:36px;border-bottom:5px solid {RED};border-right:5px solid {RED}}}
.z{{position:relative;z-index:4;height:100%;display:flex;flex-direction:column;
  align-items:center;padding:60px 70px 50px}}

.word{{width:360px;filter:drop-shadow(0 0 28px rgba(255,46,67,.42))}}
.kick{{margin-top:14px;display:inline-flex;align-items:center;gap:13px;
  padding:12px 26px 10px;background:{RED};box-shadow:0 0 44px rgba(255,46,67,.5)}}
.kick b{{font-family:Anton;font-size:34px;letter-spacing:.07em;color:#fff}}
.kick i{{width:10px;height:10px;background:#fff;border-radius:50%;display:block}}

.amt{{margin-top:18px;text-align:center;line-height:.85}}
.amt b{{font-family:Anton;font-size:86px;color:{CHALK};
  text-shadow:0 0 40px rgba(255,46,67,.45);font-variant-numeric:tabular-nums}}
.amt b em{{font-style:normal;font-size:.42em;color:{RED};margin-left:10px}}
.amt span{{display:block;margin-top:12px;font-family:Mono;font-weight:700;font-size:16px;
  letter-spacing:.2em;color:{STEEL}}}

/* QR panel — chalk ground and a real quiet zone, see the module docstring */
.panel{{position:relative;margin-top:18px;width:500px;height:500px;background:{CHALK};
  padding:48px;flex:none;box-shadow:0 0 70px rgba(61,225,255,.16)}}
.panel .rt{{position:absolute;width:26px;height:26px;z-index:2}}
.panel .rt.a{{top:12px;left:12px;border-top:4px solid {RED};border-left:4px solid {RED}}}
.panel .rt.b{{top:12px;right:12px;border-top:4px solid {RED};border-right:4px solid {RED}}}
.panel .rt.c{{bottom:12px;left:12px;border-bottom:4px solid {RED};border-left:4px solid {RED}}}
.panel .rt.d{{bottom:12px;right:12px;border-bottom:4px solid {RED};border-right:4px solid {RED}}}
.qr{{width:100%;height:100%;display:block;object-fit:contain;image-rendering:pixelated}}
.qr.ph{{display:flex;flex-direction:column;align-items:center;justify-content:center;
  border:4px dashed rgba(10,12,18,.22);background:rgba(10,12,18,.03)}}
.qr.ph .phi{{font-family:Anton;font-size:104px;color:rgba(10,12,18,.16);line-height:1}}
.qr.ph .pht{{margin-top:16px;font-family:Mono;font-weight:700;font-size:19px;
  letter-spacing:.16em;color:rgba(10,12,18,.5);text-align:center}}
.qr.ph .phs{{margin-top:9px;font-family:Mono;font-weight:700;font-size:13px;
  letter-spacing:.13em;color:rgba(10,12,18,.32);text-align:center}}

.or{{display:flex;align-items:center;gap:14px;width:100%;margin:20px 0 12px}}
.or b{{font-family:Mono;font-weight:700;font-size:13px;letter-spacing:.3em;color:{RED};
  white-space:nowrap}}
.or i{{flex:1;height:1px;background:rgba(244,246,250,.14)}}

.fields{{width:100%;background:rgba(16,20,32,.92);padding:8px 24px 10px;
  background-image:linear-gradient({ICE},{ICE}),linear-gradient({ICE},{ICE});
  background-size:24px 3px,3px 24px;background-position:0 0,0 0;background-repeat:no-repeat}}
.fr{{display:flex;align-items:baseline;gap:18px;padding:11px 0;
  border-bottom:1px solid rgba(244,246,250,.07)}}
.fr:last-child{{border-bottom:none}}
.fr .l{{flex:none;width:190px;font-family:Mono;font-weight:700;font-size:14px;
  letter-spacing:.16em;color:{STEEL}}}
.fr .v{{flex:1;font-family:Mono;font-weight:700;font-size:22px;letter-spacing:.04em;
  color:{CHALK};overflow:hidden;text-overflow:ellipsis;white-space:nowrap}}
.fr .blank{{flex:1;height:22px;border-bottom:2px dotted rgba(244,246,250,.26)}}

.ref{{width:100%;margin-top:14px;margin-bottom:auto;text-align:center;font-family:Mono;
  font-weight:700;font-size:16px;letter-spacing:.11em;color:{CHALK}}}
.ref em{{font-style:normal;color:{ICE}}}

.foot{{margin-top:18px;display:flex;align-items:center;justify-content:space-between;width:100%}}
.foot .u{{font-family:Anton;font-size:32px;letter-spacing:.03em}}
.foot .u em{{font-style:normal;color:{RED}}}
.foot .s{{margin-top:5px;font-family:Mono;font-weight:700;font-size:12px;
  letter-spacing:.18em;color:{STEEL}}}
.foot img{{height:96px;filter:drop-shadow(0 0 18px rgba(255,46,67,.5))}}
"""

amount_html = (f'''<div class="amt"><b>{A.amount}<em>OMR</em></b>
    <span>{A.unit}</span></div>''' if A.amount else '')

HTML = f"""<!doctype html><meta charset="utf-8"><style>{CSS}</style>
<div class="grid"></div><div class="tk tl"></div><div class="tk br"></div>
<div class="z">
  <img class="word" src="data:image/png;base64,{word}" alt="August Attack">
  <div class="kick"><i></i><b>SCAN TO PAY</b></div>
  {amount_html}

  <div class="panel">
    <div class="rt a"></div><div class="rt b"></div>
    <div class="rt c"></div><div class="rt d"></div>
    {qr_block}
  </div>

  <div class="or"><b>OR TRANSFER TO</b><i></i></div>
  <div class="fields">
    {field('BANK', A.bank)}
    {field('ACCOUNT NAME', A.account)}
    {field('IBAN', A.iban)}
  </div>
  <div class="ref">SEND YOUR <em>NAME</em> WITH THE TRANSFER</div>

  <div class="foot">
    <div>
      <div class="u">ATTACK<em>.</em>URBANPADEL<em>.</em>OM</div>
      <div class="s">URBAN SOCIAL SERIES &middot; VOL.6</div>
    </div>
    <img src="data:image/png;base64,{emblem}" alt="Urban Playground">
  </div>
</div>"""

open(f'{SC}/{A.out}.html', 'w').write(HTML)
print(f'built {A.out}.html', '(placeholder)' if not A.qr else f'(QR: {A.qr})')
