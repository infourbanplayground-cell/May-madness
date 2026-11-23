#!/usr/bin/env python3
"""Muscat Heist (Vol.10) — the app, generated from 56 National Series (Vol.9).

    python3 build-heist-app.py && bash ops/deploy-heist.sh

The same inheritance every volume since July has used, with one difference:
the screens players see are NOT patched Vol.9 screens. They are the Heist
modules (brand/heist/heist-*.jsx), built phase by phase against the design
handoff, fed by heist-adapter.jsx from the INHERITED ENGINE. So:

  * scoring, saving, sign-in, the recovery banner, the draw, the bracket and
    every organiser sheet are Vol.9's, untouched — the code that has run nine
    volumes of nights;
  * App() renders HeistShell instead of the Vol.9 tabs; the organiser reaches
    the inherited tools through the ORGANISER chip (?classic), and a night's
    full editor opens over the Heist screens;
  * the season comes from heist-season.json and nothing else.

Every substitution is asserted: a string that stops matching fails the build
rather than shipping a half-Heist app.
"""
import hashlib
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "national-index.html")
DST = os.path.join(HERE, "heist-index.html")
H = os.path.join(HERE, "brand", "heist")
season = json.load(open(os.path.join(HERE, "heist-season.json"), encoding="utf-8"))
read = lambda n: open(os.path.join(H, n), encoding="utf-8").read()
MODULES = ["heist-components.jsx", "heist-screens.jsx", "heist-night.jsx", "heist-moments.jsx",
           "heist-stories.jsx", "heist-adapter.jsx"]


def once(s, a, b, what):
    n = s.count(a)
    assert n == 1, f"{what}: anchor found {n} times, wanted 1"
    return s.replace(a, b)


def const(s, name, value):
    """Rewrite a one-line `const NAME = ...;` at the top level of the page."""
    pat = re.compile(r"(\nconst " + re.escape(name) + r" = )[^\n]*?;\n")
    m = pat.findall(s)
    assert len(m) == 1, f"const {name}: found {len(m)}"
    return pat.sub(lambda mm: mm.group(1) + value + ";\n", s)


def top_names(js):
    return set(re.findall(r"^(?:function|const|let|var|class)\s+([A-Za-z_$][\w$]*)", js, re.M))


def main():
    s = open(SRC, encoding="utf-8").read()
    S = season
    pool = sum(S["seasonPrizes"]) + S["voucher"] * 2 * S["sessions"]

    # ── the season ──
    s = const(s, "SESSIONS_TOTAL", str(S["sessions"]))
    s = const(s, "SEASON_PRIZES", json.dumps(S["seasonPrizes"]))
    s = const(s, "DOUBLE_NIGHTS", json.dumps(S["doubleNights"]))
    s = const(s, "SEASON_NIGHTS", json.dumps(S["nights"]))
    s = const(s, "SEASON_VOUCHER", str(S["voucher"]))
    s = const(s, "FINALS_DATE", json.dumps(S["finalsDate"]))
    s = const(s, "SERIES_NAME", repr(S["name"].upper()))
    s = const(s, "VOLUME_LABEL", repr(S["volumeLabel"]))
    s = const(s, "SEASON_MONTH_SHORT", repr(S["monthShort"]))
    s = const(s, "LOCAL_KEY", '"heist-state-v1"')
    # Vol.9's National Day is a fact about November. Heist has no such night,
    # so the inherited double-night dressing names the night by its date.
    s = const(s, "NATIONAL_DAY_DATE", "''")
    s = const(s, "NATIONAL_DAY_TITLE", '"DOUBLE POINTS"')
    s = const(s, "NA_VOLUME_NAME", json.dumps(S["name"]))
    s = s.replace("56 NATIONAL SERIES", S["name"].upper())
    s = once(s, "<title>", "<title>Muscat Heist · ", "title")

    # ── fonts: the Heist faces beside the inherited ones, served locally ──
    s = once(s, "</head>",
             '<link rel="stylesheet" href="assets/fonts/brand/fonts.css" />\n'
             '<link rel="stylesheet" href="assets/fonts/heist/fonts.css" />\n'
             f'<style id="heist-css">\n{read("heist.css")}\n</style>\n</head>', "head")

    # ── the modules, ahead of App(), with a name-clash guard ──
    mods = "\n".join(read(m) for m in MODULES)
    i = s.index("function App()")
    script_start = s.rindex('<script type="text/babel"', 0, i)
    page_js = s[script_start:]
    clash = top_names(mods) & top_names(page_js)
    # a duplicate top-level declaration is a SyntaxError that blanks the WHOLE
    # page (the americano build learned this) — refuse instead
    assert not clash, f"Heist modules redeclare page names: {sorted(clash)}"
    s = s[:i] + f"window.MH_SEASON = {json.dumps(S, ensure_ascii=False)};\n{mods}\n\n" + s[i:]

    # ── App(): the Heist shell instead of the Vol.9 tabs ──
    s = once(s, "  const [showLogin, setShowLogin] = useState(false);\n",
             "  const [showLogin, setShowLogin] = useState(false);\n"
             "  // ?classic opens the inherited Vol.9 screens: the organiser's tools for\n"
             "  // what the Heist design does not draw (a new night, the draw, the bracket).\n"
             "  const [classic] = useState(() => new URLSearchParams(location.search).has(\"classic\"));\n",
             "classic state")
    app = s.index("function App()")
    nav = s.index("  const navTabs = [", app)
    tail = s[nav:s.index("\n}\n", nav)]
    grab = lambda key: re.search(r"\n(\s*\{" + re.escape(key) + r".*?/>\})", tail, re.S).group(1).strip()
    sheets = "\n      ".join(grab(k) for k in ("currentSession && <SessionDetail", "showLogin && <LoginModal", "showMe && <MePicker"))
    shell = f"""  if (!classic) return (
    <>
      <HeistShell state={{state}} leaderboard={{leaderboard}} meId={{meId}} canScore={{canScore}} sync={{sync}} syncErr={{syncErr}}
        updateSession={{updateSession}} signedIn={{role !== "guest"}}
        openLogin={{() => setShowLogin(true)}} openMe={{() => setShowMe(true)}}
        openOrganiser={{() => {{ location.href = location.pathname + "?classic"; }}}}
        openSession={{id => setOpenSessionId(id)}} />
      {sheets}
    </>
  );

"""
    s = s[:nav] + shell + s[nav:]

    # the way back from the inherited screens
    s = once(s, "</body>", """<a id="mh-back" href="./" hidden style="position:fixed;right:12px;bottom:92px;z-index:90;padding:12px 16px;border-radius:999px;background:#F26B5B;color:#0F1B2B;font:800 13px system-ui;text-decoration:none;box-shadow:0 6px 18px rgba(0,0,0,.4)">← Back to Muscat Heist</a>
<script>if (new URLSearchParams(location.search).has("classic")) document.getElementById("mh-back").hidden = false;</script>
</body>""", "classic way back")

    # ── stamp ──
    bid = hashlib.sha256(s.encode()).hexdigest()[:12]
    s, n = re.subn(r'(\n\s*var V = )"[0-9a-f]{6,}";', r'\1"%s";' % bid, s, count=1)
    assert n == 1, "build stamp not found"
    open(DST, "w", encoding="utf-8").write(s)
    open(DST + ".version", "w").write(bid + "\n")

    left = {t: s.count(t) for t in ("56 NATIONAL SERIES", "national.urbanpadel.om") if s.count(t)}
    print(f"wrote {os.path.basename(DST)}  {len(s) // 1024}KB  build {bid}  pool {pool}  modules {len(MODULES)}")
    if left:
        print("  note — Vol.9 strings still in the page:", left)


if __name__ == "__main__":
    main()
