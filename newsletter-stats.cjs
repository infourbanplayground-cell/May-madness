// Richer highlight set, still computed with the app's own engine.
const fs=require('fs');
const S=require('./aa_score.cjs');
const d=JSON.parse(fs.readFileSync('aa_live2.json','utf8'));
const st=d.state||d, sessions=st.sessions, players=st.players;
const photos=(JSON.parse(fs.readFileSync('aa_photos.json','utf8')).photos)||{};
const P=id=>players.find(p=>p.id===id)||{};
const name=id=>P(id).name||'?';
const teamOf=(s,tid)=>(s.teams||[]).find(x=>x.id===tid);
const teamLbl=(s,tid)=>{const t=teamOf(s,tid);return t?`${name(t.p1Id)} & ${name(t.p2Id)}`:'?';};
const prevOf=p=>Object.values(p.prevSeriesPts||{}).reduce((a,b)=>a+(Number(b)||0),0)+(p.prevSeriesPoints||0);

const full=players.map(p=>{
  const r=S.calcPlayerStats(p.id,sessions);
  const form=S.recentForm(p.id,sessions,10);
  return {id:p.id,name:p.name,pts:r.totalPts,stats:r.stats,bd:r.breakdown,
    prev:prevOf(p), photo:!!photos[p.id],
    wins:r.stats.groupWins+r.stats.qfWins+r.stats.sfWins+r.stats.finalsWon,
    form, streak:S.currentStreak(form)};
});
const played=full.filter(e=>e.stats.sessionsPlayed>0).sort((a,b)=>b.pts-a.pts);

// rank after night 1 vs now -> movers
const after1=players.map(p=>({id:p.id,pts:S.calcPlayerStats(p.id,[sessions[0]]).totalPts}))
  .sort((a,b)=>b.pts-a.pts);
const rank1=new Map(after1.filter(x=>x.pts>0).map((x,i)=>[x.id,i+1]));
const rankNow=new Map(played.map((e,i)=>[e.id,i+1]));
const movers=played.filter(e=>rank1.has(e.id))
  .map(e=>({...e,delta:rank1.get(e.id)-rankNow.get(e.id)}))
  .sort((a,b)=>b.delta-a.delta);

const winRate=e=>e.stats.groupPlayed?Math.round(e.wins/(e.stats.groupPlayed+e.stats.qfReached+e.stats.sfReached+e.stats.finalsReached)*100):0;
const champs=sessions.map(s=>{const f=(s.bracket||{}).final; if(!f||!f.winner) return null;
  const tid=f.winner==='team1'?f.team1Id:f.team2Id; const t=teamOf(s,tid);
  return t?{s:s.name,p1:t.p1Id,p2:t.p2Id,label:teamLbl(s,tid)}:null;}).filter(Boolean);

// debutants: no points from any previous series
const debut=played.filter(e=>e.prev===0);
const champDebut=champs.flatMap(c=>[c.p1,c.p2]).filter(id=>prevOf(P(id))===0).map(name);

const out={
  leader:played[0], runnerUp:played[1],
  topClimber:movers[0]||null,
  bestRate:[...played].filter(e=>e.stats.sessionsPlayed===2).sort((a,b)=>winRate(b)-winRate(a))[0],
  mostWins:[...played].sort((a,b)=>b.wins-a.wins)[0],
  hotStreak:[...played].sort((a,b)=>b.streak-a.streak)[0],
  streakBonus:played.filter(e=>e.bd.streakPts>0).length,
  comeback:played.filter(e=>e.bd.comebackPts>0).map(e=>e.name),
  topOfGroup:[...played].sort((a,b)=>b.bd.topOfGroup-a.bd.topOfGroup)[0],
  debutants:debut.length, champDebut,
  newFaces:players.length,
  champions:champs,
  mvps:sessions.map(s=>s.mvpId?name(s.mvpId):null),
  photoIds:Object.keys(photos).length,
  top:played.slice(0,8).map((e,i)=>({rank:i+1,id:e.id,name:e.name,pts:e.pts,
    sess:e.stats.sessionsPlayed,wins:e.wins,rate:winRate(e),photo:e.photo,
    delta:rank1.has(e.id)?rank1.get(e.id)-rankNow.get(e.id):null})),
};
const brief=(e)=>e?{name:e.name,pts:e.pts,wins:e.wins,sess:e.stats.sessionsPlayed,
  rate:winRate(e),streak:e.streak,tog:e.bd.topOfGroup,delta:e.delta,photo:e.photo,id:e.id}:null;
['leader','runnerUp','topClimber','bestRate','mostWins','hotStreak','topOfGroup']
  .forEach(k=>out[k]=brief(out[k]));
console.log(JSON.stringify(out,null,1));

// ── highlights that are about DIFFERENT people ────────────────────────
// Munther tops wins, win-rate, streak and top-of-group, so naming him four
// more times is one highlight wearing five hats. These pick distinct names.
const perNight = players.map(p => ({id:p.id, name:p.name,
  best: Math.max(...sessions.map(s => S.calcPlayerStats(p.id,[s]).totalPts))}))
  .sort((a,b)=>b.best-a.best);
const excl = new Set([out.leader && out.leader.id, out.topClimber && out.topClimber.id]);
const others = played.filter(e=>!excl.has(e.id));
const extra = {
  bigNight: perNight[0],
  bestRateOther: [...others].filter(e=>e.stats.sessionsPlayed===2)
    .sort((a,b)=>winRate(b)-winRate(a))[0],
  mostWinsOther: [...others].sort((a,b)=>b.wins-a.wins)[0],
};
for (const k of Object.keys(extra)) if (extra[k] && extra[k].stats) extra[k]=brief(extra[k]);
fs.writeFileSync('news_extra.json', JSON.stringify(extra,null,1));
