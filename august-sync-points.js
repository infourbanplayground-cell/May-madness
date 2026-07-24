// Seed/sync August Attack points from July Heat. Idempotent:
//  - first run seeds August with the July Heat roster + points (+ profile photos)
//  - re-run at July Heat's finish updates each player's "July Heat" series points
// Never touches July Heat data or August sessions.
require("dotenv").config({ path: "/opt/august-attack-api/.env" });
const { Pool } = require("pg");
const pool = new Pool({ connectionString: process.env.DATABASE_URL });
const GROUPS = ["A", "B", "C", "D"];
function getSessionGroups(session) {
  return GROUPS.slice(0, session?.groupCount || 4);
}
function getQualifyCount(session) {
  return session?.qualifyCount || 2;  // default: top 2 per group qualify
}

function getPlayerTeam(s, pid) { return (s.teams || []).find(t => t.p1Id === pid || t.p2Id === pid); }
function teamWon(m, tid) { if (!m || !m.winner) return false; if (m.winner === "team1") return m.team1Id === tid; if (m.winner === "team2") return m.team2Id === tid; return false; }

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
  // h2h wins map
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
    if (b.gf !== a.gf) return b.gf - a.gf;           // 3) points scored
    const aH = (h2h[a.team.id]?.[b.team.id] || 0) - (h2h[b.team.id]?.[a.team.id] || 0);
    if (aH !== 0) return -aH; // 4) head-to-head fallback
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
function calcGroupStandingsNormalized(session, group) {
  const teams = (session.teams || []).filter(t => t.group === group);
  const matchList = session.groupMatches || [];
  const sizes = getSessionGroups(session)
    .map(g => (session.teams || []).filter(t => t.group === g).length)
    .filter(n => n > 0);
  const minSize = sizes.length ? Math.min(...sizes) : teams.length;
  // If this group is already at the smallest size, there is nothing to drop.
  if (teams.length <= minSize) return calcGroupStandings(session, group);
  const keep = Math.max(1, minSize - 1);   // matches to count per team
  const rows = teams.map(team => {
    const myMatches = matchList.filter(m => (m.team1Id === team.id || m.team2Id === team.id) && m.winner);
    const scored = myMatches.map(m => {
      const isT1 = m.team1Id === team.id;
      const won = teamWon(m, team.id);
      const pts = won ? 3 : (m.lossType === "tiebreak" ? 2 : m.lossType === "competitive" ? 1 : 0);
      return { pts, gf: m.score ? (isT1 ? m.score.t1 : m.score.t2) : 0, ga: m.score ? (isT1 ? m.score.t2 : m.score.t1) : 0, w: won ? 1 : 0 };
    });
    // Keep the best `keep` results: sort best-first (pts, then game difference), drop the rest.
    scored.sort((a, b) => b.pts - a.pts || (b.gf - b.ga) - (a.gf - a.ga) || b.gf - a.gf);
    const best = scored.slice(0, keep);
    let pts = 0, wins = 0, gf = 0, ga = 0;
    best.forEach(s => { pts += s.pts; wins += s.w; gf += s.gf; ga += s.ga; });
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
    // Uneven-group fairness: when a session's groups differ in size (e.g. 5/5/4),
    // teams in the larger groups play more group matches and would otherwise bank
    // extra series points. Cap each team's counted group results to (smallest
    // group − 1) — everyone contributes the same number of best results, dropping
    // their lowest. Equal-size sessions are unaffected (cap = all matches).
    const grpSizes = {};
    (s.teams || []).forEach(t => { if (t.group != null) grpSizes[t.group] = (grpSizes[t.group] || 0) + 1; });
    const sizeVals = Object.values(grpSizes);
    const uneven = sizeVals.length > 1 && new Set(sizeVals).size > 1;
    const cap = uneven ? Math.max(1, Math.min(...sizeVals) - 1) : Infinity;
    const grpResults = [];
    (s.groupMatches || []).forEach(m => {
      if (m.team1Id !== team.id && m.team2Id !== team.id) return;
      if (!m.winner) return; stats.groupPlayed++; sessionPlayed++;
      const won = teamWon(m, team.id);
      if (won) stats.groupWins++;
      const lt = m.lossType || "tiebreak";
      grpResults.push(won ? 3 : (lt === "tiebreak" ? 2 : lt === "competitive" ? 1 : 0));
    });
    // Keep each player's best `cap` group results toward series points (record
    // counts above stay actual; only the points contribution is normalized).
    grpResults.sort((a, b) => b - a);
    const counted = cap === Infinity ? grpResults : grpResults.slice(0, cap);
    counted.forEach(pts => { total += pts * mult; breakdown.matchPts += pts * mult; });
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

(async () => {
  const jh = (await pool.query("SELECT data FROM jh_tournament_state WHERE id=1")).rows[0]?.data || {};
  const jhPlayers = jh.players || [], jhSessions = jh.sessions || [];
  const totals = {};
  jhPlayers.forEach(p => { totals[p.id] = calcPlayerStats(p.id, jhSessions).totalPts; });

  const aaRow = (await pool.query("SELECT data, version FROM aa_tournament_state WHERE id=1")).rows[0];
  let aa = aaRow?.data; const version = aaRow?.version ?? 0;
  if (!aa || !aa.players) {
    aa = { seasonName: "AUGUST ATTACK", seasonSubtitle: "URBAN SOCIAL SERIES · VOL. 6",
      seasonTagline: "Serve First. Strike Hard.",
      prevSeriesNames: ["April Clash","Midnight Madness","Midnight Rally","June Fury","July Heat"],
      players: [], sessions: [] };
  }
  const byId = new Map(aa.players.map(p => [p.id, p]));
  let added = 0, updated = 0;
  jhPlayers.forEach(jp => {
    const total = totals[jp.id] || 0;
    let ap = byId.get(jp.id);
    if (!ap) { ap = { id: jp.id, name: jp.name, addedAt: jp.addedAt || Date.now(), photoUrl: jp.photoUrl || "", prevSeriesPts: {} }; aa.players.push(ap); byId.set(jp.id, ap); added++; }
    else updated++;
    ap.prevSeriesPts = { ...(jp.prevSeriesPts || {}), "July Heat": total };
  });

  const newVersion = version + 1;
  await pool.query("UPDATE aa_tournament_state SET data=$1, version=$2, updated_at=NOW() WHERE id=1", [aa, newVersion]);
  await pool.query("INSERT INTO aa_state_history (data, player_ct, match_ct, role) VALUES ($1,$2,$3,$4)",
    [aa, aa.players.length, 0, "points-sync"]).catch(()=>{});
  // best-effort: carry player profile photos
  try { await pool.query("INSERT INTO aa_player_photos SELECT * FROM jh_player_photos ON CONFLICT DO NOTHING"); } catch (e) { console.log("photo copy skipped:", e.message); }

  console.log(`Sync OK. players +${added} new / ${updated} updated. version ${version}->${newVersion}`);
  console.log("Top July Heat points carried:");
  jhPlayers.map(p=>({n:p.name,t:totals[p.id]||0})).sort((a,b)=>b.t-a.t).slice(0,6).forEach(x=>console.log("   "+x.n+": "+x.t));
  await pool.end();
})().catch(e => { console.error("SYNC FAILED:", e); process.exit(1); });
