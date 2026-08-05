// Newsletter figures, computed with the app's OWN scoring engine (aa_score.cjs
// extracted verbatim from august-attack-index.html) so nothing can disagree
// with the live leaderboard.
const fs=require('fs');
const S=require('./aa_score.cjs');
const d=JSON.parse(fs.readFileSync('aa_live2.json','utf8'));
const st=d.state||d;
const sessions=st.sessions, players=st.players;
const name=id=>(players.find(p=>p.id===id)||{}).name||'?';
const teamLbl=(s,tid)=>{const t=(s.teams||[]).find(x=>x.id===tid);return t?`${name(t.p1Id)} & ${name(t.p2Id)}`:'?';};

const board=players.map(p=>{
  const r=S.calcPlayerStats(p.id,sessions);
  const prev=Object.values(p.prevSeriesPts||{}).reduce((a,b)=>a+(Number(b)||0),0)+(p.prevSeriesPoints||0);
  return {p,pts:r.totalPts,stats:r.stats,bd:r.breakdown,prev};
}).sort((a,b)=>b.pts-a.pts);

const played=board.filter(e=>e.stats.sessionsPlayed>0);
const out={
  sessions:sessions.map(s=>{
    const b=s.bracket||{};
    const gm=s.groupMatches||{};
    const allG=Object.values(gm).flat ? Object.values(gm).flat() : [];
    const ko=[...(b.qf||[]),...(b.sf||[]),b.final].filter(Boolean);
    return {name:s.name,date:s.date,teams:(s.teams||[]).length,
      groupMatches:allG.length, koMatches:ko.filter(m=>m.winner).length,
      champion:b.final&&b.final.winner?teamLbl(s,b.final.winner==='team1'?b.final.team1Id:b.final.team2Id):null,
      runnerUp:b.final&&b.final.winner?teamLbl(s,b.final.winner==='team1'?b.final.team2Id:b.final.team1Id):null,
      finalScore:b.final&&b.final.score?`${b.final.score.t1}-${b.final.score.t2}`:null,
      mvp:s.mvpId?name(s.mvpId):null, photos:(s.photos||[]).length,
      double:!!s.doublePoints};
  }),
  totals:{players:players.length, ranked:played.length,
    matches:sessions.reduce((n,s)=>{const gm=s.groupMatches||{};const g=Object.values(gm).flat?Object.values(gm).flat():[];
      const b=s.bracket||{};const ko=[...(b.qf||[]),...(b.sf||[]),b.final].filter(m=>m&&m.winner);
      return n+g.filter(m=>m&&m.winner).length+ko.length;},0)},
  top:played.slice(0,10).map((e,i)=>({rank:i+1,name:e.p.name,pts:e.pts,
    sess:e.stats.sessionsPlayed,
    wins:e.stats.groupWins+e.stats.qfWins+e.stats.sfWins+e.stats.finalsWon,
    finals:e.stats.finalsReached, titles:e.stats.finalsWon, allTime:e.pts+e.prev})),
  bothNights: played.filter(e=>e.stats.sessionsPlayed===2).length,
  oneNight: played.filter(e=>e.stats.sessionsPlayed===1).length,
};
console.log(JSON.stringify(out,null,1));
