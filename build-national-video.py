# -*- coding: utf-8 -*-
"""56 National Series (Vol.9) — the 18-second SEASON OPENING film.

THIS IS NOT VOL.8'S HYPE CUT AND COULD NOT BE. `build-hype-video.py` is a
mid-season film: every figure in it comes from `ops/blackout-standings.mjs`
run over a live table, and its whole argument is who is winning and what is
left. Vol.9 has played nothing. There is no table to argue from, and a film
that invented one would be the worst thing in this repo.

So this one argues the only things that are true before a ball is hit: what
the season IS. The name, the shape of it, the one night that is an occasion,
the money, and the date it starts.

  0.00  the name            56 NATIONAL SERIES · السلسلة الوطنية
  3.60  the shape           nine nights, all November, Mon & Wed
  7.60  the occasion        National Day night, and what else pays double
 11.40  the money           the pool, the entry, the vouchers, the season
 14.80  the ask             starts tomorrow · One flag. One court.

EVERY FIGURE COMES FROM `national-season.json`, none is typed — the same
discipline the app, the posts and the announcement work under, and the reason
none of them can advertise a number the others contradict. The pool is
DERIVED from its parts (voucher x 2 x nights + season prizes), exactly as
`build-national-app.py` derives it, so the film cannot drift from the app by
having the total written down twice.

IT REFUSES TO BUILD IF ITS OWN HEADLINE IS NOT TRUE. The cut ends on the word
TOMORROW in 150px type, so it will not build unless the first night really is
tomorrow; it will not build once the season has started; and it will not claim
a doubled night the schedule does not list. A poster wrong on its own headline
is worse than no poster, and a film is worse again, because nobody re-reads it.

IT NEVER SAYS WHAT A DOUBLED NIGHT IS WORTH IN POINTS. 2X applies to
everything except the streak bonus, so multiplying it out is close — and close
is how a film ends up contradicting the app.

Deterministic: no CSS animations anywhere, every moving value a pure function
of t behind `window.__seek(t)`. The recorder scrubs each frame to an exact
time rather than grabbing it off a running clock.

  python3 build-national-video.py
  python3.13 build-national-audio.py
  node record-national-video.mjs
"""
import datetime
import json
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "ops"))
from font_bundle import bundle          # noqa: E402
from national_assets import assets      # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
SP = ("/tmp/claude-0/-home-user-May-madness/"
      "0e44f0ad-a683-5f0d-9de6-9459ae328963/scratchpad")
OUT = os.path.join(SP, "national.html")
CAPS = os.path.join(HERE, "brand", "national", "posts", "VIDEO-CAPTIONS.txt")

W, H = 1080, 1920
DUR = 18.00
# Five beats. The picture is cut on them and so is the bed, from one table —
# two media reading the same list is the only way they stay in step.
SCENES = [0.00, 3.60, 7.60, 11.40, 14.80]
BEATS = [0.00, 1.80, 3.60, 5.60, 7.60, 9.40, 11.40, 13.10, 14.80, 16.40]
HERO = [0.00, 7.60, 14.80]

DAYS = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]
MONS = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN",
        "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
WORDS = {1: "ONE", 2: "TWO", 3: "THREE", 4: "FOUR", 5: "FIVE", 6: "SIX",
         7: "SEVEN", 8: "EIGHT", 9: "NINE", 10: "TEN", 11: "ELEVEN",
         12: "TWELVE"}


def d(s):
    return datetime.date.fromisoformat(s)


def short(s):
    x = d(s)
    return f"{DAYS[x.weekday()]} {x.day}"


def longish(s):
    x = d(s)
    return f"{DAYS[x.weekday()]} {x.day} {MONS[x.month - 1]}"


def check_arabic(cfg, strings):
    """Refuse to set a character Noto Kufi was not subsetted to draw.

    The face is cut to exactly the words the brand uses, which takes it from
    120KB a weight to a couple of KB. The cost is that a word added anywhere
    else renders in the container's DejaVu with nothing on screen to say so —
    the same silent-fallback failure the Latin faces are vendored to prevent,
    and the reason `build-national-app.py` carries this guard too.
    """
    cov = set(open(os.path.join(HERE, "brand", "fonts", "kufi-coverage.txt"),
                   encoding="utf-8").read())
    bad = sorted({c for s in strings for c in s
                  if "؀" <= c <= "ۿ" and c not in cov})
    if bad:
        raise SystemExit(
            "the Arabic in this film uses characters Noto Kufi was not "
            f"subsetted for: {' '.join(bad)}\n"
            "add the string to national-season.json's `arabic` block and "
            "re-run ops/vendor-fonts.py")


def main():
    cfg = json.load(open(os.path.join(HERE, "national-season.json"),
                         encoding="utf-8"))
    P = cfg["palette"]
    A = assets()
    today = datetime.date.today()

    nights = cfg["nights"]
    first, last = d(nights[0]), d(nights[-1])
    doubles = cfg["doubleNights"]
    natday = cfg["nationalDay"]

    # ── the guards ──────────────────────────────────────────────────────────
    # The cut ends on TOMORROW in 150px type. Every other check in this repo
    # is about where the ink landed; this one is about whether the sentence is
    # still true, which no amount of looking at the frame will tell you.
    if first - today != datetime.timedelta(days=1):
        raise SystemExit(
            f"the film says the season starts TOMORROW, but night 1 is "
            f"{nights[0]} and today is {today} "
            f"({(first - today).days:+d} days).\n"
            "This is a season-opening film: build it the day before night 1.")
    if today >= first:
        raise SystemExit("the season has started — this is an opening film")
    assert natday in doubles, \
        "National Day is not in doubleNights; scene 3 would be a lie"
    assert len(nights) == cfg["sessions"], \
        f"{len(nights)} dates for {cfg['sessions']} sessions"
    assert d(cfg["finalsDate"]) == last, "finalsDate is not the last night"

    # THE POOL IS DERIVED, NEVER TYPED — the same expression
    # build-national-app.py uses, so the film and the app cannot disagree by
    # having the total written down in two places.
    pool = cfg["voucher"] * 2 * cfg["sessions"] + sum(cfg["seasonPrizes"])

    # The tagline is two sentences so the two beats can be set in two inks.
    # The app's hero asserts the same thing, for the same reason: a headline
    # that splits into an empty second colour is worse than one that does not
    # split at all.
    tag = cfg["tagline"].strip()
    beats = [x.strip() for x in re.findall(r"[^.!?]+[.!?]", tag)]
    assert len(beats) == 2, \
        f"tagline must be two sentences for the two inks, got {len(beats)}: {tag!r}"

    name_ar, natday_ar = cfg["nameAr"], cfg["nationalDayLabelAr"]
    check_arabic(cfg, [name_ar, natday_ar])

    # The schedule line carries the start time; parse it rather than typing
    # one, because two assets quoting different times is the fault worth
    # engineering against.
    mt = re.search(r"(\d{1,2}(?::\d{2})?\s*(?:AM|PM))", cfg["schedule"], re.I)
    if not mt:
        raise SystemExit(f"no start time in schedule line {cfg['schedule']!r}")
    start_time = mt.group(1).upper().replace(" ", "")
    days_line = cfg["schedule"].split(",")[0].strip().upper()

    n_double = len(doubles)
    others = [x for x in doubles if x != natday]

    # ── scene 2: the nine nights ────────────────────────────────────────────
    chips = "".join(
        '<div class="nt{dd}"><div class="nd mono">{day}</div>'
        '<div class="nn disp">{num}</div>{mark}</div>'.format(
            dd=" dbl" if n in doubles else "",
            day=DAYS[d(n).weekday()],
            num=d(n).day,
            mark='<div class="x mono">2X</div>' if n in doubles else "")
        for n in nights)

    # ── scene 4: the money ──────────────────────────────────────────────────
    # Short keys. The first cut ran "EVERY NIGHT · 14 OMR VOUCHERS" against a
    # 56px figure in an 888px row and the clipped check caught it — the label
    # is the part that can give, because the figure is the point of the row.
    money = "".join(
        f'<div class="mr"><div class="mk mono">{k}</div>'
        f'<div class="mv disp">{v}</div></div>'
        for k, v in [
            ("A NIGHT TO PLAY", f"{cfg['entry']}"),
            ("VOUCHERS EVERY NIGHT", f"{cfg['voucher']}"),
            ("THE SEASON, TOP THREE",
             "/".join(str(x) for x in cfg["seasonPrizes"])),
        ])

    style = f"""
{bundle()}
*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{width:{W}px;height:{H}px;overflow:hidden;background:{P['bg']};
  font-family:'Archivo',system-ui,sans-serif;-webkit-font-smoothing:antialiased;
  color:{P['ivory']}}}
body{{position:relative}}
/* The ground: the khanjar tile at the app's own 340px and .18, never the
   handoff's 132 and .14. A film is watched on the phone the app is used on,
   and the two drifting apart is the fault worth engineering against. */
#tile{{position:absolute;inset:0;opacity:.18;pointer-events:none;z-index:0;
  background-image:url("{A['khanjar']}");background-size:340px 340px}}
/* THE MASAR TRIM — inset and pilled, not a full-bleed stripe. The handoff
   draws it 24 tall at a 14px side inset with a pill radius; at this scale
   that is 56 tall, inset 36 at the sides and 18 off each edge, keeping the
   same 2:1 of side inset to edge offset. Run full-bleed it stops being a
   trim and becomes a bar of its own, which is the mistake already recorded
   twice in CLAUDE.md. The width keeps the art's 100:56 ratio. */
.band{{position:absolute;left:36px;right:36px;height:56px;border-radius:28px;
  pointer-events:none;z-index:3;background-color:{P['deep']};
  background-image:url("{A['masar']}");
  background-size:100px 56px;background-repeat:repeat-x}}
.band.t{{top:18px}} .band.b{{bottom:18px;transform:scaleY(-1)}}
.scene{{position:absolute;inset:0;z-index:2}}
.blk{{position:absolute;left:0;right:0;text-align:center}}
.disp{{font-style:italic;font-variation-settings:'wdth' 125,'wght' 900;
  line-height:.88;text-transform:uppercase}}
.mono{{font-family:'JetBrains Mono',monospace;font-weight:700;
  text-transform:uppercase}}
.kufi{{font-family:'Noto Kufi Arabic',sans-serif;font-weight:700}}
/* NO DROP SHADOWS anywhere. Depth is the double-line ring and nothing else. */
.arch{{background:{P['ivory']};color:{P['ink']};
  border-radius:50% 50% 28px 28px / 34% 34% 28px 28px;
  box-shadow:0 0 0 7px {P['bg']},0 0 0 11px {P['ivory']};overflow:hidden}}
.sheet{{background:{P['deep']};border-radius:28px;
  border:1px solid rgba(247,241,230,.18)}}
/* The flag plaque behind the 56 — the one place in the chrome carrying white
   and green, and deliberately so: on the flag the green is not an accent,
   it is the flag. 10px of radius, because a flag drawn as a pill stops
   being a flag. */
.flag{{display:inline-flex;align-items:center;justify-content:center;
  border-radius:10px;padding:12px 30px 12px 46px;
  background-image:
    linear-gradient(90deg,{P['flag']} 0 22px,transparent 22px),
    linear-gradient(180deg,#FFFFFF 0 34%,{P['flag']} 34% 66%,{P['green']} 66% 100%);
  box-shadow:0 0 0 4px {P['ink']}}}
.flag .n{{color:#FFFFFF;-webkit-text-stroke:4px {P['ink']};
  paint-order:stroke fill;letter-spacing:-.02em}}
.med{{border-radius:50%;background-color:{P['bg']};background-repeat:no-repeat;
  background-position:center 54%;background-size:62% auto;
  box-shadow:0 0 0 3px {P['ivory']},0 0 0 6px {P['flag']}}}

/* ── scene 1 ─────────────────────────────────────────────────────────── */
#s1a{{top:560px}}
#s1b{{top:790px;font-size:118px}}
#s1c{{top:1100px;font-size:44px;color:{P['rose-txt'] if 'rose-txt' in P else '#F2D0D3'}}}
#s1d{{top:1270px;font-size:26px;letter-spacing:.34em;color:#F2D0D3}}

/* ── scene 2: nine nights ────────────────────────────────────────────── */
#s2a{{top:300px;font-size:26px;letter-spacing:.34em;color:#F2D0D3}}
#s2b{{top:380px;font-size:150px}}
#s2c{{top:580px;font-size:58px;color:#F2D0D3}}
#s2grid{{position:absolute;top:760px;left:96px;right:96px;
  display:grid;grid-template-columns:repeat(3,1fr);gap:22px;z-index:2}}
.nt{{background:{P['deep']};border-radius:28px;padding:22px 10px 20px;
  text-align:center;border:1px solid rgba(247,241,230,.18);position:relative}}
.nt.dbl{{background:{P['flag']};border-color:{P['ivory']}}}
.nd{{font-size:22px;letter-spacing:.18em;color:#F2D0D3}}
.nn{{font-size:72px;margin-top:4px;color:{P['ivory']}}}
.x{{position:absolute;top:12px;right:16px;font-size:18px;letter-spacing:.06em;
  color:{P['ivory']}}}
#s2d{{top:1500px;font-size:34px;letter-spacing:.14em;color:{P['ivory']}}}

/* ── scene 3: the one occasion ───────────────────────────────────────── */
#s3med{{position:absolute;top:420px;left:50%;margin-left:-130px;
  width:260px;height:260px;z-index:2;
  background-image:url("{A['mon-fort@white']}")}}
#s3a{{top:700px;font-size:26px;letter-spacing:.34em;color:#F2D0D3}}
/* GREEN IS SPENT HERE AND NOWHERE ELSE. The handoff reserves it for National
   Day, and spending it as a general accent is what would take the meaning
   off the 18th. */
/* The pill is as wide as the frame allows and the title is 46px, not 62: at
   62 nowrap "NATIONAL DAY NIGHT" needed 886px of a 654px cell. It stays
   nowrap because a two-line title inside a pill is not a pill any more. */
#s3pill{{position:absolute;top:780px;left:52px;right:52px;z-index:2;
  background:{P['green']};border-radius:999px;
  padding:32px 34px 32px 48px;display:flex;align-items:center;gap:22px}}
#s3pill .l{{flex:1 1 auto;min-width:0;text-align:left}}
#s3when{{font-size:26px;letter-spacing:.14em;color:#FFFFFF}}
#s3t{{font-size:46px;margin-top:8px;color:#FFFFFF;white-space:nowrap}}
#s3ar{{font-size:28px;margin-top:12px;color:#FFFFFF}}
#s3x{{flex:0 0 auto;width:120px;height:120px;border-radius:50%;background:#FFFFFF;
  color:{P['green']};display:flex;align-items:center;justify-content:center;
  font-size:48px}}
#s3b{{top:1180px;font-size:96px}}
#s3c{{top:1350px;font-size:34px;color:#F2D0D3;letter-spacing:.06em}}

/* ── scene 4: the money ──────────────────────────────────────────────── */
#s4a{{top:480px;font-size:26px;letter-spacing:.34em;color:#F2D0D3}}
/* 30px of gap, not 6. `line-height:.88` on a 210px numeral makes its line box
   SHORTER than the glyphs it holds, so the unit under it sat 20px inside the
   numeral's box — which the overlap check reads, correctly, as a collision. */
#s4arch{{position:absolute;top:550px;left:120px;right:120px;height:430px;
  z-index:2;display:flex;flex-direction:column;align-items:center;
  justify-content:center;gap:30px}}
#s4n{{font-size:210px;color:{P['bg']};line-height:.84}}
#s4u{{font-size:40px;letter-spacing:.2em;color:{P['ink']}}}
#s4k{{font-size:24px;letter-spacing:.24em;color:{P['muted']};margin-top:10px}}
#s4rows{{position:absolute;top:1050px;left:96px;right:96px;z-index:2;
  display:flex;flex-direction:column;gap:18px}}
.mr{{background:{P['deep']};border-radius:999px;
  border:1px solid rgba(247,241,230,.18);
  padding:24px 36px;display:flex;align-items:center;justify-content:space-between;
  gap:24px}}
.mk{{font-size:24px;letter-spacing:.16em;color:#F2D0D3;text-align:left}}
.mv{{font-size:56px;color:{P['ivory']};white-space:nowrap}}

/* ── scene 5: the ask ────────────────────────────────────────────────── */
#s5a{{top:470px;font-size:26px;letter-spacing:.34em;color:#F2D0D3}}
#s5b{{top:550px;font-size:150px}}
#s5c{{top:760px;font-size:52px;color:{P['ivory']};letter-spacing:.04em}}
#s5arch{{position:absolute;top:940px;left:110px;right:110px;height:330px;
  z-index:2;display:flex;flex-direction:column;align-items:center;
  justify-content:center;gap:10px}}
#s5t1{{font-size:92px;color:{P['ink']}}}
/* The second beat is the BASE RED on ivory, not the ivory it would otherwise
   inherit: the markup that exists to split the line into two inks has to
   actually do something. */
#s5t2{{font-size:92px;color:{P['bg']}}}
#s5d{{top:1370px;font-size:34px;letter-spacing:.2em;color:#F2D0D3}}
"""

    body = f"""
<div id="tile"></div>
<div class="band t"></div><div class="band b"></div>

<div class="scene" id="s1">
  <div class="blk" id="s1a"><span class="flag"><span class="n disp"
       style="font-size:150px">56</span></span></div>
  <div class="blk disp" id="s1b"><span class="fitspan">NATIONAL<br>SERIES</span></div>
  <div class="blk kufi" id="s1c">{name_ar}</div>
  <div class="blk mono" id="s1d">{cfg['volume']} &middot; URBAN SOCIAL SERIES</div>
</div>

<div class="scene" id="s2">
  <div class="blk mono" id="s2a">THE SEASON</div>
  <div class="blk disp" id="s2b"><span class="fitspan">{WORDS[cfg['sessions']]} NIGHTS</span></div>
  <div class="blk disp" id="s2c">ALL {cfg['monthUpper']}</div>
  <div id="s2grid">{chips}</div>
  <div class="blk mono" id="s2d">{days_line} &middot; {start_time}</div>
</div>

<div class="scene" id="s3">
  <div class="med" id="s3med"></div>
  <div class="blk mono" id="s3a">THE ONE NIGHT THAT IS AN OCCASION</div>
  <div id="s3pill">
    <div class="l">
      <div class="mono" id="s3when">{longish(natday)} &middot; {start_time}</div>
      <div class="disp" id="s3t">{cfg['nationalDayLabel']}</div>
      <div class="kufi" id="s3ar">{natday_ar}</div>
    </div>
    <div class="disp" id="s3x">2X</div>
  </div>
  <div class="blk disp" id="s3b"><span class="fitspan">{WORDS[n_double]} DOUBLE NIGHTS</span></div>
  <div class="blk mono" id="s3c">{' &middot; '.join(longish(x) for x in doubles)}</div>
</div>

<div class="scene" id="s4">
  <div class="blk mono" id="s4a">ON THE TABLE</div>
  <div class="arch" id="s4arch">
    <div class="disp" id="s4n">{pool}</div>
    <div class="mono" id="s4u">OMR</div>
    <div class="mono" id="s4k">PRIZE POOL, {cfg['monthUpper']}</div>
  </div>
  <div id="s4rows">{money}</div>
</div>

<div class="scene" id="s5">
  <div class="blk mono" id="s5a">{cfg['name']}</div>
  <div class="blk disp" id="s5b"><span class="fitspan">TOMORROW</span></div>
  <div class="blk disp" id="s5c">{longish(nights[0])} &middot; {start_time}</div>
  <div class="arch" id="s5arch">
    <div class="disp" id="s5t1">{beats[0]}</div>
    <div class="disp" id="s5t2">{beats[1]}</div>
  </div>
  <div class="blk mono" id="s5d">{cfg['host']}</div>
</div>
"""

    js = """
<script>
const DUR = %(dur)s, SCENES = %(scenes)s, BEATS = %(beats)s, HERO = %(hero)s;
window.__dur = DUR;
window.__scenes = SCENES;

const E = id => document.getElementById(id);
const clamp = (x,a,b) => x < a ? a : x > b ? b : x;
const ease  = u => 1 - Math.pow(1 - clamp(u,0,1), 3);
// The entrance: rise, fade and WIDEN. The width axis is the one thing that
// reads as this brand moving rather than as any fade.
function enter(el, u, rise, wide) {
  const e = ease(u);
  el.style.opacity = clamp(u * 1.6, 0, 1);
  el.style.transform = 'translateY(' + ((1 - e) * (rise === undefined ? 34 : rise)).toFixed(2) + 'px)';
  if (wide) {
    const s = el.querySelector('.fitspan') || el;
    s.style.fontVariationSettings = "'wdth' " + (84 + 41 * e).toFixed(1) + ",'wght' 900";
  }
}
// Energy from the beat table, so the picture pulses with the bed rather than
// near it. Clamped AT THE POINT IT IS MADE: the window opens 20ms early so the
// hit is not late, which makes (1-u)^3 exceed one and anything derived from it
// — a radius, a scale — go negative.
function energy(t) {
  let e = 0;
  for (const b of BEATS) {
    const u = (t - (b - 0.02)) / 0.30;
    if (u >= 0 && u <= 1) e = Math.max(e, Math.pow(1 - clamp(u,0,1), 3) * (HERO.includes(b) ? 1 : 0.55));
  }
  return clamp(e, 0, 1);
}

// SHRINK-TO-FIT, run once after the faces are ready. Sizing before that sizes
// against the fallback, which measures nothing like Archivo at wdth 125 — the
// reason the Blackout lockup once shipped with its first and last letters
// sliced off while every assertion passed.
// EVERY SCENE MUST BE VISIBLE WHILE IT RUNS. __seek(0) has already hidden
// scenes 2-5 by the time document.fonts.ready resolves, and a hidden box
// measures 0 — so `room` went negative and the loop shrank every headline in
// them to the 10px floor. Three of the five headlines were simply absent from
// the film, and nothing failed: no text had overflowed anything.
function fitAll() {
  const scenes = [...document.querySelectorAll('.scene')];
  const was = scenes.map(el => el.style.display);
  scenes.forEach(el => { el.style.display = 'block'; });
  for (const s of document.querySelectorAll('.fitspan')) {
    const box = s.parentElement;
    const room = box.clientWidth - 48;
    let px = parseFloat(getComputedStyle(box).fontSize);
    s.style.whiteSpace = 'nowrap';           // a .fit line that WRAPS never
    s.style.display = 'inline-block';        // overflows, so it never shrinks
    if (room <= 0) throw new Error('fit: ' + (box.id || box.className) + ' has no width');
    while (s.getBoundingClientRect().width > room && px > 10) {
      px -= 2; box.style.fontSize = px + 'px';
    }
    if (px <= 10) throw new Error('fit: ' + (box.id || box.className) + ' hit the floor');
  }
  scenes.forEach((el, k) => { el.style.display = was[k]; });
}

function sceneAt(t) {
  let i = 0;
  for (let k = 0; k < SCENES.length; k++) if (t >= SCENES[k]) i = k;
  return i;
}

window.__seek = function (t) {
  t = clamp(t, 0, DUR);
  const i = sceneAt(t);
  const t0 = SCENES[i], t1 = (i + 1 < SCENES.length) ? SCENES[i + 1] : DUR;
  const u = (t - t0) / (t1 - t0);
  const e = energy(t);

  document.querySelectorAll('.scene').forEach((el, k) => {
    el.style.display = (k === i) ? 'block' : 'none';
  });

  // The ground breathes on the hits and the trim brightens with them: the
  // motif is the volume, so it should be part of the cut rather than wallpaper
  // behind it.
  E('tile').style.opacity = (0.18 + 0.10 * e).toFixed(3);
  E('tile').style.backgroundSize = (340 + 26 * e).toFixed(1) + 'px ' + (340 + 26 * e).toFixed(1) + 'px';
  for (const b of document.querySelectorAll('.band'))
    b.style.opacity = (0.82 + 0.18 * e).toFixed(3);

  const S = (t - t0);
  if (i === 0) {
    enter(E('s1a'), S / 0.70, 26);
    enter(E('s1b'), (S - 0.22) / 0.80, 40, true);
    enter(E('s1c'), (S - 0.55) / 0.70, 22);
    enter(E('s1d'), (S - 0.80) / 0.70, 16);
    E('s1a').style.transform += ' scale(' + (1 + 0.035 * e).toFixed(4) + ')';
  } else if (i === 1) {
    enter(E('s2a'), S / 0.55, 16);
    enter(E('s2b'), (S - 0.12) / 0.75, 36, true);
    enter(E('s2c'), (S - 0.34) / 0.70, 26);
    enter(E('s2d'), (S - 1.30) / 0.70, 18);
    // The nine land one after another, which is the scene doing the counting
    // instead of a line of copy claiming it.
    const tiles = document.querySelectorAll('#s2grid .nt');
    tiles.forEach((el, k) => {
      const uu = (S - 0.50 - k * 0.11) / 0.46;
      el.style.opacity = clamp(uu * 1.7, 0, 1);
      const ee = ease(uu);
      el.style.transform = 'translateY(' + ((1 - ee) * 26).toFixed(2) + 'px) scale('
        + (0.90 + 0.10 * ee).toFixed(4) + ')';
    });
  } else if (i === 2) {
    enter(E('s3med'), S / 0.70, 20);
    E('s3med').style.transform += ' scale(' + (1 + 0.05 * e).toFixed(4) + ')';
    enter(E('s3a'), (S - 0.20) / 0.60, 16);
    enter(E('s3pill'), (S - 0.38) / 0.75, 34);
    enter(E('s3b'), (S - 1.25) / 0.75, 34, true);
    enter(E('s3c'), (S - 1.60) / 0.70, 18);
    E('s3x').style.transform = 'scale(' + (1 + 0.09 * e).toFixed(4) + ')';
  } else if (i === 3) {
    enter(E('s4a'), S / 0.55, 16);
    enter(E('s4arch'), (S - 0.14) / 0.80, 38);
    // The pool counts up to its derived total rather than appearing: the one
    // number in the film anybody repeats afterwards.
    const n = Math.round(%(pool)s * ease((S - 0.20) / 1.25));
    E('s4n').textContent = n;
    document.querySelectorAll('#s4rows .mr').forEach((el, k) => {
      const uu = (S - 1.05 - k * 0.20) / 0.55;
      el.style.opacity = clamp(uu * 1.7, 0, 1);
      el.style.transform = 'translateX(' + ((1 - ease(uu)) * 44).toFixed(2) + 'px)';
    });
  } else {
    enter(E('s5a'), S / 0.55, 16);
    enter(E('s5b'), (S - 0.12) / 0.80, 40, true);
    enter(E('s5c'), (S - 0.42) / 0.70, 26);
    enter(E('s5arch'), (S - 0.70) / 0.85, 40);
    enter(E('s5d'), (S - 1.15) / 0.70, 18);
    E('s5arch').style.transform += ' scale(' + (1 + 0.02 * e).toFixed(4) + ')';
  }
};

document.fonts.ready.then(() => { fitAll(); window.__seek(0); window.__ready = true; });
window.__seek(0);
</script>
"""% {"dur": DUR, "scenes": json.dumps(SCENES), "beats": json.dumps(BEATS),
      "hero": json.dumps(HERO), "pool": pool}

    html = ("<!doctype html><html><head><meta charset='utf-8'>\n<style>"
            + style + "</style></head><body>\n" + body + js + "\n</body></html>")

    os.makedirs(SP, exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(html)

    # ── the captions, from the same figures ─────────────────────────────────
    os.makedirs(os.path.dirname(CAPS), exist_ok=True)
    # Prose, not shouting. The film sets these words in caps because that is
    # the display face; a caption that writes "NINE nights, all November" mid
    # sentence reads as a typo, and nothing here is wrapped by hand — a line
    # broken mid-clause is how a WhatsApp post ends up looking pasted.
    def nice(s):
        x = d(s)
        return (f"{['Mon','Tue','Wed','Thu','Fri','Sat','Sun'][x.weekday()]} "
                f"{x.day} {cfg['month'][:3] if x.month == d(nights[0]).month else MONS[x.month-1].title()}")

    n_word = WORDS[cfg["sessions"]].lower()
    dbl_word = WORDS[n_double].lower()
    prizes = "/".join(str(x) for x in cfg["seasonPrizes"])
    cap = f"""{cfg['name']} — season opening film
{'=' * 54}
1080x1920 · {DUR:.0f}s · {cfg['host']}
Built from national-season.json; every figure is read, none typed.

— WHATSAPP —

🇴🇲 *{cfg['name']}* starts TOMORROW.

{nice(nights[0])}, {start_time}. {n_word.capitalize()} nights across {cfg['month']}, {days_line.title()}.

{pool} OMR on the table across the season — {cfg['voucher']} OMR vouchers every night, and {prizes} for the top three at the end of it. {cfg['entry']} OMR a night to play.

{dbl_word.capitalize()} of the nights pay DOUBLE POINTS, and one of them is {cfg['nationalDayLabel'].title()} on {nice(natday)}.

{tag}
{cfg['host']}

— INSTAGRAM —

{tag}

{cfg['name']} — {cfg['volume']} of the Urban Social Series — opens {nice(nights[0])}. {n_word.capitalize()} nights across {cfg['month']}, {days_line.title()} at {start_time}. {pool} OMR across the season, and {dbl_word} double-points nights — one of them {cfg['nationalDayLabel'].title()}.

{cfg['entry']} OMR a night. Link in bio.

#urbanplayground #padel #oman #56nationalseries #نادي_بادل #عمان
"""
    with open(CAPS, "w", encoding="utf-8") as f:
        f.write(cap)

    print(f"built {OUT}  {len(html)/1024:.0f}KB  {DUR:.0f}s  "
          f"{len(SCENES)} scenes")
    print(f"  pool {pool} OMR (derived)  ·  {cfg['sessions']} nights  ·  "
          f"{n_double} double, incl. {longish(natday)}")
    print(f"  night 1 is {longish(nights[0])} — tomorrow, which is what the "
          f"cut says")
    print(f"  captions {CAPS}")
    print("\nnow:  python3.13 build-national-audio.py && node record-national-video.mjs")


if __name__ == "__main__":
    main()
