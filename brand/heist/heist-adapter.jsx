// MUSCAT HEIST · Vol.10 — the adapter and the shell.
//
// heistData() turns the season STATE (the same shape every volume since July
// has saved) into the one data shape the Heist screens read — the shape
// brand/heist/preview-data.js builds out of the handoff's fixtures. EVERY
// FIGURE COMES FROM THE INHERITED ENGINE: calcPlayerStats for points,
// calcPlayerNights for what a night paid, rankAt for the table after any
// night, calcGroupStandings for a group, scoreToResult for a score. Nothing
// here scores anything (handoff rule 2).
//
// HeistShell is what App() renders instead of the Vol.9 tabs. It routes the
// Heist screens by hash, queues the moments, carries the NOT SAVING banner
// (the 17 Oct lesson), and hands the organiser to the inherited screens for
// what the handoff does not draw: creating a night, the draw, the bracket.

const MH_HOST_PHOTOS = "/api/roster";              // Heist portraits, by id
const MH_HOST_LOOT = "/api/loot";                  // the owner's champion art, by "<night>/<id>"
const mhFirstOf = n => (n || "").split(/\s+/)[0];

// ── the card stats (data.md, approved 22 Nov) ───────────────────────────
// SMASH  group-stage win rate
// WALL   share of losses that were close or a tiebreak
// SPEED  knockout win rate
// CLUTCH tiebreak matches won, of tiebreak matches played
// 0-99; under cardStats.minMatches behind a stat it is a dash, not a number.
function mhCardStats(pid, sessions) {
  const g = { w: 0, n: 0 }, ko = { w: 0, n: 0 }, loss = { close: 0, n: 0 }, tb = { w: 0, n: 0 };
  sessions.forEach(s => {
    const team = getPlayerTeam(s, pid); if (!team) return;
    const mine = m => m && m.winner && (m.team1Id === team.id || m.team2Id === team.id);
    const tally = (m, bucket) => {
      const won = teamWon(m, team.id);
      bucket.n++; if (won) bucket.w++;
      if (!won) { loss.n++; if (m.lossType === "competitive" || m.lossType === "tiebreak") loss.close++; }
      if (m.lossType === "tiebreak") { tb.n++; if (won) tb.w++; }
    };
    (s.groupMatches || []).filter(mine).forEach(m => tally(m, g));
    const B = s.bracket || {};
    [...(B.qf || []), ...(B.sf || []), B.final].filter(mine).forEach(m => tally(m, ko));
  });
  const min = (MH.cardStats && MH.cardStats.minMatches) || 3;
  const sc = (a, n) => n >= min ? Math.min(99, Math.round(a / n * 99)) : null;
  return { smash: sc(g.w, g.n), wall: sc(loss.close, loss.n), speed: sc(ko.w, ko.n), clutch: sc(tb.w, tb.n) };
}

function mhTeamNames(s, tid, byId) {
  const t = (s.teams || []).find(x => x.id === tid);
  if (!t) return "TBD";
  return [t.p1Id, t.p2Id].map(i => mhFirstOf((byId[i] || {}).name || "?")).join(" & ");
}
const mhScore = m => m && m.score && m.score.t1 != null ? `${m.score.t1}-${m.score.t2}` : null;

// Every match two players were both in this season, newest first.
function mhMeetings(a, b, sessions) {
  const out = [];
  sessions.forEach((s, idx) => {
    const ta = getPlayerTeam(s, a), tb = getPlayerTeam(s, b);
    if (!ta || !tb) return;
    const B = s.bracket || {};
    const all = [...(s.groupMatches || []).map(m => [m, "Group " + ((s.teams.find(t => t.id === m.team1Id) || {}).group || "")]),
      ...(B.qf || []).map(m => [m, "Quarter-final"]), ...(B.sf || []).map(m => [m, "Semi-final"]), [B.final, "Final"]];
    all.forEach(([m, label]) => {
      if (!m || !m.winner) return;
      const inA = m.team1Id === ta.id || m.team2Id === ta.id, inB = m.team1Id === tb.id || m.team2Id === tb.id;
      if (!inA || !inB) return;
      const sc = mhScore(m); const won = teamWon(m, ta.id);
      const mine = sc ? (m.team1Id === ta.id ? sc : sc.split("-").reverse().join("-")) : "";
      if (ta.id === tb.id) out.push({ session: idx + 1, same: true, label: label + " (same team)", won,
        result: label === "Final" && won ? "Champions" : (won ? "Won " : "Lost ") + mine, at: m.resultAt || 0 });
      else out.push({ session: idx + 1, same: false, label, won, result: (won ? "Won " : "Lost ") + mine, score: mine, at: m.resultAt || 0 });
    });
  });
  return out.sort((x, y) => y.session - x.session || y.at - x.at);
}

// ── the adapter ─────────────────────────────────────────────────────────
function heistData(state, o) {
  const S = MH, sessions = state.sessions || [], players = state.players || [];
  const byId = Object.fromEntries(players.map(p => [p.id, p]));
  const nights = S.nights || [];
  const sessFor = date => sessions.find(s => s.date === date);
  const today = (() => { const d = new Date(); return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`; })();
  const done = sessions.map((s, i) => [s, i]).filter(([s]) => s.completed);
  const lastDoneIdx = done.length ? done[done.length - 1][1] : -1;

  // the table after each completed night — rankAt is the engine's own
  const after = sessions.map((s, i) => s.completed ? rankAt(state, i) : null);
  const ptsAfter = (pid, i) => { for (let k = i; k >= 0; k--) if (after[k]) { const r = after[k].rows.find(x => x.id === pid); return r ? r.pts : 0; } return 0; };
  const now = (o.leaderboard || []).map(r => ({ id: r.player.id, pts: r.totalPts, played: (r.stats || {}).sessionsPlayed || 0 }));
  const season = now.filter(r => r.played > 0 || r.pts > 0);
  // before night one nobody has a point: the crew is the carried roster, ranked all-time
  const preseason = season.length === 0;
  const ordered = preseason
    ? (o.leaderboard || []).slice().sort((a, b) => (b.lifetimePts || 0) - (a.lifetimePts || 0)).filter(r => (r.lifetimePts || 0) > 0).slice(0, 60)
        .map(r => ({ id: r.player.id, pts: 0, played: 0 }))
    : season.sort((a, b) => b.pts - a.pts || (byId[a.id].name || "").localeCompare(byId[b.id].name || ""));
  const before = lastDoneIdx > 0 ? rankAt(state, (done[done.length - 2] || [null, -1])[1]) : null;

  const P = ordered.map((r, i) => {
    const p = byId[r.id] || {};
    const totals = sessions.map((s, k) => after[k] ? ptsAfter(r.id, k) : null).filter(x => x != null);
    const rep = mhRepFor(totals.length ? totals : [0]);
    const was = before && before.rank[r.id];
    const mv = !before || !was ? "—" : was > i + 1 ? "▲" + (was - i - 1) : was < i + 1 ? "▼" + (i + 1 - was) : "—";
    const heist = (o.portraits || {})[r.id];
    return { id: r.id, name: p.name || "?", points: r.pts, rank: i + 1, movement: mv, nights: r.played,
      repId: rep && rep.id, stats: mhCardStats(r.id, sessions),
      photo: heist || p.photo || p.photoUrl || null, // A Heist portrait is made with the face in the top third, so the card shows its
      // TOP edge: at 20% the face rose into the corners and the tier tag and rank
      // sat on foreheads (owner, 24 Nov: "the badge covers the photos").
      pos: heist ? "center 0%" : "center 25%" };
  });

  const ep = n => (S.episodes || [])[n - 1] || { code: "EP." + String(n).padStart(2, "0"), title: "", art: "" };
  const S2 = nights.map((date, k) => {
    const no = k + 1, s = sessFor(date);
    const fx = s ? [...(s.groupMatches || []), ...((s.bracket || {}).qf || []), ...((s.bracket || {}).sf || []), (s.bracket || {}).final].filter(Boolean) : [];
    const played = fx.filter(m => m.winner).length;
    const started = played > 0 || (s && date === today);
    const st = s && s.completed ? "done" : s && started ? "live" : "soon";
    const f = s && (s.bracket || {}).final;
    const champTeam = f && f.winner && (s.teams || []).find(t => t.id === (f.winner === "team1" ? f.team1Id : f.team2Id));
    return { no, date, state: st, code: ep(no).code, title: ep(no).title, art: (o.artBase || "") + ep(no).art, artPos: ep(no).artPos,
      time: S.time, doublePoints: (S.doubleNights || []).indexOf(date) >= 0, finale: no === nights.length,
      sid: s && s.id,
      champions: champTeam ? [champTeam.p1Id, champTeam.p2Id].map(i => (byId[i] || {}).name) : undefined,
      progress: st === "live" ? { played, total: Math.max(fx.length, played) } : undefined,
      signups: s && st === "soon" ? { teams: (s.teams || []).length, max: typeof MAX_TEAMS !== "undefined" ? MAX_TEAMS : 16, open: true } : undefined };
  });
  const live = S2.find(s => s.state === "live");
  const next = S2.find(s => s.state === "soon");

  // ── one night, for the session screen ──
  // One night, for the session screen and its share cards. Every figure is the
  // inherited engine's: calcGroupStandings (wins, GD, head to head, games won),
  // qualifyingTeamIds (the same set the bracket seeds from), calcPlayerNights.
  // Photos: a Heist portrait wins, then the volume photo (stored as photoUrl —
  // reading .photo alone is why every pair drew as initials).
  const photoOf = id => (o.portraits || {})[id] || (byId[id] || {}).photo || (byId[id] || {}).photoUrl || null;
  const nightOf = sv => {
    const s = sessions.find(x => x.id === sv.sid); if (!s) return {};
    const pl = id => ({ id, name: (byId[id] || {}).name || "?", first: mhFirstOf((byId[id] || {}).name), photo: photoOf(id) });
    const teamOf = tid => {
      const t = (s.teams || []).find(x => x.id === tid);
      return t ? { id: tid, group: t.group, name: mhTeamNames(s, tid, byId), players: [pl(t.p1Id), pl(t.p2Id)] } : null;
    };
    const fx = [...(s.groupMatches || []), ...((s.bracket || {}).qf || []), ...((s.bracket || {}).sf || []), (s.bracket || {}).final].filter(Boolean);
    const started = fx.some(m => m.winner);
    let Q = new Set();
    try { if (started && typeof qualifyingTeamIds === "function") Q = qualifyingTeamIds(s); } catch (e) {}
    const side = (m, k) => m.score ? (k === "a" ? m.score.t1 : m.score.t2) : null;
    const groups = {}, posOf = {};
    [...new Set((s.teams || []).map(t => t.group).filter(Boolean))].sort().forEach(g => {
      const rows = calcGroupStandings(s, g);
      const ids = new Set((s.teams || []).filter(t => t.group === g).map(t => t.id));
      const ms = (s.groupMatches || []).filter(m => ids.has(m.team1Id));
      rows.forEach((r, i) => { posOf[r.team.id] = { pos: i + 1, w: r.wins, pts: r.pts, gd: r.gd, p: r.played - (r.byes || 0) }; });
      groups[g] = {
        done: ms.length > 0 && ms.every(m => m.winner),
        standings: rows.map((r, i) => ({ ...teamOf(r.team.id), team: mhTeamNames(s, r.team.id, byId), id: r.team.id,
          pos: i + 1, w: r.wins, pts: r.pts, gd: r.gd, gf: r.gf, p: r.played - (r.byes || 0), q: Q.has(r.team.id) })),
        matches: ms.map((m, i) => ({
          id: m.id, sid: s.id, n: i + 1, a: mhTeamNames(s, m.team1Id, byId), b: mhTeamNames(s, m.team2Id, byId),
          ta: teamOf(m.team1Id), tb: teamOf(m.team2Id), ga: side(m, "a"), gb: side(m, "b"),
          winner: m.winner === "team1" ? "a" : m.winner === "team2" ? "b" : null,
          score: mhScore(m), state: m.winner ? "final" : mhScore(m) ? "live" : "next", court: m.court })),
      };
    });
    const B = s.bracket || {};
    const ko = (m, round, n) => m && { round, n, a: m.team1Id ? mhTeamNames(s, m.team1Id, byId) : null, b: m.team2Id ? mhTeamNames(s, m.team2Id, byId) : null,
      ta: m.team1Id ? teamOf(m.team1Id) : null, tb: m.team2Id ? teamOf(m.team2Id) : null, ga: side(m, "a"), gb: side(m, "b"),
      sa: m.s1, sb: m.s2, score: mhScore(m), winner: m.winner === "team1" ? "a" : m.winner === "team2" ? "b" : null };
    const hasKo = (B.qf || []).length || (B.sf || []).length || B.final;
    const K = hasKo ? { qf: (B.qf || []).map((m, i) => ko(m, "qf", i + 1)), sf: (B.sf || []).map((m, i) => ko(m, "sf", i + 1)), final: ko(B.final, "final", 1) } : null;
    const champ = K && K.final && K.final.winner ? {
      team: K.final.winner === "a" ? K.final.ta : K.final.tb, beat: K.final.winner === "a" ? K.final.tb : K.final.ta,
      score: K.final.winner === "a" ? `${K.final.ga}-${K.final.gb}` : `${K.final.gb}-${K.final.ga}` } : null;
    const votes = {};
    Object.values(s.mvpVotes || {}).forEach(v => { const id = typeof v === "string" ? v : v && v.playerId; if (id) votes[id] = (votes[id] || 0) + 1; });
    // tonight's points: asked for only when a screen shows them (one engine
    // walk per player), and remembered after the first ask
    let tonightMemo = null;
    const tonight = () => {
      if (tonightMemo) return tonightMemo;
      const ids = [...new Set((s.teams || []).flatMap(t => [t.p1Id, t.p2Id]))];
      tonightMemo = ids.map(id => {
        const r = calcPlayerNights(id, sessions, () => "").nights.find(n => n.id === s.id);
        return r ? { ...pl(id), points: r.nightTotal, outcome: r.outcome } : null;
      }).filter(x => x && x.points > 0).sort((a, b) => b.points - a.points || a.name.localeCompare(b.name));
      return tonightMemo;
    };
    const teamsSorted = (s.teams || []).slice().sort((x, y) => (x.group || "").localeCompare(y.group || "") || ((posOf[x.id] || {}).pos || 9) - ((posOf[y.id] || {}).pos || 9));
    return {
      started, champion: champ, tonight,
      groups,
      teams: teamsSorted.map(t => ({ ...teamOf(t.id), ...(started ? posOf[t.id] || {} : {}), q: Q.has(t.id),
        a: mhFirstOf((byId[t.p1Id] || {}).name), b: mhFirstOf((byId[t.p2Id] || {}).name), aPhoto: photoOf(t.p1Id), bPhoto: photoOf(t.p2Id) })),
      knockout: K,
      mvp: { open: !s.completed && !!s.mvpVotingOpen, votes: Object.entries(votes).map(([id, n]) => ({ ...pl(id), votes: n })).sort((x, y) => y.votes - x.votes) },
    };
  };
  const nightsD = {}; S2.forEach(sv => { if (sv.sid) nightsD[sv.no] = nightOf(sv); });

  // ── the recap of a finished night ──
  const recaps = {};
  const repAt = (pid, i) => mhRepFor(sessions.slice(0, i + 1).map((s, k) => after[k] ? ptsAfter(pid, k) : null).filter(x => x != null));
  S2.filter(sv => sv.state === "done").forEach(sv => {
    const idx = sessions.findIndex(x => x.id === sv.sid), s = sessions[idx], f = (s.bracket || {}).final;
    if (!f || !f.winner) return;
    const win = f.winner === "team1" ? f.team1Id : f.team2Id, lose = f.winner === "team1" ? f.team2Id : f.team1Id;
    const tm = id => (s.teams || []).find(t => t.id === id) || {};
    const names = id => [tm(id).p1Id, tm(id).p2Id].map(i => (byId[i] || {}).name).filter(Boolean);
    const nightPts = pid => { const r = calcPlayerNights(pid, sessions, () => "").nights.find(n => n.id === s.id); return r ? r.nightTotal : null; };
    const champPts = names(win).length ? [tm(win).p1Id, tm(win).p2Id].map(nightPts) : [];
    const all = [...(s.groupMatches || []), ...((s.bracket || {}).qf || []), ...((s.bracket || {}).sf || []), f].filter(m => m && m.winner && m.score);
    const big = all.slice().sort((x, y) => Math.abs(y.score.t1 - y.score.t2) - Math.abs(x.score.t1 - x.score.t2))[0];
    // the upset: the biggest gap in season rank (before the night) a winning pair overturned
    const prevRank = idx > 0 ? rankAt(state, idx - 1).rank : {};
    const pairRank = id => Math.min(...[tm(id).p1Id, tm(id).p2Id].map(i => prevRank[i] || 999));
    let upset = null;
    if (idx > 0) all.forEach(m => {
      const w = m.winner === "team1" ? m.team1Id : m.team2Id, l = m.winner === "team1" ? m.team2Id : m.team1Id;
      const gap = pairRank(w) - pairRank(l);
      if (gap > 0 && (!upset || gap > upset.gap)) upset = { gap, team: mhTeamNames(s, w, byId), note: `beat the #${pairRank(l)}` };
    });
    const votes = {}; Object.values(s.mvpVotes || {}).forEach(v => { const id = typeof v === "string" ? v : v && v.playerId; if (id) votes[id] = (votes[id] || 0) + 1; });
    const mvpId = Object.keys(votes).sort((a, b) => votes[b] - votes[a])[0];
    const repUps = idx > 0 ? (s.teams || []).flatMap(t => [t.p1Id, t.p2Id]).map(pid => {
      const a = repAt(pid, idx - 1), b = repAt(pid, idx);
      return a && b && MH_REPS.indexOf(b) < MH_REPS.indexOf(a) ? { name: mhFirstOf((byId[pid] || {}).name), from: a.label, to: b.label, id: pid } : null;
    }).filter(Boolean) : [];
    const myNight = o.meId ? calcPlayerNights(o.meId, sessions, () => "").nights.find(n => n.id === s.id) : null;
    recaps[sv.no] = {
      art: sv.art, champions: names(win), beat: names(lose), score: mhScore(f) && (f.winner === "team1" ? mhScore(f) : mhScore(f).split("-").reverse().join("-")),
      pointsEach: champPts.length === 2 && champPts[0] === champPts[1] ? champPts[0] : null,
      mvp: mvpId ? { name: mhFirstOf((byId[mvpId] || {}).name), votes: votes[mvpId] } : { name: "—", votes: 0 },
      biggestWin: big ? { team: mhTeamNames(s, big.winner === "team1" ? big.team1Id : big.team2Id, byId),
        score: big.winner === "team1" ? mhScore(big) : mhScore(big).split("-").reverse().join("-") } : { team: "—", score: "" },
      upset: upset || { team: "—", note: "no upsets" },
      repUps,
      yourNight: myNight ? { points: myNight.nightTotal, note: myNight.outcome } : null,
    };
  });

  // ── me: the points by kind, and the night-by-night ──
  let meD = null;
  if (o.meId && byId[o.meId]) {
    const r = calcPlayerNights(o.meId, sessions, () => "");
    const sg = r.seg;
    meD = { seg: { groupWins: sg.groupWins + sg.topOfGroup, lossPts: sg.lossPts, knockout: sg.knockout, titles: sg.titles,
                   bonus: sg.comeback + sg.streak + sg.double },
      ok: r.ok,
      episodes: r.nights.slice().reverse().map(n => {
        const k = nights.indexOf(n.date) + 1;
        return { session: k || n.no, label: n.outcome, pts: n.nightTotal, title: /champion/i.test(n.outcome), knockout: /knockout|final/i.test(n.outcome) };
      }) };
  }

  // ── rival, and you-v-them for any card ──
  const meIdx = P.findIndex(p => p.id === o.meId);
  let rival = null;
  if (meIdx >= 0 && !preseason) {
    const them = meIdx === 0 ? P[1] : P[meIdx - 1];
    if (them) {
      const m = mhMeetings(o.meId, them.id, sessions);
      const opp = m.filter(x => !x.same);
      rival = { playerId: o.meId, rivalId: them.id, h2h: { w: opp.filter(x => x.won).length, l: opp.filter(x => !x.won).length },
        meetings: m.slice(0, 3).map(x => ({ session: nights.indexOf((sessions[x.session - 1] || {}).date) + 1 || x.session, label: x.label, result: x.result })) };
    }
  }
  const vsFor = id => {
    if (!o.meId || id === o.meId) return null;
    const opp = mhMeetings(o.meId, id, sessions).filter(x => !x.same);
    if (!opp.length) return null;
    const last = opp[0];
    return { playerId: id, meetings: opp.length, w: opp.filter(x => x.won).length, l: opp.filter(x => !x.won).length,
      last: { session: nights.indexOf((sessions[last.session - 1] || {}).date) + 1 || last.session, won: last.won, score: (last.score || "").replace("-", "–") } };
  };

  // ── the moments, for the player on this phone, after the last finished night ──
  const moments = [];
  if (o.meId && lastDoneIdx >= 0 && !preseason) {
    const no = nights.indexOf(sessions[lastDoneIdx].date) + 1;
    const prevI = done.length > 1 ? done[done.length - 2][1] : -1;
    const a = prevI >= 0 ? repAt(o.meId, prevI) : MH_REPS[MH_REPS.length - 1], b = repAt(o.meId, lastDoneIdx);
    if (a && b && MH_REPS.indexOf(b) < MH_REPS.indexOf(a)) moments.push({ type: "repUp", playerId: o.meId, from: a.id, to: b.id, session: no, points: ptsAfter(o.meId, lastDoneIdx) });
    const me = P.find(p => p.id === o.meId);
    if (me && getPlayerTeam(sessions[lastDoneIdx], o.meId)) {
      const wasRank = before ? before.rank[o.meId] : null;
      moments.push({ type: "tierUp", playerId: o.meId, from: wasRank ? mhTierFor(wasRank).id : mhTierFor(me.rank).id, to: mhTierFor(me.rank).id, session: no });
      if (before && wasRank && wasRank > me.rank) {
        const above = before.rows[wasRank - 2];
        if (above && P.find(p => p.id === above.id) && P.find(p => p.id === above.id).rank > me.rank)
          moments.push({ type: "scoreSettled", playerId: o.meId, overtookId: above.id, session: no,
            points: [me.points, P.find(p => p.id === above.id).points] });
      }
    }
  }

  // a knockout card dealt last night (heist-loot.jsx): shown once, after the others.
  // Pushed as a marker; the card itself is derived when the screen asks.
  if (o.meId && lastDoneIdx >= 0 && !preseason) {
    const no = nights.indexOf(sessions[lastDoneIdx].date) + 1;
    const B = sessions[lastDoneIdx].bracket || {};
    const inKo = [...(B.qf || []), ...(B.sf || []), B.final].filter(Boolean).some(m => {
      const t = getPlayerTeam(sessions[lastDoneIdx], o.meId); return t && (m.team1Id === t.id || m.team2Id === t.id); });
    if (no > 0 && inKo) moments.push({ type: "loot", playerId: o.meId, session: no });
  }

  const n8 = sessions.findIndex(s => s.date === nights[nights.length - 2]);
  let leadAtStart = null;
  if (n8 >= 0 && after[n8]) { const rows = after[n8].rows; leadAtStart = rows.length > 1 ? rows[0].pts - rows[1].pts : null; }

  // the whole roster, for "who are you?": table order first, then everyone else by name
  const inP = new Set(P.map(p => p.id));
  const roster = [...P.filter(p => !preseason), ...players.filter(p => preseason || !inP.has(p.id))
    .map(p => ({ id: p.id, name: p.name || "?", points: 0, nights: 0, photo: photoOf(p.id), pos: (o.portraits || {})[p.id] ? "center 0%" : "center 25%" }))
    .sort((a, b) => a.name.localeCompare(b.name))];

  return {
    meId: o.meId || null, players: P, sessions: S2, preseason, roster,
    homeNext: (next || S2[S2.length - 1]).no, homeShowsLive: !!live,
    nights: nightsD, recaps, me: meD, rival, vsFor, moments,
    live: null, finale: { leadAtStart },
    paidOMR: done.length * (S.voucher || 0) * 2,
    rosterSize: preseason ? players.length : P.length,
    artBase: o.artBase || "", logo: o.logo, lootArt: o.lootArt || {},
    // every scene the owner has sent: the nine episodes, then the spares. Pages
    // draw from this through mhScene() so no two pages open on the same picture.
    scenes: [...(S.episodes || []).map(e => ({ src: (o.artBase || "") + e.art, pos: e.artPos, code: e.code, title: e.title })),
             ...(S.extraArt || []).map(e => ({ src: (o.artBase || "") + e.art, pos: e.artPos }))].filter(x => x.src && !/\/$/.test(x.src)),
    // the loading screen's own posters (owner, 24 Nov: "GTA style"), then the scenes
    loadingArt: (S.loadingArt || []).map(e => ({ src: (o.artBase || "") + e.art, pos: e.artPos })),
  };
}

// ── the shell ───────────────────────────────────────────────────────────
// Routes by hash (#home, #jobs, #card/<id>, #session/<no>, #live/<no>/<matchId>
// ...), the same table the preview uses, so the screens are exactly the ones
// the phase reports checked.
const MH_SCREENS = () => ({ home: MhHome, jobs: MhJobs, wanted: MhWanted, me: MhMe, crew: MhCrew, card: MhCardScreen, take: MhTake,
  session: MhSession, live: MhLive, recap: MhRecap, slides: MhSlides,
  loading: MhLoading, cardpull: MhCardPull, repup: MhRepUp, rival: MhRival, settled: MhSettled, finale: MhFinale,
  share: MhShareSheet, nightshare: MhNightShare, loot: MhLootScreen, who: MhWho, howto: MhHowTo });

function HeistShell(props) {
  const { state, leaderboard, meId, canScore, sync, syncErr, updateSession, openLogin, openMe, openOrganiser, openSession, signedIn,
    setMe, clearMe, lastSync, refreshNow, pullY } = props;
  const read = () => (location.hash.slice(1) || "").split("/");
  const [route, setRoute] = React.useState(read);
  const [portraits, setPortraits] = React.useState({});
  const [lootArt, setLootArt] = React.useState({});
  const [undo, setUndo] = React.useState(null);
  React.useEffect(() => { if (!undo) return; const t = setTimeout(() => setUndo(null), 10000); return () => clearTimeout(t); }, [undo]);
  const takeBack = () => {
    if (!undo || !undo.prev) { setUndo(null); return; }
    const u = undo; setUndo(null);
    updateSession(u.sid, ss => ({ ...ss, groupMatches: (ss.groupMatches || []).map(x => x.id === u.mid ? u.prev : x) }));
  };
  React.useEffect(() => { const f = () => setRoute(read()); addEventListener("hashchange", f); return () => removeEventListener("hashchange", f); }, []);
  // the Heist portraits made on /photos/ — a portrait wins over the volume photo
  React.useEffect(() => {
    let live = true;
    const pull = () => fetch(MH_HOST_PHOTOS).then(r => r.json()).then(j => {
      if (!live || !j.ok) return;
      setPortraits(Object.fromEntries(j.players.filter(p => p.heist).map(p => [p.id, p.heist])));
    }).catch(() => {});
    pull(); const t = setInterval(pull, 5 * 60000);
    return () => { live = false; clearInterval(t); };
  }, []);
  // the owner's champion artwork, uploaded on /photos/ — it replaces a SCORE card
  React.useEffect(() => {
    let live = true;
    const pull = () => fetch(MH_HOST_LOOT).then(r => r.json()).then(j => { if (live && j.ok) setLootArt(j.art || {}); }).catch(() => {});
    pull(); const t = setInterval(pull, 5 * 60000);
    return () => { live = false; clearInterval(t); };
  }, []);
  const D = React.useMemo(() => {
    const d = heistData(state, { leaderboard, meId, portraits, lootArt, artBase: "assets/art/", logo: "assets/up-logo-tight.png" });
    d.onLogo = openLogin; d.organiser = canScore ? openOrganiser : null; d.signedIn = signedIn;
    // the Heist picker when the shell was handed the setter; the inherited sheet otherwise
    d.setMe = setMe || null; d.clearMe = clearMe || null;
    d.pickMe = setMe ? () => { location.hash = "who"; } : openMe;
    // check-in: stored on the night, never read by the engine
    d.checkedIn = Object.fromEntries((d.sessions || []).filter(x => x.sid).map(x => [x.no, ((state.sessions || []).find(y => y.id === x.sid) || {}).checkIn || {}]));
    d.checkIn = canScore ? (sid, pid, on) => updateSession(sid, ss => {
      const c = { ...(ss.checkIn || {}) }; if (on) c[pid] = Date.now(); else delete c[pid]; return { ...ss, checkIn: c }; }) : null;
    return d;
  }, [state, leaderboard, meId, portraits, lootArt, canScore, signedIn, setMe, clearMe, updateSession]);

  // first open of the day: Now Loading Muscat, then any moment not yet seen
  const day = (() => { const t = new Date(); return `${t.getFullYear()}-${t.getMonth() + 1}-${t.getDate()}`; })();
  React.useEffect(() => {
    if (location.hash) return;
    if (mhOnce("loaded", day).due()) { mhOnce("loaded", day).seen(); location.replace("#loading"); return; }
    const m = mhNextMoment(D) || mhFirstRun(D);
    location.replace(m ? "#" + m : "#home");
  }, []);

  const go = (to, arg) => {
    if (to === "back") { if (history.length > 1) history.back(); else location.hash = "home"; return; }
    if (to === "home") { const m = mhNextMoment(D) || mhFirstRun(D); if (m) { location.hash = m; return; } }
    if (to === "signup" || to === "results") {
      const s = D.sessions.find(x => x.no === +arg);
      if (s && s.sid) { openSession(s.sid); return; }
      location.hash = "jobs"; return;
    }
    if (to === "cardpull") to = "cardpull";
    location.hash = arg != null ? `${to}/${arg}` : to; scrollTo(0, 0);
  };
  const [name, arg, arg2] = route;
  const Screens = MH_SCREENS();
  const Screen = Screens[name] || MhHome;
  // live scoring writes the result through the engine's own scoreToResult
  let live = null, onLock = null;
  if (name === "live") {
    const s = D.sessions.find(x => x.no === +arg);
    const N = s && D.nights[s.no];
    const m = N && Object.values(N.groups).flatMap(g => g.matches.map(x => ({ ...x, group: Object.keys(N.groups).find(k => N.groups[k] === g) }))).find(x => x.id === arg2);
    if (m && canScore) {
      const [a, b] = (m.score || "0-0").split("-").map(Number);
      live = { court: m.court || 1, group: m.group, teamA: m.a, teamB: m.b, a, b, serving: "A", art: s.art, artPos: s.artPos };
      onLock = ({ t1, t2 }) => {
        const r = scoreToResult(t1, t2);
        if (!r.winner || Math.max(t1, t2) < 6) { alert("Not a finished score: a set is first to 6 (7-5 or 7-6 if it goes on)."); return; }
        const sess = (state.sessions || []).find(x => x.id === m.sid);
        const prev = sess && (sess.groupMatches || []).find(x => x.id === m.id);
        updateSession(m.sid, ss => ({ ...ss, groupMatches: (ss.groupMatches || []).map(x => x.id === m.id ? { ...x, ...r, resultAt: Date.now() } : x) }));
        // ten seconds to take it back, and what to start next
        const later = sess && (sess.groupMatches || []).filter(x => !x.winner && x.id !== m.id);
        const nm = later && later[0];
        const nameOf = id => mhTeamNames(sess, id, Object.fromEntries((state.players || []).map(p => [p.id, p])));
        setUndo({ sid: m.sid, mid: m.id, prev: prev ? JSON.parse(JSON.stringify(prev)) : null, at: Date.now(),
          label: `${t1}–${t2} locked`, next: nm ? `${nameOf(nm.team1Id)} v ${nameOf(nm.team2Id)}${nm.court ? " · Court " + nm.court : ""}` : null });
        go("back");
      };
    } else if (name === "live") { location.replace("#session/" + arg); return null; }
  }
  // Unsaved changes, counted from the scorer's own edits: every state change
  // while signed in is a change to send, and a save that lands clears them.
  const [pending, setPending] = React.useState(0);
  const seen = React.useRef(state);
  React.useEffect(() => { if (canScore && seen.current && state !== seen.current) setPending(n => n + 1); seen.current = state; }, [state]);
  React.useEffect(() => { if (sync === "saved") setPending(0); }, [sync]);
  React.useEffect(() => { window.__mhDirty = canScore && pending > 0; }, [canScore, pending, sync]);
  // back in signal: nudge the save rather than wait out the backoff
  React.useEffect(() => {
    const f = () => { if (!window.__mhDirty) return; const sid = ((state.sessions || [])[0] || {}).id; if (sid) updateSession(sid, ss => ({ ...ss })); };
    addEventListener("online", f); return () => removeEventListener("online", f);
  }, [state]);
  const banner = canScore && (sync === "error" || sync === "offline");
  const noSignal = typeof navigator !== "undefined" && navigator.onLine === false;
  const auth = /401|403|token|auth|unauthor/i.test(syncErr || "");
  return (
    <>
      {banner && (noSignal || !auth ? (
        <div className="mh-savebanner" role="status" data-kind="offline">
          ⏳ {noSignal ? "No signal" : "Not saved yet"} — {pending > 0 ? `${pending} change${pending > 1 ? "s" : ""} waiting` : "changes waiting"} on this phone. They send by themselves; keep the app open.
        </div>
      ) : (
        <button type="button" className="mh-savebanner" onClick={() => openLogin()}>
          ⚠ NOT SAVING — your changes are only on this phone. {syncErr ? `(${syncErr}) ` : ""}Tap to sign in again.
        </button>
      ))}
      {typeof MhFresh === "function" && ["home", "wanted", "session", "me", "jobs"].includes(name || "home") &&
        <MhFresh pullY={pullY || 0} lastSync={lastSync} sync={sync} onRefresh={refreshNow} />}
      {undo && canScore && (
        <div className="mh-undotoast" role="status">
          <div style={{ minWidth: 0 }}>
            <b>{undo.label}</b>
            {undo.next && <div className="mh-undonext">Up next: {undo.next}</div>}
          </div>
          <button type="button" onClick={takeBack}>Undo</button>
        </div>
      )}
      <Screen key={route.join("/")} D={D} go={go} id={name === "share" ? arg2 : arg} no={arg} what={arg}
        start={+arg2 || 0} kind={arg2} canScore={canScore} match={live} onLock={onLock} />
    </>
  );
}
// A phone's first open: how it works once, then who are you once (a player
// who says "just looking" is not asked again).
function mhFirstRun(D) {
  if (typeof mhStore === "undefined") return null;
  if (mhStore.get("mh-howto-seen", "") !== "1") return "howto";
  if (!D.meId && D.setMe && mhStore.get("mh-who-asked", "") !== "1") return "who";
  return null;
}
// The next moment this phone has not seen, in the order the handoff plays them.
function mhNextMoment(D) {
  if (!D.meId) return null;
  for (const m of D.moments || []) {
    const key = { tierUp: ["card", `${m.playerId}/${m.session}`, `cardpull/${m.session}`],
                  repUp: ["rep", `${m.playerId}/${m.to}`, `repup/${m.playerId}`],
                  scoreSettled: ["settled", `${m.playerId}/${m.session}`, "settled"],
                  loot: ["loot", `${m.playerId}/${m.session}`, `loot/${m.playerId}.${m.session}`] }[m.type];
    if (key && mhOnce(key[0], key[1]).due()) { mhOnce(key[0], key[1]).seen(); return key[2]; }
  }
  return null;
}
