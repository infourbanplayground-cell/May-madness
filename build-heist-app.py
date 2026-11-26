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
           "heist-stories.jsx", "heist-loot.jsx", "heist-night-share.jsx", "heist-adapter.jsx"]


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


# ── the organiser's screens: Vol.9's markup, re-dressed as Heist ────────
# National's whole palette is ten values; each maps to the Heist token that
# does the same JOB (the ground, the surface on it, the accent, bright type,
# the readable muted tier, the label tint, the winner's edge). Applied to the
# INHERITED page only, before the Heist modules go in.
VOL9_HEX = {
    "#6B0F17": "#0F1B2B",  # the ground            -> --mn-navy
    "#520B12": "#13202F",  # surfaces on it        -> --mn-navy-2
    "#1A0A0C": "#0F1B2B",  # ink on light plates   -> --mn-navy
    "#D7202E": "#F26B5B",  # the accent            -> --mn-coral
    "#F7F1E6": "#FFF4E8",  # bright type / plates  -> --mn-sand
    "#F2D0D3": "#B9C6D3",  # readable muted text   -> --mn-mist
    "#F2B8BC": "#FFC9A3",  # label tint            -> --mn-peach
    "#CBBDB6": "#8E9DAE",  # inactive
    "#6B5A52": "#46566A",  # muted ink on a light plate
    "#087A3F": "#2FB7B0",  # the winner's edge     -> --mn-teal
    "#066434": "#23908A", "#0CA856": "#2FB7B0", "#3FA33C": "#2FB7B0", "#BFE3CD": "#BFEAE7",
    "#1A0006": "#0A131E", "#FF6B7A": "#F59A62",
}
VOL9_RGB = {
    "247,241,230": "255,244,232", "242,208,211": "185,198,211", "82,11,18": "19,32,47",
    "242,184,188": "255,201,163", "107,15,23": "15,27,43", "26,10,12": "15,27,43",
    "203,189,182": "142,157,174", "215,32,46": "242,107,91", "8,122,63": "47,183,176",
}


def reskin(s):
    n = {}
    # Vol.9's INK was text on an ivory plate. The plates are Heist glass now,
    # so ink AS TEXT is sand and muted ink is mist; ink as a background (the
    # tab bar, a CTA) stays navy through the table below.
    for ink, to in (("#1A0A0C", "#FFF4E8"), ("#6B5A52", "#B9C6D3")):
        s, k = re.subn(r"(?<![-\w])(color\s*:\s*['\"]?)" + re.escape(ink), lambda m: m.group(1) + to, s, flags=re.I)
        n["ink as text " + ink] = k
    for a, b in VOL9_HEX.items():
        s, k = re.subn(re.escape(a), b, s, flags=re.I); n[a] = k
    for a, b in VOL9_RGB.items():
        pat = r"(rgba?\(\s*)" + r"\s*,\s*".join(a.split(",")) + r"(?=\s*[,)])"
        s, k = re.subn(pat, lambda m: m.group(1) + b.replace(",", ", "), s); n[a] = k
    # the display face: Heist's is upright and condensed (wdth 66), Vol.9's wide italic
    for w in ("125", "118", "112"):
        s, k = re.subn(r"'wdth' " + w + r"\b", "'wdth' 66", s); n["wdth " + w] = k
    s, k = re.subn(r'fontStyle:\s*"italic"', 'fontStyle:"normal"', s); n["italic jsx"] = k
    s, k = re.subn(r"font-style:\s*italic", "font-style: normal", s); n["italic css"] = k
    # Vol.9's ARTWORK (khanjar tile, masar weave, landmark medallions) lives in
    # its skin as data URLs; Heist has none of it, so it is removed, not recoloured
    i = s.index('<style id="vol9-skin">'); j = s.index("</style>", i)
    skin, k = re.subn(r'url\(\s*["\']?data:image/[^)]*\)', "none", s[i:j]); n["vol9 artwork"] = k
    s = s[:i] + skin + s[j:]
    s = s.replace("VOL.9", "VOL.10").replace("Vol.9", "Vol.10")
    # NO ARABIC (owner, 22 Nov): Vol.9 set an Arabic line under every title and
    # in its constants. Every Arabic run in the inherited page goes; a string
    # left empty draws nothing, and the elements around it collapse.
    s, k = re.subn(r"[\u0600-\u06FF\u0750-\u077F\uFB50-\uFDFF\uFE70-\uFEFF]+(?:[ \u00a0·.،:-]*[\u0600-\u06FF\u0750-\u077F\uFB50-\uFDFF\uFE70-\uFEFF]+)*", "", s)
    n["arabic runs"] = k
    assert not re.search(r"[\u0600-\u06FF]", s), "Arabic survived the re-skin"
    left = [a for a in VOL9_HEX if re.search(re.escape(a), s, re.I)]
    assert not left, f"Vol.9 colours survived the re-skin: {left}"
    return s, n


def top_names(js):
    return set(re.findall(r"^(?:function|const|let|var|class)\s+([A-Za-z_$][\w$]*)", js, re.M))


def rebrand_copy(s, S):
    """Every word the organiser POSTS — WhatsApp copy, share captions, the
    link-preview tags. These are the surfaces that leave the app, so a Vol.9
    leftover here is not a stale colour, it is a link to the wrong season
    pasted into the group. Written from heist-season.json, then asserted."""
    host, name = S["host"], S["name"]
    month = S["month"]
    nights, dbl = S["nights"], S["doubleNights"]
    nos = [str(nights.index(d) + 1) for d in dbl]
    dbl_nos = " & ".join(nos) if len(nos) <= 2 else ", ".join(nos[:-1]) + " & " + nos[-1]
    import datetime as _dt
    lab = lambda d: _dt.date.fromisoformat(d).strftime("%a %-d %b")
    dbl_dates = " & ".join(lab(d) for d in dbl)
    pool = S["voucher"] * 2 * len(nights) + sum(S["seasonPrizes"])
    tag = "Now Loading Muscat."
    sched = f"Mon & Wed · {S['schedule'].split(', ')[-1]} · all {month}"
    n = {}
    def sub(a, b, what, count=None):
        nonlocal s
        k = s.count(a)
        assert k, f"rebrand: '{what}' anchor not found"
        if count is not None: assert k == count, f"rebrand: '{what}' matched {k}, expected {count}"
        s = s.replace(a, b); n[what] = k

    # the season announcement and the format post, replaced wholesale
    a0 = s.index("const SEASON_ANNOUNCEMENT = `"); a1 = s.index("`;", a0) + 2
    ann = f"""const SEASON_ANNOUNCEMENT = `🔥🔥🔥 *IT'S BACK* 🔥🔥🔥

*{name.upper()} · Urban Social Series Vol.{S['volume']}*
_{tag}_ ⚡

{S['previousVolume']} is done and dusted — new season, new partners, new rivalries 🏆

━━━━━━━━━━━━━━━━━━━━
📅 *{sched.upper()}*
📍 {S['venue']}
💸 {S['entry']} OMR per player
━━━━━━━━━━━━━━━━━━━━

🗓️ {len(nights)} sessions total · Sessions {dbl_nos} pay *DOUBLE POINTS* 🔥
💰 *{pool} OMR prize pool* up for grabs

━━━━━━━━━━━━━━━━━━━━
Series points reset to *zero* — your *all-time* total carries over 👑

📊 *{name} live tracker:*
https://{host}
━━━━━━━━━━━━━━━━━━━━

Drop your name + partner below to lock your spot 👇

⚠️ *16 teams max · first come, first served*
💥 *{tag}* 👑`;"""
    s = s[:a0] + ann + s[a1:]; n["announcement"] = 1
    sub('|| "Vol. 9";', f'|| "Vol. {S["volume"]}";', "format vol")
    sub("t += `📍 Urban Playground, Oman\\n`;", f"t += `📍 {S['venue']}\\n`;", "format venue", 1)
    sub("t += `🗓️ Mon & Wed · 5:30 PM · all November\\n`;", f"t += `🗓️ {sched}\\n`;", "format schedule", 1)
    i0 = s.index("t += `⚡ *Sessions 6, 8 & 9 pay DOUBLE points*"); i1 = s.index("\n", i0)
    s = s[:i0] + f"t += `⚡ *Sessions {dbl_nos} pay DOUBLE points* — the last two nights, {dbl_dates}. The table can still flip on the last night, so it's never too late to join.\\n\\n`;" + s[i1:]
    n["format doubles"] = 1

    # every caption and link
    sub("national.urbanpadel.om", host, "host")
    sub("NATIONAL.URBANPADEL.OM", host.upper(), "host on cards")
    sub('letterSpacing: "-.01em" }}>NATIONAL</div>', 'letterSpacing: "-.01em" }}>MUSCAT HEIST</div>', "wall title", 1)
    sub("the 56 National Series", f"{name}", "series in captions")
    sub('"56 National Series"', f'"{name}"', "share titles")
    sub("One flag. One court.", tag, "tagline")
    sub("ALL NOVEMBER", f"ALL {month.upper()}", "hero schedule")
    sub("ONE FLAG. <span", "NOW LOADING <span", "hero tagline")
    sub('<span style={{color:"#FFF4E8"}}>ONE COURT.</span>', '<span style={{color:"#FFF4E8"}}>MUSCAT.</span>', "hero tagline 2")
    # the volume's lockup is not on this host: the club mark the app already ships
    sub('<source type="image/webp" srcSet="assets/national-lockup.webp" />', "", "hero webp")
    sub('src="assets/national-lockup.png"', 'src="assets/up-logo-tight.png"', "lockups")
    sub("const NATIONAL_DAY_LABEL = 'Wed 18 Nov';", f"const NATIONAL_DAY_LABEL = '{lab(dbl[0])}';", "2X label", 1)

    # the head: title, description and the link preview
    h0 = s.index("<head>"); h1 = s.index("</head>")
    head = s[h0:h1]
    # Heist is "bring a partner": the inherited "New partners every session" was
    # Americano copy, and it sat under the link right beside a sign-up list
    # asking for name + partner
    import datetime as _dt
    first = _dt.date.fromisoformat(S["nights"][0]).strftime("%a %-d %b")
    _w = ["Zero", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine", "Ten"]
    desc = (f"Social padel in Oman. {_w[len(S['nights'])]} nights, every Mon &amp; Wed at {S['schedule'].split(', ')[-1]} "
            f"from {first}, {S['venue']}. Bring a partner. {pool} OMR prize pool.")
    assert len(desc.replace("&amp;", "&")) <= 150, f"link description is {len(desc)} chars; WhatsApp cuts near 150"
    head = re.sub(r'<meta name="apple-mobile-web-app-title" content="[^"]*" />', f'<meta name="apple-mobile-web-app-title" content="{name}" />', head)
    head = re.sub(r'<meta name="description" content="[^"]*" />', f'<meta name="description" content="{name} — Vol.{S["volume"]} of the Urban Social Series. {desc}" />', head)
    head = re.sub(r'<meta (property|name)="(og|twitter):description" content="[^"]*" />', lambda m: f'<meta {m.group(1)}="{m.group(2)}:description" content="{desc}" />', head)
    # the preview is its own 1200x630 card (build-heist-post.py), served from the
    # SITE ROOT so it exists before and after launch, and stamped with its own
    # hash: Cloudflare caches it for hours and a same-URL re-upload unfurls old
    og = os.path.join(HERE, "brand", "heist", "posts", "og-card.jpg")
    assert os.path.exists(og) and os.path.getsize(og) < 300_000, "og-card.jpg missing or over 300KB (WhatsApp drops it)"
    ogv = hashlib.sha256(open(og, "rb").read()).hexdigest()[:10]
    head = re.sub(r'<meta (property|name)="(og:image|twitter:image)" content="[^"]*" />', lambda m: f'<meta {m.group(1)}="{m.group(2)}" content="https://{host}/og-card.jpg?v={ogv}" />', head)
    # the tab icon was National's red khanjar; a phone's home screen had no icon at all
    head, k = re.subn(r'<link rel="icon"[^>]*/>', '<link rel="icon" type="image/png" sizes="64x64" href="/favicon-64.png" />\n'
                      '<link rel="apple-touch-icon" href="/apple-touch-icon.png" />\n<link rel="manifest" href="/manifest.webmanifest" />', head, count=1)
    assert k == 1, "favicon link not found"
    head = re.sub(r"<title>.*?</title>", f"<title>{name} · Urban Playground</title>", head, count=1, flags=re.S)
    head = re.sub(r'<meta property="og:image:alt" content="[^"]*" />', f'<meta property="og:image:alt" content="{name} — {tag}" />', head)
    s = s[:h0] + head + s[h1:]

    # nothing a visitor reads or a post carries may still name Vol.9. CSS
    # comments are notes about the inherited skin, not copy, so they are skipped.
    visible = re.sub(r"/\*.*?\*/", "", s, flags=re.S)
    visible = re.sub(r"^\s*//.*$", "", visible, flags=re.M)
    for bad in ("national.urbanpadel.om", "NATIONAL.URBANPADEL.OM", ">NATIONAL<", "56 National Series", "ALL NOVEMBER", "all November", "One flag", "NATIONAL DAY NIGHT*", "national-lockup"):
        assert bad not in visible, f"rebrand: '{bad}' still in the page"
    return s, n

def reskin_cards(s):
    """The share cards are drawn on a canvas, so no stylesheet reaches them:
    their palette is NC's constants and a few literals in the painters. The
    National weave and khanjar tile are not drawn; the trim is the Heist
    nights gradient, the ghost numeral is this volume's."""
    a = s.index("/*NA-CANVAS{*/"); b = s.index("/*}NA-CANVAS*/")
    c = s[a:b]
    n = {}
    def sub(x, y, what):
        nonlocal c
        k = c.count(x); assert k, f"cards: '{what}' not found"; c = c.replace(x, y); n[what] = k
    sub('BG: "#B8141F", DEEP: "#9E1520"', 'BG: "#24456E", DEEP: "#13202F"', "ground")
    sub('MUTED: "#8C7B74"', 'MUTED: "#5B6B7E"', "muted (only ever on the sand plate)")
    sub("rgba(158,21,32,", "rgba(19,32,47,", "floor")
    sub('const t = "56";', 'const t = "10";', "ghost numeral")
    sub("if (LU_TILE_IMG) {", "if (false) {", "khanjar tile")
    sub("  const b = LU_BAND_IMG;\n", "  const b = null;\n", "masar band")
    sub("  g.fillStyle = NC.DEEP; g.fillRect(x0, y, w, h);\n",
        "  { const gr = g.createLinearGradient(x0, 0, x0 + w, 0); gr.addColorStop(0, \"#F26B5B\"); gr.addColorStop(1, \"#F5895E\");\n"
        "    g.fillStyle = gr; g.fillRect(x0, y, w, h); }\n", "trim")
    # the plates' own trims: coral, not the weave
    sub("const b = LU_BAND_IMG, h = 16;\n    g.fillStyle = A.DEEP;", "const b = null, h = 16;\n    g.fillStyle = A.FLAG;", "plate trim")
    sub("const b = LU_BAND_IMG, th2 = 14;\n    g.fillStyle = A.DEEP;", "const b = null, th2 = 14;\n    g.fillStyle = A.FLAG;", "champions trim")
    # the landmark medallion: there is no landmark, and an empty ringed disc
    # reads as a missing image, so the block is not drawn at all
    sub("  {\n    const lm = ncLandmark(d);\n", "  if (false) {\n    const lm = ncLandmark(d);\n", "arch medallion")
    sub("  {\n    const lm = ngLandmark(d);\n", "  if (false) {\n    const lm = ngLandmark(d);\n", "list medallion")
    return s[:a] + c + s[b:], n

def launch_day(S):
    # the app opens the day before night one (owner, 23 Nov: "goes live Tue 1 Dec")
    import datetime as _d
    return (_d.date.fromisoformat(S["nights"][0]) - _d.timedelta(days=1)).strftime("%a %-d %b")


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

    s, swept = reskin(s)
    classic_css = open(os.path.join(H, "heist-classic.css"), encoding="utf-8").read()

    # ── fonts: the Heist faces beside the inherited ones, served locally ──
    s = once(s, "</head>",
             '<link rel="stylesheet" href="assets/fonts/brand/fonts.css" />\n'
             '<link rel="stylesheet" href="assets/fonts/heist/fonts.css" />\n'
             f'<style id="heist-css">\n{read("heist.css")}\n</style>\n'
             f'<style id="heist-classic">\n{classic_css}\n</style>\n</head>', "head")

    # ── the inherited universal corner rule stops at the Heist screens ──
    # A Vol.9-era layer rounds EVERY element 28px with !important. The handoff's
    # tags, chips, pills and the knockout cards' badges have their own radii, and
    # in the app (never in the preview, which has no such rule) they all came out
    # as 28px lozenges. Organiser screens keep it: they are not inside .mh-page.
    s = once(s, '*:not(.rounded-full):not([style*="border-radius: 50"]):not([style*="border-radius:50"]) {',
             '*:not(.rounded-full):not([style*="border-radius: 50"]):not([style*="border-radius:50"]):not(.mh-page):not(.mh-page *) {',
             "corner rule scoped")

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
    # A bar in FLOW above the app, not a floating pill: floating, it sat over
    # the score of whatever row was under it, on every screen and every sheet.
    s = once(s, '  <div id="root"></div>', """  <a id="mh-back" href="./" hidden>← Muscat Heist<span>ORGANISER TOOLS</span></a>
  <script>if (new URLSearchParams(location.search).has("classic")) document.getElementById("mh-back").hidden = false;</script>
  <div id="root"></div>""", "classic way back")

    # THE BOOT SPLASH. The inherited page shows a static splash — the club mark
    # and "LOADING..." — for the seconds Babel takes to compile the app, and it
    # is the first thing anybody sees. The owner (24 Nov): "the loading still
    # shows urban playground logo then loading", wanting the GTA-style posters.
    # So the static splash IS the Now Loading screen now, drawn without React:
    # the same poster (same day rotation), the same lockup classes, the same
    # spinner — the React screen takes over on the identical picture. The pan
    # crops a WIDE poster to a tall phone, so it always wants the 1200 cut.
    import re as _re
    posters = [x["art"].rsplit(".", 1)[0] for x in S.get("loadingArt", [])]
    assert posters, "loadingArt is empty: the boot splash has no poster"
    # the owner's logo (25 Nov), the same file MhTitleLockup draws at size M
    lock = (f'<div class="mn-lockup"><span class="mn-logo">'
            f'<img src="assets/heist-logo.webp" alt="Urban Playground {S["nameLine1"]} {S["nameLine2"]}" width="260" height="179" style="width:260px;height:auto"></span>'
            f'<div class="mn-meta">{S["volumeLabel"]} · Muscat · {S["monthShort"]} {S["year"]}</div></div>')
    boot_logo = '<script>window.MH_LOGO="assets/heist-logo";</script>'
    boot = f"""  <div id="splash" class="mh-boot" role="status" aria-label="Now loading Muscat">
    <div class="mhb-art"><img id="mhb-img" alt="" fetchpriority="high"></div>
    <div class="mhb-shade"></div>
    <div class="mhb-lock">{lock}</div>
    <div class="mhb-spin"><span class="mhb-ring"></span><span>NOW LOADING MUSCAT</span></div>
  </div>
  {boot_logo}
  <script>(function(){{var P={json.dumps(posters)};var n=P[Math.floor(Date.now()/864e5)%P.length];
    var i=document.getElementById("mhb-img");i.onerror=function(){{i.onerror=null;i.src="assets/art/"+n+".jpg";}};
    i.src="assets/art/"+n+"-"+(Math.max(innerWidth,innerHeight)*(devicePixelRatio||1)>2400?1600:1200)+".webp";}})();</script>
  <style>
  .mh-boot{{position:fixed;inset:0;z-index:999;background:#0F1B2B;overflow:hidden}}
  .mh-boot .mhb-art{{position:absolute;inset:0}}
  .mh-boot .mhb-art img{{width:100%;height:100%;object-fit:cover;object-position:0% 35%;transform:scale(1.06);animation:mhbPan 4.6s linear forwards}}
  @keyframes mhbPan{{to{{object-position:100% 35%;transform:scale(1.12)}}}}
  .mh-boot .mhb-shade{{position:absolute;inset:0;background:linear-gradient(180deg,rgba(10,16,26,.78),rgba(10,16,26,.35) 26%,rgba(10,16,26,0) 40%,rgba(10,16,26,0) 62%,rgba(10,16,26,.85) 88%)}}
  .mh-boot .mhb-lock{{position:absolute;left:20px;top:calc(58px + env(safe-area-inset-top))}}
  .mh-boot .mn-logo img{{display:block;filter:drop-shadow(0 6px 14px rgba(0,0,0,.55))}}
  .mh-boot .mn-meta{{text-shadow:0 1px 6px rgba(0,0,0,.9)}}
  .mh-boot .mhb-spin{{position:absolute;right:18px;bottom:calc(22px + env(safe-area-inset-bottom));display:flex;align-items:center;gap:10px;font:500 11px/1 'JetBrains Mono',monospace;letter-spacing:.14em;color:#F2E6D8}}
  .mh-boot .mhb-ring{{width:22px;height:22px;border-radius:50%;border:3px solid rgba(255,255,255,.25);border-top-color:#FFC9A3;animation:mhbSpin .8s linear infinite}}
  @keyframes mhbSpin{{to{{transform:rotate(360deg)}}}}
  @media (prefers-reduced-motion:reduce){{.mh-boot .mhb-art img{{animation:none}}.mh-boot .mhb-ring{{animation-duration:2.4s}}}}
  </style>
"""
    s, n = _re.subn(r'  <div id="splash" class="splash">.*?</div></div>\n', lambda m: boot, s, count=1)
    assert n == 1, "inherited splash markup not found"
    assert "up-logo-tight.png\" alt=\"Muscat Heist\"></div><div class=\"splash-chip\"" not in s

    # POSTS and LINE-UP in the inherited night editor opened Vol.9's canvas
    # cards, re-coloured. They open the Heist night share now (the session's
    # number is its date's place in the season's nights).
    for key, kind in (("groups", "draw"), ("lineup", "lineup")):
        old = {"groups": 'go:() => setShowGroupCards(true),', "lineup": 'go:() => setShowLineup(true),'}[key]
        new = ('go:() => { const n = (MH.nights || []).indexOf(session.date) + 1; '
               f'location.href = location.pathname + "#nightshare/" + (n || 1) + "/{kind}"; }},')
        s = once(s, old, new, "classic " + key + " -> night share")
    s = once(s, 'show:lineups.length > 0, warm:true },', 'show:(session.teams || []).length > 0, warm:true },', "line-up shown once there are teams")

    # The selected qualify chip was WHITE on ivory in the inherited markup
    # (1.08:1): the selected state of the one control that decides who goes through.
    s = once(s, 'style={q === currentQC ? { background: "#FFF4E8", color: "#FFFFFF",',
                'style={q === currentQC ? { background: "#FFF4E8", color: "#0F1B2B",', "qualify chip ink")

    s, rb = rebrand_copy(s, S)
    s, rc = reskin_cards(s)
    print("  cards: " + ", ".join(f"{k} {v}" for k, v in rc.items()))
    print("  rebrand: " + ", ".join(f"{k} {v}" for k, v in rb.items()))

    # The nights wore Vol.9's landmarks ("MON 7 DEC · MUSCAT GATE"). Heist has
    # episodes, so the same slot carries the episode title, one per night in
    # order; there is no artwork for them, so the medallion has nothing to draw.
    eps = [{"id": e["code"], "nameEn": e["title"], "nameAr": "", "asset": ""} for e in S["episodes"]]
    s, k = re.subn(r"^const LANDMARKS = \[.*?\];$", lambda m: "const LANDMARKS = " + json.dumps(eps, ensure_ascii=False) + ";", s, count=1, flags=re.M)
    assert k == 1, "LANDMARKS not found"

    # ── compile the JSX here, once, instead of on every phone on every open ──
    # (3.1MB of Babel downloaded and ~900KB compiled before the first frame);
    # ops/precompile-jsx.js runs the same compiler and preset and drops the CDN tag
    import subprocess
    s = subprocess.run(["node", os.path.join(HERE, "ops", "precompile-jsx.js")], input=s, capture_output=True,
                       text=True, check=True).stdout

    # ── stamp ──
    bid = hashlib.sha256(s.encode()).hexdigest()[:12]
    s, n = re.subn(r'(\n\s*var V = )"[0-9a-f]{6,}";', r'\1"%s";' % bid, s, count=1)
    assert n == 1, "build stamp not found"
    open(DST, "w", encoding="utf-8").write(s)
    open(DST + ".version", "w").write(bid + "\n")

    # ── the holding page at the site root until launch day ──
    # A link pasted into the group before Tue 1 Dec lands here, so it carries the
    # app's own <head> tags (title, description, preview card, icons) and nothing else.
    import html as _h
    hd = s[s.index("<head>") + 6:s.index("</head>")]
    tags = "\n".join(m for m in re.findall(r'<meta (?:property|name)="(?:og:[^"]*|twitter:[^"]*|description|theme-color)"[^>]*/>|<link rel="(?:icon|apple-touch-icon|manifest)"[^>]*/>|<title>.*?</title>', hd, flags=re.S))
    hold = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
{tags}
<style>html,body{{margin:0;background:#0F1B2B;color:#F6EAD3;font:16px/1.5 system-ui,sans-serif}}main{{min-height:100dvh;display:grid;place-items:center;text-align:center;padding:24px}}
img{{width:min(300px,70vw);height:auto}}b{{display:block;font-size:22px;letter-spacing:.04em;margin-top:18px}}p{{color:#D8DEE8;margin:8px 0}}a{{color:#FFB36B}}</style>
</head><body data-heist-holding><main><div><img src="/preview/assets/heist-logo.webp" alt="Urban Playground Muscat Heist">
<b>Opens {_h.escape(launch_day(S))}</b><p>{_h.escape(S["schedule"].replace(", ", " · "))} · {_h.escape(S["venue"])}</p>
<p><a href="/photos/">Player photos</a></p></div></main></body></html>"""
    open(os.path.join(HERE, "heist-holding.html"), "w", encoding="utf-8").write(hold)

    left = {t: s.count(t) for t in ("56 NATIONAL SERIES", "national.urbanpadel.om") if s.count(t)}
    print("  re-skin:", ", ".join(f"{k} {v}" for k, v in swept.items() if v))
    print(f"wrote {os.path.basename(DST)}  {len(s) // 1024}KB  build {bid}  pool {pool}  modules {len(MODULES)}")
    if left:
        print("  note — Vol.9 strings still in the page:", left)


if __name__ == "__main__":
    main()
