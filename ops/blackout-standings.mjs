// Blackout (Vol.8) series standings, computed with the APP'S OWN scoring engine.
//
// Same approach as make-winner-data.mjs, and for the same reason: the functions
// are lifted out of blackout-index.html at run time rather than reimplemented,
// because a copy drifts the moment scoring changes and a hype post that
// disagrees with the leaderboard everyone is looking at is worse than none.
//
// It also computes what the REMAINING nights are worth, which is the whole
// point of a final-week post. That comes from DOUBLE_FROM_SESSION and
// SESSIONS_TOTAL in the app and the night list in blackout-season.json, so the
// "worth double" claim cannot be typed in wrongly.
//
//   node ops/blackout-standings.mjs <state.json> [out.json]
import fs from 'fs';
import path from 'path';

const ROOT = path.resolve(path.dirname(new URL(import.meta.url).pathname), '..');
const APP = path.join(ROOT, 'blackout-index.html');
const SEASON = JSON.parse(fs.readFileSync(path.join(ROOT, 'blackout-season.json'), 'utf8'));
const STATE = process.argv[2];
const OUT = process.argv[3];
if (!STATE) { console.error('usage: node ops/blackout-standings.mjs <state.json> [out.json]'); process.exit(1); }

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
const { calcPlayerStats, DOUBLE_FROM_SESSION, SESSIONS_TOTAL } = new Function(
  `${engine}; return { calcPlayerStats, DOUBLE_FROM_SESSION, SESSIONS_TOTAL };`)();

const raw = JSON.parse(fs.readFileSync(STATE, 'utf8'));
const st = raw.state || raw;
const sessions = st.sessions || [];
const byId = Object.fromEntries((st.players || []).map(p => [p.id, p]));

// A row per player who has played a Vol.8 night. `pts` is the SERIES total —
// the only thing the season prizes are decided on. All-time is a separate
// ladder and deliberately not mixed in here.
const row = (p, upto) => {
  const r = calcPlayerStats(p.id, upto);
  return {
    id: p.id, name: p.name, pts: r.totalPts,
    nights: r.stats.sessionsPlayed, wins: r.stats.groupWins, played: r.stats.groupPlayed,
    finals: r.stats.finalsReached, titles: r.stats.finalsWon,
    sf: r.stats.sfReached, qf: r.stats.qfReached,
  };
};
const order = (a, b) => b.pts - a.pts || b.titles - a.titles || b.nights - a.nights;

const rows = (st.players || []).map(p => row(p, sessions)).filter(x => x.nights > 0).sort(order);

// Night-by-night cumulative totals for the top of the table, so a chart can
// show the race rather than assert it. Each point is the same engine run over
// the first n sessions, never a running sum of per-night deltas — the streak
// bonus is not additive and a sum would quietly disagree with the app.
const done = sessions.filter(s => s.completed);
const trackIds = rows.slice(0, 6).map(r => r.id);
const race = trackIds.map(id => {
  const pts = done.map((_, i) => row(byId[id], sessions.slice(0, i + 1)).pts);
  // Where the line STARTS. A player who missed the opening nights sits on zero
  // through them, and a chart that draws that as a flat line along the axis
  // says they played and scored nothing — which is a different story from the
  // one the table tells. Hassan Salhi is fourth off four nights; drawing him as
  // six nights of nothing would be a lie the chart told on its own.
  const from = done.findIndex(s => row(byId[id], [s]).nights > 0);
  return { id, name: byId[id].name, pts, from, last2: pts.at(-1) - (pts.at(-3) ?? 0) };
});

// Who won each completed night, by that night's own points. "Winner" is the
// best series haul on the night, which is what the recap screens show.
const nightTop = done.map((s, i) => {
  const gained = (st.players || []).map(p => {
    const a = row(p, sessions.slice(0, i + 1)).pts;
    const b = i === 0 ? 0 : row(p, sessions.slice(0, i)).pts;
    const played = row(p, [s]).nights > 0;
    return { name: p.name, gain: a - b, played };
  }).filter(x => x.played).sort((a, b) => b.gain - a.gain);
  return { n: i + 1, date: s.date, doubled: !!s.doublePoints, teams: (s.teams || []).length,
    top: gained.slice(0, 3) };
});

const remaining = SEASON.nights.filter(d => !done.some(s => s.date === d));
const played = done.length;
const doubleNights = remaining.filter((_, i) => played + i + 1 >= DOUBLE_FROM_SESSION);

const out = {
  volume: SEASON.volume, name: SEASON.name, host: SEASON.host,
  sessionsTotal: SESSIONS_TOTAL, doubleFromSession: DOUBLE_FROM_SESSION,
  played, remaining, doubleNights, finalsDate: SEASON.finalsDate,
  seasonPrizes: SEASON.seasonPrizes, voucher: SEASON.voucher, entry: SEASON.entry,
  pool: SEASON.voucher * 2 * SEASON.sessions + SEASON.seasonPrizes.reduce((a, b) => a + b, 0),
  playersIn: rows.length, rosterSize: (st.players || []).length,
  matches: done.reduce((a, s) =>
    a + (s.groupMatches || []).filter(m => m.winner).length
      + Object.values(s.knockout || {}).flat().filter(m => m && m.winner).length, 0),
  table: rows,
  race, nightTop,
  // The form story, derived rather than chosen: who has taken the most points
  // out of the last two nights, and what the biggest single night has been
  // worth so far. The second is what makes "the last two are worth double"
  // mean something — a reader can do the arithmetic themselves.
  climber: [...race].sort((a, b) => b.last2 - a.last2)[0] || null,
  bestNight: Math.max(0, ...nightTop.map(n => (n.top[0] || { gain: 0 }).gain)),
  gap14: rows.length >= 4 ? rows[0].pts - rows[3].pts : null,
};

if (OUT) fs.writeFileSync(OUT, JSON.stringify(out, null, 2));

console.log(`${out.name} ${out.volume} — ${played}/${out.sessionsTotal} nights, `
  + `${out.matches} matches, ${out.playersIn} players in the series`);
console.log(`remaining: ${remaining.join(', ')}  (double from session ${DOUBLE_FROM_SESSION}: `
  + `${doubleNights.join(', ') || 'none'})`);
console.log('');
rows.slice(0, 12).forEach((r, i) =>
  console.log(`  ${String(i + 1).padStart(2)}. ${r.name.padEnd(22)} ${String(r.pts).padStart(4)}`
    + `   ${r.nights}n ${r.wins}/${r.played}w ${r.titles}t`));
console.log('');
nightTop.forEach(n => console.log(`  N${n.n} ${n.date}${n.doubled ? ' 2X' : '  '} `
  + `${String(n.teams).padStart(2)} teams  →  ${n.top.map(t => `${t.name} +${t.gain}`).join(', ')}`));
if (OUT) console.log(`\nwrote ${OUT}`);
