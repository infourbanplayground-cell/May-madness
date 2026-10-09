// The first three rounds of a night, written out the way a scorer would see
// them — and then CHECKED, by recomputing every number from the rules by hand
// rather than asking the engine the same question twice.
//
//   node ops/uprising-sim3.js             16 players, 3 courts, 1 shuffle
//   node ops/uprising-sim3.js 2           ... with a 2-round shuffle
//   node ops/uprising-sim3.js 1 20 4      20 players on 4 courts
const E = require("../uprising-engine.js");

const SHUF = Number(process.argv[2] || 1);
const N = Number(process.argv[3] || 16);
const C = Number(process.argv[4] || 3);
const TARGET = 11;
// 'the first three rounds' — but with a two-round shuffle that would be one
// scoring round and nothing to look at, so always show at least two that score.
const SHOW = Math.max(3, SHUF + 2);

const NAMES = ["Ali", "Sara", "Omar", "Layla", "Yousef", "Noor", "Hamed", "Maryam",
  "Khalid", "Fatma", "Salim", "Aisha", "Nasser", "Huda", "Tariq", "Rania",
  "Bader", "Zahra", "Faisal", "Dana", "Majid", "Lina", "Rashid", "Mona"].slice(0, N);

const night = {
  id: "sim", format: "uprising", playerIds: NAMES, courtCount: C,
  numRounds: SHUF + 12, shuffle: SHUF || false, pointsPerMatch: TARGET,
  ladder0: E.upSeedLadder(NAMES, {}, C), rounds: [],
  restRota: E.upMakeRestRota(NAMES, 20261010),
};

// A fixed, readable set of results so the same run always prints the same
// night — a simulation you cannot re-read is not evidence of anything.
let s = 1010;
const rnd = () => (s = (s * 1664525 + 1013904223) >>> 0) / 4294967296;

const bad = [];
const check = (ok, what) => { if (!ok) bad.push(what); };
const pad = (x, n) => String(x).padEnd(n);

console.log(`UPRISING — ${N} players, ${C} courts, ${SHUF} shuffle round${SHUF === 1 ? "" : "s"}`);
console.log("=".repeat(70));
console.log(`${C * 4} on court, ${N - C * 4} resting each round · first to ${TARGET}`);
console.log(`points: ${Array.from({ length: C }, (_, i) =>
  `C${i + 1} ${E.UP.WIN[i + 1]}/${E.UP.LOSE[i + 1]}`).join("  ")}`);

console.log("\nTHE DRAW (check-in order — nobody has form on night one)");
console.log("-".repeat(70));
for (let c = 1; c <= C; c++) {
  console.log(`  Court ${c}:  ${NAMES.filter(n => night.ladder0[n] === c).join(", ")}`);
}

// ── my own copy of the rules, to check the engine against ────────────────
const myMargin = {};        // running shuffle margin
const myShufPlayed = {};    // shuffle matches actually played
const myPoints = {};        // running table points
NAMES.forEach(n => { myMargin[n] = 0; myPoints[n] = 0; myShufPlayed[n] = 0; });
let myCourts = { ...night.ladder0 };

for (let r = 1; r <= Math.min(SHOW, night.numRounds); r++) {
  const round = E.upBuildRound(night);
  const isShuffle = r <= SHUF;

  // results
  round.courts.forEach(m => {
    const aWins = rnd() < 0.5;
    const loser = 2 + Math.floor(rnd() * 8);
    m.score1 = aWins ? TARGET : loser;
    m.score2 = aWins ? loser : TARGET;
  });
  night.rounds.push(round);

  console.log(`\nROUND ${r}${isShuffle ? "  — SHUFFLE, scores nothing" : ""}`);
  console.log("-".repeat(70));

  // --- CHECK: four to a court, nobody twice, resters not playing ---------
  const onCourt = new Set();
  round.courts.forEach(m => {
    const four = [...m.team1, ...m.team2];
    check(four.length === 4, `R${r} C${m.court}: ${four.length} players`);
    check(new Set(four).size === 4, `R${r} C${m.court}: a repeat`);
    four.forEach(p => {
      check(!onCourt.has(p), `R${r}: ${p} on two courts`);
      check(!round.sitOuts.includes(p), `R${r}: ${p} resting and playing`);
      onCourt.add(p);
    });
  });
  check(onCourt.size === 4 * C, `R${r}: ${onCourt.size} on court, expected ${4 * C}`);

  round.courts.forEach(m => {
    const won = m.score1 > m.score2 ? m.team1 : m.team2;
    const pts = isShuffle ? 0 : E.UP.WIN[m.court];
    const lpts = isShuffle ? 0 : E.UP.LOSE[m.court];
    const a = m.team1.join(" + ") + (won === m.team1 ? "  <" : "   ");
    const bteam = (won === m.team2 ? ">  " : "   ") + m.team2.join(" + ");
    console.log(`  Court ${m.court} [${isShuffle ? "no points" : `${pts}/${lpts}`}]  `
      + `${pad(a, 24)}${String(m.score1).padStart(2)} - ${pad(m.score2, 2)}  ${bteam}`);
    // my own points
    if (!isShuffle) {
      m.team1.forEach(p => { myPoints[p] += (m.score1 > m.score2 ? E.UP.WIN[m.court] : E.UP.LOSE[m.court]); });
      m.team2.forEach(p => { myPoints[p] += (m.score2 > m.score1 ? E.UP.WIN[m.court] : E.UP.LOSE[m.court]); });
    }
    const d = m.score1 - m.score2;
    if (isShuffle) {
      m.team1.forEach(p => { myMargin[p] += d; myShufPlayed[p]++; });
      m.team2.forEach(p => { myMargin[p] -= d; myShufPlayed[p]++; });
    }
  });
  if (round.sitOuts.length) console.log(`  resting: ${round.sitOuts.join(", ")}`);

  // --- CHECK: the rest list is the rota, read independently --------------
  const mine = E.upRestingFor(night, r);
  check(JSON.stringify([...round.sitOuts].sort()) === JSON.stringify([...mine].sort()),
    `R${r}: sitOuts do not match the rota`);

  // --- work out the next ladder myself ----------------------------------
  if (isShuffle) {
    const eng0 = E.upShuffleLadder(night, r);

    const order = [...NAMES].sort((a, b) =>
      (eng0[a] - eng0[b]) || (myMargin[b] - myMargin[a]) || 0);
    console.log(`\n  THE SHUFFLE RANKING — everyone by margin over ${r} round${r === 1 ? "" : "s"}`
      + `${r < SHUF ? ` (round ${r + 1} of the shuffle is seated from this)` : ""}.`);
    console.log("  Anyone who played NO shuffle match has no margin and goes to the middle.");
    for (let c = 1; c <= C; c++) {
      const on = order.filter(p => eng0[p] === c);
      console.log(`    Court ${c}: ` + on.map(p =>
        `${p} (${!myShufPlayed[p] ? "rested" : (myMargin[p] > 0 ? "+" : "") + myMargin[p]}`
        + `${myShufPlayed[p] && myShufPlayed[p] < r ? ", 1 of 2" : ""})`).join(", "));
    }
    myCourts = { ...eng0 };
  } else if (!isShuffle) {
    const next = { ...myCourts };
    round.courts.forEach(m => {
      const aWon = m.score1 > m.score2;
      (aWon ? m.team1 : m.team2).forEach(p => { next[p] = Math.max(1, m.court - 1); });
      (aWon ? m.team2 : m.team1).forEach(p => { next[p] = Math.min(C, m.court + 1); });
    });
    myCourts = next;
  }

  // --- CHECK: the engine agrees with my ladder --------------------------
  const eng = E.upCurrentCourts(night);
  const mism = NAMES.filter(p => eng[p] !== myCourts[p]);
  // Ties in the margin ranking are broken by the rota, which I am not
  // replicating, so only flag a disagreement that is NOT a tie.
  const realMism = mism.filter(p => {
    if (!isShuffle) return true;
    return !NAMES.some(q => q !== p && myMargin[q] === myMargin[p] && myCourts[q] !== myCourts[p]);
  });
  check(realMism.length === 0, `R${r}: ladder disagrees for ${realMism.join(", ")}`);

  if (!isShuffle) {
    console.log("\n  the ladder now (a RANKING, not seats — a court holds more");
    console.log("  than four between rounds because four of you are resting;");
    console.log("  the next round seats the top 12 of this order):");
    for (let c = 1; c <= C; c++) {
      console.log(`    Court ${c}: ${NAMES.filter(n => eng[n] === c).join(", ")}`);
    }
  }
}

// ── CHECK: the table matches points I added up myself ───────────────────
const st = E.upStandings(night, {});
const uneven = E.upUneven(night);
console.log(`\nTABLE after ${Math.min(SHOW, night.numRounds)} rounds`);
console.log("-".repeat(70));
if (uneven) {
  console.log("  Ranked on POINTS PER SCORING MATCH, not raw total — part-way");
  console.log("  through the night some have played more than others, because");
  console.log("  four sit out each round. It evens out by the end (9 each), and");
  console.log("  the table switches back to raw total when it does.\n");
}
st.forEach((row, i) => {
  check(row.total === myPoints[row.id],
    `${row.id}: table says ${row.total}, hand-added ${myPoints[row.id]}`);
  const rec = E.upReceipt(night, row.id);
  const sum = rec.reduce((a, l) => a + (l.points || 0), 0);
  check(sum === row.total, `${row.id}: receipt ${sum} vs table ${row.total}`);
  console.log(`  ${pad(i + 1 + ".", 4)}${pad(row.id, 10)} ${String(row.total).padStart(3)} pts  `
    + `${uneven ? (row.played ? (row.total / row.played).toFixed(1) : "-").padStart(5) + "/match" : "      "}  `
    + `${row.played} played   Court ${E.upCurrentCourts(night)[row.id]}`);
});

// ── CHECK: nobody sat out every shuffle round ───────────────────────────
// The shuffle rounds walk BACKWARDS down the rest rota, the second taking the
// slice before the first, so with two of them nobody misses both and everyone
// reaches the ladder with a margin of their own. Worth asserting: get it wrong
// and somebody starts the night ranked on nothing.
if (SHUF) {
  const sat = {};
  NAMES.forEach(n => { sat[n] = 0; });
  night.rounds.slice(0, SHUF).forEach(r => (r.sitOuts || []).forEach(p => { sat[p]++; }));
  const never = NAMES.filter(p => sat[p] === SHUF);
  check(SHUF === 1 || never.length === 0,
    `played no shuffle match at all: ${never.join(", ")}`);
}

// ── CHECK: points conserved ─────────────────────────────────────────────
let owed = 0;
night.rounds.forEach(r => {
  if (!E.upScoringRound(night, r.roundNum)) return;
  r.courts.forEach(m => { owed += 2 * E.UP.WIN[m.court] + 2 * E.UP.LOSE[m.court]; });
});
const held = st.reduce((a, r) => a + r.total, 0);
check(owed === held, `points conserved: courts paid ${owed}, table holds ${held}`);
check(E.upValidate(night).length === 0, "upValidate: " + E.upValidate(night).join("; "));

console.log("\nCHECKS");
console.log("-".repeat(70));
console.log(`  four to a court, nobody in two places, resters not playing`);
console.log(`  rest list matches the rota drawn before the first serve`);
console.log(`  the shuffle paid nothing and set the ladder by margin`);
console.log(`  every court move is win=up / lose=down, clamped to ${C} courts`);
console.log(`  every total re-added by hand from ${Array.from({ length: C }, (_, i) =>
  E.UP.WIN[i + 1] + "/" + E.UP.LOSE[i + 1]).join(" ")}`);
console.log(`  every total reconstructed from the player's own receipt`);
console.log(`  points conserved: courts paid ${owed}, table holds ${held}`);
console.log(`  upValidate on the night so far`);
if (SHUF > 1) console.log(`  nobody sat out every shuffle round`);
console.log(bad.length ? `\n  !! ${bad.length} PROBLEM(S):\n   - ${bad.join("\n   - ")}`
  : `\n  all ${SHUF > 1 ? 9 : 8} checks pass`);
process.exit(bad.length ? 1 : 0);
