// Does the scheme favour whoever is already ahead? Equal skill, so any change
// in how often the halfway leader converts is the scheduler, not the padel.
const E = require(process.argv[2]); const [N, C, SC, T] = process.argv.slice(3).map(Number);
let seed = 9; const rnd = () => (seed = (seed * 1664525 + 1013904223) >>> 0) / 4294967296;
let leadWin = 0, top3Win = 0, comeback = 0, bottomN = 0, restLeaderLate = 0, restLeaderN = 0, restRankSum = {}, restRankN = {};
for (let k = 0; k < T; k++) {
  const ids = Array.from({ length: N }, (_, i) => 'p' + i);
  const t = { id:'t', format:'uprising', playerIds:ids, courtCount:C, numRounds:SC+1, shuffle:1, pointsPerMatch:11,
    ladder0:E.upSeedLadder(ids, {}, C), rounds:[], restRota:E.upMakeRestRota(ids, Math.floor(rnd()*1e9)+1) };
  let half = null;
  while (t.rounds.length < t.numRounds) {
    if (t.rounds.length >= 2) {
      const st = E.upStandings(t, {}); const rank = {}; st.forEach((r, i) => rank[r.id] = i);
      const r0 = E.upBuildRound(t);
      // where in the table are the people the scheduler rests?  third of the field
      const phase = t.rounds.length - 1 < SC / 2 ? 'first half' : 'second half';
      r0.sitOuts.forEach(p => { const third = Math.min(2, Math.floor(3 * rank[p] / N)); const key = phase + ' ' + ['top','mid','bottom'][third];
        restRankN[key] = (restRankN[key] || 0) + 1; });
    }
    if (t.rounds.length === 1 + Math.floor(SC / 2)) half = E.upStandings(t, {}).map(r => r.id);
    const r = E.upBuildRound(t);
    r.courts.forEach(m => { const a = rnd() < .5, l = Math.floor(rnd()*11); m.score1 = a ? 11 : l; m.score2 = a ? l : 11; });
    t.rounds.push(r);
  }
  const fin = E.upStandings(t, {}).map(r => r.id);
  if (fin[0] === half[0]) leadWin++;
  if (half.slice(0, 3).includes(fin[0])) top3Win++;
  const bottom = half.slice(Math.ceil(N / 2)); bottomN += bottom.length; comeback += bottom.filter(p => fin.slice(0, 3).includes(p)).length;
}
const p = (a, b) => (100 * a / b).toFixed(1) + '%';
console.log(`  halfway leader wins ${p(leadWin, T)} · winner was top-3 at halfway ${p(top3Win, T)} · bottom half reaches top 3 ${p(comeback, bottomN)}`);
const tot = h => ['top','mid','bottom'].reduce((s, x) => s + (restRankN[h + ' ' + x] || 0), 0);
for (const h of ['first half', 'second half']) console.log(`  rested in ${h}: ` + ['top','mid','bottom'].map(x => `${x} third ${p(restRankN[h + ' ' + x] || 0, tot(h))}`).join('  '));
