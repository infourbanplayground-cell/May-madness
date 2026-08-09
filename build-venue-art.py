# -*- coding: utf-8 -*-
"""URBAN PLAYGROUND — venue signage set.

One shared frame, several sheets, so the walls read as one system rather
than as a pile of one-offs. A4 proportions (1080x1528) throughout; render at
3x for print.

  python3 build_venue_art.py --sheet all
  python3 build_venue_art.py --sheet court --n 1
  python3 build_venue_art.py --sheet wifi --ssid "Urban Playground" --wifi-pass "..."

Sheets
  court   giant court numeral, readable across the venue
  rules   house rules
  basics  padel in five points, for first-timers
  book    QR to the booking app
  live    QR to the live series table
  wifi    network name, password, and a real WIFI: join code

WHAT IS AND IS NOT VERIFIED
  · book/live QR targets were checked live before being drawn. bookings
    redirects to /login (307), so that sheet says "sign in or sign up"
    rather than pretending it is a one-tap booking.
  · RULES below are a STARTING POINT, not the venue's actual policy. Read
    them before printing and edit the list; nobody but the owner knows
    whether e.g. non-marking soles are enforced here.
  · wifi renders blank writable rules until --ssid/--wifi-pass are passed.

QR rules as per build_pay_card.py: chalk panel, never dark-on-dark, and a
real quiet zone (border=2 minimum -- border=0 tested undecodable).
"""
import argparse, base64, os, sys

SC = os.path.dirname(os.path.abspath(__file__))
b64f = lambda f: base64.b64encode(open(f'{SC}/{f}', 'rb').read()).decode()

SHEETS = ('court', 'rules', 'basics', 'book', 'live', 'wifi')

ap = argparse.ArgumentParser()
ap.add_argument('--sheet', default='all', choices=SHEETS + ('all',))
ap.add_argument('--n', default='1', help='court number, for --sheet court')
ap.add_argument('--ssid', default=None)
ap.add_argument('--wifi-pass', dest='wifi_pass', default=None)
ap.add_argument('--out', default=None)
A = ap.parse_args()

anton = b64f('anton.woff2');      mono  = b64f('jbmono700.woff2')
arch8 = b64f('archivo800.woff2'); arch6 = b64f('archivo600.woff2')
logo  = b64f('up-logo-clean.png')

ORANGE, CHALK, STEEL = '#F56530', '#F4F6FA', '#8B95A7'

BOOK_URL = 'https://bookings.urbanpadel.om'
LIVE_URL = 'https://attack.urbanpadel.om'

# EDIT ME before printing. These are sensible defaults for a padel club, not
# a transcription of this venue's policy.
RULES = [
    ('NON-MARKING SOLES ONLY',  'Court shoes on court. Black soles leave marks that do not come out.'),
    ('MIND THE GLASS',          'No hanging off the fence, no leaning on the glass, no sitting on the net.'),
    ('FINISH ON TIME',          'Play stops at the end of your slot. The next four are already waiting.'),
    ('TAKE IT WITH YOU',        'Bottles, tape, cans. Bins are by the entrance.'),
    ('BALLS STAY ON COURT',     'Loose balls behind the glass, not underfoot.'),
]

BASICS = [
    ('SCORING IS TENNIS',   '15, 30, 40, game. Six games a set, best of three.'),
    ('SERVE UNDERARM',      'Bounce it behind the line, strike it below your waist, diagonally across.'),
    ('THE WALLS ARE YOURS', 'After the ball bounces on your side it can come off the glass and still be live.'),
    ('BOUNCE FIRST',        'Straight into the glass or the fence without bouncing first is out.'),
    ('PLAY IT OFF THE BACK','Let it come off your own back wall and put it back over. That is the game.')
]


def qr_data_uri(payload):
    import qrcode
    from qrcode.constants import ERROR_CORRECT_M
    q = qrcode.QRCode(error_correction=ERROR_CORRECT_M, box_size=20, border=2)
    q.add_data(payload); q.make(fit=True)
    q.make_image(fill_color='black', back_color='white').convert('L').save(f'{SC}/_v_qr.png')
    return 'data:image/png;base64,' + b64f('_v_qr.png')


def wifi_payload(ssid, pw):
    # WIFI: escaping — ; , : \ and " are special and must be backslash-escaped
    esc = lambda t: ''.join('\\' + c if c in '\\;,:"' else c for c in t)
    return f'WIFI:T:WPA;S:{esc(ssid)};P:{esc(pw)};;'


def panel(uri, note=None):
    inner = (f'<img class="qr" src="{uri}">' if uri else
             '<div class="qr ph"><div class="phi">QR</div></div>')
    n = f'<div class="qn">{note}</div>' if note else ''
    return f'<div class="qwrap"><div class="qp">{inner}</div>{n}</div>'


def numbered(items, accent_title=True):
    return '<div class="list">' + ''.join(
        f'''<div class="li"><div class="ln">{i:02d}</div>
        <div class="lt"><h3>{t}</h3><p>{b}</p></div></div>'''
        for i, (t, b) in enumerate(items, 1)) + '</div>'


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
  align-items:flex-start;padding:66px 76px 58px}}

.top{{display:flex;align-items:center;gap:18px}}
.top img{{height:84px;filter:drop-shadow(0 0 22px rgba(245,101,48,.4))}}
.top .wm{{font-family:Mono;font-weight:700;font-size:15px;letter-spacing:.24em;color:{STEEL};
  line-height:1.9}}
.top .wm b{{display:block;font-family:Anton;font-size:26px;letter-spacing:.05em;color:{CHALK}}}

h1{{margin-top:30px;font-family:Anton;font-size:104px;line-height:.9;text-transform:uppercase}}
h1.sm{{font-size:82px}}
h1 em{{font-style:normal;color:{ORANGE};text-shadow:0 0 44px rgba(245,101,48,.5)}}
.sub{{margin-top:18px;font-weight:600;font-size:27px;line-height:1.4;color:#C3CAD6;max-width:840px}}
.sub b{{color:{CHALK};font-weight:800}}

.list{{width:100%;margin-top:34px;flex:1;display:flex;flex-direction:column;
  justify-content:center}}
.li{{display:flex;gap:28px;align-items:flex-start;padding:26px 0;
  border-bottom:1px solid rgba(244,246,250,.10)}}
.li:last-child{{border-bottom:none}}
.ln{{flex:none;width:88px;font-family:Anton;font-size:62px;line-height:.9;color:{ORANGE};
  font-variant-numeric:tabular-nums}}
.lt h3{{font-family:Anton;font-size:46px;letter-spacing:.02em;line-height:1}}
.lt p{{margin-top:10px;font-weight:600;font-size:27px;line-height:1.4;color:#C3CAD6}}

/* giant court numeral */
.big{{width:100%;flex:1;display:flex;flex-direction:column;align-items:center;
  justify-content:center;gap:52px}}
.big .lab{{font-family:Mono;font-weight:700;font-size:34px;letter-spacing:.42em;
  color:{STEEL};margin-left:.42em}}
.big .num{{font-family:Anton;font-size:620px;line-height:.78;color:{ORANGE};
  text-shadow:0 0 90px rgba(245,101,48,.45);font-variant-numeric:tabular-nums}}

/* QR block */
.qwrap{{margin-top:34px;width:100%;flex:1;display:flex;flex-direction:column;
  align-items:center;justify-content:center}}
.qp{{width:470px;height:470px;background:{CHALK};padding:44px;flex:none}}
.qr{{width:100%;height:100%;display:block;object-fit:contain;image-rendering:pixelated}}
.qr.ph{{height:100%;display:flex;align-items:center;justify-content:center;
  border:4px dashed rgba(10,12,18,.22)}}
.qr.ph .phi{{font-family:Anton;font-size:96px;color:rgba(10,12,18,.16)}}
.qn{{margin-top:20px;font-family:Mono;font-weight:700;font-size:19px;letter-spacing:.14em;
  color:{STEEL};text-align:center}}

/* key/value rows (wifi) */
.kv{{width:100%;margin-top:34px;background:rgba(20,22,28,.92);padding:8px 28px 12px;
  background-image:linear-gradient({ORANGE},{ORANGE}),linear-gradient({ORANGE},{ORANGE});
  background-size:26px 3px,3px 26px;background-position:0 0,0 0;background-repeat:no-repeat}}
.kvr{{display:flex;align-items:baseline;gap:20px;padding:15px 0;
  border-bottom:1px solid rgba(244,246,250,.08)}}
.kvr:last-child{{border-bottom:none}}
.kvr .k{{flex:none;width:200px;font-family:Mono;font-weight:700;font-size:16px;
  letter-spacing:.18em;color:{STEEL}}}
.kvr .v{{flex:1;height:44px;line-height:44px;font-family:Mono;font-weight:700;font-size:36px;
  color:{CHALK};overflow:hidden;text-overflow:ellipsis;white-space:nowrap}}
.kvr .blank{{flex:1;height:44px;border-bottom:3px dotted rgba(244,246,250,.28)}}

.foot{{margin-top:auto;width:100%;border-top:1px solid rgba(244,246,250,.14);
  padding:20px 84px 0 0;display:flex;align-items:baseline;justify-content:space-between}}
.foot .u{{font-family:Anton;font-size:30px;letter-spacing:.04em}}
.foot .u em{{font-style:normal;color:{ORANGE}}}
.foot .s{{font-family:Mono;font-weight:700;font-size:14px;letter-spacing:.2em;color:{STEEL}}}
"""


def shell(kicker, body):
    return f"""<!doctype html><meta charset="utf-8"><style>{CSS}</style>
<div class="grid"></div><div class="tk tl"></div><div class="tk br"></div>
<div class="z">
  <div class="top">
    <img src="data:image/png;base64,{logo}" alt="Urban Playground">
    <div class="wm"><b>URBAN PLAYGROUND</b>{kicker}</div>
  </div>
  {body}
  <div class="foot">
    <div class="u">URBANPADEL<em>.</em>OM</div>
    <div class="s">URBAN PLAYGROUND &middot; OMAN</div>
  </div>
</div>"""


def build(sheet):
    if sheet == 'court':
        body = (f'<div class="big"><div class="lab">COURT</div>'
                f'<div class="num">{A.n}</div></div>')
        return shell('COURT MARKER', body)

    if sheet == 'rules':
        return shell('HOUSE RULES',
            '<h1>HOUSE<br><em>RULES</em></h1>' + numbered(RULES))

    if sheet == 'basics':
        return shell('NEW TO PADEL',
            '<h1 class="sm">PADEL IN<br><em>FIVE</em> POINTS</h1>' + numbered(BASICS))

    if sheet == 'book':
        return shell('BOOK A COURT',
            '<h1>BOOK<br>YOUR <em>COURT</em></h1>'
            '<p class="sub">Scan to open the booking app. '
            '<b>Sign in or create an account</b>, pick your slot, done.</p>'
            + panel(qr_data_uri(BOOK_URL), 'BOOKINGS.URBANPADEL.OM'))

    if sheet == 'live':
        return shell('LIVE TABLE',
            '<h1 class="sm">LIVE TABLE<br>&amp; <em>FIXTURES</em></h1>'
            '<p class="sub">Every result, every ranking, updated as it happens. '
            '<b>No app, no login.</b></p>'
            + panel(qr_data_uri(LIVE_URL), 'ATTACK.URBANPADEL.OM'))

    if sheet == 'wifi':
        have = A.ssid and A.wifi_pass
        rows = (f'<div class="kvr"><span class="k">NETWORK</span>'
                f'{f"<span class=v>{A.ssid}</span>" if A.ssid else "<span class=blank></span>"}</div>'
                f'<div class="kvr"><span class="k">PASSWORD</span>'
                f'{f"<span class=v>{A.wifi_pass}</span>" if A.wifi_pass else "<span class=blank></span>"}</div>')
        uri = qr_data_uri(wifi_payload(A.ssid, A.wifi_pass)) if have else None
        return shell('GUEST WI-FI',
            '<h1>GUEST<br><em>WI-FI</em></h1>'
            f'<div class="kv">{rows}</div>'
            + panel(uri, 'SCAN TO JOIN &middot; NO TYPING' if have
                         else 'RUN WITH --ssid AND --wifi-pass'))

    sys.exit(f'unknown sheet {sheet}')


targets = SHEETS if A.sheet == 'all' else (A.sheet,)
for sh in targets:
    name = A.out or (f'venue-court-{A.n}' if sh == 'court' else f'venue-{sh}')
    open(f'{SC}/{name}.html', 'w').write(build(sh))
    print('built', name + '.html')
