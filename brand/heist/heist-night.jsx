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
function MhSession({ D, go, no, canScore }) {
  const s = D.sessions.find(x => x.no === +no) || D.sessions.find(x => x.state === "live");
  const N = (D.nights && D.nights[s.no]) || {};
  const [tab, setTab] = React.useState("groups");
  const groups = Object.keys(N.groups || {});
  const [g, setG] = React.useState(groups[0] || "A");
  const live = s.state === "live";
  const stateLabel = live ? `● Live · ${mhDay(s.date)}` : s.state === "done" ? `Played · ${mhDay(s.date)}` : `${mhDay(s.date)} · ${s.time}`;
  return (
    <div className="mh-page">
      <main className="mh-body" data-bare="" style={{ padding: 0 }}>
        <MhSessionHead s={s} back={{ label: "Jobs", onClick: () => go("jobs") }}
          label={stateLabel} tone={live ? "coral" : "peach"} title={`${s.code} · ${s.title}`} />
        <div className="mh-col" style={{ padding: "4px 20px 0", gap: 10 }}>
          <MhPills label="Session" items={[["teams", "Teams"], ["groups", "Groups"], ["knockout", "Knockout"], ["mvp", "MVP"]]} value={tab} onChange={setTab} />
          {tab === "groups" && <>
            {groups.length > 0 && <MhPills label="Group" items={groups} value={g} onChange={setG} />}
            <MhGroupTable rows={(N.groups[g] || {}).standings || []} played={(N.groups[g] || {}).matches || []} />
            <MhLabel>Matches{canScore ? " · tap to score" : ""}</MhLabel>
            {((N.groups[g] || {}).matches || []).map((m, i) => (
              <MhMatchCard key={i} m={m} onClick={canScore && m.state !== "final" ? () => go("live", `${s.no}/${m.id || g + i}`) : null} />
            ))}
          </>}
          {tab === "teams" && <MhTeams N={N} />}
          {tab === "knockout" && <MhKnockout N={N} />}
          {tab === "mvp" && <MhMvp N={N} />}
        </div>
      </main>
      <MhGrain />
    </div>
  );
}
function MhGroupTable({ rows, played }) {
  const started = played.some(m => m.state === "final");
  return (
    <MhGlass style={{ padding: "6px 14px" }}>
      {rows.map((r, i) => (
        <div key={r.team} className="mh-grow">
          {/* nothing is marked as qualifying before a ball is hit */}
          <div className="mn-display" style={{ fontSize: 14, color: started && i < 2 ? "var(--mn-teal)" : "var(--mn-mist)" }}>{i + 1}</div>
          <div className="mh-gteam">{r.team}</div>
          <div className="mh-gw">{r.w}</div>
          <div className="mn-display" style={{ fontSize: 17, textAlign: "right" }}>{r.pts}</div>
        </div>
      ))}
    </MhGlass>
  );
}
function MhMatchCard({ m, onClick }) {
  const inner = (
    <div className="mh-split">
      <div style={{ textAlign: "left", minWidth: 0 }}>
        <div className="mh-mteam">{m.a}</div>
        <div className="mh-mteam" style={{ color: "var(--mn-mist)" }}>{m.b}</div>
      </div>
      <div style={{ textAlign: "right", flex: "none" }}>
        <MhDisplay size={22}>{m.score ? m.score.replace("-", "–") : "—"}</MhDisplay>
        {m.state === "live" ? <MhLabel tone="coral">● Live · Court {m.court}</MhLabel>
          : m.state === "final" ? <MhLabel>Final</MhLabel> : <MhLabel>Next</MhLabel>}
      </div>
    </div>
  );
  return onClick
    ? <button type="button" className="mn-glass mh-tap mh-match" onClick={onClick}>{inner}</button>
    : <div className="mn-glass mh-match">{inner}</div>;
}
function MhTeams({ N }) {
  const by = {};
  (N.teams || []).forEach(t => { (by[t.group] = by[t.group] || []).push(t); });
  const gs = Object.keys(by);
  if (!gs.length) return <MhGlass><MhSerif size={14}>The draw hasn't been made yet.</MhSerif></MhGlass>;
  return gs.map(g => (
    <div key={g} className="mh-col" style={{ gap: 6 }}>
      <MhLabel tone="peach">Group {g}</MhLabel>
      <MhGlass style={{ padding: "6px 14px" }}>
        {by[g].map(t => (
          <div key={t.a + t.b} className="mh-trow">
            <MhAvatar player={{ name: t.a, photo: t.aPhoto }} size={28} />
            <MhAvatar player={{ name: t.b, photo: t.bPhoto }} size={28} />
            <div className="mh-gteam" style={{ marginLeft: 4 }}>{t.a} &amp; {t.b}</div>
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
  return MH_ROUNDS.filter(([k]) => K[k] && [].concat(K[k]).length).map(([k, label]) => (
    <div key={k} className="mh-col" style={{ gap: 6 }}>
      <MhLabel tone={k === "final" ? "gold" : "peach"}>{label}</MhLabel>
      {[].concat(K[k]).map((m, i) => (
        <div key={i} className="mn-glass mh-match" data-accent={k === "final" ? "gold" : undefined}>
          <div className="mh-split">
            <div style={{ minWidth: 0 }}>
              <div className="mh-mteam" style={{ color: m.winner === "b" ? "var(--mn-mist)" : undefined }}>
                {m.sa && <span className="mh-seed">{m.sa}</span>}{m.a || "TBD"}</div>
              <div className="mh-mteam" style={{ color: m.winner === "a" ? "var(--mn-mist)" : m.winner === "b" ? undefined : "var(--mn-mist)" }}>
                {m.sb && <span className="mh-seed">{m.sb}</span>}{m.b || "TBD"}</div>
            </div>
            <MhDisplay size={22}>{m.score ? m.score.replace("-", "–") : "—"}</MhDisplay>
          </div>
        </div>
      ))}
    </div>
  ));
}
function MhMvp({ N }) {
  const M = N.mvp || { votes: [] };
  const top = M.votes.length ? Math.max(...M.votes.map(v => v.votes)) : 0;
  return (
    <div className="mh-col" style={{ gap: 10 }}>
      <MhLabel>{M.open ? "Voting open · players vote" : "MVP · player vote"}</MhLabel>
      {M.votes.length === 0 && <MhGlass><MhSerif size={14}>No votes yet.</MhSerif></MhGlass>}
      {M.votes.map(v => (
        <div key={v.name} className="mn-glass mh-match" data-accent={v.votes === top ? "peach" : undefined}>
          <div className="mh-split">
            <div className="mh-mteam">{v.name}</div>
            <MhDisplay size={20} tone={v.votes === top ? "peach" : undefined}>{v.votes}</MhDisplay>
          </div>
          <div className="mh-vbar"><div className="mn-fill" style={{ width: (top ? v.votes / top * 100 : 0) + "%" }} /></div>
        </div>
      ))}
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
  const add = side => { setHist(h => h.concat([[a, b]])); side === "a" ? setA(a + 1) : setB(b + 1); };
  const undo = () => { if (!hist.length) return; const [x, y] = hist[hist.length - 1]; setA(x); setB(y); setHist(hist.slice(0, -1)); };
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
          <MhButton kind="light" live onClick={() => onLock ? onLock({ t1: a, t2: b }) : go("back")}>Lock result</MhButton>
        </div>
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
