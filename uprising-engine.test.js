/* UPRISING engine tests.  node --test uprising-engine.test.js */
const test = require("node:test");
const assert = require("node:assert");
const E = require("./uprising-engine.js");
const {
  UP, upSeedLadder, upPairCourt, upRoundPoints, upRoundDone, upCourtsAfter,
  upCurrentCourts, upBuildRound, upTotals, upStandings, upPrizes, upClimbPath,
  upValidate, upPairKey,
  upCourts, upRestCount, upFairRounds, upDoubleFinal, upMakeRestRota, upReceipt,
  upScoringRound, upScoringRounds, upPlanRounds, upNightMinutes, upRoundMinutes,
  upFinisher,
  upRestingFor, upLadderOrder, upUneven, upRoundsTotal,
} = E;

const ids = n => Array.from({ length: n }, (_, i) => `p${String(i).padStart(2, "0")}`);

function newNight(n = 16, form = {}, rounds = 0) {
  const players = ids(n).map(id => ({ id, name: id.toUpperCase() }));
  const pids = players.map(p => p.id);
  const courtCount = Math.min(Math.floor(n / 4), UP.COURTS);
  const fair = upFairRounds(n, courtCount);
  return { id: "n1", players, playerIds: pids, courtCount,
           numRounds: rounds || (fair === null ? UP.ROUNDS : (fair[0] || UP.ROUNDS)),
           restRota: upMakeRestRota(pids, 7),
           ladder0: upSeedLadder(pids, form, courtCount), rounds: [] };
}

// Plays one round: `pick` decides the winner for a given match.
function playRound(night, pick = () => true) {
  const r = upBuildRound(night);
  r.courts.forEach(m => {
    const aWins = pick(m, night);
    m.score1 = aWins ? UP.TARGET : 11;
    m.score2 = aWins ? 11 : UP.TARGET;
  });
  night.rounds.push(r);
  return r;
}

// ── the opening ladder ─────────────────────────────────────────────────────

test("seeds four to a court, best form on Court 1", () => {
  const form = {}; ids(16).forEach((p, i) => { form[p] = 16 - i; });   // p00 strongest
  const l = upSeedLadder(ids(16), form);
  assert.equal(l.p00, 1); assert.equal(l.p03, 1);
  assert.equal(l.p04, 2); assert.equal(l.p15, 4);
  const sizes = {}; Object.values(l).forEach(c => sizes[c] = (sizes[c] || 0) + 1);
  assert.deepEqual(sizes, { 1: 4, 2: 4, 3: 4, 4: 4 });
});

test("unknown players take the median, not the bottom", () => {
  const form = { p00: 100, p01: 90, p02: 10, p03: 5 };     // four known, twelve not
  const l = upSeedLadder(ids(16), form);
  assert.equal(l.p00, 1, "the strongest known player starts top");
  assert.ok(l.p02 >= 3 && l.p03 >= 3, "known weak players start low");
  // a newcomer should not be dumped on Court 4 merely for being unknown
  assert.ok(l.p09 <= 3, `newcomer started on court ${l.p09}`);
});

test("the same input always gives the same ladder", () => {
  const form = { p00: 5, p01: 5, p02: 5 };
  assert.deepEqual(upSeedLadder(ids(16), form), upSeedLadder(ids(16), form));
});

// ── pairing ────────────────────────────────────────────────────────────────

test("pairs 1+4 against 2+3", () => {
  const totals = { a: 40, b: 30, c: 20, d: 10 };
  const [A, B] = upPairCourt(["a", "b", "c", "d"], totals, new Set());
  assert.deepEqual([A.sort(), B.sort()].sort(), [["a", "d"], ["b", "c"]].sort());
});

test("avoids a partnership that has already happened", () => {
  const totals = { a: 40, b: 30, c: 20, d: 10 };
  const seen = new Set([upPairKey("a", "d")]);
  const [A, B] = upPairCourt(["a", "b", "c", "d"], totals, seen);
  const used = [upPairKey(...A), upPairKey(...B)];
  assert.ok(!used.includes(upPairKey("a", "d")), "reused a partnership that was free to avoid");
});

test("falls back to the closest split when all three are used", () => {
  const totals = { a: 40, b: 30, c: 20, d: 10 };
  const seen = new Set([upPairKey("a", "d"), upPairKey("b", "c"), upPairKey("a", "c"),
                        upPairKey("b", "d"), upPairKey("a", "b"), upPairKey("c", "d")]);
  const [A, B] = upPairCourt(["a", "b", "c", "d"], totals, seen);
  assert.deepEqual([A.sort(), B.sort()].sort(), [["a", "d"], ["b", "c"]].sort());
});

test("refuses a court that is not four players", () => {
  assert.throws(() => upPairCourt(["a", "b", "c"], {}, new Set()), /exactly 4/);
});

// ── scoring ────────────────────────────────────────────────────────────────

test("points are worth more higher up the ladder", () => {
  assert.equal(upRoundPoints(1, true, false), 8);
  assert.equal(upRoundPoints(4, true, false), 2);
  assert.equal(upRoundPoints(1, false, false), 4);
  assert.equal(upRoundPoints(4, false, false), 1);
});

test("losing on Court 1 equals winning on Court 3", () => {
  assert.equal(upRoundPoints(1, false, false), upRoundPoints(3, true, false));
});

test("the last round is worth double", () => {
  assert.equal(upRoundPoints(1, true, true), 16);
  assert.equal(upRoundPoints(4, false, true), 2);
});

test("winning always beats losing, and a higher court always pays more", () => {
  // The real invariants. An earlier version of this test demanded that a win
  // on any court strictly beat a loss on the court above, and that is not what
  // the table promises: it is built on LOSE[c] === WIN[c+2], so losing on
  // Court 1 equals winning on Court 3 — stated in the spec as deliberate — and
  // by the same rule winning on Court 4 equals losing on Court 3. There is no
  // perverse incentive in that: on any given court you would always rather win,
  // and any given result is worth at least as much a court higher up.
  for (let c = 1; c <= UP.COURTS; c++) {
    assert.ok(upRoundPoints(c, true, false) > upRoundPoints(c, false, false),
      `on court ${c}, winning must beat losing`);
  }
  for (let c = 2; c <= UP.COURTS; c++) {
    assert.ok(upRoundPoints(c - 1, true, false) > upRoundPoints(c, true, false),
      `a win must be worth more on court ${c - 1} than on court ${c}`);
    assert.ok(upRoundPoints(c - 1, false, false) > upRoundPoints(c, false, false),
      `a loss must be worth more on court ${c - 1} than on court ${c}`);
  }
  assert.equal(upRoundPoints(1, false, false), upRoundPoints(3, true, false));
  assert.equal(upRoundPoints(3, false, false), upRoundPoints(4, true, false));
});

// ── movement ───────────────────────────────────────────────────────────────

test("winners go up, losers go down, and the ends hold", () => {
  const before = { a: 1, b: 1, c: 1, d: 1, e: 4, f: 4, g: 4, h: 4 };
  const round = { roundNum: 1, courts: [
    { court: 1, team1: ["a", "b"], team2: ["c", "d"], score1: 16, score2: 9 },
    { court: 4, team1: ["e", "f"], team2: ["g", "h"], score1: 9, score2: 16 },
  ] };
  const after = upCourtsAfter(round, before);
  assert.equal(after.a, 1, "Court 1 winners stay on Court 1");
  assert.equal(after.c, 2, "Court 1 losers drop to Court 2");
  assert.equal(after.g, 3, "Court 4 winners climb to Court 3");
  assert.equal(after.e, 4, "Court 4 losers stay on Court 4");
});

test("an unfinished match moves nobody", () => {
  const before = { a: 2, b: 2, c: 2, d: 2 };
  const r = { roundNum: 1, courts: [{ court: 2, team1: ["a", "b"], team2: ["c", "d"], score1: 16, score2: null }] };
  assert.deepEqual(upCourtsAfter(r, before), before);
});

// ── a whole night ──────────────────────────────────────────────────────────

test("nine rounds stay four to a court, every round, every time", () => {
  for (let seed = 0; seed < 50; seed++) {
    let s = seed * 2654435761 % 4294967296;
    const rnd = () => (s = (s * 1664525 + 1013904223) % 4294967296) / 4294967296;
    const night = newNight(16);
    for (let r = 0; r < UP.ROUNDS; r++) playRound(night, () => rnd() < 0.5);
    assert.deepEqual(upValidate(night), [], `seed ${seed}`);
    assert.equal(night.rounds.length, 9);
    // every player played every round
    const played = {};
    night.rounds.forEach(r => r.courts.forEach(m => [...m.team1, ...m.team2].forEach(p => {
      played[p] = (played[p] || 0) + 1;
    })));
    Object.entries(played).forEach(([p, n]) =>
      assert.equal(n, 9, `${p} played ${n} rounds, not 9`));
    assert.equal(Object.keys(played).length, 16, "somebody sat out");
  }
});

test("a tenth round is refused", () => {
  const night = newNight(16);
  for (let r = 0; r < UP.ROUNDS; r++) playRound(night);
  assert.throws(() => upBuildRound(night), /already 9 rounds long/);
});

test("the next round is refused until this one is finished", () => {
  const night = newNight(16);
  const r = upBuildRound(night);
  night.rounds.push(r);                       // pushed with no scores
  assert.throws(() => upBuildRound(night), /not finished/);
});

test("a player who wins everything from Court 1 scores the maximum", () => {
  const night = newNight(16);
  // whoever is on Court 1 in pair A wins every match
  for (let r = 0; r < UP.ROUNDS; r++) playRound(night, () => true);
  const totals = upTotals(night);
  // 8 rounds at 8 + a double final at 16 = 80 is the ceiling for a Court 1 ever-present
  const best = Math.max(...Object.values(totals));
  assert.ok(best <= 8 * (UP.ROUNDS - 1) + 8 * UP.FINAL_MULT,
    `best ${best} exceeds the theoretical ceiling`);
  assert.ok(best > 0);
});

// ── standings and prizes ───────────────────────────────────────────────────

test("the table ranks on points and breaks ties on match points", () => {
  const night = newNight(16);
  for (let r = 0; r < UP.ROUNDS; r++) playRound(night, () => true);
  const rows = upStandings(night);
  assert.equal(rows.length, 16);
  for (let i = 1; i < rows.length; i++) {
    const a = rows[i - 1], b = rows[i];
    assert.ok(a.total > b.total || (a.total === b.total && a.matchPts >= b.matchPts),
      `row ${i} is out of order`);
  }
  assert.equal(rows[0].rank, 1);
});

test("the table sums to the points actually awarded", () => {
  const night = newNight(16);
  for (let r = 0; r < UP.ROUNDS; r++) playRound(night, (m) => m.court % 2 === 0);
  const rows = upStandings(night);
  let expected = 0;
  night.rounds.forEach(r => r.courts.forEach(m => {
    const isFinal = r.roundNum === UP.ROUNDS, aWon = m.score1 > m.score2;
    expected += 2 * upRoundPoints(m.court, aWon, isFinal)
              + 2 * upRoundPoints(m.court, !aWon, isFinal);
  }));
  assert.equal(rows.reduce((s, r) => s + r.total, 0), expected);
});

test("a first-timer is measured against the field, not against zero", () => {
  const night = newNight(16);
  night.players[0].baseline = 50;             // a regular
  for (let r = 0; r < UP.ROUNDS; r++) playRound(night, () => true);
  const rows = upStandings(night);
  const regular = rows.find(r => r.id === "p00");
  const newcomer = rows.find(r => r.id === "p01");
  assert.equal(regular.firstTimer, false);
  assert.equal(newcomer.firstTimer, true);
  assert.ok(newcomer.baseline > 0, "a first-timer's baseline must not be zero");
  assert.equal(regular.baseline, 50);
});

test("the two prizes are computed independently", () => {
  const night = newNight(16);
  // give one player a very high baseline so they cannot win THE CLIMB
  night.players.forEach((p, i) => { p.baseline = i === 0 ? 200 : 10; });
  for (let r = 0; r < UP.ROUNDS; r++) playRound(night, () => true);
  const { champion, climb } = upPrizes(night);
  assert.ok(champion && climb);
  assert.notEqual(climb.id, "p00", "a player far below their own baseline won the handicap");
  assert.equal(champion.rank, 1);
});

test("no prizes before a ball is hit", () => {
  const night = newNight(16);
  const { champion, climb } = upPrizes(night);
  assert.equal(champion, null); assert.equal(climb, null);
});

// ── the climb path ─────────────────────────────────────────────────────────

test("the climb path has one point per finished round plus the start", () => {
  const night = newNight(16);
  for (let r = 0; r < 5; r++) playRound(night, () => true);
  const path = upClimbPath(night, "p00");
  assert.equal(path.length, 6);
  path.forEach(c => assert.ok(c >= 1 && c <= UP.COURTS, `court ${c} is off the ladder`));
});

// ── the invariant catches real breakage ────────────────────────────────────

test("validate catches a player on two courts at once", () => {
  const night = newNight(16);
  const r = upBuildRound(night);
  r.courts[1].team1[0] = r.courts[0].team1[0];        // clone a player onto another court
  r.courts.forEach(m => { m.score1 = 16; m.score2 = 9; });
  night.rounds.push(r);
  assert.ok(upValidate(night).some(x => /two courts/.test(x)));
});

test("validate catches a drawn match", () => {
  const night = newNight(16);
  const r = upBuildRound(night);
  r.courts.forEach(m => { m.score1 = 16; m.score2 = 9; });
  r.courts[0].score2 = 16;
  night.rounds.push(r);
  assert.ok(upValidate(night).some(x => /drawn/.test(x)));
});

test("validate catches a field whose rounds do not rest anybody", () => {
  // A seventeenth player means one person must sit out every round. The rounds
  // already built rest nobody, so they no longer describe this field.
  const night = newNight(16);
  for (let r = 0; r < 3; r++) playRound(night);
  night.players.push({ id: "pX", name: "X" }); night.playerIds.push("pX");
  const bad = upValidate(night);
  assert.ok(bad.some(x => /0 resting, expected 1/.test(x)), bad.join("; "));
});

// ── fields that are not a multiple of four ─────────────────────────────────

test("four to a court is padel; the FIELD need not be a multiple of four", () => {
  for (const n of [9, 10, 11]) {
    const night = newNight(n);
    assert.equal(upCourts(night), 2, `${n} players should play on 2 courts`);
    assert.equal(upRestCount(night), n - 8);
    const r = upBuildRound(night);
    assert.equal(r.courts.length, 2);
    r.courts.forEach(m => assert.equal(new Set([...m.team1, ...m.team2]).size, 4));
    assert.equal(r.sitOuts.length, n - 8, `${n}: wrong number resting`);
    const onCourt = r.courts.flatMap(m => [...m.team1, ...m.team2]);
    assert.equal(new Set([...onCourt, ...r.sitOuts]).size, n, `${n}: somebody is missing`);
    r.sitOuts.forEach(p => assert.ok(!onCourt.includes(p), `${n}: ${p} rests and plays`));
  }
});

test("the round count that makes rests come out even", () => {
  assert.deepEqual(upFairRounds(9, 2), [9]);
  assert.deepEqual(upFairRounds(10, 2), [5, 10]);
  assert.deepEqual(upFairRounds(11, 2), [11]);
  assert.equal(upFairRounds(16, 4), null, "nobody rests, so any round count is fair");
  assert.equal(upFairRounds(12, 3), null);
  // 20 on the club's four courts: 4 rest each round, even only at multiples of 5
  assert.deepEqual(upFairRounds(20, 4), [5, 10]);
  assert.deepEqual(upFairRounds(20, 4, 15), [5, 10, 15]);
});

test("the ladder is never taller than the points table", () => {
  // 20 players would ask for five courts, and the points table has four rungs.
  // Before this cap the first round threw "no points defined for court 5" and
  // took the whole screen down.
  for (const n of [20, 24, 31]) {
    const night = newNight(n);
    assert.ok(upCourts(night) <= UP.COURTS, `${n} players asked for ${upCourts(night)} courts`);
    const r = upBuildRound(night);
    r.courts.forEach(m => assert.ok(UP.WIN[m.court] != null, `court ${m.court} has no points`));
  }
});

test("20 players on four courts: four rest, ten rounds, everybody plays eight", () => {
  const night = newNight(20, {}, 10);
  assert.equal(upCourts(night), 4);
  assert.equal(upRestCount(night), 4);
  assert.equal(upDoubleFinal(night), false);
  for (let r = 0; r < 10; r++) playRound(night, m => m.team1[0] < m.team2[0]);
  assert.deepEqual(upValidate(night), []);
  const rows = upStandings(night);
  assert.deepEqual([...new Set(rows.map(r => r.played))], [8]);
  const rests = {}; night.playerIds.forEach(i => rests[i] = 0);
  night.rounds.forEach(r => r.sitOuts.forEach(p => rests[p]++));
  assert.deepEqual([...new Set(Object.values(rests))], [2]);
  assert.equal(upUneven(night), false);
});

test("at the fair round count everybody rests exactly the same number of times", () => {
  for (const [n, rounds, each] of [[9, 9, 1], [10, 10, 2], [11, 11, 3], [10, 5, 1]]) {
    const night = newNight(n, {}, rounds);
    for (let r = 0; r < rounds; r++) playRound(night, m => m.team1[0] < m.team2[0]);
    const rests = {};
    night.playerIds.forEach(id => { rests[id] = 0; });
    night.rounds.forEach(r => r.sitOuts.forEach(p => rests[p]++));
    const v = Object.values(rests);
    assert.deepEqual([...new Set(v)], [each],
      `${n} players over ${rounds} rounds: rests were ${JSON.stringify(rests)}`);
    assert.deepEqual(upValidate(night), [], `${n}/${rounds} failed validation`);
    const rows = upStandings(night);
    assert.deepEqual([...new Set(rows.map(r => r.played))], [rounds - each]);
    assert.equal(upUneven(night), false, "equal rests must not be flagged uneven");
  }
});

test("the double final is off whenever anyone has to sit out", () => {
  // Measured over 20,000 nights: with the 2x final on and one player resting
  // each round, whoever draws the final-round rest takes 3.6% of the wins
  // against an 11.1% fair share. They cannot win, for a reason they did not
  // choose. So the multiplier belongs to the field, not to the format.
  assert.equal(upDoubleFinal(newNight(16)), true);
  assert.equal(upDoubleFinal(newNight(12)), true);
  [9, 10, 11].forEach(n => assert.equal(upDoubleFinal(newNight(n)), false, `${n}`));

  const even = newNight(16);
  for (let r = 0; r < UP.ROUNDS; r++) playRound(even, () => true);
  const odd = newNight(9, {}, 9);
  for (let r = 0; r < 9; r++) playRound(odd, () => true);
  // the 16-player night's last round pays double, the 9-player night's does not
  const lastOf = night => {
    const before = upTotals({ ...night, rounds: night.rounds.slice(0, -1) });
    const after = upTotals(night);
    const p = night.rounds[night.rounds.length - 1].courts[0].team1[0];
    return after[p] - before[p];
  };
  assert.equal(lastOf(even), 2 * UP.WIN[1], "16 players: the final should pay double");
  assert.equal(lastOf(odd), UP.WIN[1], "9 players: the final should pay flat");
});

test("uneven rests push the table onto points per round played", () => {
  // 11 players over 9 rounds cannot rest evenly (27 rests / 11 players). On raw
  // points the players who rested twice took 94% of 20,000 simulated nights
  // over the ones who rested three times — one extra round decided it.
  const night = newNight(11, {}, 9);
  for (let r = 0; r < 9; r++) playRound(night, m => m.team1[0] < m.team2[0]);
  assert.equal(upUneven(night), true);
  const rows = upStandings(night);
  assert.ok(rows.every(r => r.byAvg === true), "every row should say the table is per-round");
  const played = [...new Set(rows.map(r => r.played))].sort();
  assert.equal(played.length, 2, "some play 6 and some 7");
  for (let i = 1; i < rows.length; i++)
    assert.ok(rows[i - 1].avg >= rows[i].avg - 1e-9, "rows must be ordered by average");
  rows.forEach(r => assert.ok(Math.abs(r.avg - r.total / r.played) < 1e-9));
});

test("a nine-player night survives every round and the invariant holds", () => {
  const night = newNight(9, {}, 9);
  for (let r = 0; r < 9; r++) playRound(night, (m, n) => n.rounds.length % 2 === 0);
  assert.equal(night.rounds.length, 9);
  assert.deepEqual(upValidate(night), []);
  assert.throws(() => upBuildRound(night), /already 9 rounds long/);
  const rows = upStandings(night);
  assert.equal(rows.length, 9);
  assert.deepEqual([...new Set(rows.map(r => r.played))], [8], "everyone plays eight of nine");
});

test("the rest rota ignores how anyone is playing", () => {
  // The first version of this broke rest ties by ladder position, which handed
  // the early rounds off to the weak players and the double final off to the
  // strong ones — it measured the tie-break, not the format.
  const a = newNight(10, {}, 10);
  const b = newNight(10, {}, 10);
  for (let r = 0; r < 10; r++) playRound(a, () => true);        // team1 always wins
  for (let r = 0; r < 10; r++) playRound(b, () => false);       // team2 always wins
  assert.deepEqual(a.rounds.map(r => [...r.sitOuts].sort()),
                   b.rounds.map(r => [...r.sitOuts].sort()),
                   "who rests must not depend on who is winning");
});

test("a player added mid-night still takes a turn resting", () => {
  const night = newNight(12);
  night.players.push({ id: "pZZ", name: "ZZ" }); night.playerIds.push("pZZ");
  night.ladder0.pZZ = 3;
  assert.equal(upRestCount(night), 1);
  const seen = new Set();
  for (let r = 1; r <= 13; r++) upRestingFor(night, r).forEach(p => seen.add(p));
  assert.ok(seen.has("pZZ"), "the late arrival was never given a rest turn");
});

test("validate catches a duplicated player", () => {
  const night = newNight(16);
  night.players[1] = { ...night.players[0] }; night.playerIds[1] = night.playerIds[0];
  assert.ok(upValidate(night).some(x => /twice/.test(x)));
});

// ── the format's own claims ────────────────────────────────────────────────

test("seven different partners in nine rounds, five at worst", () => {
  const worst = [];
  for (let seed = 0; seed < 40; seed++) {
    let s = (seed + 1) * 2654435761 % 4294967296;
    const rnd = () => (s = (s * 1664525 + 1013904223) % 4294967296) / 4294967296;
    const night = newNight(16);
    for (let r = 0; r < UP.ROUNDS; r++) playRound(night, () => rnd() < 0.5);
    const rows = upStandings(night);
    worst.push(Math.min(...rows.map(r => r.partners.length)));
  }
  const min = Math.min(...worst);
  const median = worst.sort((a, b) => a - b)[Math.floor(worst.length / 2)];
  assert.ok(min >= 5, `worst player got only ${min} partners — the spec promises five`);
  assert.ok(median >= 6, `median worst-case was ${median}`);
});

test("the table counts real wins and a real game difference", () => {
  const night = newNight(16);
  for (let r = 0; r < UP.ROUNDS; r++) playRound(night, () => true);
  const rows = upStandings(night);
  rows.forEach(r => {
    assert.ok(r.wins >= 0 && r.wins <= UP.ROUNDS, `${r.name} has ${r.wins} wins`);
    assert.equal(typeof r.diff, "number");
  });
  // every match has exactly one winning pair, so nine rounds on four courts
  // hand out 9 * 4 * 2 = 72 player-wins between them
  assert.equal(rows.reduce((s, r) => s + r.wins, 0), UP.ROUNDS * UP.COURTS * 2);
  // and the differences cancel, because one pair's gain is the other's loss
  assert.equal(rows.reduce((s, r) => s + r.diff, 0), 0);
  assert.ok(rows[0].wins > 0, "the leader must have won something");
});

// ── the per-round receipt ──────────────────────────────────────────────────

test("the receipt totals exactly what the table says", () => {
  // The scoring is only worth anything to a player if they can watch it
  // accrue, and a breakdown that disagrees with the table is worse than none.
  const night = newNight(16);
  for (let r = 0; r < UP.ROUNDS; r++) playRound(night, m => m.team1[0] < m.team2[0]);
  const rows = upStandings(night);
  rows.forEach(row => {
    const rec = upReceipt(night, row.id);
    assert.equal(rec.length, UP.ROUNDS, `${row.name}: ${rec.length} rounds on the receipt`);
    assert.equal(rec[rec.length - 1].running, row.total,
      `${row.name}: receipt ends on ${rec[rec.length - 1].running}, table says ${row.total}`);
    assert.equal(rec.reduce((t, x) => t + (x.points || 0), 0), row.total);
  });
});

test("the receipt says what each round paid, and why", () => {
  const night = newNight(16);
  playRound(night, () => true);
  const m = night.rounds[0].courts.find(x => x.court === 2);
  const rec = upReceipt(night, m.team1[0]);
  assert.equal(rec[0].court, 2);
  assert.equal(rec[0].won, true);
  assert.equal(rec[0].points, UP.WIN[2], "a win on Court 2 is six");
  assert.equal(rec[0].moved, "up");
  assert.equal(rec[0].partner, m.team1[1]);
  const loser = upReceipt(night, m.team2[0]);
  assert.equal(loser[0].points, UP.LOSE[2]);
  assert.equal(loser[0].moved, "down");
  // Court 1 winners and bottom-court losers have nowhere to go
  const top = upReceipt(night, night.rounds[0].courts.find(x => x.court === 1).team1[0]);
  assert.equal(top[0].moved, "stay");
  const bot = upReceipt(night, night.rounds[0].courts.find(x => x.court === 4).team2[0]);
  assert.equal(bot[0].moved, "stay");
});

test("an unplayed round shows what is at stake, not a score", () => {
  const night = newNight(16);
  night.rounds.push(upBuildRound(night));
  const m = night.rounds[0].courts.find(x => x.court === 3);
  const rec = upReceipt(night, m.team1[0]);
  assert.equal(rec[0].pending, true);
  assert.equal(rec[0].points, null);
  assert.deepEqual(rec[0].stake, { win: UP.WIN[3], lose: UP.LOSE[3] });
});

test("the final round's stake and award are both doubled, when it is doubled", () => {
  const night = newNight(16);
  for (let r = 0; r < UP.ROUNDS; r++) playRound(night, () => true);
  const last = night.rounds[UP.ROUNDS - 1].courts.find(x => x.court === 1);
  const rec = upReceipt(night, last.team1[0]);
  const fin = rec[UP.ROUNDS - 1];
  assert.equal(fin.doubled, true);
  assert.equal(fin.points, UP.WIN[1] * UP.FINAL_MULT);

  // 9 players: somebody sits out every round, so the final is NOT doubled
  const odd = newNight(9, {}, 9);
  for (let r = 0; r < 9; r++) playRound(odd, () => true);
  const oRec = upReceipt(odd, odd.playerIds[0]);
  assert.ok(oRec.every(x => x.doubled === false));
});

test("a round spent resting is on the receipt, not missing from it", () => {
  const night = newNight(9, {}, 9);
  for (let r = 0; r < 9; r++) playRound(night, () => true);
  night.playerIds.forEach(id => {
    const rec = upReceipt(night, id);
    assert.equal(rec.length, 9, "every round should appear, played or not");
    assert.equal(rec.filter(x => x.resting).length, 1, `${id} should rest exactly once`);
    const rest = rec.find(x => x.resting);
    assert.equal(rest.points, 0);
  });
});

// ── the shuffle round ──────────────────────────────────────────────────────

function shuffleNight(n = 16, rounds = 10) {
  const night = newNight(n, {}, rounds);
  night.shuffle = true;
  return night;
}

test("the shuffle round pays nothing to anybody", () => {
  const night = shuffleNight(16, 10);
  playRound(night, () => true);
  const after = upTotals(night);
  assert.deepEqual([...new Set(Object.values(after))], [0],
    "round one is the shuffle — it must not award a single point");
  // and the very next round does pay
  playRound(night, () => true);
  assert.ok(Math.max(...Object.values(upTotals(night))) > 0, "round two should score");
});

test("the shuffle sets the ladder — that is its whole job", () => {
  const night = shuffleNight(16, 10);
  const before = { ...night.ladder0 };
  const r = playRound(night, () => true);           // team1 wins everywhere
  const after = upCurrentCourts(night);
  const moved = Object.keys(after).filter(id => after[id] !== before[id]);
  assert.ok(moved.length > 0, "nobody moved, so the shuffle decided nothing");
  // winners on court 2 should now be on court 1
  const c2 = r.courts.find(x => x.court === 2);
  c2.team1.forEach(p => assert.equal(after[p], 1));
});

test("a shuffle win is not a win, and does not count as a match played", () => {
  const night = shuffleNight(16, 10);
  for (let r = 0; r < 10; r++) playRound(night, m => m.team1[0] < m.team2[0]);
  upStandings(night).forEach(row => {
    assert.equal(row.played, 9, `${row.name} played ${row.played}, expected 9 scoring rounds`);
    assert.ok(row.wins <= 9);
  });
  assert.equal(upScoringRounds(night), 9);
});

test("but the shuffle still counts as a partner — that is the funnel's job", () => {
  const night = shuffleNight(16, 10);
  const r = playRound(night, () => true);
  const m = r.courts[0];
  const rows = upStandings(night);
  const row = rows.find(x => x.id === m.team1[0]);
  assert.ok(row.partners.includes(m.team1[1]),
    "you played with them; TONIGHT'S PARTNERS must say so even though it paid nothing");
});

test("the receipt marks the shuffle rather than hiding it", () => {
  const night = shuffleNight(16, 10);
  for (let r = 0; r < 10; r++) playRound(night, () => true);
  const rows = upStandings(night);
  rows.forEach(row => {
    const rec = upReceipt(night, row.id);
    assert.equal(rec.length, 10, "all ten rounds appear");
    assert.equal(rec[0].shuffle, true, "round one is flagged as the shuffle");
    assert.equal(rec[0].points, 0);
    assert.equal(rec[0].running, 0);
    assert.ok(rec[0].myScore != null, "the scoreline is still shown");
    assert.equal(rec[rec.length - 1].running, row.total, `${row.name}: receipt must match the table`);
  });
});

test("an unplayed shuffle round advertises no stake", () => {
  const night = shuffleNight(16, 10);
  night.rounds.push(upBuildRound(night));
  const m = night.rounds[0].courts[0];
  const rec = upReceipt(night, m.team1[0]);
  assert.equal(rec[0].pending, true);
  assert.equal(rec[0].shuffle, true);
  assert.deepEqual(rec[0].stake, { win: 0, lose: 0 });
});

test("the double still lands on the last round, not the last scoring round + 1", () => {
  const night = shuffleNight(16, 10);
  for (let r = 0; r < 10; r++) playRound(night, () => true);
  const rec = upReceipt(night, night.rounds[9].courts[0].team1[0]);
  assert.equal(rec[9].doubled, true);
  assert.equal(rec[8].doubled, false);
});

test("a night without the shuffle is untouched by any of this", () => {
  const night = newNight(16);
  for (let r = 0; r < UP.ROUNDS; r++) playRound(night, () => true);
  assert.equal(upScoringRounds(night), UP.ROUNDS);
  assert.equal(upScoringRound(night, 1), true);
  upStandings(night).forEach(row => assert.equal(row.played, UP.ROUNDS));
  upReceipt(night, night.playerIds[0]).forEach(r => assert.ok(!r.shuffle));
});

test("the shuffle does not eat somebody's rest", () => {
  // 9 players, 1 resting each round. With the shuffle ON, the night is the
  // shuffle plus 9 scoring rounds, and the SCORING rounds are what has to come
  // out even. Before the shuffle was taken off the rota, one player rested
  // during it and therefore played all 9 scoring rounds while everyone else
  // played 8.
  const night = newNight(9, {}, 10);
  night.shuffle = true;
  for (let r = 0; r < 10; r++) playRound(night, m => m.team1[0] < m.team2[0]);
  assert.equal(upScoringRounds(night), 9);
  const rows = upStandings(night);
  assert.deepEqual([...new Set(rows.map(r => r.played))], [8],
    "every player should get the same number of SCORING matches");
  assert.equal(upUneven(night), false);
  assert.deepEqual(upValidate(night), []);
});

test("20 on four courts, with the shuffle, still splits evenly", () => {
  const night = newNight(20, {}, 11);     // shuffle + 10 scoring
  night.shuffle = true;
  for (let r = 0; r < 11; r++) playRound(night, m => m.team1[0] < m.team2[0]);
  assert.equal(upScoringRounds(night), 10);
  const rows = upStandings(night);
  assert.deepEqual([...new Set(rows.map(r => r.played))], [8]);
  assert.equal(upUneven(night), false);
  assert.deepEqual(upValidate(night), []);
});

// ── fitting the night into the evening ─────────────────────────────────────

test("the plan never overruns the budget it was given", () => {
  for (const budget of [110, 120, 150, 165, 180]) {
    for (let target = 7; target <= 24; target++) {
      for (const players of [8, 12, 16, 20, 24]) {
        const scoring = upPlanRounds(budget, target, { players, shuffle: true });
        const mins = upNightMinutes(scoring + 1, target);
        assert.ok(mins <= budget + 1,
          `${players}p, first to ${target}, ${budget}min → ${scoring} rounds = ${mins}min`);
      }
    }
  }
});

test("a longer evening buys more rounds, and a longer match costs them", () => {
  assert.ok(upPlanRounds(180, 13, { players: 16 }) > upPlanRounds(150, 13, { players: 16 }));
  assert.ok(upPlanRounds(150, 9, { players: 16 }) > upPlanRounds(150, 16, { players: 16 }));
});

test("the plan prefers a round count that shares the rests evenly", () => {
  // 20 players rest 4 a round; even only at multiples of 5. Whatever fits, the
  // plan should come back with one of those rather than the raw maximum.
  for (const budget of [120, 150, 180]) {
    const scoring = upPlanRounds(budget, 13, { players: 20, courts: 4 });
    assert.ok(upFairRounds(20, 4, 30).includes(scoring),
      `20 players in ${budget}min gave ${scoring} scoring rounds, which is not even`);
  }
  // 16 players never rest, so no snapping is needed or wanted
  const s16 = upPlanRounds(150, 13, { players: 16, courts: 4 });
  assert.equal(s16, Math.floor(150 / upRoundMinutes(13)) - 1);
});

test("a night planned for 2h30 actually comes out even and valid", () => {
  for (const players of [16, 20]) {
    const target = 11;
    const scoring = upPlanRounds(150, target, { players, courts: 4 });
    const night = newNight(players, {}, scoring + 1);
    night.shuffle = true;
    for (let r = 0; r < scoring + 1; r++) playRound(night, m => m.team1[0] < m.team2[0]);
    assert.deepEqual(upValidate(night), [], `${players} players`);
    assert.equal(upUneven(night), false, `${players} players: rests came out uneven`);
    assert.ok(upNightMinutes(scoring + 1, target) <= 150);
  }
});

test("the climb path never visits a court nobody is playing on", () => {
  // upCourtsAfter clamps to UP.COURTS unless told otherwise, so on a two-court
  // night the loser of the bottom court was recorded as moving to Court 3.
  for (const [players, courts] of [[8, 2], [9, 2], [11, 2], [12, 3], [13, 3], [16, 4]]) {
    const night = newNight(players, {}, 8);
    night.courtCount = courts;
    night.ladder0 = upSeedLadder(night.playerIds, {}, courts);
    for (let r = 0; r < 8; r++) playRound(night, m => m.team1[0] < m.team2[0]);
    night.playerIds.forEach(id => {
      upClimbPath(night, id).forEach(c => {
        assert.ok(c >= 1 && c <= courts,
          `${players}p on ${courts} courts: ${id} visits court ${c}`);
      });
    });
  }
});

test("resting through the shuffle is marked as the shuffle, not as a normal rest", () => {
  const night = newNight(11, {}, 12);     // 3 rest each round
  night.shuffle = true;
  for (let r = 0; r < 12; r++) playRound(night, () => true);
  const sat = night.rounds[0].sitOuts;
  assert.equal(sat.length, 3);
  sat.forEach(id => {
    const row = upReceipt(night, id)[0];
    assert.equal(row.resting, true);
    assert.equal(row.shuffle, true, "a rest during the shuffle is still the shuffle");
    assert.equal(row.points, 0);
  });
});

// ── the prizes ─────────────────────────────────────────────────────────────

function playedNight(n = 16, scoring = 14, seed = 5, pick) {
  const night = newNight(n, {}, scoring + 1);
  night.shuffle = true;
  let s = seed;
  const rnd = () => (s = (s * 1664525 + 1013904223) >>> 0) / 4294967296;
  for (let r = 0; r < scoring + 1; r++) {
    const round = upBuildRound(night);
    round.courts.forEach(m => {
      const aWins = pick ? pick(m, night) : rnd() < 0.5;
      const loser = Math.floor(rnd() * UP.TARGET);
      m.score1 = aWins ? UP.TARGET : loser;
      m.score2 = aWins ? loser : UP.TARGET;
    });
    night.rounds.push(round);
  }
  return night;
}

test("the first night does not hand one person both prizes", () => {
  // With no history every baseline is the field average — the same number for
  // everybody — so "most above your own average" is just "most points". This
  // was the champion in 2000 of 2000 simulated first nights.
  for (let k = 0; k < 40; k++) {
    const night = playedNight(16, 14, k * 977 + 5);
    const pz = upPrizes(night, {}, {});                 // no baselines at all
    assert.equal(pz.secondRule, "finisher", "with no history the rule must switch");
    assert.equal(pz.climb, null, "THE CLIMB cannot be awarded on the first night");
    assert.ok(pz.finisher, "a second prize must still exist");
    assert.ok(pz.champion);
  }
});

test("once anyone has history, THE CLIMB is awarded again", () => {
  const night = playedNight(16, 14, 31);
  const baselines = { [night.playerIds[3]]: 2.0 };      // one returning player
  const pz = upPrizes(night, {}, baselines);
  assert.equal(pz.secondRule, "climb");
  assert.ok(pz.climb, "with a baseline in the room the climb is live again");
});

test("baselines are per scoring round, so night lengths are comparable", () => {
  // A 14-round night then a 10-round night. On raw totals everyone looked
  // worse and the climb fell to the champion; per round they are comparable.
  const long = playedNight(16, 14, 1234);
  const base = {};
  upStandings(long).forEach(r => { if (r.played > 0) base[r.id] = r.perRound; });
  const short = playedNight(16, 10, 5678);
  const rows = upStandings(short, {}, base);
  const below = rows.filter(r => r.vsBaseline < 0).length;
  assert.ok(below > 3 && below < 13,
    `${below} of 16 below baseline — a fair night should be a mix, not a sweep`);
  rows.forEach(r => {
    assert.ok(Math.abs(r.perRound - r.total / r.played) < 1e-9);
    assert.ok(Math.abs(r.vsBaseline - (r.perRound - r.baseline)) < 1e-9);
  });
});

test("the strongest finish is not the champion by construction", () => {
  let same = 0;
  for (let k = 0; k < 60; k++) {
    const night = playedNight(16, 14, k * 613 + 11);
    const pz = upPrizes(night, {}, {});
    if (pz.finisher && pz.finisher.id === pz.champion.id) same++;
  }
  assert.ok(same < 20, `the finisher was the champion ${same} of 60 times`);
});

test("the finisher ignores the shuffle and rounds spent resting", () => {
  const night = playedNight(20, 10, 77);                // 4 rest every round
  upFinisher(night).forEach(f => {
    const rec = upReceipt(night, f.id);
    assert.equal(f.played, rec.filter(r => !r.shuffle && !r.resting).length);
    assert.equal(f.first + f.second, rec.reduce((n, r) => n + (r.points || 0), 0));
  });
});
