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
  // Before the season starts nobody has series points, so ordering by them puts
  // 314 people in an arbitrary order and shows every one of them a zero. Until
  // the first match is played the roster ranks on all-time instead, which is
  // the only number that exists and the reason the history was carried over.
  const started = leaderboard.some(e => e.totalPts > 0);
  const ranked = started ? leaderboard
                         : [...leaderboard].sort((a, b) => b.lifetimePts - a.lifetimePts);
  const rows = ranked
    .map((e, i) => {
      const form = recentForm(e.player.id, state.sessions || []);
      return { ...e, rank: i + 1, form, streak: currentStreak(form) };
    })
    .filter(e => !q || (e.player.name || "").toLowerCase().includes(q.toLowerCase()));
  return (
    <div>
      <div style={{ fontFamily: "'JetBrains Mono',monospace", fontWeight: 700, fontSize: 10,
                    letterSpacing: ".28em", color: "#9A9A9A" }}>
        THE ROSTER &middot; {leaderboard.length} PLAYERS
        {!started && <span style={{ color: "#6E6E6E" }}> &middot; BY ALL-TIME</span>}
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
              {e.streak >= 3 && (
                <span style={{ marginLeft: "auto", fontFamily: "'JetBrains Mono',monospace",
                  fontWeight: 700, fontSize: 8, letterSpacing: ".14em", color: "#FF2E88",
                  border: "1px solid rgba(255,46,136,.5)", padding: "1px 4px" }}>W{e.streak}</span>
              )}
            </div>
            {/* A roster of 314 names needs faces. The photo slot keeps its
                height whether or not there is one, so the grid stays even. */}
            <div style={{ width: "100%", height: 120, marginTop: 8, background: "#111",
              border: "1px solid rgba(255,255,255,.05)", overflow: "hidden",
              display: "flex", alignItems: "center", justifyContent: "center" }}>
              {e.player.photoUrl
                ? <img src={e.player.photoUrl} alt="" style={{ width: "100%", height: "100%",
                    objectFit: "cover", objectPosition: "center 28%" }} />
                : <span style={{ fontFamily: "'JetBrains Mono',monospace", fontWeight: 700,
                    fontSize: 26, color: "#2A2A2A" }}>
                    {(e.player.name || "?").split(" ").map(w => w[0]).join("").slice(0,2).toUpperCase()}
                  </span>}
            </div>
            <div style={{ fontWeight: 800, fontSize: 14, marginTop: 8, whiteSpace: "nowrap",
                          overflow: "hidden", textOverflow: "ellipsis" }}>{e.player.name}</div>
            <div style={{ fontSize: 11, color: "#9A9A9A", marginTop: 2 }}>
              {started
                ? e.stats.sessionsPlayed + " night" + (e.stats.sessionsPlayed === 1 ? "" : "s")
                : (e.lifetimePts > 0 ? "all-time" : "new this season")}
            </div>
            <div style={{ fontFamily: "'JetBrains Mono',monospace", fontWeight: 700, fontSize: 22,
                          marginTop: 8,
                          color: (started ? e.totalPts : e.lifetimePts) > 0 ? "#C6FF00" : "#6E6E6E" }}>
              {started ? e.totalPts : e.lifetimePts}
            </div>
            {e.form && e.form.length > 0 && (
              <div style={{ display: "flex", gap: 2, marginTop: 7 }}>
                {e.form.slice(-8).map((w, i) => (
                  <span key={i} style={{ flex: 1, height: 4,
                    background: w ? "#C6FF00" : "rgba(110,110,110,.3)" }} />
                ))}
              </div>
            )}
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


# ══════════════════════════════════════════════════════════════════════════
# 4 · PULL TO REFRESH, SKELETON, FINALS COUNTDOWN, PRIZE TRACKER, RECAP
# ══════════════════════════════════════════════════════════════════════════
CHROME = r"""

// ══ VOL.8 · LOADING AND REFRESH ═══════════════════════════════════════════

// Six blocks in the shape of the home screen, with a lime sweep across them.
// Shown on first paint and during a manual refresh, because a blank screen for
// a second reads as "broken" and a skeleton reads as "coming".
function Skeleton() {
  const H = [176, 92, 66, 66, 66, 120];
  return (
    <div style={{ padding: "4px 0" }}>
      {H.map((h, i) => (
        <div key={i} style={{ height: h, marginBottom: 12, position: "relative",
          overflow: "hidden", background: "rgba(20,20,20,.96)",
          border: "1px solid rgba(255,255,255,.05)" }}>
          <div style={{ position: "absolute", inset: 0, animation: "bo-shimmer 1.1s linear infinite",
            background: "linear-gradient(90deg, transparent, rgba(198,255,0,.07), transparent)" }} />
        </div>
      ))}
    </div>
  );
}

// Pull-to-refresh. Touch only: a mouse has a refresh button and a trackpad
// gesture already, and binding this to the mouse hijacks text selection.
function usePullToRefresh(onRefresh, blocked) {
  const [pull, setPull] = React.useState(0);
  const start = React.useRef(null);
  React.useEffect(() => {
    const TH = 64, MAX = 110;
    const down = e => {
      if (blocked() || window.scrollY > 0) { start.current = null; return; }
      start.current = e.touches[0].clientY;
    };
    const move = e => {
      if (start.current == null) return;
      const d = e.touches[0].clientY - start.current;
      if (d <= 0) { setPull(0); return; }
      // Half the finger travel, capped: a 1:1 strip feels loose and a long drag
      // on a phone overshoots the whole header.
      setPull(Math.min(d * 0.5, MAX));
    };
    const up = () => {
      if (start.current == null) return;
      setPull(p => { if (p >= TH) onRefresh(); return 0; });
      start.current = null;
    };
    document.addEventListener("touchstart", down, { passive: true });
    document.addEventListener("touchmove", move, { passive: true });
    document.addEventListener("touchend", up, { passive: true });
    document.addEventListener("touchcancel", up, { passive: true });
    return () => {
      document.removeEventListener("touchstart", down);
      document.removeEventListener("touchmove", move);
      document.removeEventListener("touchend", up);
      document.removeEventListener("touchcancel", up);
    };
  }, [onRefresh, blocked]);
  return pull;
}

function PullStrip({ pull }) {
  if (pull <= 0) return null;
  const ready = pull >= 64;
  return (
    <div style={{ height: pull, display: "flex", flexDirection: "column",
      alignItems: "center", justifyContent: "center", overflow: "hidden" }}>
      <div style={{ width: Math.min(90, pull), height: 3, background: "#C6FF00" }} />
      <div style={{ marginTop: 8, fontFamily: "'JetBrains Mono',monospace", fontWeight: 700,
        fontSize: 9, letterSpacing: ".24em", color: ready ? "#C6FF00" : "#6E6E6E" }}>
        {ready ? "RELEASE TO REFRESH" : "PULL TO REFRESH"}
      </div>
    </div>
  );
}

// ══ VOL.8 · FINALS COUNTDOWN ══════════════════════════════════════════════
// Dates come from the sessions themselves, so the countdown cannot drift from
// the schedule the organiser actually entered.
function FinalsCountdown({ state, leaderboard, meId, setTab }) {
  const [now, setNow] = React.useState(Date.now());
  React.useEffect(() => {
    const t = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(t);
  }, []);

  const sessions = state.sessions || [];
  // Before the organiser has created the nine nights there is no session to
  // read a date from, and the countdown is most wanted exactly then -- during
  // signup. So it falls back to the scheduled finals date from the season
  // config, and only prefers a session once one exists at that slot.
  const finals = sessions.length >= SESSIONS_TOTAL ? sessions[SESSIONS_TOTAL - 1]
               : sessions.length ? sessions[sessions.length - 1]
               : { date: FINALS_DATE };
  if (!finals || !finals.date) return null;
  // Parsed field by field: the server runs UTC+4, and new Date("2026-10-30")
  // is parsed as UTC, which puts the night a day early for everyone here.
  const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(finals.date);
  if (!m) return null;
  const target = new Date(+m[1], +m[2] - 1, +m[3], 17, 30, 0).getTime();
  const left = Math.max(0, target - now);
  const d = Math.floor(left / 86400000);
  const h = Math.floor(left / 3600000) % 24;
  const mi = Math.floor(left / 60000) % 60;
  const se = Math.floor(left / 1000) % 60;
  const done = left === 0;

  const myRank = meId ? leaderboard.findIndex(e => e.player.id === meId) + 1 : 0;
  const myPts = myRank ? leaderboard[myRank - 1].totalPts : 0;
  const third = leaderboard[2]?.totalPts ?? 0;
  const fourth = leaderboard[3]?.totalPts ?? 0;
  const inPrizes = myRank > 0 && myRank <= 3;
  const gap = inPrizes ? myPts - fourth : third - myPts;

  const Tile = ({ v, l }) => (
    <div style={{ flex: 1, textAlign: "center", padding: "10px 0",
                  border: "1px solid rgba(255,46,136,.3)" }}>
      <div style={{ fontStyle: "italic", fontVariationSettings: "'wdth' 125,'wght' 900",
        fontSize: 30, lineHeight: 1, fontVariantNumeric: "tabular-nums" }}>
        {String(v).padStart(2, "0")}
      </div>
      <div style={{ fontFamily: "'JetBrains Mono',monospace", fontWeight: 700, fontSize: 8,
        letterSpacing: ".2em", color: "#9A9A9A", marginTop: 5 }}>{l}</div>
    </div>
  );

  return (
    <div style={{ border: "1px solid rgba(255,46,136,.4)", background: "rgba(20,20,20,.96)",
                  padding: 16, marginTop: 20 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline" }}>
        <div style={{ fontFamily: "'JetBrains Mono',monospace", fontWeight: 700, fontSize: 9,
          letterSpacing: ".26em", color: "#FF2E88" }}>
          {done ? "FINALS NIGHT · TONIGHT" : "FINALS NIGHT · " + fmtNightDate(finals.date)}
        </div>
        <div style={{ fontFamily: "'JetBrains Mono',monospace", fontWeight: 700, fontSize: 12,
          color: "#C6FF00" }}>{SEASON_PRIZES.join(" · ")} OMR</div>
      </div>
      {!done && (
        <div style={{ display: "flex", gap: 6, marginTop: 12 }}>
          <Tile v={d} l="DAYS" /><Tile v={h} l="HRS" /><Tile v={mi} l="MIN" /><Tile v={se} l="SEC" />
        </div>
      )}
      {myRank > 0 && (
        <button onClick={() => setTab("me")} style={{ width: "100%", marginTop: 12, padding: "12px",
          display: "flex", alignItems: "center", gap: 10, cursor: "pointer", color: "inherit",
          background: "transparent", border: "1px solid rgba(110,110,110,.25)", textAlign: "left" }}>
          <span style={{ fontFamily: "'JetBrains Mono',monospace", fontWeight: 700, fontSize: 15,
            padding: "3px 8px", color: "#050505",
            background: inPrizes ? "#C6FF00" : "#FF2E88" }}>#{myRank}</span>
          <span style={{ flex: 1, fontSize: 12, color: "#9A9A9A", lineHeight: 1.35 }}>
            {inPrizes
              ? <>In the season prizes &middot; <b style={{ color: "#F2F2F2" }}>{gap} pts</b> clear of 4th</>
              : <><b style={{ color: "#F2F2F2" }}>{Math.max(0, gap)} pts</b> behind 3rd place</>}
          </span>
          <span style={{ color: "#6E6E6E" }}>&#9654;</span>
        </button>
      )}
    </div>
  );
}

function fmtNightDate(s) {
  const M = ["JAN","FEB","MAR","APR","MAY","JUN","JUL","AUG","SEP","OCT","NOV","DEC"];
  const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(s || "");
  return m ? (+m[3]) + " " + M[+m[2] - 1] : (s || "").toUpperCase();
}

// ══ VOL.8 · PRIZE TRACKER ═════════════════════════════════════════════════
function PrizeSheet({ open, state, leaderboard, onClose }) {
  if (!open) return null;
  const sessions = state.sessions || [];
  const doneNights = sessions.filter(s => s.completed);
  const voucher = 14, perTeam = 2;
  const pool = voucher * perTeam * SESSIONS_TOTAL + SEASON_PRIZES.reduce((a, b) => a + b, 0);
  const paid = doneNights.length * voucher * perTeam;
  const left = pool - paid;
  const nameOf = id => (state.players.find(p => p.id === id) || {}).name || "?";
  const champsOf = s => {
    const f = s.bracket?.final;
    if (!f || !f.winner) return null;
    const tid = f.winner === "team1" ? f.team1Id : f.team2Id;
    const t = (s.teams || []).find(x => x.id === tid);
    return t ? [nameOf(t.p1Id), nameOf(t.p2Id)] : null;
  };
  const earners = {};
  doneNights.forEach(s => { (champsOf(s) || []).forEach(n => { earners[n] = (earners[n] || 0) + voucher; }); });
  const top = Object.entries(earners).sort((a, b) => b[1] - a[1]).slice(0, 6);

  return (
    <div onClick={onClose} style={{ position: "fixed", inset: 0, zIndex: 80,
      background: "rgba(5,5,5,.88)", display: "flex", alignItems: "flex-end" }}>
      <div onClick={e => e.stopPropagation()} style={{ background: "#0A0A0A", width: "100%",
        maxHeight: "90vh", overflowY: "auto", borderTop: "3px solid #C6FF00", padding: 16 }}>
        <div style={{ background: "#C6FF00", color: "#050505", padding: 18 }}>
          <div style={{ fontFamily: "'JetBrains Mono',monospace", fontWeight: 700, fontSize: 10,
            letterSpacing: ".26em" }}>PLAYING FOR</div>
          <div style={{ fontStyle: "italic", fontVariationSettings: "'wdth' 125,'wght' 900",
            fontSize: 60, lineHeight: 1 }}>{pool} OMR</div>
          <div style={{ height: 8, background: "rgba(5,5,5,.2)", marginTop: 14 }}>
            <div style={{ height: "100%", background: "#050505",
                          width: Math.round(paid / pool * 100) + "%" }} />
          </div>
          <div style={{ display: "flex", justifyContent: "space-between", marginTop: 8,
            fontFamily: "'JetBrains Mono',monospace", fontWeight: 700, fontSize: 11 }}>
            <span>{paid} OMR PAID</span><span>{left} OMR LEFT</span>
          </div>
        </div>

        <div style={{ fontFamily: "'JetBrains Mono',monospace", fontWeight: 700, fontSize: 10,
          letterSpacing: ".26em", color: "#9A9A9A", marginTop: 22 }}>
          SEASON PRIZES &middot; IF IT ENDED NOW
        </div>
        {SEASON_PRIZES.map((amt, i) => {
          const e = leaderboard[i];
          return (
            <div key={i} style={{ display: "flex", alignItems: "center", gap: 12, padding: "12px 0",
              borderBottom: "1px solid rgba(110,110,110,.16)" }}>
              <span style={{ fontFamily: "'JetBrains Mono',monospace", fontWeight: 700, fontSize: 13,
                color: "#C6FF00", width: 34 }}>{i + 1}{["ST","ND","RD"][i] || "TH"}</span>
              <span style={{ flex: 1, fontWeight: 800, fontSize: 14 }}>{e ? e.player.name : "—"}</span>
              <span style={{ fontSize: 12, color: "#9A9A9A" }}>{e ? e.totalPts + " pts" : ""}</span>
              <span style={{ fontFamily: "'JetBrains Mono',monospace", fontWeight: 700, fontSize: 16,
                color: "#FF2E88" }}>{amt}</span>
            </div>
          );
        })}

        <div style={{ fontFamily: "'JetBrains Mono',monospace", fontWeight: 700, fontSize: 10,
          letterSpacing: ".26em", color: "#9A9A9A", marginTop: 22 }}>
          NIGHTLY VOUCHERS &middot; {voucher} OMR EACH
        </div>
        {doneNights.length === 0 && (
          <div style={{ fontSize: 13, color: "#6E6E6E", marginTop: 10 }}>No nights finished yet.</div>
        )}
        {doneNights.map((s, i) => {
          const c = champsOf(s);
          return (
            <div key={s.id} style={{ display: "flex", alignItems: "center", gap: 12, padding: "11px 0",
              borderBottom: "1px solid rgba(110,110,110,.16)" }}>
              <span style={{ fontFamily: "'JetBrains Mono',monospace", fontWeight: 700, fontSize: 12,
                color: "#6E6E6E", width: 28 }}>{i + 1}</span>
              <span style={{ flex: 1, fontSize: 13 }}>{c ? c.join(" & ") : "—"}</span>
              <span style={{ fontFamily: "'JetBrains Mono',monospace", fontWeight: 700, fontSize: 13,
                color: "#C6FF00" }}>{voucher * perTeam}</span>
            </div>
          );
        })}

        {top.length > 0 && <>
          <div style={{ fontFamily: "'JetBrains Mono',monospace", fontWeight: 700, fontSize: 10,
            letterSpacing: ".26em", color: "#9A9A9A", marginTop: 22 }}>TOP EARNERS SO FAR</div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8, marginTop: 10 }}>
            {top.map(([n, v]) => (
              <div key={n} style={{ padding: 10, border: "1px solid rgba(255,255,255,.07)" }}>
                <div style={{ fontWeight: 800, fontSize: 13, whiteSpace: "nowrap",
                  overflow: "hidden", textOverflow: "ellipsis" }}>{n}</div>
                <div style={{ fontFamily: "'JetBrains Mono',monospace", fontWeight: 700, fontSize: 18,
                  color: "#C6FF00", marginTop: 3 }}>{v} OMR</div>
              </div>
            ))}
          </div>
        </>}

        <button onClick={onClose} style={{ width: "100%", marginTop: 20, padding: "14px",
          background: "transparent", border: "1px solid rgba(110,110,110,.4)", color: "#9A9A9A",
          fontFamily: "'JetBrains Mono',monospace", fontWeight: 700, fontSize: 11,
          letterSpacing: ".24em", cursor: "pointer" }}>CLOSE</button>
      </div>
    </div>
  );
}

// ══ VOL.8 · NIGHT RECAP ═══════════════════════════════════════════════════
function RecapSheet({ session, state, leaderboard, meId, onClose, onOpenSession }) {
  if (!session) return null;
  const nameOf = id => (state.players.find(p => p.id === id) || {}).name || "?";
  const teamName = tid => {
    const t = (session.teams || []).find(x => x.id === tid);
    return t ? nameOf(t.p1Id) + " & " + nameOf(t.p2Id) : "—";
  };
  const f = session.bracket?.final;
  const champTid = f && f.winner ? (f.winner === "team1" ? f.team1Id : f.team2Id) : null;
  const idx = (state.sessions || []).findIndex(s => s.id === session.id);

  // Top scorer on the night, from the same per-event engine the receipts use.
  const nightOf = pid => {
    const r = calcPlayerNights(pid, (state.sessions || []).slice(0, idx + 1), () => "");
    const n = r.nights.find(x => x.idx === idx);
    return n ? n.nightTotal : 0;
  };
  const inIt = (state.players || []).filter(p => getPlayerTeam(session, p.id));
  const scored = inIt.map(p => ({ p, pts: nightOf(p.id) })).sort((a, b) => b.pts - a.pts);
  const topScorer = scored[0];

  // Biggest win of the night, by margin.
  const all = (session.groupMatches || []).concat(session.bracket?.qf || [],
    session.bracket?.sf || [], f ? [f] : []).filter(m => m && m.winner && m.score);
  const biggest = all.map(m => {
    const w = m.winner === "team1" ? m.team1Id : m.team2Id;
    const a = Math.abs(m.score.t1 - m.score.t2);
    return { m, w, margin: a };
  }).sort((x, y) => y.margin - x.margin)[0];

  const votes = session.mvpVotes || {};
  const mvpId = Object.keys(votes).sort((a, b) => (votes[b] || 0) - (votes[a] || 0))[0];

  const Row = ({ k, v, sub, c }) => (
    <div style={{ display: "flex", alignItems: "center", gap: 12, padding: "13px 0",
      borderBottom: "1px solid rgba(110,110,110,.16)" }}>
      <span style={{ fontFamily: "'JetBrains Mono',monospace", fontWeight: 700, fontSize: 9,
        letterSpacing: ".2em", color: "#9A9A9A", width: 104 }}>{k}</span>
      <span style={{ flex: 1, minWidth: 0 }}>
        <span style={{ fontWeight: 800, fontSize: 14, display: "block" }}>{v}</span>
        {sub && <span style={{ fontSize: 12, color: "#9A9A9A" }}>{sub}</span>}
      </span>
      {c && <span style={{ fontFamily: "'JetBrains Mono',monospace", fontWeight: 700,
        fontSize: 16, color: "#C6FF00" }}>{c}</span>}
    </div>
  );

  return (
    <div onClick={onClose} style={{ position: "fixed", inset: 0, zIndex: 80,
      background: "rgba(5,5,5,.88)", display: "flex", alignItems: "flex-end" }}>
      <div onClick={e => e.stopPropagation()} style={{ background: "#0A0A0A", width: "100%",
        maxHeight: "90vh", overflowY: "auto", borderTop: "3px solid #C6FF00", padding: 16 }}>
        <div style={{ fontFamily: "'JetBrains Mono',monospace", fontWeight: 700, fontSize: 10,
          letterSpacing: ".26em", color: "#9A9A9A" }}>
          SESSION {idx + 1} &middot; {fmtNightDate(session.date)}{session.doublePoints ? " · 2X NIGHT" : ""}
        </div>
        <div style={{ fontStyle: "italic", fontVariationSettings: "'wdth' 125,'wght' 900",
          fontSize: 44, lineHeight: .9, marginTop: 6 }}>SESSION {idx + 1}<br />RECAP</div>

        {champTid && (
          <div style={{ border: "2px solid #C6FF00", background: "rgba(198,255,0,.06)",
            padding: 16, marginTop: 18, boxShadow: "0 0 30px rgba(198,255,0,.18)" }}>
            <div style={{ fontFamily: "'JetBrains Mono',monospace", fontWeight: 700, fontSize: 9,
              letterSpacing: ".26em", color: "#C6FF00" }}>CHAMPIONS</div>
            <div style={{ fontStyle: "italic", fontVariationSettings: "'wdth' 118,'wght' 900",
              fontSize: 26, marginTop: 6 }}>{teamName(champTid)}</div>
            {f.score && <div style={{ fontSize: 12, color: "#9A9A9A", marginTop: 4 }}>
              Final {f.score.t1}&ndash;{f.score.t2} &middot; {inIt.length} players
            </div>}
          </div>
        )}

        <div style={{ marginTop: 16 }}>
          {mvpId && <Row k="MVP" v={nameOf(mvpId)} sub="player vote" c={votes[mvpId]} />}
          {topScorer && topScorer.pts > 0 &&
            <Row k="TOP SCORER" v={topScorer.p.name} sub="points on the night" c={"+" + topScorer.pts} />}
          {biggest && <Row k="BIGGEST WIN" v={teamName(biggest.w)}
            sub={biggest.m.score.t1 + "–" + biggest.m.score.t2} />}
        </div>

        {meId && getPlayerTeam(session, meId) && (
          <div style={{ border: "1px solid rgba(255,46,136,.4)", padding: 14, marginTop: 16 }}>
            <div style={{ fontFamily: "'JetBrains Mono',monospace", fontWeight: 700, fontSize: 9,
              letterSpacing: ".24em", color: "#FF2E88" }}>YOUR NIGHT</div>
            <div style={{ fontSize: 14, fontWeight: 800, marginTop: 5 }}>
              +{nightOf(meId)} points &middot; open ME for the receipt
            </div>
          </div>
        )}

        {onOpenSession && (
          <button onClick={onOpenSession} style={{ width: "100%", marginTop: 16, padding: "14px",
            background: "transparent", border: "1px solid rgba(198,255,0,.4)", color: "#C6FF00",
            fontFamily: "'JetBrains Mono',monospace", fontWeight: 700, fontSize: 11,
            letterSpacing: ".24em", cursor: "pointer" }}>OPEN THE NIGHT &#9654;</button>
        )}
        <button onClick={onClose} style={{ width: "100%", marginTop: 10, padding: "14px",
          background: "transparent", border: "1px solid rgba(110,110,110,.4)", color: "#9A9A9A",
          fontFamily: "'JetBrains Mono',monospace", fontWeight: 700, fontSize: 11,
          letterSpacing: ".24em", cursor: "pointer" }}>CLOSE</button>
      </div>
    </div>
  );
}
"""

# ── Dashboard splices ─────────────────────────────────────────────────────
DASH_SIG_OLD = "function DashboardView({ state, leaderboard, setTab, setOpenSessionId, isAdmin, meId, onOpenPicker }) {"
DASH_SIG_NEW = """function DashboardView({ state, leaderboard, setTab, setOpenSessionId, isAdmin, meId, onOpenPicker }) {
  const [showPrizes, setShowPrizes] = React.useState(false);
  const [recap, setRecap] = React.useState(null);"""

DASH_ANCHOR_OLD = """      {/* ── WORTH WATCHING ── */}"""
DASH_ANCHOR_NEW = """      {/* ── FINALS COUNTDOWN (Vol.8) ── */}
      <FinalsCountdown state={state} leaderboard={leaderboard} meId={meId} setTab={setTab} />

      {/* ── WORTH WATCHING ── */}"""

DASH_TAIL_OLD = """      {/* ── HOW POINTS ARE EARNED ──"""
DASH_TAIL_NEW = """      {/* ── LAST NIGHT + PRIZE TRACKER (Vol.8) ── */}
      <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:10,marginTop:20}}>
        <button onClick={() => {
            const done = (state.sessions || []).filter(s => s.completed);
            if (done.length) setRecap(done[done.length - 1]);
          }}
          style={{textAlign:"left",padding:14,cursor:"pointer",color:"inherit",
            background:"rgba(14,14,14,.94)",border:"1px solid rgba(198,255,0,.3)"}}>
          <div style={{fontFamily:"'JetBrains Mono',monospace",fontWeight:700,fontSize:8,
            letterSpacing:".2em",color:"#C6FF00"}}>LAST NIGHT</div>
          <div style={{fontStyle:"italic",fontVariationSettings:"'wdth' 118,'wght' 900",
            fontSize:22,marginTop:6}}>RECAP</div>
          <div style={{fontSize:11,color:"#9A9A9A",marginTop:4}}>
            {(state.sessions || []).filter(s => s.completed).length
              ? "champions, MVP, top scorer" : "after the first night"}
          </div>
        </button>
        <button onClick={() => setShowPrizes(true)}
          style={{textAlign:"left",padding:14,cursor:"pointer",color:"inherit",
            background:"rgba(14,14,14,.94)",border:"1px solid rgba(255,46,136,.35)"}}>
          <div style={{fontFamily:"'JetBrains Mono',monospace",fontWeight:700,fontSize:8,
            letterSpacing:".2em",color:"#FF2E88"}}>PRIZE TRACKER</div>
          <div style={{fontStyle:"italic",fontVariationSettings:"'wdth' 118,'wght' 900",
            fontSize:22,marginTop:6}}>{pool} OMR</div>
          <div style={{fontSize:11,color:"#9A9A9A",marginTop:4}}>
            {(state.sessions || []).filter(s => s.completed).length * 28} paid so far
          </div>
        </button>
      </div>

      <PrizeSheet open={showPrizes} state={state} leaderboard={leaderboard}
                  onClose={() => setShowPrizes(false)} />
      <RecapSheet session={recap} state={state} leaderboard={leaderboard} meId={meId}
                  onClose={() => setRecap(null)} />

      {/* ── HOW POINTS ARE EARNED ──"""

# ── App splices: refresh + skeleton ───────────────────────────────────────
APP_STATE_OLD = "  const pollTimer = useRef();"
APP_STATE_NEW = """  const pollTimer = useRef();
  // Vol.8: a manual refresh people can reach, and something to look at while it
  // runs. The poll already keeps the page fresh; this is for the moment someone
  // wants to KNOW it is fresh, which is every time a score goes in.
  const [refreshing, setRefreshing] = useState(false);
  const [lastSync, setLastSync] = useState(null);
  const refreshNow = React.useCallback(async () => {
    setRefreshing(true);
    setSync("syncing");
    try {
      const res = await apiGet("getState");
      if (res?.ok && res.state) {
        setState(res.state);
        try { localStorage.setItem(LOCAL_KEY, JSON.stringify(stateForLocalCache(res.state))); } catch (e) {}
        setSync("idle");
        setLastSync(new Date());
      } else { setSync("offline"); }
    } catch (e) { setSync("offline"); }
    // Held deliberately: a refresh that returns in 80ms looks like nothing
    // happened, and people pull again.
    setTimeout(() => setRefreshing(false), 650);
  }, []);

  // Installed here, above the loading guard, because hooks must run in the same
  // order on every render. Below the guard it ran only once state had arrived,
  // and React counted more hooks on the second render than the first --
  // "Rendered more hooks than during the previous render", a blank page.
  //
  // Blocked while a sheet or a session is open: pulling down inside a
  // scrollable sheet should scroll it, not refresh the page behind it.
  const pullBlocked = React.useCallback(
    () => !!(openSessionId || openPlayerId || showMe || showLogin),
    [openSessionId, openPlayerId, showMe, showLogin]);
  const pullY = usePullToRefresh(refreshNow, pullBlocked);"""

APP_GUARD_OLD = "  if (!state) return null;"
APP_GUARD_NEW = """  // First paint. A blank screen for a second reads as broken; the skeleton reads
  // as loading, and it is the shape of what is about to arrive.
  if (!state) return (
    <div className="min-h-screen">
      <main className="max-w-3xl mx-auto px-4 py-4"><Skeleton /></main>
    </div>
  );"""

APP_MAIN_OLD = """      <main className="max-w-3xl mx-auto px-4 py-4 pb-24">"""
APP_MAIN_NEW = """      <PullStrip pull={pullY} />
      <main className="max-w-3xl mx-auto px-4 py-4 pb-24">
        {refreshing && <Skeleton />}
        {!refreshing && <>"""

APP_MAIN_END_OLD = """        {tab === "settings" && isAdmin && <SettingsView state={state} update={update} setTab={setTab} logout={logout} />}
      </main>"""
APP_MAIN_END_NEW = """        {tab === "settings" && isAdmin && <SettingsView state={state} update={update} setTab={setTab} logout={logout} />}
        </>}
      </main>"""

# The hook needs the sheet state, so it is installed after those are declared.


# MVP voting: Vol.7 showed the tab to scorers only. The handoff wants players to
# vote, one per device, which is what MvpVoteTab already enforces.
MVP_OLD = """                count:session.mvpVotingOpen && votes ? votes : null, go:() => setTab("mvp"), show:canScore },"""
MVP_NEW = """                count:session.mvpVotingOpen && votes ? votes : null, go:() => setTab("mvp"),
                // Vol.7 showed this to scorers only, so the "player vote" was
                // whoever was holding the scoring phone. The tab is open to
                // everyone once voting is; MvpVoteTab already enforces one
                // vote per device.
                show:canScore || !!session.mvpVotingOpen },"""

SHIMMER = """
@keyframes bo-shimmer { from { transform: translateX(-100%); } to { transform: translateX(100%); } }
"""


# ══════════════════════════════════════════════════════════════════════════
# 5 · SCORE SHEET — the court-side screen
# ══════════════════════════════════════════════════════════════════════════
#
# Replaces MatchEditorModal wholesale. The handoff's spec: a 4x2 pad of 0-7 with
# 64px buttons, the winning panel tinted, how-the-loss-went, a points preview and
# a lock button that says why it is disabled.
#
# ONE DELIBERATE DEPARTURE. The handoff draws HOW THE LOSS WENT as three buttons
# the scorer picks. In this app the loss type is DERIVED from the score
# (scoreToResult: 0-1 blowout, 5 tiebreak, else close), and the handoff is also
# explicit that the scoring rules must not change. Buttons that let a scorer
# contradict the score would be a scoring change, so the three are shown as a
# read-out with the derived one lit: same information, same place on screen, no
# way to enter a result that disagrees with itself.
#
# The pad also goes to 7 rather than 6. Group matches could not record a 7-5 at
# all before, which is a legal score and the one that makes a tiebreak loss.
SCORESHEET = r"""function MatchEditorModal({ session, state, group, match, onClose, onSave, onDelete }) {
  const teams = (session.teams || []).filter(t => t.group === group);
  const [t1, setT1] = useState(match?.team1Id || "");
  const [t2, setT2] = useState(match?.team2Id || "");
  const initS1 = match?.score?.t1 ?? (match?.winner ? (match.winner === "team1" ? 6 : 3) : null);
  const initS2 = match?.score?.t2 ?? (match?.winner ? (match.winner === "team2" ? 6 : 3) : null);
  const [s1, setS1] = useState(initS1);
  const [s2, setS2] = useState(initS2);

  const first = id => (state.players.find(p => p.id === id)?.name || "?").split(" ")[0];
  const lbl = t => t ? `${first(t.p1Id)} & ${first(t.p2Id)}` : "?";
  const inits = t => t ? (first(t.p1Id)[0] || "?") + (first(t.p2Id)[0] || "?") : "??";

  const playedPairs = new Set(
    (session.groupMatches || [])
      .filter(m => m.winner && (!match || m.id !== match.id))
      .map(m => [m.team1Id, m.team2Id].sort().join("|"))
  );
  const hasPlayed = (id1, id2) => id1 && id2 && playedPairs.has([id1, id2].sort().join("|"));

  const derived = (s1 !== null && s2 !== null && s1 !== s2) ? scoreToResult(s1, s2) : null;
  const matchNo = (session.groupMatches || []).filter(m => {
    const t = (session.teams || []).find(x => x.id === m.team1Id);
    return t && t.group === group;
  }).findIndex(m => match && m.id === match.id) + 1;

  const why = s1 === null || s2 === null ? "PICK BOTH SCORES"
            : s1 === s2 ? "SCORES CAN'T BE LEVEL"
            : !t1 || !t2 ? "PICK BOTH TEAMS" : null;

  const Panel = ({ tid, val, setVal, side }) => {
    const t = teams.find(x => x.id === tid);
    const won = derived?.winner === side;
    const lost = derived && !won;
    return (
      <div style={{ padding: 12, marginBottom: 10,
        background: won ? "rgba(198,255,0,.08)" : "rgba(14,14,14,.94)",
        border: "1px solid " + (won ? "rgba(198,255,0,.5)" : "rgba(255,255,255,.07)") }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <div style={{ width: 38, height: 38, flexShrink: 0, display: "flex", alignItems: "center",
            justifyContent: "center", background: won ? "#C6FF00" : "#1A1A1A",
            color: won ? "#050505" : "#9A9A9A", fontFamily: "'JetBrains Mono',monospace",
            fontWeight: 700, fontSize: 14 }}>{inits(t)}</div>
          <div style={{ flex: 1, minWidth: 0, fontWeight: 800, fontSize: 15,
            color: lost ? "#9A9A9A" : "#F2F2F2", whiteSpace: "nowrap", overflow: "hidden",
            textOverflow: "ellipsis" }}>{lbl(t)}</div>
          <div style={{ fontFamily: "'JetBrains Mono',monospace", fontWeight: 700, fontSize: 30,
            lineHeight: 1, color: won ? "#C6FF00" : lost ? "#9A9A9A" : "#F2F2F2" }}>
            {val ?? "—"}
          </div>
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: 6, marginTop: 10 }}>
          {[0,1,2,3,4,5,6,7].map(n => (
            <button key={n} type="button" onClick={() => setVal(n)}
              style={{ height: 64, cursor: "pointer", border: "1px solid",
                fontFamily: "'JetBrains Mono',monospace", fontWeight: 700, fontSize: 26,
                transition: "transform 170ms cubic-bezier(.2,.7,.3,1)",
                ...(val === n
                  ? { background: "#C6FF00", color: "#050505", borderColor: "#C6FF00" }
                  : { background: "#111", color: "#CFCFCF", borderColor: "rgba(110,110,110,.3)" }) }}>
              {n}
            </button>
          ))}
        </div>
      </div>
    );
  };

  return <Modal open={true} onClose={onClose} title={match ? "EDIT MATCH" : `GROUP ${group} MATCH`}>
    <div>
      <div style={{ fontFamily: "'JetBrains Mono',monospace", fontWeight: 700, fontSize: 10,
        letterSpacing: ".26em", color: "#9A9A9A", marginBottom: 12 }}>
        GROUP {group}{matchNo > 0 ? " · MATCH " + matchNo : ""}
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8, marginBottom: 12 }}>
        {[[t1, setT1, t2], [t2, setT2, t1]].map(([val, set, other], i) => (
          <select key={i} value={val} onChange={e => set(e.target.value)}
            style={{ width: "100%", padding: "11px 10px", background: "#111", color: "#F2F2F2",
              border: "1px solid rgba(110,110,110,.3)", fontSize: 13, outline: "none" }}>
            <option value="">Team {i + 1}</option>
            {teams.filter(t => t.id !== other && !hasPlayed(t.id, other)).map(t =>
              <option key={t.id} value={t.id}>{lbl(t)}</option>)}
          </select>
        ))}
      </div>

      {t1 && t2 && <>
        <Panel tid={t1} val={s1} setVal={setS1} side="team1" />
        <Panel tid={t2} val={s2} setVal={setS2} side="team2" />

        <LossReadout derived={derived} />
        <PointsPreview derived={derived} />
      </>}

      <div style={{ display: "flex", gap: 8, marginTop: 16 }}>
        {onDelete && <Btn variant="danger" onClick={() => { onDelete(); onClose(); }}><I.trash size={14} /></Btn>}
        <Btn variant="ghost" onClick={onClose}>Cancel</Btn>
        <button type="button" disabled={!!why || saving}
          onClick={() => {
            if (why) return;
            setSaving(true);
            celebrate(lbl(teams.find(t => t.id === (derived.winner === "team1" ? t1 : t2))) + " TAKE IT");
            onSave({ team1Id: t1, team2Id: t2, ...derived, resultAt: Date.now() });
            onClose();
          }}
          style={{ flex: 1, padding: "22px 16px", cursor: why ? "default" : "pointer",
            fontFamily: "'JetBrains Mono',monospace", fontWeight: 700, fontSize: 12,
            letterSpacing: ".2em", border: "none",
            ...(why
              ? { background: "#1A1A1A", color: "#6E6E6E" }
              : { background: "#C6FF00", color: "#050505",
                  boxShadow: "0 0 30px rgba(198,255,0,.32)" }) }}>
          {why || "LOCK RESULT ▶"}
        </button>
      </div>
    </div>
  </Modal>;
}"""

# The celebration the handoff asks for on a locked result: two expanding rings
# and a word. Kept as a DOM node rather than React state so it can be fired from
# anywhere a result is saved, including the knockout editor.
CELEBRATE = r"""

// ══ VOL.8 · CELEBRATION ═══════════════════════════════════════════════════
// Fired when a result is locked. Deliberately short (1.6s) and non-blocking:
// on a busy night the scorer is already looking at the next match.
function celebrate(word) {
  try {
    if (window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    const host = document.createElement("div");
    host.style.cssText = "position:fixed;inset:0;z-index:200;pointer-events:none;" +
      "display:flex;align-items:center;justify-content:center";
    host.innerHTML =
      '<div class="bo-ring"></div><div class="bo-ring" style="animation-delay:.18s"></div>' +
      '<div class="bo-pop"></div>';
    host.querySelector(".bo-pop").textContent = word || "";
    document.body.appendChild(host);
    setTimeout(() => host.remove(), 1700);
  } catch (e) {}
}
"""

CELEBRATE_CSS = """
/* ── Result-locked celebration ── */
.bo-ring{position:absolute;width:160px;height:160px;border:3px solid #C6FF00;border-radius:50%;
  opacity:0;animation:bo-ring 1.6s cubic-bezier(.2,.7,.3,1) forwards}
@keyframes bo-ring{0%{transform:scale(.3);opacity:.8}100%{transform:scale(4.2);opacity:0}}
.bo-pop{position:relative;padding:18px 26px;background:#C6FF00;color:#050505;
  font-family:'Archivo',sans-serif;font-style:italic;
  font-variation-settings:'wdth' 118,'wght' 900;font-size:30px;line-height:1;
  animation:bo-pop 1.6s cubic-bezier(.34,1.56,.64,1) forwards;text-align:center}
@keyframes bo-pop{0%{transform:scale(.7);opacity:0}18%{transform:scale(1);opacity:1}
  72%{transform:scale(1);opacity:1}100%{transform:scale(.96);opacity:0}}
@media (prefers-reduced-motion:reduce){.bo-ring,.bo-pop{animation:none;display:none}}
"""

SHARED_SCORE = r"""

// ══ VOL.8 · SCORE PANEL ═══════════════════════════════════════════════════
// One team's side of a score sheet: initials, name, big score, and a 4-wide pad
// of 64px buttons. Shared by the group editor and the knockout editor, because
// the alternative is two court-side controls that drift apart.
function ScorePanel({ label, initials, val, setVal, won, lost, max = 7 }) {
  return (
    <div style={{ padding: 12, marginBottom: 10,
      background: won ? "rgba(198,255,0,.08)" : "rgba(14,14,14,.94)",
      border: "1px solid " + (won ? "rgba(198,255,0,.5)" : "rgba(255,255,255,.07)") }}>
      <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
        <div style={{ width: 38, height: 38, flexShrink: 0, display: "flex", alignItems: "center",
          justifyContent: "center", background: won ? "#C6FF00" : "#1A1A1A",
          color: won ? "#050505" : "#9A9A9A", fontFamily: "'JetBrains Mono',monospace",
          fontWeight: 700, fontSize: 14 }}>{initials}</div>
        <div style={{ flex: 1, minWidth: 0, fontWeight: 800, fontSize: 15,
          color: lost ? "#9A9A9A" : "#F2F2F2", whiteSpace: "nowrap", overflow: "hidden",
          textOverflow: "ellipsis" }}>{label}</div>
        <div style={{ fontFamily: "'JetBrains Mono',monospace", fontWeight: 700, fontSize: 30,
          lineHeight: 1, color: won ? "#C6FF00" : lost ? "#9A9A9A" : "#F2F2F2" }}>
          {val ?? "—"}
        </div>
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: 6, marginTop: 10 }}>
        {Array.from({ length: max + 1 }, (_, n) => (
          <button key={n} type="button" onClick={() => setVal(n)}
            style={{ height: 64, cursor: "pointer", border: "1px solid",
              fontFamily: "'JetBrains Mono',monospace", fontWeight: 700, fontSize: 26,
              transition: "transform 170ms cubic-bezier(.2,.7,.3,1)",
              ...(val === n
                ? { background: "#C6FF00", color: "#050505", borderColor: "#C6FF00" }
                : { background: "#111", color: "#CFCFCF", borderColor: "rgba(110,110,110,.3)" }) }}>
            {n}
          </button>
        ))}
      </div>
    </div>
  );
}

// How the loss went: a READ-OUT, not a choice. The type is derived from the
// score, and the scoring rules are not ours to change.
function LossReadout({ derived }) {
  return (
    <>
      <div style={{ fontFamily: "'JetBrains Mono',monospace", fontWeight: 700, fontSize: 9,
        letterSpacing: ".24em", color: "#9A9A9A", margin: "14px 0 8px" }}>HOW THE LOSS WENT</div>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(3,1fr)", gap: 6 }}>
        {LOSS_TYPES.map(lt => {
          const on = derived?.lossType === lt.id;
          return (
            <div key={lt.id} style={{ minHeight: 72, padding: "10px 8px", textAlign: "center",
              display: "flex", flexDirection: "column", justifyContent: "center",
              background: on ? "rgba(255,46,136,.1)" : "transparent",
              border: "1px solid " + (on ? "rgba(255,46,136,.5)" : "rgba(110,110,110,.2)") }}>
              <div style={{ fontSize: 12, fontWeight: 800,
                color: on ? "#F2F2F2" : "#6E6E6E" }}>{lt.label.replace(" Loss", "")}</div>
              <div style={{ fontFamily: "'JetBrains Mono',monospace", fontWeight: 700, fontSize: 18,
                marginTop: 4, color: on ? "#FF2E88" : "#6E6E6E" }}>+{lt.pts}</div>
            </div>
          );
        })}
      </div>
      <div style={{ fontSize: 11, color: "#6E6E6E", marginTop: 8, lineHeight: 1.4 }}>
        Set by the score, not picked: 0 or 1 games is a blowout, 5 is a tiebreak,
        anything else is close.
      </div>
    </>
  );
}

function PointsPreview({ derived, winPts = 3 }) {
  if (!derived) return null;
  const lp = LOSS_TYPES.find(l => l.id === derived.lossType)?.pts ?? 0;
  return (
    <div style={{ display: "flex", gap: 8, marginTop: 14 }}>
      <div style={{ flex: 1, padding: 12, background: "rgba(198,255,0,.07)",
        border: "1px solid rgba(198,255,0,.3)" }}>
        <div style={{ fontFamily: "'JetBrains Mono',monospace", fontWeight: 700, fontSize: 9,
          letterSpacing: ".2em", color: "#9A9A9A" }}>WINNER</div>
        <div style={{ fontFamily: "'JetBrains Mono',monospace", fontWeight: 700, fontSize: 24,
          color: "#C6FF00", marginTop: 3 }}>+{winPts}</div>
      </div>
      <div style={{ flex: 1, padding: 12, border: "1px solid rgba(110,110,110,.25)" }}>
        <div style={{ fontFamily: "'JetBrains Mono',monospace", fontWeight: 700, fontSize: 9,
          letterSpacing: ".2em", color: "#9A9A9A" }}>LOSER</div>
        <div style={{ fontFamily: "'JetBrains Mono',monospace", fontWeight: 700, fontSize: 24,
          color: lp ? "#F2F2F2" : "#6E6E6E", marginTop: 3 }}>+{lp}</div>
      </div>
    </div>
  );
}

function LockButton({ why, onLock }) {
  return (
    <button type="button" disabled={!!why} onClick={() => { if (!why) onLock(); }}
      style={{ flex: 1, padding: "22px 16px", cursor: why ? "default" : "pointer",
        fontFamily: "'JetBrains Mono',monospace", fontWeight: 700, fontSize: 12,
        letterSpacing: ".2em", border: "none",
        ...(why ? { background: "#1A1A1A", color: "#6E6E6E" }
                : { background: "#C6FF00", color: "#050505",
                    boxShadow: "0 0 30px rgba(198,255,0,.32)" }) }}>
      {why || "LOCK RESULT ▶"}
    </button>
  );
}
"""


# ── Knockout editor: same panel, same read-out, same lock button ──────────
# It had its own pad, one row of 8-10 cells across a 430px phone (~40px each).
# Two court-side controls that look different is how one of them gets fixed and
# the other does not.
KO_SCORE_OLD = '''        {!confirmed ? (
          <div>
            <label className="text-xs text-stone-400 uppercase tracking-wider font-semibold mb-2 block">Score — tap each team's games{match.round === "final" ? " (up to 9)" : ""}</label>
            <div className="space-y-2.5">
              {[[t1, s1, setS1, "team1"], [t2, s2, setS2, "team2"]].map(([tid, sval, setS, side]) => (
                <div key={side}>
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm font-semibold truncate pr-2" style={{ color: derived?.winner === side ? "#C6FF00" : derived && derived.winner ? "#78716c" : "#e7e5e4" }}>{lbl(tid)}</span>
                    <span className="font-mono text-2xl font-bold w-7 text-center shrink-0" style={{ color: derived?.winner === side ? "#C6FF00" : "#e7e5e4" }}>{sval ?? "—"}</span>
                  </div>
                  <div className="grid gap-1" style={{ gridTemplateColumns: `repeat(${maxScore + 1}, minmax(0, 1fr))` }}>
                    {Array.from({ length: maxScore + 1 }, (_, n) => (
                      <button key={n} type="button" onClick={() => { setS(n); setConfirmed(false); }}
                        className="h-10 rounded-lg font-bold text-sm active:scale-90 transition-transform"
                        style={sval === n
                          ? { background: "#C6FF00", color: "#fff", border: "1px solid rgba(242,242,242,.14)", boxShadow: "0 2px 0 rgba(0,0,0,.4)" }
                          : { background: "#292524", color: "#d6d3d1", border: "1px solid #2A2A2A" }}>{n}</button>
                    ))}
                  </div>
                </div>
              ))}
            </div>
            <div className="mt-2 text-center text-xs">
              {derived ? <span className="text-emerald-400">{lbl(derived.winner === "team1" ? t1 : t2)} wins · <span className="text-stone-500">{LOSS_TYPES.find(lt => lt.id === derived.lossType)?.label}</span></span>
                : s1 !== null && s1 === s2 ? <span className="text-cyan-300">Tied — adjust score</span>
                : <span className="text-stone-600">Enter score above</span>}
            </div>
          </div>
        ) : (
          <div className="rounded-xl p-4 text-center space-y-1" style={{ background: "rgba(198,255,0,.08)", border: "1px solid rgba(198,255,0,.25)" }}>
            <div className="font-mono text-3xl font-bold text-stone-100">{s1} — {s2}</div>
            <div className="text-emerald-400 text-sm font-semibold">{lbl(derived.winner === "team1" ? t1 : t2)} wins</div>
            <div className="text-stone-500 text-xs">{LOSS_TYPES.find(lt => lt.id === derived.lossType)?.label}</div>
          </div>
        )}
      </>}'''
KO_SCORE_NEW = '''        {(() => {
          const ini = tid => { const t = teams.find(x => x.id === tid); if (!t) return "??";
            const f = id => (state.players.find(p => p.id === id)?.name || "?")[0];
            return (f(t.p1Id) || "?") + (f(t.p2Id) || "?"); };
          return <>
            <ScorePanel label={lbl(t1)} initials={ini(t1)} val={s1}
              setVal={n => { setS1(n); setConfirmed(false); }}
              won={derived?.winner === "team1"} lost={derived && derived.winner !== "team1"} max={maxScore} />
            <ScorePanel label={lbl(t2)} initials={ini(t2)} val={s2}
              setVal={n => { setS2(n); setConfirmed(false); }}
              won={derived?.winner === "team2"} lost={derived && derived.winner !== "team2"} max={maxScore} />
            <LossReadout derived={derived} />
            {/* The knockout ladder pays by round, so the preview says which. */}
            <PointsPreview derived={derived}
              winPts={match.round === "final" ? 8 : match.round === "sf" ? 3 : 2} />
          </>;
        })()}
      </>}'''

KO_BTN_OLD = '''        {!confirmed
          ? <Btn onClick={() => canConfirm && setConfirmed(true)} disabled={!canConfirm}>Confirm ▶</Btn>
          : <Btn onClick={() => { onSave({ team1Id: t1 || null, team2Id: t2 || null, ...derived, resultAt: Date.now() }); onClose(); }}>Save Result ✓</Btn>
        }'''
KO_BTN_NEW = '''        <LockButton
          why={s1 === null || s2 === null ? "PICK BOTH SCORES"
             : s1 === s2 ? "SCORES CAN'T BE LEVEL"
             : !canConfirm ? "PICK BOTH TEAMS" : null}
          onLock={() => {
            celebrate(lbl(derived.winner === "team1" ? t1 : t2) + " GO THROUGH");
            onSave({ team1Id: t1 || null, team2Id: t2 || null, ...derived, resultAt: Date.now() });
            onClose();
          }} />'''


# ── Header: the handoff's lockup, and a sync pill anyone can tap ──────────
HEADER_OLD = '''          <div className="flex items-center gap-3 min-w-0">
            <button onClick={secretTap} className="shrink-0" aria-label="Blackout Series" style={{lineHeight:0}}>
              <img src={UP_LOGO_FULL} style={{height:64,width:"auto",display:"block",margin:"-8px 0",filter:"drop-shadow(0 0 10px rgba(198,255,0,.5)) drop-shadow(0 0 14px rgba(198,255,0,.4))"}} alt="Blackout Series" />
            </button>
          </div>'''
HEADER_NEW = '''          <div className="flex items-center gap-3 min-w-0">
            <button onClick={secretTap} className="shrink-0" aria-label="Urban Playground" style={{lineHeight:0}}>
              <img src={UP_LOGO_FULL} style={{height:44,width:"auto",display:"block",margin:"-4px 0",filter:"drop-shadow(0 0 10px rgba(198,255,0,.4))"}} alt="Urban Playground" />
            </button>
            {/* The chrome carried no Blackout branding at all -- a player opened
                the app and the only mark on screen was the club's. */}
            <span style={{width:1,height:28,background:"rgba(255,255,255,.14)",flexShrink:0}} />
            <span style={{width:30,height:30,flexShrink:0,position:"relative",background:"#C6FF00"}}>
              <span style={{position:"absolute",left:0,right:0,top:14,height:1,background:"#050505"}} />
              <span style={{position:"absolute",left:0,right:0,top:18,height:2,background:"#050505"}} />
              <span style={{position:"absolute",left:0,right:0,top:22,height:3,background:"#050505"}} />
              <span style={{position:"absolute",left:0,right:0,top:27,height:3,background:"#050505"}} />
              <span style={{position:"absolute",right:4,top:4,width:4,height:4,background:"#FF2E88"}} />
            </span>
            <div style={{minWidth:0}}>
              <div style={{fontStyle:"italic",fontVariationSettings:"'wdth' 118,'wght' 900",
                fontSize:20,lineHeight:1,whiteSpace:"nowrap"}}>BLACKOUT SERIES</div>
              <div style={{fontFamily:"'JetBrains Mono',monospace",fontWeight:700,fontSize:8,
                letterSpacing:".2em",color:"#6E6E6E",marginTop:3,whiteSpace:"nowrap"}}>
                URBAN SOCIAL SERIES &middot; VOL.8</div>
            </div>
          </div>'''

# The sync pill was gated behind canScore, so a player had no way to ask for
# fresh data except pulling down -- and no way to see whether it was fresh.
SYNCPILL_OLD = '''            {canScore && <SyncIndicator status={sync} errMsg={syncErr} />}'''
SYNCPILL_NEW = '''            {canScore
              ? <SyncIndicator status={sync} errMsg={syncErr} />
              : <button onClick={refreshNow} aria-label="Refresh"
                  style={{display:"flex",alignItems:"center",gap:6,padding:"5px 9px",cursor:"pointer",
                    background:"transparent",border:"1px solid rgba(110,110,110,.3)"}}>
                  <span style={{width:6,height:6,borderRadius:"50%",
                    background: refreshing ? "#FF2E88" : "#C6FF00"}} />
                  <span style={{fontFamily:"'JetBrains Mono',monospace",fontWeight:700,fontSize:8,
                    letterSpacing:".18em",color:"#9A9A9A"}}>
                    {refreshing ? "SYNCING" : "SYNCED"}</span>
                </button>}'''

# ── Sessions list: a finished row should open its recap ───────────────────
SESSROW_OLD = '''               onClick={() => setOpenSessionId(s.id)}'''
SESSROW_NEW = '''               onClick={() => s.completed ? setRecapSession(s) : setOpenSessionId(s.id)}'''

SESSVIEW_OLD = '''function SessionsView({ state, update, setOpenSessionId, isAdmin, leaderboard, setTab }) {'''
SESSVIEW_NEW = '''function SessionsView({ state, update, setOpenSessionId, isAdmin, leaderboard, setTab, meId }) {
  // A finished night's row used to open the live session screen, which is the
  // scorer's view of a night nobody is scoring any more. It opens the recap
  // instead; the session screen is still one tap away from inside it.
  const [recapSession, setRecapSession] = React.useState(null);'''

SESSVIEW_TAIL_OLD = '''      {show && <CreateSessionModal'''
SESSVIEW_TAIL_NEW = '''      <RecapSheet session={recapSession} state={state} leaderboard={leaderboard} meId={meId}
        onClose={() => setRecapSession(null)}
        onOpenSession={() => { const s = recapSession; setRecapSession(null); setOpenSessionId(s.id); }} />
      {show && <CreateSessionModal'''

SESSVIEW_PROP_OLD = '''{tab === "sessions" && <SessionsView state={state} update={update} setOpenSessionId={setOpenSessionId} isAdmin={isAdmin} leaderboard={leaderboard} setTab={setTab} />}'''
SESSVIEW_PROP_NEW = '''{tab === "sessions" && <SessionsView state={state} update={update} setOpenSessionId={setOpenSessionId} isAdmin={isAdmin} leaderboard={leaderboard} setTab={setTab} meId={meId} />}'''


# ══════════════════════════════════════════════════════════════════════════
# 6 · PLAYER CARD EXTRAS, RICHER ROSTER, FOUR SPOTLIGHT AXES
# ══════════════════════════════════════════════════════════════════════════
EXTRAS = r"""

// ══ VOL.8 · PLAYER CARD EXTRAS ════════════════════════════════════════════
// The card showed a points breakdown and stopped there. The handoff asks for the
// three things that make it worth opening someone else's: where their points
// came from NIGHT BY NIGHT (each tapping through to that night's receipt),
// their badges, and the head-to-head against you.
function PlayerExtras({ player, state, leaderboard, meId }) {
  const [receipt, setReceipt] = React.useState(null);
  const players = state.players || [];
  const sessions = state.sessions || [];
  const nameOf = React.useCallback((s, teamId, pidDirect) => {
    if (pidDirect) return (players.find(p => p.id === pidDirect) || {}).name || "?";
    const t = (s.teams || []).find(x => x.id === teamId);
    if (!t) return "?";
    const n = id => ((players.find(p => p.id === id) || {}).name || "?").split(" ")[0];
    return n(t.p1Id) + " & " + n(t.p2Id);
  }, [players]);

  const data = calcPlayerNights(player.id, sessions, nameOf);
  const ranks = React.useMemo(() => rankByNight(players, sessions), [players, sessions]);
  const best = Math.max(1, ...data.nights.map(n => n.nightTotal));

  // Head to head: every decided match where the two were on opposite teams.
  const h2h = React.useMemo(() => {
    if (!meId || meId === player.id) return null;
    let mine = 0, theirs = 0, last = null;
    sessions.forEach((s, idx) => {
      const a = getPlayerTeam(s, meId), b = getPlayerTeam(s, player.id);
      if (!a || !b || a.id === b.id) return;
      const all = (s.groupMatches || []).concat(s.bracket?.qf || [], s.bracket?.sf || [],
                                                s.bracket?.final ? [s.bracket.final] : []);
      all.forEach(m => {
        if (!m || !m.winner) return;
        const ids = [m.team1Id, m.team2Id];
        if (!ids.includes(a.id) || !ids.includes(b.id)) return;
        const iWon = teamWon(m, a.id);
        if (iWon) mine++; else theirs++;
        last = { idx, iWon, score: m.score, date: s.date };
      });
    });
    return mine + theirs ? { mine, theirs, last } : null;
  }, [sessions, meId, player.id]);

  if (data.nights.length === 0 && !h2h) return null;

  return (
    <div style={{ marginTop: 20 }}>
      {data.nights.length > 0 && <>
        <div style={{ fontFamily: "'JetBrains Mono',monospace", fontWeight: 700, fontSize: 9,
          letterSpacing: ".26em", color: "#9A9A9A" }}>WHERE THE POINTS CAME FROM</div>
        <StackedBar seg={data.seg} total={data.total} />
        <SegLegend seg={data.seg} />

        <div style={{ display: "grid", gridTemplateColumns: "repeat(5,1fr)", gap: 6, marginTop: 16 }}>
          {data.nights.slice(-5).map(n => (
            <button key={n.id} onClick={() => setReceipt(n)}
              style={{ padding: "10px 4px", cursor: "pointer", color: "inherit", textAlign: "center",
                background: "rgba(14,14,14,.94)", border: "1px solid rgba(198,255,0,.25)" }}>
              <div style={{ fontFamily: "'JetBrains Mono',monospace", fontWeight: 700, fontSize: 9,
                color: "#6E6E6E" }}>S{n.no}</div>
              <div style={{ fontFamily: "'JetBrains Mono',monospace", fontWeight: 700, fontSize: 17,
                color: "#C6FF00", marginTop: 3 }}>+{n.nightTotal}</div>
              <div style={{ height: 3, background: "rgba(110,110,110,.25)", marginTop: 6 }}>
                <div style={{ height: "100%", background: "#C6FF00",
                  width: Math.round(n.nightTotal / best * 100) + "%" }} />
              </div>
            </button>
          ))}
        </div>
      </>}

      {h2h && (
        <div style={{ border: "1px solid rgba(255,46,136,.4)", padding: 14, marginTop: 20 }}>
          <div style={{ fontFamily: "'JetBrains Mono',monospace", fontWeight: 700, fontSize: 9,
            letterSpacing: ".24em", color: "#FF2E88" }}>HEAD TO HEAD &middot; YOU</div>
          <div style={{ fontStyle: "italic", fontVariationSettings: "'wdth' 118,'wght' 900",
            fontSize: 26, marginTop: 6 }}>
            YOU {h2h.mine} &ndash; {h2h.theirs} {(player.name || "").split(" ")[0].toUpperCase()}
          </div>
          <div style={{ fontSize: 12, color: "#9A9A9A", marginTop: 4 }}>
            {h2h.mine + h2h.theirs} meeting{h2h.mine + h2h.theirs === 1 ? "" : "s"}
            {h2h.last && h2h.last.score
              ? ` · last: ${h2h.last.iWon ? "you won" : "they won"} `
                + `${h2h.last.score.t1}–${h2h.last.score.t2}`
              : ""}
          </div>
        </div>
      )}

      <ReceiptSheet night={receipt} player={player}
        rankAfter={receipt ? (ranks[receipt.idx] || {})[player.id] : null}
        onClose={() => setReceipt(null)} />
    </div>
  );
}
"""

# PlayerDetail: hang the extras off the end of its body, before the closing div.
PLAYEREXTRA_OLD = '''function PlayerDetail({ playerId, state, leaderboard, canScore, sync, syncErr, update, onClose }) {'''
PLAYEREXTRA_NEW = '''function PlayerDetail({ playerId, state, leaderboard, canScore, sync, syncErr, update, onClose, meId }) {'''

PLAYERPROP_OLD = '''<PlayerDetail playerId={openPlayerId}'''
PLAYERPROP_NEW = '''<PlayerDetail meId={meId} playerId={openPlayerId}'''

PLAYERTAIL_OLD = '''      <Btn variant="secondary" className="w-full" onClick={() => {
        const txt = generatePlayerCard(entry, state);
        navigator.clipboard?.writeText(txt);
        alert("Player card copied — paste it in WhatsApp.");
      }}>Copy my player card</Btn>'''
PLAYERTAIL_NEW = '''      <PlayerExtras player={entry.player} state={state} leaderboard={leaderboard} meId={meId} />
      <Btn variant="secondary" className="w-full" onClick={() => {
        const txt = generatePlayerCard(entry, state);
        navigator.clipboard?.writeText(txt);
        alert("Player card copied — paste it in WhatsApp.");
      }}>Copy my player card</Btn>'''


# ── Worth watching: four axes, de-duplicated ─────────────────────────────
# Vol.7 showed two, and both could land on the same person, which wastes half
# the row. The handoff asks for four chosen from outside the top three, each
# player used once.
SPOT_OLD = '''      {/* ── WORTH WATCHING ── */}
      {(climber || bestRate) && <>
        <div className="sg-kicker" style={{marginTop:20}}>Worth watching</div>
        <div style={{display:"grid",gridTemplateColumns:"repeat(2,minmax(0,1fr))",gap:10,marginTop:10}}>'''
SPOT_NEW = '''      {/* ── WORTH WATCHING (Vol.8: four axes, de-duplicated) ── */}
      {spotlights.length > 0 && <>
        <div className="sg-kicker" style={{marginTop:20}}>Worth watching</div>
        <div style={{display:"grid",gridTemplateColumns:"repeat(2,minmax(0,1fr))",gap:10,marginTop:10}}>
          {spotlights.map(sp => (
            <div key={sp.key} onClick={() => setTab("leaderboard")} className="sg-card"
                 style={{cursor:"pointer",padding:14,
                   backgroundImage:`linear-gradient(180deg,${sp.colour},rgba(110,110,110,.05))`,
                   backgroundSize:"3px 100%",backgroundRepeat:"no-repeat"}}>
              <div style={{fontFamily:"'Archivo',sans-serif",fontWeight:800,fontSize:8,
                   letterSpacing:".2em",color:sp.colour}}>{sp.label}</div>
              <div style={{fontFamily:"'Archivo',sans-serif",fontStyle:"italic",
                   fontVariationSettings:"'wdth' 118,'wght' 900",fontSize:34,lineHeight:1,
                   color:sp.colour,marginTop:7}}>{sp.value}</div>
              <div style={{fontFamily:"'Archivo',sans-serif",fontWeight:800,fontSize:14,
                   color:"#F2F2F2",marginTop:8,whiteSpace:"nowrap",overflow:"hidden",
                   textOverflow:"ellipsis"}}>{sp.name}</div>
              <div style={{fontSize:12,lineHeight:1.4,color:"#CFCFCF",marginTop:5}}>{sp.note}</div>
            </div>
          ))}
        </div>
      </>}'''

# Computed right after climber/bestRate so both can be reused rather than
# recalculated. Anchored on the line that closes bestRate.
SPOT_CALC_OLD = '''    return pool2.sort((a, b) => b.en.winRate - a.en.winRate || b.e.totalPts - a.e.totalPts)[0];
  })();'''
SPOT_CALC_NEW = '''    return pool2.sort((a, b) => b.en.winRate - a.en.winRate || b.e.totalPts - a.e.totalPts)[0];
  })();

  // Vol.8: four spotlight axes instead of two, each player used once. Two tiles
  // that land on the same person waste half the row, which is what happened
  // whenever the biggest climber also had the best win rate.
  const spotlights = (() => {
    const out = [], used = new Set(podium.map(e => e.player.id));
    const push = (id, sp) => { if (id && !used.has(id)) { used.add(id); out.push(sp); } };
    const nightsDone = sessions.filter(s => s.completed).length;

    if (climber) push(climber.e.player.id, { key: "climb", colour: "#C6FF00",
      label: "BIGGEST CLIMBER", value: "\u25b2" + climber.n, name: climber.e.player.name,
      note: "places gained since last session" });

    if (bestRate) push(bestRate.e.player.id, { key: "rate", colour: "#FF2E88",
      label: "BEST WIN RATE", value: bestRate.en.winRate + "%", name: bestRate.e.player.name,
      note: "from " + bestRate.en.decided + " matches" });

    // Never missed a night -- only meaningful once there are nights to miss.
    if (nightsDone >= 2) {
      const iron = played.find(e => !used.has(e.player.id) && e.stats.sessionsPlayed >= nightsDone);
      if (iron) push(iron.player.id, { key: "iron", colour: "#C6FF00",
        label: "NEVER MISSED A NIGHT", value: nightsDone + "/" + nightsDone,
        name: iron.player.name, note: "every night so far" });
    }

    const titled = played.filter(e => !used.has(e.player.id) && e.stats.finalsWon > 0)
      .sort((a, b) => b.stats.finalsWon - a.stats.finalsWon)[0];
    if (titled) push(titled.player.id, { key: "titles", colour: "#FF2E88",
      label: "SESSION TITLES", value: String(titled.stats.finalsWon), name: titled.player.name,
      note: titled.stats.finalsWon === 1 ? "one night won" : "nights won outright" });

    return out.slice(0, 4);
  })();'''



# ── Motion polish ────────────────────────────────────────────────────────
POLISH_CSS = """
/* ── Leader sheen: a slow diagonal pass, mostly paused ── */
.bo-sheen{position:relative;overflow:hidden}
.bo-sheen::after{content:"";position:absolute;top:0;bottom:0;width:40%;
  background:linear-gradient(100deg,transparent,rgba(198,255,0,.14),transparent);
  transform:translateX(-160%);animation:bo-sheen 6s ease-in-out infinite}
@keyframes bo-sheen{0%{transform:translateX(-160%)}28%{transform:translateX(320%)}
  100%{transform:translateX(320%)}}

/* ── Rows arrive from below, staggered ── */
.bo-rowin{animation:bo-rowin 420ms cubic-bezier(.34,1.4,.64,1) both}
@keyframes bo-rowin{from{opacity:0;transform:translateY(12px)}to{opacity:1;transform:none}}

@media (prefers-reduced-motion:reduce){
  .bo-sheen::after{animation:none;display:none}
  .bo-rowin{animation:none}
}
"""

COUNTUP = r"""

// ══ VOL.8 · COUNT-UP ══════════════════════════════════════════════════════
// Headline numbers ease to their value instead of snapping. Stepped rather than
// time-based so it lands exactly on the target: max(1, ceil(remaining * .16))
// per frame, which is the handoff's rule.
function useCountUp(target) {
  const [n, setN] = React.useState(0);
  const raf = React.useRef();
  React.useEffect(() => {
    const t = Number(target) || 0;
    if (window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      setN(t); return;
    }
    let cur = 0;
    const tick = () => {
      const diff = t - cur;
      if (Math.abs(diff) <= 1) { setN(t); return; }
      cur += Math.sign(diff) * Math.max(1, Math.ceil(Math.abs(diff) * 0.16));
      setN(cur);
      raf.current = requestAnimationFrame(tick);
    };
    raf.current = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf.current);
  }, [target]);
  return n;
}
function CountUp({ to, prefix = "", suffix = "" }) {
  const n = useCountUp(to);
  return <>{prefix}{n}{suffix}</>;
}
"""

# ME's headline number is the one people stare at.
COUNT_ME_OLD = '''            <div style={{ fontFamily: "'JetBrains Mono',monospace", fontWeight: 700, fontSize: 62,
                          lineHeight: 1, color: "#C6FF00" }}>{data.total}</div>'''
COUNT_ME_NEW = '''            <div style={{ fontFamily: "'JetBrains Mono',monospace", fontWeight: 700, fontSize: 62,
                          lineHeight: 1, color: "#C6FF00" }}><CountUp to={data.total} /></div>'''


# ══════════════════════════════════════════════════════════════════════════
# 10 · LINE-UP STORY CARDS — the semi-finals and the final
# ══════════════════════════════════════════════════════════════════════════
#
# The design handover shipped these as a separate file, `Semi-Final Story`, and
# nothing in the app ever used it: 1080x1920, a photo slot with a colour grade
# over it, SEMI / FINAL in display type, the two teams on plates and the pool
# across the foot. This is that template, driven by the bracket.
#
# It is a LINE-UP card, not a result card — it goes out when the draw is known
# and the match has not been played, which is the moment people actually want to
# post. The four existing share cards are all after the fact.
#
# Three things worth knowing:
#
# The photo is OPTIONAL and the card is designed to work without one. Session
# photos live on Cloudinary, so drawing one into the canvas is a cross-origin
# draw; if the CDN does not send CORS headers the canvas is tainted and
# toDataURL throws. That is caught and the card is repainted without the photo
# rather than failing.
#
# Canvas cannot set `font-variation-settings`, so the display type here is at
# Archivo's default width, not 'wdth' 125 — the same compromise the other share
# cards make.
#
# The pool is derived from the same constants the app uses everywhere else. The
# handover's own artwork says 402 OMR, which does not add up from its parts;
# nothing here types a total.

LINEUP = r"""
const LU_W = 1080, LU_H = 1920;

function luImg(src) {
  return new Promise(res => {
    if (!src) return res(null);
    const im = new Image();
    im.crossOrigin = "anonymous";
    im.onload = () => res(im);
    im.onerror = () => res(null);
    im.src = src;
  });
}

// Cover-fit, the way CSS background-size:cover does it: fill the box, crop the
// overflow, never distort faces.
function luCover(g, im, x, y, w, h) {
  const r = Math.max(w / im.width, h / im.height);
  const dw = im.width * r, dh = im.height * r;
  g.drawImage(im, x + (w - dw) / 2, y + (h - dh) / 2, dw, dh);
}

function luPaint(g, kind, d, im) {
  g.fillStyle = "#050505"; g.fillRect(0, 0, LU_W, LU_H);

  // ── the photo, and the grade that makes any photo look like this volume ──
  if (im) {
    const top = 420, hh = 1140;
    g.save();
    g.beginPath(); g.rect(0, top, LU_W, hh); g.clip();
    luCover(g, im, 0, top, LU_W, hh);
    // desaturate, then push the brand's two colours in from the two edges
    g.globalCompositeOperation = "saturation";
    g.fillStyle = "#1a1a1a"; g.globalAlpha = 0.85;
    g.fillRect(0, top, LU_W, hh);
    g.globalAlpha = 1;
    g.globalCompositeOperation = "screen";
    let lr = g.createLinearGradient(0, 0, LU_W, 0);
    lr.addColorStop(0, "rgba(255,46,136,.55)");
    lr.addColorStop(0.38, "rgba(255,46,136,0)");
    lr.addColorStop(0.62, "rgba(198,255,0,0)");
    lr.addColorStop(1, "rgba(198,255,0,.45)");
    g.fillStyle = lr; g.fillRect(0, top, LU_W, hh);
    g.restore();
    // fade the photo into the ground at both ends, so it has no visible edge
    let vg = g.createLinearGradient(0, top, 0, top + hh);
    vg.addColorStop(0, "#050505");
    vg.addColorStop(0.18, "rgba(5,5,5,0)");
    vg.addColorStop(0.62, "rgba(5,5,5,0)");
    vg.addColorStop(1, "#050505");
    g.fillStyle = vg; g.fillRect(0, top, LU_W, hh);
  } else {
    // No photo: the corner washes the rest of the brand uses, so the card is
    // never a flat black rectangle.
    let rg = g.createRadialGradient(LU_W, LU_H * 0.16, 0, LU_W, LU_H * 0.16, LU_W);
    rg.addColorStop(0, "rgba(255,46,136,.22)"); rg.addColorStop(1, "rgba(255,46,136,0)");
    g.fillStyle = rg; g.fillRect(0, 0, LU_W, LU_H);
    rg = g.createRadialGradient(0, LU_H * 0.9, 0, 0, LU_H * 0.9, LU_W);
    rg.addColorStop(0, "rgba(198,255,0,.12)"); rg.addColorStop(1, "rgba(198,255,0,0)");
    g.fillStyle = rg; g.fillRect(0, 0, LU_W, LU_H);
  }

  // scanlines over everything
  g.fillStyle = "rgba(198,255,0,.055)";
  for (let y = 0; y < LU_H; y += 10) g.fillRect(0, y, LU_W, 2);
  g.fillStyle = "#C6FF00"; g.fillRect(0, 0, LU_W, 10);

  const L = 80, R = LU_W - 80, W = R - L;

  // ── header ──
  g.fillStyle = "#C6FF00"; g.fillRect(L, 146, 16, 16);
  stMono(g, "BLACKOUT SERIES · VOL.8", L + 40, 161, 26, "#C6FF00", 6);

  const big = kind === "final" ? ["THE", "FINAL"] : ["SEMI", "FINAL"];
  stDisp(g, big[0], L, 350, 164, "#F2F2F2", W);
  stDisp(g, big[1], L, 500, 164, "#C6FF00", W);

  // ── the two plates, sitting on the floor of the card ──
  const plate = (y, name, chip, colour) => {
    g.fillStyle = "rgba(15,15,15,.92)";
    g.fillRect(L, y, W, 150);
    g.strokeStyle = colour; g.lineWidth = 3;
    g.strokeRect(L + 1.5, y + 1.5, W - 3, 147);
    const room = W - 72 - (chip ? 140 : 0);
    const size = stFit(g, name, room, 56, 900);
    g.font = `italic 900 ${size}px Archivo, sans-serif`;
    g.fillStyle = "#F2F2F2";
    g.fillText(name, L + 36, y + 95);
    if (chip) {
      g.font = '700 26px "JetBrains Mono", monospace';
      g.fillStyle = colour;
      g.fillText(chip, R - 36 - g.measureText(chip).width, y + 92);
    }
  };

  const baseY = 1270;
  plate(baseY, (d.a || "TBD").toUpperCase(), d.aChip || "", "#C6FF00");
  g.font = '900 30px Archivo, sans-serif'; g.fillStyle = "#FF2E88";
  {
    const t = "V S";
    g.fillText(t, (LU_W - g.measureText(t).width) / 2, baseY + 222);
  }
  plate(baseY + 260, (d.b || "TBD").toUpperCase(), d.bChip || "", "#FF2E88");

  // ── footer ──
  stMono(g, d.foot || "", L, LU_H - 150, 28, "#8A8A8A", 6);
  g.font = '800 28px Archivo, sans-serif'; g.fillStyle = "#C6FF00";
  {
    const t = `${d.pool} OMR`;
    g.fillText(t, R - g.measureText(t).width, LU_H - 150);
  }
}

// Returns a data URL. The photo may taint the canvas, which only shows up at
// toDataURL, so the fallback is a clean repaint without it rather than an error.
async function drawLineup(kind, d, photo) {
  const im = await luImg(photo);
  const mk = (img) => {
    const c = document.createElement("canvas");
    c.width = LU_W; c.height = LU_H;
    luPaint(c.getContext("2d"), kind, d, img);
    return c;
  };
  try {
    return mk(im).toDataURL("image/png");
  } catch (e) {
    return mk(null).toDataURL("image/png");
  }
}

// Every line-up this session can show: each semi with both teams known, then
// the final. Built from the bracket, so it cannot disagree with the draw.
function buildLineups(session, state, pool) {
  const teams = session.teams || [];
  const nm = id => {
    const t = teams.find(x => x.id === id);
    if (!t) return "";
    // First names, as the handover's own template shows them: two full names
    // on one plate shrink to the point where neither is readable in a story.
    const f = pid => (((state.players || []).find(p => p.id === pid) || {}).name || "?")
                       .split(" ")[0];
    return `${f(t.p1Id)} & ${f(t.p2Id)}`;
  };
  const grp = id => {
    const t = teams.find(x => x.id === id);
    return t && t.group ? "GRP " + t.group : "";
  };
  // The session's own name is what everyone calls it; fall back to its position
  // only when the name carries no number.
  const named = (session.name || "").match(/\d+/);
  const no = named ? Number(named[0])
                   : (state.sessions || []).findIndex(s => s.id === session.id) + 1;
  const foot = `NIGHT ${String(no).padStart(2, "0")}`;
  const out = [];
  const b = session.bracket || {};
  (b.sf || []).forEach((m, i) => {
    if (!m || !m.team1Id || !m.team2Id) return;
    out.push({
      key: "sf" + i, kind: "semi", label: `SEMI ${i + 1}`,
      a: nm(m.team1Id), b: nm(m.team2Id), aChip: grp(m.team1Id), bChip: grp(m.team2Id),
      foot, pool,
      caption: `Semi-final ${i + 1} tonight — ${nm(m.team1Id)} vs ${nm(m.team2Id)}. `
             + `Night ${no} of the Blackout Series. blackout.urbanpadel.om`,
    });
  });
  const f = b.final;
  if (f && f.team1Id && f.team2Id) {
    out.push({
      key: "final", kind: "final", label: "FINAL",
      a: nm(f.team1Id), b: nm(f.team2Id), aChip: grp(f.team1Id), bChip: grp(f.team2Id),
      foot, pool,
      caption: `The final — ${nm(f.team1Id)} vs ${nm(f.team2Id)}. `
             + `Night ${no} of the Blackout Series. blackout.urbanpadel.om`,
    });
  }
  return out;
}

function LineupSheet({ open, items, photos, onClose }) {
  const [i, setI] = React.useState(0);
  const [ph, setPh] = React.useState(-1);          // -1 = no photo
  const [url, setUrl] = React.useState("");
  const [flash, setFlash] = React.useState("");
  React.useEffect(() => { if (open) { setI(0); setPh(-1); } }, [open]);
  const item = items[i];
  React.useEffect(() => {
    if (!open || !item) return;
    let alive = true;
    setUrl("");
    // The display face has to be in before the canvas measures anything, or the
    // card is laid out against a fallback and the names overrun their plates.
    document.fonts.ready
      .then(() => drawLineup(item.kind, item, ph >= 0 ? photos[ph] : null))
      .then(u => { if (alive) setUrl(u); });
    return () => { alive = false; };
  }, [open, i, ph, items, photos]);
  if (!open || !item) return null;

  const save = async () => {
    try {
      const blob = await (await fetch(url)).blob();
      const f = new File([blob], `blackout-${item.key}.png`, { type: "image/png" });
      if (navigator.canShare && navigator.canShare({ files: [f] })) {
        await navigator.share({ files: [f], title: "Blackout Series" });
        return;
      }
    } catch (e) { if (e && e.name === "AbortError") return; }
    const a = document.createElement("a");
    a.href = url; a.download = `blackout-${item.key}.png`;
    document.body.appendChild(a); a.click(); a.remove();
    setFlash("SAVED"); setTimeout(() => setFlash(""), 1600);
  };
  const copy = async () => {
    try { await navigator.clipboard.writeText(item.caption || ""); setFlash("CAPTION COPIED"); }
    catch (e) { setFlash("COULDN'T COPY"); }
    setTimeout(() => setFlash(""), 1600);
  };

  return (
    <div onClick={onClose} style={{ position: "fixed", inset: 0, zIndex: 90,
      background: "rgba(5,5,5,.9)", display: "flex", alignItems: "flex-end" }}>
      <div onClick={e => e.stopPropagation()} style={{ background: "#0A0A0A", width: "100%",
        maxHeight: "94vh", overflowY: "auto", borderTop: "3px solid #C6FF00", padding: 16 }}>
        <div style={{ display: "grid",
                      gridTemplateColumns: `repeat(${Math.min(items.length, 4)},1fr)`, gap: 6 }}>
          {items.map((it, k) => (
            <button key={it.key} onClick={() => setI(k)} style={{ padding: "10px 4px", cursor: "pointer",
              background: i === k ? "#C6FF00" : "transparent",
              color: i === k ? "#050505" : "#9A9A9A",
              border: "1px solid " + (i === k ? "#C6FF00" : "rgba(110,110,110,.3)"),
              fontFamily: "'JetBrains Mono',monospace", fontWeight: 700, fontSize: 10,
              letterSpacing: ".12em" }}>{it.label}</button>
          ))}
        </div>

        {photos.length > 0 && (
          <button onClick={() => setPh(p => (p + 2 > photos.length ? -1 : p + 1))}
            style={{ width: "100%", marginTop: 8, padding: "10px", cursor: "pointer",
              background: "transparent", color: ph >= 0 ? "#C6FF00" : "#9A9A9A",
              border: "1px solid " + (ph >= 0 ? "rgba(198,255,0,.45)" : "rgba(110,110,110,.3)"),
              fontFamily: "'JetBrains Mono',monospace", fontWeight: 700, fontSize: 10,
              letterSpacing: ".12em" }}>
            {ph >= 0 ? `PHOTO ${ph + 1} / ${photos.length} — TAP TO CHANGE` : "ADD A PHOTO FROM TONIGHT"}
          </button>
        )}

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
            fontWeight: 700, fontSize: 11, letterSpacing: ".14em" }}>SHARE / SAVE</button>
          <button onClick={copy} style={{ padding: "16px", background: "transparent", color: "#C6FF00",
            border: "1px solid rgba(198,255,0,.45)", cursor: "pointer",
            fontFamily: "'JetBrains Mono',monospace", fontWeight: 700, fontSize: 11,
            letterSpacing: ".14em" }}>COPY CAPTION</button>
        </div>
        {flash && <div style={{ textAlign: "center", color: "#C6FF00", marginTop: 10,
          fontFamily: "'JetBrains Mono',monospace", fontSize: 11, letterSpacing: ".14em" }}>{flash}</div>}
        <button onClick={onClose} style={{ width: "100%", marginTop: 10, padding: "12px",
          background: "transparent", color: "#6E6E6E", border: "none", cursor: "pointer",
          fontFamily: "'JetBrains Mono',monospace", fontSize: 11, letterSpacing: ".14em" }}>CLOSE</button>
      </div>
    </div>
  );
}
"""

# The chip that opens it, in the session's action row. It appears the moment a
# line-up exists — which is the point: the card is for the gap between the draw
# and the match, not for afterwards.
LU_ACT_OLD = """              { key:"draw", label:"Draw", Ic:CIc.dice, go:() => setShowDraw(true), show:isAdmin },"""
LU_ACT_NEW = """              { key:"lineup", label:"Line-up", Ic:CIc.share, go:() => setShowLineup(true),
                show:lineups.length > 0, warm:true },
              { key:"draw", label:"Draw", Ic:CIc.dice, go:() => setShowDraw(true), show:isAdmin },"""

LU_STATE_OLD = """  const [showShare, setShowShare] = useState(false);"""
LU_STATE_NEW = """  const [showShare, setShowShare] = useState(false);
  const [showLineup, setShowLineup] = useState(false);
  // Derived, not stored: the draw is the source of truth for who is playing.
  const lineups = buildLineups(session, state,
    14 * 2 * SESSIONS_TOTAL + SEASON_PRIZES.reduce((a, b) => a + b, 0));"""

LU_MOUNT_OLD = """      {showEdit && <Modal open={true} onClose={() => setShowEdit(false)} title="SESSION OPTIONS">"""
LU_MOUNT_NEW = """      <LineupSheet open={showLineup} items={lineups} photos={sessionPhotos}
                   onClose={() => setShowLineup(false)} />
      {showEdit && <Modal open={true} onClose={() => setShowEdit(false)} title="SESSION OPTIONS">"""


# ══════════════════════════════════════════════════════════════════════════
# 11 · UI/UX REQUEST — the logo on screens, and the table on SESSIONS
# ══════════════════════════════════════════════════════════════════════════
#
# Two things the owner asked for directly, plus the shared pieces the social /
# recap package needs.
#
# The mark is drawn as inline SVG rather than loaded from assets/: it appears on
# five screens, and five <img> requests for the same 16px square is five chances
# for a screen to render with a hole in its header. It is the same geometry the
# share cards draw on canvas.
#
# rankAt() is the one new piece of engine. It ranks the field as it stood after
# any given night, which is what every movement arrow in this package is: the
# difference between rankAt(n) and rankAt(n-1). Computed, never stored — a
# stored delta is a delta that goes stale the moment a score is corrected.

UIUX = r"""
function BoMark({ size = 16, style }) {
  const s = size;
  return (
    <svg width={s} height={s} viewBox="0 0 100 100" aria-hidden="true"
         style={{ display: "block", flex: "0 0 auto", ...(style || {}) }}>
      <rect x="0" y="0" width="100" height="46" fill="#C6FF00" />
      <rect x="75" y="12" width="13" height="13" fill="#FF2E88" />
      <rect x="0" y="55" width="100" height="7" fill="#C6FF00" />
      <rect x="0" y="69" width="100" height="9" fill="#C6FF00" />
      <rect x="0" y="85" width="100" height="11" fill="#C6FF00" />
    </svg>
  );
}

// An eyebrow with the mark in front of it. Every screen head uses this, so the
// mark sits in the same place on all of them instead of five near-misses.
function ScreenEyebrow({ children, color = "#C6FF00" }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
      <BoMark size={14} />
      <div style={{ fontFamily: "'Archivo',sans-serif", fontWeight: 800, fontSize: 10,
                    letterSpacing: ".34em", textTransform: "uppercase", color }}>
        {children}
      </div>
    </div>
  );
}

// The table as it stood after night `upto` (0-based, inclusive). Returns a map
// of playerId -> rank, plus the ordered rows.
function rankAt(state, upto) {
  const sessions = (state.sessions || []).slice(0, upto + 1);
  const rows = (state.players || []).map(p => {
    const s = calcPlayerStats(p.id, sessions);
    // sessionsPlayed lives on s.stats, not on s — reading it off the top level
    // silently returns undefined and ranks nobody who has yet to score.
    return { id: p.id, name: p.name, pts: s.totalPts, played: (s.stats || {}).sessionsPlayed || 0 };
  }).filter(r => r.played > 0 || r.pts > 0)
    .sort((a, b) => b.pts - a.pts || a.name.localeCompare(b.name));
  const rank = {};
  rows.forEach((r, i) => { rank[r.id] = i + 1; });
  return { rows, rank };
}

// Movement into the latest completed night: ▲n, ▼n or —.
function moveInto(state, idx) {
  if (idx <= 0) return { rank: rankAt(state, idx).rank, prev: {} };
  return { rank: rankAt(state, idx).rank, prev: rankAt(state, idx - 1).rank };
}

function Delta({ now, before }) {
  if (!before || !now || before === now) {
    return <span style={{ fontFamily: "'JetBrains Mono',monospace", fontSize: 11,
                          color: "#6E6E6E" }}>—</span>;
  }
  const up = before > now;
  return (
    <span style={{ fontFamily: "'JetBrains Mono',monospace", fontSize: 11, fontWeight: 700,
                   color: up ? "#C6FF00" : "#FF2E88" }}>
      {up ? "▲" : "▼"}{Math.abs(before - now)}
    </span>
  );
}

// The standings, on the SESSIONS screen. The owner asked to see the ranking
// without leaving for the RANK tab — this is the top five plus your own row
// when you are outside it, which is the only part of the table anyone checks
// between nights.
function SessionsTable({ state, meId, onOpen }) {
  const played = (state.sessions || []).reduce(
    (n, s, i) => (s.completed || (s.bracket && s.bracket.final && s.bracket.final.winner) ? i : n), -1);
  const { rows } = rankAt(state, Math.max(played, (state.sessions || []).length - 1));
  if (!rows.length) {
    return (
      <div style={{ border: "1px solid rgba(110,110,110,.3)", background: "rgba(14,14,14,.94)",
                    padding: 16, textAlign: "center", color: "#6E6E6E", fontSize: 12 }}>
        The table opens after the first night is played.
      </div>
    );
  }
  const { rank, prev } = moveInto(state, played);
  const top = rows.slice(0, 5);
  const mine = rows.findIndex(r => r.id === meId);
  const extra = mine >= 5 ? rows[mine] : null;

  const Row = ({ r, i }) => {
    const you = r.id === meId;
    return (
      <div onClick={() => onOpen && onOpen(r.id)}
           style={{ display: "grid", gridTemplateColumns: "22px 1fr 44px 42px", alignItems: "center",
                    gap: 8, padding: "9px 0", cursor: onOpen ? "pointer" : "default",
                    borderTop: i === 0 ? "none" : "1px solid rgba(110,110,110,.16)" }}>
        <div style={{ fontFamily: "'JetBrains Mono',monospace", fontSize: 12,
                      color: i === 0 ? "#C6FF00" : "#6E6E6E" }}>{rank[r.id] || i + 1}</div>
        <div style={{ fontSize: 14, fontWeight: 800,
                      color: you ? "#FF2E88" : "#F2F2F2", overflow: "hidden",
                      textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
          {r.name}{you ? " · you" : ""}
        </div>
        <div style={{ textAlign: "center" }}>
          <Delta now={rank[r.id]} before={prev[r.id]} />
        </div>
        <div style={{ fontStyle: "italic", fontVariationSettings: "'wdth' 112,'wght' 900",
                      fontSize: 17, textAlign: "right",
                      color: you ? "#FF2E88" : "#F2F2F2" }}>{r.pts}</div>
      </div>
    );
  };

  return (
    <div style={{ border: "1px solid rgba(198,255,0,.35)", background: "rgba(20,20,20,.96)",
                  padding: "12px 14px 6px" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center",
                    marginBottom: 4 }}>
        <div style={{ fontFamily: "'Archivo',sans-serif", fontWeight: 900, fontSize: 9,
                      letterSpacing: ".3em", color: "#C6FF00" }}>
          {played >= 0 ? `TABLE AFTER S${played + 1}` : "THE TABLE"}
        </div>
        <div style={{ fontFamily: "'JetBrains Mono',monospace", fontSize: 10, color: "#9A9A9A" }}>
          {rows.length} RANKED
        </div>
      </div>
      {top.map((r, i) => <Row key={r.id} r={r} i={i} />)}
      {extra && (
        <>
          <div style={{ borderTop: "1px solid rgba(110,110,110,.16)", margin: "2px 0" }} />
          <Row r={extra} i={1} />
        </>
      )}
    </div>
  );
}
"""

# The mark, on every screen head. Each of these is the eyebrow line above a
# screen's 44px headline; swapping the plain div for ScreenEyebrow puts the mark
# in front of it without touching the headline underneath.
LOGO_SESSIONS_OLD = """          <div style={{fontFamily:"'Archivo',sans-serif",fontWeight:800,fontSize:10,letterSpacing:".34em",
               textTransform:"uppercase",color:"#C6FF00"}}>{state.sessions.length || SESSIONS_TOTAL} nights · Vol.8</div>"""
LOGO_SESSIONS_NEW = """          <ScreenEyebrow>{state.sessions.length || SESSIONS_TOTAL} nights &middot; Vol.8</ScreenEyebrow>"""

# The standings card, between the SESSIONS head and the list of nights.
TABLE_ON_SESSIONS_OLD = """      <div style={{display:"flex",flexDirection:"column",gap:8,marginTop:12}}>
        {state.sessions.length === 0 ? ("""
TABLE_ON_SESSIONS_NEW = """      <div style={{marginTop:14}}>
        <SessionsTable state={state} meId={meId}
                       onOpen={() => setTab && setTab("leaderboard")} />
      </div>

      <div style={{display:"flex",flexDirection:"column",gap:8,marginTop:12}}>
        {state.sessions.length === 0 ? ("""

# The mark on the other four screen heads. Each is an eyebrow above a big
# headline; the mark goes in front of the eyebrow so it sits in the same
# position on every screen rather than five near-misses.
LOGO_ME_OLD = """      <div style={{ fontFamily: "'JetBrains Mono',monospace", fontWeight: 700, fontSize: 10,
                    letterSpacing: ".28em", color: "#9A9A9A" }}>
        YOUR SEASON &middot; {(me?.name || "").toUpperCase()}
      </div>"""
LOGO_ME_NEW = """      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
        <BoMark size={14} />
        <div style={{ fontFamily: "'JetBrains Mono',monospace", fontWeight: 700, fontSize: 10,
                      letterSpacing: ".28em", color: "#9A9A9A" }}>
          YOUR SEASON &middot; {(me?.name || "").toUpperCase()}
        </div>
      </div>"""

LOGO_PLAYERS_OLD = """      <div style={{ fontFamily: "'JetBrains Mono',monospace", fontWeight: 700, fontSize: 10,
                    letterSpacing: ".28em", color: "#9A9A9A" }}>
        THE ROSTER &middot; {leaderboard.length} PLAYERS"""
LOGO_PLAYERS_NEW = """      <div style={{ fontFamily: "'JetBrains Mono',monospace", fontWeight: 700, fontSize: 10,
                    letterSpacing: ".28em", color: "#9A9A9A",
                    display: "flex", alignItems: "center", gap: 8 }}>
        <BoMark size={14} />
        THE ROSTER &middot; {leaderboard.length} PLAYERS"""

LOGO_RANK_OLD = """        <div style={{position:"relative",fontFamily:"'Archivo',sans-serif",fontWeight:800,fontSize:10,
             letterSpacing:".34em",textTransform:"uppercase",color:"#C6FF00"}}>
          Series standings · {active.length} players</div>"""
LOGO_RANK_NEW = """        <div style={{position:"relative",fontFamily:"'Archivo',sans-serif",fontWeight:800,fontSize:10,
             letterSpacing:".34em",textTransform:"uppercase",color:"#C6FF00",
             display:"flex",alignItems:"center",gap:8}}>
          <BoMark size={14} />Series standings · {active.length} players</div>"""

LOGO_RECAP_OLD = """          SESSION {idx + 1} &middot; {fmtNightDate(session.date)}{session.doublePoints ? " · 2X NIGHT" : ""}"""
LOGO_RECAP_NEW = """          <BoMark size={13} style={{ display: "inline-block", verticalAlign: "-2px", marginRight: 7 }} />
          SESSION {idx + 1} &middot; {fmtNightDate(session.date)}{session.doublePoints ? " · 2X NIGHT" : ""}"""


# ══════════════════════════════════════════════════════════════════════════
# 12 · SESSION RECAPS — "my night" and "everyone", from the social handoff
# ══════════════════════════════════════════════════════════════════════════
#
# The handoff asks for one Recap screen with two tabs. Vol.8 already shipped the
# "everyone" half as RecapSheet, so this keeps it and adds the half that was
# missing: the player's own night, game by game.
#
# Everything is DERIVED from the session. The handoff specifies a
# sessionRecap(sessionId, userId) endpoint returning pointsBefore/After and
# rankBefore/After; there is no such endpoint and there does not need to be —
# the app already holds every session, so before/after is rankAt(n-1) against
# rankAt(n) and the games come out of the match lists. A stored recap is a recap
# that lies the moment a score is corrected, which on this app happens most
# weeks.
#
# The headline is generated from the result, per the handoff's rule. The order
# matters: a tiebreak is more interesting than a count of wins, and beating the
# leader is more interesting than either.

RECAP2 = r"""
// Every game one player played on a night, in the order they played them.
function recapGames(session, state, pid) {
  const team = getPlayerTeam(session, pid);
  if (!team) return [];
  const nameOf = id => ((state.players || []).find(p => p.id === id) || {}).name || "?";
  const first = id => nameOf(id).split(" ")[0];
  const partner = team.p1Id === pid ? team.p2Id : team.p1Id;
  const teamOf = tid => (session.teams || []).find(t => t.id === tid);
  const opp = tid => {
    const t = teamOf(tid);
    return t ? [first(t.p1Id), first(t.p2Id)] : ["?", "?"];
  };

  const rows = [];
  const push = (m, stage) => {
    if (!m || !m.winner || (m.team1Id !== team.id && m.team2Id !== team.id)) return;
    const mine = m.team1Id === team.id;
    const otherId = mine ? m.team2Id : m.team1Id;
    const won = teamWon(m, team.id);
    const a = mine ? m.score.t1 : m.score.t2;
    const b = mine ? m.score.t2 : m.score.t1;
    rows.push({
      stage, won, score: `${a}–${b}`,
      partner: first(partner), opponents: opp(otherId),
      tiebreak: m.lossType === "tiebreak" || Math.abs(a - b) === 1,
    });
  };

  let g = 0;
  (session.groupMatches || []).forEach(m => {
    if (m.team1Id === team.id || m.team2Id === team.id) { g += 1; push(m, `GROUP · G${g}`); }
  });
  ((session.bracket || {}).qf || []).forEach(m => push(m, "QUARTER-FINAL"));
  ((session.bracket || {}).sf || []).forEach(m => push(m, "SEMI-FINAL"));
  const f = (session.bracket || {}).final;
  if (f) push(f, "FINAL");
  const tp = (session.bracket || {}).thirdsPlayoff || (session.bracket || {}).thirdPlace;
  if (tp) push(tp, "3RD PLACE");
  return rows;
}

// The headline, generated from what actually happened. Ordered by what is worth
// saying: winning the thing, then beating the leader, then a tiebreak, then a
// count of wins.
function recapHeadline(games, opts) {
  const w = games.filter(g => g.won).length;
  const l = games.length - w;
  if (!games.length) return ["NO GAMES", "ON THE NIGHT"];
  if (opts && opts.champion) return [`${w}–${l} AND`, "THE TITLE."];
  if (opts && opts.beatLeader) return ["YOU BEAT", "THE LEADER."];
  if (games.some(g => g.won && g.tiebreak)) return [`${w} WINS.`, "ONE TIEBREAK."];
  if (w && !l) return ["UNBEATEN", "ON THE NIGHT."];
  if (!w) return ["TOUGH ONE.", `${l} LOSSES.`];
  return [`${w} WINS.`, `${l} ${l === 1 ? "LOSS" : "LOSSES"}.`];
}

// The whole group's night, the same for everyone.
function sessionSummary(session, state, idx) {
  const nameOf = id => ((state.players || []).find(p => p.id === id) || {}).name || "?";
  const teamName = tid => {
    const t = (session.teams || []).find(x => x.id === tid);
    return t ? nameOf(t.p1Id).split(" ")[0] + " & " + nameOf(t.p2Id).split(" ")[0] : "—";
  };
  const f = (session.bracket || {}).final;
  const all = (session.groupMatches || []).concat((session.bracket || {}).qf || [],
    (session.bracket || {}).sf || [], f ? [f] : []).filter(m => m && m.winner && m.score);
  const players = (state.players || []).filter(p => getPlayerTeam(session, p.id));

  const { rank } = rankAt(state, idx);
  const prev = idx > 0 ? rankAt(state, idx - 1).rank : {};
  let climb = null;
  players.forEach(p => {
    const before = prev[p.id], now = rank[p.id];
    if (!before || !now) return;
    const up = before - now;
    if (up > 0 && (!climb || up > climb.up)) climb = { name: p.name, up };
  });

  const tiebreaks = all.filter(m => Math.abs(m.score.t1 - m.score.t2) === 1).length;
  const closest = all.map(m => ({ m, d: Math.abs(m.score.t1 - m.score.t2) }))
                     .sort((a, b) => a.d - b.d)[0];

  return {
    playerCount: players.length,
    gameCount: all.length,
    final: f && f.winner ? {
      winners: teamName(f.winner === "team1" ? f.team1Id : f.team2Id),
      runnersUp: teamName(f.winner === "team1" ? f.team2Id : f.team1Id),
      score: f.score ? `${Math.max(f.score.t1, f.score.t2)}–${Math.min(f.score.t1, f.score.t2)}` : "",
    } : null,
    climb, tiebreaks,
    closest: closest ? { score: `${closest.m.score.t1}–${closest.m.score.t2}` } : null,
  };
}

// ── the two tabs ──────────────────────────────────────────────────────────
function RecapToggle({ tab, setTab }) {
  const B = ({ id, label }) => (
    <button onClick={() => setTab(id)} style={{ padding: "11px 4px", cursor: "pointer",
      background: tab === id ? "#C6FF00" : "transparent",
      color: tab === id ? "#050505" : "#9A9A9A", border: "none",
      fontFamily: "'Archivo',sans-serif", fontWeight: 900, fontSize: 10,
      letterSpacing: ".24em", textTransform: "uppercase" }}>{label}</button>
  );
  return (
    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr",
                  border: "1px solid rgba(110,110,110,.4)", marginTop: 14 }}>
      <B id="mine" label="My night" /><B id="everyone" label="Everyone" />
    </div>
  );
}

function RecapMine({ session, state, meId, idx, onShare }) {
  if (!meId) {
    return <div style={{ padding: "28px 0", textAlign: "center", color: "#6E6E6E", fontSize: 13 }}>
      Pick who you are on the ME tab and your night appears here.
    </div>;
  }
  const games = recapGames(session, state, meId);
  if (!games.length) {
    return <div style={{ padding: "28px 0", textAlign: "center", color: "#6E6E6E", fontSize: 13 }}>
      You did not play this night.
    </div>;
  }
  const after = rankAt(state, idx), before = idx > 0 ? rankAt(state, idx - 1) : { rank: {} };
  const rankNow = after.rank[meId], rankWas = before.rank[meId];
  const ptsNow = calcPlayerStats(meId, (state.sessions || []).slice(0, idx + 1)).totalPts;
  const ptsWas = idx > 0 ? calcPlayerStats(meId, (state.sessions || []).slice(0, idx)).totalPts : 0;
  const f = (session.bracket || {}).final;
  const myTeam = getPlayerTeam(session, meId);
  const champion = !!(f && f.winner && myTeam &&
    (f.winner === "team1" ? f.team1Id : f.team2Id) === myTeam.id);
  const head = recapHeadline(games, { champion });
  const down = rankWas && rankNow && rankNow > rankWas;
  // calcBadges(pid, sessions, players, nightsData, ranks) — passing `state`
  // where `sessions` belongs crashes the screen, since state has no .filter.
  const upto = (state.sessions || []).slice(0, idx + 1);
  const nameOf = id => ((state.players || []).find(p => p.id === id) || {}).name || "?";
  const nights = calcPlayerNights(meId, upto, nameOf);
  const badges = calcBadges(meId, upto, state.players || [], nights,
                            rankByNight(state.players || [], upto));
  const fresh = (badges || []).filter(b => b.got).slice(-1)[0];

  return (
    <div>
      <div style={{ fontStyle: "italic", fontVariationSettings: "'wdth' 125,'wght' 900",
                    fontSize: 44, lineHeight: .88, marginTop: 14 }}>
        {head[0]}<br /><span style={{ color: "#C6FF00" }}>{head[1]}</span>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", marginTop: 16,
                    border: "1px solid rgba(198,255,0,.35)" }}>
        <div style={{ padding: 14, borderRight: "1px solid rgba(110,110,110,.3)" }}>
          <div style={{ fontFamily: "'Archivo',sans-serif", fontWeight: 800, fontSize: 8,
                        letterSpacing: ".2em", color: "#9A9A9A" }}>RANK</div>
          <div style={{ marginTop: 6, display: "flex", alignItems: "baseline", gap: 7 }}>
            <span style={{ fontFamily: "'JetBrains Mono',monospace", fontSize: 22,
                           color: "#6E6E6E" }}>{rankWas ? "#" + rankWas : "-"}</span>
            <span style={{ color: "#6E6E6E" }}>&#9654;</span>
            <span style={{ fontStyle: "italic", fontVariationSettings: "'wdth' 112,'wght' 900",
                           fontSize: 34, color: down ? "#FF2E88" : "#C6FF00" }}>
              {rankNow ? "#" + rankNow : "-"}</span>
          </div>
        </div>
        <div style={{ padding: 14, textAlign: "right" }}>
          <div style={{ fontFamily: "'Archivo',sans-serif", fontWeight: 800, fontSize: 8,
                        letterSpacing: ".2em", color: "#9A9A9A" }}>POINTS</div>
          <div style={{ marginTop: 6, fontStyle: "italic",
                        fontVariationSettings: "'wdth' 112,'wght' 900", fontSize: 34,
                        color: "#C6FF00" }}>{ptsWas} &#9654; {ptsNow}</div>
        </div>
      </div>

      <div style={{ fontFamily: "'Archivo',sans-serif", fontWeight: 900, fontSize: 9,
                    letterSpacing: ".3em", color: "#9A9A9A", margin: "18px 0 2px" }}>GAMES</div>
      {games.map((g, i) => (
        <div key={i} style={{ display: "flex", alignItems: "center", gap: 10, padding: "10px 0",
                              borderTop: "1px solid rgba(110,110,110,.16)" }}>
          <span style={{ width: 8, height: 8, flex: "0 0 auto",
                         background: g.won ? "#C6FF00" : "#FF2E88" }} />
          <span style={{ flex: 1, minWidth: 0 }}>
            <span style={{ fontSize: 14, fontWeight: 800, display: "block", overflow: "hidden",
                           textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
              w/ {g.partner} vs {g.opponents.join(" & ")}
            </span>
            <span style={{ fontFamily: "'Archivo',sans-serif", fontWeight: 800, fontSize: 9,
                           letterSpacing: ".16em", color: "#9A9A9A" }}>
              {g.stage}{g.tiebreak ? " · TIEBREAK" : ""}
            </span>
          </span>
          <span style={{ fontStyle: "italic", fontVariationSettings: "'wdth' 112,'wght' 900",
                         fontSize: 18 }}>{g.score}</span>
        </div>
      ))}

      {fresh && (
        <div style={{ background: "rgba(255,46,136,.08)", border: "1px solid rgba(255,46,136,.4)",
                      padding: 12, marginTop: 16 }}>
          <div style={{ fontFamily: "'Archivo',sans-serif", fontWeight: 900, fontSize: 9,
                        letterSpacing: ".24em", color: "#FF2E88" }}>UNLOCKED &middot; {fresh.name}</div>
          <div style={{ fontSize: 12, color: "#CFCFCF", marginTop: 4 }}>{fresh.desc}</div>
        </div>
      )}

      {onShare && (
        <button onClick={() => onShare({ head, games, ptsNow, ptsWas, rankNow,
                                         total: (state.players || []).length })}
          style={{ width: "100%", marginTop: 16, padding: 14, background: "#C6FF00",
                   color: "#050505", border: "none", cursor: "pointer",
                   fontFamily: "'JetBrains Mono',monospace", fontWeight: 700, fontSize: 11,
                   letterSpacing: ".2em" }}>SHARE STORY</button>
      )}
    </div>
  );
}

// The group's night. Keeps what Vol.8 already showed — champions, MVP, top
// scorer, biggest win — and adds the three things the handoff asks for: the
// final as a card, the table as it stands after this night, and the night in
// numbers.
function RecapEveryone({ session, state, meId, idx, nameOf, teamName, champTid, f,
                         mvpId, votes, topScorer, biggest, inIt, onShare }) {
  const sum = sessionSummary(session, state, idx);
  const { rows, rank } = rankAt(state, idx);
  const prev = idx > 0 ? rankAt(state, idx - 1).rank : {};
  const top = rows.slice(0, 5);
  const mineIdx = rows.findIndex(r => r.id === meId);
  const extra = mineIdx >= 5 ? rows[mineIdx] : null;

  const Row = ({ k, v, sub, c }) => (
    <div style={{ display: "flex", alignItems: "center", gap: 12, padding: "13px 0",
      borderBottom: "1px solid rgba(110,110,110,.16)" }}>
      <span style={{ fontFamily: "'JetBrains Mono',monospace", fontWeight: 700, fontSize: 9,
        letterSpacing: ".2em", color: "#9A9A9A", width: 104 }}>{k}</span>
      <span style={{ flex: 1, minWidth: 0 }}>
        <span style={{ fontWeight: 800, fontSize: 14, display: "block" }}>{v}</span>
        {sub && <span style={{ fontSize: 12, color: "#9A9A9A" }}>{sub}</span>}
      </span>
      {c && <span style={{ fontFamily: "'JetBrains Mono',monospace", fontWeight: 700,
        fontSize: 16, color: "#C6FF00" }}>{c}</span>}
    </div>
  );

  const TRow = ({ r, i }) => {
    const you = r.id === meId;
    return (
      <div style={{ display: "grid", gridTemplateColumns: "22px 1fr 44px 40px", alignItems: "center",
                    gap: 8, padding: "8px 0",
                    borderTop: i === 0 ? "none" : "1px solid rgba(110,110,110,.16)" }}>
        <span style={{ fontFamily: "'JetBrains Mono',monospace", fontSize: 12,
                       color: i === 0 ? "#C6FF00" : "#6E6E6E" }}>{rank[r.id] || i + 1}</span>
        <span style={{ fontSize: 14, fontWeight: 800, color: you ? "#FF2E88" : "#F2F2F2",
                       overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
          {r.name}{you ? " · you" : ""}</span>
        <span style={{ textAlign: "center" }}><Delta now={rank[r.id]} before={prev[r.id]} /></span>
        <span style={{ fontStyle: "italic", fontVariationSettings: "'wdth' 112,'wght' 900",
                       fontSize: 17, textAlign: "right",
                       color: you ? "#FF2E88" : "#F2F2F2" }}>{r.pts}</span>
      </div>
    );
  };

  const Tile = ({ k, v, c }) => (
    <div style={{ background: "rgba(14,14,14,.94)", padding: 10, flex: 1, minWidth: 0 }}>
      <div style={{ fontFamily: "'Archivo',sans-serif", fontWeight: 800, fontSize: 8,
                    letterSpacing: ".2em", color: "#9A9A9A" }}>{k}</div>
      <div style={{ fontStyle: "italic", fontVariationSettings: "'wdth' 112,'wght' 900",
                    fontSize: 20, marginTop: 5, color: c || "#F2F2F2", overflow: "hidden",
                    textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{v}</div>
    </div>
  );

  return (
    <div>
      <div style={{ fontFamily: "'JetBrains Mono',monospace", fontSize: 10, letterSpacing: ".2em",
                    color: "#9A9A9A", marginTop: 14 }}>
        {sum.playerCount} PLAYERS &middot; {sum.gameCount} GAMES
      </div>
      {sum.final && (
        <div style={{ fontStyle: "italic", fontVariationSettings: "'wdth' 125,'wght' 900",
                      fontSize: 40, lineHeight: .9, marginTop: 8 }}>
          {sum.final.winners.toUpperCase()}<br /><span style={{ color: "#C6FF00" }}>TAKE IT</span>
        </div>
      )}

      {champTid && (
        <div style={{ border: "1px solid rgba(198,255,0,.35)", padding: 14, marginTop: 14 }}>
          <div style={{ fontFamily: "'Archivo',sans-serif", fontWeight: 900, fontSize: 9,
                        letterSpacing: ".3em", color: "#C6FF00" }}>FINAL</div>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline",
                        marginTop: 8 }}>
            <span style={{ fontSize: 15, fontWeight: 800, color: "#C6FF00" }}>{teamName(champTid)}</span>
            <span style={{ fontStyle: "italic", fontVariationSettings: "'wdth' 112,'wght' 900",
                           fontSize: 24, color: "#C6FF00" }}>
              {f && f.score ? Math.max(f.score.t1, f.score.t2) : ""}</span>
          </div>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline",
                        marginTop: 4 }}>
            <span style={{ fontSize: 15, fontWeight: 800, color: "#9A9A9A" }}>
              {teamName(f.winner === "team1" ? f.team2Id : f.team1Id)}</span>
            <span style={{ fontStyle: "italic", fontVariationSettings: "'wdth' 112,'wght' 900",
                           fontSize: 24, color: "#9A9A9A" }}>
              {f && f.score ? Math.min(f.score.t1, f.score.t2) : ""}</span>
          </div>
        </div>
      )}

      <div style={{ marginTop: 16 }}>
        {mvpId && <Row k="MVP" v={nameOf(mvpId)} sub="player vote" c={votes[mvpId]} />}
        {topScorer && topScorer.pts > 0 &&
          <Row k="TOP SCORER" v={topScorer.p.name} sub="points on the night" c={"+" + topScorer.pts} />}
        {biggest && <Row k="BIGGEST WIN" v={teamName(biggest.w)}
          sub={biggest.m.score.t1 + "-" + biggest.m.score.t2} />}
      </div>

      {top.length > 0 && (
        <>
          <div style={{ fontFamily: "'Archivo',sans-serif", fontWeight: 900, fontSize: 9,
                        letterSpacing: ".3em", color: "#9A9A9A", margin: "18px 0 2px" }}>
            TABLE AFTER S{idx + 1}</div>
          {top.map((r, i) => <TRow key={r.id} r={r} i={i} />)}
          {extra && <>
            <div style={{ borderTop: "1px solid rgba(110,110,110,.16)", margin: "2px 0" }} />
            <TRow r={extra} i={1} />
          </>}
        </>
      )}

      <div style={{ fontFamily: "'Archivo',sans-serif", fontWeight: 900, fontSize: 9,
                    letterSpacing: ".3em", color: "#9A9A9A", margin: "18px 0 8px" }}>
        NIGHT IN NUMBERS</div>
      <div style={{ display: "flex", gap: 8 }}>
        <Tile k="BIGGEST CLIMB" v={sum.climb ? sum.climb.name.split(" ")[0] : "—"} c="#C6FF00" />
        <Tile k="TIEBREAKS" v={String(sum.tiebreaks)} />
        <Tile k="CLOSEST" v={sum.closest ? sum.closest.score : "—"} c="#FF2E88" />
      </div>

      {onShare && (
        <button onClick={() => onShare(sum)} style={{ width: "100%", marginTop: 16, padding: 14,
          background: "#C6FF00", color: "#050505", border: "none", cursor: "pointer",
          fontFamily: "'JetBrains Mono',monospace", fontWeight: 700, fontSize: 11,
          letterSpacing: ".2em" }}>SHARE NIGHT RECAP</button>
      )}
    </div>
  );
}

// The 9:16 recap story. Same canvas approach as every other share card here, so
// what you preview is the file you post.
function drawRecapStory(d) {
  const c = document.createElement("canvas");
  c.width = 1080; c.height = 1920;
  const g = c.getContext("2d");
  g.fillStyle = "#050505"; g.fillRect(0, 0, 1080, 1920);
  let rg = g.createRadialGradient(1080, 300, 0, 1080, 300, 1000);
  rg.addColorStop(0, "rgba(255,46,136,.22)"); rg.addColorStop(1, "rgba(255,46,136,0)");
  g.fillStyle = rg; g.fillRect(0, 0, 1080, 1920);
  rg = g.createRadialGradient(0, 1700, 0, 0, 1700, 1000);
  rg.addColorStop(0, "rgba(198,255,0,.12)"); rg.addColorStop(1, "rgba(198,255,0,0)");
  g.fillStyle = rg; g.fillRect(0, 0, 1080, 1920);
  g.fillStyle = "rgba(198,255,0,.05)";
  for (let y = 0; y < 1920; y += 10) g.fillRect(0, y, 1080, 2);
  g.fillStyle = "#C6FF00"; g.fillRect(0, 0, 1080, 10);

  const L = 86, R = 1080 - 86, W = R - L;
  stMono(g, `BLACKOUT SERIES · VOL.8 · S${d.no}`, L, 190, 24, "#C6FF00", 5);
  stDisp(g, (d.who || "").toUpperCase(), L, 400, 112, "#F2F2F2", W);
  stDisp(g, d.record, L, 530, 112, "#C6FF00", W);
  stDisp(g, "ON THE", L, 650, 112, "#F2F2F2", W);
  stDisp(g, "NIGHT", L, 770, 112, "#F2F2F2", W);

  let y = 1020;
  (d.rows || []).slice(0, 3).forEach(r => {
    g.fillStyle = "rgba(110,110,110,.3)"; g.fillRect(L, y - 56, W, 2);
    stMono(g, r.k, L, y - 18, 22, "#9A9A9A", 4);
    stDisp(g, r.v, L, y + 36, 56, r.lime ? "#C6FF00" : "#F2F2F2", W);
    y += 180;
  });

  stMono(g, d.foot || "", L, 1920 - 150, 26, "#FF2E88", 5);
  g.font = '700 26px "JetBrains Mono", monospace'; g.fillStyle = "#9A9A9A";
  const t = d.rankLine || "";
  g.fillText(t, R - g.measureText(t).width, 1920 - 150);
  return c.toDataURL("image/png");
}

function RecapStorySheet({ open, onClose }) {
  const [url, setUrl] = React.useState("");
  const [flash, setFlash] = React.useState("");
  React.useEffect(() => {
    if (!open) return;
    let alive = true;
    document.fonts.ready.then(() => { if (alive) setUrl(drawRecapStory(open)); });
    return () => { alive = false; };
  }, [open]);
  if (!open) return null;
  const save = async () => {
    try {
      const blob = await (await fetch(url)).blob();
      const f = new File([blob], "blackout-recap.png", { type: "image/png" });
      if (navigator.canShare && navigator.canShare({ files: [f] })) {
        await navigator.share({ files: [f], title: "Blackout Series" }); return;
      }
    } catch (e) { if (e && e.name === "AbortError") return; }
    const a = document.createElement("a");
    a.href = url; a.download = "blackout-recap.png";
    document.body.appendChild(a); a.click(); a.remove();
    setFlash("SAVED"); setTimeout(() => setFlash(""), 1600);
  };
  return (
    <div onClick={onClose} style={{ position: "fixed", inset: 0, zIndex: 95,
      background: "rgba(5,5,5,.92)", display: "flex", alignItems: "flex-end" }}>
      <div onClick={e => e.stopPropagation()} style={{ background: "#0A0A0A", width: "100%",
        maxHeight: "94vh", overflowY: "auto", borderTop: "3px solid #C6FF00", padding: 16 }}>
        <div style={{ display: "flex", justifyContent: "center", margin: "6px 0 14px" }}>
          {url ? <img src={url} alt="" style={{ width: 260, height: 462, display: "block",
                        border: "1px solid rgba(110,110,110,.3)" }} />
               : <div style={{ width: 260, height: 462, background: "#111" }} />}
        </div>
        <button onClick={save} style={{ width: "100%", padding: 16, background: "#C6FF00",
          color: "#050505", border: "none", cursor: "pointer",
          fontFamily: "'JetBrains Mono',monospace", fontWeight: 700, fontSize: 11,
          letterSpacing: ".2em" }}>SHARE / SAVE</button>
        {flash && <div style={{ textAlign: "center", color: "#C6FF00", marginTop: 10,
          fontFamily: "'JetBrains Mono',monospace", fontSize: 11 }}>{flash}</div>}
        <button onClick={onClose} style={{ width: "100%", marginTop: 10, padding: 12,
          background: "transparent", color: "#6E6E6E", border: "none", cursor: "pointer",
          fontFamily: "'JetBrains Mono',monospace", fontSize: 11,
          letterSpacing: ".14em" }}>CLOSE</button>
      </div>
    </div>
  );
}

"""


# The sheet itself, replacing Vol.8's. It is the same screen with a toggle on
# top: EVERYONE is what Vol.8 already showed, extended; MY NIGHT is the half the
# social handoff adds. The last tab used is remembered, as the handoff asks.
RECAP_SHEET = r"""
function RecapSheet({ session, state, leaderboard, meId, onClose, onOpenSession }) {
  if (!session) return null;
  const [tab, setTab] = React.useState(() => {
    try { return localStorage.getItem("bo_recap_tab") || "mine"; } catch (e) { return "mine"; }
  });
  const [story, setStory] = React.useState(null);
  React.useEffect(() => {
    try { localStorage.setItem("bo_recap_tab", tab); } catch (e) {}
  }, [tab]);

  const nameOf = id => (state.players.find(p => p.id === id) || {}).name || "?";
  const teamName = tid => {
    const t = (session.teams || []).find(x => x.id === tid);
    return t ? nameOf(t.p1Id) + " & " + nameOf(t.p2Id) : "-";
  };
  const f = session.bracket && session.bracket.final;
  const champTid = f && f.winner ? (f.winner === "team1" ? f.team1Id : f.team2Id) : null;
  const idx = (state.sessions || []).findIndex(s => s.id === session.id);

  const nightOf = pid => {
    const r = calcPlayerNights(pid, (state.sessions || []).slice(0, idx + 1), () => "");
    const n = r.nights.find(x => x.idx === idx);
    return n ? n.nightTotal : 0;
  };
  const inIt = (state.players || []).filter(p => getPlayerTeam(session, p.id));
  const scored = inIt.map(p => ({ p, pts: nightOf(p.id) })).sort((a, b) => b.pts - a.pts);
  const topScorer = scored[0];

  const all = (session.groupMatches || []).concat((session.bracket || {}).qf || [],
    (session.bracket || {}).sf || [], f ? [f] : []).filter(m => m && m.winner && m.score);
  const biggest = all.map(m => {
    const w = m.winner === "team1" ? m.team1Id : m.team2Id;
    return { m, w, margin: Math.abs(m.score.t1 - m.score.t2) };
  }).sort((x, y) => y.margin - x.margin)[0];

  const votes = session.mvpVotes || {};
  const mvpId = Object.keys(votes).sort((a, b) => (votes[b] || 0) - (votes[a] || 0))[0];

  // My story: the handoff's three stat rows, filled from the night.
  const mineStory = d => {
    const wins = d.games.filter(g => g.won).length;
    const best = d.games.filter(g => g.won)
      .sort((a, b) => parseInt(b.score) - parseInt(a.score))[0];
    const far = d.games.some(g => g.stage === "FINAL") ? "REACHED THE FINAL"
              : d.games.some(g => g.stage === "SEMI-FINAL") ? "REACHED SEMI-FINAL"
              : d.games.some(g => g.stage === "QUARTER-FINAL") ? "REACHED THE QUARTERS"
              : "GROUP STAGE";
    setStory({
      no: idx + 1, who: (nameOf(meId) || "").split(" ")[0],
      record: wins + "-" + (d.games.length - wins),
      rows: [
        { k: "POINTS", v: "+" + (d.ptsNow - d.ptsWas), lime: true },
        { k: "HOW FAR", v: far },
        best ? { k: "BEST WIN", v: best.score + " VS " + best.opponents[0].toUpperCase() } : null,
      ].filter(Boolean),
      foot: "SESSION " + (idx + 1) + " \u00b7 " + fmtNightDate(session.date).toUpperCase(),
      rankLine: d.rankNow ? "#" + d.rankNow + " OF " + d.total : "",
    });
  };

  const groupStory = sum => setStory({
    no: idx + 1, who: sum.final ? sum.final.winners.toUpperCase() : "THE NIGHT",
    record: sum.final ? sum.final.score : "",
    rows: [
      { k: "PLAYERS", v: String(sum.playerCount) },
      { k: "GAMES", v: String(sum.gameCount) },
      sum.closest ? { k: "CLOSEST", v: sum.closest.score, lime: true } : null,
    ].filter(Boolean),
    foot: "SESSION " + (idx + 1) + " \u00b7 " + fmtNightDate(session.date).toUpperCase(),
    rankLine: sum.tiebreaks + (sum.tiebreaks === 1 ? " TIEBREAK" : " TIEBREAKS"),
  });

  return (
    <div onClick={onClose} style={{ position: "fixed", inset: 0, zIndex: 80,
      background: "rgba(5,5,5,.88)", display: "flex", alignItems: "flex-end" }}>
      <div onClick={e => e.stopPropagation()} style={{ background: "#0A0A0A", width: "100%",
        maxHeight: "90vh", overflowY: "auto", borderTop: "3px solid #C6FF00", padding: 16 }}>
        <div style={{ fontFamily: "'JetBrains Mono',monospace", fontWeight: 700, fontSize: 10,
          letterSpacing: ".26em", color: "#9A9A9A" }}>
          <BoMark size={13} style={{ display: "inline-block", verticalAlign: "-2px", marginRight: 7 }} />
          SESSION {idx + 1} &middot; {fmtNightDate(session.date)}{session.doublePoints ? " \u00b7 2X NIGHT" : ""}
        </div>
        <div style={{ fontStyle: "italic", fontVariationSettings: "'wdth' 125,'wght' 900",
          fontSize: 44, lineHeight: .9, marginTop: 6 }}>SESSION {idx + 1}<br />RECAP</div>

        <RecapToggle tab={tab} setTab={setTab} />

        {tab === "mine"
          ? <RecapMine session={session} state={state} meId={meId} idx={idx} onShare={mineStory} />
          : <RecapEveryone session={session} state={state} meId={meId} idx={idx}
              nameOf={nameOf} teamName={teamName} champTid={champTid} f={f}
              mvpId={mvpId} votes={votes} topScorer={topScorer} biggest={biggest}
              inIt={inIt} onShare={groupStory} />}

        {onOpenSession && (
          <button onClick={onOpenSession} style={{ width: "100%", marginTop: 16, padding: "14px",
            background: "transparent", border: "1px solid rgba(198,255,0,.4)", color: "#C6FF00",
            fontFamily: "'JetBrains Mono',monospace", fontWeight: 700, fontSize: 11,
            letterSpacing: ".24em", cursor: "pointer" }}>FULL RESULTS &#9654;</button>
        )}
        <button onClick={onClose} style={{ width: "100%", marginTop: 10, padding: "14px",
          background: "transparent", border: "1px solid rgba(110,110,110,.4)", color: "#9A9A9A",
          fontFamily: "'JetBrains Mono',monospace", fontWeight: 700, fontSize: 11,
          letterSpacing: ".24em", cursor: "pointer" }}>CLOSE</button>
      </div>
      <RecapStorySheet open={story} onClose={() => setStory(null)} />
    </div>
  );
}
"""
