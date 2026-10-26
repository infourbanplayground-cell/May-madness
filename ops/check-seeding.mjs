// Prove the four-group knockout draw crosses by LETTER — A1 v D2, B1 v C2,
// C1 v B2, D1 v A2 — against a real night's results.
//
// The seeding lives inside BracketTab, so it cannot be lifted the way
// ops/blackout-standings.mjs lifts calcPlayerStats. What IS lifted is
// everything the seeding reads — the normalised group standings and the
// comparators — and the CROSS table is read out of the shipped app rather
// than retyped, so this cannot pass against a build that no longer carries it.
//
//   node ops/check-seeding.mjs [state.json]
import fs from 'fs';
import path from 'path';

const ROOT = path.resolve(path.dirname(new URL(import.meta.url).pathname), '..');
// APP= lets the check be pointed at an older build, which is how the
// 'crosses by letter' assertion was proved to fail against the merit seeding.
const APP = process.env.APP || path.join(ROOT, 'blackout-index.html');
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
const liftConst = (name) => {
  const m = new RegExp(`\\nconst ${name}\\s*=\\s*[^;]+;`).exec(src);
  if (!m) throw new Error(`cannot find const ${name}`);
  return m[0];
};

const engine = [
  ...['teamWon', 'getSessionGroups', 'getQualifyCount', 'compareThirds', 'teamGroupResults',
      'calcGroupStandings', 'calcGroupStandingsNormalized'].map(lift),
  ...['GROUP_COUNTED_GAMES', 'GROUPS'].map(liftConst),
].join('\n');
const E = new Function(`${engine}; return { getSessionGroups, getQualifyCount,
  calcGroupStandingsNormalized, compareThirds };`)();

// The pairing table as the app actually ships it. Retyping it here would let
// the app drift back to merit seeding with this check still green.
const mCross = /const CROSS = (\[\[.*?\]\]);/.exec(src);
if (!mCross) { console.error('FAIL: the app no longer carries a CROSS pairing table'); process.exit(1); }
const CROSS = JSON.parse(mCross[1]);

const STATE = process.argv[2]
  || '/tmp/claude-0/-home-user-May-madness/0e44f0ad-a683-5f0d-9de6-9459ae328963/scratchpad/bo-ko2.json';
const raw = JSON.parse(fs.readFileSync(STATE, 'utf8'));
const st = raw.state || raw;
const players = Object.fromEntries((st.players || []).map(p => [p.id, p.name]));

// The seeding, exactly as BracketTab runs it for 4 groups / top 2.
function seed(session) {
  const groups = E.getSessionGroups(session);
  const standings = groups.map(g => E.calcGroupStandingsNormalized(session, g));
  const mkTier = (rank) => standings.map((s, i) => s[rank]?.team?.id
    ? { id: s[rank].team.id, seed: groups[i] + (rank + 1), group: groups[i] } : null);
  const winners = mkTier(0), runners = mkTier(1);
  if (winners.some(w => !w) || runners.some(r => !r)) return null;
  return CROSS.map(([w, r], i) => ({ slot: i + 1, a: winners[w], b: runners[r] }));
}

let fails = 0;
const four = (st.sessions || []).filter(s =>
  (s.groupCount || 4) === 4 && (s.qualifyCount || 2) === 2
  && (s.groupMatches || []).some(m => m.winner));

if (!four.length) { console.error('no four-group night with results to check'); process.exit(1); }

for (const session of four) {
  const teams = Object.fromEntries((session.teams || []).map(t => [t.id, t]));
  const nm = (t) => t ? `${(players[teams[t.id].p1Id] || '?').split(' ')[0]} & `
                      + `${(players[teams[t.id].p2Id] || '?').split(' ')[0]}` : '—';
  const qf = seed(session);
  console.log(`\n${session.date}  ${(session.groupMatches || []).filter(m => m.winner).length} group results`);
  if (!qf) { console.log('  not enough results to seed — skipped'); continue; }

  const bad = [];
  const groups = E.getSessionGroups(session);
  for (const m of qf) {
    console.log(`  QF${m.slot}  ${m.a.seed} ${nm(m.a).padEnd(22)} v  ${m.b.seed} ${nm(m.b)}`);
    // The label must name the team's OWN group. The bracket stored on the
    // server tonight has "B2" against a team from group D, which is what a
    // seed string copied from a slot rather than from a team looks like.
    if (m.a.seed !== teams[m.a.id].group + '1') bad.push(`QF${m.slot} first is labelled ${m.a.seed} but sits in group ${teams[m.a.id].group}`);
    if (m.b.seed !== teams[m.b.id].group + '2') bad.push(`QF${m.slot} second is labelled ${m.b.seed} but sits in group ${teams[m.b.id].group}`);
    // No quarter-final may repeat a group match.
    if (teams[m.a.id].group === teams[m.b.id].group) bad.push(`QF${m.slot} is two teams out of group ${teams[m.a.id].group}`);
  }
  // The owner's rule, stated as letters rather than as indices.
  const want = [[groups[0], groups[3]], [groups[1], groups[2]],
                [groups[2], groups[1]], [groups[3], groups[0]]];
  qf.forEach((m, i) => {
    const got = [teams[m.a.id].group, teams[m.b.id].group];
    if (got[0] !== want[i][0] || got[1] !== want[i][1])
      bad.push(`QF${i + 1} is ${got[0]}1 v ${got[1]}2, should be ${want[i][0]}1 v ${want[i][1]}2`);
  });
  // Every qualifier appears exactly once.
  const ids = qf.flatMap(m => [m.a.id, m.b.id]);
  if (new Set(ids).size !== 8) bad.push('a team appears twice in the draw');
  // The halves: slots 1-2 feed SF1, 3-4 feed SF2.
  console.log(`  SF1 <- QF1/QF2 (${groups[0]}1 half)   SF2 <- QF3/QF4 (${groups[2]}1 half)`);

  if (bad.length) { fails++; bad.forEach(b => console.log('  FAIL ' + b)); }
  else console.log('  ok — crosses by letter, no group meets itself, labels match');
}

console.log(fails ? `\n${fails} failing night(s)` : '\nseeding ok');
process.exit(fails ? 1 : 0);
