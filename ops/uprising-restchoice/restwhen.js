// With EQUAL skill, does the round you first rest in predict winning the night?
// Every group should win its fair share (1.00x). The app choosing rests is only
// fair if this stays flat.
const E = require(process.argv[2]); const [N, C, SC, T] = process.argv.slice(3).map(Number);
let seed = 5; const rnd = () => (seed = (seed * 1664525 + 1013904223) >>> 0) / 4294967296;
const g = {}; let courtRest = {};   // court you were standing on when you rested -> wins / count
const win = {}; let players = 0;
for (let k = 0; k < T; k++) {
  const ids = Array.from({ length: N }, (_, i) => 'p' + i);
  const t = { id:'t', format:'uprising', playerIds:ids, courtCount:C, numRounds:SC+1, shuffle:1, pointsPerMatch:11,
    ladder0:E.upSeedLadder(ids, {}, C), rounds:[], restRota:E.upMakeRestRota(ids, Math.floor(rnd()*1e9)+1) };
  const restCourt = {};
  while (t.rounds.length < t.numRounds) {
    const before = E.upCurrentCourts(t);
    const r = E.upBuildRound(t);
    if (r.roundNum > 1) r.sitOuts.forEach(p => { (restCourt[p] = restCourt[p] || []).push(before[p] || C); });
    r.courts.forEach(m => { const a = rnd() < .5, l = Math.floor(rnd()*11); m.score1 = a ? 11 : l; m.score2 = a ? l : 11; });
    t.rounds.push(r);
  }
  const st = E.upStandings(t, {}); const champ = st[0].id;
  // tied leaders share the title
  const top = st.filter(r => (r.ppr ?? r.avg ?? r.total) === (st[0].ppr ?? st[0].avg ?? st[0].total)).map(r => r.id);
  ids.forEach(p => {
    const first = t.rounds.findIndex((r, i) => i > 0 && r.sitOuts.includes(p));
    const key = first; g[key] = g[key] || { w: 0, n: 0 }; g[key].n++; if (top.includes(p)) g[key].w += 1 / top.length;
    (restCourt[p] || []).forEach(c => { courtRest[c] = courtRest[c] || { w: 0, n: 0 }; courtRest[c].n++; if (top.includes(p)) courtRest[c].w += 1 / top.length; });
  });
}
const fair = 1 / N;
const line = (o, lab) => Object.keys(o).sort((a, b) => a - b).map(k => `${lab}${k} ${(o[k].w / o[k].n / fair).toFixed(2)}x`).join('  ');
const spread = o => { const v = Object.values(o).map(x => x.w / x.n / fair); return (Math.max(...v) / Math.min(...v)).toFixed(2); };
console.log('  first rest in round: ' + line(g, 'R') + `   spread ${spread(g)}x`);
console.log('  rested while on court: ' + line(courtRest, 'C') + `   spread ${spread(courtRest)}x`);
