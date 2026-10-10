// Is the night FAIR? Not "does it crash" — the stress harness covers that.
// This asks whether the format hands anybody an advantage they did not earn.
//
// Every player is given IDENTICAL skill, so any difference in the final table
// is the format talking, not the padel. Four questions:
//
//   1. EQUAL PLAY     does everyone get the same number of matches?
//   2. EQUAL REST     does everyone sit out the same number of times?
//   3. THE DRAW       does where you were seeded predict how you finish?
//   4. THE ROTA       does WHEN you happen to rest predict how you finish?
//
// 1 and 2 are arithmetic and reported exactly. 3 and 4 are measured over
// thousands of nights; with equal skill both should come out at 1.00x, and
// anything above about 1.05x is the format quietly picking a winner.
//
//   node ops/uprising-fairness.js            the default sweep
//   node ops/uprising-fairness.js 4000       more nights per row
const E = require("../uprising-engine.js");

const TRIALS = Number(process.argv[2]) || 1500;
const TARGET = 11, BUDGET = 150;
let seed = 31;
const rnd = () => (seed = (seed * 1664525 + 1013904223) >>> 0) / 4294967296;

function night(n, courts, scoring, shuffle) {
  const ids = Array.from({ length: n }, () => Math.random().toString(36).slice(2, 9));
  return {
    id: "t", format: "uprising", playerIds: ids, courtCount: courts,
    numRounds: scoring + E.upShuffleRounds({ shuffle }), shuffle,
    pointsPerMatch: TARGET, ladder0: E.upSeedLadder(ids, {}, courts), rounds: [],
    restRota: E.upMakeRestRota(ids, Math.floor(rnd() * 1e9) + 1),
  };
}

function play(t) {
  while (t.rounds.length < t.numRounds) {
    const r = E.upBuildRound(t);
    r.courts.forEach(m => {
      const a = rnd() < 0.5, l = Math.floor(rnd() * TARGET);
      m.score1 = a ? TARGET : l; m.score2 = a ? l : TARGET;
    });
    t.rounds.push(r);
  }
  return t;
}

const rows = [];
const problems = [];

for (let n = 8; n <= 24; n++) {
  const courts = Math.max(2, Math.min(E.UP.COURTS, Math.floor(n / 4)));
  const scoring = E.upPlanRounds(BUDGET, TARGET, { shuffle: true, players: n, courts });

  // by seeded court, and by the court you were on when you rested
  const bySeed = {}; for (let c = 1; c <= courts; c++) bySeed[c] = { s: 0, n: 0 };
  const byRestWhen = { early: { s: 0, n: 0 }, late: { s: 0, n: 0 } };
  let playedMin = 99, playedMax = 0, restMin = 99, restMax = 0, partMin = 99, partMax = 0;
  // COURT TIME counts the shuffle; matches-each does not. They differ as
  // soon as anybody rests, and with anybody resting the total can never
  // divide the field evenly — so this column is reported, not asserted.
  let ctMin = 99, ctMax = 0;
  let uneven = 0;

  for (let t = 0; t < TRIALS; t++) {
    const T0 = night(n, courts, scoring, true);
    const seedOf = { ...T0.ladder0 };
    play(T0);
    const st = E.upStandings(T0, {});
    const pts = {}; st.forEach(r => { pts[r.id] = r.total; });
    st.forEach(r => {
      playedMin = Math.min(playedMin, r.played); playedMax = Math.max(playedMax, r.played);
      const b = bySeed[seedOf[r.id]]; if (b) { b.s += r.total; b.n++; }
    });
    if (E.upUneven(T0)) uneven++;
    const half = T0.numRounds / 2;
    T0.playerIds.forEach(id => {
      const mine = T0.rounds.filter(r => (r.sitOuts || []).includes(id));
      restMin = Math.min(restMin, mine.length); restMax = Math.max(restMax, mine.length);
      mine.forEach(r => {
        const b = r.roundNum <= half ? byRestWhen.early : byRestWhen.late;
        b.s += pts[id]; b.n++;
      });
      let ct = 0;
      T0.rounds.forEach(r => (r.courts || []).forEach(m => {
        if ([...m.team1, ...m.team2].includes(id)) ct++;
      }));
      ctMin = Math.min(ctMin, ct); ctMax = Math.max(ctMax, ct);
      const pset = new Set();
      T0.rounds.forEach(r => (r.courts || []).forEach(m => {
        const team = [m.team1, m.team2].find(x => x && x.includes(id));
        if (team) team.filter(y => y !== id).forEach(y => pset.add(y));
      }));
      partMin = Math.min(partMin, pset.size); partMax = Math.max(partMax, pset.size);
    });
  }

  const sv = Object.values(bySeed).map(o => o.s / o.n);
  const seedAdv = Math.max(...sv) / Math.min(...sv);
  const rv = [byRestWhen.early, byRestWhen.late].filter(o => o.n).map(o => o.s / o.n);
  const rotaAdv = rv.length === 2 ? Math.max(...rv) / Math.min(...rv) : 1;

  const row = {
    n, courts, rest: n - 4 * courts, scoring,
    played: playedMin === playedMax ? String(playedMax) : `${playedMin}-${playedMax}`,
    rests: restMin === restMax ? String(restMax) : `${restMin}-${restMax}`,
    partners: `${partMin}-${partMax}`,
    court: ctMin === ctMax ? String(ctMax) : `${ctMin}-${ctMax}`,
    seedAdv, rotaAdv,
    fair: playedMin === playedMax,
  };
  rows.push(row);

  if (!row.fair) problems.push(`${n}p: ${row.played} matches each — not equal play`);
  if (restMax - restMin > 1) problems.push(`${n}p: rests ${row.rests} — more than one apart`);
  if (seedAdv > 1.05) problems.push(`${n}p: the DRAW is worth ${seedAdv.toFixed(2)}x`);
  if (rotaAdv > 1.05) problems.push(`${n}p: WHEN you rest is worth ${rotaAdv.toFixed(2)}x`);
}

const h = ["players", "courts", "resting", "rounds", "scoring ea", "court time", "rests ea", "partners", "draw", "rest timing"];
const w = h.map(x => x.length);
const cell = r => [r.n, r.courts, r.rest, r.scoring + 1, r.played, r.court, r.rests, r.partners,
  r.seedAdv.toFixed(2) + "x", r.rotaAdv.toFixed(2) + "x"];
rows.forEach(r => cell(r).forEach((v, i) => { w[i] = Math.max(w[i], String(v).length); }));

console.log(`UPRISING fairness — ${TRIALS} nights per row, every player identical`);
console.log(`150-minute budget, first to ${TARGET}, one shuffle round.`);
console.log(`"draw" and "rest timing" are 1.00x when the format decides nothing.`);
console.log(`"scoring ea" is what the table is built from. "court time" adds the`);
console.log(`shuffle, which pays nothing and is kept off the rest rota on purpose —`);
console.log(`with anybody resting the total can never divide the field evenly.\n`);
console.log(h.map((x, i) => x.padStart(w[i])).join("  "));
console.log(w.map(x => "-".repeat(x)).join("  "));
rows.forEach(r => console.log(cell(r).map((v, i) => String(v).padStart(w[i])).join("  ")
  + (r.fair ? "" : "   <- uneven")));

console.log("\nROUND COUNTS THAT GIVE EVERYONE THE SAME NUMBER OF MATCHES");
console.log("-".repeat(62));
rows.filter(r => r.rest > 0).forEach(r => {
  const f = E.upFairRounds(r.n, r.courts, 24) || [];
  console.log(`  ${String(r.n).padStart(2)} players on ${r.courts} courts: `
    + (f.length ? f.join(", ") + " scoring rounds" : "none at or under 24")
    + (f.includes(r.scoring) ? `   (using ${r.scoring})` : `   !! USING ${r.scoring}, WHICH IS NOT ONE OF THEM`));
});

console.log("\nVERDICT");
console.log("-".repeat(62));
if (problems.length) {
  console.log(`  !! ${problems.length} finding(s):`);
  [...new Set(problems)].forEach(p => console.log("   - " + p));
} else {
  console.log("  Equal play, equal rest, and neither the draw nor the rest rota");
  console.log("  is worth more than 1.05x at any field size from 8 to 24.");
}
process.exit(problems.length ? 1 : 0);
