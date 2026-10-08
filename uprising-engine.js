/* UPRISING — the engine.
 *
 * Every rule in UPRISING.md lives here and nowhere else. The app inlines this
 * file verbatim (build-uprising-app.py) so that the thing the tests exercise is
 * the thing the browser runs — the one mistake this repo has made more than any
 * other is two copies of the same logic quietly drifting apart.
 *
 * Pure functions, no DOM, no fetch. `node --test uprising-engine.test.js`.
 */

const UP = {
  COURTS: 4,
  ROUNDS: 9,
  FIELD: 16,
  TARGET: 16,            // a match is first to 16 points
  FINAL_MULT: 2,         // the last round is worth double

  // Points are worth more higher up the ladder. Ranking on raw match points
  // would reward farming wins on Court 4, which is the opposite of a format
  // called UPRISING. Losing on Court 1 is worth the same as winning on Court 3:
  // where you got to counts as much as what you did when you got there.
  WIN:  { 1: 8, 2: 6, 3: 4, 4: 2 },
  LOSE: { 1: 4, 2: 3, 3: 2, 4: 1 },
};

// ── helpers ────────────────────────────────────────────────────────────────

function upPairKey(a, b) { return [a, b].sort().join("|"); }

function upCourtSizes(courts) {
  const n = {};
  Object.values(courts).forEach(c => { n[c] = (n[c] || 0) + 1; });
  return n;
}

// ── the opening ladder ─────────────────────────────────────────────────────
//
// Seeded by form, never drawn at random. Measured over 3,000 nights, a random
// opening ladder gives a Court 1 starter 40% of the wins and a Court 4 starter
// 8% — a five-fold swing decided before a ball is hit, which is luck choosing
// who takes a voucher. Seeded, that same 40% is the form player starting where
// they earned it.
//
// `form` is a map of playerId -> number (higher is better). A player with no
// history gets the median, so newcomers start in the middle rather than being
// punished or rewarded for being unknown.
function upSeedLadder(playerIds, form = {}) {
  const known = playerIds.filter(p => typeof form[p] === "number").map(p => form[p]).sort((a, b) => a - b);
  const median = known.length ? known[Math.floor(known.length / 2)] : 0;
  const keyOf = p => (typeof form[p] === "number" ? form[p] : median);
  // Ties broken by id so the ladder is deterministic — the same input must
  // always give the same draw, or a reload reshuffles the night.
  const order = [...playerIds].sort((a, b) => (keyOf(b) - keyOf(a)) || String(a).localeCompare(String(b)));
  const out = {};
  order.forEach((p, i) => { out[p] = 1 + Math.floor(i / 4); });
  return out;
}

// ── pairing within a court ─────────────────────────────────────────────────
//
// Rank the four by running total and pair 1+4 against 2+3: the closest match
// the four of them can produce. There are exactly three ways to split four
// players, so when the closest one would repeat a partnership the next-closest
// split that does not is taken instead.
//
// This yields seven different partners in nine rounds (median; five at worst).
// Not nine — once a group settles on a court, three rounds exhausts the three
// splits. A "one up, one down, two stay" ladder was tested as a way to churn
// membership faster and is worse on both counts, so pairs travel together.
function upPairCourt(ids, totals = {}, seen = new Set()) {
  if (ids.length !== 4) throw new Error(`a court needs exactly 4 players, got ${ids.length}`);
  const t = p => totals[p] || 0;
  const on = [...ids].sort((a, b) => (t(b) - t(a)) || String(a).localeCompare(String(b)));
  const splits = [
    [[on[0], on[3]], [on[1], on[2]]],   // 1+4 v 2+3 — the closest match
    [[on[0], on[2]], [on[1], on[3]]],
    [[on[0], on[1]], [on[2], on[3]]],
  ];
  const fresh = splits.find(([A, B]) => !seen.has(upPairKey(...A)) && !seen.has(upPairKey(...B)));
  return fresh || splits[0];
}

// ── scoring ────────────────────────────────────────────────────────────────

function upRoundPoints(court, won, isFinalRound) {
  const base = won ? UP.WIN[court] : UP.LOSE[court];
  if (base == null) throw new Error(`no points defined for court ${court}`);
  return base * (isFinalRound ? UP.FINAL_MULT : 1);
}

function upMatchDone(m) {
  return m && Number.isFinite(m.score1) && Number.isFinite(m.score2) && m.score1 !== m.score2;
}

function upRoundDone(round) {
  return !!round && (round.courts || []).length > 0 && round.courts.every(upMatchDone);
}

// ── movement ───────────────────────────────────────────────────────────────
//
// The winning pair moves up a court, the losing pair moves down. Court 1
// winners stay on Court 1; Court 4 losers stay on Court 4. This balances
// exactly — each court sends two away and receives two — which `upValidate`
// checks on every round rather than trusting.
function upCourtsAfter(round, before) {
  const next = { ...before };
  (round.courts || []).forEach(m => {
    if (!upMatchDone(m)) return;
    const aWon = m.score1 > m.score2;
    const up = aWon ? m.team1 : m.team2;
    const down = aWon ? m.team2 : m.team1;
    up.forEach(p => { next[p] = Math.max(1, m.court - 1); });
    down.forEach(p => { next[p] = Math.min(UP.COURTS, m.court + 1); });
  });
  return next;
}

// Where everyone stands right now: the opening ladder, moved on by every round
// that has been fully played.
function upCurrentCourts(night) {
  let courts = { ...(night.ladder0 || {}) };
  (night.rounds || []).forEach(r => { if (upRoundDone(r)) courts = upCourtsAfter(r, courts); });
  return courts;
}

// Every partnership used so far, so the pairing rule can avoid repeats.
function upSeenPairs(night) {
  const seen = new Set();
  (night.rounds || []).forEach(r => (r.courts || []).forEach(m => {
    if (m.team1) seen.add(upPairKey(...m.team1));
    if (m.team2) seen.add(upPairKey(...m.team2));
  }));
  return seen;
}

// ── building the next round ────────────────────────────────────────────────

function upBuildRound(night) {
  const rounds = night.rounds || [];
  const last = rounds[rounds.length - 1];
  if (last && !upRoundDone(last)) throw new Error("the previous round is not finished");
  if (rounds.length >= UP.ROUNDS) throw new Error("the night is already nine rounds long");

  const courts = upCurrentCourts(night);
  const totals = upTotals(night);
  const seen = upSeenPairs(night);
  const out = { roundNum: rounds.length + 1, sitOuts: [], courts: [] };
  for (let c = 1; c <= UP.COURTS; c++) {
    const on = Object.keys(courts).filter(p => courts[p] === c);
    if (on.length !== 4) throw new Error(`court ${c} has ${on.length} players, not 4`);
    const [A, B] = upPairCourt(on, totals, seen);
    seen.add(upPairKey(...A)); seen.add(upPairKey(...B));
    out.courts.push({ court: c, team1: A, team2: B, score1: null, score2: null });
  }
  return out;
}

// ── standings ──────────────────────────────────────────────────────────────

function upPlayerIds(night) {
  return night.playerIds || (night.players || []).map(p => p.id);
}

function upTotals(night) {
  const total = {};
  upPlayerIds(night).forEach(id => { total[id] = 0; });
  (night.rounds || []).forEach(r => (r.courts || []).forEach(m => {
    if (!upMatchDone(m)) return;
    const isFinal = r.roundNum === UP.ROUNDS;
    const aWon = m.score1 > m.score2;
    m.team1.forEach(p => { total[p] = (total[p] || 0) + upRoundPoints(m.court, aWon, isFinal); });
    m.team2.forEach(p => { total[p] = (total[p] || 0) + upRoundPoints(m.court, !aWon, isFinal); });
  }));
  return total;
}

// The full table. `baseline` is a player's own running average from previous
// nights; a first-timer has none and is given the field average for tonight,
// which is deliberately generous — a newcomer being able to win THE CLIMB on
// their first night is the point of a format built to convert newcomers.
function upStandings(night, byId = {}, baselines = {}) {
  const total = upTotals(night);
  const courts = upCurrentCourts(night);
  const start = night.ladder0 || {};
  const match = {}, against = {}, wins = {}, played = {}, partners = {};
  upPlayerIds(night).forEach(id => {
    match[id] = 0; against[id] = 0; wins[id] = 0; played[id] = 0; partners[id] = new Set();
  });
  (night.rounds || []).forEach(r => (r.courts || []).forEach(m => {
    if (!upMatchDone(m)) return;
    const aWon = m.score1 > m.score2;
    m.team1.forEach(p => { match[p] += m.score1; against[p] += m.score2; played[p]++; if (aWon) wins[p]++; });
    m.team2.forEach(p => { match[p] += m.score2; against[p] += m.score1; played[p]++; if (!aWon) wins[p]++; });
    partners[m.team1[0]].add(m.team1[1]); partners[m.team1[1]].add(m.team1[0]);
    partners[m.team2[0]].add(m.team2[1]); partners[m.team2[1]].add(m.team2[0]);
  }));

  const scored = upPlayerIds(night).filter(id => played[id] > 0);
  const fieldAvg = scored.length
    ? scored.reduce((s, id) => s + total[id], 0) / scored.length : 0;

  const rows = upPlayerIds(night).map(id => {
    // A baseline can arrive on the player record or in the `baselines` map the
    // app builds from previous nights. Resolved into a local, never written
    // back onto the caller's objects — upStandings is called on every render.
    const p = (night.players || []).find(x => x.id === id) || {};
    const own = Number.isFinite(p.baseline) ? p.baseline
              : Number.isFinite(baselines[id]) ? baselines[id] : null;
    const base = own == null ? fieldAvg : own;
    return {
      id,
      name: p.name || (byId[id] || {}).name || "?",
      photoUrl: p.photoUrl || (byId[id] || {}).photoUrl || "",
      total: total[id] || 0,
      matchPts: match[id] || 0,
      // Real wins and a real game difference. The table showed "0 WON" beside
      // a player on 80 points because the engine never counted either, and the
      // app's row was rendering match points under a "+" as if they were a
      // difference.
      wins: wins[id] || 0,
      diff: (match[id] || 0) - (against[id] || 0),
      played: played[id] || 0,
      court: courts[id] || start[id] || UP.COURTS,
      startCourt: start[id] || UP.COURTS,
      partners: [...partners[id]],
      baseline: base,
      firstTimer: own == null,
      vsBaseline: (total[id] || 0) - base,
    };
  });
  // CHAMPION: most points, match points break the tie.
  rows.sort((x, y) => (y.total - x.total) || (y.matchPts - x.matchPts)
                      || String(x.name).localeCompare(String(y.name)));
  rows.forEach((r, i) => { r.rank = i + 1; });
  return rows;
}

// The two prizes. CHAMPION is scratch and is won on merit; THE CLIMB is the
// handicap and is open to anyone — measured at 21% of nights going to a top-3
// player, against 70% for scratch alone.
function upPrizes(night, byId = {}, baselines = {}) {
  const rows = upStandings(night, byId, baselines);
  const eligible = rows.filter(r => r.played > 0);
  if (!eligible.length) return { champion: null, climb: null };
  const champion = eligible[0];
  const climb = [...eligible].sort((a, b) => (b.vsBaseline - a.vsBaseline)
                                             || (b.total - a.total))[0];
  return { champion, climb };
}

// Each player's court after every round — the line that makes the share card.
function upClimbPath(night, playerId) {
  const path = [night.ladder0 ? night.ladder0[playerId] : UP.COURTS];
  let courts = { ...(night.ladder0 || {}) };
  (night.rounds || []).forEach(r => {
    if (!upRoundDone(r)) return;
    courts = upCourtsAfter(r, courts);
    path.push(courts[playerId]);
  });
  return path;
}

// ── the invariant ──────────────────────────────────────────────────────────
//
// Four to a court, always. If this ever fails the night is unplayable, so it is
// checked rather than assumed — the simulation that designed this format had a
// bug that moved players between courts while still iterating over courts, and
// it silently skipped rounds instead of crashing.
function upValidate(night) {
  const bad = [];
  const ids = upPlayerIds(night);
  if (new Set(ids).size !== ids.length) bad.push("a player appears twice");
  if (ids.length && ids.length % 4 !== 0) bad.push(`${ids.length} players is not a multiple of 4`);

  const sizes0 = upCourtSizes(night.ladder0 || {});
  Object.entries(sizes0).forEach(([c, n]) => {
    if (n !== 4) bad.push(`opening ladder: court ${c} has ${n}`);
  });

  let courts = { ...(night.ladder0 || {}) };
  (night.rounds || []).forEach(r => {
    const onCourt = {};
    (r.courts || []).forEach(m => {
      [...(m.team1 || []), ...(m.team2 || [])].forEach(p => {
        if (onCourt[p]) bad.push(`round ${r.roundNum}: ${p} is on two courts`);
        onCourt[p] = m.court;
      });
      if (new Set([...(m.team1 || []), ...(m.team2 || [])]).size !== 4)
        bad.push(`round ${r.roundNum} court ${m.court}: not four distinct players`);
      // NOT `upMatchDone(m) && m.score1 === m.score2` — upMatchDone already requires the
      // scores to differ, so that condition can never be true and the check was
      // dead code. A draw is exactly the case where a match has two scores and
      // no winner, which is what has to be caught.
      if (Number.isFinite(m.score1) && Number.isFinite(m.score2) && m.score1 === m.score2)
        bad.push(`round ${r.roundNum} court ${m.court}: drawn match`);
    });
    if (upRoundDone(r)) {
      courts = upCourtsAfter(r, courts);
      Object.entries(upCourtSizes(courts)).forEach(([c, n]) => {
        if (n !== 4) bad.push(`after round ${r.no}: court ${c} has ${n}`);
      });
    }
  });
  return bad;
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = {
    UP, upPlayerIds, upSeedLadder, upPairCourt, upRoundPoints, upMatchDone, upRoundDone,
    upCourtsAfter, upCurrentCourts, upSeenPairs, upBuildRound, upTotals,
    upStandings, upPrizes, upClimbPath, upValidate, upPairKey,
  };
}
