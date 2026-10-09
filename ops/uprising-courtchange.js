// Courts changing MID-NIGHT, which is the one thing neither the unit tests
// nor the stress harness covered: they both fix the court count at setup.
//
// A court frees up at round 6, or one is taken away at round 9. Everything
// already played has to stay exactly as it was played, the night has to keep
// building, and the table has to stay honest about who got more court time.
//
//   node ops/uprising-courtchange.js [trials]
const E = require("../uprising-engine.js");

const TRIALS = Number(process.argv[2]) || 3000;
let seed = 7;
const rnd = () => (seed = (seed * 1664525 + 1013904223) >>> 0) / 4294967296;
const ri = (lo, hi) => lo + Math.floor(rnd() * (hi - lo + 1));

const problems = [];
const check = (ok, what, ctx) => { if (!ok) problems.push(`${what}  [${ctx}]`); };

function playTo(night, upto, target) {
  while (night.rounds.length < upto) {
    const r = E.upBuildRound(night);
    r.courts.forEach(m => {
      const a = rnd() < 0.5, l = Math.floor(rnd() * target);
      m.score1 = a ? target : l; m.score2 = a ? l : target;
    });
    night.rounds.push(r);
  }
}

for (let t = 0; t < TRIALS; t++) {
  const players = ri(8, 24);
  const target = ri(7, 15);
  const maxC = Math.max(2, Math.min(E.UP.COURTS, Math.floor(players / 4)));
  const c0 = ri(2, maxC);
  const scoring = ri(6, 16);
  const ids = Array.from({ length: players }, (_, i) => "p" + i);
  const night = {
    id: "t", format: "uprising", playerIds: ids, courtCount: c0,
    numRounds: scoring + 1, shuffle: true, pointsPerMatch: target,
    ladder0: E.upSeedLadder(ids, {}, c0), rounds: [],
    restRota: E.upMakeRestRota(ids, t + 1),
  };
  const at = ri(2, night.numRounds - 1);          // the round we change before
  const c1 = ri(2, maxC);
  const ctx = `${players}p ${c0}->${c1}c at r${at} first-to-${target} ${scoring}sc`;

  playTo(night, at - 1, target);

  // Snapshot everything about the rounds already played. None of it may move.
  const before = JSON.stringify(night.rounds);
  const ptsBefore = E.upTotals(night);
  const courtsBefore = E.upCurrentCourts(night);

  // THE CHANGE. This is all the app does: set the number and carry on.
  night.courtCount = c1;

  // And, half the time, the organiser also moves the finish line — "we have
  // the court for one more" or "we are running late". upSetRounds freezes the
  // doubling on everything already played; without that, lengthening the
  // night un-doubles a round people watched and every total moves.
  const extend = rnd() < 0.5 ? ri(-2, 3) : 0;

  let n2 = night;
  if (extend) n2 = E.upSetRounds(night, E.upRoundsTotal(night) + extend);
  Object.assign(night, n2);

  const playedBefore = JSON.parse(before).filter(r =>
    (r.courts || []).some(m => Number.isFinite(m.score1)));
  const playedAfter = (night.rounds || []).filter(r =>
    (r.courts || []).some(m => Number.isFinite(m.score1)));
  check(playedAfter.length === playedBefore.length, "a played round vanished or appeared", ctx);
  playedAfter.forEach((r, k) => {
    const b4 = playedBefore[k];
    check(JSON.stringify(r.courts) === JSON.stringify(b4.courts),
      `round ${r.roundNum}: its matches changed`, ctx);
  });
  check(E.upRoundsTotal(night) >= playedAfter.length,
    "the night is now shorter than the rounds already played", ctx);
  const ptsAfter = E.upTotals(night);
  // Totals may legitimately move ONLY by the final-round doubling, and only if
  // the final round has been played — which it has not here.
  check(ids.every(id => (ptsBefore[id] || 0) === (ptsAfter[id] || 0)),
    "points on the board moved when the courts or the round count changed", ctx);

  const courtsAfter = E.upCurrentCourts(night);
  const Cnow = E.upCourts(night);
  check(Object.values(courtsAfter).every(c => c >= 1 && c <= Cnow),
    "somebody is standing on a court that does not exist", ctx);
  if (c1 >= c0) {
    check(ids.every(id => (courtsBefore[id] || 1) === (courtsAfter[id] || 1)),
      "adding a court moved people who had not played a round", ctx);
  }

  // The night must keep building, and finish.
  let threw = null;
  try { playTo(night, night.numRounds, target); } catch (e) { threw = e.message; }
  check(!threw, "could not finish the night: " + threw, ctx);
  if (threw) continue;

  check(E.upValidate(night).length === 0, "upValidate: " + E.upValidate(night).join("; "), ctx);
  check(night.rounds.length === night.numRounds, "wrong number of rounds", ctx);

  // Every round is four to a court, nobody in two places, resters not playing.
  night.rounds.forEach(r => {
    const seen = new Set();
    const Cr = E.upRoundCourts(r);
    check(Cr >= 1 && Cr <= E.UP.COURTS, `round ${r.roundNum}: ${Cr} courts`, ctx);
    check((r.sitOuts || []).length === players - 4 * Cr,
      `round ${r.roundNum}: rest count does not match its own court count`, ctx);
    r.courts.forEach(m => {
      [...m.team1, ...m.team2].forEach(p => {
        check(!seen.has(p), `round ${r.roundNum}: ${p} in two places`, ctx);
        check(!(r.sitOuts || []).includes(p), `round ${r.roundNum}: ${p} resting and playing`, ctx);
        seen.add(p);
      });
      check(m.court >= 1 && m.court <= Cr, `round ${r.roundNum}: court ${m.court} of ${Cr}`, ctx);
    });
  });

  // The table must still reconstruct from the receipts, and must rank on the
  // mode it claims.
  const st = E.upStandings(night, {});
  st.forEach(row => {
    const rec = E.upReceipt(night, row.id);
    const sum = rec.reduce((s, line) => s + (line.points || 0), 0);
    check(sum === row.total, `${row.id}: receipt ${sum} vs table ${row.total}`, ctx);
  });
  const uneven = E.upUneven(night);
  for (let i = 1; i < st.length; i++) {
    const a = st[i - 1], b = st[i];
    const key = r => (uneven ? (r.played ? r.total / r.played : 0) : r.total);
    check(key(a) >= key(b) - 1e-9, `table out of order at ${i}`, ctx);
  }

  // Points conserved: what the courts paid out is what the table holds.
  let owed = 0;
  
  night.rounds.forEach(r => {
    if (!E.upScoringRound(night, r.roundNum)) return;
    const isFinal = E.upRoundDoubled(night, r);
    r.courts.forEach(m => {
      owed += 2 * E.upRoundPoints(m.court, true, isFinal);
      owed += 2 * E.upRoundPoints(m.court, false, isFinal);
    });
  });
  const held = st.reduce((s, r) => s + r.total, 0);
  check(owed === held, `points conserved: courts owe ${owed}, table holds ${held}`, ctx);
}

console.log(`${TRIALS} nights with a mid-night court change and/or a moved finish line`);
if (problems.length) {
  const uniq = [...new Set(problems)];
  console.log(`\n!! ${problems.length} failures (${uniq.length} distinct):`);
  uniq.slice(0, 12).forEach(p => console.log("   " + p));
  process.exit(1);
}
console.log("✓ no invariant broken");
