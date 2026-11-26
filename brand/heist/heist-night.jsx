// MUSCAT HEIST · Vol.10 — the session night (handoff phase 3):
// 07 Session detail (Teams · Groups · Knockout · MVP) · 08 Live Scoring ·
// 09 Episode Recap · 10 Recap Slides. Values are the static design's own.
//
// SCORING IS NOT CHANGED. Live Scoring's "+1 MUNTHER" adds one GAME (the
// fixture is first to 6, at 5-3), so +1 / Undo / Lock result produce exactly
// the final score the app has always recorded — entered game by game instead
// of on a number pad. Lock calls back with { t1, t2 } and the app's own
// engine decides winner, loss type and points, as it always has.

// The session header: art with the cut, the back link, and the episode line.
function MhSessionHead({ s, height = 250, cut = [80, 100], fade = "session", back, label, tone = "coral", title, titleSize = 38, children }) {
  return (
    <MhHeroCut height={height} src={s && s.art} pos={s && s.artPos} cut={cut} fade={fade}>
      {back && <button type="button" className="mh-back" onClick={back.onClick}>‹ {back.label}</button>}
      {children}
      {title && (
        <div style={{ position: "absolute", left: 20, bottom: 46 }}>
          {label && <MhLabel tone={tone}>{label}</MhLabel>}
          <div className="mn-display" style={{ fontSize: titleSize, lineHeight: .9 }}>{title}</div>
        </div>
      )}
    </MhHeroCut>
  );
}

// ── 07 SESSION DETAIL ─────────────────────────────────────────────────────
// What the night IS, before which tab you are on: a played night says who won,
// a live one what is happening, an upcoming one when and how full. Then the
// four tabs, every row carrying faces, every result saying who won it.
function MhSession({ D, go, no, canScore }) {
  const s = D.sessions.find(x => x.no === +no) || D.sessions.find(x => x.state === "live") || D.sessions[0];
  const N = (D.nights && D.nights[s.no]) || {};
  const groups = Object.keys(N.groups || {});
  const koDrawn = !!(N.knockout && [].concat(N.knockout.qf || [], N.knockout.sf || [], N.knockout.final || []).some(m => m && (m.a || m.b)));
  const [tab, setTab] = React.useState(s.state === "done" && koDrawn ? "knockout" : groups.length ? "groups" : "teams");
  const firstOpen = groups.find(g => !(N.groups[g] || {}).done) || groups[0] || "A";
  const [g, setG] = React.useState(firstOpen);
  const live = s.state === "live";
  const stateLabel = live ? `● Live · ${mhDay(s.date)}` : s.state === "done" ? `Played · ${mhDay(s.date)}` : `${mhDay(s.date)} · ${s.time}`;
  const hasTeams = (N.teams || []).length > 0;
  const clipSt = mhUseClips()(s.state === "live");
  const clips = mhClipsFor(clipSt, s.date);
  return (
    <div className="mh-page">
      <main className="mh-body" data-bare="" style={{ padding: 0 }}>
        <MhSessionHead s={s} back={{ label: "Jobs", onClick: () => go("jobs") }}
          label={stateLabel + (s.doublePoints ? " · 2X" : "")} tone={live ? "coral" : "peach"} title={`${s.code} · ${s.title}`} />
        <div className="mh-col" style={{ padding: "4px 20px 0", gap: 12 }}>
          <MhNightStatus s={s} N={N} go={go} />
          <div className="mh-actions">
            {hasTeams && <button type="button" className="mh-act" onClick={() => go("nightshare", `${s.no}/${N.champion ? "champions" : koDrawn ? "lineup" : "draw"}`)}>
              <span aria-hidden="true">↗</span> Posts</button>}
            {s.state === "done" && <button type="button" className="mh-act" onClick={() => go("recap", s.no)}><span aria-hidden="true">★</span> Recap</button>}
            {canScore && s.sid && <button type="button" className="mh-act" data-org="" onClick={() => go("results", s.no)}><span aria-hidden="true">⚙</span> Organiser</button>}
            {(clips.length > 0 || s.state !== "soon") && <button type="button" className="mh-act" data-on={tab === "clips" ? "" : undefined}
              onClick={() => setTab(tab === "clips" ? (hasTeams ? "teams" : "") : "clips")}><span aria-hidden="true">▶</span> Clips{clips.length ? ` · ${clips.length}` : ""}</button>}
          </div>
          {tab === "clips" ? <MhClips st={clipSt} list={clips} /> : hasTeams ? <>
            <MhPills label="Session" items={[["teams", "Teams"], ["groups", "Groups"], ["knockout", "Knockout"], ["mvp", N.mvp && N.mvp.votes.length ? "MVP" : "Points"]]} value={tab} onChange={setTab} />
            {tab === "groups" && <>
              {groups.length > 0 && <MhPills label="Group" items={groups.map(x => [x, (N.groups[x] || {}).done ? `${x} ✓` : x])} value={g} onChange={setG} />}
              <MhGroupTable rows={(N.groups[g] || {}).standings || []} started={N.started} done={(N.groups[g] || {}).done} />
              <MhLabel>Group {g} matches{canScore ? " · tap to score" : ""}</MhLabel>
              {((N.groups[g] || {}).matches || []).map((m, i) => (
                <MhMatchCard key={i} m={m} onClick={canScore && m.state !== "final" ? () => go("live", `${s.no}/${m.id || g + i}`) : null} />
              ))}
            </>}
            {tab === "teams" && <MhTeams N={N} />}
            {tab === "knockout" && <MhKnockout N={N} />}
            {tab === "mvp" && <MhMvp N={N} />}
          </> : <MhGlass><MhSerif size={15}>{s.state === "soon" ? "The draw is made on the night, once everybody has signed in." : "No teams were drawn for this night."}</MhSerif></MhGlass>}
        </div>
      </main>
      <MhGrain />
    </div>
  );
}
// the line under the header: who won / what is on / when it is
function MhNightStatus({ s, N, go }) {
  if (N.champion) {
    const C = N.champion;
    return (
      <MhGlass accent="gold" style={{ padding: "12px 14px" }}>
        <div className="mh-champ">
          <div className="mh-pairfaces">{C.team.players.map(p => <MhAvatar key={p.id} player={p} size={52} ring="gold" />)}</div>
          <div style={{ minWidth: 0, flex: 1 }}>
            <MhLabel tone="gold">Champions</MhLabel>
            <div className="mn-display mh-champname">{C.team.players.map(p => p.first).join(" & ")}</div>
            <div className="mh-champsub">won the final v {C.beat ? C.beat.players.map(p => p.first).join(" & ") : "—"}</div>
          </div>
          <MhDisplay size={30} tone="gold">{C.score.replace("-", "–")}</MhDisplay>
        </div>
      </MhGlass>
    );
  }
  if (s.state === "live" && s.progress) {
    const all = Object.values(N.groups || {}).flatMap(g => g.matches);
    const on = all.find(m => m.state === "live"), nx = all.find(m => m.state === "next");
    return (
      <MhGlass accent="coral" style={{ padding: "12px 14px" }}>
        <div className="mh-split"><MhLabel tone="coral">● Tonight · in play</MhLabel><MhLabel>{s.progress.played}/{s.progress.total} matches</MhLabel></div>
        <div className="mh-progress"><div style={{ width: (s.progress.total ? s.progress.played / s.progress.total * 100 : 0) + "%" }} /></div>
        {(on || nx) && <div className="mh-onnow"><span>{on ? "On court" : "Next"}</span>{(on || nx).a} <i>v</i> {(on || nx).b}</div>}
      </MhGlass>
    );
  }
  if (s.state === "soon") {
    const S = s.signups;
    return (
      <MhGlass style={{ padding: "12px 14px" }}>
        <div className="mh-split">
          <div><MhLabel tone="peach">{mhDay(s.date)} · {s.time}</MhLabel><MhSerif size={14} style={{ marginTop: 4 }}>{MH.venue}</MhSerif></div>
          {S && <div style={{ textAlign: "right" }}><MhDisplay size={26}>{S.teams}/{S.max}</MhDisplay><MhLabel>teams in</MhLabel></div>}
        </div>
      </MhGlass>
    );
  }
  return null;
}
function MhGroupTable({ rows, started, done }) {
  return (
    <MhGlass style={{ padding: "4px 14px 6px" }}>
      <div className="mh-grow mh-ghead" aria-hidden="true"><span>#</span><span>Team</span><span>W</span><span>GD</span><span>Pts</span></div>
      {rows.map(r => (
        // nothing is marked as qualifying before a ball is hit, and the mark is
        // the engine's own qualifying set, not "top two"
        <div key={r.id} className="mh-grow" data-q={started && r.q ? "" : undefined}>
          <div className="mn-display mh-gpos">{r.pos}</div>
          <div className="mh-gteamcell">
            <div className="mh-pairfaces mh-pairfaces-s">{(r.players || []).map(p => <MhAvatar key={p.id} player={p} size={24} />)}</div>
            <div className="mh-gteam">{r.team}</div>
          </div>
          <div className="mh-gw">{r.w}</div>
          <div className="mh-gw">{r.gd > 0 ? "+" + r.gd : r.gd}</div>
          <div className="mn-display mh-gpts">{r.pts}</div>
        </div>
      ))}
      {started && rows.some(r => r.q) && <div className="mh-qkey"><i /> {done ? "through to the knockout" : "in a qualifying place right now"}</div>}
    </MhGlass>
  );
}
// a result says who won it: the winner lit and their games in sand, the loser
// dimmed; each side carries its own games so nobody reads a score backwards
function MhMatchRow({ t, name, games, win, lose }) {
  return (
    <div className="mh-mrow" data-win={win ? "" : undefined} data-lose={lose ? "" : undefined}>
      <div className="mh-pairfaces mh-pairfaces-s">{t && t.players.map(p => <MhAvatar key={p.id} player={p} size={24} />)}</div>
      <div className="mh-mteam">{name || "TBD"}</div>
      <div className="mn-display mh-mgames">{games == null ? "" : games}</div>
    </div>
  );
}
function MhMatchCard({ m, onClick, accent, seeds }) {
  const inner = (
    <>
      <MhMatchRow t={m.ta} name={(seeds && m.sa ? m.sa + " · " : "") + (m.a || "TBD")} games={m.ga} win={m.winner === "a"} lose={m.winner === "b"} />
      <MhMatchRow t={m.tb} name={(seeds && m.sb ? m.sb + " · " : "") + (m.b || "TBD")} games={m.gb} win={m.winner === "b"} lose={m.winner === "a"} />
      <div className="mh-mstate">
        {m.state === "live" ? <MhLabel tone="coral">● Live{m.court ? ` · Court ${m.court}` : ""}</MhLabel>
          : m.winner ? (seeds ? null : <MhLabel>Final</MhLabel>) : <MhLabel>{onClick ? "Tap to score" : "Next"}</MhLabel>}
      </div>
    </>
  );
  return onClick
    ? <button type="button" className="mn-glass mh-tap mh-match" data-accent={accent} onClick={onClick}>{inner}</button>
    : <div className="mn-glass mh-match" data-accent={accent}>{inner}</div>;
}
function MhTeams({ N }) {
  const by = {};
  (N.teams || []).forEach(t => { (by[t.group || "—"] = by[t.group || "—"] || []).push(t); });
  const gs = Object.keys(by).sort();
  if (!gs.length) return <MhGlass><MhSerif size={14}>The draw hasn't been made yet.</MhSerif></MhGlass>;
  return gs.map(g => (
    <div key={g} className="mh-col" style={{ gap: 6 }}>
      <MhLabel tone="peach">Group {g}</MhLabel>
      <MhGlass style={{ padding: "4px 14px" }}>
        {by[g].map(t => (
          <div key={t.id} className="mh-trow" data-q={N.started && t.q ? "" : undefined}>
            {/* a team without a player list (the preview's fixture teams carry a name only)
                blanked the WHOLE night page on the Teams tab — React unmounts on a throw */}
            <div className="mh-pairfaces">{(t.players || []).map(p => <MhAvatar key={p.id} player={p} size={36} />)}</div>
            <div style={{ minWidth: 0, flex: 1 }}>
              {(t.players && t.players.length ? t.players : [{ name: t.name || "TBD" }]).map((p, i) => <div key={i} className="mh-gteam">{p.name}</div>)}
            </div>
            {N.started && t.pos ? <div className="mh-tstat"><b className="mn-display">{t.pts}</b><span>{t.w}W · #{t.pos}</span></div> : null}
          </div>
        ))}
      </MhGlass>
    </div>
  ));
}
const MH_ROUNDS = [["qf", "Quarter-finals"], ["sf", "Semi-finals"], ["final", "Final"]];
function MhKnockout({ N }) {
  const K = N.knockout;
  if (!K) return <MhGlass><MhSerif size={14}>The knockout is drawn once the groups finish.</MhSerif></MhGlass>;
  return (
    <>
      {MH_ROUNDS.filter(([k]) => K[k] && [].concat(K[k]).length).map(([k, label]) => (
        <div key={k} className="mh-col" style={{ gap: 6 }}>
          <MhLabel tone={k === "final" ? "gold" : "peach"}>{label}</MhLabel>
          {[].concat(K[k]).map((m, i) => <MhMatchCard key={i} m={m} seeds accent={k === "final" ? "gold" : undefined} />)}
        </div>
      ))}
      {N.champion && (
        <MhGlass accent="gold" style={{ textAlign: "center", padding: "16px 14px" }}>
          <MhLabel tone="gold">Champions</MhLabel>
          <div className="mh-pairfaces" style={{ justifyContent: "center", margin: "10px 0 8px" }}>
            {N.champion.team.players.map(p => <MhAvatar key={p.id} player={p} size={72} ring="gold" />)}</div>
          <div className="mn-display" style={{ fontSize: 26 }}>{N.champion.team.players.map(p => p.first).join(" & ")}</div>
          <MhSerif size={14} style={{ marginTop: 4 }}>{N.champion.score.replace("-", "–")} in the final · {MH.voucher} OMR voucher each</MhSerif>
        </MhGlass>
      )}
    </>
  );
}
// MVP when the players voted; tonight's points always — the engine's own
// per-night total, streak bonus excluded (it belongs to a run of nights)
function MhMvp({ N }) {
  const M = N.mvp || { votes: [] };
  const top = M.votes.length ? Math.max(...M.votes.map(v => v.votes)) : 0;
  const T = N.started && N.tonight ? N.tonight().slice(0, 12) : [];
  return (
    <div className="mh-col" style={{ gap: 10 }}>
      {(M.votes.length > 0 || M.open) && <MhLabel>{M.open ? "MVP · voting open" : "MVP · player vote"}</MhLabel>}
      {M.votes.map(v => (
        <div key={v.id} className="mn-glass mh-match" data-accent={v.votes === top ? "peach" : undefined}>
          <div className="mh-split">
            <div className="mh-mrow" style={{ border: 0, padding: 0, flex: 1 }}><MhAvatar player={v} size={28} /><div className="mh-mteam">{v.name}</div></div>
            <MhDisplay size={20} tone={v.votes === top ? "peach" : undefined}>{v.votes}</MhDisplay>
          </div>
          <div className="mh-vbar"><div className="mn-fill" style={{ width: (top ? v.votes / top * 100 : 0) + "%" }} /></div>
        </div>
      ))}
      <MhLabel tone="peach">Tonight's points</MhLabel>
      {T.length ? (
        <MhGlass style={{ padding: "4px 14px" }}>
          {T.map((p, i) => (
            <div key={p.id} className="mh-prow">
              <div className="mn-display mh-gpos">{i > 0 && T[i - 1].points === p.points ? "" : i + 1}</div>
              <MhAvatar player={p} size={30} />
              <div style={{ minWidth: 0, flex: 1 }}><div className="mh-gteam">{p.name}</div>{p.outcome && <div className="mh-psub">{p.outcome}</div>}</div>
              <div className="mn-display mh-gpts">+{p.points}</div>
            </div>
          ))}
        </MhGlass>
      ) : <MhGlass><MhSerif size={14}>Points appear once the first result is in.</MhSerif></MhGlass>}
      {T.length > 0 && <MhSerif size={12}>Per-night points. The streak bonus counts across the season, so it isn't in here.</MhSerif>}
    </div>
  );
}

// ── 08 LIVE SCORING ───────────────────────────────────────────────────────
// Games, not points: each +1 is one game to that team. Serve alternates every
// game from whichever team served first (the score card that is lit). Lock
// hands { t1, t2 } to the app, whose existing engine validates and scores it.
function MhLive({ D, go, match, onLock }) {
  const L = match || D.live;
  const [a, setA] = React.useState(L.a || 0), [b, setB] = React.useState(L.b || 0);
  const [hist, setHist] = React.useState([]);
  const [clock, setClock] = React.useState(L.clock || "");
  React.useEffect(() => {
    if (L.clock) return;
    const f = () => { const d = new Date(); setClock(`${d.getHours()}:${String(d.getMinutes()).padStart(2, "0")}`); };
    f(); const t = setInterval(f, 30000); return () => clearInterval(t);
  }, [L.clock]);
  const firstServeA = (L.serving || "A") === "A" ? ((L.a + L.b) % 2 === 0) : ((L.a + L.b) % 2 === 1);
  const servingA = ((a + b) % 2 === 0) === firstServeA;
  const buzz = ms => { try { navigator.vibrate && navigator.vibrate(ms); } catch (e) {} };
  const add = side => { buzz(10); setHist(h => h.concat([[a, b]])); side === "a" ? setA(a + 1) : setB(b + 1); };
  const undo = () => { if (!hist.length) return; buzz(10); const [x, y] = hist[hist.length - 1]; setA(x); setB(y); setHist(hist.slice(0, -1)); };
  // Lock asks once, in words: the score and who it gives the match to. A mistyped
  // result is the commonest fault of a night, and this is the last cheap moment to catch it.
  const [ask, setAsk] = React.useState(false);
  const winner = a > b ? L.teamA : b > a ? L.teamB : null;
  const lines = t => { const p = t.split(" & "); return <>{p[0].toUpperCase()}<br />&amp; {(p[1] || "").toUpperCase()}</>; };
  const first = t => t.split(" & ")[0].toUpperCase();
  const Card = ({ team, score, on }) => (
    <MhGlass accent={on ? "peach-50" : undefined}>
      <div style={{ display: "grid", gridTemplateColumns: "1fr auto", alignItems: "center" }}>
        <div>
          {on && <MhLabel tone="peach">Serving</MhLabel>}
          <div className="mn-display" style={{ fontSize: 26, fontWeight: 800, lineHeight: 1.05, color: on ? undefined : "var(--mn-mist)" }}>{lines(team)}</div>
        </div>
        <div className="mn-display" style={{ fontSize: 92, lineHeight: .85, color: on ? undefined : "var(--mn-mist)" }} aria-live="polite">{score}</div>
      </div>
    </MhGlass>
  );
  return (
    <div className="mh-page mh-live">
      <main className="mh-body" data-bare="" style={{ padding: 0, display: "flex", flexDirection: "column", minHeight: "100dvh" }}>
        <MhHeroCut height={300} src={L.art} pos={L.artPos || "center 25%"} cut={[84, 100]} fade="live">
          {/* the pill is the way back to the session: the design has no other exit */}
          <button type="button" className="mh-livepill" onClick={() => go("back")} aria-label={`Back to the session — live, court ${L.court}, group ${L.group}`}>
            <span className="mh-dot" aria-hidden="true" /><MhLabel tone="sand">Live · Court {L.court} · Group {L.group}</MhLabel></button>
          <div className="mh-clock">{clock}</div>
        </MhHeroCut>
        <div className="mh-col" style={{ padding: "0 20px", gap: 8 }}>
          <Card team={L.teamA} score={a} on={servingA} />
          <Card team={L.teamB} score={b} on={!servingA} />
          <div className="mh-two" style={{ gap: 8 }}>
            <MhButton live onClick={() => add("a")} kind="primary">+1 {first(L.teamA)}</MhButton>
            <MhButton live onClick={() => add("b")} kind="ghost">+1 {first(L.teamB)}</MhButton>
          </div>
        </div>
        <div className="mh-livefoot">
          <button type="button" className="mh-undo" onClick={undo} disabled={!hist.length}>Undo</button>
          <MhButton kind="light" live onClick={() => { buzz(15); setAsk(true); }}>Lock result</MhButton>
        </div>
        {ask && (
          <div className="mh-confirm" role="dialog" aria-modal="true" aria-label="Confirm the result">
            <div className="mn-glass mh-confirmbox">
              <MhLabel tone="peach">Lock this result?</MhLabel>
              <div className="mn-display" style={{ fontSize: 56, lineHeight: .95, marginTop: 6 }}>{a}–{b}</div>
              <MhSerif size={15} style={{ marginTop: 6 }}>{winner ? <>Match to <b>{winner}</b></> : "Level — a set needs a winner"}</MhSerif>
              <div className="mh-two" style={{ gap: 8, marginTop: 14 }}>
                <MhButton kind="ghost" live onClick={() => setAsk(false)}>Back</MhButton>
                <MhButton kind="light" live disabled={!winner} onClick={() => { buzz([12, 40, 12]); setAsk(false); onLock ? onLock({ t1: a, t2: b }) : go("back"); }}>Lock it</MhButton>
              </div>
            </div>
          </div>
        )}
      </main>
      <MhGrain />
    </div>
  );
}

// ── 09 EPISODE RECAP ──────────────────────────────────────────────────────
function MhRecap({ D, go, no }) {
  const s = D.sessions.find(x => x.no === +no) || D.sessions.filter(x => x.state === "done").slice(-1)[0];
  const R = (D.recaps || {})[s.no];
  if (!R) return null;
  const champs = R.champions.map(n => mhFirst(n).toUpperCase());
  const rep = R.repUps && R.repUps[0];
  const tiles = [
    ["MVP", "peach", R.mvp.votes ? R.mvp.name.toUpperCase() : "NOT VOTED", R.mvp.votes ? `${R.mvp.votes} vote${R.mvp.votes === 1 ? "" : "s"}` : "no votes were cast"],
    ["Biggest win", "teal", R.biggestWin.team.toUpperCase(), R.biggestWin.score.replace("-", "–")],
    ["Upset", "coral", R.upset.team.toUpperCase(), R.upset.note],
    rep ? ["Rep up", "teal", rep.name.toUpperCase(), `${rep.from} → ${rep.to}`]
        : R.climber ? ["Biggest climber", "teal", R.climber.name.toUpperCase(), R.climber.note] : null,
  ].filter(Boolean);
  return (
    <div className="mh-page">
      <main className="mh-body" data-bare="" style={{ padding: 0, display: "flex", flexDirection: "column", minHeight: "100dvh" }}>
        <MhHeroCut height={330} src={R.art || s.art} pos={R.artPos || "center 50%"} cut={[82, 100]} fade="recap">
          <div style={{ position: "absolute", left: 20, top: 58 }}><MhSceneTag gold>Episode complete</MhSceneTag></div>
          <div style={{ position: "absolute", left: 20, bottom: 64 }}>
            <MhLabel tone="gold">{s.code} · {s.title} · Champions</MhLabel>
            <div className="mn-display" style={{ fontSize: 42, lineHeight: .88 }}>{champs[0]} &amp;<br />{champs[1]}</div>
            <MhSerif size={16} tone="sand">beat {R.beat.map(mhFirst).join(" & ")} {R.score.replace("-", "–")}{R.pointsEach ? ` · +${R.pointsEach} each` : ""}</MhSerif>
          </div>
        </MhHeroCut>
        <div className="mh-tiles">
          {tiles.map(([k, tone, name, sub]) => (
            <MhGlass key={k} style={{ padding: "10px 12px" }}>
              <MhLabel tone={tone}>{k}</MhLabel>
              <MhDisplay size={18} style={{ lineHeight: 1.05, marginTop: 3 }}>{name}</MhDisplay>
              <MhSerif size={13}>{sub}</MhSerif>
            </MhGlass>
          ))}
        </div>
        {R.yourNight && (
          <div style={{ padding: "10px 20px 0" }}>
            <button type="button" className="mn-glass mh-tap" data-accent="teal-50" onClick={() => go("cardpull", s.no)}>
              <div className="mh-split">
                <div><MhLabel tone="teal">Your episode</MhLabel>
                  <MhDisplay size={20}>+{R.yourNight.points} · {R.yourNight.note.toUpperCase()}</MhDisplay></div>
                <MhSerif size={14} tone="peach" style={{ textAlign: "right" }}>New crew card<br />waiting ›</MhSerif>
              </div>
            </button>
          </div>
        )}
        <div className="mh-recapfoot">
          <MhButton onClick={() => go("slides", s.no)}>Share</MhButton>
          <MhButton kind="ghost" onClick={() => go("results", s.no)}>Full results</MhButton>
        </div>
      </main>
      <MhGrain />
    </div>
  );
}

// ── 10 RECAP SLIDES ───────────────────────────────────────────────────────
// Five slides, 5s each, auto-advancing; pressed = paused. Tap the right third
// for next, the left third for previous; swipe down or ✕ to close; ←/→ keys.
// Under reduced motion nothing advances on its own and nothing animates.
const MH_SLIDE_MS = 5000;
function mhSlides(D, s, R) {
  const me = D.players.find(p => p.id === D.meId);
  const P = n => D.players.find(p => p.name === n || mhFirst(p.name) === n) || { name: n };
  const out = [
    { key: "Champions", label: "Champions", name: R.champions.map(mhFirst).join(" & "), sub: `beat ${R.beat.map(mhFirst).join(" & ")} ${R.score.replace("-", "–")}`, who: P(R.champions[0]) },
    // a night nobody voted on has no MVP slide rather than a slide that says "—"
    R.mvp.votes ? { key: "MVP", label: "MVP · player vote", name: R.mvp.name, sub: `${R.mvp.votes} vote${R.mvp.votes === 1 ? "" : "s"}${R.mvp.note ? " · " + R.mvp.note : ""}`, who: P(R.mvp.name) } : null,
    { key: "Biggest win", label: "Biggest win", name: R.biggestWin.team, sub: R.biggestWin.score.replace("-", "–"), who: P(R.biggestWin.team.split(" & ")[0]) },
    { key: "Upset", label: "Upset", name: R.upset.team, sub: R.upset.note, who: P(R.upset.team.split(" & ")[0]) },
  ];
  for (let k = out.length - 1; k >= 0; k--) if (!out[k]) out.splice(k, 1);
  if (R.yourNight && me) out.push({ key: "Your night", label: "Your night", name: `+${R.yourNight.points}`, sub: R.yourNight.note, who: me, last: true });
  return out;
}
function MhSlides({ D, go, no, start = 0 }) {
  const s = D.sessions.find(x => x.no === +no) || D.sessions.filter(x => x.state === "done").slice(-1)[0];
  const R = (D.recaps || {})[s.no];
  const slides = mhSlides(D, s, R);
  const [i, setI] = React.useState(Math.min(start, slides.length - 1));
  const [held, setHeld] = React.useState(false);
  const reduced = React.useMemo(() => matchMedia("(prefers-reduced-motion: reduce)").matches, []);
  const touch = React.useRef(null);
  const next = () => setI(x => Math.min(slides.length - 1, x + 1));
  const prev = () => setI(x => Math.max(0, x - 1));
  React.useEffect(() => {
    if (reduced || held || i >= slides.length - 1) return;
    const t = setTimeout(next, MH_SLIDE_MS); return () => clearTimeout(t);
  }, [i, held, reduced]);
  React.useEffect(() => {
    const k = e => { if (e.key === "ArrowRight") next(); else if (e.key === "ArrowLeft") prev(); else if (e.key === "Escape") go("back"); };
    addEventListener("keydown", k); return () => removeEventListener("keydown", k);
  }, []);
  const S = slides[i];
  const tap = e => { const x = e.clientX / innerWidth; if (x > 2 / 3) next(); else if (x < 1 / 3) prev(); };
  return (
    <div className="mh-slides" onPointerDown={() => setHeld(true)} onPointerUp={() => setHeld(false)} onPointerLeave={() => setHeld(false)}
      onClick={tap}
      onTouchStart={e => { touch.current = e.touches[0].clientY; }}
      onTouchEnd={e => { if (touch.current != null && e.changedTouches[0].clientY - touch.current > 90) go("back"); touch.current = null; }}>
      <div className="mh-slidesart"><MhArt src={R.art || s.art} pos={R.artPos || "center 50%"} /></div>
      <div className="mh-slidesfade" aria-hidden="true" />
      <div className="mh-segbar" aria-hidden="true">
        {slides.map((x, k) => (
          <div key={x.key}><div style={{ width: k < i ? "100%" : k > i ? "0%" : (reduced ? "100%" : undefined) }}
            className={k === i && !reduced ? "mh-segrun" : undefined} data-held={held ? "" : undefined} /></div>
        ))}
      </div>
      <div className="mh-slideshead">
        <MhLabel tone="sand">{s.code} recap · {i + 1} of {slides.length}</MhLabel>
        <button type="button" className="mh-x" onClick={e => { e.stopPropagation(); go("back"); }} aria-label="Close">✕</button>
      </div>
      <div className="mh-slide" key={S.key} aria-live="polite">
        <div className="mh-slidephoto">
          <MhAvatar player={{ name: S.who.name, photo: S.who.photo, photoPos: S.who.avPos || S.who.pos }} size={150} zoom={S.who.zoom} />
        </div>
        <MhLabel tone="peach">{S.label}</MhLabel>
        <div className="mn-display" style={{ fontSize: 64, lineHeight: .86 }}>{S.name}</div>
        <MhSerif size={18}>{S.sub}</MhSerif>
        {S.last && <MhButton onClick={e => { e.stopPropagation(); go("share", s.no); }} style={{ marginTop: 8, width: "100%" }}>Share</MhButton>}
      </div>
      <div className="mh-slidesfoot">
        <button type="button" className="mh-hint" onClick={e => { e.stopPropagation(); prev(); }} disabled={i === 0}>{i > 0 ? `‹ ${slides[i - 1].key}` : ""}</button>
        <button type="button" className="mh-hint" data-next="" onClick={e => { e.stopPropagation(); next(); }} disabled={i === slides.length - 1}>{i < slides.length - 1 ? `${slides[i + 1].key} ›` : ""}</button>
      </div>
    </div>
  );
}


// ── CLIPS (SaveMyPlay), as National has them ────────────────────────────────
// A player presses the button on court after a point and the last 25 seconds
// land on the club's SaveMyPlay page a few minutes later. The fetching, the
// night a clip belongs to (Muscat time, anything before 04:00 is the night
// before) and the polling are National's own (useNaClips, naClipsForNight),
// inherited with the page; these are the Heist screens over them. Nothing is
// copied to our server: the video plays from SaveMyPlay and links back there.
const mhNoClips = () => ({ clips: [], err: false });
function mhUseClips() { return typeof useNaClips === "function" ? useNaClips : mhNoClips; }
function mhClipsFor(st, date) { return typeof naClipsForNight === "function" ? naClipsForNight(st.clips, date) : []; }
const mhClipLine = c => (typeof naClipCourt === "function" ? naClipCourt(c) : "Court") + " · " + (typeof naClipWhen === "function" ? naClipWhen(c) : "");

function MhClipThumb({ c, onPick, wide }) {
  return (
    <button type="button" className="mh-clip" data-wide={wide ? "" : undefined} onClick={onPick} aria-label={"Play clip, " + mhClipLine(c)}>
      <img src={c.thumb} alt="" loading="lazy" decoding="async" />
      <span className="mh-clipplay" aria-hidden="true">▶</span>
      <span className="mh-clipcap">{mhClipLine(c)}</span>
    </button>
  );
}
function MhClipViewer({ list, at, onAt, onClose }) {
  const c = list[at];
  React.useEffect(() => {
    const k = e => { if (e.key === "Escape") onClose(); };
    addEventListener("keydown", k); return () => removeEventListener("keydown", k);
  }, []);
  if (!c) return null;
  const page = typeof naClipPage === "function" ? naClipPage(c) : (typeof NA_HIGHLIGHTS_URL !== "undefined" ? NA_HIGHLIGHTS_URL : "#");
  // portalled to <body>: inside the page it inherited the screen's entrance
  // animation, whose transform turns position:fixed into "fixed to the column"
  const ui = (
    <div className="mh-clipview" role="dialog" aria-modal="true" aria-label="Clip">
      <div className="mh-clipbar">
        <MhLabel tone="sand">{mhClipLine(c)}</MhLabel>
        <span className="mh-clipn">{at + 1} / {list.length}</span>
        <button type="button" className="mh-clipx" onClick={onClose} aria-label="Close">✕</button>
      </div>
      <video key={c.id} src={c.video} poster={c.poster || c.thumb} controls playsInline autoPlay preload="metadata" />
      <div className="mh-clipnav">
        <button type="button" className="mh-act" disabled={at === 0} onClick={() => onAt(at - 1)}>← Earlier</button>
        <a className="mh-act" href={c.video} download target="_blank" rel="noopener noreferrer">⤓ Save</a>
        <button type="button" className="mh-act" disabled={at === list.length - 1} onClick={() => onAt(at + 1)}>Later →</button>
      </div>
      <a className="mh-cliplink" href={page} target="_blank" rel="noopener noreferrer">Open on SaveMyPlay ↗</a>
    </div>
  );
  return ReactDOM.createPortal(ui, document.body);
}
function MhClips({ st, list }) {
  const [at, setAt] = React.useState(null);
  const all = typeof NA_HIGHLIGHTS_URL !== "undefined" ? NA_HIGHLIGHTS_URL : null;
  return (
    <div className="mh-col" style={{ gap: 10 }}>
      <div className="mh-split"><MhDisplay size={22}>From the courts</MhDisplay>
        {list.length > 0 && <MhLabel>{list.length} clip{list.length === 1 ? "" : "s"}</MhLabel>}</div>
      <MhSerif size={14} tone="mist">Press the SaveMyPlay button on court after a point and the last 25 seconds land here a few minutes later.</MhSerif>
      {st.clips === null && !st.err && <div className="mh-clipgrid">{[0, 1, 2, 3].map(k => <div key={k} className="mh-clip" data-skel="" />)}</div>}
      {st.err && !st.clips && <MhSerif size={14}>The clips could not be loaded just now.</MhSerif>}
      {st.clips && list.length === 0 && <MhSerif size={14}>No clips from this night yet.</MhSerif>}
      {list.length > 0 && <div className="mh-clipgrid">{list.map((c, k) => <MhClipThumb key={c.id} c={c} onPick={() => setAt(k)} />)}</div>}
      {all && <a className="mh-cliplink" href={all} target="_blank" rel="noopener noreferrer">Every clip from the club on SaveMyPlay ↗</a>}
      {at !== null && <MhClipViewer list={list} at={at} onAt={setAt} onClose={() => setAt(null)} />}
    </div>
  );
}
// HOME: the latest night's clips for a week after it, then only the night page has them
function MhHomeClips({ D, go }) {
  const st = mhUseClips()(false);
  const [at, setAt] = React.useState(null);
  if (!st.clips || !st.clips.length || typeof naClipNight !== "function") return null;
  const newest = [...st.clips].sort((a, b) => b.start_time - a.start_time)[0];
  if (Date.now() / 1000 - newest.start_time > 7 * 86400) return null;
  const night = naClipNight(newest);
  const list = mhClipsFor(st, night).reverse().slice(0, 12);
  const s = (D.sessions || []).find(x => x.date === night);
  return (
    <div className="mh-col" style={{ gap: 8 }}>
      <div className="mh-split"><MhLabel tone="peach">Latest clips · {s ? s.code : mhDay(night)}</MhLabel>
        {s && <button type="button" className="mh-linkbtn" onClick={() => go("session", s.no)}>All {list.length} ›</button>}</div>
      <div className="mh-cliprow">{list.map((c, k) => <MhClipThumb key={c.id} c={c} wide onPick={() => setAt(k)} />)}</div>
      {at !== null && <MhClipViewer list={list} at={at} onAt={setAt} onClose={() => setAt(null)} />}
    </div>
  );
}
