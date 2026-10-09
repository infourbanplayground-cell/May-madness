// Print the FORMAT facts as JSON, read out of the shipped engine.
//
// The announcement builder reads this rather than carrying its own copy of the
// court count, the round count or the points table. A post that advertises a
// number the app contradicts is the single most embarrassing thing this repo
// can produce, and it is the reason blackout-season.json exists.
import { createRequire } from 'module';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
const require = createRequire(import.meta.url);
const root = join(dirname(fileURLToPath(import.meta.url)), '..');
const E = require(join(root, 'uprising-engine.js'));

const players = 16, courts = 4, target = 11, budget = 150, shuffle = true;
const scoring = E.upPlanRounds(budget, target, { shuffle, players, courts });
const matches = scoring + (shuffle ? 1 : 0);

console.log(JSON.stringify({
  players, courts, target, shuffle, scoring, matches,
  onCourt: courts * 4,
  resting: players - courts * 4,
  minutes: E.upNightMinutes(matches, target),
  doubleFinal: players - courts * 4 === 0,
  win: Object.fromEntries(Array.from({ length: courts }, (_, i) => [i + 1, E.UP.WIN[i + 1]])),
  lose: Object.fromEntries(Array.from({ length: courts }, (_, i) => [i + 1, E.UP.LOSE[i + 1]])),
}, null, 2));
