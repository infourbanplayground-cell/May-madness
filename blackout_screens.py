# -*- coding: utf-8 -*-
"""JS/JSX payloads spliced into the Blackout (Vol.8) app by build-blackout-app.py.

Kept out of the builder so the builder stays a list of substitutions and this
stays readable code. Same arrangement surge_screens.py has for Vol.7.

Nothing here re-scores anything. The engine block walks the exact path
calcPlayerStats walks and records each award as it happens, then checks its own
total against calcPlayerStats — so a receipt can never disagree with the
leaderboard everyone is looking at.
"""

# ══════════════════════════════════════════════════════════════════════════
# 1 · ENGINE — per-event detail, cumulative rank, badges
#     Inserted directly after calcPlayerStats so it can call it.
# ══════════════════════════════════════════════════════════════════════════
ENGINE = r"""

// ══ VOL.8 · PER-EVENT SCORING DETAIL ══════════════════════════════════════
//
// Players kept asking "how many points did I get and why", and the honest
// answer used to be a single number. This block turns the same arithmetic
// calcPlayerStats does into a list of receipt lines.
//
// It deliberately does NOT re-implement scoring. It walks the same path, in the
// same order, and records each award as it is made. calcPlayerNights then checks
// its own total against calcPlayerStats and reports `ok:false` if they ever
// disagree, which the UI surfaces rather than hides — a receipt that quietly
// drifts from the leaderboard is worse than no receipt.

// Same ordering and bye logic as teamGroupResults, but keeping the match so each
// counted result can say who it was against. teamGroupResults throws the match
// away, which is fine for a total and useless for a receipt.
function countedGroupResults(session, teamId) {
  const out = [];
  (session.groupMatches || []).forEach(m => {
    if (m.team1Id !== teamId && m.team2Id !== teamId) return;
    if (!m.winner) return;
    const isT1 = m.team1Id === teamId;
    const won = teamWon(m, teamId);
    const lt = m.lossType || "tiebreak";
    out.push({
      m, won, lt,
      pts: won ? 3 : (lt === "tiebreak" ? 2 : lt === "competitive" ? 1 : 0),
      gf: m.score ? (isT1 ? m.score.t1 : m.score.t2) : 0,
      ga: m.score ? (isT1 ? m.score.t2 : m.score.t1) : 0,
    });
  });
  out.sort((a, b) => b.pts - a.pts || (b.gf - b.ga) - (a.gf - a.ga) || b.gf - a.gf);
  const gTeam = (session.teams || []).find(t => t.id === teamId);
  const gSize = gTeam ? (session.teams || []).filter(t => t.group === gTeam.group).length : 0;
  const ghosts = out.length > 0 ? Math.max(0, GROUP_COUNTED_GAMES - Math.max(0, gSize - 1)) : 0;
  const withByes = out.concat(Array.from({ length: ghosts },
    () => ({ bye: true, won: true, pts: 3, gf: 6, ga: 0 })));
  return {
    counted: withByes.slice(0, GROUP_COUNTED_GAMES),
    dropped: withByes.slice(GROUP_COUNTED_GAMES),
  };
}

function lossWord(lt) {
  return lt === "tiebreak" ? "tiebreak loss" : lt === "competitive" ? "close loss" : "blowout";
}
function scoreOf(m, teamId) {
  if (!m || !m.score) return "";
  const isT1 = m.team1Id === teamId;
  return (isT1 ? m.score.t1 : m.score.t2) + "–" + (isT1 ? m.score.t2 : m.score.t1);
}
function koLine(m, teamId) {
  if (!m) return "";
  const won = teamWon(m, teamId);
  const sc = scoreOf(m, teamId);
  if (won) return sc ? "Won " + sc : "Won";
  return (sc ? "Lost " + sc : "Lost") + " · " + lossWord(m.lossType || "tiebreak") + " · knocked out";
}

// One receipt per night a player was on a team, plus the season-level lines.
// `nameOf(session, teamId)` renders "Khalid & Rashid"; the caller owns it
// because only the component has the player list.
function calcPlayerNights(pid, sessions, nameOf) {
  const nights = [];
  const seg = { groupWins: 0, lossPts: 0, topOfGroup: 0, knockout: 0,
                titles: 0, comeback: 0, streak: 0, double: 0 };
  const attended = [];
  let total = 0;

  sessions.forEach((s, idx) => {
    const team = getPlayerTeam(s, pid);
    if (!team) return;
    const mult = s.doublePoints ? 2 : 1;
    const ev = [];
    let base = 0, flat = 0;

    const played = (s.groupMatches || [])
      .filter(m => (m.team1Id === team.id || m.team2Id === team.id) && m.winner).length;
    const { counted, dropped } = countedGroupResults(s, team.id);

    counted.forEach(r => {
      base += r.pts;
      if (r.bye) {
        ev.push({ kind: "GROUP", label: "Bye", pts: r.pts,
                  detail: "group too small for three games" });
        seg.groupWins += r.pts;
        return;
      }
      const opp = r.m.team1Id === team.id ? r.m.team2Id : r.m.team1Id;
      const sc = scoreOf(r.m, team.id);
      ev.push({
        kind: "GROUP", pts: r.pts,
        label: "vs " + nameOf(s, opp),
        detail: r.won ? (sc ? "Won " + sc : "Won")
                      : (sc ? "Lost " + sc : "Lost") + " · " + lossWord(r.lt),
      });
      if (r.won) seg.groupWins += r.pts; else seg.lossPts += r.pts;
    });

    // The best-three rule is the single most common "why don't I have more
    // points" question, so a dropped result is shown rather than omitted.
    dropped.forEach(r => {
      if (r.bye) return;
      const opp = r.m.team1Id === team.id ? r.m.team2Id : r.m.team1Id;
      ev.push({ kind: "DROPPED", pts: 0, label: "vs " + nameOf(s, opp),
                detail: "best three group results count — this one dropped" });
    });

    if (played > 0 && getTopOfGroup(s, team.group) === team.id) {
      base += 1; seg.topOfGroup += 1;
      ev.push({ kind: "GROUP", pts: 1, label: "Top of Group " + team.group, detail: "" });
    }

    // Comeback is a flat +2 in calcPlayerStats — it is NOT doubled on a 2X
    // night. Folding it into `base` would silently pay 4 on those nights.
    if (played > 0) {
      const prev = attended.length ? attended[attended.length - 1] : null;
      if (prev !== null && (idx - prev) >= 3) {
        flat += 2; seg.comeback += 2;
        ev.push({ kind: "BONUS", pts: 2, label: "Comeback",
                  detail: "back after " + (idx - prev - 1) + " nights out" });
      }
      attended.push(idx);
    }

    const qfM = (s.bracket?.qf || []).find(m => (m.team1Id === team.id || m.team2Id === team.id) && m.winner);
    if (qfM) {
      const p = 1 + koMatchPts(qfM, team.id);
      base += p; seg.knockout += p;
      ev.push({ kind: "KNOCKOUT", pts: p, label: "Quarter-final", detail: koLine(qfM, team.id) });
    }
    const sfM = (s.bracket?.sf || []).find(m => (m.team1Id === team.id || m.team2Id === team.id) && m.winner);
    if (sfM) {
      const p = 2 + koMatchPts(sfM, team.id);
      base += p; seg.knockout += p;
      ev.push({ kind: "KNOCKOUT", pts: p, label: "Semi-final", detail: koLine(sfM, team.id) });
    }
    const f = s.bracket?.final;
    const inFinal = f && (f.team1Id === team.id || f.team2Id === team.id) && f.winner;
    if (inFinal) {
      const p = 3 + koMatchPts(f, team.id);
      base += p; seg.knockout += p;
      ev.push({ kind: "KNOCKOUT", pts: p, label: "Final", detail: koLine(f, team.id) });
      if (teamWon(f, team.id)) {
        base += 5; seg.titles += 5;
        const mate = team.p1Id === pid ? team.p2Id : team.p1Id;
        ev.push({ kind: "TITLE", pts: 5, label: "Session champion",
                  detail: "With " + nameOf(s, null, mate) });
      }
    }

    const doubled = base * (mult - 1);
    seg.double += doubled;
    const nightTotal = base * mult + flat;
    total += nightTotal;

    nights.push({
      idx, id: s.id, date: s.date, name: s.name, no: idx + 1,
      x2: mult === 2, events: ev, subtotal: base, flat, mult,
      nightTotal, played,
      outcome: inFinal && teamWon(f, team.id) ? "Session champion"
             : inFinal ? "Reached the final"
             : sfM ? "Reached the semi-final"
             : qfM ? "Made the knockout"
             : "Group stage",
    });
  });

  const streak = calcStreak(attended);
  seg.streak = streak;
  total += streak;

  // The guard rail. If this ever fails the UI says so instead of showing a
  // receipt that disagrees with the table.
  const ref = calcPlayerStats(pid, sessions).totalPts;
  return { nights, seg, total, attended, ok: total === ref, ref };
}

// Where each player stood after every night, so "climbed N places" is a fact
// rather than an impression. O(sessions x players), which at nine nights and a
// roster this size is nothing.
function rankByNight(players, sessions) {
  const out = [];
  for (let i = 0; i < sessions.length; i++) {
    const upto = sessions.slice(0, i + 1);
    const table = players
      .map(p => ({ id: p.id, pts: calcPlayerStats(p.id, upto).totalPts }))
      .sort((a, b) => b.pts - a.pts);
    const pos = {};
    table.forEach((r, j) => { pos[r.id] = j + 1; });
    out.push(pos);
  }
  return out;
}

const BADGES = [
  { code: "IM", name: "Iron man",   desc: "Played every finished night" },
  { code: "3T", name: "Hat-trick",  desc: "Three session titles" },
  { code: "GK", name: "Giant killer", desc: "Beat the team holding the #1 spot" },
  { code: "CB", name: "Comeback",   desc: "Won a match after trailing 2–5" },
  { code: "+5", name: "Climber",    desc: "Moved up 5+ places in one night" },
  { code: "D1", name: "Debut win",  desc: "Won a match on your first night" },
  { code: "W3", name: "On a run",   desc: "Three match wins in a row" },
];

function calcBadges(pid, sessions, players, nightsData, ranks) {
  const done = sessions.filter(s => s.completed).length || sessions.length;
  const played = nightsData.nights.length;
  const titles = nightsData.nights.filter(n => n.outcome === "Session champion").length;

  // Every decided match this player's team was in, in order.
  const results = [];
  sessions.forEach((s, idx) => {
    const team = getPlayerTeam(s, pid); if (!team) return;
    const all = (s.groupMatches || []).concat(s.bracket?.qf || [], s.bracket?.sf || [],
                                              s.bracket?.final ? [s.bracket.final] : []);
    all.forEach(m => {
      if (!m || !m.winner) return;
      if (m.team1Id !== team.id && m.team2Id !== team.id) return;
      results.push({ idx, won: teamWon(m, team.id), m, team });
    });
  });

  let best = 0, run = 0;
  results.forEach(r => { run = r.won ? run + 1 : 0; best = Math.max(best, run); });

  const firstIdx = nightsData.nights.length ? nightsData.nights[0].idx : null;
  const debutWin = firstIdx !== null && results.some(r => r.idx === firstIdx && r.won);

  // Giant killer: beat a team containing whoever led the table going INTO that
  // night, which is the only reading that is fair at the time it happened.
  let giant = false;
  results.forEach(r => {
    if (!r.won || r.idx === 0) return;
    const prev = ranks[r.idx - 1] || {};
    const leader = Object.keys(prev).find(id => prev[id] === 1);
    if (!leader) return;
    const s = sessions[r.idx];
    const oppId = r.m.team1Id === r.team.id ? r.m.team2Id : r.m.team1Id;
    const opp = (s.teams || []).find(t => t.id === oppId);
    if (opp && (opp.p1Id === leader || opp.p2Id === leader)) giant = true;
  });

  let climb = 0;
  nightsData.nights.forEach(n => {
    if (n.idx === 0) return;
    const before = (ranks[n.idx - 1] || {})[pid];
    const after = (ranks[n.idx] || {})[pid];
    if (before && after) climb = Math.max(climb, before - after);
  });

  return BADGES.map(b => {
    switch (b.code) {
      case "IM": return { ...b, got: played >= done && done > 0, prog: played + "/" + done };
      case "3T": return { ...b, got: titles >= 3, prog: titles + "/3" };
      case "GK": return { ...b, got: giant };
      // The handoff flags this one as needing data the app does not record: a
      // comeback flag on result entry, or a game-by-game score. Only the final
      // score is stored, so it is shown locked with the reason rather than
      // quietly redefined into something else.
      case "CB": return { ...b, got: false, locked: "needs game-by-game scoring" };
      case "+5": return { ...b, got: climb >= 5, prog: climb > 0 ? "best +" + climb : null };
      case "D1": return { ...b, got: debutWin };
      case "W3": return { ...b, got: best >= 3, prog: Math.min(best, 3) + "/3" };
      default:   return { ...b, got: false };
    }
  });
}
"""


# ══════════════════════════════════════════════════════════════════════════
# 2 · ME SCREEN + RECEIPT SHEET + ROSTER
#     Inserted just before the main App component.
# ══════════════════════════════════════════════════════════════════════════
VIEWS = r"""

// ══ VOL.8 · ME ════════════════════════════════════════════════════════════
// The answer to "how did I get my points", which was the single most repeated
// question of Vol.7 and had no answer in the app at all.

const SEG_STYLE = [
  ["groupWins",  "Group wins",   "#C6FF00"],
  ["lossPts",    "Loss points",  "rgba(198,255,0,.4)"],
  ["topOfGroup", "Top of group", "rgba(198,255,0,.7)"],
  ["knockout",   "Knockout",     "#FF2E88"],
  ["titles",     "Titles",       "#F2F2F2"],
  ["comeback",   "Comeback",     "#8A8A8A"],
  ["streak",     "Streak",       "#6E6E6E"],
  ["double",     "2X bonus",     "#4A4A4A"],
];

function StackedBar({ seg, total }) {
  const parts = SEG_STYLE.filter(([k]) => seg[k] > 0);
  if (!total) return null;
  return (
    <div style={{ display: "flex", gap: 2, height: 16, marginTop: 14 }}>
      {parts.map(([k, , c]) => (
        <div key={k} title={k} style={{ flexGrow: seg[k], background: c, minWidth: 3 }} />
      ))}
    </div>
  );
}

function SegLegend({ seg }) {
  const parts = SEG_STYLE.filter(([k]) => seg[k] > 0);
  return (
    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "7px 16px", marginTop: 14 }}>
      {parts.map(([k, label, c]) => (
        <div key={k} style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <span style={{ width: 10, height: 10, background: c, flexShrink: 0 }} />
          <span style={{ fontSize: 12, color: "#9A9A9A", flex: 1 }}>{label}</span>
          <span style={{ fontFamily: "'JetBrains Mono',monospace", fontWeight: 700,
                         fontSize: 13, color: "#F2F2F2" }}>{seg[k]}</span>
        </div>
      ))}
    </div>
  );
}

function ReceiptSheet({ night, player, rankAfter, onClose }) {
  if (!night) return null;
  const kindColor = { GROUP: "#9A9A9A", KNOCKOUT: "#FF2E88", TITLE: "#FF2E88",
                      BONUS: "#C6FF00", DROPPED: "#6E6E6E" };
  return (
    <div onClick={onClose} style={{ position: "fixed", inset: 0, zIndex: 80,
      background: "rgba(5,5,5,.86)", display: "flex", alignItems: "flex-end" }}>
      <div onClick={e => e.stopPropagation()} style={{ background: "#0A0A0A", width: "100%",
        maxHeight: "88vh", overflowY: "auto", borderTop: "3px solid #C6FF00" }}>
        <div style={{ position: "sticky", top: 0, background: "#050505", padding: "16px 16px 12px",
                      borderBottom: "1px solid rgba(110,110,110,.16)" }}>
          <div style={{ fontFamily: "'JetBrains Mono',monospace", fontWeight: 700, fontSize: 10,
                        letterSpacing: ".28em", color: "#9A9A9A" }}>
            SESSION {night.no}{night.date ? " · " + night.date : ""}{night.x2 ? " · 2X NIGHT" : ""}
          </div>
          <div style={{ fontStyle: "italic", fontVariationSettings: "'wdth' 125,'wght' 900",
                        fontSize: 34, lineHeight: .95, marginTop: 8 }}>POINTS RECEIPT</div>
          <div style={{ fontSize: 13, color: "#9A9A9A", marginTop: 4 }}>{player?.name}</div>
        </div>

        <div style={{ padding: "4px 16px 16px" }}>
          <div style={{ borderTop: "1px dashed rgba(110,110,110,.4)", marginTop: 12 }} />
          {night.events.map((e, i) => (
            <div key={i} style={{ display: "flex", alignItems: "flex-start", gap: 12,
                 padding: "12px 0", borderBottom: "1px solid rgba(110,110,110,.14)",
                 opacity: e.kind === "DROPPED" ? .55 : 1 }}>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ fontFamily: "'JetBrains Mono',monospace", fontWeight: 700, fontSize: 9,
                              letterSpacing: ".22em", color: kindColor[e.kind] || "#9A9A9A" }}>
                  {e.kind}
                </div>
                <div style={{ fontWeight: 800, fontSize: 14, marginTop: 3 }}>{e.label}</div>
                {e.detail && <div style={{ fontSize: 12, color: "#9A9A9A", marginTop: 2 }}>{e.detail}</div>}
              </div>
              <div style={{ fontFamily: "'JetBrains Mono',monospace", fontWeight: 700, fontSize: 20,
                            color: e.pts === 0 ? "#6E6E6E"
                                 : e.kind === "KNOCKOUT" || e.kind === "TITLE" ? "#FF2E88" : "#C6FF00" }}>
                {e.pts > 0 ? "+" : ""}{e.pts}
              </div>
            </div>
          ))}

          <div style={{ display: "flex", justifyContent: "space-between", padding: "12px 0",
                        fontSize: 13, color: "#9A9A9A" }}>
            <span>SUBTOTAL</span>
            <span style={{ fontFamily: "'JetBrains Mono',monospace", fontWeight: 700,
                           color: "#F2F2F2" }}>{night.subtotal + night.flat}</span>
          </div>
          {night.x2 && (
            <div style={{ display: "flex", justifyContent: "space-between", padding: "0 0 12px",
                          fontSize: 13, color: "#FF2E88" }}>
              <span>DOUBLE POINTS NIGHT &times;2</span>
              <span style={{ fontFamily: "'JetBrains Mono',monospace", fontWeight: 700 }}>
                +{night.subtotal}
              </span>
            </div>
          )}
          <div style={{ background: "#C6FF00", color: "#050505", padding: "14px 16px",
                        display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <span style={{ fontFamily: "'JetBrains Mono',monospace", fontWeight: 700, fontSize: 11,
                           letterSpacing: ".24em" }}>NIGHT TOTAL</span>
            <span style={{ fontFamily: "'JetBrains Mono',monospace", fontWeight: 700, fontSize: 40,
                           lineHeight: 1 }}>{night.nightTotal}</span>
          </div>
          {rankAfter && (
            <div style={{ fontSize: 12, color: "#9A9A9A", marginTop: 14, lineHeight: 1.5 }}>
              After this night: <b style={{ color: "#F2F2F2" }}>#{rankAfter}</b> on the table.
              Only your best three group results count, and a double-points night
              doubles everything except the comeback bonus.
            </div>
          )}
          <button onClick={onClose} style={{ width: "100%", marginTop: 16, padding: "14px",
            background: "transparent", border: "1px solid rgba(110,110,110,.4)", color: "#9A9A9A",
            fontFamily: "'JetBrains Mono',monospace", fontWeight: 700, fontSize: 11,
            letterSpacing: ".24em", cursor: "pointer" }}>CLOSE</button>
        </div>
      </div>
    </div>
  );
}

function MeView({ state, leaderboard, meId, onOpenPicker, setTab }) {
  const [receipt, setReceipt] = React.useState(null);
  const [share, setShare] = React.useState(null);
  const players = state.players || [];
  const sessions = state.sessions || [];
  const nameOf = React.useCallback((s, teamId, pidDirect) => {
    if (pidDirect) return (players.find(p => p.id === pidDirect) || {}).name || "?";
    const t = (s.teams || []).find(x => x.id === teamId);
    if (!t) return "?";
    const n = id => ((players.find(p => p.id === id) || {}).name || "?").split(" ")[0];
    return n(t.p1Id) + " & " + n(t.p2Id);
  }, [players]);

  if (!meId) {
    return (
      <div style={{ padding: "48px 0", textAlign: "center" }}>
        <div style={{ fontStyle: "italic", fontVariationSettings: "'wdth' 125,'wght' 900",
                      fontSize: 34, lineHeight: .95 }}>WHICH ONE<br />ARE YOU?</div>
        <div style={{ fontSize: 13, color: "#9A9A9A", marginTop: 12, maxWidth: 280,
                      margin: "12px auto 0" }}>
          Pick your name once and this screen shows every point you have, and where it came from.
        </div>
        <button onClick={onOpenPicker} style={{ marginTop: 22, padding: "14px 28px",
          background: "#C6FF00", color: "#050505", border: "none", cursor: "pointer",
          fontFamily: "'JetBrains Mono',monospace", fontWeight: 700, fontSize: 12,
          letterSpacing: ".24em" }}>PICK YOUR NAME &#9654;</button>
      </div>
    );
  }

  const me = players.find(p => p.id === meId);
  const data = calcPlayerNights(meId, sessions, nameOf);
  const ranks = React.useMemo(() => rankByNight(players, sessions), [players, sessions]);
  const badges = calcBadges(meId, sessions, players, data, ranks);
  const rank = leaderboard.findIndex(e => e.player.id === meId) + 1;
  const bestNight = Math.max(1, ...leaderboard.flatMap(() => []), ...data.nights.map(n => n.nightTotal));
  const unlocked = badges.filter(b => b.got).length;

  // Everything the story cards need, derived from what this screen already has
  // rather than recomputed -- a card that disagrees with the screen above it is
  // worse than no card.
  const lastNight = data.nights.length ? data.nights[data.nights.length - 1] : null;
  const lastSession = lastNight ? sessions[lastNight.idx] : null;
  const champTeam = lastSession?.bracket?.final?.winner
    ? (lastSession.teams || []).find(t =>
        t.id === (lastSession.bracket.final.winner === "team1"
          ? lastSession.bracket.final.team1Id : lastSession.bracket.final.team2Id))
    : null;
  const showBadge = badges.find(b => b.got) || badges[0];
  const pool = 14 * 2 * SESSIONS_TOTAL + SEASON_PRIZES.reduce((a, b) => a + b, 0);
  const shareData = {
    night: lastNight ? {
      no: lastNight.no, date: lastNight.date, name: me?.name, total: lastNight.nightTotal,
      rank: rank || "-", series: data.total,
      lines: lastNight.events.filter(e => e.pts > 0).slice(0, 4)
                 .map(e => ({ label: e.label, pts: e.pts })),
      caption: `${lastNight.nightTotal} points on session ${lastNight.no}. `
             + `#${rank || "-"} in the Blackout Series on ${data.total}. `
             + `blackout.urbanpadel.om`,
    } : {},
    champs: champTeam ? {
      no: lastNight.no, date: lastNight.date,
      champs: [champTeam.p1Id, champTeam.p2Id]
        .map(id => (players.find(p => p.id === id) || {}).name || "?"),
      score: lastSession.bracket.final.score
        ? lastSession.bracket.final.score.t1 + "\u2013" + lastSession.bracket.final.score.t2 : "",
      caption: `Session ${lastNight.no} champions. 14 OMR voucher each. blackout.urbanpadel.om`,
    } : {},
    top5: {
      rows: leaderboard.slice(0, 5).map(e => ({ name: e.player.name, pts: e.totalPts })),
      pool,
      caption: `Top 5 in the Blackout Series. Playing for ${pool} OMR. blackout.urbanpadel.om`,
    },
    badge: showBadge ? {
      code: showBadge.code, name: showBadge.name, desc: showBadge.desc,
      got: !!showBadge.got, player: me?.name,
      caption: `${showBadge.got ? "Unlocked" : "Chasing"}: ${showBadge.name} \u2014 ${showBadge.desc}. `
             + `blackout.urbanpadel.om`,
    } : {},
  };

  return (
    <div>
      <div style={{ fontFamily: "'JetBrains Mono',monospace", fontWeight: 700, fontSize: 10,
                    letterSpacing: ".28em", color: "#9A9A9A" }}>
        YOUR SEASON &middot; {(me?.name || "").toUpperCase()}
      </div>
      <div style={{ fontStyle: "italic", fontVariationSettings: "'wdth' 125,'wght' 900",
                    fontSize: 46, lineHeight: .9, marginTop: 6 }}>MY POINTS</div>

      {/* summary */}
      <div style={{ border: "1px solid rgba(198,255,0,.35)", background: "rgba(14,14,14,.94)",
                    padding: 18, marginTop: 18 }}>
        <div style={{ display: "flex", alignItems: "flex-end", justifyContent: "space-between" }}>
          <div>
            <div style={{ fontFamily: "'JetBrains Mono',monospace", fontWeight: 700, fontSize: 9,
                          letterSpacing: ".26em", color: "#9A9A9A" }}>SERIES POINTS</div>
            <div style={{ fontFamily: "'JetBrains Mono',monospace", fontWeight: 700, fontSize: 62,
                          lineHeight: 1, color: "#C6FF00" }}>{data.total}</div>
          </div>
          <div style={{ textAlign: "right" }}>
            <div style={{ fontFamily: "'JetBrains Mono',monospace", fontWeight: 700, fontSize: 9,
                          letterSpacing: ".26em", color: "#9A9A9A" }}>RANK</div>
            <div style={{ fontFamily: "'JetBrains Mono',monospace", fontWeight: 700, fontSize: 38,
                          lineHeight: 1, color: rank && rank <= 3 ? "#C6FF00" : "#FF2E88" }}>
              {rank ? "#" + rank : "–"}
            </div>
          </div>
        </div>
        {!data.ok && (
          <div style={{ marginTop: 12, padding: 10, border: "1px solid #FF2E88", color: "#FF2E88",
                        fontSize: 12 }}>
            This breakdown sums to {data.total} but the table says {data.ref}. The table is
            right — please report this.
          </div>
        )}
        <StackedBar seg={data.seg} total={data.total} />
        <SegLegend seg={data.seg} />
      </div>

      {/* night by night */}
      <div style={{ fontFamily: "'JetBrains Mono',monospace", fontWeight: 700, fontSize: 10,
                    letterSpacing: ".28em", color: "#9A9A9A", marginTop: 28 }}>NIGHT BY NIGHT</div>
      {data.nights.length === 0 && (
        <div style={{ fontSize: 13, color: "#6E6E6E", marginTop: 12 }}>
          No nights played yet. Your first receipt appears after your first match.
        </div>
      )}
      {[...data.nights].reverse().map(n => (
        <button key={n.id} onClick={() => setReceipt(n)} style={{ width: "100%", textAlign: "left",
          display: "flex", alignItems: "center", gap: 14, padding: "14px 0",
          borderBottom: "1px solid rgba(110,110,110,.16)", background: "transparent",
          border: "none", borderBottomStyle: "solid", cursor: "pointer", color: "inherit" }}>
          <div style={{ width: 44, height: 44, flexShrink: 0, border: "1px solid rgba(198,255,0,.4)",
                        display: "flex", alignItems: "center", justifyContent: "center",
                        fontFamily: "'JetBrains Mono',monospace", fontWeight: 700, fontSize: 18,
                        color: "#C6FF00" }}>{n.no}</div>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <span style={{ fontWeight: 800, fontSize: 14 }}>{n.outcome}</span>
              {n.x2 && <span style={{ fontFamily: "'JetBrains Mono',monospace", fontWeight: 700,
                fontSize: 9, letterSpacing: ".2em", color: "#FF2E88",
                border: "1px solid rgba(255,46,136,.5)", padding: "1px 5px" }}>2X</span>}
            </div>
            <div style={{ fontSize: 12, color: "#9A9A9A", marginTop: 2 }}>{n.date}</div>
            <div style={{ height: 4, background: "rgba(110,110,110,.2)", marginTop: 7 }}>
              <div style={{ height: "100%", background: "#C6FF00",
                            width: Math.round(n.nightTotal / bestNight * 100) + "%" }} />
            </div>
          </div>
          <div style={{ fontFamily: "'JetBrains Mono',monospace", fontWeight: 700, fontSize: 24,
                        color: "#C6FF00" }}>+{n.nightTotal}</div>
          <span style={{ color: "#6E6E6E" }}>&#9654;</span>
        </button>
      ))}

      {/* badges */}
      <div style={{ display: "flex", alignItems: "baseline", justifyContent: "space-between",
                    marginTop: 28 }}>
        <div style={{ fontFamily: "'JetBrains Mono',monospace", fontWeight: 700, fontSize: 10,
                      letterSpacing: ".28em", color: "#9A9A9A" }}>BADGES</div>
        <div style={{ fontFamily: "'JetBrains Mono',monospace", fontWeight: 700, fontSize: 11,
                      color: "#C6FF00" }}>{unlocked} OF {badges.length}</div>
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10, marginTop: 12 }}>
        {badges.map(b => (
          <div key={b.code} style={{ display: "flex", gap: 10, padding: 12,
            border: "1px solid " + (b.got ? "rgba(198,255,0,.4)" : "rgba(110,110,110,.2)"),
            background: b.got ? "rgba(198,255,0,.06)" : "transparent" }}>
            <div style={{ width: 44, height: 44, flexShrink: 0,
              background: b.got ? "#C6FF00" : "transparent",
              border: b.got ? "none" : "1px solid rgba(110,110,110,.4)",
              color: b.got ? "#050505" : "#6E6E6E",
              display: "flex", alignItems: "center", justifyContent: "center",
              fontFamily: "'JetBrains Mono',monospace", fontWeight: 700, fontSize: 15 }}>{b.code}</div>
            <div style={{ minWidth: 0 }}>
              <div style={{ fontWeight: 800, fontSize: 13,
                            color: b.got ? "#F2F2F2" : "#9A9A9A" }}>{b.name}</div>
              <div style={{ fontSize: 11, color: "#6E6E6E", marginTop: 2, lineHeight: 1.35 }}>{b.desc}</div>
              <div style={{ fontFamily: "'JetBrains Mono',monospace", fontWeight: 700, fontSize: 9,
                            letterSpacing: ".18em", marginTop: 5,
                            color: b.got ? "#C6FF00" : "#6E6E6E" }}>
                {b.got ? "UNLOCKED" : b.locked ? b.locked.toUpperCase() : (b.prog || "LOCKED")}
              </div>
            </div>
          </div>
        ))}
      </div>

      <button onClick={onOpenPicker} style={{ width: "100%", marginTop: 24, padding: "12px",
        background: "transparent", border: "1px solid rgba(110,110,110,.4)", color: "#9A9A9A",
        fontFamily: "'JetBrains Mono',monospace", fontWeight: 700, fontSize: 10,
        letterSpacing: ".24em", cursor: "pointer" }}>NOT YOU? CHANGE NAME</button>

      {/* share */}
      <div style={{ fontFamily: "'JetBrains Mono',monospace", fontWeight: 700, fontSize: 10,
                    letterSpacing: ".28em", color: "#9A9A9A", marginTop: 28 }}>SHARE TO STORY</div>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 8, marginTop: 12 }}>
        <button onClick={() => setShare({ kind: "night" })} disabled={!data.nights.length}
          style={{ padding: "14px 6px", background: data.nights.length ? "#C6FF00" : "transparent",
            color: data.nights.length ? "#050505" : "#6E6E6E",
            border: data.nights.length ? "none" : "1px solid rgba(110,110,110,.3)",
            cursor: data.nights.length ? "pointer" : "default",
            fontFamily: "'JetBrains Mono',monospace", fontWeight: 700, fontSize: 10,
            letterSpacing: ".14em" }}>MY NIGHT</button>
        <button onClick={() => setShare({ kind: "top5" })}
          style={{ padding: "14px 6px", background: "transparent", color: "#F2F2F2",
            border: "1px solid rgba(110,110,110,.4)", cursor: "pointer",
            fontFamily: "'JetBrains Mono',monospace", fontWeight: 700, fontSize: 10,
            letterSpacing: ".14em" }}>TOP 5</button>
        <button onClick={() => setShare({ kind: "badge" })}
          style={{ padding: "14px 6px", background: "transparent", color: "#FF2E88",
            border: "1px solid rgba(255,46,136,.5)", cursor: "pointer",
            fontFamily: "'JetBrains Mono',monospace", fontWeight: 700, fontSize: 10,
            letterSpacing: ".14em" }}>BADGE</button>
      </div>

      <ShareSheet open={share} onClose={() => setShare(null)} data={shareData} />

      <ReceiptSheet night={receipt} player={me}
        rankAfter={receipt ? (ranks[receipt.idx] || {})[meId] : null}
        onClose={() => setReceipt(null)} />
    </div>
  );
}

// ══ VOL.8 · ROSTER ════════════════════════════════════════════════════════
// The admin PlayersView is an editor. This is the read-only wall everyone else
// gets: who is playing, how they are doing, tap through to their card.
function RosterView({ state, leaderboard, setOpenPlayerId, meId }) {
  const [q, setQ] = React.useState("");
  const rows = leaderboard
    .map((e, i) => ({ ...e, rank: i + 1 }))
    .filter(e => !q || (e.player.name || "").toLowerCase().includes(q.toLowerCase()));
  return (
    <div>
      <div style={{ fontFamily: "'JetBrains Mono',monospace", fontWeight: 700, fontSize: 10,
                    letterSpacing: ".28em", color: "#9A9A9A" }}>
        THE ROSTER &middot; {leaderboard.length} PLAYERS
      </div>
      <div style={{ fontStyle: "italic", fontVariationSettings: "'wdth' 125,'wght' 900",
                    fontSize: 46, lineHeight: .9, marginTop: 6 }}>PLAYERS</div>
      <input value={q} onChange={e => setQ(e.target.value)} placeholder="Find a player&hellip;"
        style={{ width: "100%", marginTop: 16, padding: "14px 16px", background: "rgba(20,20,20,.96)",
          border: "1px solid rgba(110,110,110,.2)", color: "#F2F2F2", fontSize: 15,
          fontFamily: "'Archivo',sans-serif", outline: "none" }} />
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10, marginTop: 14 }}>
        {rows.map(e => (
          <button key={e.player.id} onClick={() => setOpenPlayerId(e.player.id)}
            style={{ textAlign: "left", padding: 12, cursor: "pointer", color: "inherit",
              background: e.player.id === meId ? "rgba(255,46,136,.07)" : "rgba(14,14,14,.94)",
              border: "1px solid " + (e.player.id === meId ? "rgba(255,46,136,.4)"
                                                          : "rgba(255,255,255,.07)") }}>
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <span style={{ fontFamily: "'JetBrains Mono',monospace", fontWeight: 700, fontSize: 11,
                             color: e.rank <= 3 ? "#C6FF00" : "#6E6E6E" }}>#{e.rank}</span>
              {e.player.id === meId && (
                <span style={{ fontFamily: "'JetBrains Mono',monospace", fontWeight: 700, fontSize: 8,
                  letterSpacing: ".2em", color: "#FF2E88" }}>YOU</span>
              )}
            </div>
            <div style={{ fontWeight: 800, fontSize: 14, marginTop: 6, whiteSpace: "nowrap",
                          overflow: "hidden", textOverflow: "ellipsis" }}>{e.player.name}</div>
            <div style={{ fontSize: 11, color: "#9A9A9A", marginTop: 2 }}>
              {e.stats.sessionsPlayed} night{e.stats.sessionsPlayed === 1 ? "" : "s"}
            </div>
            <div style={{ fontFamily: "'JetBrains Mono',monospace", fontWeight: 700, fontSize: 22,
                          color: "#C6FF00", marginTop: 8 }}>{e.totalPts}</div>
          </button>
        ))}
      </div>
    </div>
  );
}
"""


# ── Splice anchors ────────────────────────────────────────────────────────
# The nav gains ME for everyone and a public PLAYERS tab; the admin editor keeps
# its own entry so the organiser is not sent to the read-only wall.
NAV_OLD = """  const navTabs = [
    { id: "dashboard", icon: I.flame, label: "HOME" },
    { id: "sessions", icon: I.calendar, label: "SESSIONS" },
    { id: "leaderboard", icon: I.trophy, label: "RANK" },
    ...(isAdmin ? [{ id: "players", icon: I.users, label: "PLAYERS" }] : []),
  ];"""

NAV_NEW = """  // Vol.8 runs the handoff's five tabs. ME is the new one and is the reason the
  // volume exists -- every point a player holds now traces back to a receipt.
  // The admin editor keeps its own entry so the organiser is not sent to the
  // read-only wall.
  const navTabs = [
    { id: "dashboard", icon: I.flame, label: "HOME" },
    { id: "sessions", icon: I.calendar, label: "SESSIONS" },
    { id: "leaderboard", icon: I.trophy, label: "RANK" },
    { id: "me", icon: I.user, label: "ME" },
    { id: isAdmin ? "players" : "roster", icon: I.users, label: "PLAYERS" },
  ];"""

ROUTE_OLD = """        {tab === "players" && isAdmin && <PlayersView state={state} update={update} setOpenPlayerId={setOpenPlayerId} isAdmin={isAdmin} />}"""

ROUTE_NEW = """        {tab === "players" && isAdmin && <PlayersView state={state} update={update} setOpenPlayerId={setOpenPlayerId} isAdmin={isAdmin} />}
        {tab === "me" && <MeView state={state} leaderboard={leaderboard} meId={meId} onOpenPicker={() => setShowMe(true)} setTab={setTab} />}
        {tab === "roster" && <RosterView state={state} leaderboard={leaderboard} setOpenPlayerId={setOpenPlayerId} meId={meId} />}"""

# The icon set has `users` (a group) but no single-person glyph, and ME needs one.
ICON_OLD = """  users: (p) => <Icon"""
ICON_NEW = """  user: (p) => <Icon d='<path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2"/><circle cx="12" cy="7" r="4"/>' {...p} />,
  users: (p) => <Icon"""

# The nav grid was hard-coded to 3 or 4 columns depending on admin. Vol.8 always
# has five tabs, so it wraps to two rows unless the grid is told. The handoff
# also asks for the active tab to carry a lime tick above its label, which the
# Vol.7 nav did not have.
NAVGRID_OLD = '''        <div className={`max-w-3xl mx-auto grid ${isAdmin ? "grid-cols-4" : "grid-cols-3"} px-2 py-1.5`}>'''
NAVGRID_NEW = '''        <div className="max-w-3xl mx-auto grid px-2 py-1.5"
             style={{ gridTemplateColumns: `repeat(${navTabs.length}, minmax(0, 1fr))` }}>'''

NAVBTN_OLD = '''            return <button key={t.id} onClick={() => setTab(t.id)} className={`flex flex-col items-center gap-0.5 py-2 rounded-lg transition-colors ${tab === t.id ? "" : "text-stone-500"}`} style={tab === t.id ? { color: "var(--orange-br)" } : {}}>
              <A size={20} /><span className="text-[10px] font-semibold tracking-wide uppercase">{t.label}</span>
            </button>;'''
NAVBTN_NEW = '''            const on = tab === t.id;
            return <button key={t.id} onClick={() => setTab(t.id)}
              className="relative flex flex-col items-center gap-0.5 py-2 transition-colors"
              style={{ color: on ? "#C6FF00" : "#6E6E6E",
                       background: on ? "rgba(198,255,0,.07)" : "transparent" }}>
              {on && <span style={{ position: "absolute", top: 0, width: 26, height: 3,
                                    background: "#C6FF00" }} />}
              <A size={20} />
              <span style={{ fontFamily: "'JetBrains Mono',monospace", fontWeight: 700,
                             fontSize: 10, letterSpacing: ".16em" }}>{t.label}</span>
            </button>;'''


# ══════════════════════════════════════════════════════════════════════════
# 3 · SHARE TO STORY — four card kinds, rendered once at 1080x1920
# ══════════════════════════════════════════════════════════════════════════
SHARE = r"""

// ══ VOL.8 · SHARE TO STORY ════════════════════════════════════════════════
//
// The handoff describes a 270x480 DOM preview that exports at 1080x1920 "x4".
// Two renderers of the same card drift, and the one people see is not the one
// they post. So this draws the real 1080x1920 card ONCE on a canvas and shows
// that same bitmap scaled down as the preview — what you see is the file.
//
// Canvas cannot set font-variation-settings, so the display type here sits at
// Archivo's default width rather than the app's 'wdth' 125. It is the one place
// in Vol.8 the wordmark is not pushed wide, and it is a platform limit, not an
// oversight.

const ST_W = 1080, ST_H = 1920;

function stFit(ctx, text, max, size, weight) {
  let s = size;
  for (;;) {
    ctx.font = `italic ${weight} ${s}px Archivo, sans-serif`;
    if (ctx.measureText(text).width <= max || s <= 18) return s;
    s -= 2;
  }
}
function stDisp(ctx, text, x, y, size, color, max) {
  const s = max ? stFit(ctx, text, max, size, 900) : size;
  ctx.font = `italic 900 ${s}px Archivo, sans-serif`;
  ctx.fillStyle = color;
  ctx.fillText(text, x, y);
  return s;
}
function stMono(ctx, text, x, y, size, color, track) {
  ctx.font = `700 ${size}px "JetBrains Mono", monospace`;
  ctx.fillStyle = color;
  if (!track) { ctx.fillText(text, x, y); return; }
  let cx = x;
  for (const ch of text) { ctx.fillText(ch, cx, y); cx += ctx.measureText(ch).width + track; }
}

function drawStory(kind, d) {
  const c = document.createElement("canvas");
  c.width = ST_W; c.height = ST_H;
  const g = c.getContext("2d");

  g.fillStyle = "#050505"; g.fillRect(0, 0, ST_W, ST_H);
  // the brand's corner washes
  let rg = g.createRadialGradient(ST_W, ST_H * 0.18, 0, ST_W, ST_H * 0.18, ST_W * 0.9);
  rg.addColorStop(0, "rgba(255,46,136,.20)"); rg.addColorStop(1, "rgba(255,46,136,0)");
  g.fillStyle = rg; g.fillRect(0, 0, ST_W, ST_H);
  rg = g.createRadialGradient(0, ST_H * 0.92, 0, 0, ST_H * 0.92, ST_W * 0.9);
  rg.addColorStop(0, "rgba(198,255,0,.10)"); rg.addColorStop(1, "rgba(198,255,0,0)");
  g.fillStyle = rg; g.fillRect(0, 0, ST_W, ST_H);
  // scanlines
  g.fillStyle = "rgba(198,255,0,.045)";
  for (let y = 0; y < ST_H; y += 10) g.fillRect(0, y, ST_W, 2);
  // top rail
  g.fillStyle = "#C6FF00"; g.fillRect(0, 0, ST_W, 10);

  // the mark, drawn rather than loaded so the card never waits on an image
  const mx = 86, my = 150, ms = 96;
  g.fillStyle = "#C6FF00"; g.fillRect(mx, my, ms, ms);
  g.fillStyle = "#050505";
  [[0.47, 0.03], [0.59, 0.06], [0.73, 0.09], [0.89, 0.11]].forEach(([t, h]) =>
    g.fillRect(mx, my + ms * t, ms, ms * h));
  g.fillStyle = "#FF2E88"; g.fillRect(mx + ms * 0.75, my + ms * 0.12, ms * 0.13, ms * 0.13);
  stMono(g, "BLACKOUT SERIES · VOL.8", mx + ms + 28, my + ms * 0.62, 24, "#9A9A9A", 3);

  const L = 86, R = ST_W - 86, W = R - L;
  g.textBaseline = "alphabetic";

  if (kind === "night") {
    stMono(g, `SESSION ${d.no}  ·  ${(d.date || "").toUpperCase()}`, L, 420, 26, "#C6FF00", 5);
    stDisp(g, "MY", L, 580, 150, "#F2F2F2", W);
    stDisp(g, "NIGHT", L, 720, 150, "#C6FF00", W);
    stDisp(g, (d.name || "").toUpperCase(), L, 850, 72, "#F2F2F2", W);
    g.font = "700 220px Archivo, sans-serif";
    g.fillStyle = "#C6FF00";
    g.fillText("+" + d.total, L, 1090);
    stMono(g, "POINTS THIS NIGHT", L, 1150, 24, "#9A9A9A", 4);
    // Four lines, not five: the fifth landed under the footer plate at 1628.
    let y = 1260;
    (d.lines || []).slice(0, 4).forEach(ln => {
      g.fillStyle = "rgba(110,110,110,.3)"; g.fillRect(L, y - 44, W, 2);
      g.font = "800 34px Archivo, sans-serif"; g.fillStyle = "#F2F2F2";
      g.fillText(ln.label, L, y);
      g.font = '700 38px "JetBrains Mono", monospace';
      g.fillStyle = ln.pts > 0 ? "#C6FF00" : "#6E6E6E";
      const t = (ln.pts > 0 ? "+" : "") + ln.pts;
      g.fillText(t, R - g.measureText(t).width, y);
      y += 92;
    });
    g.fillStyle = "#C6FF00"; g.fillRect(L, ST_H - 300, W, 116);
    stMono(g, `SERIES #${d.rank}  ·  ${d.series} PTS`, L + 36, ST_H - 224, 36, "#050505", 4);
  }

  if (kind === "champs") {
    stDisp(g, "NIGHT", L, 560, 150, "#F2F2F2", W);
    stDisp(g, "CHAMPS", L, 700, 150, "#C6FF00", W);
    stMono(g, `SESSION ${d.no} · ${(d.date || "").toUpperCase()}`, L, 780, 26, "#9A9A9A", 5);
    g.strokeStyle = "#C6FF00"; g.lineWidth = 4;
    g.strokeRect(L, 860, W, 420);
    (d.champs || []).forEach((n, i) => stDisp(g, n.toUpperCase(), L + 44, 990 + i * 110, 74, "#F2F2F2", W - 88));
    stMono(g, "14 OMR VOUCHER EACH", L + 44, 1220, 28, "#FF2E88", 4);
    if (d.score) stDisp(g, d.score, L, 1420, 96, "#9A9A9A", W);
    stMono(g, "BLACKOUT.URBANPADEL.OM", L, ST_H - 220, 26, "#6E6E6E", 5);
  }

  if (kind === "top5") {
    stDisp(g, "AS IT", L, 560, 150, "#F2F2F2", W);
    stDisp(g, "STANDS", L, 700, 150, "#C6FF00", W);
    let y = 880;
    (d.rows || []).slice(0, 5).forEach((r, i) => {
      if (i === 0) { g.strokeStyle = "#C6FF00"; g.lineWidth = 4; g.strokeRect(L, y - 66, W, 104); }
      else { g.fillStyle = "rgba(110,110,110,.3)"; g.fillRect(L, y + 38, W, 2); }
      g.font = '700 42px "JetBrains Mono", monospace';
      g.fillStyle = i === 0 ? "#C6FF00" : "#6E6E6E";
      g.fillText(String(i + 1), L + 26, y);
      const nm = stFit(g, r.name, W - 300, 54, 900);
      g.font = `italic 900 ${nm}px Archivo, sans-serif`; g.fillStyle = "#F2F2F2";
      g.fillText(r.name, L + 100, y);
      g.font = '700 48px "JetBrains Mono", monospace';
      g.fillStyle = i === 0 ? "#C6FF00" : "#F2F2F2";
      const t = String(r.pts);
      g.fillText(t, R - 26 - g.measureText(t).width, y);
      y += 128;
    });
    stMono(g, `PLAYING FOR ${d.pool} OMR`, L, ST_H - 240, 32, "#FF2E88", 5);
  }

  if (kind === "badge") {
    stDisp(g, "BADGE", L, 560, 150, "#F2F2F2", W);
    stDisp(g, d.got ? "UNLOCKED" : "IN REACH", L, 700, 150, d.got ? "#C6FF00" : "#FF2E88", W);
    const bs = 300, bx = (ST_W - bs) / 2;
    g.fillStyle = d.got ? "#C6FF00" : "transparent"; g.fillRect(bx, 880, bs, bs);
    if (!d.got) { g.strokeStyle = "#6E6E6E"; g.lineWidth = 4; g.strokeRect(bx, 880, bs, bs); }
    g.font = '700 128px "JetBrains Mono", monospace';
    g.fillStyle = d.got ? "#050505" : "#6E6E6E";
    g.fillText(d.code, bx + (bs - g.measureText(d.code).width) / 2, 1055);
    g.textAlign = "center";
    stDisp(g, (d.name || "").toUpperCase(), ST_W / 2, 1300, 86, "#F2F2F2", W);
    g.font = "400 36px Archivo, sans-serif"; g.fillStyle = "#9A9A9A";
    g.fillText(d.desc || "", ST_W / 2, 1370);
    g.font = "800 44px Archivo, sans-serif"; g.fillStyle = "#C6FF00";
    g.fillText(d.player || "", ST_W / 2, 1480);
    g.textAlign = "left";
  }

  return c.toDataURL("image/png");
}

const ST_TABS = [["night", "MY NIGHT"], ["champs", "CHAMPS"], ["top5", "TOP 5"], ["badge", "BADGE"]];

function ShareSheet({ open, data, onClose }) {
  const [kind, setKind] = React.useState(open?.kind || "night");
  const [url, setUrl] = React.useState("");
  const [flash, setFlash] = React.useState("");
  React.useEffect(() => { if (open) setKind(open.kind || "night"); }, [open]);
  React.useEffect(() => {
    if (!open) return;
    let alive = true;
    // The display face has to be in before the canvas measures anything, or
    // every card is laid out against a fallback and the type overruns.
    document.fonts.ready.then(() => { if (alive) setUrl(drawStory(kind, data[kind] || {})); });
    return () => { alive = false; };
  }, [open, kind, data]);
  if (!open) return null;

  const save = async () => {
    try {
      const blob = await (await fetch(url)).blob();
      const f = new File([blob], `blackout-${kind}.png`, { type: "image/png" });
      if (navigator.canShare && navigator.canShare({ files: [f] })) {
        await navigator.share({ files: [f], title: "Blackout Series" });
        return;
      }
    } catch (e) { if (e && e.name === "AbortError") return; }
    const a = document.createElement("a");
    a.href = url; a.download = `blackout-${kind}.png`;
    document.body.appendChild(a); a.click(); a.remove();
    setFlash("SAVED"); setTimeout(() => setFlash(""), 1600);
  };
  const copy = async () => {
    try { await navigator.clipboard.writeText((data[kind] || {}).caption || ""); setFlash("CAPTION COPIED"); }
    catch (e) { setFlash("COULDN'T COPY"); }
    setTimeout(() => setFlash(""), 1600);
  };

  return (
    <div onClick={onClose} style={{ position: "fixed", inset: 0, zIndex: 90,
      background: "rgba(5,5,5,.9)", display: "flex", alignItems: "flex-end" }}>
      <div onClick={e => e.stopPropagation()} style={{ background: "#0A0A0A", width: "100%",
        maxHeight: "94vh", overflowY: "auto", borderTop: "3px solid #FF2E88", padding: 16 }}>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: 6 }}>
          {ST_TABS.map(([k, label]) => (
            <button key={k} onClick={() => setKind(k)} style={{ padding: "10px 4px", cursor: "pointer",
              background: kind === k ? "#C6FF00" : "transparent",
              color: kind === k ? "#050505" : "#9A9A9A",
              border: "1px solid " + (kind === k ? "#C6FF00" : "rgba(110,110,110,.3)"),
              fontFamily: "'JetBrains Mono',monospace", fontWeight: 700, fontSize: 10,
              letterSpacing: ".12em" }}>{label}</button>
          ))}
        </div>
        <div style={{ display: "flex", justifyContent: "center", margin: "16px 0" }}>
          {url
            ? <img src={url} alt="" style={{ width: 270, height: 480, display: "block",
                                             border: "1px solid rgba(110,110,110,.3)" }} />
            : <div style={{ width: 270, height: 480, background: "#111" }} />}
        </div>
        <div style={{ fontSize: 11, color: "#6E6E6E", textAlign: "center", marginBottom: 12 }}>
          Preview is the actual 1080&times;1920 file, shown small.
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
          <button onClick={save} style={{ padding: "16px", background: "#C6FF00", color: "#050505",
            border: "none", cursor: "pointer", fontFamily: "'JetBrains Mono',monospace",
            fontWeight: 700, fontSize: 11, letterSpacing: ".2em" }}>SAVE IMAGE</button>
          <button onClick={copy} style={{ padding: "16px", background: "transparent", color: "#FF2E88",
            border: "1px solid rgba(255,46,136,.5)", cursor: "pointer",
            fontFamily: "'JetBrains Mono',monospace", fontWeight: 700, fontSize: 11,
            letterSpacing: ".2em" }}>COPY CAPTION</button>
        </div>
        {flash && <div style={{ textAlign: "center", marginTop: 12, color: "#C6FF00",
          fontFamily: "'JetBrains Mono',monospace", fontWeight: 700, fontSize: 11,
          letterSpacing: ".2em" }}>{flash}</div>}
        <button onClick={onClose} style={{ width: "100%", marginTop: 14, padding: "12px",
          background: "transparent", border: "1px solid rgba(110,110,110,.4)", color: "#9A9A9A",
          fontFamily: "'JetBrains Mono',monospace", fontWeight: 700, fontSize: 10,
          letterSpacing: ".24em", cursor: "pointer" }}>CLOSE</button>
      </div>
    </div>
  );
}
"""
