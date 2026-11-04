# VOL.9'S OWN NIGHT SCREENS.
#
# The night is the screen somebody holds for three hours beside a court, and
# it was the one part of the app nothing here had ever looked at. Shot and
# measured on the shipped build, it had three faults, all of them about the
# same thing — the screen told you the DRAW and never told you the STATE:
#
#   · THE TEAMS SCREEN WAS A LIST OF PAIRS AND NOTHING ELSE. No position, no
#     wins, no points, no mark on who is through. The one screen named after
#     the teams was the one screen that could not tell you how they were
#     doing, and the table lived behind a different chip, one group at a time.
#   · THERE WAS NO LEADERBOARD FOR THE NIGHT. The app knows exactly what every
#     player earned on a given night — `calcPlayerNights` has carried it since
#     Vol.8, with its own guard against disagreeing with the series table —
#     and no screen in the app showed it. The question everybody asks on the
#     way home had no answer in the thing they were all looking at.
#   · NOTHING SAID WHAT WAS HAPPENING NOW. No progress, no court in play, no
#     next fixture. The WALL (`?tv=`) has said ON COURT and NEXT since it was
#     built, because that is the one thing a spectator wants; the phone, which
#     is what everybody actually has, said nothing.
#
# It is a module rather than another pile of MOTIFS anchors for the reason
# `national_cards.py` is: these are NEW COMPOSITIONS, not recolours, and
# patching a layout one anchor at a time is how the cards ended up as a
# black-card design wearing red.
#
# EVERY FIGURE IS READ FROM THE APP'S OWN ENGINE, none is re-derived here:
# `calcGroupStandings` for the tables, `qualifyingTeamIds` for who is through,
# `calcPlayerNights` for what a night paid. A screen that can disagree with
# the scoring is worse than no screen, which is the rule the UPRISING RULES
# tab is built on and the same one applies here.


def screens(pal):
    """The night's own components, as JS to splice in front of SessionsView."""
    ivory = pal['ivory']
    red = pal['bg']
    green = pal['green']
    # --rose-txt. The skin's own muted copy colour: 4.72:1 on the base red,
    # where `rose` itself is 3.64:1 and under AA for a sentence. Same reason
    # the skin keeps rose for dots, rules and fills and never for prose.
    rose_txt = '#F2D0D3'

    return f"""
// ── THE NIGHT'S OWN SCREENS (Vol.9) ──────────────────────────────────────────

// MON 2 NOV, NOT 11/2/2026. The night header built its date with
// `new Date(<plain date>).toLocaleDateString()`, which is ambiguous to every
// reader outside the US and is also the construction this repo has a standing
// rule against: the string parses as UTC midnight and the server runs at
// UTC+4, so the day shown can be the day before the day stored. The parts are
// read out of the string, and the weekday is taken with the UTC getters off a
// UTC-built date, so neither half can drift.
function naNightWhen(d) {{
  const m = /^(\d{{4}})-(\d{{2}})-(\d{{2}})$/.exec(d || "");
  if (!m) return (d || "").toUpperCase();
  const DOW = ["SUN", "MON", "TUE", "WED", "THU", "FRI", "SAT"];
  const dt = new Date(Date.UTC(+m[1], +m[2] - 1, +m[3]));
  return DOW[dt.getUTCDay()] + " " + fmtNightDate(d);
}}

// What is happening RIGHT NOW, read off the fixtures the same way the wall
// reads them: a match with a record and no winner is ON COURT (the scorer has
// opened it), a match with no record at all is NEXT. Nothing here is stored,
// so it cannot drift from the scores.
function naNightPulse(session) {{
  const groups = getSessionGroups(session);
  const teams = session.teams || [];
  const nameOfTeam = (id) => {{
    const t = teams.find(x => x.id === id);
    return t || null;
  }};
  const ms = session.groupMatches || [];
  const played = ms.filter(m => m.winner).length;
  // The fixture list is what the draw owes, not what has been entered: a
  // night with nothing scored must still report how many matches it is.
  const total = ms.length;
  const live = ms.filter(m => !m.winner && m.score
    && (m.score.t1 !== null || m.score.t2 !== null));
  const next = ms.filter(m => !m.winner && !(m.score
    && (m.score.t1 !== null || m.score.t2 !== null)));
  const bracket = session.bracket || {{}};
  const koAll = (bracket.qf || []).concat(bracket.sf || [],
                                          bracket.final ? [bracket.final] : []);
  const koPlayed = koAll.filter(m => m && m.winner).length;
  const koDrawn = koAll.length > 0;
  const groupsDone = total > 0 && played === total;
  return {{ groups, played, total, live, next, koAll, koPlayed, koDrawn,
           groupsDone, teams }};
}}

// THE STRIP AT THE TOP OF THE NIGHT. One line of state and then whatever is
// on court, which is the only thing on this screen that changes while you are
// looking at it.
function NaNightPulse({{ session, state }}) {{
  const p = naNightPulse(session);
  const first = (id) => {{
    const pl = (state.players || []).find(x => x.id === id);
    return pl ? pl.name.split(" ")[0] : "?";
  }};
  const lbl = (tid) => {{
    const t = (session.teams || []).find(x => x.id === tid);
    return t ? first(t.p1Id) + " & " + first(t.p2Id) : "?";
  }};
  if (!p.total && !p.koDrawn) return null;
  const pct = p.total ? Math.round((p.played / p.total) * 100) : 0;
  const stage = p.groupsDone
    ? (p.koDrawn
        ? (p.koPlayed === p.koAll.length ? "FINISHED" : "KNOCKOUT")
        : "GROUPS DONE")
    : "GROUP STAGE";

  // THE FIXTURE GETS THE FULL WIDTH, ON ITS OWN LINE. On one row with the
  // badge and the score it had about 200px of a 390px phone, and
  // "Muntaser & Mohammed v Hisham & Jalal" came out as
  // "Muntaser & Mohammed v ..." — the half of the fixture that is cut is the
  // opponent, which is the half somebody standing by the court is reading it
  // for. Badge and score on top, the two teams underneath.
  const Row = ({{ m, kind }}) => (
    <div style={{{{ padding: "10px 0 9px",
      borderTop: "1px solid rgba(242,208,211,.16)" }}}}>
      <div style={{{{ display: "flex", alignItems: "center", gap: 10 }}}}>
        <span style={{{{ fontFamily: "'JetBrains Mono',monospace", fontWeight: 700,
          fontSize: 9, letterSpacing: ".18em", padding: "3px 8px", borderRadius: 999,
          whiteSpace: "nowrap", flex: "0 0 auto",
          background: kind === "live" ? "{ivory}" : "rgba(247,241,230,.14)",
          color: kind === "live" ? "{red}" : "{rose_txt}" }}}}>
          {{kind === "live" ? "ON COURT" : "NEXT"}}
        </span>
        <span style={{{{ flex: 1 }}}} />
        {{kind === "live" && m.score && (
          <span style={{{{ fontFamily: "'JetBrains Mono',monospace", fontWeight: 700,
            fontSize: 15, color: "{ivory}", flex: "0 0 auto" }}}}>
            {{m.score.t1 === null ? "-" : m.score.t1}}&#8201;/&#8201;{{m.score.t2 === null ? "-" : m.score.t2}}
          </span>
        )}}
      </div>
      <div style={{{{ marginTop: 5, fontSize: 13.5, lineHeight: 1.35, color: "{ivory}" }}}}>
        {{lbl(m.team1Id)}} <span style={{{{ color: "{rose_txt}" }}}}>v</span> {{lbl(m.team2Id)}}
      </div>
    </div>
  );

  return (
    <div className="na-pulse" style={{{{ padding: "14px 16px 12px", marginBottom: 12 }}}}>
      <div style={{{{ display: "flex", alignItems: "baseline", justifyContent: "space-between",
        gap: 14, flexWrap: "wrap" }}}}>
        <span style={{{{ fontFamily: "'JetBrains Mono',monospace", fontWeight: 700,
          fontSize: 10, letterSpacing: ".24em", color: "{ivory}" }}}}>{{stage}}</span>
        <span style={{{{ fontFamily: "'JetBrains Mono',monospace", fontWeight: 700,
          fontSize: 11, color: "{rose_txt}" }}}}>
          {{p.played}}&#8201;/&#8201;{{p.total}} MATCHES
          {{p.koDrawn ? "  \\u00B7  KO " + p.koPlayed + "/" + p.koAll.length : ""}}
        </span>
      </div>
      {{/* THE BAR IS A BAR, NOT A PILL. A 999px radius on a 6px rule is the
           same fault as a radius on a hairline, and the track would read as
           a lozenge rather than as a measure. */}}
      <div style={{{{ height: 6, marginTop: 10, background: "rgba(247,241,230,.16)",
        borderRadius: 3, overflow: "hidden" }}}}>
        <div style={{{{ height: "100%", width: pct + "%", borderRadius: 3,
          background: p.groupsDone ? "{green}" : "{ivory}" }}}} />
      </div>
      <div style={{{{ marginTop: 6 }}}}>
        {{p.live.slice(0, 3).map(m => <Row key={{m.id}} m={{m}} kind="live" />)}}
        {{p.live.length === 0 && p.next.slice(0, 2).map(m => <Row key={{m.id}} m={{m}} kind="next" />)}}
        {{p.live.length === 0 && p.next.length === 0 && p.groupsDone && !p.koDrawn && (
          <div style={{{{ paddingTop: 10, borderTop: "1px solid rgba(242,208,211,.16)",
            fontSize: 13, color: "{rose_txt}" }}}}>
            Every group match is in. The knockout has not been drawn yet.
          </div>
        )}}
      </div>
    </div>
  );
}}

// ── THE NIGHT LEADERBOARD ────────────────────────────────────────────────────
// What every player took home from THIS night, which is the question asked in
// the car park and which no screen in the app could answer.
//
// IT IS THE APP'S OWN RECEIPT, not a second scorer. `calcPlayerNights` walks
// the same path `calcPlayerStats` walks and checks its own total against it;
// this reads the one night out of that and sorts on it, so a row here cannot
// claim a figure the player's own card contradicts.
//
// AND IT SAYS WHAT IT IS COUNTING. The streak bonus is a fact about a RUN of
// nights, not about this one, so it is not in `nightTotal` and is not implied
// here — the same discipline as never multiplying out what a 2X night is
// worth. The line under the heading says so in words.
function NaNightPoints({{ session, state, sessions, onPick }}) {{
  const idx = sessions.findIndex(s => s.id === session.id);
  const nameOf = (s, _t, pid) => {{
    const p = (state.players || []).find(x => x.id === pid);
    return p ? p.name : "?";
  }};
  const rows = React.useMemo(() => {{
    if (idx < 0) return [];
    const upto = sessions.slice(0, idx + 1);
    const out = [];
    (session.teams || []).forEach(t => {{
      [t.p1Id, t.p2Id].forEach(pid => {{
        const pl = (state.players || []).find(x => x.id === pid);
        if (!pl) return;
        const r = calcPlayerNights(pid, upto, nameOf);
        const n = r.nights.find(x => x.id === session.id);
        if (!n) return;
        out.push({{ player: pl, team: t, n, ok: r.ok }});
      }});
    }});
    return out.sort((a, b) => (b.n.nightTotal - a.n.nightTotal)
      || a.player.name.localeCompare(b.player.name));
  }}, [session, sessions, state.players, idx]);

  if (!rows.length) return (
    <div className="sg-card" style={{{{ padding: 20, textAlign: "center",
      fontSize: 13, color: "{rose_txt}" }}}}>
      Nobody has scored on this night yet. The table fills in as results are locked.
    </div>
  );

  // A DEAD HEAT IS A DEAD HEAT. Equal points share a position, and the next
  // one skips — ranking two identical rows 1 and 2 invents a winner the
  // scoring never named.
  let lastPts = null, lastPos = 0;
  const disagree = rows.some(r => !r.ok);

  return (
    <div className="space-y-3">
      <div className="sg-card" style={{{{ padding: "14px 16px" }}}}>
        <div style={{{{ fontFamily: "'Archivo',sans-serif", fontStyle: "italic",
          fontVariationSettings: "'wdth' 125,'wght' 900", fontSize: 26,
          color: "{ivory}", lineHeight: 1.05 }}}}>TONIGHT&#8217;S POINTS</div>
        <div style={{{{ marginTop: 6, fontSize: 12, color: "{rose_txt}", lineHeight: 1.45 }}}}>
          What each player earned on this night. The attendance streak bonus is
          counted across the season, not on one night, so it is not in here.
        </div>
      </div>
      {{disagree && (
        <div style={{{{ padding: "10px 14px", background: "{ivory}", color: "{red}",
          fontSize: 12, fontWeight: 700 }}}}>
          A receipt disagrees with the series table. Do not trust this screen
          until it is looked at.
        </div>
      )}}
      <div className="sg-card" style={{{{ padding: "6px 14px 10px" }}}}>
        <div style={{{{ display: "flex", alignItems: "center", gap: 10,
          padding: "10px 0 8px", fontFamily: "'JetBrains Mono',monospace",
          fontWeight: 700, fontSize: 9, letterSpacing: ".2em", color: "{rose_txt}" }}}}>
          <span style={{{{ flex: "0 0 26px" }}}}>#</span>
          <span style={{{{ flex: 1 }}}}>PLAYER</span>
          <span style={{{{ flex: "0 0 52px", textAlign: "right" }}}}>PTS</span>
        </div>
        {{rows.map((r, i) => {{
          const pos = r.n.nightTotal === lastPts ? lastPos : i + 1;
          lastPts = r.n.nightTotal; lastPos = pos;
          const champ = r.n.outcome === "Session champion";
          return (
            <button key={{r.player.id}} onClick={{() => onPick && onPick(r.player)}}
              style={{{{ width: "100%", display: "flex", alignItems: "center", gap: 10,
                minHeight: 44, padding: "9px 0", textAlign: "left", cursor: "pointer",
                background: "transparent", border: 0,
                borderTop: "1px solid rgba(242,208,211,.16)", color: "inherit" }}}}>
              <span style={{{{ flex: "0 0 26px", fontFamily: "'JetBrains Mono',monospace",
                fontWeight: 700, fontSize: 13,
                color: pos <= 3 ? "{ivory}" : "{rose_txt}" }}}}>{{pos}}</span>
              <Avatar player={{r.player}} size={{30}} />
              <span style={{{{ flex: 1, minWidth: 0 }}}}>
                <span style={{{{ display: "block", fontSize: 14, color: "{ivory}",
                  overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}}}>
                  {{r.player.name}}
                </span>
                <span style={{{{ display: "block", marginTop: 2, fontSize: 11,
                  color: champ ? "{ivory}" : "{rose_txt}",
                  overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}}}>
                  {{r.n.outcome}}{{r.n.x2 ? " \\u00B7 2X" : ""}}
                </span>
              </span>
              <span style={{{{ flex: "0 0 52px", textAlign: "right",
                fontFamily: "'Archivo',sans-serif", fontStyle: "italic",
                fontVariationSettings: "'wdth' 125,'wght' 900", fontSize: 22,
                color: "{ivory}" }}}}>{{r.n.nightTotal}}</span>
            </button>
          );
        }})}}
      </div>
    </div>
  );
}}
"""


def group_table_block(pal):
    """The TEAMS screen's group block, rewritten to carry the standings.

    The old one listed the four pairs and stopped. This is the same card with
    the table in it: finishing order, played, wins, game difference, points,
    and a mark on whoever is through — read from `calcGroupStandings` and
    `qualifyingTeamIds`, which are what the bracket itself seeds from, so the
    screen cannot promise a place the knockout will not honour.
    """
    ivory = pal['ivory']
    green = pal['green']
    red = pal['bg']
    rose_txt = '#F2D0D3'
    return (
        '{byGroup[g].length === 0 ? <div className="text-xs text-stone-600 italic px-2 py-3 '
        'text-center border border-dashed border-stone-800 rounded-lg">Empty</div>\n'
        '            : (() => {\n'
        '              // THE TABLE, NOT THE DRAW. Ordered by the app\'s own group\n'
        '              // standings, so this screen and the GROUPS screen and the\n'
        '              // bracket cannot tell three different stories.\n'
        '              const rowsG = calcGroupStandings(session, g);\n'
        '              const through = qualifyingTeamIds(session);\n'
        '              const anyPlayed = rowsG.some(r => r.played > 0);\n'
        '              const ordered = anyPlayed\n'
        '                ? rowsG\n'
        '                : byGroup[g].map(t => ({ team: t, pts: 0, wins: 0, played: 0,\n'
        '                                         gf: 0, ga: 0, gd: 0 }));\n'
        '              return <div>\n'
        '                {anyPlayed && <div style={{ display:"flex", alignItems:"center", gap:6,\n'
        '                  padding:"0 2px 6px", fontFamily:"\'JetBrains Mono\',monospace",\n'
        f'                  fontWeight:700, fontSize:9, letterSpacing:".2em", color:"{rose_txt}" }}}}>\n'
        '                  <span style={{ flex:"0 0 15px" }} />\n'
        '                  <span style={{ flex:1 }}>TEAM</span>\n'
        '                  <span style={{ flex:"0 0 18px", textAlign:"right" }}>W</span>\n'
        '                  <span style={{ flex:"0 0 28px", textAlign:"right" }}>GD</span>\n'
        '                  <span style={{ flex:"0 0 26px", textAlign:"right" }}>PTS</span>\n'
        '                </div>}\n'
        '                <div className="space-y-1">{ordered.map((r, ri) => {\n'
        '                const t = r.team;\n'
        '                const p1 = state.players.find(p => p.id === t.p1Id);\n'
        '                const p2 = state.players.find(p => p.id === t.p2Id);\n'
        '                const seed = getSeedNum(t.id);\n'
        '                // Nothing is marked as qualifying before a ball is hit. With\n'
        '                // every team level on nothing, a green edge is not a\n'
        '                // prediction, it is the draw order wearing the flag. Same\n'
        '                // rule the wall already works under.\n'
        '                // `qualifyingTeamIds` returns a SET, not an array. Caught by\n'
        '                // rendering the screen; `.includes` on it throws and takes the\n'
        '                // whole night view down, which is the entire session screen.\n'
        '                const qual = anyPlayed && through.has(t.id);\n'
        '                return <button key={t.id} onClick={() => isAdmin && setEdit(t)}\n'
        '                  className="w-full flex items-center p-2 text-left"\n'
        '                  style={{ minHeight:44, background:"rgba(247,241,230,.05)",\n'
        '                           gap:6, paddingLeft:6 }}>\n'
        '                  {/* A BAR, NOT A BORDER. A `border-left` on a row that\n'
        '                      carries the sheet radius is bent by it — the mark came\n'
        '                      out as a green crescent down the side of the pill, which\n'
        '                      is the same fault as a radius on a hairline, one layer in.\n'
        '                      The row has a background of its own, so the skin\u2019s rule for\n'
        '                      that cannot reach it: a surface with one drawn edge is a\n'
        '                      card, and this needed to stop being an edge. */}\n'
        '                  <span aria-hidden="true" style={{ flex:"0 0 4px", height:22,\n'
        f'                    background: qual ? "{green}" : "transparent" }}}} />\n'
        '                  {anyPlayed\n'
        '                    ? <span style={{ flex:"0 0 15px", fontFamily:"\'JetBrains Mono\',monospace",\n'
        f'                        fontWeight:700, fontSize:12, color: qual ? "{ivory}" : "{rose_txt}" }}}}>{{ri + 1}}</span>\n'
        '                    : (seed\n'
        '                      ? <span className="text-[9px] font-bold px-1.5 py-0.5 font-mono shrink-0 text-center"\n'
        f'                          style={{{{ background: seed <= 4 ? "{ivory}" : "rgba(255,255,255,.08)",\n'
        f'                            color: seed <= 4 ? "{red}" : "{rose_txt}",\n'
        '                            border:"1px solid rgba(255,255,255,.14)", borderRadius:28, minWidth:28 }}>S{seed}</span>\n'
        '                      : <span className="shrink-0" style={{ width:18 }} aria-hidden="true" />)}\n'
        '                  <span className="flex items-center shrink-0" style={{ marginRight:2 }}>\n'
        '                    {p1 && <Avatar player={p1} size={22} />}\n'
        '                    {p2 && <span style={{ marginLeft:-7 }}><Avatar player={p2} size={22} /></span>}\n'
        '                  </span>\n'
        '                  <div className="flex-1 min-w-0">\n'
        '                    {/* THE PAIR IS STACKED, and it is not a style choice. A\n'
        '                        doubles name beside W, GD and PTS gets 112px at 360 and\n'
        '                        142 at 390; measured on the real roster,\n'
        '                        "Muntaser & Mohammed" wants 190, and four of the sixteen\n'
        '                        pairs overflow even at 390. There is no column width that\n'
        '                        closes a 78px gap — shaving the numbers only moves which\n'
        '                        names get cut. One per line fits every pair at every size,\n'
        '                        and the two overlapping faces beside them already say it\n'
        '                        is a pair, so the ampersand is not carrying anything. */}\n'
        '                    {anyPlayed ? <>\n'
        '                      <div className="truncate" style={{ fontSize:13, lineHeight:1.25,\n'
        f'                        color:"{ivory}" }}}}>{{(p1?.name || "?").split(" ")[0]}}</div>\n'
        '                      <div className="truncate" style={{ fontSize:13, lineHeight:1.25,\n'
        f'                        color:"{ivory}" }}}}>{{(p2?.name || "?").split(" ")[0]}}</div>\n'
        '                    </> : <div className="text-sm text-stone-100 truncate">\n'
        '                      {(p1?.name || "?") + " & " + (p2?.name || "?")}</div>}\n'
        '                  </div>\n'
        '                  {anyPlayed && <>\n'
        '                    <span style={{ flex:"0 0 18px", textAlign:"right",\n'
        f'                      fontFamily:"\'JetBrains Mono\',monospace", fontSize:12, color:"{ivory}" }}}}>{{r.wins}}</span>\n'
        '                    <span style={{ flex:"0 0 28px", textAlign:"right",\n'
        f'                      fontFamily:"\'JetBrains Mono\',monospace", fontSize:12, color:"{rose_txt}" }}}}>'
        '{r.gd > 0 ? "+" + r.gd : r.gd}</span>\n'
        '                    <span style={{ flex:"0 0 26px", textAlign:"right",\n'
        '                      fontFamily:"\'Archivo\',sans-serif", fontStyle:"italic",\n'
        f'                      fontVariationSettings:"\'wdth\' 125,\'wght\' 900", fontSize:18, color:"{ivory}" }}}}>'
        '{r.pts}</span>\n'
        '                  </>}\n'
        '                  {isAdmin && !anyPlayed && <I.edit size={12} className="text-stone-500" />}\n'
        '                </button>;\n'
        '              })}</div>\n'
        '              {anyPlayed && <div style={{ display:"flex", alignItems:"center", gap:7,\n'
        '                padding:"9px 2px 2px", fontFamily:"\'JetBrains Mono\',monospace",\n'
        f'                fontWeight:700, fontSize:9, letterSpacing:".18em", color:"{rose_txt}" }}}}>\n'
        f'                <span style={{{{ width:14, height:4, background:"{green}" }}}} />\n'
        '                THROUGH TO THE KNOCKOUT\n'
        '              </div>}\n'
        '            </div>;\n'
        '            })()}'
    )


# THE ANCHOR, VERBATIM FROM THE SOURCE Vol.8 CARRIES. MOTIFS runs after the
# wording sweep and BEFORE the colour sweep, so the literal here is the one
# with Vol.8's palette still in it (`#C6FF00`, `#9A9A9A`) and a raw `&` rather
# than the entity — transcribing it from the BUILT page is how this anchor
# fails to match, which is the single commonest way a splice here goes wrong.
TEAM_ROWS_OLD = '{byGroup[g].length === 0 ? <div className="text-xs text-stone-600 italic px-2 py-3 text-center border border-dashed border-stone-800 rounded-lg">Empty</div>\n            : <div className="space-y-1">{byGroup[g].map(t => {\n              const p1 = state.players.find(p => p.id === t.p1Id);\n              const p2 = state.players.find(p => p.id === t.p2Id);\n              const seed = getSeedNum(t.id);\n              return <button key={t.id} onClick={() => isAdmin && setEdit(t)} className="w-full flex items-center gap-2 p-2 rounded-lg bg-stone-900/50 hover:bg-stone-800/70 text-left">\n                {seed ? <span className="text-[9px] font-bold px-1.5 py-0.5 rounded font-mono shrink-0 text-center" style={{ background: seed <= 4 ? "#C6FF00" : "rgba(242,242,242,.08)", color: seed <= 4 ? "#F2F2F2" : "#9A9A9A", border: "1px solid rgba(242,242,242,.14)", borderRadius: 0, minWidth: 28 }}>S{seed}</span> : <span className="shrink-0" style={{ width: 28 }} aria-hidden="true" />}\n                <span className="flex items-center shrink-0" style={{ marginRight: 2 }}>\n                  {p1 && <Avatar player={p1} size={26} />}\n                  {p2 && <span style={{ marginLeft: -6 }}><Avatar player={p2} size={26} /></span>}\n                </span>\n                <div className="flex-1 min-w-0"><div className="text-sm text-stone-100 truncate">{p1?.name || "?"} & {p2?.name || "?"}</div></div>\n                {isAdmin && <I.edit size={12} className="text-stone-500" />}\n              </button>;\n            })}</div>}'
