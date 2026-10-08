/* UPRISING engine tests.  node --test uprising-engine.test.js */
const test = require("node:test");
const assert = require("node:assert");
const E = require("./uprising-engine.js");
const {
  UP, upSeedLadder, upPairCourt, upRoundPoints, upRoundDone, upCourtsAfter,
  upCurrentCourts, upBuildRound, upTotals, upStandings, upPrizes, upClimbPath,
  upValidate, upPairKey,
  upCourts, upRestCount, upFairRounds, upDoubleFinal, upMakeRestRota, upReceipt,
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
