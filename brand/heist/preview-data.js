// PREVIEW DATA — the handoff's fixtures, shaped the way the screens read them.
// The screens never read this file in the real app: there an adapter builds
// the same shape out of the live state and the points engine. Here it is
// built from brand/heist/handoff/fixtures plus the few figures only the
// static design carries (the ME breakdown, the episode rows, "now"), so every
// screen can be laid beside its reference PNG like for like.
//
// Photos: the fixtures name /players/pNN.png, which do not exist, and the
// reference screenshots draw the stand-in paintings, so this does too.
window.MH_PREVIEW = (function () {
  const S = window.MH_SEASON;
  const A = "art/";
  // painting, crop, and (for the two-person painting) which half of it
  const LOOK = {
    p01: { photo: A + "art-corniche.jpg", pos: "34% 18%", heroPos: "34% 20%" },
    p02: { photo: A + "art-smash.jpg", pos: "center 14%" },
    p03: { photo: A + "art-carpark.jpg", pos: "center 18%" },
    p04: { photo: A + "art-rivals.jpg", pos: "82% 18%", splitPos: "92% 22%", avPos: "center 20%", zoom: ["left", -10, -15] },
    p05: { photo: A + "art-rivals.jpg", pos: "18% 20%", splitPos: "8% 25%", meCardPos: "82% 18%", avPos: "center 20%", zoom: ["right", -10, -12] },
    p06: { photo: A + "art-club.jpg", pos: "center 60%" },
    p07: { photo: A + "art-club.jpg", pos: "center 60%" },
  };
  const STATS = {
    p01: { smash: 94, wall: 86, speed: 88, clutch: 97 }, p02: { smash: 88, wall: 84, speed: 79, clutch: 90 },
  };
  const players = [
    ["p01", "Munther Rahbi", 104, "—", 5], ["p02", "Hamed Amri", 93, "—", 5], ["p03", "Nooh Amri", 90, "▲1", 5],
    ["p04", "Baraa", 82, "▼1", 5], ["p05", "mossa", 80, "▲2", 5], ["p06", "Salim K.", 76, "—", 5],
    ["p07", "Yousuf B.", 71, "▼2", 4], ["p08", "Ahmed S.", 68, "▲1", 5], ["p09", "Khalid", 64, "—", 4],
  ].map(([id, name, points, movement, nights], i) => Object.assign(
    { id, name, points, movement, nights, rank: i + 1, stats: STATS[id] || null }, LOOK[id] || {}));
  const ep = n => S.episodes[n - 1];
  const mhShort = n => n.split(" ")[0];
  const sessions = [
    { no: 1, date: "2026-12-02", state: "done", champions: ["Munther Rahbi", "Khalid"] },
    { no: 2, date: "2026-12-07", state: "done", champions: ["Hamed Amri", "Nooh Amri"] },
    { no: 3, date: "2026-12-09", state: "done", champions: ["Salim K.", "Yousuf B."] },
    { no: 4, date: "2026-12-14", state: "done", champions: ["Munther Rahbi", "Baraa"] },
    { no: 5, date: "2026-12-16", state: "done", champions: ["Baraa", "mossa"], artPos: "center 16%" },
    { no: 6, date: "2026-12-21", state: "live", progress: { played: 14, total: 24 }, artPos: "center 30%" },
    { no: 7, date: "2026-12-23", state: "soon", signups: { teams: 12, max: 16, open: true }, artPos: "34% 18%" },
    { no: 8, date: "2026-12-28", state: "soon", signups: { opensOn: "Thursday" }, artPos: "center 20%" },
    { no: 9, date: "2026-12-30", state: "soon", artPos: "center 50%" },
  ].map(s => Object.assign({ code: ep(s.no).code, title: ep(s.no).title, art: A + ep(s.no).art, time: S.time,
    doublePoints: S.doubleNights.indexOf(s.date) >= 0, finale: s.no === S.sessions }, s));
  return {
    now: "2026-12-21T21:30:00",   // local time, like a phone in Muscat: "1D 20H TO GO" to Wed 23 Dec 17:30
    meId: "p05",
    homeNext: 7,                          // Home's NEXT JOB card (the reference shows EP.07 on a live night)
    players, sessions,
    rival: { playerId: "p05", rivalId: "p04", h2h: { w: 1, l: 1 },
      meetings: [{ session: 5, label: "Final (same team)", result: "Champions" },
                 { session: 3, label: "Group B", result: "Won 6-4" },
                 { session: 2, label: "Quarter-final", result: "Lost 3-6" }] },
    vsCard: { playerId: "p01", meetings: 3, w: 1, l: 2, last: { session: 4, won: false, score: "5–6" } },
    me: {
      seg: { groupWins: 36, lossPts: 8, knockout: 20, titles: 16 },
      episodes: [{ session: 5, label: "Champions · rep up", pts: 26, title: true },
                 { session: 4, label: "Made the knockout", pts: 11, knockout: true },
                 { session: 3, label: "Group stage", pts: 7 }],
    },
    // phase 3 — fixtures/session-night.json. Group A, the live match and the
    // EP.05 recap are the fixture's; groups B-D, the teams list, the knockout
    // and the MVP tally are filled in so those tabs have something to draw.
    nights: { 6: {
      groups: {
        A: { standings: [{ team: "Munther & Baraa", w: 2, pts: 6 }, { team: "Salim & Yousuf", w: 1, pts: 5 },
                         { team: "Hamed & Nooh", w: 1, pts: 4 }, { team: "Ahmed & Khalid", w: 0, pts: 2 }],
             matches: [{ a: "Munther & Baraa", b: "Hamed & Nooh", score: "6-3", state: "final" },
                       { a: "Salim & Yousuf", b: "Ahmed & Khalid", score: "4-3", state: "live", court: 2 }] },
        B: { standings: [{ team: "mossa & Ali", w: 1, pts: 3 }, { team: "Omar & Said", w: 0, pts: 1 }],
             matches: [{ a: "mossa & Ali", b: "Omar & Said", score: "6-2", state: "final" }] },
        C: { standings: [{ team: "Faisal & Hilal", w: 0, pts: 0 }, { team: "Majid & Talal", w: 0, pts: 0 }],
             matches: [{ a: "Faisal & Hilal", b: "Majid & Talal", state: "next" }] },
        D: { standings: [{ team: "Rashid & Zaher", w: 0, pts: 0 }, { team: "Nasser & Saif", w: 0, pts: 0 }],
             matches: [{ a: "Rashid & Zaher", b: "Nasser & Saif", state: "next" }] },
      },
      teams: [["A", "Munther Rahbi", "Baraa"], ["A", "Salim K.", "Yousuf B."], ["A", "Hamed Amri", "Nooh Amri"],
              ["A", "Ahmed S.", "Khalid"], ["B", "mossa", "Ali"], ["B", "Omar", "Said"]]
        .map(([group, a, b]) => {
          const pa = players.find(p => p.name === a) || {}, pb = players.find(p => p.name === b) || {};
          return { group, a: mhShort(a), b: mhShort(b), aPhoto: pa.photo, bPhoto: pb.photo };
        }),
      knockout: null,                         // drawn once the groups finish
      mvp: { open: false, votes: [] },
    } },
    live: { court: 1, group: "A", clock: "18:42", teamA: "Munther & Baraa", teamB: "Hamed & Nooh",
            a: 5, b: 3, serving: "A", firstTo: 6, art: A + "art-smash.jpg", artPos: "center 25%" },
    recaps: { 5: {
      art: A + "art-club.jpg", artPos: "center 50%",
      champions: ["Baraa", "mossa"], beat: ["Munther Rahbi", "Khalid"], score: "6-4", pointsEach: 8,
      mvp: { name: "Baraa", votes: 6, note: "won the final with mossa" },
      biggestWin: { team: "Hamed & Nooh", score: "6-0" },
      upset: { team: "Ali & Omar", note: "beat the #1" },
      repUps: [{ name: "mossa", from: "Rookie", to: "Rising" }],
      yourNight: { points: 26, note: "Champions" },
    } },
    // phase 4 — fixtures/rivals-and-moments.json, as the fixture has them.
    // Rep Up's 80 is mossa's total after EP.05, the night it happened.
    moments: [
      { type: "repUp", playerId: "p05", from: "rookie", to: "rising", session: 5, points: 80 },
      { type: "tierUp", playerId: "p01", from: "elite", to: "legend", session: 5 },
      { type: "scoreSettled", playerId: "p05", overtookId: "p04", session: 6, newRank: 4, points: [86, 84] },
    ],
    finale: { leadAtStart: 11 },       // the leader's lead when the finale started ("11 / 11")
    paidOMR: 140,
    rosterSize: 32,                      // "THE CREW · 32 players" — the fixtures carry nine of them
  };
})();
