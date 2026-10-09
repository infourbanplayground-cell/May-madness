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

const S = require(join(root, 'uprising-social.json'));

const target = 11, budget = 150, shuffle = true;
const players = S.cap || 16;
// The court count is the club's, not the format's — see _courts in the JSON.
// The override is for ONE night and expires on its own: it counts only while
// its date is still the date being advertised. Roll the date forward and the
// norm comes back without anyone having to remember to undo this.
const ov = S.courtsOverride || {};
const wanted = (ov.date && ov.date === S.date && ov.courts) || S.courts || E.UP.COURTS;
const courts = Math.max(2, Math.min(wanted, Math.floor(players / 4), E.UP.COURTS));
const overridden = courts !== (S.courts || E.UP.COURTS);
const scoring = E.upPlanRounds(budget, target, { shuffle, players, courts });
const rounds = scoring + (shuffle ? 1 : 0);
const resting = players - courts * 4;
// ROUNDS and MATCHES EACH are the same number only when nobody rests. With 16
// on 3 courts the night is 13 rounds and 9 matches each, and a post that
// advertises the round count as "matches each" overstates it by two thirds.
const matchesEach = (scoring * 4 * courts) / players;

console.log(JSON.stringify({
  players, courts, overridden, target, shuffle, scoring, rounds,
  matches: matchesEach,
  even: Number.isInteger(matchesEach),
  onCourt: courts * 4,
  resting,
  minutes: E.upNightMinutes(rounds, target),
  doubleFinal: resting === 0,
  win: Object.fromEntries(Array.from({ length: courts }, (_, i) => [i + 1, E.UP.WIN[i + 1]])),
  lose: Object.fromEntries(Array.from({ length: courts }, (_, i) => [i + 1, E.UP.LOSE[i + 1]])),
}, null, 2));
