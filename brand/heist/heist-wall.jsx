// ═════════════════════════════════════════════════════════════════════════
// THE WALL — the big screen beside the courts (?tv=), in the Heist's own
// clothes (owner, 26 Nov 2026: "everyone sees the session on the big screen,
// I don't want it to be bland").
//
// The inherited wall (Blackout's WallPage) stays in the page unreferenced; the
// route, the session pick (wallSession, &s=<id>) and the poll are its. What
// changes is what the room sees:
//   - the night's own painting, full-bleed and slowly pushing in
//   - the owner's logo, the episode code and title, 2X on a double night
//   - ON COURT: each group's match being played, face to face, and the next
//   - a rotating panel: the group tables, the bracket, tonight's points
//   - THE MOMENT A SCORE IS LOCKED on the scorer's phone, the wall takes it
//     over for eight seconds: the winners' faces, the score, and what it did
//     ("top of Group B", "into the final"). A final ends on the champions.
//   - a ticker of the night's results along the foot
// Every figure is heistData's, which is the inherited engine's. Nothing here
// writes, so the wall can never break the phone entering the scores.
//
// Sizes are one unit, --u = min(1vh, 1.78vw): one page serves a 1080x1920
// panel, a 4K portrait display and a landscape TV, which gets two columns.
// ═════════════════════════════════════════════════════════════════════════
const MHW_POLL = 10;          // seconds between pulls of /state
const MHW_ROTATE = 16;        // seconds a panel stays up
const MHW_FLASH = 8;          // seconds a result holds the wall

const mhwRound = { qf: "Quarter-final", sf: "Semi-final", final: "The final" };
const mhwPair = t => t ? t.players.map(p => p.first || mhFirstOf(p.name)).join(" & ") : "—";

function MhwFace({ p, size, ring, dim }) {
  return (
    <div className="mn-avatar mhw-face" data-ring={ring || undefined} data-dim={dim ? "" : undefined}
      style={{ width: `calc(var(--u) * ${size})`, height: `calc(var(--u) * ${size})`, fontSize: `calc(var(--u) * ${size} * .14)` }}>
      <MhArt src={p && p.photo} name={p && p.name} eager />
    </div>
  );
}
const MhwStack = ({ t }) => (
  <span className="mhw-stack">{(t ? t.players : []).map((p, i) => <span key={i} className="mh-fitline">{p.first || mhFirstOf(p.name)}</span>)}</span>
);
const MhwPairFaces = ({ t, size, ring, dim }) => (
  <div className="mhw-pairfaces">{(t ? t.players : [null, null]).map((p, i) => <MhwFace key={i} p={p} size={size} ring={ring} dim={dim} />)}</div>
);

// every decided match on the night, keyed so a new one can be told from an old one
function mhwDecided(N) {
  const out = [];
  Object.entries(N.groups || {}).forEach(([g, G]) => G.matches.forEach(m => {
    if (m.winner) out.push({ key: "g:" + m.id, kind: "group", group: g, m, label: "Group " + g });
  }));
  const K = N.knockout;
  if (K) [...K.qf, ...K.sf, K.final].filter(Boolean).forEach(m => {
    if (m.winner) out.push({ key: `k:${m.round}:${m.n}`, kind: m.round, m, label: mhwRound[m.round] + (m.round !== "final" ? " " + m.n : "") });
  });
  return out;
}
// what a result did, in one line, read off the tables it changed
function mhwWhat(N, r) {
  const w = r.m.winner === "a" ? r.m.ta : r.m.tb;
  if (r.kind === "final") return "tonight's champions";
  if (r.kind === "sf") return "into the final";
  if (r.kind === "qf") return "into the semi-finals";
  const G = (N.groups || {})[r.group]; const row = G && w && G.standings.find(x => x.id === w.id);
  if (!row) return "";
  if (row.pos === 1) return G.done ? `win Group ${r.group}` : `top of Group ${r.group}`;
  return `${["", "1st", "2nd", "3rd", "4th", "5th"][row.pos] || row.pos + "th"} in Group ${r.group}`;
}

// The display lines (the episode title, the champions, a result's winners) are
// set big and shrunk in proportion until they fit their box — width scales with
// the size, so one step is exact. mhFitAll stops at 60%, which "the double
// cross" in Bowlby One still overran beside the logo and the clock.
function mhwFit() {
  for (const el of document.querySelectorAll(".mhw-fit")) {
    el.style.fontSize = "";
    if (!el.clientWidth) continue;
    // a range over ellipsised text measures the TRIMMED run, so the ellipsis is
    // off while it is measured ("hassan & tal…" fitted as if it already fitted)
    el.style.textOverflow = "clip";
    const r = document.createRange(); r.selectNodeContents(el);
    const w = r.getBoundingClientRect().width, room = el.clientWidth - 2;
    el.style.textOverflow = "";
    if (w > room) el.style.fontSize = (parseFloat(getComputedStyle(el).fontSize) * room / w * .98) + "px";
  }
}

function MhWall({ state, leaderboard, refreshNow }) {
  const [portraits, setPortraits] = React.useState({});
  const [now, setNow] = React.useState(() => new Date());
  const [panel, setPanel] = React.useState(0);
  const [flash, setFlash] = React.useState(null);
  const queue = React.useRef([]);
  const seen = React.useRef(null);

  // the wall pulls for itself: the App's own poll is skipped when signed in,
  // and the screen beside the courts is very often the scoring device
  React.useEffect(() => {
    const pull = () => { try { refreshNow(); } catch (e) {} };
    const t = setInterval(pull, MHW_POLL * 1000);
    addEventListener("mh-wall-poll", pull);
    return () => { clearInterval(t); removeEventListener("mh-wall-poll", pull); };
  }, [refreshNow]);
  React.useEffect(() => { const t = setInterval(() => setNow(new Date()), 15000); return () => clearInterval(t); }, []);
  React.useEffect(() => {
    let live = true;
    fetch(MH_HOST_PHOTOS).then(r => r.json()).then(j => {
      if (live && j.ok) setPortraits(Object.fromEntries(j.players.filter(p => p.heist).map(p => [p.id, p.heist])));
    }).catch(() => {});
    return () => { live = false; };
  }, []);
  React.useLayoutEffect(mhwFit);
  React.useEffect(() => {
    const f = () => requestAnimationFrame(mhwFit);
    addEventListener("resize", f); document.fonts && document.fonts.addEventListener("loadingdone", f); document.fonts && document.fonts.ready.then(f);
    return () => { removeEventListener("resize", f); document.fonts && document.fonts.removeEventListener("loadingdone", f); };
  }, []);
  React.useEffect(() => { document.documentElement.classList.add("mhw-on"); return () => document.documentElement.classList.remove("mhw-on"); }, []);

  const D = React.useMemo(() => heistData(state, { leaderboard, portraits, artBase: "assets/art/" }), [state, leaderboard, portraits]);
  const sess = typeof wallSession === "function" ? wallSession(state) : null;
  const sv = (sess && D.sessions.find(x => x.sid === sess.id)) || D.sessions.find(x => x.state === "live") || D.sessions.find(x => x.state === "soon") || D.sessions[D.sessions.length - 1];
  const N = (sv && D.nights[sv.no]) || {};
  const groups = Object.entries(N.groups || {});
  const K = N.knockout;
  const decided = sv ? mhwDecided(N) : [];

  // a result that was not there on the last pull takes the wall over
  React.useEffect(() => {
    const keys = new Set(decided.map(r => r.key));
    if (seen.current && seen.current.sid === (sv && sv.sid)) {
      const fresh = decided.filter(r => !seen.current.keys.has(r.key));
      if (fresh.length) { queue.current.push(...fresh.map(r => ({ ...r, what: mhwWhat(N, r) }))); if (!flash) setFlash(queue.current.shift()); }
    }
    seen.current = { sid: sv && sv.sid, keys };
  }, [state]);
  React.useEffect(() => {
    if (!flash) return;
    const t = setTimeout(() => setFlash(queue.current.shift() || null), (flash.kind === "final" ? 1.5 : 1) * MHW_FLASH * 1000);
    return () => clearTimeout(t);
  }, [flash]);

  // the panels this night has, rotated
  const panels = [];
  if (sv && sv.state === "soon") panels.push("draw");
  if (groups.length && N.started) panels.push("tables");
  if (K) panels.push("bracket");
  if (N.started) panels.push("points");
  if (!panels.length) panels.push("draw");
  React.useEffect(() => {
    const step = () => setPanel(p => p + 1);
    const t = setInterval(step, MHW_ROTATE * 1000);
    addEventListener("mh-wall-next", step);   // the harness turns the panel without waiting it out
    return () => { clearInterval(t); removeEventListener("mh-wall-next", step); };
  }, []);
  const which = panels[panel % panels.length];

  if (!sv) return <div className="mhw"><div className="mhw-empty mn-display">no night scheduled</div></div>;

  // ── what is on court: the first open match in each group, then the next ──
  const groupOpen = groups.map(([g, G]) => {
    const open = G.matches.filter(m => !m.winner);
    return { g, now: open[0], next: open[1], left: open.length, total: G.matches.length };
  });
  const koOpen = K ? [...K.qf, ...K.sf, K.final].filter(m => m && !m.winner && m.ta && m.tb) : [];
  const stage = !N.started ? "soon" : N.champion ? "done" : K ? "ko" : "groups";
  const all = [...groups.flatMap(([, G]) => G.matches), ...(K ? [...K.qf, ...K.sf, K.final].filter(Boolean) : [])];
  const played = all.filter(m => m.winner).length;
  const total = Math.max(all.length, played) || 1;
  const stageWord = { soon: "Tonight", groups: "Group stage", ko: K && K.final && K.final.ta && K.final.tb ? "The final" : K && K.sf.some(m => m.ta) ? "Semi-finals" : "Knockouts", done: "Full time" }[stage];
  const clock = `${String(now.getHours()).padStart(2, "0")}:${String(now.getMinutes()).padStart(2, "0")}`;
  const ticker = decided.slice().reverse().slice(0, 10);

  return (
    <div className="mhw" data-stage={stage} data-flash={flash ? "" : undefined}>
      <div className="mhw-bg" aria-hidden="true"><div className="mhw-kb"><MhArt src={sv.art} pos={sv.artPos || "center"} eager /></div></div>
      <div className="mhw-shade" aria-hidden="true" />

      <div className="mhw-head">
        <img className="mhw-logo" src={mhLogoSrc() + ".webp"} alt="Urban Playground Muscat Heist" />
        <div className="mhw-ep">
          <div className="mhw-code">{sv.code}{sv.doublePoints && <span className="mhw-2x">2X</span>}</div>
          <div className="mn-display mhw-title mhw-fit">{sv.title}</div>
          <div className="mhw-meta">{mhDay(sv.date)} · {MH.venue || "Al Hail North"}</div>
        </div>
        <div className="mhw-clock">
          <div className="mhw-live" data-on={stage === "groups" || stage === "ko" ? "" : undefined}>{stage === "groups" || stage === "ko" ? "LIVE" : stage === "done" ? "FINAL" : MH.time || ""}</div>
          <div className="mhw-time">{clock}</div>
        </div>
      </div>

      <div className="mhw-prog">
        <div className="mhw-progword">{stageWord}</div>
        <div className="mhw-bar"><i style={{ width: (stage === "soon" ? 0 : 100 * played / total) + "%" }} /></div>
        <div className="mhw-progn">{stage === "soon" ? `${(N.teams || []).length} pairs in` : `${played} / ${total}`}</div>
      </div>

      <div className="mhw-main">
        <div className="mhw-now">
          {stage === "done" && N.champion ? <MhwChampions c={N.champion} sv={sv} />
          : stage === "soon" ? <MhwSoon sv={sv} N={N} />
          : <>
              <div className="mhw-label">{stage === "ko" ? "On court · knockouts" : "On court now"}</div>
              <div className="mhw-courts" data-n={stage === "ko" ? Math.min(koOpen.length, 4) : groupOpen.length}>
                {stage === "ko"
                  ? koOpen.slice(0, 4).map((m, i) => <MhwCourt key={i} tag={mhwRound[m.round] + (m.round !== "final" ? " " + m.n : "")} m={m} hot={m.round === "final"} />)
                  : groupOpen.map(o => <MhwCourt key={o.g} tag={`Group ${o.g}${o.now && o.now.court ? " · Court " + o.now.court : ""}`} m={o.now} next={o.next}
                      done={!o.now} left={o.left} />)}
                {stage === "ko" && !koOpen.length && <div className="mhw-wait mn-display">next round being drawn</div>}
              </div>
            </>}
        </div>

        <div className="mhw-panel" key={which}>
          {which === "tables" && <MhwTables groups={groups} />}
          {which === "bracket" && <MhwBracket K={K} />}
          {which === "points" && <MhwPoints list={N.tonight ? N.tonight().slice(0, 10) : []} double={sv.doublePoints} />}
          {which === "draw" && <MhwDraw N={N} />}
          {panels.length > 1 && <div className="mhw-dots">{panels.map((p, i) => <i key={p} data-on={p === which ? "" : undefined} />)}</div>}
        </div>
      </div>

      <div className="mhw-foot">
        <div className="mhw-tick">
          {ticker.length ? <div className="mhw-tickrun" style={{ animationDuration: Math.max(24, ticker.length * 7) + "s" }}>
            {[0, 1].map(k => <span key={k} aria-hidden={k ? "true" : undefined}>{ticker.map(r => {
              const w = r.m.winner === "a"; const sc = w ? `${r.m.ga}–${r.m.gb}` : `${r.m.gb}–${r.m.ga}`;
              return <em key={r.key}><b>{r.label}</b> {mhwPair(w ? r.m.ta : r.m.tb)} <strong>{sc}</strong> {mhwPair(w ? r.m.tb : r.m.ta)}</em>;
            })}</span>)}
          </div> : <div className="mhw-tickidle">Results land here the moment the scorer locks them</div>}
        </div>
        <div className="mhw-url">heist.urbanpadel.om</div>
      </div>

      {flash && <MhwFlash key={flash.key} r={flash} N={N} sv={sv} />}
    </div>
  );
}

function MhwCourt({ tag, m, next, done, left, hot }) {
  if (done) return (
    <div className="mhw-court" data-done="">
      <div className="mhw-ctag">{tag}</div>
      <div className="mhw-cdone mn-display">group played</div>
    </div>
  );
  return (
    <div className="mhw-court" data-hot={hot ? "" : undefined}>
      <div className="mhw-ctag">{tag}{left > 1 && <span>{left} to play</span>}</div>
      <div className="mhw-vs">
        <div className="mhw-side"><MhwPairFaces t={m.ta} size="var(--cf)" /><MhwStack t={m.ta} /></div>
        <div className="mhw-vsword mn-display">vs</div>
        <div className="mhw-side"><MhwPairFaces t={m.tb} size="var(--cf)" /><MhwStack t={m.tb} /></div>
      </div>
      {next && <div className="mhw-next"><b>Next</b> <span>{mhwPair(next.ta)} <i>v</i> {mhwPair(next.tb)}</span></div>}
    </div>
  );
}

function MhwTables({ groups }) {
  return (
    <>
      <div className="mhw-label">The tables<span className="mhw-key"><i /> qualifying right now</span></div>
      <div className="mhw-tables" data-n={groups.length}>
        {groups.map(([g, G]) => (
          <div className="mhw-group" key={g}>
            <div className="mhw-ghead"><span className="mn-display">group {g.toLowerCase()}</span><em>W</em><em>GD</em><em>PTS</em></div>
            {G.standings.map(r => (
              <div className="mhw-grow" key={r.id} data-q={r.q ? "" : undefined}>
                <span className="mhw-gpos">{r.pos}</span>
                <MhwPairFaces t={r} size="var(--rf)" />
                <MhwStack t={r} />
                <em>{r.w}</em><em>{r.gd > 0 ? "+" + r.gd : r.gd}</em><em className="mhw-gpts">{r.pts}</em>
              </div>
            ))}
          </div>
        ))}
      </div>
    </>
  );
}

function MhwBracket({ K }) {
  const row = (m, i) => (
    <div className="mhw-kmatch" key={i} data-final={m.round === "final" ? "" : undefined}>
      {[["a", m.ta, m.ga, m.sa], ["b", m.tb, m.gb, m.sb]].map(([k, t, g, s]) => (
        <div className="mhw-kside" key={k} data-win={m.winner === k ? "" : undefined} data-lose={m.winner && m.winner !== k ? "" : undefined}>
          <MhwPairFaces t={t} size={m.round === "final" ? "calc(var(--rf) * 1.3)" : "var(--rf)"} />
          <span className="mhw-kname mh-fitline">{t ? mhwPair(t) : s || "—"}</span>
          <b>{g != null ? g : ""}</b>
        </div>
      ))}
    </div>
  );
  return (
    <>
      <div className="mhw-label">The knockout</div>
      <div className="mhw-bracket">
        {K.qf.length > 0 && <div className="mhw-kround"><div className="mhw-kr">Quarter-finals</div><div className="mhw-kgrid">{K.qf.map(row)}</div></div>}
        {K.sf.length > 0 && <div className="mhw-kround"><div className="mhw-kr">Semi-finals</div><div className="mhw-kgrid" data-two="">{K.sf.map(row)}</div></div>}
        {K.final && <div className="mhw-kround"><div className="mhw-kr">The final</div>{row(K.final, 0)}</div>}
      </div>
    </>
  );
}

function MhwPoints({ list, double }) {
  return (
    <>
      <div className="mhw-label">Tonight's points{double && <span className="mhw-2x">2X</span>}<span className="mhw-key">streak bonus not included</span></div>
      <div className="mhw-points">
        {list.map((p, i) => (
          <div className="mhw-prow" key={p.id} data-top={i < 3 ? "" : undefined}>
            <span className="mhw-gpos">{list.findIndex(x => x.points === p.points) + 1}</span>
            <MhwFace p={p} size="var(--rf)" />
            <span className="mhw-gname mh-fitline">{p.name}</span>
            <b>+{p.points}</b>
          </div>
        ))}
        {!list.length && <div className="mhw-wait mn-display">first points on the way</div>}
      </div>
    </>
  );
}

function MhwDraw({ N }) {
  const teams = N.teams || [];
  const byG = {};
  teams.forEach(t => { (byG[t.group || "—"] = byG[t.group || "—"] || []).push(t); });
  const gs = Object.entries(byG);
  return (
    <>
      <div className="mhw-label">{gs.length > 1 ? "The draw" : "The crew tonight"}</div>
      <div className="mhw-tables" data-n={gs.length}>
        {gs.map(([g, ts]) => (
          <div className="mhw-group" key={g}>
            {g !== "—" && <div className="mhw-ghead"><span className="mn-display">group {g.toLowerCase()}</span></div>}
            {ts.map(t => (
              <div className="mhw-grow" key={t.id}><MhwPairFaces t={t} size="var(--rf)" /><MhwStack t={t} /></div>
            ))}
          </div>
        ))}
        {!teams.length && <div className="mhw-wait mn-display">sign-ups open</div>}
      </div>
    </>
  );
}

function MhwSoon({ sv, N }) {
  return (
    <div className="mhw-soon">
      <div className="mhw-label">Tonight's job</div>
      <div className="mn-display mhw-soonword mhw-fit">{(MH.time || "17:30")}</div>
      <div className="mhw-soonsub">first serve · {(N.teams || []).length} pairs signed in{sv.doublePoints ? " · every point counts double" : ""}</div>
    </div>
  );
}

function MhwChampions({ c, sv }) {
  return (
    <div className="mhw-champs">
      <div className="mhw-label" data-gold="">{sv.finale ? "The big score" : "Tonight's champions"}</div>
      <div className="mhw-champfaces">{c.team.players.map((p, i) => <MhwFace key={i} p={p} size="var(--chf)" ring="gold" />)}</div>
      <div className="mn-display mhw-champname mhw-fit">{mhwPair(c.team)}</div>
      <div className="mhw-champscore"><b>{c.score.replace("-", "–")}</b> in the final against {mhwPair(c.beat)}</div>
    </div>
  );
}

// the takeover the room sees the moment a score is locked
function MhwFlash({ r, N, sv }) {
  React.useLayoutEffect(mhwFit, []);
  const aw = r.m.winner === "a";
  const w = aw ? r.m.ta : r.m.tb, l = aw ? r.m.tb : r.m.ta;
  const sw = aw ? r.m.ga : r.m.gb, sl = aw ? r.m.gb : r.m.ga;
  const final = r.kind === "final";
  return (
    <div className="mhw-flash" data-final={final ? "" : undefined} role="status" aria-live="assertive">
      <div className="mhw-flashbg" aria-hidden="true" />
      <div className="mhw-shards" aria-hidden="true">{Array.from({ length: 18 }, (_, i) => <i key={i} style={{ "--a": (i * 20) + "deg", "--d": (i % 3) * .08 + "s" }} />)}</div>
      <div className="mhw-fkick">{final ? (sv.finale ? "The big score" : "Champions") : "Result · " + r.label}</div>
      <div className="mhw-fwin"><MhwPairFaces t={w} size={final ? 19 : 15} ring="gold" /></div>
      <div className="mn-display mhw-fname mhw-fit">{mhwPair(w)}</div>
      <div className="mhw-fscore mn-display">{sw}<span>–</span>{sl}</div>
      {r.what && <div className="mhw-fwhat">{r.what}</div>}
      <div className="mhw-flose"><MhwPairFaces t={l} size={5} dim /><span>{final ? "runners-up · " : "beat "}{mhwPair(l)}</span></div>
      {sv.doublePoints && <div className="mhw-f2x">2X night · points count double</div>}
    </div>
  );
}
