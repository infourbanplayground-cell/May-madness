// Final Vol.7 standings, computed with the app's OWN scoring engine.
//
// The functions are lifted out of september-surge-index.html at run time rather
// than reimplemented or copy-pasted into a sidecar: a copy drifts the moment the
// app's scoring changes, and a video that disagrees with the leaderboard
// everyone is looking at is worse than no video.
//
//   node make-winner-data.mjs <state.json> [out.json]
import fs from 'fs';
import path from 'path';

const APP = path.resolve('september-surge-index.html');
const STATE = process.argv[2];
const OUT = process.argv[3] || 'brand/reports/surge-podium.json';
if (!STATE) { console.error('usage: node make-winner-data.mjs <state.json> [out.json]'); process.exit(1); }

const src = fs.readFileSync(APP, 'utf8');

function lift(name) {
  const m = new RegExp(`\\nfunction ${name}\\s*\\([^)]*\\)\\s*\\{`).exec(src);
  if (!m) throw new Error(`cannot find function ${name} in the app`);
  let d = 0;
  for (let j = m.index + m[0].length - 1; j < src.length; j++) {
    if (src[j] === '{') d++;
    else if (src[j] === '}' && --d === 0) return src.slice(m.index, j + 1);
  }
  throw new Error(`unbalanced braces in ${name}`);
}
function liftConst(name) {
  const m = new RegExp(`\\nconst ${name}\\s*=\\s*[^;]+;`).exec(src);
  if (!m) throw new Error(`cannot find const ${name} in the app`);
  return m[0];
}

const FNS = ['teamWon', 'koMatchPts', 'calcStreak', 'getSessionGroups', 'getQualifyCount',
  'compareThirds', 'teamGroupResults', 'calcGroupStandings', 'calcGroupStandingsNormalized',
  'getTopOfGroup', 'getPlayerTeam', 'calcPlayerStats'];
const CONSTS = ['GROUP_COUNTED_GAMES', 'GROUPS', 'DOUBLE_FROM_SESSION', 'SESSIONS_TOTAL'];

const engine = [...FNS.map(lift), ...CONSTS.map(liftConst)].join('\n');
const calcPlayerStats = new Function(`${engine}; return calcPlayerStats;`)();

const raw = JSON.parse(fs.readFileSync(STATE, 'utf8'));
const st = raw.state || raw;

const rows = (st.players || []).map(p => {
  const r = calcPlayerStats(p.id, st.sessions);
  const prev = p.prevSeriesPts && typeof p.prevSeriesPts === 'object'
    ? Object.values(p.prevSeriesPts).reduce((a, b) => a + (Number(b) || 0), 0)
    : Number(p.prevSeriesPoints) || 0;
  return {
    id: p.id, name: p.name, pts: r.totalPts, prev,
    nights: r.stats.sessionsPlayed, wins: r.stats.groupWins,
    finals: r.stats.finalsReached, titles: r.stats.finalsWon,
    sf: r.stats.sfReached, qf: r.stats.qfReached,
  };
}).filter(x => x.nights > 0);

// Same ordering the app's leaderboard uses.
rows.sort((a, b) => b.pts - a.pts || b.titles - a.titles || b.nights - a.nights);

const sessions = (st.sessions || []).length;
const out = {
  volume: 'SEPTEMBER SURGE', vol: 'VOL.7',
  sessions,
  lastDate: (st.sessions || []).at(-1)?.date || null,
  podium: rows.slice(0, 3),
  table: rows.slice(0, 10),
  // The headline of this season: the margin at the top.
  margin: rows.length > 1 ? rows[0].pts - rows[1].pts : null,
  allTime: [...rows].sort((a, b) => (b.pts + b.prev) - (a.pts + a.prev))
    .slice(0, 5).map(x => ({ name: x.name, total: x.pts + x.prev })),
};

fs.mkdirSync(path.dirname(OUT), { recursive: true });
fs.writeFileSync(OUT, JSON.stringify(out, null, 2));
console.log(`${OUT}  ${sessions} sessions, ${rows.length} players`);
out.podium.forEach((p, i) => console.log(
  `  ${i + 1}. ${p.name.padEnd(20)} ${String(p.pts).padStart(4)} pts  `
  + `${p.nights}n ${p.wins}W ${p.titles} title${p.titles === 1 ? '' : 's'}`));
console.log(`  margin at the top: ${out.margin} point${out.margin === 1 ? '' : 's'}`);
