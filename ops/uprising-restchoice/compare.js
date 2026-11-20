const path = process.argv[2], [N, C, SC, T] = process.argv.slice(3).map(Number);
const E = require(path);
let seed = 11; const rnd = () => (seed = (seed * 1664525 + 1013904223) >>> 0) / 4294967296;
const c = { W:0, wStay:0, wDown:0, L:0, lStay:0, lUp:0, ret:0, retDown:0, retUp:0, jump2:0, fb:0 };
const restMinMax = [99, 0]; let skillWin = 0, skillTop3 = 0;
for (let k = 0; k < T; k++) {
  const ids = Array.from({ length: N }, (_, i) => 'p' + i);
  const skill = {}; ids.forEach(p => skill[p] = rnd());   // real skill this time, to see if the best still wins
  const t = { id:'t', format:'uprising', playerIds:ids, courtCount:C, numRounds:SC+1, shuffle:1, pointsPerMatch:11,
    ladder0:E.upSeedLadder(ids, {}, C), rounds:[], restRota:E.upMakeRestRota(ids, Math.floor(rnd()*1e9)+1) };
  const last = {};
  while (t.rounds.length < t.numRounds) {
    const r = E.upBuildRound(t);
    if (r.roundNum >= 3) r.courts.forEach(m => [...m.team1, ...m.team2].forEach(id => {
      const p = last[id]; if (!p) return; const now = m.court;
      if (Math.abs(now - p.court) > 1) c.jump2++;
      if (p.round === r.roundNum - 1) {
        if (p.won && p.court > 1) { c.W++; if (now === p.court) c.wStay++; if (now > p.court) c.wDown++; }
        if (!p.won && p.court < C) { c.L++; if (now === p.court) c.lStay++; if (now < p.court) c.lUp++; }
      } else { c.ret++; if (now > p.court) c.retDown++; if (now < p.court) c.retUp++; }
    }));
    r.courts.forEach(m => {
      const s1 = skill[m.team1[0]] + skill[m.team1[1]], s2 = skill[m.team2[0]] + skill[m.team2[1]];
      const a = rnd() < 1 / (1 + Math.exp(-(s1 - s2) * 3)), l = Math.floor(rnd() * 11);
      m.score1 = a ? 11 : l; m.score2 = a ? l : 11;
      m.team1.forEach(id => last[id] = { court: m.court, won: a, round: r.roundNum });
      m.team2.forEach(id => last[id] = { court: m.court, won: !a, round: r.roundNum });
    });
    t.rounds.push(r);
  }
  c.fb += t._fallback || 0;
  const rests = {}; t.rounds.slice(1).forEach(r => r.sitOuts.forEach(p => rests[p] = (rests[p] || 0) + 1));
  ids.forEach(p => { restMinMax[0] = Math.min(restMinMax[0], rests[p] || 0); restMinMax[1] = Math.max(restMinMax[1], rests[p] || 0); });
  const st = E.upStandings(t, {});
  const best = ids.slice().sort((a, b) => skill[b] - skill[a]);
  if (st[0].id === best[0]) skillWin++;
  if (st.slice(0, 3).some(r => r.id === best[0])) skillTop3++;
}
const p = (a, b) => (100 * a / Math.max(1, b)).toFixed(1) + '%';
console.log(`  winners held ${p(c.wStay,c.W)} (${(c.wStay/T).toFixed(2)}/night)  winners pushed down ${p(c.wDown,c.W)}  losers spared ${p(c.lStay,c.L)}  losers UP ${p(c.lUp,c.L)}`);
console.log(`  returners bumped down ${p(c.retDown,c.ret)}  returners bumped up ${p(c.retUp,c.ret)}  2-court jumps ${(c.jump2/T).toFixed(2)}/night  rests per player ${restMinMax[0]}-${restMinMax[1]}  fallbacks ${(c.fb/T).toFixed(2)}/night`);
console.log(`  best player wins ${p(skillWin,T)}, top 3 ${p(skillTop3,T)}`);
