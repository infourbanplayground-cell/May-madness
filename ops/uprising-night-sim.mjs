// Play one UPRISING night with the SHIPPED ENGINE and print it as JSON.
//
// The film that animates this does not get to invent the movement. Every court
// a chip moves to is the court `upBuildRound` actually put that player on, and
// every total is `upStandings` run over the night as it stood. A hand-drawn
// animation of "winners go up" would be a drawing of what we think the rule
// does; this is the rule doing it.
//
// Deterministic: the seed drives both the rest rota and the match results, so
// the same seed is always the same night and a re-render is always the same
// film. Skills are drawn from the seed too, so the night has favourites and the
// standings mean something — with coin-flip results the table is noise and the
// climb reads as random.
//
//   node ops/uprising-night-sim.mjs [seed] > night.json
import { createRequire } from 'module';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const require = createRequire(import.meta.url);
const root = join(dirname(fileURLToPath(import.meta.url)), '..');
const E = require(join(root, 'uprising-engine.js'));
const S = require(join(root, 'uprising-social.json'));

const SEED = Number(process.argv[2] || 20261031);
// mulberry32 — small, fast, and the same everywhere, which is the whole point.
let _s = SEED >>> 0;
const rnd = () => {
  _s |= 0; _s = (_s + 0x6D2B79F5) | 0;
  let t = Math.imul(_s ^ (_s >>> 15), 1 | _s);
  t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
  return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
};

const COURTS = S.courts || E.UP.COURTS;
const PLAYERS = S.cap || 16;
const TARGET = 11;
const LETTERS = 'ABCDEFGHIJKLMNOPQRSTUVWX'.split('');

const ids = Array.from({ length: PLAYERS }, (_, i) => 'p' + String(i).padStart(2, '0'));
// NOBODY IS LABELLED "YOU". The obvious move is to pick one chip to follow and
// give it a flattering night, and then the seed has to be chosen until that
// player climbs — which is a drawing of the format rather than a run of it.
// The film follows the CURRENT LEADER instead: that is a fact about the night,
// it is derived from the engine's own table, and it moves on its own.
const skill = {};
ids.forEach(id => { skill[id] = rnd(); });

const night = {
  id: 'sim', playerIds: ids, courtCount: COURTS,
  numRounds: E.UP.ROUNDS, shuffle: 1, pointsPerMatch: TARGET,
  restRota: E.upMakeRestRota(ids, SEED),
  ladder0: E.upSeedLadder(ids, {}, Math.min(COURTS, Math.floor(PLAYERS / 4))),
  rounds: [],
};

while (night.rounds.length < night.numRounds) {
  const r = E.upBuildRound(night);
  for (const m of r.courts) {
    // The stronger pair usually wins, and the margin follows the gap. A pure
    // coin flip makes the table noise, and a deterministic "best pair always
    // wins" makes the ladder a sort — neither is a padel night.
    const s1 = m.team1.reduce((a, p) => a + skill[p], 0) / 2;
    const s2 = m.team2.reduce((a, p) => a + skill[p], 0) / 2;
    // Skill tilts the match, it does not decide it. At *1.8 and a slope of 3
    // the best player won every round from three onward and the ladder stopped
    // churning — which is a film about seeding, not about a padel night.
    const edge = (s1 - s2) * 1.2;
    const p1 = 1 / (1 + Math.exp(-edge * 1.6));
    const aWins = rnd() < p1;
    const closeness = Math.abs(edge);
    const loser = Math.max(0, Math.min(TARGET - 1,
      Math.round(TARGET * (0.78 - closeness * 0.55) + (rnd() - 0.5) * 3)));
    m.score1 = aWins ? TARGET : loser;
    m.score2 = aWins ? loser : TARGET;
  }
  night.rounds.push(r);
}

const bad = E.upValidate(night);
if (bad.length) {
  console.error('the engine rejected the night it built: ' + bad.join('; '));
  process.exit(1);
}

// Per round: who was where, what the score was, and the table as it stood
// AFTER that round — sliced and re-run, never accumulated. The engine's
// standings are not a running sum (the doubled final is applied to the round,
// not added on), so a sum would quietly disagree with the app.
const out = { seed: SEED, players: [], courts: COURTS, target: TARGET,
              rounds: night.numRounds, shuffleRounds: E.upShuffleRounds(night),
              doubleFinal: E.upDoubleFinal(night), frames: [] };

out.players = ids.map((id, i) => ({ id, label: LETTERS[i] }));

for (let n = 1; n <= night.numRounds; n++) {
  const r = night.rounds[n - 1];
  const upto = { ...night, rounds: night.rounds.slice(0, n) };
  const table = E.upStandings(upto);
  const pts = {};
  // The row key is `total`, not `pts` — upStandings also carries matchPts,
  // which is the raw match score and not what the table ranks on.
  for (const row of table) pts[row.id] = row.total;
  out.frames.push({
    n,
    shuffle: n <= out.shuffleRounds,
    doubled: E.upRoundDoubled(night, r, n),
    resting: r.sitOuts || [],
    courts: r.courts.map(m => ({
      court: m.court, team1: m.team1, team2: m.team2, s1: m.score1, s2: m.score2,
    })),
    pts,
    top: table.slice(0, 5).map(row => ({ id: row.id, pts: row.total })),
  });
}

process.stdout.write(JSON.stringify(out));
