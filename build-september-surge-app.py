# -*- coding: utf-8 -*-
"""Derive the September Surge (Vol.7) app from the August Attack (Vol.6) app.

Every volume in this series inherits the previous one's markup — that is how
July Heat became August Attack. Doing it as a script rather than a hand-fork
means Vol.6 fixes can be pulled forward by re-running this, and every
substitution is asserted, so a rename that stops matching fails the build
instead of shipping a half-rebranded app.

What it does NOT change: the scoring engine, the bracket seeding, the API
contract. Vol.7 runs the same rules on its own data (ss_* tables, port 3008).

  python3 build-september-surge-app.py
"""
import hashlib, os, re, sys

import surge_screens as SCREENS

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "august-attack-index.html")
DST = os.path.join(HERE, "september-surge-index.html")

# ── Palette: Attack (red-led, court black) -> Surge (cyan-led, deep current) ──
# Two passes via sentinels, because the old secondary (#3DE1FF) and the new
# primary (#00E5FF) are both cyans — a naive sequential replace would collide.
# Tokens are read out of surge-index.html's :root, which is the page built to
# the September Surge design language — not invented here. Surge is a two-colour
# system: cyan leads, amber supports. August's red was the lead, so red -> cyan;
# August's cyan was its second voice (crowns, trophies, badges, the glitch pair),
# so it becomes amber. No third accent is introduced.
COLOURS = [
    # was                     sentinel      becomes      what it is
    ("#FF2E43", "@@P@@", "#00E5FF"),   # lead: Attack Red -> Surge Cyan
    ("#3DE1FF", "@@S@@", "#FF9E1B"),   # support: Ice -> Strike Amber
    ("#1FA8C4", "@@S2@@", "#C77A12"),  # deep variant of the support accent
    ("#8DE8F5", "@@S3@@", "#FFC46B"),  # soft variant of the support accent
    ("#0A0C12", "@@BG@@", "#0A0F14"),  # Court Black -> Deep Current
    ("#06070B", "@@BG2@@", "#050709"), # Deep Black -> Void
    ("#F4F6FA", "@@FG@@", "#F4F9FA"),  # Chalk -> Voltage White
    ("#8B95A7", "@@MU@@", "#8A9BA8"),  # Steel -> Steel Text (see note below)
    # "cyan absorbs green" — the spec retires the separate live/done green.
    ("#27E08A", "@@G1@@", "#00E5FF"),
    ("#1FD9C4", "@@G2@@", "#00E5FF"),
]
# NOTE ON --muted. The handoff's JSX table says #8B95A7 -> #5C6B78, but its own
# contrast note says #5C6B78 is ~3.3:1 on the base and is for bold letterspaced
# kickers only, with #8A9BA8 as "the second steel for body-length secondary
# text". These inline styles are mostly prose-length, so they take #8A9BA8 and
# stay above 4.5:1; the skin layer still re-points the CSS --muted token to
# #5C6B78 for the labels and kickers it was specified for.
# The same colours again as rgb() triples, which the app uses inside rgba().
RGBS = [
    ("255,46,67", "@@RP@@", "0,229,255"),
    ("61,225,255", "@@RS@@", "255,158,27"),
    ("10,12,18", "@@RBG@@", "10,15,20"),
    ("6,7,11", "@@RBG2@@", "5,7,9"),
    ("244,246,250", "@@RFG@@", "244,249,250"),
    ("139,149,167", "@@RMU@@", "138,155,168"),
]
# Motion and depth also differ. Surge overshoots slightly where Attack eased
# flat, and its glow is wider and softer than Attack's tight 14px halo.
MOTION = [
    ("cubic-bezier(.23,1,.32,1)", "cubic-bezier(.34,1.56,.64,1)"),
    ("0 0 14px rgba(0,229,255,.32)",
     "0 0 40px rgba(0,229,255,.24), 0 0 90px rgba(0,229,255,.12)"),
]

# ── Display face. Attack stands tall (Anton); Surge leans forward — Archivo
# pushed wide, heavy and italic, the same treatment surge-index.html uses. This
# is the biggest single "is it Surge or is it Attack in cyan paint" lever, so it
# is done properly rather than left as a colour swap. Both the CSS and the JSX
# inline-style forms are declaration lists, so siblings can be added safely.
# Matched by regex, not exact strings: the Vol.6 app writes this declaration in
# at least five shapes (CSS and JSX, with and without spaces, with 'cursive' or
# 'Impact,sans-serif' fallbacks), and an exact-match table silently missed 35 of
# them on the first attempt — leaving most of the app still standing tall.
DISPLAY_RE = [
    # CSS:  font-family:'Anton',cursive   /   font-family: 'Anton', Impact, sans-serif
    (re.compile(r"font-family:\s*'Anton'[^;}\"']*"),
     "font-family:'Archivo',sans-serif;font-style:italic;"
     "font-variation-settings:'wdth' 125,'wght' 900"),
    # JSX:  fontFamily: "'Anton',cursive"
    (re.compile(r'fontFamily:\s*"\'Anton\'[^"]*"'),
     'fontFamily:"\'Archivo\',sans-serif",fontStyle:"italic",'
     'fontVariationSettings:"\'wdth\' 125,\'wght\' 900"'),
    # The splash preloads the display face by name before first paint.
    (re.compile(r'document\.fonts\.load\("(\d+)px \'Anton\'"\)'),
     r'document.fonts.load("italic \1px Archivo")'),
    # The shareable player card is drawn on a canvas, where the display face is
    # a font shorthand string rather than a CSS declaration. Missing this would
    # leave every card players post to WhatsApp still set in Attack's face.
    (re.compile(r"px \'Anton\', Impact, sans-serif`"),
     "px 'Archivo', sans-serif`"),
    (re.compile(r"ctx\.font = `\$\{([^}]+)\}px 'Archivo', sans-serif`"),
     r"ctx.font = `italic 900 ${\1}px 'Archivo', sans-serif`"),
    (re.compile(r"/\* ── Fonts: Anton for all display text ── \*/"),
     "/* ── Fonts: Archivo, leaned forward, for all display text ── */"),
]
DISPLAY = [
    # Load the variable axes Surge needs instead of Anton. The static Archivo
    # request that Vol.6 also made is dropped in the same step — the variable
    # axes cover every weight it asked for, and requesting the family twice in
    # one URL just fetches a second overlapping face.
    ("family=Anton&", "family=Archivo:ital,wdth,wght@0,62..125,400..900;1,62..125,400..900&"),
    ("family=Archivo:ital,wght@0,400;0,500;0,600;0,700;0,800;0,900;1,700;1,800&", ""),
    ("family=JetBrains+Mono:wght@500;700", "family=JetBrains+Mono:wght@400;500;700"),
]

# ── Assets. The Surge lockup replaces the Attack wordmark; the cyan Urban
# Playground emblem (already on this subdomain) replaces the Attack emblem. ──
ASSETS = [
    ("assets/aa-wordmark.png", "assets/surge-lockup.png"),
    ("assets/aa-emblem.png", "assets/up-logo-cyan.png"),
    ("assets/jh-watermark.png", "assets/surge-lockup.png"),   # splash mark
    ("assets/up-logo.png", "assets/up-logo-cyan.png"),
    ("assets/og-cover.png", "assets/surge-og.png"),
]

# ── Wording. Deliberately NOT replacing the bare word "August", which appears
# in real dates and in copy about the previous volume. ──
TEXT = [
    ("AUGUST ATTACK", "SEPTEMBER SURGE"),
    ("August Attack", "September Surge"),
    ("attack.urbanpadel.om", "surge.urbanpadel.om"),
    ("VOL.6", "VOL.7"),
    ("Vol.6", "Vol.7"),
    ("Vol. 6", "Vol. 7"),
    # Month-bound copy: these run in meta descriptions, the mock signup card and
    # the generated WhatsApp posts, so leaving them would have Vol.7 telling
    # players it runs "all August".
    ("all August", "all September"),
    ("ALL AUGUST", "ALL SEPTEMBER"),
    # Vol.6's tagline. Surge's is set in DESIGN.md / the landing page.
    ("SERVE FIRST. <b>STRIKE HARD.</b>", "RIDE <b>THE SURGE.</b>"),
    # The tagline recurs in three casings across the season config and the
    # generated WhatsApp posts, which is what the organiser actually sends out.
    ("Serve First. Strike Hard.", "Ride The Surge."),
    ("Serve first. Strike hard.", "Ride the surge."),
    ("URBAN SOCIAL SERIES · VOL. 6", "URBAN SOCIAL SERIES · VOL. 7"),
    ("VOL. 6", "VOL. 7"),
    # Vol.6 shipped with Vol.5 as its "previous series"; Vol.7's is Vol.6.
    ('"June Fury", "July Heat"]', '"June Fury", "July Heat", "August Attack"]'),
    ("July Heat is done and dusted", "August Attack is done and dusted"),
    # Vol.6 told players their previous *series* points carried over. For Vol.7
    # only the all-time total does: the series table starts at zero, while
    # prevSeriesPts keeps every earlier volume alive in the all-time ranking.
    # Saying either half alone would be wrong, so the line says both.
    ("Your *July Heat* points carry over — but the throne is wide open 👑",
     "Series points reset to *zero* — your *all-time* total carries over 👑"),
    ("🏆 *July Heat final standings:*\nheat.urbanpadel.om → Leaderboard",
     "🏆 *August Attack final standings:*\nattack.urbanpadel.om → Leaderboard"),
]

# Direction. The spec makes everything that can imply direction point right:
# navigational and call-to-action arrows become ▶. Rank movement arrows are
# already ▲▼ and are deliberately left alone.
ARROWS = [("→", "▶")]

# A third place where the blanket swap gives the wrong answer, alongside the two
# the handoff names. This button was August's cyan (its support accent), so the
# #3DE1FF -> amber rule turned it amber — but the spec is explicit that Strike
# Amber is for "live-now and urgency states only", and "see all-time rankings"
# is neither. It is a navigation CTA, so it takes the lead colour.
POST_SWEEP = [
    ('color:"#0A0F14",background:"#FF9E1B",border:"none",padding:"10px 20px 8px",'
     'cursor:"pointer",boxShadow:"0 0 22px rgba(255,158,27,.35)"',
     'color:"#050709",background:"#00E5FF",border:"none",padding:"10px 20px 8px",'
     'cursor:"pointer",boxShadow:"0 0 30px rgba(0,229,255,.4)"'),
]


SKIN = os.path.join(HERE, "ops", "surge-skin.css")


RANK_ANCHOR = "  // Rank 4+, collapsed to one line:"
RANK_END = "\n}\n\nfunction PlayerDetail("

# Section 06 of the design language is the RANK screen, and the handoff is
# explicit that it "is the screen that tests the skin". Vol.6 renders the top
# three as a three-up podium of rotated cards with a crown, which no amount of
# CSS re-pointing turns into Surge's language — the spec replaces it with three
# full-width rows carrying the rising bar, and moves the pinned YOU row above
# them, directly under the search.
#
# So this is the one place the build rewrites markup rather than re-skinning it.
# It swaps the render half of LeaderboardView only; every value it draws
# (`ptsOf`, `enrich`, `moveOf`, `climber`, `restMain`, `restTail`, `found`,
# `ThinRow`) is computed by the half above, which is untouched, so no scoring
# or ranking behaviour changes with it.
RANK_JSX = r'''  // ── RANKS 4+ (design language, section 06) ──
  // A plain table: rank, name, movement, win %, points. No photo, no bar,
  // no pill strip — those are spent on the top three and the pinned YOU row
  // and nowhere else, or the accent stops meaning anything. Rows run about
  // 42pt against August's 88, so 48 ranks fit in roughly three screens.
  const ThinRow = ({ e, i }) => {
    const en = enrich(e);
    const isMe = e.player.id === meId;
    return (
      <div onClick={() => setOpenPlayerId(e.player.id)} className="sg-thin"
        style={{display:"flex",alignItems:"center",gap:10,padding:"10px 4px",
                borderTop:"1px solid rgba(92,107,120,.18)",cursor:"pointer",
                background:isMe ? "rgba(255,158,27,.07)" : "none"}}>
        <div style={{width:20,flex:"0 0 auto",fontFamily:"'JetBrains Mono',monospace",fontSize:12,
                     color:isMe ? "#FF9E1B" : "#5C6B78"}}>{i + 1}</div>
        <div style={{flex:1,minWidth:0,display:"flex",alignItems:"center",gap:6}}>
          <span style={{fontFamily:"'Archivo',sans-serif",fontWeight:800,fontSize:15,color:"#F4F9FA",
                        overflow:"hidden",textOverflow:"ellipsis",whiteSpace:"nowrap"}}>{e.player.name}</span>
          {en.streak >= 3 && <span style={{display:"inline-flex",flex:"0 0 auto"}}><CIc.flame size={12} /></span>}
        </div>
        {mode === "season" && <MoveChip mv={moveOf(e, i)} />}
        <div style={{width:32,flex:"0 0 auto",textAlign:"right",fontFamily:"'JetBrains Mono',monospace",
                     fontSize:10,color:"#5C6B78"}}>{hasPlayed(e) ? en.winRate + "%" : "–"}</div>
        <div style={{width:30,flex:"0 0 auto",textAlign:"right",fontFamily:"'JetBrains Mono',monospace",
                     fontSize:15,fontWeight:700,color:"#F4F9FA"}}>{ptsOf(e)}</div>
      </div>
    );
  };

  // ── TOP THREE (design language, section 06) ──
  // One card signature, spent where it means something: only the top three
  // carry a rising bar, and only first place carries the bloom. The bar is
  // the same 3px gradient the panels use, so RANK reads as the same system.
  const TopRow = ({ e, i }) => {
    const en = enrich(e), lead = i === 0;
    const bar = lead ? "#00E5FF" : "#5C6B78";
    const isClimber = climber && climber.e.player.id === e.player.id;
    return (
      <div onClick={() => setOpenPlayerId(e.player.id)}
        className="sg-top" data-lead={lead ? "1" : "0"}
        style={{display:"flex",alignItems:"center",gap:11,cursor:"pointer",
                background:"#050709",padding:"12px 12px 12px 15px",
                backgroundImage:`linear-gradient(180deg,${bar},${lead ? "rgba(0,229,255,.06)" : "rgba(92,107,120,.06)"})`,
                backgroundSize:"3px 100%",backgroundPosition:"left top",backgroundRepeat:"no-repeat",
                boxShadow:lead ? "0 0 30px rgba(0,229,255,.12)" : "none"}}>
        <div style={{width:20,flex:"0 0 auto",fontFamily:"'JetBrains Mono',monospace",fontSize:15,
                     fontWeight:700,color:bar}}>{i + 1}</div>
        <Avatar player={e.player} size={38} />
        <div style={{flex:1,minWidth:0,display:"flex",flexDirection:"column",gap:3}}>
          <div style={{fontFamily:"'Archivo',sans-serif",fontStyle:"italic",fontVariationSettings:"'wdth' 118,'wght' 800",
                       fontSize:19,lineHeight:1,textTransform:"uppercase",color:"#F4F9FA",
                       overflow:"hidden",textOverflow:"ellipsis",whiteSpace:"nowrap"}}>{e.player.name}</div>
          <div style={{fontFamily:"'JetBrains Mono',monospace",fontSize:9.5,color:"#5C6B78",
                       display:"flex",alignItems:"center",gap:5,minWidth:0,overflow:"hidden",whiteSpace:"nowrap"}}>
            {e.stats.sessionsPlayed > 0
              ? <span>{e.stats.sessionsPlayed} SESS &middot; {en.winRate}% WIN</span>
              : <span>CARRIED OVER</span>}
            {/* Biggest climber is a fact inside the player's own row, not the
                striped banner above the list it was in August. */}
            {isClimber
              ? <span>&middot; &#9650;{climber.n} BIGGEST CLIMBER</span>
              /* The form run is set as mono letters, not August's green/red
                 chips: on this screen colour is reserved for rank, and five
                 traffic lights per row is exactly the noise section 06 is
                 written to remove. */
              : en.form.length > 0 && <span style={{letterSpacing:".08em"}}>&middot; {en.form.join("")}</span>}
          </div>
        </div>
        <div className="sg-top-pts" style={{flex:"0 0 auto",fontFamily:"'JetBrains Mono',monospace",fontSize:23,fontWeight:700,
                     color:lead ? "#00E5FF" : "#F4F9FA"}}>{ptsOf(e)}</div>
      </div>
    );
  };

  // ── THE PINNED YOU ROW ──
  // The one place Strike Amber appears on this screen: it is the only row
  // about the person holding the phone. Sits under the search, above the
  // top three, and steps aside when they are already in the top three.
  const MeRow = () => {
    const mi = meId ? list.findIndex(e => e.player.id === meId) : -1;
    if (mi < 3) return null;
    const e = list[mi], mv = moveOf(e, mi);
    return (
      <div onClick={() => setOpenPlayerId(e.player.id)}
        style={{display:"flex",alignItems:"center",gap:11,cursor:"pointer",
                background:"#050709",padding:"10px 12px 10px 15px",
                backgroundImage:"linear-gradient(180deg,#FF9E1B,rgba(255,158,27,.08))",
                backgroundSize:"3px 100%",backgroundPosition:"left top",backgroundRepeat:"no-repeat"}}>
        <div style={{fontFamily:"'Archivo',sans-serif",fontWeight:800,letterSpacing:".34em",
                     textTransform:"uppercase",fontSize:8.5,color:"#FF9E1B"}}>You</div>
        <div style={{fontFamily:"'JetBrains Mono',monospace",fontSize:12,fontWeight:700,color:"#5C6B78"}}>{mi + 1}</div>
        <div style={{flex:1,minWidth:0,fontFamily:"'Archivo',sans-serif",fontStyle:"italic",
                     fontVariationSettings:"'wdth' 118,'wght' 800",fontSize:17,textTransform:"uppercase",
                     color:"#F4F9FA",overflow:"hidden",textOverflow:"ellipsis",whiteSpace:"nowrap"}}>{e.player.name}</div>
        {mode === "season" && <MoveChip mv={mv} />}
        <div style={{fontFamily:"'JetBrains Mono',monospace",fontSize:16,fontWeight:700,color:"#F4F9FA"}}>{ptsOf(e)}</div>
        <button onClick={(ev) => { ev.stopPropagation(); onOpenPicker(); }}
          style={{background:"none",border:"none",cursor:"pointer",padding:"2px 0",
                  fontFamily:"'JetBrains Mono',monospace",fontWeight:700,fontSize:9,
                  letterSpacing:".14em",color:"#5C6B78"}}>NOT YOU?</button>
      </div>
    );
  };

  return (
    <div className="space-y-4">
      <div className="flex items-end justify-between" style={{paddingTop:8}}>
        <div>
          <div className="jh-sec-kicker">Series Standings</div>
          <h2 className="jh-sec-title">RANKINGS</h2>
        </div>
        {active.length > 0 && (
          <span style={{fontFamily:"'JetBrains Mono',monospace",fontSize:10,letterSpacing:".12em",
                        color:"#5C6B78",border:"1px solid rgba(92,107,120,.3)",padding:"5px 8px",
                        whiteSpace:"nowrap"}}>{active.length} RANKED</span>
        )}
      </div>

      {/* The active segment is a solid cyan fill, same as the primary button
          on HOME, so "the filled cyan thing is the live one" holds app-wide. */}
      {hasLifetime && (
        <div style={{display:"flex",border:"1px solid rgba(92,107,120,.3)"}}>
          {["season","lifetime"].map(m => (
            <button key={m} onClick={() => setMode(m)}
              style={{flex:1,textAlign:"center",padding:"10px 0",border:"none",cursor:"pointer",
                      fontFamily:"'Archivo',sans-serif",fontStyle:"italic",
                      fontVariationSettings:"'wdth' 118,'wght' 800",fontSize:14,textTransform:"uppercase",
                      background:mode===m?"#00E5FF":"transparent",color:mode===m?"#050709":"#5C6B78",
                      boxShadow:mode===m?"0 0 24px rgba(0,229,255,.3)":"none"}}>
              {m === "season" ? "This series" : "All-time"}
            </button>
          ))}
        </div>
      )}

      <Input value={q} onChange={setQ} placeholder="Find a player&hellip;" />

      {q ? (
        <div>
          {found.length === 0
            ? <div style={{padding:"18px 4px",fontFamily:"'JetBrains Mono',monospace",fontSize:11,
                           letterSpacing:".1em",color:"#5C6B78",textTransform:"uppercase"}}>No ranked player by that name</div>
            : found.map(({ e, i }) => <ThinRow key={e.player.id} e={e} i={i} />)}
        </div>
      ) : list.length === 0 ? (
        <>
        <Card className="p-8 text-center border-dashed">
          <I.trophy className="mx-auto mb-3 text-stone-600" size={32} />
          <div className="text-stone-300 font-semibold">Ranking locked</div>
          <div className="text-stone-500 text-sm mt-1">Standings appear after the first match is played</div>
        </Card>
        {hasLifetime && mode === "season" && (
          <div style={{textAlign:"center",marginTop:14}}>
            <button onClick={() => setMode("lifetime")} style={{fontFamily:"'Archivo',sans-serif",fontStyle:"italic",fontVariationSettings:"'wdth' 118,'wght' 800",fontSize:14,letterSpacing:2,color:"#050709",background:"#00E5FF",border:"none",padding:"10px 20px 8px",cursor:"pointer",boxShadow:"0 0 30px rgba(0,229,255,.4)"}}>SEE ALL-TIME RANKINGS &#9654;</button>
          </div>
        )}
        </>
      ) : (
        <>
          <MeRow />
          <div style={{display:"flex",flexDirection:"column",gap:7,marginTop:14}}>
            {podium.map((e, i) => <TopRow key={e.player.id} e={e} i={i} />)}
          </div>

          {/* ── RANKS 4+ — a plain table, and a quiet tail ──
              Thin rows run about 42pt against August's 88, so the ranked
              field fits in roughly three screens instead of ten. restTail
              (a single-match walk-on on TAIL_MAX pts or fewer) sits behind
              one tap. */}
          {restMain.length > 0 && (
            <div style={{marginTop:8}}>
              {restMain.map(({ e, i }) => <ThinRow key={e.player.id} e={e} i={i} />)}
            </div>
          )}
          {restTail.length > 0 && (showTail
            ? <div>{restTail.map(({ e, i }) => <ThinRow key={e.player.id} e={e} i={i} />)}</div>
            : <button onClick={() => setShowTail(true)}
                style={{width:"100%",textAlign:"left",background:"none",border:"none",
                        borderTop:"1px solid rgba(92,107,120,.18)",padding:"14px 4px",cursor:"pointer",
                        fontFamily:"'JetBrains Mono',monospace",fontSize:10,fontWeight:700,
                        letterSpacing:".14em",color:"#00E5FF",textTransform:"uppercase"}}>
                Show {restTail.length} more on {TAIL_MAX} pts or fewer &#9654;
              </button>)}
        </>
      )}
    </div>
  );
'''


# HOME's top-three block still carried August's medal treatment: the panel
# took `.jh-fill-blue`, and `--blue` is Vol.7's amber, so the one card on HOME
# that is not urgent wore the urgency accent; and the first-place chip was that
# same amber over silver and bronze. Both break rules the spec states outright
# — amber is live-now and urgency only, and gold stays out of the palette in
# favour of the cyan / #C3D0D8 / steel ladder.
#
# `.jh-fill-blue` carries `--blue`, and the skin maps that family to amber. It
# is worn by the two largest panels in the app (HOME's top three, SESSIONS'
# list), neither of which is urgent, so both move to the cyan family.
HOME_MEDALS = [
    ('<div className="jh-panel jh-fill-blue" style={{transform:"none"}}>',
     '<div className="jh-panel jh-fill-red" style={{transform:"none"}}>', 2),
    ('style={{background: i === 0 ? "var(--blue)" : i === 1 ? "#C9C9C9" : "#8A9BA8"}}',
     'style={{background: i === 0 ? "#00E5FF" : i === 1 ? "#C3D0D8" : "#5C6B78",'
     ' color: "#050709"}}', 1),
    # The crown above first place is drawn as an inline SVG with a hardcoded
    # fill, so neither the colour sweep nor the skin reaches it. Gold stays
    # out of the palette and amber is urgency-only, so it takes the cyan.
    ('<path d="M2.5 5.5 L7 9.5 L12 2 L17 9.5 L21.5 5.5 L19.5 14.5 H4.5 Z" fill="#FF9E1B"',
     '<path d="M2.5 5.5 L7 9.5 L12 2 L17 9.5 L21.5 5.5 L19.5 14.5 H4.5 Z" fill="#00E5FF"', 1),
]


UX_LAYER = '\n\n/* ══ 9 · UX REFINEMENT LAYER (Vol.7, second pass) ═══════════════════════\n   Applied from the UI/UX enhancement bundle. Visual only: no scoring, no\n   API, no routing. Three things from that bundle were deliberately NOT\n   taken, and are recorded here so the next volume does not "restore" them:\n\n     · the session tab-bar rebuild (4-up grid + action row) — an IA change,\n       and the owner chose to keep the single scrolling chip row;\n     · every `table` / `tbody` / `td` / `th` rule — this app has no <table>\n       anywhere; group standings are divs, so those rules matched nothing;\n     · `tbody tr:nth-child(-n+2)` as "the qualifiers" — qualification here\n       is 1, 2 or 4 per group, or top-2-plus-best-thirds, or all thirds.\n       Rebuilt below against the real rule instead.\n   ────────────────────────────────────────────────────────────────────── */\n\n:root{\n  --sg-plate-1:rgba(9,14,20,.94);\n  --sg-plate-2:rgba(16,23,31,.96);\n  --sg-text-2:#9FB0BC;            /* secondary prose — 4.5:1 on the base */\n  --sg-hit:44px;\n  --sg-t:170ms cubic-bezier(.2,.7,.3,1);\n}\n\n/* ── 9.1 HIERARCHY ─────────────────────────────────────────────────── */\n.text-stone-400,.text-stone-500,[class*="bg-stone-9"] .text-stone-400,\n[class*="bg-stone-9"] .text-stone-500{ color:var(--sg-text-2) !important; }\n.text-stone-600{ color:#7C8B98 !important; }\n\n.jh-panel,[class*="bg-stone-9"]:not(nav):not(header):not(.sticky){\n  padding-top:16px !important; padding-bottom:16px !important;\n  padding-right:16px !important;\n  background-color:var(--sg-plate-1) !important;\n}\n.jh-panel .jh-mock-row,.jh-panel .jh-mock-sess,\n[class*="bg-stone-9"] [class*="bg-stone-9"]{\n  padding-top:11px !important; padding-bottom:11px !important;\n}\n\nlabel,.uppercase.tracking-wider,.uppercase.tracking-wide{\n  font-family:\'Archivo\',sans-serif !important; font-style:normal !important;\n  font-weight:800 !important; letter-spacing:.2em !important;\n  color:var(--surge-steel) !important;\n}\n.font-mono,.sg-top-pts,.sg-thin-pts{ font-variant-numeric:tabular-nums; }\n.jh-sec-title{ margin-bottom:14px !important; }\n\n/* ── 9.2 ENERGY ─────────────────────────────────────────────────────\n   Retargeted. The bundle aimed these at .jh-srow / .jh-lbrow, which this\n   build stopped using when RANK was rebuilt to the design language —\n   they matched nothing. The real hooks are the classes below.        */\n.sg-top{ position:relative; }\n.sg-top[data-lead="1"]{ overflow:hidden; }\n.sg-top[data-lead="1"]::after{\n  content:"";position:absolute;inset:0;pointer-events:none;\n  background:linear-gradient(105deg,transparent 38%,rgba(0,229,255,.10) 50%,transparent 62%);\n  transform:translateX(-120%);animation:sgSheen 6s ease-in-out infinite;\n}\n@keyframes sgSheen{ 0%,72%{transform:translateX(-120%)} 100%{transform:translateX(120%)} }\n\n.jh-mock-sess[data-live="1"]{\n  background-color:rgba(0,229,255,.07) !important;\n  box-shadow:inset 0 0 0 1px rgba(0,229,255,.22) !important;\n}\n\nbutton[style*="00E5FF"]{\n  background-image:linear-gradient(100deg,rgba(255,255,255,.22),transparent 46%) !important;\n  transition:transform var(--sg-t),box-shadow var(--sg-t),filter var(--sg-t) !important;\n}\n\n/* ── 9.3 FEEDBACK — every tap answers ──────────────────────────────── */\nbutton,[role="button"],.jh-mock-row,.jh-mock-sess,.jh-chipbtn,.sg-top,.sg-thin{\n  transition:transform var(--sg-t),background-color var(--sg-t),\n             box-shadow var(--sg-t),color var(--sg-t),opacity var(--sg-t);\n  -webkit-tap-highlight-color:transparent;\n}\nbutton:active,[role="button"]:active,.jh-chipbtn:active{ transform:scale(.955); }\n.jh-mock-row:active,.jh-mock-sess:active,.sg-top:active,.sg-thin:active{\n  transform:scale(.99);background-color:rgba(0,229,255,.10) !important;\n}\nbutton:focus-visible,a:focus-visible,input:focus-visible,select:focus-visible,\ntextarea:focus-visible{ outline:2px solid var(--surge-cyan) !important;outline-offset:2px !important; }\nnav.fixed button{ min-height:var(--sg-hit); }\n\n/* a value that just changed says so. No display change: the bundle set\n   display:inline-block here, which would have collapsed any flex or grid\n   child it landed on, and every number in this app is one. */\n@keyframes sgBump{ 0%{transform:none} 34%{transform:scale(1.16);filter:brightness(1.5)} 100%{transform:none} }\n.sg-bump{ animation:sgBump 420ms var(--ease-out); }\n\n.sg-ripple{\n  position:fixed;z-index:9999;pointer-events:none;border-radius:50%;\n  width:16px;height:16px;margin:-8px 0 0 -8px;\n  background:radial-gradient(circle,rgba(0,229,255,.5),rgba(0,229,255,0) 70%);\n  animation:sgRip 460ms ease-out forwards;\n}\n@keyframes sgRip{ to{ transform:scale(7);opacity:0 } }\n\n/* staggered entrance, first screenful only */\nmain .sg-top,main .jh-panel,main .jh-mock-sess{ animation:sgRowIn 320ms var(--ease-out) both; }\n@keyframes sgRowIn{ from{opacity:0;transform:translateX(-8px)} to{opacity:1;transform:none} }\nmain .sg-top:nth-child(2){animation-delay:40ms}\nmain .sg-top:nth-child(3){animation-delay:80ms}\n\n/* ── 9.4 BOTTOM NAV — the active tab reads at a glance ─────────────── */\nnav.fixed button[style*="color: var(--orange-br)"],\nnav.fixed button[style*="color:var(--orange-br)"]{ position:relative; }\nnav.fixed button[style*="color: var(--orange-br)"]::before,\nnav.fixed button[style*="color:var(--orange-br)"]::before{\n  content:"";position:absolute;top:-6px;left:22%;right:22%;height:3px;\n  background:var(--surge-cyan);box-shadow:0 0 14px rgba(0,229,255,.7);\n}\nnav.fixed button[style*="color: var(--orange-br)"] svg,\nnav.fixed button[style*="color:var(--orange-br)"] svg{\n  filter:drop-shadow(0 0 8px rgba(0,229,255,.55));\n}\n\n/* ── 9.5 BACKGROUND MOTIF — diagonal speed streaks ──────────────────\n   Replaces the surge trace from section 1. Same single cyan at the same\n   weight; the read is forward motion rather than an oscilloscope line.\n   Two layers so the rhythm is not uniform. Chosen by the owner over the\n   trace. Note the position is NOT !important — pinning it is what froze\n   the trace\'s drift the first time round.                            */\nhtml body::before{\n  background-image:\n    repeating-linear-gradient(66deg,\n      rgba(0,229,255,.10) 0 1px, transparent 1px 92px),\n    repeating-linear-gradient(66deg,\n      rgba(0,229,255,.05) 0 2px, transparent 2px 31px) !important;\n  background-size:auto !important;\n  background-repeat:repeat !important;\n  background-position:0 0;\n  animation:sgStreaks 22s linear infinite !important;\n}\n@keyframes sgStreaks{ to{ background-position:-276px -620px, -138px -310px } }\n\n/* ── 9.6 MEDIA ──────────────────────────────────────────────────────── */\n.aa-wall > div{ transition:transform var(--sg-t),box-shadow var(--sg-t); }\n.aa-wall > div:active{ transform:scale(.98); }\n@media (hover:hover){\n  .aa-wall > div:hover{ box-shadow:0 0 0 1px rgba(0,229,255,.5),0 0 30px rgba(0,229,255,.2); }\n}\n\n/* ── 9.9 SCREEN PRIMITIVES ─────────────────────────────────────────
   The classes the rebuilt HOME / SESSIONS / RANK views reference. Kept as
   classes rather than inline styles because they repeat across all three.  */

.sg-kicker{
  font-family:'Archivo',sans-serif !important;
  font-weight:800 !important; font-style:normal !important;
  font-size:10px !important; letter-spacing:.34em !important;
  text-transform:uppercase !important; color:var(--sg-text-2) !important;
  margin:0 !important; padding:0 !important; background:none !important;
  border:none !important; box-shadow:none !important; display:block !important;
}
.sg-card{
  background:rgba(9,14,20,.94);
  border:none;
}
.sg-card-cyan{
  background:rgba(16,23,31,.96);
  background-image:linear-gradient(180deg,#00E5FF,rgba(0,229,255,.06));
  background-size:3px 100%; background-repeat:no-repeat;
}
.sg-livedot{
  position:relative; display:block; width:7px; height:7px; border-radius:50%;
  background:var(--surge-cyan); box-shadow:0 0 10px rgba(0,229,255,.8);
  animation:sgBar 2s ease-in-out infinite;
}
@keyframes sgBar{ 0%,100%{opacity:.55} 50%{opacity:1} }
@keyframes sgSlide{ from{opacity:0;transform:translateX(-10px)} to{opacity:1;transform:none} }

@media (prefers-reduced-motion:reduce){
  .sg-livedot{ animation:none !important; }
}

/* ── 9.7 QUALIFYING ROWS — the real rule ────────────────────────────\n   Driven by data-qual, which GroupsTab sets from qualifyingTeamIds() —\n   the same computation seedQF uses. So this marks 1, 2 or 4 rows per\n   group, or top-2-plus-the-two-best-thirds, or all three, according to\n   the session\'s own format, and it follows the scores live.         */\n.sg-standrow[data-qual="1"]{\n  box-shadow:inset 3px 0 0 var(--surge-cyan);\n  background-color:rgba(0,229,255,.05) !important;\n}\n\n/* ── 9.8 SESSION SCREEN — scale and presence ────────────────────────\n   The overlay carried a whole night\'s scoring at 11–14px. Scoped to the\n   session overlay so nothing else shifts. The bundle\'s table rules are\n   dropped (no tables exist); the group-heading rules are retargeted at\n   the markup this app actually renders.                             */\n.fixed.inset-0.z-40 .text-sm{ font-size:15px !important; line-height:1.35 !important; }\n.fixed.inset-0.z-40 .text-xs{ font-size:13px !important; line-height:1.4 !important; }\n.fixed.inset-0.z-40 .text-\\[11px\\]{ font-size:12.5px !important; line-height:1.45 !important; }\n.fixed.inset-0.z-40 .text-\\[10px\\]{ font-size:11px !important; letter-spacing:.16em !important; }\n.fixed.inset-0.z-40 .text-\\[9px\\]{ font-size:11px !important; }\n.fixed.inset-0.z-40 .font-display.text-xl{ font-size:26px !important; line-height:1 !important; }\n\n.fixed.inset-0.z-40 button.w-full.flex.items-center{\n  min-height:56px !important; padding:10px 12px !important;\n  border-bottom:1px solid rgba(92,107,120,.16) !important;\n}\n.fixed.inset-0.z-40 button.w-full.flex.items-center .truncate{\n  font-family:\'Archivo\',sans-serif !important; font-weight:800 !important;\n  font-size:17px !important; letter-spacing:-.005em !important; color:var(--surge-white) !important;\n}\n.fixed.inset-0.z-40 .font-mono{ font-variant-numeric:tabular-nums; font-size:14px !important; }\n.fixed.inset-0.z-40 .sg-standrow{ padding-top:9px !important; padding-bottom:9px !important; }\n.fixed.inset-0.z-40 .border-dashed{\n  font-size:13px !important; padding:18px !important;\n  border-color:rgba(0,229,255,.22) !important; color:var(--sg-text-2) !important;\n  letter-spacing:.12em !important; text-transform:uppercase !important;\n}\n\n@media (prefers-reduced-motion:reduce){\n  html body::before{ animation:none !important; }\n  .sg-top[data-lead="1"]::after{ animation:none !important; }\n  main .sg-top,main .jh-panel,main .jh-mock-sess,.sg-bump{ animation:none !important; }\n  .sg-ripple{ display:none !important; }\n}\n'

UX_SCRIPT = '\n<script>\n/* Presentational only — a press ripple and a bump on numbers that change.\n   Reads no state, writes no state, touches no React props. */\n(function(){\n  if (matchMedia("(prefers-reduced-motion:reduce)").matches) return;\n\n  document.addEventListener("pointerdown", function(e){\n    var t = e.target.closest && e.target.closest(\n      "button,[role=\'button\'],.jh-mock-row,.jh-mock-sess,.sg-top,.sg-thin,.jh-chipbtn");\n    if (!t) return;\n    var r = document.createElement("span");\n    r.className = "sg-ripple";\n    r.style.left = e.clientX + "px";\n    r.style.top  = e.clientY + "px";\n    document.body.appendChild(r);\n    setTimeout(function(){ r.remove(); }, 480);\n  }, { passive: true });\n\n  // Bump whichever number just changed. Guarded three ways: not during the\n  // first paint, not inside a field the user is typing in, and never more\n  // than a handful at once — a full-table re-render after a server sync\n  // would otherwise flash the whole screen.\n  var boot = Date.now();\n  var mo = new MutationObserver(function(muts){\n    if (Date.now() - boot < 1500) return;\n    if (muts.length > 12) return;\n    muts.forEach(function(m){\n      var el = m.target.nodeType === 3 ? m.target.parentElement : m.target;\n      if (!el || !el.classList) return;\n      if (!/^[\\d\\s.,:+\\-–]+$/.test((el.textContent || "").trim())) return;\n      if (el.closest("input,textarea,nav")) return;\n      el.classList.remove("sg-bump");\n      void el.offsetWidth;\n      el.classList.add("sg-bump");\n      setTimeout(function(){ el.classList.remove("sg-bump"); }, 460);\n    });\n  });\n  (function start(){\n    var root = document.getElementById("root");\n    if (!root) return setTimeout(start, 400);\n    mo.observe(root, { subtree: true, characterData: true });\n  })();\n})();\n</script>\n'


QUALIFY = [
    ('function getQualifyCount(session) {\n  return session?.qualifyCount || 2;  // default: top 2 per group qualify\n}',
     'function getQualifyCount(session) {\n  return session?.qualifyCount || 2;  // default: top 2 per group qualify\n}\n\n// Which teams are currently on course to qualify — the same rule seedQF uses,\n// so a group table can never promise a spot the bracket won\'t honour. There is\n// no single "top N" in this series: it is qualifyCount per group (1, 2 or 4),\n// except that 3 groups is fixed at top-2 plus the two best thirds, and\n// 4-groups/all-thirds sends every third through to a round of 16.\nfunction qualifyingTeamIds(session) {\n  const groups = getSessionGroups(session);\n  const N = groups.length;\n  const stand = groups.map(g => calcGroupStandingsNormalized(session, g));\n  const ids = new Set();\n  const take = (rows, n) => rows.slice(0, n).forEach(r => r && r.team && r.team.id && ids.add(r.team.id));\n\n  if (N === 4 && session && session.thirdPlaceMode === "all4r16") {\n    stand.forEach(rows => take(rows, 3));\n    return ids;\n  }\n  if (N === 3) {\n    stand.forEach(rows => take(rows, 2));\n    // the two best thirds, ranked exactly the way the bracket ranks them\n    const thirds = stand.map(rows => rows[2]).filter(r => r && r.team && r.team.id)\n      .map(r => ({ id: r.team.id, pts: r.pts, wins: r.wins, gd: r.gd || 0, gf: r.gf || 0 }));\n    thirds.sort(compareThirds).slice(0, 2).forEach(t => ids.add(t.id));\n    return ids;\n  }\n  stand.forEach(rows => take(rows, getQualifyCount(session)));\n  return ids;\n}', 1),
    ('  const groups = getSessionGroups(session);\n  const groupSizes = groups.map(g => (session.teams || []).filter(t => t.group === g).length);',
     '  const groups = getSessionGroups(session);\n  // Recomputed every render, so the marks track the scores as results go in\n  // rather than freezing at whatever was true when the bracket was seeded.\n  const qualIds = qualifyingTeamIds(session);\n  const groupSizes = groups.map(g => (session.teams || []).filter(t => t.group === g).length);', 1),
    ('                const isTop = s.team.id === top;\n                return <div key={s.team.id} className="flex items-center gap-2 px-2 py-1.5 rounded-md"',
     '                const isTop = s.team.id === top;\n                const isQual = qualIds.has(s.team.id);\n                return <div key={s.team.id} data-qual={isQual ? "1" : "0"} className="sg-standrow flex items-center gap-2 px-2 py-1.5 rounded-md"', 1),
]


VERSION_CHECK = ('(function(){\n  var V = "20260701_000001";\n  fetch("/version.txt?_=" + Date.now(), { cache: "no-store" })\n    .then(function(r){ return r.text(); })\n    .then(function(v){\n      v = v.trim();\n      var stored = localStorage.getItem("jh-build");\n      if (stored && stored !== v) { localStorage.setItem("jh-build", v); location.reload(true); }\n      else { localStorage.setItem("jh-build", v); }\n    }).catch(function(){});\n})();',
                 '(function(){\n  // Self-healing update check.\n  //\n  // The version this document was BUILT as — stamped by\n  // build-september-surge-app.py from the file\'s own content hash, and\n  // written to version.txt by the same deploy. So the comparison below is\n  // "is the page I am running the page the server now has", which is the\n  // actual question. It replaces a localStorage marker that could not\n  // answer it: the old code wrote the new version to localStorage BEFORE\n  // reloading, so if that reload came back out of a cache the marker said\n  // "current" while the page was stale — and it never checked again.\n  // A phone could sit on a superseded build indefinitely.\n  var V = "__BUILD_ID__";\n  fetch("/version.txt?_=" + Date.now(), { cache: "no-store" })\n    .then(function(r){ return r.text(); })\n    .then(function(v){\n      v = v.trim();\n      localStorage.setItem("jh-build", v);\n      if (!v || v === V) return;\n      // One reload per server version, so a mismatch we cannot fix — a\n      // version.txt that never matches any build — degrades to serving the\n      // stale page rather than reloading forever.\n      try {\n        if (sessionStorage.getItem("jh-reloaded") === v) return;\n        sessionStorage.setItem("jh-reloaded", v);\n      } catch (e) { return; }\n      // Reload through a changed URL: a plain reload can be answered from\n      // the browser\'s cache, and that cache is exactly what is stale.\n      var u = location.pathname + "?b=" + encodeURIComponent(v) + location.hash;\n      location.replace(u);\n    }).catch(function(){});\n})();')



def replace_fn(s, name, new_src, report, label):
    """Swap a whole view function out by brace-matching its body."""
    i = s.find("function %s(" % name)
    if i < 0 or s.count("function %s(" % name) != 1:
        sys.exit("BUILD FAILED: expected exactly one 'function %s('" % name)
    # The first "{" after the name is the destructured PARAMETER list, not the
    # body — brace-matching from there replaces the arguments and leaves the
    # function behind. The body opens at the ") {" that closes those params.
    j = s.index(") {", i) + 2
    depth, k = 0, j
    while True:
        if s[k] == "{":
            depth += 1
        elif s[k] == "}":
            depth -= 1
            if depth == 0:
                break
        k += 1
    old = s[i:k + 1]
    report.append("  screen %s (%.0fKB -> %.0fKB)" % (label, len(old) / 1024, len(new_src) / 1024))
    return s[:i] + new_src + s[k + 1:]


def rebuild_screens(s, report):
    """HOME, SESSIONS and RANK, rebuilt from the Claude Design canvas.

    Whole views rather than a re-skin, because the canvas changes what each
    screen is made of. Everything still renders off the existing engine.
    """
    s = replace_fn(s, "DashboardView", SCREENS.HOME_FN, report, "HOME")
    s = replace_fn(s, "LeaderboardView", SCREENS.RANK_FN, report, "RANK")

    return replace_fn(s, "SessionsView", SCREENS.SESSIONS_FN, report, "SESSIONS")


def rebuild_rank(s, report):
    """Replace LeaderboardView's render with the design language's RANK screen."""
    i = s.find(RANK_ANCHOR)
    if i < 0 or s.count(RANK_ANCHOR) != 1:
        sys.exit("BUILD FAILED: could not locate LeaderboardView's podium block "
                 "(expected exactly one 'const PODIUM_CFG = {')")
    j = s.find(RANK_END, i)
    if j < 0:
        sys.exit("BUILD FAILED: LeaderboardView no longer ends before PlayerDetail")
    old = s[i:j]
    # The three things Vol.6's podium does that the spec removes. If any has
    # already gone, the block is not what this rewrite was written against.
    for marker in ("PODIUM_CFG", "CIc.crown", "rotate(${rot})"):
        if marker not in old:
            sys.exit(f"BUILD FAILED: podium block is missing {marker!r} — "
                     f"has the Vol.6 RANK screen been rewritten?")
    s = s[:i] + RANK_JSX + s[j:]
    report.append(f"  rank   podium -> section-06 top-three rows "
                  f"({len(old)/1024:.0f}KB -> {len(RANK_JSX)/1024:.0f}KB)")
    return s


def apply_skin(s, report):
    """Append the handoff's surge-skin.css as the last <style> block.

    The August skin is itself a stack of append-only override layers; the
    handoff is explicit that Surge is one more layer in that shape and that
    nothing above it should be deleted.

    Two selectors in the file are rewritten on the way in. They target August's
    literal values — button[style*="FF2E43"] and [style*="Anton"] — which the
    JSX sweep above has already replaced, so pasted verbatim they would match
    nothing. Retargeting them at the post-sweep values keeps the rules doing
    the job they were written to do.
    """
    css = open(SKIN).read()
    css = css.replace('button[style*="FF2E43"]', 'button[style*="00E5FF"]')
    css = css.replace('[style*="Anton"]', '[style*="wdth"]')
    # This build renames Vol.6's .aa-* classes (DESIGN.md's "class names lie"
    # complaint), so the skin's lockup selectors have to follow or its rules
    # would silently match nothing.
    css = css.replace('.aa-wordmark', '.surge-lockup-img').replace('.aa-emblem', '.surge-emblem')

    # The waveform's drift was frozen by its own rule. Section 1 pins
    # `background-position:0 0 !important` on body::before and then animates
    # that same property with surgeTrace — and a CSS animation cannot override
    # an !important declaration, so the animation ran while the background sat
    # still. The !important is there to beat August's grid, which sets
    # background-image and background-size but never position, so dropping it
    # on this one declaration costs nothing and lets the trace actually move.
    frozen = "  background-position:0 0 !important;"
    if css.count(frozen) != 1:
        sys.exit(f"BUILD FAILED: expected exactly 1 pinned background-position in the "
                 f"skin's waveform rule, found {css.count(frozen)}")
    css = css.replace(frozen, "  background-position:0 0;")
    report.append("  fix    waveform background-position un-pinned (!important froze surgeTrace)")

    # The spec's two documented exceptions to the blanket cyan swap.
    css += """

/* ── 6 · THE TWO EXCEPTIONS THE HANDOFF CALLS OUT ──────────────────────
   Both are places where the blanket red->cyan sweep produces the wrong
   answer, named explicitly in the handoff's JSX table.
   ────────────────────────────────────────────────────────────────────── */

/* The signup-state pill is the clearest use of the warm accent in the app,
   so it takes Strike Amber rather than following red into cyan. */
.jh-signup-pill,.jh-chipbtn.signup,[data-signup-state]{
  background:var(--surge-amber) !important;
  color:var(--surge-void) !important;
  box-shadow:0 0 24px rgba(255,158,27,.35) !important;
}

/* The pinned YOU row on RANK is already cyan-bordered and would lose its
   distinction against a now-cyan screen, so it goes amber — and it is the
   only amber on that screen. */
.jh-lbrow.is-me,.jh-lbrow.me,[data-me="1"]{
  --tick:var(--surge-amber) !important;
  border-color:rgba(255,158,27,.55) !important;
}


/* ── 7 · UN-HIDE THE WAVEFORM ──────────────────────────────────────────
   The skin paints the surge trace on body::before, but an earlier August
   layer carries `html:not(.light) body::before{ display:none }` — written
   when that pseudo-element held a halftone dot field nobody wanted in
   dark mode. `html` never gets `.light` here, so that rule always matches
   and it out-specifies the skin's bare `body::before`: the trace was being
   painted and then hidden, which also took its animation with it.

   Restated at matching specificity with the geometry the layer above had
   set unimportantly, so the background-image and `surgeTrace` in section 1
   are the ones that survive.
   ────────────────────────────────────────────────────────────────────── */

html body::before{
  content:"" !important;
  display:block !important;
  position:fixed !important;
  inset:0 !important;
  z-index:0 !important;
  pointer-events:none !important;
}
html:not(.light) .court-motif{ display:none !important; }


/* ── 8 · SECTION TITLES ARE TYPE, NOT PLATES ───────────────────────────
   A July Heat layer still styles .jh-sec-title as a filled "burst badge",
   which under the token swap turned RANKINGS into a solid cyan block —
   the loudest object on the screen the skin is supposed to quieten. The
   design language sets it as plain uppercase italic display type at 38px
   with no plate, letting the rising bar be the only card signature.
   ────────────────────────────────────────────────────────────────────── */

.jh-sec-title{
  display:block !important;
  background:none !important;
  border:none !important;
  box-shadow:none !important;
  text-shadow:none !important;
  -webkit-text-stroke:0 !important;
  padding:0 !important;
  margin-bottom:0 !important;
  color:var(--surge-white) !important;
  font-size:38px !important;
  line-height:.88 !important;
  letter-spacing:-.01em !important;
}
.jh-sec-title em{ color:var(--surge-cyan) !important; text-shadow:none !important; }

/* The nav's 5px rule was August's orange and still showed through at the
   left edge. Amber is urgency-only in Vol.7, so the rule is cyan. */
nav.fixed{ border-top-color:var(--surge-cyan) !important; }

/* The nav also carried an amber radial bloom at 10% 8%, which read as an
   orange sliver in its top-left corner. Same rule: amber is urgency-only. */
nav.fixed.bottom-0{ background-image:none !important; }
"""

    # The second-pass UX layer goes after every section above, so it can
    # refine what they set without any of them needing to change.
    css += UX_LAYER

    marker = "</style>"
    i = s.rindex(marker)
    block = ("\n<style>\n/* ══ SEPTEMBER SURGE · VOL.7 SKIN — appended last, per the handoff ══ */\n"
             + css + "\n</style>\n" + UX_SCRIPT)
    s = s[:i + len(marker)] + block + s[i + len(marker):]
    report.append(f"  skin   surge-skin.css appended as last style block ({len(css)/1024:.0f}KB)")
    return s


def main():
    s = open(SRC).read()
    orig_len = len(s)
    report = []

    # Colours, sentinel round-trip so old/new cyans cannot collide.
    for table in (COLOURS, RGBS):
        for old, sent, _ in table:
            for variant in ({old, old.upper(), old.lower()} if old.startswith("#") else {old}):
                s = s.replace(variant, sent)
        for old, sent, new in table:
            n = s.count(sent)
            s = s.replace(sent, new)
            if n:
                report.append(f"  colour {old:<12} -> {new:<12} {n:>5}")

    for rx, new in DISPLAY_RE:
        s, n = rx.subn(new, s)
        if n:
            report.append(f"  display {rx.pattern[:44]:<44} {n:>4}")

    for old, new in DISPLAY:
        n = s.count(old)
        if n:
            s = s.replace(old, new)
            report.append(f"  display {old[:44]:<44} {n:>4}")

    for old, new in MOTION:
        n = s.count(old)
        if n:
            s = s.replace(old, new)
            report.append(f"  motion {old[:34]:<34} -> {new[:26]:<26} {n:>3}")

    # The three copies of the emblem carried inline as base64 are ~950KB of a
    # 1.6MB file (DESIGN.md flags this). Vol.7 points them at the asset instead,
    # which is both correct branding and a large cut to every cold load.
    b64 = re.search(r'const UP_LOGO_FULL = "data:image/png;base64,[A-Za-z0-9+/=]+";', s)
    if not b64:
        sys.exit("BUILD FAILED: could not find the inline UP_LOGO_FULL constant")
    saved = len(b64.group(0))
    s = s.replace(b64.group(0), 'const UP_LOGO_FULL = "assets/up-logo-cyan.png";')
    report.append(f"  inlined emblem -> assets/up-logo-cyan.png  (-{saved/1024:.0f}KB)")

    for old, new in ASSETS:
        n = s.count(old)
        if n:
            s = s.replace(old, new)
            report.append(f"  asset  {old:<26} -> {new:<26} {n:>3}")

    # Class names too. DESIGN.md's standing complaint about this codebase is
    # that "class names lie" — the Vol.6 app is full of .jh-* classes inherited
    # from July Heat. Since this fork is mechanical, rename rather than add
    # another volume's worth of misleading selectors.
    for old, new in [("aa-wordmark", "surge-lockup-img"), ("aa-emblem", "surge-emblem")]:
        n = s.count(old)
        s = s.replace(old, new)
        report.append(f"  class  .{old:<21} -> .{new:<21} {n:>3}")

    for old, new in TEXT:
        n = s.count(old)
        if not n:
            sys.exit(f"BUILD FAILED: expected to rename {old!r} but found none — "
                     f"has the Vol.6 app been reworded?")
        s = s.replace(old, new)
        report.append(f"  text   {old:<22} -> {new:<22} {n:>3}")

    for old, new in ARROWS:
        n = s.count(old)
        if n:
            s = s.replace(old, new)
            report.append(f"  arrows {old} -> {new}{'':<34} {n:>4}")

    for old, new in POST_SWEEP:
        n = s.count(old)
        if n != 1:
            sys.exit(f"BUILD FAILED: post-sweep fix expected 1 match, found {n}")
        s = s.replace(old, new)
        report.append("  fix    all-time CTA amber -> cyan (amber is urgency-only)")

    # Anything left over would ship as Vol.6 branding on a Vol.7 site.
    #
    # Two Vol.6 references are legitimate and deliberate: Vol.7 names Vol.6 as
    # its predecessor, the way Vol.6 named July Heat. Those are pinned to exact
    # counts rather than waved through, so an accidental leftover still fails.
    EXPECTED = {"August Attack": 3, "attack.urbanpadel.om": 1}
    FORBIDDEN = ["AUGUST ATTACK", "aa-wordmark", "aa-emblem", "jh-watermark",
                 "#FF2E43", "#3DE1FF", "Serve first", "Serve First", "Anton",
                 "VOL. 6", "Vol.6", "all August", "heat.urbanpadel.om"]

    bad = {p: s.count(p) for p in FORBIDDEN if s.count(p)}
    if bad:
        sys.exit(f"BUILD FAILED: Vol.6/Vol.5 references survived: {bad}")
    for p, want in EXPECTED.items():
        got = s.count(p)
        if got != want:
            sys.exit(f"BUILD FAILED: expected exactly {want} reference(s) to {p!r} "
                     f"(Vol.7 citing its predecessor), found {got}")
    report.append(f"  kept   {EXPECTED} as predecessor references")

    # Appended after the guard: the handoff's CSS carries its own commentary
    # ("Anton can then be dropped", "Serve first. Strike hard." as the line
    # being replaced), which is documentation of the change, not a leftover.
    for old, new, want in HOME_MEDALS:
        if s.count(old) != want:
            sys.exit(f"BUILD FAILED: expected exactly {want} match(es) for the medal/panel "
                     f"fix, found {s.count(old)}: {old[:60]!r}")
        s = s.replace(old, new)
    report.append("  fix    panel bars amber -> cyan, medal chips -> cyan/steel ladder")

    # Stamp this build's identity into the page and make the update check
    # self-healing. The hash is computed after every other transform, over the
    # file with the stamp itself blanked, so it is stable and depends only on
    # what actually ships.
    vc_old, vc_new = VERSION_CHECK
    if s.count(vc_old) != 1:
        sys.exit(f"BUILD FAILED: expected 1 version-check block, found {s.count(vc_old)}")
    s = s.replace(vc_old, vc_new)

    for old, new, want in QUALIFY:
        if s.count(old) != want:
            sys.exit(f"BUILD FAILED: qualifying-row patch expected {want} match(es), "
                     f"found {s.count(old)}: {old[:70]!r}")
        s = s.replace(old, new)
    report.append("  qual   group tables mark the real qualifiers (per-format, live)")

    s = rebuild_screens(s, report)
    s = apply_skin(s, report)

    build_id = hashlib.sha256(s.encode()).hexdigest()[:12]
    s = s.replace("__BUILD_ID__", build_id)
    open(DST, "w").write(s)
    with open(DST + ".version", "w") as f:
        f.write(build_id + "\n")
    report.append(f"  build  id {build_id} -> stamped in page + {os.path.basename(DST)}.version")
    print("\n".join(report))
    print(f"\nwrote {os.path.basename(DST)}  {orig_len/1024/1024:.2f}MB -> {len(s)/1024/1024:.2f}MB")


if __name__ == "__main__":
    main()
