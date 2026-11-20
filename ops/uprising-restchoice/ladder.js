// Does the ladder do what the poster says — win and you go up, lose and you go
// down — round by round, for a given field? Equal skill, random results.
const E = require(process.argv[6] || '../../uprising-engine.js');
const [N, C, SCORING, TRIALS] = process.argv.slice(2).map(Number);
let seed = 11; const rnd = () => (seed = (seed * 1664525 + 1013904223) >>> 0) / 4294967296;
const c = { wUp:0, wStay:0, wDown:0, wTop:0, lDown:0, lStay:0, lUp:0, lBot:0, ret:0, retMoved2:0, jump2:0 };
let stuckRounds = 0, rounds = 0, nightsWithStuck = 0;
const stuckBy = {}; // court -> count of winners who stayed
for (let k = 0; k < TRIALS; k++) {
  const ids = Array.from({ length: N }, (_, i) => 'p' + i);
  const t = { id:'t', format:'uprising', playerIds:ids, courtCount:C, numRounds:SCORING+1, shuffle:1,
    pointsPerMatch:11, ladder0:E.upSeedLadder(ids, {}, C), rounds:[], restRota:E.upMakeRestRota(ids, Math.floor(rnd()*1e9)+1) };
  const last = {}; // id -> {court, won, round}
  let stuckThisNight = false;
  while (t.rounds.length < t.numRounds) {
    const r = E.upBuildRound(t);
    // compare where each player was put against where they last played
    if (r.roundNum >= 3) { // round 2 is seated from the shuffle margins
      let stuck = false;
      r.courts.forEach(m => [...m.team1, ...m.team2].forEach(id => {
        const p = last[id]; if (!p) return;
        const now = m.court;
        if (p.round === r.roundNum - 1) {
          if (p.won) {
            if (p.court === 1) { c.wTop++; return; }
            if (now < p.court) c.wUp++; else if (now === p.court) { c.wStay++; stuck = true; stuckBy[p.court]=(stuckBy[p.court]||0)+1; } else c.wDown++;
          } else {
            if (p.court === C) { c.lBot++; return; }
            if (now > p.court) c.lDown++; else if (now === p.court) c.lStay++; else c.lUp++;
          }
          if (Math.abs(now - p.court) > 1) c.jump2++;
        } else { c.ret++; if (Math.abs(now - p.court) > 1) c.retMoved2++; }
      }));
      rounds++; if (stuck) { stuckRounds++; stuckThisNight = true; }
    }
    r.courts.forEach(m => {
      const a = rnd() < 0.5, l = Math.floor(rnd() * 11);
      m.score1 = a ? 11 : l; m.score2 = a ? l : 11;
      m.team1.forEach(id => last[id] = { court: m.court, won: a, round: r.roundNum });
      m.team2.forEach(id => last[id] = { court: m.court, won: !a, round: r.roundNum });
    });
    t.rounds.push(r);
  }
  if (stuckThisNight) nightsWithStuck++;
}
const pct = (a, b) => (100 * a / Math.max(1, b)).toFixed(1) + '%';
const W = c.wUp + c.wStay + c.wDown, L = c.lDown + c.lStay + c.lUp;
console.log(`${N} players, ${C} courts, ${SCORING} scoring rounds, ${TRIALS} nights`);
console.log(`  winners who could climb: ${W}  up ${pct(c.wUp,W)}  STAYED ${pct(c.wStay,W)}  pushed DOWN ${pct(c.wDown,W)}`);
console.log(`    stayed, by court they won on: ` + Object.entries(stuckBy).map(([k,v]) => `C${k} ${v}`).join('  '));
console.log(`  losers who could drop:   ${L}  down ${pct(c.lDown,L)}  stayed ${pct(c.lStay,L)}  went UP ${pct(c.lUp,L)}`);
console.log(`  returners from a rest: ${c.ret}, moved 2+ courts ${pct(c.retMoved2,c.ret)}`);
console.log(`  rounds with a stuck winner: ${pct(stuckRounds,rounds)} · nights with at least one: ${pct(nightsWithStuck,TRIALS)}`);
console.log(`  per night: ${(c.wStay/TRIALS).toFixed(2)} stuck winners, ${(c.wDown/TRIALS).toFixed(2)} winners pushed down`);
