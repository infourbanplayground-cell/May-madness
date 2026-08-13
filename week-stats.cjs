// Week stats for the recap, computed with the app's OWN engine so nothing on
// the video can disagree with the RANK tab.
const fs = require('fs');
const E = require('./aa_score.cjs');
const SC = '/tmp/claude-0/-home-user-May-madness/0e44f0ad-a683-5f0d-9de6-9459ae328963/scratchpad';
const st = JSON.parse(fs.readFileSync(SC + '/aa_now.json', 'utf8'));

const names = Object.fromEntries(st.players.map(p => [p.id, p.name]));
const sessions = st.sessions;
const WEEK = sessions.slice(2);          // sessions 3 and 4
const BEFORE = sessions.slice(0, 2);     // the table as it stood before the week

const teamOf = (s, tid) => (s.teams || []).find(t => t.id === tid);
const pairName = (s, tid) => {
  const t = teamOf(s, tid);
  return t ? `${names[t.p1Id]} & ${names[t.p2Id]}` : '?';
};

// Every match played this week, group and knockout alike.
const allMatches = [];
for (const s of WEEK) {
  for (const m of (s.groupMatches || [])) allMatches.push({ s, m, round: 'GROUP' });
  for (const r of ['qf', 'sf']) for (const m of (s.bracket?.[r] || [])) allMatches.push({ s, m, round: r.toUpperCase() });
  if (s.bracket?.final) allMatches.push({ s, m: s.bracket.final, round: 'FINAL' });
}
const played = allMatches.filter(x => x.m.winner && x.m.score);

const games = played.reduce((n, x) => n + x.m.score.t1 + x.m.score.t2, 0);

// Closest and most one-sided results of the week.
const withMargin = played.map(x => {
  const { t1, t2 } = x.m.score;
  const win = x.m.winner === 'team1' ? x.m.team1Id : x.m.team2Id;
  const lose = x.m.winner === 'team1' ? x.m.team2Id : x.m.team1Id;
  return { ...x, margin: Math.abs(t1 - t2), hi: Math.max(t1, t2), lo: Math.min(t1, t2), win, lose };
});
const oneGame = withMargin.filter(x => x.margin === 1);
const biggest = withMargin.slice().sort((a, b) => b.margin - a.margin || b.hi - a.hi)[0];

// Per-player week form.
const wk = {};
for (const x of played) {
  for (const tid of [x.m.team1Id, x.m.team2Id]) {
    const t = teamOf(x.s, tid); if (!t) continue;
    const won = (x.m.winner === 'team1' ? x.m.team1Id : x.m.team2Id) === tid;
    for (const pid of [t.p1Id, t.p2Id]) {
      if (!pid) continue;
      wk[pid] ||= { pid, name: names[pid], w: 0, l: 0, gf: 0, ga: 0, sess: new Set() };
      wk[pid].sess.add(x.s.id);
      won ? wk[pid].w++ : wk[pid].l++;
      const isT1 = x.m.team1Id === tid;
      wk[pid].gf += isT1 ? x.m.score.t1 : x.m.score.t2;
      wk[pid].ga += isT1 ? x.m.score.t2 : x.m.score.t1;
    }
  }
}
const wkArr = Object.values(wk).map(p => ({ ...p, sessions: p.sess.size, played: p.w + p.l,
  rate: Math.round((p.w / (p.w + p.l)) * 100) }));

const mostWins = wkArr.slice().sort((a, b) => b.w - a.w || b.gf - b.ga - (a.gf - a.ga))[0];
const bestRate = wkArr.filter(p => p.played >= 4).sort((a, b) => b.rate - a.rate || b.w - a.w)[0];

// Series table before and after the week. Sorted exactly the way the app's RANK
// tab sorts (totalPts desc, no tiebreak) so nothing on the video can disagree
// with the screen. Players with no sessions are dropped after ranking, not
// before — they score 0 and sit at the bottom either way.
const table = (ss) => st.players
  .map(p => { const s = E.calcPlayerStats(p.id, ss);
              return { id: p.id, name: p.name, points: s.totalPts, ...s.stats }; })
  .sort((a, b) => b.points - a.points)
  .map((p, i) => ({ ...p, rank: i + 1 }))
  .filter(p => p.sessionsPlayed > 0);

const after = table(sessions), before = table(BEFORE);
const rankBefore = Object.fromEntries(before.map(p => [p.id, p.rank]));
const climbers = after
  .filter(p => rankBefore[p.id])
  .map(p => ({ ...p, delta: rankBefore[p.id] - p.rank }))
  .sort((a, b) => b.delta - a.delta);

// Anyone whose very first appearance was this week.
const seenBefore = new Set();
for (const s of BEFORE) for (const t of (s.teams || [])) { seenBefore.add(t.p1Id); seenBefore.add(t.p2Id); }
const debut = [...new Set(WEEK.flatMap(s => (s.teams || []).flatMap(t => [t.p1Id, t.p2Id])))]
  .filter(p => p && !seenBefore.has(p));

const out = {
  matches: played.length,
  games,
  teams: WEEK.reduce((n, s) => n + (s.teams || []).length, 0),
  players: new Set(WEEK.flatMap(s => (s.teams || []).flatMap(t => [t.p1Id, t.p2Id]))).size,
  debutants: debut.length,
  oneGameThrillers: oneGame.length,
  biggest: biggest && { score: `${biggest.hi}-${biggest.lo}`, round: biggest.round,
                        winner: pairName(biggest.s, biggest.win), loser: pairName(biggest.s, biggest.lose) },
  mostWins: mostWins && { name: mostWins.name, w: mostWins.w, played: mostWins.played, rate: mostWins.rate },
  bestRate: bestRate && { name: bestRate.name, rate: bestRate.rate, w: bestRate.w, played: bestRate.played },
  topClimber: climbers[0] && { name: climbers[0].name, delta: climbers[0].delta, rank: climbers[0].rank, points: climbers[0].points },
  top3: after.slice(0, 3).map(p => ({ name: p.name, points: p.points, rank: p.rank })),
  ranked: after.length,
  champions: WEEK.map(s => {
    const f = s.bracket.final;
    const w = f.winner === 'team1' ? f.team1Id : f.team2Id;
    return { session: s.name, date: s.date, pair: pairName(s, w),
             score: `${Math.max(f.score.t1, f.score.t2)}-${Math.min(f.score.t1, f.score.t2)}` };
  }),
};
fs.writeFileSync(SC + '/week_stats.json', JSON.stringify(out, null, 1));
console.log(JSON.stringify(out, null, 1));
