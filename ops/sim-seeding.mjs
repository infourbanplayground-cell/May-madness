// SIMULATE A NIGHT'S DRAW AND KNOCKOUT for a given number of teams, against
// the SHIPPED app's own functions.
//
//   node ops/sim-seeding.mjs 13              # 13 teams, both group shapes
//   node ops/sim-seeding.mjs 13 4            # just 4 groups
//   NIGHTS=4000 node ops/sim-seeding.mjs 13  # also run the fairness sweep
//
// WHY THIS EXISTS. "Does 13 teams work?" is three different questions and only
// one of them is about the bracket:
//
//   1. Does the DRAW produce legal groups and a legal knockout — eight
//      distinct qualifiers, no quarter-final between two teams out of the same
//      group, no quarter-final that merely replays a group match?
//   2. How many matches is the night, which is how long it runs?
//   3. Is it FAIR — because 13 does not divide by 4, so the groups come out
//      uneven, and this app pays for an undersized group with notional 6-0
//      BYE WINS (GROUP_COUNTED_GAMES = 3, i.e. the shape it is designed
//      around is groups of four). Those byes are worth 3 series points and a
//      win, and they are awarded by GROUP, not by anything a team did.
//
// Question 3 is the one no structural check in this repo asks, and it is the
// one that decides which shape to run. So the sweep gives every team identical
// skill and measures whether the group you were drawn into predicts your
// night — anything that shows up is the format, not the padel.
//
// NOTHING HERE RETYPES A RULE. The engine is lifted out of the built app at
// run time (the trick ops/blackout-standings.mjs uses), the serpentine is
// lifted as source text because it lives inside a component, and the CROSS and
// SEED_PAIRS tables are read out of the file — so a build that changed any of
// them cannot pass this unnoticed.
import fs from 'fs';
import path from 'path';

const ROOT = path.resolve(path.dirname(new URL(import.meta.url).pathname), '..');
const APP = process.env.APP || path.join(ROOT, 'national-index.html');
const src = fs.readFileSync(APP, 'utf8');

function lift(name) {
  const m = new RegExp(`\\nfunction ${name}\\s*\\([^)]*\\)\\s*\\{`).exec(src);
  if (!m) throw new Error(`cannot find function ${name} in ${path.basename(APP)}`);
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
// The serpentine lives inside TeamsTab as an arrow function, so it cannot be
// lifted by name the way a top-level function can. Lift its SOURCE and close
// it over the groups list — retyping the snake here is how this check would
// come to disagree with the app it is meant to be testing.
function liftSnake() {
  const m = /\n  const serpentineFromOrder = \(ordered, allTeams\) => \{/.exec(src);
  if (!m) throw new Error('cannot find serpentineFromOrder in the app');
  let d = 0;
  for (let j = m.index + m[0].length - 1; j < src.length; j++) {
    if (src[j] === '{') d++;
    else if (src[j] === '}' && --d === 0) return src.slice(m.index, j + 2);
  }
  throw new Error('unbalanced braces in serpentineFromOrder');
}

const engine = [
  ...['teamWon', 'getSessionGroups', 'getQualifyCount', 'compareThirds',
      'teamGroupResults', 'calcGroupStandings', 'calcGroupStandingsNormalized',
      'equalizeThirds', 'seedStandardBracket', 'scoreToResult', 'groupFixtures',
      'qualifyingTeamIds'].map(lift),
  ...['GROUP_COUNTED_GAMES', 'GROUPS', 'SEED_PAIRS'].map(liftConst),
].join('\n');
const E = new Function(`${engine}
  return { getSessionGroups, getQualifyCount, calcGroupStandings,
           calcGroupStandingsNormalized, compareThirds, equalizeThirds,
           seedStandardBracket, scoreToResult, groupFixtures, qualifyingTeamIds,
           teamGroupResults, GROUP_COUNTED_GAMES, GROUPS };`)();

const mCross = /const CROSS = (\[\[.*?\]\]);/.exec(src);
if (!mCross) { console.error('FAIL: the app no longer carries a CROSS pairing table'); process.exit(1); }
const CROSS = JSON.parse(mCross[1]);

const snakeSrc = liftSnake();
const makeSnake = (groups) =>
  new Function('groups', `${snakeSrc}; return serpentineFromOrder;`)(groups);

// ---------------------------------------------------------------- the night

// Deterministic so two runs are comparable; seeded per night in the sweep.
function rng(seed) {
  let s = seed >>> 0;
  return () => { s ^= s << 13; s ^= s >>> 17; s ^= s << 5; s >>>= 0; return s / 4294967296; };
}

// A padel group match to 6. The loss type is DERIVED by the app from the
// score, never chosen here — scoreToResult owns that mapping.
function playMatch(id, a, b, rnd, skill) {
  const pa = skill ? skill[a.id] : 0.5, pb = skill ? skill[b.id] : 0.5;
  const aWins = rnd() < (pa / (pa + pb));
  const loser = [0, 1, 2, 3, 4, 5][Math.floor(rnd() * 6)];
  const [s1, s2] = aWins ? [6, loser] : [loser, 6];
  return { id, team1Id: a.id, team2Id: b.id, group: a.group, ...E.scoreToResult(s1, s2) };
}

function buildNight(nTeams, groupCount, seed, skill, mode = 'best2') {
  const rnd = rng(seed);
  const groups = E.GROUPS.slice(0, groupCount);
  const snake = makeSnake(groups);
  // Seed order is the app's own: by all-time rank. With equal skill the order
  // carries no information, which is the point of the sweep.
  const raw = Array.from({ length: nTeams }, (_, i) => ({ id: `t${i + 1}`, name: `Team ${i + 1}` }));
  const teams = snake(raw, raw);
  const session = { groupCount, qualifyCount: 2, thirdPlaceMode: mode, teams, groupMatches: [] };
  let n = 0;
  groups.forEach(g => {
    const inG = teams.filter(t => t.group === g);
    for (let i = 0; i < inG.length; i++)
      for (let j = i + 1; j < inG.length; j++)
        session.groupMatches.push(playMatch(`m${++n}`, inG[i], inG[j], rnd, skill));
  });
  return { session, groups, rnd };
}

// The knockout seeding, run the way BracketTab runs it for the two shapes a
// 13-team night can take. CROSS and SEED_PAIRS come out of the shipped file.
function seedQF(session, groups) {
  const standings = groups.map(g => E.calcGroupStandingsNormalized(session, g));
  const N = groups.length;
  const mkTier = (rank) => standings.map((s, i) => s[rank]?.team?.id
    ? { id: s[rank].team.id, seed: groups[i] + (rank + 1), group: groups[i],
        pts: s[rank].pts, wins: s[rank].wins, gd: s[rank].gd || 0, gf: s[rank].gf || 0 }
    : null);

  if (N === 4) {
    const winners = mkTier(0), runners = mkTier(1);
    if (winners.some(w => !w) || runners.some(r => !r)) return null;
    return { qf: CROSS.map(([w, r], i) => ({
      slot: i + 1, a: winners[w], b: runners[r],
      s1: winners[w].seed, s2: runners[r].seed,
    })), playoff: null };
  }
  if (N === 3) {
    const t1 = mkTier(0).filter(Boolean).sort(E.compareThirds);
    const t2 = mkTier(1).filter(Boolean).sort(E.compareThirds);
    const thirds = mkTier(2).filter(Boolean).sort(E.compareThirds);
    if (t1.length < 3 || t2.length < 3 || thirds.length < 3) return null;
    // PLAYOFF mode is a different bracket from best2 and has to be simulated as
    // itself: the BEST third takes seed 7 outright and the other two play a
    // qualifier for seed 8. In best2 the third-best third is simply out.
    const playoff = session.thirdPlaceMode === 'playoff';
    const tier3 = playoff
      ? [thirds[0], { id: 'PLAYOFF_TBD', seed: 'Q' }]
      : thirds.slice(0, 2);
    const pairing = E.seedStandardBracket([t1, t2, tier3]);
    if (!pairing) return null;
    return {
      qf: pairing.map(p => ({ slot: p.slot, a: p.a, b: p.b, s1: p.a.seed, s2: p.b.seed })),
      playoff: playoff ? { a: thirds[1], b: thirds[2] } : null,
    };
  }
  return null;
}

// ------------------------------------------------------------- the checks

function check(nTeams, groupCount, seed = 56, mode = 'best2') {
  const { session, groups } = buildNight(nTeams, groupCount, seed, null, mode);
  const sizes = groups.map(g => session.teams.filter(t => t.group === g).length);
  const fx = groups.map(g => E.groupFixtures(session, g).total);
  const fails = [];
  const notes = [];

  // Every team in exactly one group, and the snake cannot leave a gap.
  const placed = session.teams.filter(t => groups.includes(t.group)).length;
  if (placed !== nTeams) fails.push(`${nTeams - placed} team(s) not placed in a group`);
  if (Math.max(...sizes) - Math.min(...sizes) > 1)
    fails.push(`group sizes differ by more than one: ${sizes.join('/')}`);
  if (Math.min(...sizes) < 3)
    fails.push(`a group of ${Math.min(...sizes)} cannot produce a 1st, 2nd and 3rd`);

  // The byes an undersized group is paid, which is the fairness question.
  const G = E.GROUP_COUNTED_GAMES;
  const byGroupByes = {};
  groups.forEach((g, i) => { byGroupByes[g] = Math.max(0, G - Math.max(0, sizes[i] - 1)); });
  const byed = groups.filter(g => byGroupByes[g] > 0);
  const dropped = groups.filter((g, i) => sizes[i] - 1 > G);

  const qual = E.qualifyingTeamIds(session);
  if (qual.size !== 8) fails.push(`${qual.size} qualifiers, not 8`);

  const seeded = seedQF(session, groups);
  const qf = seeded && seeded.qf;
  const playoff = seeded && seeded.playoff;
  if (!qf) { fails.push('the quarter-finals could not be seeded'); return { fails, notes, sizes, fx, qf: null, playoff: null, session, groups, byGroupByes, byed, dropped }; }

  // Nobody twice, nobody who did not qualify.
  const inKo = qf.flatMap(m => [m.a.id, m.b.id]);
  if (new Set(inKo).size !== 8) fails.push('a team appears twice in the quarter-finals');
  // In playoff mode one slot is the qualifier's winner and has no team yet;
  // asserting it against qualifyingTeamIds would fail on a TBD, not a fault.
  inKo.filter(id => id !== 'PLAYOFF_TBD').forEach(id => {
    if (!qual.has(id)) fails.push(`${id} is in the bracket but does not qualify`);
  });

  // No quarter-final out of one group, and none that merely replays a group match.
  const grpOf = Object.fromEntries(session.teams.map(t => [t.id, t.group]));
  const met = new Set(session.groupMatches.filter(m => m.winner)
    .map(m => [m.team1Id, m.team2Id].sort().join('|')));
  qf.forEach(m => {
    if (!grpOf[m.a.id] || !grpOf[m.b.id]) return;   // the undecided qualifier slot
    if (grpOf[m.a.id] === grpOf[m.b.id])
      fails.push(`QF${m.slot} is two teams out of group ${grpOf[m.a.id]}`);
    if (met.has([m.a.id, m.b.id].sort().join('|')))
      fails.push(`QF${m.slot} replays a group match (${m.s1} v ${m.s2})`);
  });

  return { fails, notes, sizes, fx, qf, playoff, session, groups, byGroupByes, byed, dropped };
}

// -------------------------------------------- does the DRAW decide the night

// Equal skill throughout, so a group that outperforms is the format talking.
// Measured on what a team actually takes home: whether it reached the
// knockout, and its series points for the night (which the byes inflate).
function sweep(nTeams, groupCount, nights, mode = 'best2') {
  const groups = E.GROUPS.slice(0, groupCount);
  const stat = {};
  groups.forEach(g => (stat[g] = { n: 0, qual: 0, pts: 0, wins: 0 }));
  for (let k = 0; k < nights; k++) {
    const { session } = buildNight(nTeams, groupCount, 1000 + k * 7919, null, mode);
    const qual = E.qualifyingTeamIds(session);
    groups.forEach(g => {
      session.teams.filter(t => t.group === g).forEach(t => {
        const r = E.teamGroupResults(session, t.id);
        const pts = r.counted.reduce((a, x) => a + (x.pts || 0), 0);
        const s = stat[g];
        s.n++; s.pts += pts; s.wins += r.byes;
        if (qual.has(t.id)) s.qual++;
      });
    });
  }
  return { groups, stat };
}

// WHOSE THIRD TAKES THE LAST SPOT on an uneven 3-group night. The thirds are
// compared on NORMALISED standings — every team ranked on the smallest group's
// match count — and the comment in the app says that is what makes them
// comparable. It does the opposite for the BIGGER group: a team that played
// four and keeps its best three has DROPPED ITS WORST RESULT, while a team
// that played three keeps a bad one it cannot shed. So this measures which
// group's third actually gets through, rather than assuming either way.
function thirdsProbe(nTeams, groupCount, nights, mode = 'best2') {
  const groups = E.GROUPS.slice(0, groupCount);
  const got = {}, sizes = {};
  groups.forEach(g => (got[g] = 0));
  for (let k = 0; k < nights; k++) {
    const { session } = buildNight(nTeams, groupCount, 1000 + k * 7919, null, mode);
    groups.forEach(g => (sizes[g] = session.teams.filter(t => t.group === g).length));
    const qual = E.qualifyingTeamIds(session);
    groups.forEach(g => {
      const rows = E.calcGroupStandingsNormalized(session, g);
      const third = rows[2]?.team?.id;
      if (third && qual.has(third)) got[g]++;
    });
  }
  return { groups, got, sizes };
}

// ------------------------------------------------------------------ report

const N = Number(process.argv[2] || 13);
const only = process.argv[3] ? [Number(process.argv[3])] : [4, 3];
const NIGHTS = Number(process.env.NIGHTS || 0);
// best2 or playoff — the two ways 3 groups can send eight teams through, and
// they are DIFFERENT brackets, so simulating one says nothing about the other.
const MODE = process.env.MODE || 'best2';
let bad = 0;

console.log(`=== ${N} teams · ${path.basename(APP)} · thirds=${MODE}`
  + ` · GROUP_COUNTED_GAMES=${E.GROUP_COUNTED_GAMES} ===\n`);

for (const gc of only) {
  const r = check(N, gc, 56, MODE);
  const label = `${gc} groups`;
  console.log(`--- ${label} ---`);
  console.log(`  sizes        ${r.groups.map((g, i) => `${g}:${r.sizes[i]}`).join('  ')}`);
  console.log(`  group matches ${r.fx.reduce((a, b) => a + b, 0)}  (${r.fx.join(' + ')})`);
  if (r.byed.length)
    console.log(`  BYES         ${r.byed.map(g => `${g}:+${r.byGroupByes[g]}`).join('  ')}`
      + `  — ${r.session.teams.filter(t => r.byed.includes(t.group)).length} of ${N} teams`
      + ` get a free 6-0 win worth 3 series points`);
  else
    console.log(`  BYES         none — every group plays at least ${E.GROUP_COUNTED_GAMES} matches`);
  if (r.dropped.length)
    console.log(`  DROPPED      ${r.dropped.join(',')} — each team's worst result does not count`);
  if (r.qf) {
    console.log(`  quarter-finals`);
    r.qf.forEach(m => console.log(`    QF${m.slot}  ${m.s1}  v  ${m.s2}`));
    if (r.playoff) console.log(`    + a THIRDS QUALIFIER first: ${r.playoff.a.seed} v ${r.playoff.b.seed}  (winner takes the Q slot)`);
    console.log(`    SF1 = QF1/QF2 winners · SF2 = QF3/QF4 winners`);
  }
  if (r.fails.length) { bad++; r.fails.forEach(f => console.log(`  !! ${f}`)); }
  else console.log(`  ok — 8 distinct qualifiers, no same-group tie, no group replay`);

  if (NIGHTS) {
    const { groups, stat } = sweep(N, gc, NIGHTS, MODE);
    const qr = groups.map(g => stat[g].qual / stat[g].n);
    const pr = groups.map(g => stat[g].pts / stat[g].n);
    console.log(`  --- ${NIGHTS} equal-skill nights ---`);
    groups.forEach((g, i) => console.log(
      `    ${g}  reaches the knockout ${(qr[i] * 100).toFixed(1)}%   series points ${pr[i].toFixed(2)}`
      + `   free wins ${(stat[g].wins / stat[g].n).toFixed(2)}`));
    const spread = Math.max(...pr) / Math.min(...pr);
    console.log(`    points spread by group  ${spread.toFixed(3)}x`
      + (spread > 1.05 ? '   <<< THE GROUP YOU ARE DRAWN INTO DECIDES THIS' : '   (even)'));
    if (gc === 3) {
      const t = thirdsProbe(N, gc, NIGHTS, MODE);
      console.log(`    the last spot goes to a THIRD, and whose:`);
      t.groups.forEach(g => console.log(
        `      ${g} (size ${t.sizes[g]})  its 3rd qualifies ${(t.got[g] / NIGHTS * 100).toFixed(1)}% of nights`));
    }
  }
  console.log('');
}

// WHAT THE TEAMS TABLE SHOWS vs WHO IS ACTUALLY ALIVE. qualifyingTeamIds has
// no thirdPlaceMode branch: for 3 groups it always marks top-2 plus the TWO
// best thirds. In `playoff` mode all THREE thirds are alive — the best takes a
// direct slot and the other two play a qualifier for the last one — so the
// screen marks one team as not through while it still has a match to win.
if (process.env.ALIVE) {
  const gc = Number(process.argv[3] || 3);
  const { session, groups } = buildNight(N, gc, 56, null, MODE);
  const qual = E.qualifyingTeamIds(session);
  const thirds = groups.map(g => {
    const rows = E.calcGroupStandingsNormalized(session, g);
    return { g, id: rows[2]?.team?.id, marked: qual.has(rows[2]?.team?.id) };
  });
  console.log(`--- what the table marks (thirds=${MODE}) ---`);
  console.log(`  marked as qualifying: ${qual.size} of ${N} teams`);
  thirds.forEach(t => console.log(`  ${t.g}3  marked through: ${t.marked ? 'yes' : 'NO'}`));
  if (MODE === 'playoff') {
    const unmarked = thirds.filter(t => !t.marked);
    console.log(unmarked.length
      ? `  !! ${unmarked.map(t => t.g + '3').join(', ')} shown as NOT through, but in playoff`
        + ` mode ${unmarked.length === 1 ? 'it has' : 'they have'} a qualifier still to play`
      : `  ok — every live team is marked`);
  }
}

process.exit(bad ? 1 : 0);
