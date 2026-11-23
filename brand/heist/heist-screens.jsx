// MUSCAT HEIST · Vol.10 — the season screens (handoff phase 2):
// 01 Home · 02 Jobs · 03 Most Wanted · 04 ME · 05 The Crew · 06 Crew Card ·
// 17 The Take. Every value is the static design's own (handoff/design/
// Muscat Nights App.html); every colour is a token. They read ONE shape of
// data, D, built by brand/heist/preview-data.js in preview and by the app's
// adapter from the live state — so a screen cannot be right in preview and
// wrong on the night.

// ── dates, without the UTC trap ──────────────────────────────────────────
// A plain "2026-12-23" is parsed by its parts. new Date("2026-12-23") is UTC
// midnight, which on this server and on every phone in Oman is 4am — fine —
// but the repo's rule is never to rely on it (CLAUDE.md, dates on UTC+4).
const MH_DOW = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
const MH_MON = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
function mhDate(s) { const [y, m, d] = s.split("-").map(Number); return new Date(y, m - 1, d); }
function mhDay(s) { const d = mhDate(s); return `${MH_DOW[d.getDay()]} ${d.getDate()} ${MH_MON[d.getMonth()]}`; }
function mhStart(s, time) { const d = mhDate(s); const [h, m] = (time || "17:30").split(":").map(Number); d.setHours(h, m, 0, 0); return d; }
function mhCountdown(to, now) {
  const ms = to - now; if (ms <= 0) return null;
  const m = Math.floor(ms / 60000), d = Math.floor(m / 1440), h = Math.floor((m % 1440) / 60);
  return d > 0 ? `${d}D ${h}H` : `${h}H ${m % 60}M`;
}
const mhFirst = n => (n || "").split(" ")[0];
const mhPts = n => `${n} pt${n === 1 ? "" : "s"}`;

// ── what every screen derives from D ─────────────────────────────────────
function mhDerive(D) {
  const nightsPlayed = D.sessions.filter(s => s.state === "done").length;
  const players = D.players.map(p => {
    const rep = p.repId ? MH_REPS.find(r => r.id === p.repId) : mhRepAt(p.points, Math.max(1, nightsPlayed));
    return Object.assign({}, p, { rep, tier: mhTierFor(p.rank) });
  });
  const byId = Object.fromEntries(players.map(p => [p.id, p]));
  const above = p => players.find(q => q.rank === p.rank - 1);
  const me = byId[D.meId] || null;
  const lastDone = D.sessions.filter(s => s.state === "done").slice(-1)[0];
  return { players, byId, above, me, nightsPlayed, lastDone,
    gap: p => { const a = above(p); return a ? a.points - p.points : null; } };
}

// ── page shell: top bar, scrolling content, nav ──────────────────────────
function MhPage({ D, tab, onTab, children, nav = true, pad = "96px 20px 0" }) {
  return (
    <div className="mh-page">
      <MhTopBar logo={D.logo || "up-logo-tight.png"} line={`${MH.volumeLabel.replace("VOL", "Vol")} · ${MH.month}`} onLogo={D.onLogo} />
      {D.organiser && <button type="button" className="mh-orgchip" onClick={D.organiser}>Organiser</button>}
      <main className="mh-body" style={{ padding: pad }}>{children}</main>
      {nav && <MhBottomNav tab={tab} onTab={onTab} />}
      <MhGrain />
    </div>
  );
}
const MhTitle = ({ title, aside }) => (
  <div className="mh-title">
    <h1 className="mn-display">{title}</h1>
    {aside && <div className="mn-serif">{aside}</div>}
  </div>
);

// ── 01 HOME ──────────────────────────────────────────────────────────────
function MhHome({ D, go }) {
  const X = mhDerive(D);
  // the countdown moves every minute (spec); D.now pins it in preview only
  const [tick, setTick] = React.useState(0);
  React.useEffect(() => { if (D.now) return; const t = setInterval(() => setTick(x => x + 1), 60000); return () => clearInterval(t); }, [D.now]);
  const now = D.now ? new Date(D.now) : new Date();
  const live = D.sessions.find(s => s.state === "live");
  const next = D.sessions.find(s => s.no === D.homeNext) || D.sessions.find(s => s.state === "soon");
  const showLive = live && D.homeShowsLive;
  const hero = showLive ? live : (next || X.lastDone);
  const lead = X.players[0], second = X.players[1];
  const me = X.me, rival = me && X.above(me);
  const left = next && mhCountdown(mhStart(next.date, next.time), now);
  return (
    <MhPage D={D} tab="home" onTab={go} pad="0">
      <MhHeroCut height={470} src={hero && hero.art} pos={hero && hero.heroPos || "34% 20%"}
        scenes={D.scenes} sceneStart={mhSceneIndex(D, "home")} every={6000}>
        <div style={{ position: "absolute", left: 22, top: 250 }}><MhTitleLockup size="S" /></div>
      </MhHeroCut>
      <div className="mh-col" style={{ padding: "0 20px", marginTop: -8, gap: 10 }}>
        {showLive ? (
          <button type="button" className="mn-glass mh-tap" data-accent="coral" onClick={() => go("session", live.no)}>
            <div className="mh-split">
              <div>
                <MhLabel tone="coral">● Live now · {live.code}</MhLabel>
                <MhDisplay size={28} style={{ marginTop: 3 }}>{live.title}</MhDisplay>
                {live.progress && <MhSerif>{live.progress.played} of {live.progress.total} matches played</MhSerif>}
              </div>
              <MhDisplay size={18} tone="coral">OPEN ›</MhDisplay>
            </div>
          </button>
        ) : next ? (
          <button type="button" className="mn-glass mh-tap" onClick={() => go("session", next.no)}>
            <div className="mh-split">
              <div>
                <MhLabel tone="peach">Next job · {next.code}</MhLabel>
                <MhDisplay size={28} style={{ marginTop: 3 }}>{mhDay(next.date).toUpperCase()}</MhDisplay>
                <MhSerif>{next.time} · {MH.venue}</MhSerif>
              </div>
              {left && <div style={{ textAlign: "right" }}>
                <MhDisplay size={28} tone="peach">{left}</MhDisplay>
                <MhLabel>to go</MhLabel>
              </div>}
            </div>
          </button>
        ) : null}
        {typeof MhHomeClips === "function" && <MhHomeClips D={D} go={go} />}
        {D.preseason ? (
          <MhGlass>
            <MhLabel tone="peach">The table</MhLabel>
            <MhDisplay size={22} style={{ marginTop: 3, lineHeight: 1.05 }}>Opens after {(D.sessions[0] || {}).code || "EP.01"}</MhDisplay>
            <MhSerif size={14}>Everyone starts on zero on {D.sessions[0] ? mhDay(D.sessions[0].date) : "night one"}. Your rival is whoever finishes just above you.</MhSerif>
          </MhGlass>
        ) : <div className="mh-two">
          {lead && <button type="button" className="mn-glass mh-tap mh-small" onClick={() => go("wanted")}>
            <MhLabel tone="peach">Leader</MhLabel>
            <MhDisplay size={19} weight={800} style={{ marginTop: 3, lineHeight: 1.05 }}>{mhFirst(lead.name)} · {lead.points}</MhDisplay>
            <MhSerif size={14}>{second ? `${lead.points - second.points} clear` : "on top"}</MhSerif>
          </button>}
          {me && (rival ? (
            <button type="button" className="mn-glass mh-tap mh-small" onClick={() => go("rival")}>
              <MhLabel tone="teal">Your rival</MhLabel>
              <MhDisplay size={19} weight={800} style={{ marginTop: 3, lineHeight: 1.05 }}>{mhFirst(rival.name)} · {rival.points}</MhDisplay>
              <MhSerif size={14}>{mhPts(rival.points - me.points)} ahead</MhSerif>
            </button>
          ) : second && (
            <button type="button" className="mn-glass mh-tap mh-small" onClick={() => go("rival")}>
              <MhLabel tone="teal">#2 chasing</MhLabel>
              <MhDisplay size={19} weight={800} style={{ marginTop: 3, lineHeight: 1.05 }}>{mhFirst(second.name)} · {second.points}</MhDisplay>
              <MhSerif size={14}>{mhPts(me.points - second.points)} behind you</MhSerif>
            </button>
          ))}
        </div>}
      </div>
    </MhPage>
  );
}

// ── 02 JOBS ──────────────────────────────────────────────────────────────
function MhJobs({ D, go }) {
  const [f, setF] = React.useState("upcoming");
  const rows = D.sessions.filter(s => f === "all" || (f === "done" ? s.state === "done" : s.state !== "done"));
  const ordered = f === "done" ? rows.slice().reverse() : f === "all" ? rows
    : rows.concat(D.sessions.filter(s => s.state === "done").slice(-1));   // the reference trails the latest recap
  const upcoming = D.sessions.some(s => s.state !== "done");
  return (
    <MhPage D={D} tab="jobs" onTab={go}>
      <div className="mh-col">
        <MhTitle title="JOBS" aside={`${MH.month} · ${D.sessions.length} episodes`} />
        <MhPills label="Filter" items={[["upcoming", "Upcoming"], ["done", "Done"], ["all", "All"]]} value={f} onChange={setF} />
        {!upcoming && f === "upcoming" && (
          <button type="button" className="mn-glass mh-tap" onClick={() => go("take")}>
            <MhDisplay size={19}>Season complete</MhDisplay><MhSerif size={14}>See The Take ›</MhSerif>
          </button>
        )}
        {ordered.map(s => <MhJobRow key={s.no} s={s} go={go} />)}
      </div>
    </MhPage>
  );
}
function MhJobRow({ s, go }) {
  const live = s.state === "live", done = s.state === "done", signup = s.signups && s.signups.open;
  const day = mhDay(s.date);
  const label = live ? `● Live now · ${day}` : done ? day : `${day} · ${s.time}`;
  const tone = live ? "coral" : done ? "dim" : s.finale ? "gold" : signup ? "peach" : "mist";
  const sub = live && s.progress ? `${s.progress.played} of ${s.progress.total} matches played`
    : done ? `${(s.champions || []).map(mhFirst).join(" & ")} won · recap ›`
    : s.finale ? `Finale · 2× points`
    : signup ? `Signups open · ${s.signups.teams} of ${s.signups.max} teams`
    : s.signups && s.signups.opensOn ? `Signups open ${s.signups.opensOn}` : (s.doublePoints ? "2× points" : "");
  return (
    <div className="mh-job" data-state={live ? "live" : s.finale ? "finale" : done ? "done" : "soon"}>
      <button type="button" className="mh-jobmain" onClick={() => go(done ? "recap" : "session", s.no)}
        aria-label={`${s.code} ${s.title}`}>
        <div className="mh-thumb"><MhArt src={s.art} pos={s.artPos} sizes="96px" /></div>
        <div style={{ minWidth: 0 }}>
          <MhLabel tone={tone}>{label}</MhLabel>
          <div className="mn-display mh-jobtitle">{s.code} · {s.title}</div>
          {sub && <MhSerif size={14}>{sub}</MhSerif>}
        </div>
      </button>
      {live ? <MhDisplay size={15} tone="coral" style={{ alignSelf: "center" }}>OPEN ›</MhDisplay>
        : s.finale && !done ? <MhDisplay size={15} tone="gold" style={{ alignSelf: "center" }}>FINALE</MhDisplay>
        : signup ? <button type="button" className="mn-pill" aria-pressed="true" onClick={() => go("signup", s.no)}><span>Sign up</span></button>
        : null}
    </div>
  );
}

// ── 03 MOST WANTED ───────────────────────────────────────────────────────
function MhWanted({ D, go }) {
  const X = mhDerive(D);
  const lead = X.players[0];
  const bounty = r => (MH.seasonPrizes || [])[r - 1];
  return (
    <MhPage D={D} tab="wanted" onTab={go}>
      <div className="mh-col">
        <MhTitle title="MOST WANTED" aside={X.lastDone ? `after ${X.lastDone.code}` : "before EP.01"} />
        {D.preseason && (
          <MhGlass>
            <MhDisplay size={22} style={{ lineHeight: 1.05 }}>Nobody's wanted yet</MhDisplay>
            <MhSerif size={14}>The table fills in as {(D.sessions[0] || {}).code || "EP.01"} is played on {D.sessions[0] ? mhDay(D.sessions[0].date) : "night one"}. Last season's crew is on the Crew tab.</MhSerif>
          </MhGlass>
        )}
        {lead && !D.preseason && (
          <button type="button" className="mh-leader mh-tap" onClick={() => go("card", lead.id)}>
            <MhArt src={lead.photo} pos={lead.pos} name={lead.name} />
            <div className="mh-leaderfade" aria-hidden="true" />
            <div className="mh-stars" aria-hidden="true">★★★★★</div>
            <div className="mh-leaderbody">
              <MhLabel tone="gold">Most wanted · Rep {lead.rep.label}</MhLabel>
              <div className="mn-display" style={{ fontSize: 36, lineHeight: .86 }}>
                {lead.name.split(" ").map((w, i) => <React.Fragment key={i}>{i ? <br /> : null}{w}</React.Fragment>)}
              </div>
              <div className="mh-mono-row">
                <span>{lead.points} PTS</span>
                {bounty(1) && <span style={{ color: "var(--mn-peach)" }}>BOUNTY {bounty(1)} OMR</span>}
              </div>
            </div>
          </button>
        )}
        <div className="mh-replegend">
          {MH_REPS.slice().reverse().map(r => (
            <div key={r.id} style={{ borderTopColor: `var(--mn-rep-${r.id})` }}>
              <b>{r.label.toUpperCase()}</b><span>{r.perNight * Math.max(1, X.nightsPlayed)}+</span>
            </div>
          ))}
        </div>
        {X.players.length >= 2 && !D.preseason && (
          <div>
            {X.players.slice(1).map(p => {
              const g = X.gap(p), mine = X.me && p.id === X.me.id;
              const ring = p.rep.id === "rookie" ? null : `rep-${p.rep.id}`;
              return (
                <button type="button" key={p.id} className="mh-wrow mh-tap" data-me={mine ? "" : undefined}
                  onClick={() => go("card", p.id)}>
                  <div className="mn-display mh-wrank">{p.rank}</div>
                  <MhAvatar player={{ name: p.name, photo: p.photo, photoPos: p.avPos || p.pos }} size={34} ring={ring} zoom={p.zoom} />
                  <div style={{ minWidth: 0, textAlign: "left" }}>
                    <div className="mh-wname">{p.name}{mine && <span className="mn-serif"> you</span>}</div>
                    <MhLabel style={{ color: `var(--mn-rep-${p.rep.id})` }}>Rep · {p.rep.label.toUpperCase()}</MhLabel>
                  </div>
                  <div className="mh-wmove">{p.movement || "—"}</div>
                  <div style={{ textAlign: "right" }}>
                    <div className="mn-display" style={{ fontSize: 20, fontWeight: 800, lineHeight: 1 }}>{p.points}</div>
                    <div className="mh-wgap">{g === 0 ? "level" : `−${g}`}</div>
                  </div>
                </button>
              );
            })}
          </div>
        )}
      </div>
    </MhPage>
  );
}

// ── 04 ME ────────────────────────────────────────────────────────────────
const MH_SEG = [["groupWins", "Group wins", "var(--mn-teal)"], ["lossPts", "Loss points", "var(--mn-teal-45)", "var(--mn-teal-60)"],
                ["knockout", "Knockout", "var(--mn-coral)"], ["titles", "Titles", "var(--mn-sand)"],
                // comeback, streak and the 2X extra: the engine pays them and the design's four
                // segments have no room for them, so without this the bar would not add up to the total
                ["bonus", "Bonuses & 2X", "var(--mn-gold)"]];
function MhMe({ D, go }) {
  const X = mhDerive(D);
  const me = X.me;
  if (!me || !me.points) {
    return (
      <MhPage D={D} tab="me" onTab={go}>
        <div className="mh-col">
          <MhTitle title="ME" />
          {!D.meId && D.pickMe ? <MhGlass><MhDisplay size={22}>Who are you?</MhDisplay>
            <MhSerif size={14}>Pick yourself once and this phone shows your card, your rival and every point you earn.</MhSerif>
            <MhButton style={{ marginTop: 10, width: "100%" }} onClick={D.pickMe}>Pick yourself</MhButton></MhGlass>
          : <MhGlass><MhDisplay size={22}>Play your first night</MhDisplay>
            <MhSerif size={14}>Your card, your rival and every point you earn show up here.</MhSerif></MhGlass>}
        </div>
      </MhPage>
    );
  }
  const rival = X.above(me), next = mhNextRep(me.rep), n = Math.max(1, X.nightsPlayed);
  const lo = me.rep.perNight * n, hi = next ? next.perNight * n : lo;
  const frac = next ? Math.max(0, Math.min(1, (me.points - lo) / Math.max(1, hi - lo))) : 1;
  const seg = (D.me && D.me.seg) || {};
  const segTotal = MH_SEG.reduce((a, [k]) => a + (seg[k] || 0), 0);
  return (
    <MhPage D={D} tab="me" onTab={go}>
      <div className="mh-col">
        <div style={{ display: "flex", gap: 14, alignItems: "center" }}>
          <MhCrewCard player={{ name: me.name, photo: me.photo, photoPos: me.meCardPos || me.pos }} rank={me.rank}
            points={me.points} rep={me.rep} size="S" foil={false} onClick={() => go("card", me.id)} />
          <div style={{ flex: 1, display: "flex", flexDirection: "column", gap: 6 }}>
            <MhLabel>Your season</MhLabel>
            <MhDisplay size={56} style={{ lineHeight: .85 }}>{me.points}</MhDisplay>
            <div style={{ display: "flex", gap: 6 }}>
              <span className="mh-chip" data-tone={me.rep.id}>#{me.rank}</span>
              <span className="mh-chip" data-tone={me.rep.id}>REP {me.rep.label.toUpperCase()}</span>
            </div>
            {next ? <>
              <div className="mh-progress"><div className="mn-fill" style={{ width: (frac * 100).toFixed(1) + "%" }} /></div>
              <MhLabel>{mhPts(hi - me.points)} to {next.label}</MhLabel>
            </> : <MhLabel tone="gold">Top rep reached</MhLabel>}
          </div>
        </div>
        {rival && (
          <button type="button" className="mn-glass mh-tap" onClick={() => go("rival")}>
            <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
              <MhAvatar player={{ name: rival.name, photo: rival.photo, photoPos: rival.avPos || rival.pos }} size={42} ring="coral" zoom={rival.zoom} />
              <div style={{ flex: 1, textAlign: "left" }}>
                <MhLabel tone="coral">Your rival · #{rival.rank}</MhLabel>
                <MhDisplay size={20}>{mhFirst(rival.name)} · {rival.points}</MhDisplay>
                {D.rival && D.rival.h2h && <MhSerif size={14}>Head to head {D.rival.h2h.w}–{D.rival.h2h.l}</MhSerif>}
              </div>
              <div style={{ textAlign: "right" }}>
                <MhDisplay size={26} tone="peach">{rival.points - me.points}</MhDisplay>
                <MhLabel>pts</MhLabel>
              </div>
            </div>
          </button>
        )}
        {segTotal > 0 && <>
          <MhLabel>Where the points came from</MhLabel>
          <div className="mh-stack" role="img" aria-label={MH_SEG.map(([k, l]) => `${l} ${seg[k] || 0}`).join(", ")}>
            {MH_SEG.map(([k, , c]) => (seg[k] ? <div key={k} style={{ flex: seg[k], background: c }} /> : null))}
          </div>
          <div className="mh-legend">
            {MH_SEG.filter(([k]) => k !== "bonus" || seg[k]).map(([k, l, c, sw]) => (
              <div key={k}><span><span style={{ color: sw || c }}>■</span> {l}</span><b>{seg[k] || 0}</b></div>
            ))}
          </div>
        </>}
        {D.me && D.me.episodes && D.me.episodes.length > 0 && <>
          <MhLabel>Episode by episode</MhLabel>
          <div>
            {D.me.episodes.map(e => (
              <button type="button" key={e.session} className="mh-eprow mh-tap" onClick={() => go("receipt", e.session)}>
                <MhDisplay size={16} tone="mist">{D.sessions[e.session - 1].code}</MhDisplay>
                <span>{e.label}</span>
                <MhDisplay size={17} tone={e.title ? "gold" : e.knockout ? "teal" : undefined}>+{e.pts}</MhDisplay>
              </button>
            ))}
          </div>
        </>}
      </div>
    </MhPage>
  );
}

// ── 05 THE CREW ──────────────────────────────────────────────────────────
function MhCrew({ D, go }) {
  const X = mhDerive(D);
  const [t, setT] = React.useState("all");
  const tiers = [["all", "All"]].concat((MH.tiers || []).map(x => [x.id, x.label[0] + x.label.slice(1).toLowerCase()]));
  const shown = X.players.filter(p => t === "all" || p.tier.id === t);
  return (
    <MhPage D={D} tab="crew" onTab={go}>
      <div className="mh-col">
        <MhTitle title="THE CREW" aside={`${D.rosterSize || X.players.length} players`} />
        <MhPills label="Tier" items={tiers} value={t} onChange={setT} />
        <div className="mh-grid">
          {shown.map(p => (
            <MhCrewCard key={p.id} player={{ name: p.name, photo: p.photo, photoPos: p.pos }} rank={p.rank}
              points={p.points} rep={p.rep} size="M" onClick={() => go("card", p.id)} />
          ))}
        </div>
      </div>
    </MhPage>
  );
}

// ── 06 CREW CARD ─────────────────────────────────────────────────────────
function MhCardScreen({ D, go, id }) {
  const X = mhDerive(D);
  const p = X.byId[id] || X.players[0];
  const own = X.me && p.id === X.me.id;
  // the app works you-v-them out for whichever card is open; the preview carries one fixed pair
  const v = D.vsFor ? D.vsFor(p.id) : D.vsCard && D.vsCard.playerId === p.id ? D.vsCard : null;
  return (
    <MhPage D={D} tab="crew" onTab={go} nav={false} pad="92px 20px 0">
      <div className="mh-col">
        <div className="mh-split">
          <MhLabel>Crew card</MhLabel>
          <button type="button" className="mh-close mn-serif" onClick={() => go("back")}>close ✕</button>
        </div>
        <div style={{ display: "flex", justifyContent: "center" }}>
          <MhCrewCard player={{ name: p.name, photo: p.photo, photoPos: p.pos }} rank={p.rank} points={p.points}
            rep={p.rep} size="L" stats={p.stats || {}} />
        </div>
        {/* the handoff's "Share (optional) → share sheet MY CARD", on your own card only */}
        {own && <MhButton live onClick={() => go("share", "card/" + p.id)}>Share my card</MhButton>}
        {!own && v && (
          <MhGlass>
            <div className="mh-split">
              <div>
                <MhLabel tone="coral">You vs him</MhLabel>
                <MhSerif size={14}>{v.meetings} meeting{v.meetings === 1 ? "" : "s"} · last {D.sessions[v.last.session - 1].code}, {v.last.won ? "won" : "lost"} {v.last.score}</MhSerif>
              </div>
              <MhDisplay size={28}>{v.w}–{v.l}</MhDisplay>
            </div>
          </MhGlass>
        )}
      </div>
    </MhPage>
  );
}

// ── 17 THE TAKE ──────────────────────────────────────────────────────────
function MhTake({ D, go }) {
  const X = mhDerive(D);
  const pool = (MH.seasonPrizes || []).reduce((a, b) => a + b, 0) + MH.voucher * 2 * D.sessions.length;
  const paid = D.paidOMR != null ? D.paidOMR : X.nightsPlayed * MH.voucher * 2;
  const left = pool - paid;
  const place = [["1ST", "gold"], ["2ND", "silver"], ["3RD", "bronze"]];
  return (
    <MhPage D={D} tab="me" onTab={go}>
      <div className="mh-col">
        <MhTitle title="THE TAKE" />
        <div className="mh-takehero">
          <MhArt src={mhScene(D, "take").src || D.sessions[D.sessions.length - 1].art} pos={mhScene(D, "take").pos || "center 50%"} />
          <div className="mh-takebody">
            <MhLabel tone="peach">Prize pool</MhLabel>
            <MhDisplay size={52} style={{ lineHeight: .9 }}>{pool} OMR</MhDisplay>
            <div style={{ display: "flex", gap: 14 }}><MhLabel tone="teal">{paid} paid</MhLabel><MhLabel tone="gold">{left} left</MhLabel></div>
          </div>
        </div>
        <div className="mh-col" style={{ gap: 6 }}>
          <div className="mh-split"><MhLabel tone="teal">Won so far</MhLabel><MhLabel>{X.nightsPlayed} of {D.sessions.length} nights</MhLabel></div>
          <div className="mh-meter"><div className="mn-fill" style={{ width: (paid / pool * 100).toFixed(1) + "%" }} /></div>
          <div className="mh-segs" style={{ gridTemplateColumns: `repeat(${D.sessions.length},minmax(0,1fr))` }}>
            {D.sessions.map(s => <div key={s.no} data-s={s.state === "done" ? "done" : s.finale ? "finale" : "rest"} />)}
          </div>
          <div className="mh-split mn-serif" style={{ fontSize: 13 }}><span>{paid} OMR in vouchers paid</span><span>{left} OMR still to win</span></div>
        </div>
        <MhLabel>If the season ended now</MhLabel>
        {X.players.slice(0, 3).map((p, i) => (
          <button type="button" key={p.id} className="mn-glass mh-tap mh-prize" onClick={() => go("card", p.id)}>
            <MhDisplay size={20} tone={place[i][1]} style={{ width: 36 }}>{place[i][0]}</MhDisplay>
            <MhAvatar player={{ name: p.name, photo: p.photo, photoPos: p.avPos || p.pos }} size={38} ring={place[i][1]} zoom={p.zoom} />
            <div className="mn-display" style={{ flex: 1, fontSize: 17, textAlign: "left" }}>{p.name.toUpperCase()}
              <div className="mh-ptsline">{p.points} PTS</div></div>
            <MhDisplay size={24}>{MH.seasonPrizes[i]}<span className="mh-omr"> OMR</span></MhDisplay>
          </button>
        ))}
        <MhLabel>Nightly · {MH.voucher * 2} OMR to each episode's champions</MhLabel>
      </div>
    </MhPage>
  );
}
