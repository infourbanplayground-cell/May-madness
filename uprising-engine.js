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

// UP.COURTS and UP.ROUNDS describe the 16-player night the format was designed
// around. A real social is whoever turns up, so every rule below reads the
// night's own numbers and falls back to those constants.
// Capped at UP.COURTS, and that cap is not arbitrary: the points table has
// exactly four rungs (8/6/4/2 over 4/3/2/1), so a fifth court has no points
// defined for it. 20 players would otherwise ask for 5 courts and the night
// would throw on the first round. The club has four courts anyway — the ladder
// is as tall as the venue.
function upCourts(night) {
  const most = Math.min(Math.floor(upPlayerIds(night).length / 4), UP.COURTS);
  const want = night.courtCount || most;
  // Two is the floor wherever the field allows it: a one-court "ladder" has
  // nowhere to climb to, and with 8 players minimum there is always a second
  // court to fill.
  return Math.max(Math.min(2, most), Math.min(want, most));
}
function upRoundsTotal(night) { return night.numRounds || UP.ROUNDS; }

// How many people sit out each round. Four to a court is padel, not a choice —
// but the FIELD does not have to be a multiple of four, it just means somebody
// rests every round.
function upRestCount(night) {
  return Math.max(0, upPlayerIds(night).length - 4 * upCourts(night));
}

// SCORING-round counts at which every player rests exactly the same number of
// times. With P players and R resting each round, N rounds deal N*R rests, so
// they divide evenly exactly when P divides N*R. 9 players want 9 scoring
// rounds, 10 want 5 or 10, 11 want 11. A night with the shuffle runs one round
// longer than the number this returns.
function upFairRounds(playerCount, courts = 0, maxRounds = 14) {
  const C = Math.max(1, Math.min(courts || Math.floor(playerCount / 4),
                                 Math.floor(playerCount / 4), UP.COURTS));
  const R = playerCount - 4 * C;
  if (C < 1) return [];
  if (R === 0) return null;                 // null means "any round count is fair"
  const out = [];
  for (let n = 2; n <= maxRounds; n++) if ((n * R) % playerCount === 0) out.push(n);
  return out;
}

// The last round is worth double — but ONLY when nobody ever sits out.
// Measured over 20,000 nights: with the 2x final on and one player resting
// each round, whoever draws the final-round rest takes 3.6% of the wins
// against the 11.1% that would be their share if it cost nothing. They
// effectively cannot win the night, for a reason they had no say in. With a
// flat final it is 13.6% — slightly generous, which is the right direction for
// a social. So the multiplier is a property of the field, not of the format.
// The last round is worth double only when NOBODY sits it out — somebody who
// is resting the decider could not win it.
//
// Once the final round has been played this reads what actually happened on
// it, not what the night is set to now. Otherwise taking a court away after
// the last round was played would retroactively un-double it and move every
// total on the table, which is the one moment of the night when the numbers
// have to stop moving.
function upDoubleFinal(night) {
  const last = (night.rounds || [])[upRoundsTotal(night) - 1];
  if (last) return (last.sitOuts || []).length === 0;
  return upRestCount(night) === 0;
}

// ── the shuffle ────────────────────────────────────────────────────────────
//
// On night one nobody has form, so the opening ladder is a draw — and a draw
// decides far too much. Measured over 30,000 nights with a random opening
// ladder and 9 scoring rounds, a Court 1 starter takes 45% of the wins and a
// Court 4 starter 6%: a 7.3x swing settled before a ball is hit. Playing a
// longer night barely helps (3.7x at 15 rounds, 2.4x at 25) because the
// advantage compounds rather than washes out.
//
// So round one can be a SHUFFLE: a real match that sets where you start and
// pays nothing. That drops the draw's influence to 2.7x at 9 scoring rounds
// and 2.1x at 15, and what is left is earned — you are on Court 1 because you
// won a match, not because of a hat. It costs one round of time and it is one
// sentence to explain, which is why it beats every seeding scheme that needs
// data we do not have for a room of strangers.
function upScoringRound(night, roundNum) {
  return !(night.shuffle && roundNum === 1);
}
function upScoringRounds(night) {
  return upRoundsTotal(night) - (night.shuffle ? 1 : 0);
}

// ── fitting the night into the evening ─────────────────────────────────────
//
// A round costs roughly PER_POINT minutes a point plus a fixed changeover, so
// the round count follows from the target and the time available rather than
// being guessed at. Measured on 16 players over 4,000 nights per setting, at a
// fixed budget MORE SHORTER rounds beats fewer longer ones every time — at 150
// minutes, 17 rounds of first to 9 correlates 0.893 with true skill where 12
// rounds of first to 13 manages 0.875 — because the ladder needs rounds to
// sort itself and a longer match mostly buys precision you already have.
//
// The changeover is the thing to be honest about: at 2 minutes a 150-minute
// evening holds 18 matches, at 3 minutes only 16. UP_PACE is deliberately a
// little pessimistic so a night finishes early rather than late.
const UP_PACE = { perPoint: 0.68, change: 2.5 };

function upRoundMinutes(target, pace = UP_PACE) {
  return pace.perPoint * target + pace.change;
}
function upNightMinutes(matches, target, pace = UP_PACE) {
  return Math.round(matches * upRoundMinutes(target, pace));
}

// How many SCORING rounds fit in `budget` minutes, given the target and
// whether a shuffle is being played. Snapped to a round count that shares the
// rests evenly when one exists at or below the fit, because an even night that
// finishes early beats an uneven one that uses every minute.
function upPlanRounds(budget, target, opts = {}) {
  const { shuffle = true, players = 16, courts = 0, pace = UP_PACE, min = 4, max = 30 } = opts;
  const matches = Math.floor(budget / upRoundMinutes(target, pace));
  let scoring = matches - (shuffle ? 1 : 0);
  scoring = Math.max(min, Math.min(max, scoring));
  const C = Math.max(1, Math.min(courts || Math.floor(players / 4), Math.floor(players / 4), UP.COURTS));
  const fair = upFairRounds(players, C, max);
  if (fair === null || !fair.length) return scoring;      // nobody rests, or nothing divides
  const under = fair.filter(n => n <= scoring);
  return under.length ? under[under.length - 1] : scoring;
}

// ── who sits out ───────────────────────────────────────────────────────────
//
// A fixed rota, drawn once at the start of the night and walked in order, so
// that when your turn comes it has nothing to do with how you are playing. The
// first attempt at this broke rest ties by ladder position, which quietly gave
// the weak players the early rounds off and the strong players the double final
// off — it measured the tie-break rather than the format.
function upMakeRestRota(playerIds, seed = 1) {
  const ids = [...playerIds];
  let s = (seed >>> 0) || 1;
  const rnd = () => (s = (s * 1664525 + 1013904223) >>> 0) / 4294967296;
  for (let i = ids.length - 1; i > 0; i--) {
    const j = Math.floor(rnd() * (i + 1));
    [ids[i], ids[j]] = [ids[j], ids[i]];
  }
  return ids;
}

function upRestRota(night) {
  const ids = upPlayerIds(night);
  const rota = (night.restRota || []).filter(id => ids.includes(id));
  // Anyone added after the rota was drawn goes on the end rather than being
  // silently exempt from ever resting.
  return [...rota, ...ids.filter(id => !rota.includes(id))];
}

// Who sits out round `roundNum` (1-based). Deterministic: the same night always
// produces the same rota, so a reload cannot reshuffle who is resting.
//
// The shuffle is taken OFF the rota and given the tail of it. If the shuffle
// consumed a normal rota slot, the one player who happened to rest during it
// would spend their rest on a round that pays nothing and so play every
// scoring round, while everyone else played one fewer — 9 players over 9
// rounds came out 8 scoring matches for one person and 7 for the other eight.
// Taking the shuffle off the rota means the scoring rounds, which are the only
// ones that count, divide evenly again.
function upRestingFor(night, roundNum) {
  const R = upRestCount(night);
  if (R <= 0) return [];
  const rota = upRestRota(night);
  const out = [];
  if (night.shuffle && roundNum === 1) {
    for (let i = 0; i < R; i++) out.push(rota[(rota.length - 1 - i + rota.length) % rota.length]);
    return [...new Set(out)];
  }
  const idx = night.shuffle ? roundNum - 2 : roundNum - 1;
  for (let i = 0; i < R; i++) out.push(rota[(idx * R + i) % rota.length]);
  return [...new Set(out)];
}

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
function upSeedLadder(playerIds, form = {}, courtCount = 0) {
  const known = playerIds.filter(p => typeof form[p] === "number").map(p => form[p]).sort((a, b) => a - b);
  const median = known.length ? known[Math.floor(known.length / 2)] : 0;
  const keyOf = p => (typeof form[p] === "number" ? form[p] : median);
  // Ties broken by id so the ladder is deterministic — the same input must
  // always give the same draw, or a reload reshuffles the night.
  const order = [...playerIds].sort((a, b) => (keyOf(b) - keyOf(a)) || String(a).localeCompare(String(b)));
  // Clamped to the courts that actually exist: with 9 players on 2 courts the
  // ninth person is not standing on a Court 3 that nobody is playing on, they
  // are the bottom of Court 2 and the first to sit out.
  const C = courtCount || Math.floor(playerIds.length / 4) || 1;
  const out = {};
  order.forEach((p, i) => { out[p] = Math.min(C, 1 + Math.floor(i / 4)); });
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
// How many courts a round was ACTUALLY played on. A round carries its own
// courts array, so this is a fact about history and not about the night's
// current setting — which is the whole point once the count can change
// mid-night. A court lost at round 6 must not rewrite rounds 1 to 5.
function upRoundCourts(round) {
  return (round && round.courts ? round.courts.length : 0);
}

// The court count in effect for a given round: the round's own if it has been
// built, otherwise whatever the night is set to now.
function upCourtsAt(night, roundNum) {
  const r = (night.rounds || [])[roundNum - 1];
  return upRoundCourts(r) || upCourts(night);
}

function upCourtsAfter(round, before, courtCount = UP.COURTS) {
  const next = { ...before };
  (round.courts || []).forEach(m => {
    if (!upMatchDone(m)) return;
    const aWon = m.score1 > m.score2;
    const up = aWon ? m.team1 : m.team2;
    const down = aWon ? m.team2 : m.team1;
    up.forEach(p => { next[p] = Math.max(1, m.court - 1); });
    down.forEach(p => { next[p] = Math.min(courtCount, m.court + 1); });
  });
  return next;
}

// Where everyone stands right now: the opening ladder, moved on by every round
// that has been fully played.
function upCurrentCourts(night) {
  let courts = { ...(night.ladder0 || {}) };
  const C = upCourts(night);
  const rs = night.rounds || [];
  rs.forEach(r => {
    if (!upRoundDone(r)) return;
    // Each round is resolved against the number of courts IT was played on.
    // A round that happened on three courts kept its bottom-court losers where
    // they were; gaining a fourth court later must not reach back and drop
    // them into it. History does not move.
    courts = upCourtsAfter(r, courts, upRoundCourts(r) || C);
  });
  // Lose a court and anybody standing on the one that went — including whoever
  // was resting when it went, who no round moved — comes down to the new
  // bottom. Without this they sit on a court nobody is playing on and the next
  // round seats them below players who are genuinely last.
  Object.keys(courts).forEach(p => { courts[p] = Math.min(courts[p] || 1, C); });
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

// The ladder as an ORDER, not just a court number. With nobody resting the two
// are the same thing. With somebody resting they are not: if a Court 1 player
// sits out, Court 1 has three, and the round has to be seated from the ranking
// rather than from the court map. Court first, then running total, then id so
// that the same night always deals the same seats.
function upLadderOrder(night) {
  const courts = upCurrentCourts(night);
  const totals = upTotals(night);
  const C = upCourts(night);
  return upPlayerIds(night).slice().sort((a, b) =>
    ((courts[a] || C) - (courts[b] || C))
    || ((totals[b] || 0) - (totals[a] || 0))
    || String(a).localeCompare(String(b)));
}

// ── building the next round ────────────────────────────────────────────────

function upBuildRound(night) {
  const rounds = night.rounds || [];
  const last = rounds[rounds.length - 1];
  if (last && !upRoundDone(last)) throw new Error("the previous round is not finished");
  const N = upRoundsTotal(night);
  if (rounds.length >= N) throw new Error(`the night is already ${N} rounds long`);

  const C = upCourts(night);
  const totals = upTotals(night);
  const seen = upSeenPairs(night);
  const roundNum = rounds.length + 1;

  const sitOuts = upRestingFor(night, roundNum);
  const playing = upLadderOrder(night).filter(p => !sitOuts.includes(p));
  if (playing.length !== 4 * C)
    throw new Error(`${playing.length} players to seat on ${C} courts, not ${4 * C}`);

  const out = { roundNum, sitOuts, courts: [] };
  for (let c = 1; c <= C; c++) {
    const on = playing.slice((c - 1) * 4, c * 4);
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
  const N = upRoundsTotal(night), dbl = upDoubleFinal(night);
  upPlayerIds(night).forEach(id => { total[id] = 0; });
  (night.rounds || []).forEach(r => (r.courts || []).forEach(m => {
    if (!upMatchDone(m)) return;
    if (!upScoringRound(night, r.roundNum)) return;   // the shuffle pays nothing
    const isFinal = dbl && r.roundNum === N;
    const aWon = m.score1 > m.score2;
    m.team1.forEach(p => { total[p] = (total[p] || 0) + upRoundPoints(m.court, aWon, isFinal); });
    m.team2.forEach(p => { total[p] = (total[p] || 0) + upRoundPoints(m.court, !aWon, isFinal); });
  }));
  return total;
}

// Do the rests come out even? They do when the round count was chosen for the
// field (upFairRounds), and they do not when the night runs to a different
// number because everyone has to be gone by eight.
function upUneven(night) {
  const played = {};
  upPlayerIds(night).forEach(id => { played[id] = 0; });
  (night.rounds || []).forEach(r => (r.courts || []).forEach(m => {
    if (!upMatchDone(m) || !upScoringRound(night, r.roundNum)) return;
    [...m.team1, ...m.team2].forEach(p => { played[p] = (played[p] || 0) + 1; });
  }));
  const counts = Object.values(played);
  if (!counts.length) return false;
  return Math.max(...counts) - Math.min(...counts) > 0;
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
    // Partners count even in the shuffle — you did play with them, and
    // TONIGHT'S PARTNERS is the card that does this format's actual job. The
    // rest of the table does not: a shuffle win is not a win, because it paid
    // nothing, and counting it would make "6 won" disagree with the points.
    partners[m.team1[0]].add(m.team1[1]); partners[m.team1[1]].add(m.team1[0]);
    partners[m.team2[0]].add(m.team2[1]); partners[m.team2[1]].add(m.team2[0]);
    if (!upScoringRound(night, r.roundNum)) return;
    const aWon = m.score1 > m.score2;
    m.team1.forEach(p => { match[p] += m.score1; against[p] += m.score2; played[p]++; if (aWon) wins[p]++; });
    m.team2.forEach(p => { match[p] += m.score2; against[p] += m.score1; played[p]++; if (!aWon) wins[p]++; });
  }));

  // A baseline has to be PER SCORING ROUND, not a night total. Nights are not
  // all the same length — the planner sizes them to the clock — and comparing
  // a total earned over 14 rounds with one earned over 10 made 14 of 16
  // players look like they had got worse, which then handed THE CLIMB to the
  // champion as the least-bad of them.
  const perRound = id => (played[id] ? (total[id] || 0) / played[id] : 0);
  const scored = upPlayerIds(night).filter(id => played[id] > 0);
  const fieldAvg = scored.length
    ? scored.reduce((s, id) => s + perRound(id), 0) / scored.length : 0;

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
      // Points per round actually played. When the rests are uneven this is
      // what the table ranks on, and it is not a nicety: measured over 20,000
      // nights of 11 players over 9 rounds, ranking on raw points gave the
      // players who rested twice 94% of the wins over the ones who rested
      // three times. One extra round decided the night. On points per round
      // that is 58/42 against a 55/45 split of the field.
      avg: played[id] ? (total[id] || 0) / played[id] : 0,
      court: courts[id] || start[id] || UP.COURTS,
      startCourt: start[id] || UP.COURTS,
      partners: [...partners[id]],
      // Everything below is in POINTS PER SCORING ROUND, so it compares across
      // nights of different lengths.
      perRound: perRound(id),
      baseline: base,
      firstTimer: own == null,
      vsBaseline: perRound(id) - base,
    };
  });
  // CHAMPION: most points, match points break the tie — unless some players
  // got more rounds than others, in which case per-round is the only honest
  // order. `byAvg` is reported on every row so the screen can say which it is.
  const uneven = upUneven(night);
  rows.forEach(r => { r.byAvg = uneven; });
  rows.sort((x, y) => (uneven ? (y.avg - x.avg) : 0) || (y.total - x.total)
                      || (y.matchPts - x.matchPts)
                      || String(x.name).localeCompare(String(y.name)));
  rows.forEach((r, i) => { r.rank = i + 1; });
  return rows;
}

// Who finished strongest: points in the second half of their night minus
// points in the first. Computable from one night alone, which is the whole
// point of it — see upPrizes.
function upFinisher(night) {
  return upPlayerIds(night).map(id => {
    const rec = upReceipt(night, id).filter(r => !r.shuffle && !r.resting);
    const h = Math.floor(rec.length / 2);
    const first = rec.slice(0, h).reduce((n, r) => n + (r.points || 0), 0);
    const second = rec.slice(h).reduce((n, r) => n + (r.points || 0), 0);
    return { id, first, second, swing: second - first, played: rec.length };
  }).filter(r => r.played > 1)
    .sort((a, b) => (b.swing - a.swing) || (b.second - a.second)
                    || String(a.id).localeCompare(String(b.id)));
}

// The prizes. CHAMPION is scratch and is won on merit. THE CLIMB is the
// handicap — most points per round above your own average — and is open to
// anyone: measured at 21% of nights going to a top-3 player against 70% for
// scratch alone.
//
// THE CLIMB CANNOT BE AWARDED ON THE FIRST NIGHT. With no history every
// baseline falls back to the field average, which is the same number for
// everybody, so "most above your average" collapses into "most points" — the
// champion, in 2000 of 2000 simulated first nights. Handing one person both
// prizes is not a rounding error, it is the second prize not existing.
//
// So when nobody in the room has played before, the second prize is the
// STRONGEST FINISH instead: most points in the second half of the night minus
// the first. It needs no history, it is the champion only 7% of the time, and
// unlike "biggest rise up the ladder" it is not inverted — that one goes 80%
// to whoever the shuffle dropped to the bottom court and can never be won from
// Court 1, which is why UPRISING.md rejected it.
function upPrizes(night, byId = {}, baselines = {}) {
  const rows = upStandings(night, byId, baselines);
  const eligible = rows.filter(r => r.played > 0);
  if (!eligible.length) return { champion: null, climb: null, finisher: null, secondRule: "none" };
  const champion = eligible[0];

  const anyHistory = eligible.some(r => !r.firstTimer);
  const climb = anyHistory
    ? [...eligible].sort((a, b) => (b.vsBaseline - a.vsBaseline)
                                   || (b.total - a.total))[0]
    : null;

  const swings = upFinisher(night);
  const byId2 = {}; eligible.forEach(r => { byId2[r.id] = r; });
  const top = swings.find(s => byId2[s.id]);
  const finisher = top ? { ...byId2[top.id], swing: top.swing } : null;

  return { champion, climb, finisher,
           secondRule: anyHistory ? "climb" : "finisher" };
}

// Round by round, what one player did and what it paid. The scoring is only
// worth anything to a player if they can see it accruing — "Court 1 is worth
// double Court 3" means nothing until you have watched it happen to you — so
// this walks the same rounds the table walks and records every award as it is
// made, rather than re-deriving a total some other way. The running figure at
// the end therefore cannot disagree with upStandings: same loop, same call to
// upRoundPoints.
function upReceipt(night, playerId) {
  const dbl = upDoubleFinal(night), N = upRoundsTotal(night);
  const out = [];
  let running = 0;
  (night.rounds || []).forEach(r => {
    const isFinal = dbl && r.roundNum === N;
    const m = (r.courts || []).find(x =>
      (x.team1 || []).includes(playerId) || (x.team2 || []).includes(playerId));
    if (!m) {
      out.push({ roundNum: r.roundNum, resting: true, points: 0, running,
                 shuffle: !upScoringRound(night, r.roundNum), doubled: isFinal });
      return;
    }
    const mine = (m.team1 || []).includes(playerId) ? 1 : 2;
    const partner = (mine === 1 ? m.team1 : m.team2).find(p => p !== playerId);
    const against = mine === 1 ? m.team2 : m.team1;
    if (!upMatchDone(m)) {
      out.push({ roundNum: r.roundNum, court: m.court, partner, against,
                 pending: true, doubled: isFinal,
                 shuffle: !upScoringRound(night, r.roundNum),
                 stake: upScoringRound(night, r.roundNum)
                   ? { win: upRoundPoints(m.court, true, isFinal),
                       lose: upRoundPoints(m.court, false, isFinal) }
                   : { win: 0, lose: 0 },
                 points: null, running });
      return;
    }
    const myScore = mine === 1 ? m.score1 : m.score2;
    const theirScore = mine === 1 ? m.score2 : m.score1;
    const won = myScore > theirScore;
    const scores = upScoringRound(night, r.roundNum);
    const points = scores ? upRoundPoints(m.court, won, isFinal) : 0;
    running += points;
    out.push({ roundNum: r.roundNum, court: m.court, partner, against, shuffle: !scores,
               won, myScore, theirScore, points, running, doubled: isFinal,
               moved: won ? (m.court === 1 ? "stay" : "up")
                          : (m.court === upCourts(night) ? "stay" : "down") });
  });
  return out;
}

// Each player's court after every round — the line that makes the share card.
function upClimbPath(night, playerId) {
  // upCourtsAfter defaults its clamp to UP.COURTS. Called without the night's
  // own court count, a loser on the bottom court of a TWO-court night was sent
  // to Court 3 — a court nobody was standing on — and the climb line that is
  // the whole point of the share card drew a rung that did not exist. Every
  // other caller already passes this; this one was missed.
  const C = upCourts(night);
  // And each round is resolved against the courts IT was played on, so a path
  // drawn after a mid-night court change traces the rungs the player actually
  // stood on rather than redrawing the night at today's height.
  const path = [Math.min(night.ladder0 ? night.ladder0[playerId] : C, C)];
  let courts = { ...(night.ladder0 || {}) };
  (night.rounds || []).forEach(r => {
    if (!upRoundDone(r)) return;
    courts = upCourtsAfter(r, courts, upRoundCourts(r) || C);
    path.push(Math.min(courts[playerId] || C, Math.max(C, upRoundCourts(r) || C)));
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
  const C = upCourts(night), R = upRestCount(night);
  if (new Set(ids).size !== ids.length) bad.push("a player appears twice");
  // The FIELD no longer has to be a multiple of four — only the seating does.
  // What has to hold is that the people on court are 4C and the rest are
  // resting, and that the resting turns come round evenly.
  if (ids.length < 8) bad.push(`${ids.length} players is fewer than two courts`);
  if (ids.length - 4 * C !== R) bad.push("rest count does not match the field");
  if (C > UP.COURTS) bad.push(`${C} courts, but points are only defined for ${UP.COURTS}`);

  const rests = {};
  ids.forEach(id => { rests[id] = 0; });

  let courts = { ...(night.ladder0 || {}) };
  const rs = night.rounds || [];
  // The court count can change mid-night — a court frees up, or one is taken
  // away. Each round is therefore judged against ITS OWN shape, not the
  // night's current one; judging round 2 by a count set at round 7 fails every
  // round that came before the change for no reason.
  const changed = rs.some(r => upRoundCourts(r) && upRoundCourts(r) !== upRoundCourts(rs[0]));
  rs.forEach((r, i) => {
    const Cr = upRoundCourts(r) || C;
    const Rr = Math.max(0, ids.length - 4 * Cr);
    const sit = r.sitOuts || [];
    if (sit.length !== Rr) bad.push(`round ${r.roundNum}: ${sit.length} resting, expected ${Rr}`);
    sit.forEach(p => {
      if (!ids.includes(p)) bad.push(`round ${r.roundNum}: ${p} is resting but is not in the field`);
      rests[p] = (rests[p] || 0) + 1;
    });
    if (Cr > UP.COURTS || Cr < 1)
      bad.push(`round ${r.roundNum}: ${Cr} courts, but points are defined for 1-${UP.COURTS}`);
    const onCourt = {};
    (r.courts || []).forEach(m => {
      [...(m.team1 || []), ...(m.team2 || [])].forEach(p => {
        if (onCourt[p]) bad.push(`round ${r.roundNum}: ${p} is on two courts`);
        if (sit.includes(p)) bad.push(`round ${r.roundNum}: ${p} is resting and playing`);
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
      courts = upCourtsAfter(r, courts, Cr);
      // Court sizes only have to be exactly four when nobody rests. With
      // resters a court legitimately holds three or five BETWEEN rounds,
      // because the next round is seated from the ladder order, not from the
      // court map — what matters is that the seating is four to a court, which
      // is checked above.
      if (Rr === 0) {
        Object.entries(upCourtSizes(courts)).forEach(([c, n]) => {
          if (n !== 4) bad.push(`after round ${r.roundNum}: court ${c} has ${n}`);
        });
      }
    }
  });

  // Rests must come out within one of each other across the rounds played —
  // but only while the night kept the same number of courts. Gain a court at
  // round 7 and the rota it was walking stops part-way; the people who had
  // already taken their turn have one more rest than the people who had not,
  // and no amount of care afterwards can undo a round that is already played.
  // That is not corruption, it is the night that actually happened, and the
  // table handles it: upUneven() goes true and the standings rank on points
  // per round played, so nobody wins on extra court time.
  const counts = Object.values(rests);
  if (!changed && R > 0 && counts.length && Math.max(...counts) - Math.min(...counts) > 1)
    bad.push(`rests are uneven: ${Math.min(...counts)}–${Math.max(...counts)} across the night`);
  return bad;
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = {
    UP, upPlayerIds, upSeedLadder, upPairCourt, upRoundPoints, upMatchDone, upRoundDone,
    upCourtsAfter, upCurrentCourts, upSeenPairs, upBuildRound, upTotals,
    upStandings, upPrizes, upClimbPath, upValidate, upPairKey, upFinisher,
    upCourts, upRoundsTotal, upRestCount, upFairRounds, upDoubleFinal, upReceipt,
    upScoringRound, upScoringRounds,
    UP_PACE, upRoundMinutes, upNightMinutes, upPlanRounds,
    upMakeRestRota, upRestRota, upRestingFor, upLadderOrder, upUneven,
    upRoundCourts, upCourtsAt,
  };
}
