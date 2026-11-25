// MUSCAT HEIST · Vol.10 — a NIGHT's posts: line-up, the draw, group tables,
// the bracket, champions and tonight's points, as 1080x1920 stories.
//
// These replace the inherited canvas painters behind POSTS and LINE-UP, which
// were Vol.9's compositions re-coloured. They are DOM, built from the same
// glass, display type and faces as the screens, and they go out through the
// same export as the campaign poster (mhExportStory): the frame on screen is
// the file that is posted. Every name and number is the night data the
// session screen shows — the engine's standings, its qualifying set, its
// per-night points — so a post cannot disagree with the app.

const MH_NIGHT_KINDS = [["lineup", "Line-up"], ["draw", "The draw"], ["tables", "Tables"],
  ["bracket", "Bracket"], ["champions", "Champions"], ["points", "Tonight"]];
const MH_ROUND_NAME = { qf: "Quarter-final", sf: "Semi-final", final: "The final" };

// the chrome every night story shares: art at the top fading to navy, the club
// mark and the episode, a kicker and a headline, the venue line at the foot
function MhNightFrame({ D, s, kicker, title, art = 300, children, label }) {
  return (
    <MhStoryFrame label={label || `${MH.name} · ${s.code} · ${title}`}>
      <div className="mh-nsart" style={{ height: art }}><MhArt src={s.art} pos={s.artPos || "center 30%"} /></div>
      <div className="mh-nsfade" style={{ height: art }} aria-hidden="true" />
      <div className="mh-nstop">
        <img src={D.logo || "up-logo-tight.png"} alt="Urban Playground" style={{ height: 24 }} />
        <span className="mn-label" style={{ color: "var(--mn-sand)" }}>{MH.name} · {s.code}</span>
      </div>
      <div className="mh-nshead">
        <div className="mn-label" style={{ color: "var(--mn-peach)" }}>{kicker}</div>
        <div className="mn-display mh-nstitle">{title}</div>
      </div>
      <div className="mh-nsbody">{children}</div>
      <div className="mh-nsfoot">
        <span>{mhDay(s.date)} · {MH.venue}</span>
        <span>{(MH.stories || {}).url || MH.host}</span>
      </div>
    </MhStoryFrame>
  );
}
const mhPairName = t => t ? t.players.map(p => p.first).join(" & ") : "TBD";
function MhNPair({ t, size = 22, stacked }) {
  return (
    <div className="mh-npair">
      <div className="mh-pairfaces mh-pairfaces-s">{t && t.players.map(p => <MhAvatar key={p.id} player={p} size={size} />)}</div>
      {stacked && t
        ? <div className="mh-nnames"><div>{t.players[0].first}</div><div>{t.players[1].first}</div></div>
        : <div className="mh-nname">{mhPairName(t)}</div>}
    </div>
  );
}

// ── THE DRAW ──────────────────────────────────────────────────────────────
function MhNightDraw({ D, s, N }) {
  const gs = Object.keys(N.groups || {});
  return (
    <MhNightFrame D={D} s={s} kicker={`${s.title} · ${(N.teams || []).length} teams`} title="The draw">
      <div className="mh-ngrid" data-n={gs.length}>
        {gs.map(g => (
          <div key={g} className="mh-npanel">
            <div className="mh-npanelhead"><span className="mh-nletter">{g}</span>Group {g}</div>
            {N.groups[g].standings.slice().sort((a, b) => a.team.localeCompare(b.team)).map(r => <MhNPair key={r.id} t={r} stacked />)}
          </div>
        ))}
      </div>
    </MhNightFrame>
  );
}

// ── GROUP TABLES ──────────────────────────────────────────────────────────
function MhNightTables({ D, s, N }) {
  const gs = Object.keys(N.groups || {});
  const done = gs.every(g => N.groups[g].done);
  return (
    <MhNightFrame D={D} s={s} kicker={done ? "Groups complete" : "Group stage · live"} title="Group tables">
      <div className="mh-ngrid" data-n={gs.length}>
        {gs.map(g => (
          <div key={g} className="mh-npanel">
            <div className="mh-npanelhead"><span className="mh-nletter">{g}</span>Group {g}<span className="mh-nhcols">W&nbsp;&nbsp;Pts</span></div>
            {N.groups[g].standings.map(r => (
              <div key={r.id} className="mh-ntrow" data-q={N.started && r.q ? "" : undefined}>
                <span className="mh-npos">{r.pos}</span>
                <div className="mh-nnames"><div>{r.players[0].first}</div><div>{r.players[1].first}</div></div>
                <span className="mh-nw">{r.w}</span><b className="mn-display">{r.pts}</b>
              </div>
            ))}
          </div>
        ))}
      </div>
      {N.started && <div className="mh-nkey"><i /> {done ? "through to the knockout" : "in a qualifying place right now"}</div>}
    </MhNightFrame>
  );
}

// ── THE BRACKET ───────────────────────────────────────────────────────────
function MhNMini({ m, big }) {
  const row = (t, sd, g, win, lose) => (
    <div className="mh-nmrow" data-win={win ? "" : undefined} data-lose={lose ? "" : undefined}>
      {big && <div className="mh-pairfaces mh-pairfaces-s">{t && t.players.map(p => <MhAvatar key={p.id} player={p} size={26} />)}</div>}
      {sd && <span className="mh-nseed">{sd}</span>}
      <span className="mh-nname">{mhPairName(t)}</span>
      <b className="mn-display">{g == null ? "" : g}</b>
    </div>
  );
  return (
    <div className="mh-nmini" data-big={big ? "" : undefined}>
      {row(m.ta, m.sa, m.ga, m.winner === "a", m.winner === "b")}
      {row(m.tb, m.sb, m.gb, m.winner === "b", m.winner === "a")}
    </div>
  );
}
function MhNightBracket({ D, s, N }) {
  const K = N.knockout || {};
  return (
    <MhNightFrame D={D} s={s} kicker={N.champion ? "Knockout · decided" : "Knockout"} title="The bracket" art={260}>
      {(K.qf || []).length > 0 && <><div className="mh-nround">Quarter-finals</div>
        <div className="mh-ngrid" data-n="4" data-tight="">{K.qf.map((m, i) => <MhNMini key={i} m={m} />)}</div></>}
      {(K.sf || []).length > 0 && <><div className="mh-nround">Semi-finals</div>
        <div className="mh-ngrid" data-n="2" data-tight="">{K.sf.map((m, i) => <MhNMini key={i} m={m} />)}</div></>}
      {K.final && <><div className="mh-nround" style={{ color: "var(--mn-gold)" }}>The final</div><MhNMini m={K.final} big /></>}
      {N.champion && (
        <div className="mh-nchampline">
          <span className="mn-label" style={{ color: "var(--mn-gold)" }}>Champions</span>
          <b className="mn-display">{mhPairName(N.champion.team)}</b>
        </div>
      )}
    </MhNightFrame>
  );
}

// ── LINE-UP: one match, face to face ─────────────────────────────────────
function MhNightLineup({ D, s, m }) {
  if (!m) return null;
  const decided = !!m.winner;
  const side = (t, sd, k) => (
    <div className="mh-nside" data-win={m.winner === k ? "" : undefined} data-lose={decided && m.winner !== k ? "" : undefined}>
      <div className="mh-pairfaces mh-nfaces">{t && t.players.map(p => <MhAvatar key={p.id} player={p} size={118} ring={m.winner === k ? "gold" : undefined} />)}</div>
      <div className="mn-display mh-nsidename">{t ? t.players[0].first : "TBD"}<br />{t ? t.players[1].first : ""}</div>
      {sd && <div className="mn-label" style={{ color: "var(--mn-mist)" }}>{sd}</div>}
    </div>
  );
  const label = m.round ? `${MH_ROUND_NAME[m.round]}${m.round !== "final" ? " " + m.n : ""}` : `Group ${m.group} · match ${m.n}`;
  return (
    <MhStoryFrame label={`${MH.name} line-up: ${mhPairName(m.ta)} v ${mhPairName(m.tb)}`}>
      <div style={{ position: "absolute", inset: 0 }}><MhArt src={s.art} pos={s.artPos || "center 30%"} /></div>
      <div className="mh-nlufade" aria-hidden="true" />
      <div className="mh-nstop">
        <img src={D.logo || "up-logo-tight.png"} alt="Urban Playground" style={{ height: 24 }} />
        <span className="mn-label" style={{ color: "var(--mn-sand)" }}>{s.code} · {s.title}</span>
      </div>
      <div className="mh-nluhead">
        <MhSceneTag>{label}</MhSceneTag>
        {s.doublePoints && <span className="mh-n2x">2X</span>}
      </div>
      <div className="mh-nlu">
        {side(m.ta, m.sa, "a")}
        <div className="mh-nvs">{decided ? <><span>{m.ga}</span><i>–</i><span>{m.gb}</span></> : "VS"}</div>
        {side(m.tb, m.sb, "b")}
      </div>
      <div className="mh-nlufoot">
        {/* the owner's logo stands ~50% taller than the typeset lockup it replaced: at 64 it sat on the second pair's names */}
        <MhTitleLockup size={46} center meta={false} />
        <div className="mn-label" style={{ color: "var(--mn-sand)", marginTop: 6, textAlign: "center" }}>
          {decided ? (m.round === "final" ? "Champions crowned" : "Score settled") : `${mhDay(s.date)} · ${s.time} · ${MH.venue}`}</div>
      </div>
    </MhStoryFrame>
  );
}

// ── CHAMPIONS ────────────────────────────────────────────────────────────
function MhNightChampions({ D, s, N }) {
  const C = N.champion; if (!C) return null;
  const T = N.tonight ? N.tonight() : [];
  const ptsOf = id => (T.find(p => p.id === id) || {}).points;
  return (
    <MhStoryFrame label={`${MH.name} champions: ${mhPairName(C.team)}`}>
      <div style={{ position: "absolute", inset: 0 }}><MhArt src={s.art} pos={s.artPos || "center 30%"} /></div>
      <div className="mh-nchfade" aria-hidden="true" />
      <div className="mh-nstop">
        <img src={D.logo || "up-logo-tight.png"} alt="Urban Playground" style={{ height: 24 }} />
        <span className="mn-label" style={{ color: "var(--mn-sand)" }}>{s.code} · {s.title}</span>
      </div>
      <div className="mh-nchhead">
        <div className="mn-label" style={{ color: "var(--mn-gold)" }}>{mhDay(s.date)} · {MH.name}</div>
        <div className="mn-display mh-nchword">Champions</div>
      </div>
      <div className="mh-nchpics">
        {C.team.players.map(p => (
          <div key={p.id} className="mh-nchpic">
            <div className="mh-nchphoto"><MhArt src={p.photo} name={p.name} pos="center 22%" /></div>
            <div className="mn-display mh-nchname">{p.first}</div>
            {ptsOf(p.id) != null && <div className="mn-label" style={{ color: "var(--mn-peach)" }}>+{ptsOf(p.id)} pts tonight</div>}
          </div>
        ))}
      </div>
      <div className="mh-nchscore">
        <div className="mn-display" style={{ fontSize: 58, color: "var(--mn-gold)" }}>{C.score.replace("-", "–")}</div>
        <div className="mn-serif" style={{ fontSize: 16, color: "var(--mn-sand)" }}>in the final against {mhPairName(C.beat)}</div>
        <div className="mn-label" style={{ color: "var(--mn-sand)", marginTop: 10 }}>{MH.voucher} OMR voucher each</div>
      </div>
      <div className="mh-nsfoot"><span>{MH.venue}</span><span>{(MH.stories || {}).url || MH.host}</span></div>
    </MhStoryFrame>
  );
}

// ── TONIGHT'S POINTS ─────────────────────────────────────────────────────
function MhNightPoints({ D, s, N }) {
  const T = (N.tonight ? N.tonight() : []).slice(0, 8);
  return (
    <MhNightFrame D={D} s={s} kicker={`Points earned · ${s.doublePoints ? "2X night" : "tonight"}`} title="Tonight's take" art={240}>
      <div className="mh-npanel" style={{ padding: "4px 14px" }}>
        {T.map((p, i) => (
          <div key={p.id} className="mh-nprow">
            <span className="mh-npos" style={{ fontSize: 17 }}>{i > 0 && T[i - 1].points === p.points ? "" : i + 1}</span>
            <MhAvatar player={p} size={40} ring={i === 0 ? "gold" : undefined} />
            <div style={{ minWidth: 0, flex: 1 }}><div className="mh-nname" style={{ fontSize: 15 }}>{p.name}</div>{p.outcome && <div className="mh-nsub">{p.outcome}</div>}</div>
            <b className="mn-display">+{p.points}</b>
          </div>
        ))}
      </div>
      <div className="mh-nkey" style={{ justifyContent: "center" }}>streak bonus not included · it counts across the season</div>
    </MhNightFrame>
  );
}

// ── the sheet ────────────────────────────────────────────────────────────
// What can be posted is what the night has: a draw once there are teams, the
// tables and points once a ball is hit, the bracket once it is drawn, the
// champions once the final is won. Line-ups are the knockout's matches, or —
// before it — the group matches still to play.
function mhLineups(N) {
  const K = N.knockout;
  const ko = K ? [...(K.qf || []), ...(K.sf || []), ...(K.final ? [K.final] : [])].filter(m => m && m.ta && m.tb) : [];
  if (ko.length) return ko;
  return Object.entries(N.groups || {}).flatMap(([g, G]) => G.matches.map(m => ({ ...m, group: g }))).filter(m => m.ta && m.tb);
}
function MhNightShare({ D, go, no, kind }) {
  const s = D.sessions.find(x => x.no === +no) || D.sessions[0];
  const N = (D.nights && D.nights[s.no]) || {};
  const L = mhLineups(N);
  const has = { lineup: L.length > 0, draw: (N.teams || []).length > 0, tables: !!N.started, bracket: !!N.knockout,
    champions: !!N.champion, points: !!N.started && N.tonight && N.tonight().length > 0 };
  const kinds = MH_NIGHT_KINDS.filter(([k]) => has[k]);
  const [k, setK] = React.useState(has[kind] ? kind : (kinds[0] || [])[0]);
  // the first undecided match is the one about to be played
  const [li, setLi] = React.useState(() => Math.max(0, L.findIndex(m => !m.winner)));
  const [busy, setBusy] = React.useState(false), [err, setErr] = React.useState("");
  const ref = React.useRef(null);
  const m = L[Math.min(li, L.length - 1)];
  const run = async () => {
    setBusy(true); setErr("");
    try {
      const blob = await mhExportStory(ref.current.firstChild);
      const tag = k === "lineup" && m ? (m.round ? m.round + (m.round !== "final" ? m.n : "") : `g${m.group}${m.n}`) : k;
      const file = new File([blob], `muscat-heist-${s.code.replace(/\W/g, "").toLowerCase()}-${tag}.png`, { type: "image/png" });
      window.__mhLastExport = blob;                       // for the harness
      if (navigator.canShare && navigator.canShare({ files: [file] })) await navigator.share({ files: [file] });
      else { const a = document.createElement("a"); a.href = URL.createObjectURL(blob); a.download = file.name; a.click(); }
    } catch (e) { if (e && e.name !== "AbortError") setErr("Couldn't make the image. Try again."); }
    setBusy(false);
  };
  const body = !k ? null : k === "lineup" ? <MhNightLineup D={D} s={s} m={m} /> : k === "draw" ? <MhNightDraw D={D} s={s} N={N} />
    : k === "tables" ? <MhNightTables D={D} s={s} N={N} /> : k === "bracket" ? <MhNightBracket D={D} s={s} N={N} />
    : k === "champions" ? <MhNightChampions D={D} s={s} N={N} /> : <MhNightPoints D={D} s={s} N={N} />;
  return (
    <div className="mh-page">
      <main className="mh-body" data-bare="" style={{ padding: "56px 20px 0", display: "flex", flexDirection: "column", minHeight: "100dvh" }}>
        <div className="mh-split">
          <MhLabel>{s.code} · posts</MhLabel>
          <button type="button" className="mh-close mn-serif" onClick={() => go("session", s.no)}>close ✕</button>
        </div>
        {kinds.length ? <>
          <div style={{ marginTop: 10 }}><MhPills label="What to post" items={kinds} value={k} onChange={setK} /></div>
          {k === "lineup" && L.length > 1 && (
            <div className="mh-lupick">
              <button type="button" className="mh-act" aria-label="Previous match" disabled={li <= 0} onClick={() => setLi(i => Math.max(0, i - 1))}>‹</button>
              <select className="mh-luselect" value={li} onChange={e => setLi(+e.target.value)} aria-label="Match">
                {L.map((x, i) => <option key={i} value={i}>
                  {(x.round ? `${MH_ROUND_NAME[x.round]}${x.round !== "final" ? " " + x.n : ""}` : `Group ${x.group} · ${x.n}`)} — {mhPairName(x.ta)} v {mhPairName(x.tb)}{x.winner ? " ✓" : ""}
                </option>)}
              </select>
              <button type="button" className="mh-act" aria-label="Next match" disabled={li >= L.length - 1} onClick={() => setLi(i => Math.min(L.length - 1, i + 1))}>›</button>
            </div>
          )}
          <div className="mh-sharepreview"><div ref={ref} className="mh-sharescale">{body}</div></div>
          <MhLabel style={{ textAlign: "center" }}>1080 × 1920 · Instagram story</MhLabel>
          {err && <MhSerif size={14} tone="coral" style={{ textAlign: "center" }}>{err}</MhSerif>}
          <div className="mh-momentfoot" style={{ padding: "12px 0 26px" }}>
            <MhButton live onClick={run} disabled={busy}>{busy ? "Making the image…" : "Share image"}</MhButton>
          </div>
        </> : <MhGlass style={{ marginTop: 14 }}><MhSerif size={15}>Nothing to post yet — the draw is made on the night.</MhSerif></MhGlass>}
      </main>
    </div>
  );
}
