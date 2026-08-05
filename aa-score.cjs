function getPlayerTeam(s, pid) { return (s.teams || []).find(t => t.p1Id === pid || t.p2Id === pid); }
function teamWon(m, tid) { if (!m || !m.winner) return false; if (m.winner === "team1") return m.team1Id === tid; if (m.winner === "team2") return m.team2Id === tid; return false; }

// Points baseline for the SERIES leaderboard only: a group of 4 plays 3
// matches, so only each team's best GROUP_COUNTED_GAMES results earn series
// points. A 5-team group therefore drops its lowest game and cannot out-earn a
// group of 4. This does NOT touch the group table below — group standings use
// every match played, so qualification is decided on real results.
const GROUP_COUNTED_GAMES = 3;

function teamGroupResults(session, teamId) {
  const out = [];
  (session.groupMatches || []).forEach(m => {
    if (m.team1Id !== teamId && m.team2Id !== teamId) return;
    if (!m.winner) return;
    const isT1 = m.team1Id === teamId;
    const won = teamWon(m, teamId);
    const lt = m.lossType || "tiebreak";
    out.push({
      pts: won ? 3 : (lt === "tiebreak" ? 2 : lt === "competitive" ? 1 : 0),
      w: won ? 1 : 0,
      gf: m.score ? (isT1 ? m.score.t1 : m.score.t2) : 0,
      ga: m.score ? (isT1 ? m.score.t2 : m.score.t1) : 0,
    });
  });
  const playedActual = out.length;
  out.sort((a, b) => b.pts - a.pts || (b.gf - b.ga) - (a.gf - a.ga) || b.gf - a.gf);
  return { all: out, counted: out.slice(0, GROUP_COUNTED_GAMES), playedActual };
}

// GROUP TABLE — every match played counts. This is the real standing and it is
// what decides top-of-group and who qualifies.
function calcGroupStandings(session, group) {
  const teams = (session.teams || []).filter(t => t.group === group);
  const matchList = session.groupMatches || [];
  const rows = teams.map(team => {
    let pts = 0, wins = 0, played = 0, gf = 0, ga = 0;
    matchList.forEach(m => {
      if (m.team1Id !== team.id && m.team2Id !== team.id) return;
      if (!m.winner) return;
      played++;
      const isT1 = m.team1Id === team.id;
      if (m.score) { gf += isT1 ? m.score.t1 : m.score.t2; ga += isT1 ? m.score.t2 : m.score.t1; }
      if (teamWon(m, team.id)) { pts += 3; wins++; }
      else { const t = m.lossType || "tiebreak"; if (t === "tiebreak") pts += 2; else if (t === "competitive") pts += 1; }
    });
    return { team, pts, wins, played, gf, ga, gd: gf - ga };
  });
  const h2h = {};
  matchList.forEach(m => {
    if (!m.winner) return;
    const wid = m.winner === "team1" ? m.team1Id : m.team2Id;
    const lid = m.winner === "team1" ? m.team2Id : m.team1Id;
    if (!h2h[wid]) h2h[wid] = {};
    h2h[wid][lid] = (h2h[wid][lid] || 0) + 1;
  });
  return rows.sort((a, b) => {
    if (b.wins !== a.wins) return b.wins - a.wins;   // 1) most wins
    if (b.gd !== a.gd) return b.gd - a.gd;           // 2) game difference
    if (b.gf !== a.gf) return b.gf - a.gf;           // 3) games won
    const aH = (h2h[a.team.id]?.[b.team.id] || 0) - (h2h[b.team.id]?.[a.team.id] || 0);
    if (aH !== 0) return -aH;                        // 4) head-to-head
    return b.pts - a.pts;
  });
}

function scoreToResult(s1, s2) {
  if (s1 === s2 || (s1 === null || s2 === null)) return { winner: null, lossType: null };
  const [winScore, loseScore] = s1 > s2 ? [s1, s2] : [s2, s1];
  const lossType = (loseScore <= 1) ? "blowout" : (loseScore === 5) ? "tiebreak" : "competitive";
  return { winner: s1 > s2 ? "team1" : "team2", lossType, score: { t1: s1, t2: s2 } };
}

function getTopOfGroup(s, g) { const ov = s.topOfGroupOverride && s.topOfGroupOverride[g]; if (ov) return ov; const r = calcGroupStandings(s, g); return r[0]?.team?.id || null; }

// Returns standings for a group NORMALISED to the session's smallest group size:
// each team keeps only its best (minGroupSize − 1) results, so every team across
// differently-sized groups is compared on the same number of matches. In a 5/5/4
// session that means everyone is ranked on their best 3 games — the group-of-5
// teams drop their single worst result, the group-of-4 teams are unchanged.
// Used for KNOCKOUT SEEDING only; the displayed group table and leaderboard are
// handled separately.
// KO SEEDING ONLY — when groups are UNEVEN (e.g. 5/5/4) teams have played a
// different number of matches, so ranking them against each other across groups
// is unfair. In that case rank everyone on the smallest group's match count
// (larger groups drop their lowest). Equal-size groups need no adjustment and
// use the real table.
function calcGroupStandingsNormalized(session, group) {
  const teams = (session.teams || []).filter(t => t.group === group);
  const sizes = getSessionGroups(session)
    .map(g => (session.teams || []).filter(t => t.group === g).length)
    .filter(n => n > 0);
  const uneven = sizes.length > 1 && new Set(sizes).size > 1;
  if (!uneven) return calcGroupStandings(session, group);
  const keep = Math.max(1, Math.min(...sizes) - 1);
  const rows = teams.map(team => {
    const best = teamGroupResults(session, team.id).all.slice(0, keep);
    let pts = 0, wins = 0, gf = 0, ga = 0;
    best.forEach(r => { pts += r.pts; wins += r.w; gf += r.gf; ga += r.ga; });
    return { team, pts, wins, played: best.length, gf, ga, gd: gf - ga };
  });
  return rows.sort((a, b) => b.wins - a.wins || b.gd - a.gd || b.gf - a.gf || b.pts - a.pts);
}

// Equalizes 3rd-place entries for cross-group comparison by adding ghost BYE wins
// (+3 pts each) for teams in smaller groups to normalize to the largest group's match count.
function equalizeThirds(thirds, session) {
  const groups = getSessionGroups(session);
  const groupSizes = {};
  groups.forEach(g => { groupSizes[g] = (session.teams || []).filter(t => t.group === g).length; });
  const maxPerTeam = Math.max(...Object.values(groupSizes)) - 1;
  return thirds.map(t => {
    const g = (session.teams || []).find(tm => tm.id === t.id)?.group;
    const missing = maxPerTeam - ((groupSizes[g] || maxPerTeam + 1) - 1);
    // Ghost BYE win: +1 win, +6 games for (notional 6-0), +6 GD
    return { ...t, wins: t.wins + missing, gd: (t.gd || 0) + missing * 6, gf: (t.gf || 0) + missing * 6, ghostWins: missing };
  });
}

// Compare two thirds entries: wins → GD → GF (padel tiebreaker order)
function compareThirds(a, b) {
  return b.wins - a.wins || b.gd - a.gd || b.gf - a.gf;
}

function calcStreak(idxs) {
  if (!idxs?.length) return 0;
  const sorted = [...idxs].sort((a, b) => a - b);
  let total = 0, len = 0, last = null;
  for (const i of sorted) {
    if (last === null || i === last + 1) len++; else len = 1;
    last = i;
    // len=1: no bonus (first session alone doesn't count)
    // len=2: +1, len=3: +1, len=4: jackpot +3
    if (len === 2 || len === 3) total += 1;
    else if (len >= 4) total += 3;
  }
  return Math.min(total, 5);
}

function koMatchPts(match, teamId) {
  if (teamWon(match, teamId)) return 3;
  const t = match.lossType || "tiebreak";
  return t === "tiebreak" ? 2 : t === "competitive" ? 1 : 0;
}

function calcPlayerStats(pid, sessions) {
  let total = 0;
  const breakdown = { matchPts: 0, topOfGroup: 0, knockoutPts: 0, streakPts: 0, comebackPts: 0 };
  const stats = { groupWins: 0, groupPlayed: 0, sessionsPlayed: 0, qfReached: 0, qfWins: 0, sfReached: 0, sfWins: 0, finalsReached: 0, finalsWon: 0 };
  const attended = [];
  const partners = {};
  sessions.forEach((s, idx) => {
    const team = getPlayerTeam(s, pid); if (!team) return;
    stats.sessionsPlayed++;
    const partnerId = team.p1Id === pid ? team.p2Id : team.p1Id;
    partners[partnerId] = (partners[partnerId] || 0) + 1;
    // 2X Double Points (applies to everything except streak)
    const mult = s.doublePoints ? 2 : 1;
    let sessionPlayed = 0;
    // Group scoring is normalised to the group-of-4 baseline: only each team's
    // best GROUP_COUNTED_GAMES (3) results count toward series points, so a
    // 5-team group (4 matches) drops its lowest and the maximum matches a group
    // of 4. Win/played records below stay actual. Knockout and playoff matches
    // are not group matches, so they never enter this calculation.
    (s.groupMatches || []).forEach(m => {
      if (m.team1Id !== team.id && m.team2Id !== team.id) return;
      if (!m.winner) return;
      stats.groupPlayed++; sessionPlayed++;
      if (teamWon(m, team.id)) stats.groupWins++;
    });
    teamGroupResults(s, team.id).counted.forEach(r => {
      total += r.pts * mult; breakdown.matchPts += r.pts * mult;
    });
    // Only award top-of-group if team actually played matches
    if (sessionPlayed > 0 && getTopOfGroup(s, team.group) === team.id) { total += 1 * mult; breakdown.topOfGroup += 1 * mult; }
    // Only count streak if player actually played a match this session
    if (sessionPlayed > 0) {
      // Comeback bonus: +2 for returning after missing 2+ consecutive sessions
      if (attended.length > 0 && (idx - attended[attended.length - 1]) >= 3) {
        total += 2; breakdown.comebackPts += 2;
      }
      attended.push(idx);
    }
    const qfM = s.bracket?.qf?.find(m => (m.team1Id === team.id || m.team2Id === team.id) && m.winner);
    if (qfM) { stats.qfReached++; if (teamWon(qfM, team.id)) stats.qfWins++; const qp = (1 + koMatchPts(qfM, team.id)) * mult; total += qp; breakdown.knockoutPts += qp; }
    const sfM = s.bracket?.sf?.find(m => (m.team1Id === team.id || m.team2Id === team.id) && m.winner);
    if (sfM) { stats.sfReached++; if (teamWon(sfM, team.id)) stats.sfWins++; const sp = (2 + koMatchPts(sfM, team.id)) * mult; total += sp; breakdown.knockoutPts += sp; }
    const f = s.bracket?.final;
    if (f && (f.team1Id === team.id || f.team2Id === team.id) && f.winner) {
      stats.finalsReached++;
      const fp = (3 + koMatchPts(f, team.id) + (teamWon(f, team.id) ? 5 : 0)) * mult;
      total += fp; breakdown.knockoutPts += fp;
      if (teamWon(f, team.id)) stats.finalsWon++;
    }
  });
  const streak = calcStreak(attended); total += streak; breakdown.streakPts = streak;
  return { totalPts: total, breakdown, stats, attended, partners };
}

// Last n decided results for a player across the series (most recent last),
// as 'W'/'L'. Used for the form strip and hot-streak detection.
function recentForm(pid, sessions, n = 5) {
  const res = [];
  sessions.forEach(s => {
    const team = getPlayerTeam(s, pid); if (!team) return;
    (s.groupMatches || []).forEach(m => {
      if ((m.team1Id === team.id || m.team2Id === team.id) && m.winner) res.push(teamWon(m, team.id) ? "W" : "L");
    });
    ["qf", "sf"].forEach(r => {
      const km = s.bracket?.[r]?.find(m => (m.team1Id === team.id || m.team2Id === team.id) && m.winner);
      if (km) res.push(teamWon(km, team.id) ? "W" : "L");
    });
    const f = s.bracket?.final;
    if (f && (f.team1Id === team.id || f.team2Id === team.id) && f.winner) res.push(teamWon(f, team.id) ? "W" : "L");
  });
  return res.slice(-n);
}

// Current win streak (trailing W count) from a form array.
function currentStreak(form) {
  let n = 0;
  for (let i = form.length - 1; i >= 0; i--) { if (form[i] === "W") n++; else break; }
  return n;
}

function getLockedPartners(pid, sessions) {
  const locked = new Set();
  sessions.forEach(s => {
    const team = getPlayerTeam(s, pid); if (!team) return;
    const partnerId = team.p1Id === pid ? team.p2Id : team.p1Id;
    // Lock only if they WON the final together (session champions)
    const wonFinal = s.bracket?.final && teamWon(s.bracket.final, team.id);
    if (wonFinal) locked.add(partnerId);
  });
  return locked;
}
module.exports={calcPlayerStats,teamGroupResults,calcGroupStandings,getTopOfGroup,
  getPlayerTeam,teamWon,koMatchPts,recentForm,currentStreak,getLockedPartners,GROUP_COUNTED_GAMES};
