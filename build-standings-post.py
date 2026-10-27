# -*- coding: utf-8 -*-
"""Blackout Vol.8 — the standings post, with two nights to go.

Four cards at 1080x1350 plus a 1080x1920 story:

  standings-1-table.png   the table after seven nights
  standings-2-math.png    why it is still open: the gap, and the biggest night
  standings-3-form.png    the form player
  standings-4-nights.png  what is left, and what it is worth
  standings-story.png     the whole thing on one tall card

EVERY FIGURE COMES FROM `ops/blackout-standings.mjs`, which lifts the app's own
scoring engine out of blackout-index.html and runs it over the live state. No
number here is typed, so a post cannot advertise a total the leaderboard
contradicts.

IT NEVER SAYS WHAT A DOUBLED NIGHT IS WORTH IN POINTS. 2X applies to everything
except the streak bonus, so "the best night was +33, doubled that is +66" is
close, and close is how a post ends up contradicting the app. It prints the
biggest night actually recorded and lets the reader do the arithmetic — the
same discipline the final-week film works under.

  ssh urbanpadel 'curl -s localhost:3009/state' > $SP/bo.json
  node ops/blackout-standings.mjs $SP/bo.json $SP/bo-standings.json
  python3 build-standings-post.py && node render-standings-post.mjs
"""
import datetime, json, os, sys
from importlib.machinery import SourceFileLoader

HERE = os.path.dirname(os.path.abspath(__file__))
SP = "/tmp/claude-0/-home-user-May-madness/0e44f0ad-a683-5f0d-9de6-9459ae328963/scratchpad"
OUT = os.path.join(HERE, "brand", "blackout", "posts")
DATA = os.path.join(SP, "bo-standings.json")

# The card shell — faces, wash, scanlines, shrink-to-fit — is the announcement
# post's. Two copies of it is how two posts drift apart.
_ann = SourceFileLoader("announce_post",
                        os.path.join(HERE, "build-announce-post.py")).load_module()
head, footer, MARK_B64 = _ann.head, _ann.footer, _ann.MARK_B64
LIME, MAGENTA, INK, MUTED, DIM = _ann.LIME, _ann.MAGENTA, _ann.INK, _ann.MUTED, _ann.DIM

DAYS = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]
MONS = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN",
        "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]


def d(iso):
    return datetime.date.fromisoformat(iso)


def short(iso):
    x = d(iso)
    return f"{DAYS[x.weekday()]} {x.day} {MONS[x.month - 1]}"


def rows(table, n):
    """The table as HTML rows. Nights played is on every row because it is the
    whole shape of this table — third place has played five, the two above him
    have played seven, and without that column the standings read as a simple
    ladder when they are not."""
    out = []
    for i, r in enumerate(table[:n]):
        lit = i < 3
        out.append(
            f'<div class="row">'
            f'<span class="pos" style="color:{LIME if lit else MUTED}">{i + 1}</span>'
            f'<span class="who"><span class="nm" data-fit="470">'
            f'{r["name"].upper()}</span></span>'
            f'<span class="np">{r["nights"]}N</span>'
            f'<span class="pts" style="color:{LIME if lit else INK}">{r["pts"]}</span>'
            f'</div>')
    return "\n".join(out)


CSS = f"""
.row{{display:flex;align-items:center;gap:22px;height:94px;
      border-bottom:3px solid rgba(242,242,242,.09)}}
.row .pos{{font-family:'JetBrains Mono',monospace;font-weight:700;font-size:30px;
      width:52px;flex:0 0 52px}}
.row .who{{flex:1;min-width:0}}
.row .nm{{display:inline-block;font-style:italic;
      font-variation-settings:'wdth' 104,'wght' 900;font-size:46px;white-space:nowrap}}
.row .np{{font-family:'JetBrains Mono',monospace;font-weight:700;font-size:21px;
      letter-spacing:.14em;color:{DIM};flex:0 0 auto}}
.row .pts{{font-style:italic;font-variation-settings:'wdth' 112,'wght' 900;
      font-size:58px;line-height:1;width:150px;text-align:right;flex:0 0 150px}}
.big{{font-style:italic;font-variation-settings:'wdth' 125,'wght' 900;line-height:.86}}
.note{{font-family:'JetBrains Mono',monospace;font-weight:700;font-size:25px;
      line-height:1.5;color:{_ann.MUTED}}}
.dbl{{border:4px solid {MAGENTA};background:rgba(255,46,136,.10);
      display:flex;flex-direction:column;align-items:center;justify-content:center}}
"""


def shell(w, h):
    return head(w, h).replace("</style>", CSS + "</style>")


def card_table(c, w, h):
    return shell(w, h) + f"""
<div class="bar" style="top:0;height:9px"></div>
<div class="bar" style="bottom:0;height:5px"></div>
<div style="position:absolute;left:70px;top:72px;width:92px;height:92px">
  <img src="data:image/svg+xml;base64,{MARK_B64}" style="width:100%;display:block">
</div>
<div class="k" style="position:absolute;left:184px;top:92px;font-size:21px">BLACKOUT &middot; VOL.8</div>
<div class="m" style="position:absolute;left:184px;top:128px;font-size:21px;letter-spacing:.18em">
  AFTER {c['played']} OF {c['sessionsTotal']} NIGHTS</div>
<div style="position:absolute;left:70px;top:206px"><span class="big" data-fit="940"
  style="display:inline-block;font-size:150px;white-space:nowrap">STANDINGS</span></div>
<div style="position:absolute;left:70px;right:70px;top:388px">
{rows(c['table'], 8)}
</div>
<div class="dbl" style="position:absolute;left:70px;right:70px;top:1176px;height:104px">
  <div class="big" style="font-size:50px;color:{MAGENTA}">TWO NIGHTS LEFT</div>
  <div class="m" style="font-size:21px;letter-spacing:.2em;color:{INK};margin-top:7px">
    {' &middot; '.join(short(x) for x in c['remaining'])} &middot; BOTH DOUBLE</div>
</div>
{footer(1304)}"""


def card_math(c, w, h):
    """The argument for reading the table at all: it is not settled. Both
    figures are measured — the gap is first minus fourth, and the best night is
    the biggest single night anyone has actually recorded. What two doubled
    nights add up to is deliberately left to the reader."""
    return shell(w, h) + f"""
<div class="bar" style="top:0;height:9px"></div>
<div class="bar" style="bottom:0;height:5px"></div>
<div class="k ctr" style="top:96px;font-size:22px">STILL ANYBODY&rsquo;S</div>

<div class="ctr" style="top:188px"><span class="big" data-fit="{w-140}"
  style="display:inline-block;font-size:250px;color:{LIME}">{c['gap14']}</span></div>
<div class="m ctr" style="top:452px;font-size:26px;letter-spacing:.2em;color:{INK}">
  POINTS BETWEEN 1ST AND 4TH</div>

<div style="position:absolute;left:170px;right:170px;top:548px;height:3px;
  background:rgba(242,242,242,.14)"></div>

<div class="ctr" style="top:606px"><span class="big" data-fit="{w-140}"
  style="display:inline-block;font-size:250px">+{c['bestNight']}</span></div>
<div class="m ctr" style="top:870px;font-size:26px;letter-spacing:.2em;color:{INK}">
  THE BIGGEST NIGHT ANYONE HAS HAD</div>

<div class="dbl" style="position:absolute;left:70px;right:70px;top:1000px;height:200px">
  <div class="big" style="font-size:72px;color:{MAGENTA}">BOTH LEFT</div>
  <div class="big" style="font-size:72px;color:{MAGENTA}">ARE DOUBLE</div>
</div>
<div class="m ctr" style="top:1240px;font-size:23px;letter-spacing:.2em;color:{MUTED}">
  {' &nbsp;&middot;&nbsp; '.join(short(x) for x in c['remaining'])}</div>
{footer(1304)}"""


def card_form(c, w, h):
    f = c['form']
    return shell(w, h) + f"""
<div class="bar" style="top:0;height:9px"></div>
<div class="bar" style="bottom:0;height:5px"></div>
<div class="k ctr" style="top:96px;font-size:22px">FORM</div>
<div class="ctr" style="top:168px"><span class="big" data-fit="{w-120}"
  style="display:inline-block;font-size:112px;white-space:nowrap">{f['name'].upper()}</span></div>

<div class="ctr" style="top:330px"><span class="big" data-fit="{w-120}"
  style="display:inline-block;font-size:124px;color:{LIME};white-space:nowrap">
  {f['finals']} FINALS</span></div>
<div class="ctr" style="top:462px"><span class="big" data-fit="{w-120}"
  style="display:inline-block;font-size:124px;color:{LIME};white-space:nowrap">
  {f['titles']} WINS</span></div>

<div style="position:absolute;left:70px;right:70px;top:664px;display:flex">
  <div style="flex:1;text-align:center">
    <div class="big" style="font-size:96px">{f['nights']}</div>
    <div class="m" style="font-size:21px;letter-spacing:.18em;margin-top:10px">NIGHTS</div></div>
  <div style="flex:1;text-align:center;border-left:3px solid rgba(242,242,242,.12);
       border-right:3px solid rgba(242,242,242,.12)">
    <div class="big" style="font-size:96px">{f['pts']}</div>
    <div class="m" style="font-size:21px;letter-spacing:.18em;margin-top:10px">POINTS</div></div>
  <div style="flex:1;text-align:center">
    <div class="big" style="font-size:96px;color:{LIME}">{f['rank']}</div>
    <div class="m" style="font-size:21px;letter-spacing:.18em;margin-top:10px">IN THE SERIES</div></div>
</div>

<div class="note ctr" style="top:900px;left:100px;right:100px;font-size:27px;color:{INK}">
  {f['line']}</div>

<div class="dbl" style="position:absolute;left:70px;right:70px;top:1100px;height:180px">
  <div class="big" style="font-size:58px;color:{MAGENTA}">TWO NIGHTS LEFT</div>
  <div class="m" style="font-size:21px;letter-spacing:.2em;color:{INK};margin-top:10px">
    BOTH WORTH DOUBLE</div>
</div>
{footer(1304)}"""


def card_nights(c, w, h):
    a, b = (short(x) for x in c['remaining'])
    return shell(w, h) + f"""
<div class="bar" style="top:0;height:9px"></div>
<div class="bar" style="bottom:0;height:5px"></div>
<div class="k ctr" style="top:96px;font-size:22px">WHAT IS LEFT</div>
<div class="ctr" style="top:176px"><span class="big" data-fit="{w-120}"
  style="display:inline-block;font-size:150px">TWO NIGHTS</span></div>

<div class="dbl" style="position:absolute;left:70px;right:70px;top:400px;height:240px">
  <div class="m" style="font-size:22px;letter-spacing:.22em;color:{INK}">SESSION {c['played'] + 1}</div>
  <div class="big" style="font-size:96px;color:{MAGENTA};margin-top:8px">{a}</div>
</div>
<div class="dbl" style="position:absolute;left:70px;right:70px;top:672px;height:240px">
  <div class="m" style="font-size:22px;letter-spacing:.22em;color:{INK}">SESSION {c['sessionsTotal']} &middot; FINALS NIGHT</div>
  <div class="big" style="font-size:96px;color:{MAGENTA};margin-top:8px">{b}</div>
</div>

<div class="ctr" style="top:966px"><span class="big"
  style="font-size:92px;color:{MAGENTA}">BOTH DOUBLE</span></div>
<div class="note ctr" style="top:1080px;left:100px;right:100px;font-size:26px;color:{INK}">
  Season top three take {' / '.join(str(p) for p in c['seasonPrizes'])} OMR.<br>
  {c['entry']} OMR a night. Everyone is still in it.</div>
{footer(1304)}"""


def card_story(c, w, h):
    return shell(w, h) + f"""
<div class="bar" style="top:0;height:11px"></div>
<div class="bar" style="bottom:0;height:7px"></div>
<div style="position:absolute;left:50%;top:214px;width:104px;height:104px;margin-left:-52px">
  <img src="data:image/svg+xml;base64,{MARK_B64}" style="width:100%;display:block">
</div>
<div class="k ctr" style="top:356px;font-size:22px">BLACKOUT &middot; VOL.8 &middot; AFTER {c['played']} OF {c['sessionsTotal']}</div>
<div class="ctr" style="top:412px"><span class="big" data-fit="{w-120}"
  style="display:inline-block;font-size:142px;white-space:nowrap">STANDINGS</span></div>

<div style="position:absolute;left:84px;right:84px;top:600px">
{rows(c['table'], 6)}
</div>

<div class="ctr" style="top:1222px"><span class="big"
  style="font-size:150px;color:{LIME}">{c['gap14']}</span></div>
<div class="m ctr" style="top:1392px;font-size:24px;letter-spacing:.2em;color:{INK}">
  POINTS BETWEEN 1ST AND 4TH</div>

<div class="dbl" style="position:absolute;left:84px;right:84px;top:1400px;height:196px">
  <div class="big" style="font-size:62px;color:{MAGENTA}">TWO NIGHTS LEFT</div>
  <div class="m" style="font-size:22px;letter-spacing:.2em;color:{INK};margin-top:12px">
    {' &middot; '.join(short(x) for x in c['remaining'])}</div>
  <div class="m" style="font-size:22px;letter-spacing:.2em;color:{MAGENTA};margin-top:6px">
    BOTH WORTH DOUBLE</div>
</div>
<div class="m ctr" style="top:1626px;font-size:23px;letter-spacing:.2em;color:{MUTED}">
  {c['host'].upper()}</div>
{footer(1668)}"""


CAPTIONS = """BLACKOUT VOL.8 — STANDINGS, TWO NIGHTS TO GO
{dash}

WHATSAPP — the standings post

{wa}

WHATSAPP — short, for the day of

{wa2}

INSTAGRAM — carousel caption

{ig}

CARD ORDER
  1  standings-1-table    the table after {played} nights
  2  standings-2-math     {gap} points, and the biggest night anyone has had
  3  standings-3-form     {formname}
  4  standings-4-nights   what is left and what it is worth
  S  standings-story      one tall card for status
"""


def captions(c):
    t = c['table']
    f = c['form']
    a, b = (short(x) for x in c['remaining'])
    lead = t[0]['pts'] - t[1]['pts']
    wa = (
        f"*BLACKOUT VOL.8 — AFTER {c['played']} OF {c['sessionsTotal']} NIGHTS*\n\n"
        + "\n".join(f"{i+1}. {r['name']} — {r['pts']}" for i, r in enumerate(t[:6]))
        + f"\n\n{c['gap14']} points separate 1st from 4th.\n"
        f"The biggest night anyone has had is +{c['bestNight']}.\n\n"
        f"*Two nights left — {a} and {b} — and both are worth DOUBLE.*\n\n"
        f"{f['name']}: {f['finals']} finals, {f['titles']} wins, {f['nights']} nights. "
        f"Everyone above him has played {t[0]['nights']}.\n\n"
        f"{c['entry']} OMR a night. Season top three take "
        f"{' / '.join(str(p) for p in c['seasonPrizes'])} OMR.\n"
        f"{c['host']}")
    wa2 = (f"*{a.title()} — Session {c['played'] + 1}. Double points.*\n\n"
           f"{t[0]['name']} leads on {t[0]['pts']}, {lead} clear. "
           f"{c['gap14']} covers the top four.\n"
           f"Two nights left and both count twice.\n\n{c['host']}")
    ig = (f"Seven nights down, two to go — and both are worth double. "
          f"{c['gap14']} points separate 1st from 4th, and the biggest night "
          f"anyone has had all season is +{c['bestNight']}. Do the maths.\n\n"
          f"{a} · {b}\n"
          f"#urbanplayground #blackoutseries #padel #muscat #oman")
    return CAPTIONS.format(dash="=" * 44, wa=wa, wa2=wa2, ig=ig,
                           played=c['played'], gap=c['gap14'], formname=f['name'])


def main():
    if not os.path.exists(DATA):
        sys.exit(f"missing {DATA}\n"
                 f"  ssh urbanpadel 'curl -s localhost:3009/state' > {SP}/bo.json\n"
                 f"  node ops/blackout-standings.mjs {SP}/bo.json {DATA}")
    c = json.load(open(DATA))

    if len(c['remaining']) != 2:
        print(f"NOTE: {len(c['remaining'])} nights remain, not two — "
              f"the copy on these cards says TWO NIGHTS LEFT.", file=sys.stderr)
        sys.exit("refusing to build a post that would be wrong on its own headline")
    if set(c['remaining']) != set(c['doubleNights']):
        sys.exit("refusing: the cards say both remaining nights are double, "
                 "and the season file does not agree")

    # The form player: whoever has won the most finals per night played, among
    # those still in the top of the table. It is picked from the data rather
    # than named here, so next week's post does not quietly keep this week's
    # story after the facts have moved.
    top = c['table'][:6]
    f = max(top, key=lambda r: (r['titles'] / max(r['nights'], 1), r['titles']))
    rank = c['table'].index(f) + 1
    ORD = {1: "1ST", 2: "2ND", 3: "3RD"}
    busiest = max(r['nights'] for r in c['table'][:rank - 1]) if rank > 1 else f['nights']
    line = (f"Everyone above him has played {busiest}."
            if rank > 1 and busiest > f['nights'] else
            f"Off {f['nights']} nights.")
    c['form'] = dict(name=f['name'], finals=f['finals'], titles=f['titles'],
                     nights=f['nights'], pts=f['pts'],
                     rank=ORD.get(rank, f"{rank}TH"), line=line)

    os.makedirs(OUT, exist_ok=True)
    pages = {
        "standings-1-table": card_table(c, 1080, 1350),
        "standings-2-math": card_math(c, 1080, 1350),
        "standings-3-form": card_form(c, 1080, 1350),
        "standings-4-nights": card_nights(c, 1080, 1350),
        "standings-story": card_story(c, 1080, 1920),
    }
    for name, html in pages.items():
        with open(os.path.join(OUT, name + ".html"), "w") as fh:
            fh.write(html)
        print(f"built {name}.html")

    with open(os.path.join(OUT, "STANDINGS-CAPTIONS.txt"), "w") as fh:
        fh.write(captions(c))
    print("built STANDINGS-CAPTIONS.txt")

    print(f"\nafter {c['played']} of {c['sessionsTotal']}  ·  "
          f"{c['table'][0]['name']} {c['table'][0]['pts']}  ·  "
          f"gap 1st-4th {c['gap14']}  ·  best night +{c['bestNight']}")
    print(f"form: {c['form']['name']} — {c['form']['line']}")
    print(f"left: {', '.join(short(x) for x in c['remaining'])}  (both double)")
    print("\nnow render:  node render-standings-post.mjs")


if __name__ == "__main__":
    main()
