# -*- coding: utf-8 -*-
"""The UPRISING infographic — one page that explains the whole format.

1080x1350 for the feed and 1080x1920 for a story. Same content; the story gets
the deeper top and bottom padding Instagram's own chrome demands (it draws over
roughly the top 170px and the reply bar over the bottom 200px).

EVERY FIGURE IS READ OUT OF THE SHIPPED ENGINE, none is typed. `brand/uprising/
format-card.html` was hand-written, and CLAUDE.md carried a standing note to
"re-check them against the RULES screen when the defaults move" — which is a
note that a thing can be wrong, not a thing that cannot be. The defaults then
moved: a night became 12 rounds on the board rather than 15, and the card still
advertised "up to 15 matches" and "leave with ten" when the engine says 11
matches each at 16 on 4 courts. This builder runs `ops/uprising-facts.mjs`, the
same source the announcement and the sign-up list read, so the court count, the
points table, the round count, the running time and whether the final doubles
all come from `uprising-engine.js` and cannot disagree with the app.

Three things it DERIVES rather than states, because each is only true for some
set-ups and a poster that keeps saying them after they stop being true is worse
than one that never said them:

  - "A win on Court 3 is worth the same as a loss on Court 1" — printed only
    when WIN[3] really does equal LOSE[1].
  - The double final — printed only when nobody rests, which is the engine's
    own condition for it.
  - "Leave with N" — N is matches each, and it is only a flat number when the
    schedule is even. When it is not, the card says so instead of rounding.

  python3 build-uprising-infographic.py
  node ops/render-uprising-infographic.mjs
"""
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "brand", "uprising")
SOCIAL = os.path.join(HERE, "uprising-social.json")

# DESIGN.md §2c: volt leads, ultraviolet is the second voice. Volt is 14.4:1 on
# the void and ultraviolet 5.8:1, which is Blackout's own lime/magenta split in
# a different hue — a violet lead would break every solid accent surface.
VOLT = "#00F5C8"
UV = "#9D6BFF"
VOID = "#06060A"
CREAM = "#F2F0F7"
MUTED = "#9A95A8"
MUTED2 = "#8A84A2"

SIZES = {"feed": (1080, 1350, 60, 54), "story": (1080, 1920, 196, 214)}

ORDINAL = ("", "one", "two", "three", "four", "five", "six",
           "seven", "eight", "nine", "ten", "eleven", "twelve")


def facts():
    """The format, straight out of the engine."""
    r = subprocess.run([ "node", os.path.join(HERE, "ops", "uprising-facts.mjs") ],
                       capture_output=True, text=True, cwd=HERE)
    if r.returncode != 0:
        raise SystemExit("ops/uprising-facts.mjs failed:\n" + (r.stderr or r.stdout))
    f = json.loads(r.stdout)
    if f["courts"] < 2:
        raise SystemExit(f"the engine reports {f['courts']} courts — there is no ladder to draw")
    for c in range(1, f["courts"] + 1):
        if str(c) not in f["win"] or str(c) not in f["lose"]:
            raise SystemExit(f"no points table for Court {c}; the engine and the card disagree")
    return f


def check_promise(social, f):
    """The tagline names a number, and the engine is what decides it.

    `promise` in uprising-social.json read "Come alone. Leave with ten." — true
    when a night was fifteen rounds on three courts, and wrong the moment the
    default moved to twelve rounds on four, where everyone plays eleven. It is
    hand-written and nothing checked it, which is the same hole the rest of this
    builder exists to close: the card would have printed "eleven matches, eleven
    different partners" nine lines above "Leave with ten".

    So the number in the tagline is checked against the engine and the build
    refuses rather than shipping a card that contradicts itself. The tagline
    stays in the JSON, because it is the series' line and the captions and the
    landing panel use it too — this only stops it drifting.
    """
    if not f["even"]:
        return
    want = int(f["matches"])
    text = social.get("promise", "")
    for i, w in enumerate(ORDINAL):
        if i and re.search(rf"\b{w}\b", text, re.I) and i != want:
            fixed = re.sub(rf"\b{w}\b", ORDINAL[want], text, flags=re.I)
            raise SystemExit(
                f'uprising-social.json "promise" says "{text}", but the engine '
                f'gives {want} matches each.\n'
                f'  The card would print "{ORDINAL[want]} matches, {ORDINAL[want]} different '
                f'partners" and then contradict itself in the footer.\n'
                f'  Set it to: "{fixed}"')
    m = re.search(r"\b(\d+)\b", text)
    if m and int(m.group(1)) != want:
        raise SystemExit(f'uprising-social.json "promise" says {m.group(1)}, '
                         f'the engine gives {want} matches each')


def hhmm(minutes):
    h, m = divmod(int(minutes), 60)
    return f"{h}h{m:02d}" if m else f"{h}h"


def rung_note(c, courts, f):
    if c == 1:
        return "The top. Winners stay."
    if c == courts:
        return "The bottom. Only one way to go."
    # Printed only when it is arithmetically true of the table that shipped.
    if f["win"][str(c)] == f["lose"]["1"]:
        return f"A win here banks what a loss on Court 1 does."
    return f"Win here and you are on Court {c - 1} next round."


def ladder(f):
    courts = f["courts"]
    out = []
    for c in range(1, courts + 1):
        top = " top" if c == 1 else ""
        out.append(
            f'<div class="rung{top}">'
            f'<span class="cn">COURT {c}</span>'
            f'<span class="note">{rung_note(c, courts, f)}</span>'
            f'<span class="pts"><b>{f["win"][str(c)]}</b><i> / {f["lose"][str(c)]}</i></span>'
            f'</div>')
        if c == 1:
            out.append('<div class="mid"><span class="up">&#9650; Winners move up</span>'
                       '<span class="dn">Losers move down &#9660;</span></div>')
    return "\n".join(out)


def timeline(f):
    """The night as a strip of rounds — the thing a list of rules cannot show.

    The shuffle scoring nothing and the last round counting double are the two
    facts people get wrong, and both are about WHERE in the night you are. A
    pip per round says it in one look; the old card said it in two paragraphs
    four boxes apart.
    """
    n = f["rounds"]
    shuffle_n = n - f["scoring"]
    pips = []
    for i in range(1, n + 1):
        if i <= shuffle_n:
            pips.append(f'<span class="pip sh"><i>{i}</i></span>')
        elif i == n and f["doubleFinal"]:
            pips.append(f'<span class="pip x2"><i>{i}</i><u>&times;2</u></span>')
        else:
            pips.append(f'<span class="pip"><i>{i}</i></span>')
    keys = [f'<span class="k sh">{"Shuffle" if shuffle_n == 1 else f"{shuffle_n} shuffle rounds"}'
            f' &middot; scores nothing</span>',
            f'<span class="k">{f["scoring"]} scoring rounds</span>']
    if f["doubleFinal"]:
        keys.append('<span class="k x2">Last round counts double</span>')
    return ('<div class="strip">' + "".join(pips) + "</div>\n"
            '<div class="keys">' + "".join(keys) + "</div>")


def leave_with(f):
    """What you actually get out of the night, and it is not the round count.

    Rounds and matches-each are the same number only when nobody rests. The old
    card advertised the round count as matches, which at 16 on 3 courts
    overstates it by two thirds.
    """
    m = f["matches"]
    if f["even"]:
        n = int(m)
        word = ORDINAL[n] if n < len(ORDINAL) else str(n)
        return f"{n}", f"{word.capitalize()} matches, {word} different partners."
    return f"~{m:.1f}", "Matches each, within one — the court time does not divide evenly."


def card(f, social, size):
    w, h, pad_t, pad_b = SIZES[size]
    courts = f["courts"]
    n_each, each_line = leave_with(f)
    double_line = (" <b>The last round counts double.</b>" if f["doubleFinal"] else
                   f" <b>{f['resting']} rest each round</b>, so the table ranks on points per round.")
    rest_fact = ("Nobody sits out" if f["resting"] == 0
                 else f"{f['resting']} rest a round")

    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8" />
<link href="../fonts/fonts.css" rel="stylesheet" />
<style>
  :root{{
    --volt-rgb:0,245,200; --uv-rgb:157,107,255; --cream-rgb:242,240,247;
    --volt:{VOLT}; --uv:{UV}; --ink:{VOID}; --cream:{CREAM};
    --muted:{MUTED}; --muted2:{MUTED2};
    --line:rgba(var(--cream-rgb),.12); --neon:rgba(var(--volt-rgb),.55);
    --grain:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='160' height='160'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.9' numOctaves='2' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E");
  }}
  *{{margin:0;padding:0;box-sizing:border-box;}}
  html,body{{width:{w}px;height:{h}px;}}
  body{{position:relative;overflow:hidden;background:{VOID};color:var(--cream);
    font-family:'Archivo',system-ui,sans-serif;-webkit-font-smoothing:antialiased;}}
  .wash{{position:absolute;inset:0;background:
      radial-gradient(ellipse 90% 55% at 12% 4%,rgba(var(--uv-rgb),.17),transparent),
      radial-gradient(ellipse 80% 55% at 92% 8%,rgba(var(--volt-rgb),.15),transparent),
      radial-gradient(ellipse 70% 50% at 50% 100%,rgba(var(--volt-rgb),.10),transparent),
      linear-gradient(180deg,#030305,{VOID} 58%,#04040A);}}
  .grid{{position:absolute;inset:0;background-image:
      linear-gradient(rgba(var(--volt-rgb),.05) 1px,transparent 1px),
      linear-gradient(90deg,rgba(var(--volt-rgb),.05) 1px,transparent 1px);
    background-size:60px 60px;}}
  .grain{{position:absolute;inset:0;opacity:.26;mix-blend-mode:overlay;background-image:var(--grain);}}
  .pad{{position:relative;padding:{pad_t}px 64px {pad_b}px;height:100%;
    display:flex;flex-direction:column;justify-content:space-between;}}

  .disp{{font-family:'Archivo';font-style:italic;font-variation-settings:'wdth' 125,'wght' 900;
    text-transform:uppercase;letter-spacing:.01em;}}

  .top{{display:flex;align-items:center;gap:16px;}}
  .mark{{width:46px;height:46px;border:1px solid var(--neon);background:rgba(var(--volt-rgb),.12);
    display:flex;align-items:center;justify-content:center;}}
  .top .nm{{font-size:30px;}}
  .top .sub{{margin-left:auto;font-family:'JetBrains Mono',monospace;font-size:12px;font-weight:700;
    letter-spacing:.3em;color:var(--uv);text-transform:uppercase;}}

  /* The headline does NOT scale with the canvas. A story is taller, not wider,
     so scaling the type with the height sent CLIMB TO COURT ONE onto three
     lines in a 1080px box — the extra room belongs to the gaps between the
     blocks, which space-between already spends for us. */
  h1{{font-size:96px;line-height:.86;margin-top:38px;}}
  h1 em{{font-style:italic;color:var(--volt);}}
  .lede{{font-size:22px;line-height:1.45;color:var(--muted);margin-top:22px;max-width:900px;}}
  .lede b{{color:var(--cream);font-weight:800;}}

  .sect{{font-family:'JetBrains Mono',monospace;font-size:12px;font-weight:700;
    letter-spacing:.26em;text-transform:uppercase;color:var(--muted2);
    display:flex;justify-content:space-between;margin-bottom:12px;}}

  .rung{{display:flex;align-items:center;gap:20px;border:1px solid var(--line);
    padding:19px 22px;margin-bottom:9px;background:rgba(var(--cream-rgb),.025);}}
  .rung.top{{border-color:var(--neon);background:rgba(var(--volt-rgb),.10);}}
  .rung .cn{{font-family:'JetBrains Mono',monospace;font-size:19px;font-weight:700;
    letter-spacing:.14em;width:168px;color:var(--muted);}}
  .rung.top .cn{{color:var(--volt);}}
  .rung .note{{flex:1;font-size:17px;color:var(--muted2);}}
  .rung .pts{{font-family:'JetBrains Mono',monospace;font-size:26px;font-weight:700;
    width:112px;text-align:right;}}
  .rung .pts b{{color:var(--cream);}}
  .rung.top .pts b{{color:var(--volt);}}
  .rung .pts i{{font-style:normal;color:var(--muted2);}}
  .mid{{display:flex;justify-content:space-between;padding:0 24px;margin:-3px 0 5px;}}
  .mid span{{font-size:15px;font-weight:800;letter-spacing:.18em;text-transform:uppercase;}}
  .up{{color:var(--volt);}} .dn{{color:var(--uv);}}

  /* The night as a strip. Each pip is a round; the width is shared, so adding
     or removing a round from the engine re-spaces the whole strip rather than
     running it off the card. */
  .strip{{display:flex;gap:7px;}}
  .pip{{flex:1;height:62px;border:1px solid var(--line);background:rgba(var(--cream-rgb),.025);
    display:flex;flex-direction:column;align-items:center;justify-content:center;gap:2px;}}
  .pip i{{font-style:normal;font-family:'JetBrains Mono',monospace;font-size:15px;
    font-weight:700;color:var(--muted2);}}
  .pip.sh{{border-color:rgba(var(--uv-rgb),.55);background:rgba(var(--uv-rgb),.14);}}
  .pip.sh i{{color:var(--uv);}}
  .pip.x2{{border-color:var(--neon);background:rgba(var(--volt-rgb),.14);}}
  .pip.x2 i{{color:var(--volt);}}
  .pip u{{text-decoration:none;font-family:'JetBrains Mono',monospace;font-size:12px;
    font-weight:700;color:var(--volt);letter-spacing:.06em;}}
  .keys{{display:flex;gap:26px;margin-top:12px;flex-wrap:wrap;}}
  .k{{font-size:15px;color:var(--muted2);display:flex;align-items:center;gap:9px;}}
  .k::before{{content:"";width:11px;height:11px;border:1px solid var(--line);
    background:rgba(var(--cream-rgb),.06);}}
  .k.sh::before{{border-color:rgba(var(--uv-rgb),.55);background:rgba(var(--uv-rgb),.3);}}
  .k.x2::before{{border-color:var(--neon);background:rgba(var(--volt-rgb),.3);}}

  .steps{{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;}}
  .step{{border:1px solid var(--line);padding:19px 19px 21px;background:rgba(var(--cream-rgb),.025);}}
  .step .n{{font-family:'JetBrains Mono',monospace;font-size:13px;font-weight:700;
    color:var(--volt);letter-spacing:.14em;}}
  .step b{{display:block;font-size:19px;font-weight:800;color:var(--cream);margin-top:8px;line-height:1.2;}}
  .step i{{display:block;font-style:normal;font-size:15px;line-height:1.4;color:var(--muted2);margin-top:6px;}}

  .foot{{padding-top:26px;border-top:1px solid var(--line);
    display:flex;align-items:flex-end;justify-content:space-between;gap:26px;}}
  /* 38px of gap and .2em of tracking ran the host line 59px past the card's
     own margin — measured, not guessed, and it stopped 5px short of the crop
     so nothing that only watched the canvas edge noticed. */
  .facts{{display:flex;gap:26px;align-items:flex-end;}}
  .fact b{{display:block;font-family:'Archivo';font-style:italic;
    font-variation-settings:'wdth' 125,'wght' 900;font-size:34px;text-transform:uppercase;
    white-space:nowrap;}}
  .fact i{{display:block;font-style:normal;font-size:12px;font-weight:800;letter-spacing:.2em;
    text-transform:uppercase;color:var(--muted2);margin-top:5px;white-space:nowrap;}}
  .fact b u{{display:block;text-decoration:none;font-family:'Archivo',sans-serif;
    font-style:normal;font-variation-settings:normal;font-weight:800;
    font-size:.32em;letter-spacing:.2em;color:var(--muted2);margin-bottom:2px;}}
  .host{{font-family:'JetBrains Mono',monospace;font-size:14px;font-weight:700;letter-spacing:.1em;
    color:var(--volt);text-align:right;white-space:nowrap;text-transform:uppercase;}}
  .host small{{display:block;color:var(--muted2);font-size:12px;letter-spacing:.08em;margin-top:6px;
    text-transform:none;}}
</style></head>
<body>
<div class="wash"></div><div class="grid"></div><div class="grain"></div>
<div class="pad">

  <div>
    <div class="top">
      <span class="mark">
        <svg viewBox="0 0 100 100" width="24" height="24" aria-hidden="true">
          <path d="M18 64 L50 32 L82 64" fill="none" stroke="{VOLT}" stroke-width="13"
                stroke-linecap="square"/>
        </svg>
      </span>
      <span class="nm disp">{social['name'].title()}</span>
      <span class="sub">{social['cadenceLine']}</span>
    </div>

    <h1 class="disp">Climb to<br><em>Court {ORDINAL[1].capitalize()}</em></h1>
    <p class="lede">Come alone — no partner needed. <b>{ORDINAL[courts].capitalize()} courts, one
      ladder.</b> Every match is first to {f['target']}, straight rallies, no games and no sets.
      Win and you move up a court; lose and you move down.
      <b>The {f['target']} decides the match; the court decides what you bank.</b></p>
  </div>

  <div>
    <div class="sect"><span>The ladder</span><span>Win / lose</span></div>
    {ladder(f)}
  </div>

  <div>
    <div class="sect"><span>One night</span><span>{f['rounds']} rounds &middot; about {hhmm(f['minutes'])}</span></div>
    {timeline(f)}
  </div>

  <div class="steps">
    <div class="step"><span class="n">01</span><b>The shuffle</b>
      <i>It scores nothing. It decides where you start, so your court is won and not drawn.</i></div>
    <div class="step"><span class="n">02</span><b>Up or down</b>
      <i>Winners climb a court together, losers drop one. Every round, all night.</i></div>
    <div class="step"><span class="n">03</span><b>New partners</b>
      <i>Re-paired on arrival, 1+4 against 2+3. {each_line}</i></div>
  </div>

  <div class="foot">
    <div class="facts">
      <span class="fact"><b class="disp"><u>Up to</u>{f['players']}</b><i>Players</i></span>
      <span class="fact"><b class="disp">{courts}</b><i>Courts</i></span>
      <span class="fact"><b class="disp">{n_each}</b><i>Matches each</i></span>
      <span class="fact"><b class="disp">{f['target']}</b><i>Point match</i></span>
      <span class="fact"><b class="disp">0</b><i>Partners needed</i></span>
    </div>
    <span class="host">{social['host']}<small>{social['promise']}</small></span>
  </div>

</div>
</body></html>"""


def main():
    social = json.load(open(SOCIAL))
    f = facts()
    check_promise(social, f)
    os.makedirs(OUT, exist_ok=True)
    for size in SIZES:
        path = os.path.join(OUT, f"infographic-{size}.html")
        with open(path, "w") as fh:
            fh.write(card(f, social, size))
        print(f"built {os.path.basename(path)}  {SIZES[size][0]}x{SIZES[size][1]}")

    n_each, _ = leave_with(f)
    ending = "double final" if f["doubleFinal"] else f"{f['resting']} resting, no double final"
    print(f"\nfrom the engine: {f['players']} players · {f['courts']} courts · "
          f"{f['rounds']} rounds ({f['scoring']} scoring) · {n_each} matches each · "
          f"first to {f['target']} · about {hhmm(f['minutes'])} · {ending}")
    if f["overridden"]:
        print("!! the court count is a one-night override, not the norm — "
              "check uprising-social.json courtsOverride before posting")
    print("\nnow render:  node ops/render-uprising-infographic.mjs")


if __name__ == "__main__":
    main()
