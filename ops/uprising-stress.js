// Exhaustive stress test of the SHIPPED engine.
//
// The design simulations earlier in this work compared formats using my own
// model of the ladder. That is fine for choosing between designs and useless
// for proving the code is right. This one calls uprising-engine.js — the exact
// file inlined into the page — across thousands of randomised nights and
// asserts every invariant the format depends on.
const E = require('/home/user/May-madness/uprising-engine.js');
const {
  UP, upSeedLadder, upMakeRestRota, upBuildRound, upStandings, upReceipt,
  upValidate, upCourts, upRestCount, upUneven, upScoringRounds, upScoringRound,
  upDoubleFinal, upRoundPoints, upFairRounds, upPlanRounds, upTotals, upRoundDoubled,
  upCurrentCourts, upClimbPath, upPrizes, upPairKey, upFinisher, upShuffleRounds,
} = E;

let rngState = 1;
const rnd = () => (rngState = (rngState * 1664525 + 1013904223) >>> 0) / 4294967296;
const pick = a => a[Math.floor(rnd() * a.length)];
const ri = (lo, hi) => lo + Math.floor(rnd() * (hi - lo + 1));

const problems = [];
function check(cond, what, ctx) {
  if (!cond) problems.push(`${what}   [${ctx}]`);
  return cond;
}

function buildNight(cfg) {
  const { players, courts, target, shuffle, scoring } = cfg;
  const ids = Array.from({ length: players }, (_, i) => 'p' + String(i).padStart(2, '0'));
  return {
    id: 'n', playerIds: ids, courtCount: courts,
    numRounds: scoring + upShuffleRounds({ shuffle }), shuffle,
    pointsPerMatch: target,
    restRota: upMakeRestRota(ids, ri(1, 1e9)),
    ladder0: upSeedLadder(ids, {}, Math.min(courts, Math.floor(players / 4))),
    rounds: [],
  };
}

function playNight(night, target) {
  while (night.rounds.length < night.numRounds) {
    const r = upBuildRound(night);
    r.courts.forEach(m => {
      const aWins = rnd() < 0.5;
      const loser = Math.floor(rnd() * target);
      m.score1 = aWins ? target : loser;
      m.score2 = aWins ? loser : target;
    });
    night.rounds.push(r);
  }
  return night;
}

function audit(night, cfg, tag) {
  const ctx = `${cfg.players}p ${cfg.courts}c first-to-${cfg.target} ${cfg.scoring}sc shuffle=${cfg.shuffle} ${tag}`;
  const C = upCourts(night), R = upRestCount(night);
  const ids = night.playerIds;

  check(upValidate(night).length === 0, 'upValidate: ' + upValidate(night).join('; '), ctx);
  check(night.rounds.length === night.numRounds, `built ${night.rounds.length} of ${night.numRounds} rounds`, ctx);

  // every round: four to a court, right number resting, nobody in two places
  const rests = {}; ids.forEach(i => rests[i] = 0);
  const playedRaw = {}; ids.forEach(i => playedRaw[i] = 0);
  night.rounds.forEach(r => {
    check(r.courts.length === C, `round ${r.roundNum}: ${r.courts.length} courts, expected ${C}`, ctx);
    const seen = new Set();
    r.courts.forEach(m => {
      const four = [...m.team1, ...m.team2];
      check(four.length === 4, `round ${r.roundNum} court ${m.court}: ${four.length} players`, ctx);
      check(new Set(four).size === 4, `round ${r.roundNum} court ${m.court}: duplicate player`, ctx);
      check(UP.WIN[m.court] != null, `round ${r.roundNum}: court ${m.court} has no points defined`, ctx);
      four.forEach(p => {
        check(!seen.has(p), `round ${r.roundNum}: ${p} on two courts`, ctx);
        check(ids.includes(p), `round ${r.roundNum}: ${p} is not in the field`, ctx);
        seen.add(p); playedRaw[p]++;
      });
      check(m.score1 !== m.score2, `round ${r.roundNum} court ${m.court}: drawn match`, ctx);
      check(Math.max(m.score1, m.score2) === cfg.target, `round ${r.roundNum}: winner not on the target`, ctx);
    });
    (r.sitOuts || []).forEach(p => { rests[p]++; check(!seen.has(p), `round ${r.roundNum}: ${p} rests and plays`, ctx); });
    check((r.sitOuts || []).length === R, `round ${r.roundNum}: ${(r.sitOuts || []).length} resting, expected ${R}`, ctx);
    check(seen.size + (r.sitOuts || []).length === ids.length, `round ${r.roundNum}: ${seen.size + (r.sitOuts||[]).length} accounted for, not ${ids.length}`, ctx);
  });

  // rests balanced within one across the whole night
  const rv = Object.values(rests);
  check(Math.max(...rv) - Math.min(...rv) <= 1, `rest spread ${Math.min(...rv)}–${Math.max(...rv)}`, ctx);

  // the table
  const rows = upStandings(night);
  check(rows.length === ids.length, `table has ${rows.length} rows for ${ids.length} players`, ctx);
  const scoringRounds = upScoringRounds(night);
  check(scoringRounds === cfg.scoring, `upScoringRounds says ${scoringRounds}, expected ${cfg.scoring}`, ctx);

  // played = scoring rounds a player was actually on court for
  rows.forEach(row => {
    let expect = 0;
    night.rounds.forEach(r => {
      if (!upScoringRound(night, r.roundNum)) return;
      if (r.courts.some(m => [...m.team1, ...m.team2].includes(row.id))) expect++;
    });
    check(row.played === expect, `${row.id}: played ${row.played}, counted ${expect}`, ctx);
  });

  // the receipt must reconstruct the table exactly
  rows.forEach(row => {
    const rec = upReceipt(night, row.id);
    check(rec.length === night.rounds.length, `${row.id}: receipt has ${rec.length} rows for ${night.rounds.length} rounds`, ctx);
    check(rec[rec.length - 1].running === row.total, `${row.id}: receipt ends ${rec[rec.length-1].running}, table says ${row.total}`, ctx);
    check(rec.reduce((n, x) => n + (x.points || 0), 0) === row.total, `${row.id}: receipt rows do not sum to the total`, ctx);
    const shuf = rec.filter(x => x.shuffle);
    check(shuf.length === upShuffleRounds({ shuffle: cfg.shuffle }),
      `${row.id}: ${shuf.length} shuffle rows, expected ${upShuffleRounds({ shuffle: cfg.shuffle })}`, ctx);
    shuf.forEach(x => check(x.points === 0, `${row.id}: the shuffle paid ${x.points}`, ctx));
    check(rec.every(x => x.points === null || x.points >= 0), `${row.id}: negative points on the receipt`, ctx);
    check(rec.filter(x => x.resting).length === rests[row.id], `${row.id}: receipt shows ${rec.filter(x=>x.resting).length} rests, rota gave ${rests[row.id]}`, ctx);
  });

  // conservation: the points awarded must equal what the courts owe
  const dbl = upDoubleFinal(night);
  let owed = 0;
  night.rounds.forEach(r => {
    if (!upScoringRound(night, r.roundNum)) return;
    const mult = (dbl && r.roundNum === night.numRounds) ? UP.FINAL_MULT : 1;
    r.courts.forEach(m => { owed += (UP.WIN[m.court] + UP.LOSE[m.court]) * 2 * mult; });
  });
  const given = rows.reduce((n, r) => n + r.total, 0);
  check(given === owed, `points awarded ${given}, courts owe ${owed}`, ctx);

  // the double final is a property of the field, not a setting
  check(dbl === (R === 0), `doubleFinal=${dbl} with ${R} resting`, ctx);

  // the table's ranking mode must match reality
  const played = rows.map(r => r.played);
  check(rows[0].byAvg === (Math.max(...played) !== Math.min(...played)),
    `byAvg=${rows[0].byAvg} but played spans ${Math.min(...played)}–${Math.max(...played)}`, ctx);
  // and it must actually be sorted that way
  for (let i = 1; i < rows.length; i++) {
    const a = rows[i - 1], b = rows[i];
    const key = rows[0].byAvg ? 'avg' : 'total';
    check(a[key] >= b[key] - 1e-9, `table out of order at rank ${i + 1} (${key})`, ctx);
  }

  // climb path and prizes must not throw and must be the right length
  ids.forEach(id => {
    const path = upClimbPath(night, id);
    check(path.length === night.rounds.length + 1, `${id}: climb path ${path.length} long`, ctx);
    path.forEach(c => check(c >= 1 && c <= C, `${id}: climb path visits court ${c}`, ctx));
  });
  // THE CLIMB is deliberately NOT awarded when nobody in the room has history:
  // every baseline falls back to the field average, so the rule collapses into
  // "most points" and hands the champion both prizes. These nights carry no
  // baselines, so the second prize must be the strongest finish instead.
  const pz = upPrizes(night);
  check(!!pz.champion, 'no champion', ctx);
  check(pz.champion.id === rows[0].id, 'champion is not the top of the table', ctx);
  check(pz.secondRule === 'finisher', `secondRule is ${pz.secondRule} with no history`, ctx);
  check(pz.climb === null, 'THE CLIMB was awarded with nobody holding a baseline', ctx);
  if (upScoringRounds(night) > 1 && rows.some(r => r.played > 1))
    check(!!pz.finisher, 'no second prize at all', ctx);

  // and with history in the room it must come back
  const withBase = {};
  rows.slice(0, 2).forEach(r => { withBase[r.id] = r.perRound; });
  const pz2 = upPrizes(night, {}, withBase);
  check(pz2.secondRule === 'climb', 'the climb did not return once a baseline existed', ctx);
  check(!!pz2.climb, 'climb null despite a baseline', ctx);

  // per-round figures must be internally consistent
  rows.forEach(r => {
    check(Math.abs(r.perRound - (r.played ? r.total / r.played : 0)) < 1e-9,
      `${r.id}: perRound ${r.perRound} does not match ${r.total}/${r.played}`, ctx);
  });
}

// ── the sweep ──────────────────────────────────────────────────────────────
const NIGHTS = Number(process.argv[2] || 3000);
let built = 0, refused = 0;
for (let n = 0; n < NIGHTS; n++) {
  const players = ri(8, 32);
  const maxC = Math.min(Math.floor(players / 4), UP.COURTS);
  const courts = ri(1, maxC);
  const target = pick([6, 8, 9, 11, 13, 16, 21, 24]);
  // 0, 1 or 2 opening shuffle rounds. Two is allowed now, so the harness
  // has to build them or the option ships untested.
  const shuffle = rnd() < 0.3 ? false : (rnd() < 0.3 ? 2 : true);
  const usePlanner = rnd() < 0.5;
  const scoring = usePlanner
    ? upPlanRounds(pick([120, 150, 180]), target, { shuffle, players, courts })
    : ri(2, 20);
  const cfg = { players, courts, target, shuffle, scoring };
  let night;
  try {
    night = playNight(buildNight(cfg), target);
  } catch (e) {
    problems.push(`THREW: ${e.message}   [${players}p ${courts}c ${scoring}sc shuffle=${shuffle}]`);
    refused++;
    continue;
  }
  built++;
  audit(night, cfg, usePlanner ? 'planned' : 'manual');
}

// ── the edit path: a scorer fixing a typo three rounds back ────────────────
// The app deliberately does NOT rebuild later rounds when an earlier score is
// corrected, because re-pairing would rewrite matches people have already
// played. So the stored rounds can disagree with the ladder afterwards. What
// must still hold is that nothing throws and the table stays self-consistent.
let edited = 0;
for (let n = 0; n < 400; n++) {
  const players = pick([12, 16, 20]);
  const cfg = { players, courts: Math.min(4, players / 4), target: 11, shuffle: true, scoring: 10 };
  const night = playNight(buildNight(cfg), 11);
  const r = night.rounds[ri(1, night.rounds.length - 2)];
  const m = r.courts[ri(0, r.courts.length - 1)];
  [m.score1, m.score2] = [m.score2, m.score1];          // flip the result
  edited++;
  const rows = upStandings(night);
  check(rows.length === players, 'edit: table lost rows', `${players}p`);
  rows.forEach(row => {
    const rec = upReceipt(night, row.id);
    check(rec[rec.length - 1].running === row.total,
      `edit: ${row.id} receipt ${rec[rec.length-1].running} vs table ${row.total}`, `${players}p`);
  });
  let owed = 0;
  const dbl = upDoubleFinal(night);
  night.rounds.forEach(rr => {
    if (!upScoringRound(night, rr.roundNum)) return;
    const mult = (dbl && rr.roundNum === night.numRounds) ? UP.FINAL_MULT : 1;
    rr.courts.forEach(mm => { owed += (UP.WIN[mm.court] + UP.LOSE[mm.court]) * 2 * mult; });
  });
  check(rows.reduce((a, b) => a + b.total, 0) === owed, 'edit: points no longer conserved', `${players}p`);
}

console.log(`${built} nights built and audited, ${refused} refused, ${edited} score-edits replayed`);
const uniq = [...new Set(problems)];
if (!problems.length) console.log('✓ no invariant broken');
else {
  console.log(`\n✗ ${problems.length} failures, ${uniq.length} distinct:\n`);
  uniq.slice(0, 25).forEach(x => console.log('  ' + x));
}
process.exit(problems.length ? 1 : 0);
