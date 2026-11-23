// MUSCAT HEIST · Vol.10 — the moments (handoff phase 4):
// 11 Now Loading Muscat · 12 New Crew Card · 13 Rep Up · 14 Your Rival ·
// 15 Score Settled · 16 The Big Score. Values are the static design's own.
//
// Every figure is DERIVED, never copied out of the fixture's prose: the gap
// to your rival is the difference in points, "10 to Known" is the next rep's
// per-night threshold times the nights played, the next rival after Score
// Settled is recomputed from the table with the locked result applied, and
// the leader's lead is #1 minus #2. Boss Kill +3 is not scored anywhere and
// its rule row only shows while bossKillBonus.enabled (handoff rule 11).

// a moment's player rows, in the shape the screens read
const mhRepById = id => MH_REPS.find(r => r.id === id) || MH_REPS[MH_REPS.length - 1];
const mhTierById = id => (MH.tiers || []).find(t => t.id === id);
const mhTierIdx = id => (MH.tiers || []).findIndex(t => t.id === id);

// The full-screen backdrop the moments share: the player's art, blurred and
// darkened, under a radial glow in the moment's own colour.
function MhMomentBack({ src, pos, dim = .6, glow, at = "50% 45%", strength = 35, fadeTo = 70, fadeAt = 60 }) {
  return (
    <>
      <div className="mh-mback" aria-hidden="true" style={{ "--mh-dim": dim }}><MhArt src={src} pos={pos} /></div>
      <div className="mh-mglow" aria-hidden="true" style={{
        background: `radial-gradient(circle at ${at}, color-mix(in srgb, var(--mn-${glow}) ${strength}%, transparent), color-mix(in srgb, var(--mn-navy) ${fadeTo}%, transparent) ${fadeAt}%)` }} />
    </>
  );
}
function MhMoment({ children, foot, kind }) {
  return (
    <div className="mh-page mh-moment" data-kind={kind}>
      <main className="mh-body" data-bare="" style={{ padding: 0, display: "flex", flexDirection: "column", minHeight: "100dvh" }}>
        {children}
        {foot && <div className="mh-momentfoot">{foot}</div>}
      </main>
      <MhGrain />
    </div>
  );
}

// ── 11 NOW LOADING MUSCAT ─────────────────────────────────────────────────
// Shown while the app loads and on the first open of a session day, once per
// device per day. progress: 0..1, from the real load; the bar never finishes
// in under MH_LOAD_MIN, and a tap only goes through once the data is ready.
const MH_LOAD_MIN = 1200;
// "Once" is per device: a moment is keyed by what it is about, e.g.
// mhOnce("loaded", "2026-12-21"), mhOnce("card", "p05/5"), mhOnce("rep", "p05/rising").
// due() asks, seen() records. Storage can be missing (private mode) — then a
// moment shows again rather than never, which is the cheaper of the two faults.
const mhOnce = (kind, key) => ({
  due() { try { return localStorage.getItem("mh-once-" + kind) !== key && !(localStorage.getItem("mh-once-" + kind + "-" + key)); } catch (e) { return true; } },
  seen() { try { localStorage.setItem(kind === "loaded" ? "mh-once-loaded" : "mh-once-" + kind + "-" + key, kind === "loaded" ? key : "1"); } catch (e) { /* show again next time */ } },
});
// The tips in heist-season.json, filled from the player's own data. A tip
// whose blanks cannot be filled is skipped rather than shown with a hole.
function mhTips(D, X) {
  const me = X.me, rival = me && X.above(me), next = me && mhNextRep(me.rep);
  const n = Math.max(1, X.nightsPlayed);
  const fin = D.sessions.find(s => s.finale);
  const vals = {
    rival: rival && mhFirst(rival.name), gap: rival && rival.points - me.points,
    n: next && Math.max(0, next.perNight * n - me.points), nextRep: next && next.label,
    finaleDay: fin && mhDay(fin.date), voucher: MH.voucher,
  };
  return (MH.tips || []).map(t => {
    let ok = true;
    const s = t.replace(/\{(\w+)\}/g, (_, k) => { if (vals[k] == null) ok = false; return vals[k]; });
    return ok ? s : null;
  }).filter(Boolean);
}
function MhLoading({ D, go, progress, ready = true, tip }) {
  const X = mhDerive(D);
  const s = D.sessions.find(x => x.no === (D.homeNext || 0)) || D.sessions.find(x => x.state !== "done") || D.sessions[D.sessions.length - 1];
  const tips = mhTips(D, X);
  const line = tips.length ? tips[(tip != null ? tip : Math.floor(Date.now() / 864e5)) % tips.length] : "";
  // with no real progress to follow, the bar fills over the minimum time
  const [t, setT] = React.useState(progress != null ? progress : 0);
  React.useEffect(() => {
    if (progress != null) { setT(progress); return; }
    const t0 = performance.now(); let raf;
    const f = now => { const k = Math.min(1, (now - t0) / MH_LOAD_MIN); setT(k); if (k < 1) raf = requestAnimationFrame(f); };
    raf = requestAnimationFrame(f); return () => cancelAnimationFrame(raf);
  }, [progress]);
  const done = ready && t >= 1;
  return (
    <div className="mh-page mh-loading">
      <button type="button" className="mh-loadtap" disabled={!done} onClick={() => go("home")}
        aria-label={done ? "Continue to Home" : "Loading"}>
        <MhHeroCut height="100%" src={s.art} pos={s.artPos || "center 28%"} cut={[54, 62]} fade="none"
          style={{ position: "absolute", inset: 0 }} />
        <div className="mh-loadtag"><MhSceneTag>{s.code} · {s.title}</MhSceneTag></div>
        <div className="mh-loadlock"><MhTitleLockup size="M" center /></div>
        <div className="mh-loadfoot">
          <MhLabel tone="peach">Did you know</MhLabel>
          <MhSerif size={18} tone="sand" style={{ lineHeight: 1.3 }}>{line}</MhSerif>
          <div className="mh-loadbar">
            <div role="progressbar" aria-valuemin={0} aria-valuemax={100} aria-valuenow={Math.round(t * 100)}
              aria-label="Now loading Muscat"><div style={{ width: (t * 100) + "%" }} /></div>
            <MhLabel>Now loading Muscat</MhLabel>
          </div>
        </div>
      </button>
      <MhGrain />
    </div>
  );
}

// ── 12 NEW CREW CARD ──────────────────────────────────────────────────────
// After each finished session, once per player per session: the card as it
// now stands. The headline follows the tier change (up / holding / down).
function MhCardPull({ D, go, no }) {
  const X = mhDerive(D);
  const m = (D.moments || []).find(x => x.type === "tierUp" && (no == null || x.session === +no))
    || (X.me ? { playerId: X.me.id, session: +no || X.lastDone, from: X.me.tier.id, to: X.me.tier.id } : {});
  const p = X.byId[m.playerId];
  const s = D.sessions.find(x => x.no === m.session);
  React.useEffect(() => { if (!p || !s) go("home"); }, [p, s]);
  if (!p || !s) return null;
  const from = mhTierById(m.from), to = p.tier;
  const dir = mhTierIdx(to.id) < mhTierIdx(from.id) ? "up" : mhTierIdx(to.id) > mhTierIdx(from.id) ? "down" : "hold";
  const title = dir === "up" ? <>TIER UP:<br /><span className="mh-hl" style={{ color: "var(--mn-gold)" }}>{to.label}</span></>
    : dir === "down" ? <>TIER DOWN:<br /><span className="mh-hl">{to.label}</span></>
    : <>HOLDING<br /><span className="mh-hl" style={{ color: "var(--mn-gold)" }}>{to.label}</span></>;
  const where = p.rank === 1 ? "top of the table" : `#${p.rank} on the table`;
  const cap = w => w.charAt(0) + w.slice(1).toLowerCase();
  const line = dir === "up" ? `Upgraded from ${cap(from.label)} · ${where}`
    : dir === "down" ? `Down from ${cap(from.label)} · ${where}` : `Still ${cap(to.label)} · ${where}`;
  return (
    <MhMoment foot={<>
      <MhButton kind="ghost" live onClick={() => go("crew")}>Collection</MhButton>
      <MhButton live onClick={() => go("share", "card/" + p.id)}>Share card</MhButton>
    </>}>
      <MhMomentBack src={p.photo} pos={p.heroPos || p.pos} dim={.6} glow="gold" />
      <div className="mh-pullhead">
        <MhLabel tone="peach">New crew card · {s.code}</MhLabel>
        <h1 className="mn-display mh-mtitle" style={{ fontSize: 44, lineHeight: .9, textAlign: "center" }}>{title}</h1>
        <div style={{ marginTop: 8 }}>
          <MhCrewCard player={{ name: p.name, photo: p.photo, photoPos: p.pos }} rank={p.rank} points={p.points}
            rep={p.rep} size="L" stats={p.stats || {}} />
        </div>
        <MhSerif size={15}>{line}</MhSerif>
      </div>
    </MhMoment>
  );
}

// ── 13 REP UP ─────────────────────────────────────────────────────────────
function MhRepUp({ D, go, id }) {
  const X = mhDerive(D);
  const m = (D.moments || []).find(x => x.type === "repUp" && (id == null || x.playerId === id));
  // a moment that is not (or no longer) true is never drawn: a stale link goes home
  React.useEffect(() => { if (!m) go("home"); }, [m]);
  if (!m || !X.byId[m.playerId]) return null;
  const p = X.byId[m.playerId];
  const from = mhRepById(m.from), to = mhRepById(m.to), next = mhNextRep(to);
  const nights = m.session;                               // the threshold is per night played
  const pts = m.points != null ? m.points : p.points;
  const tail = next ? `${Math.max(0, next.perNight * nights - pts)} to ${next.label}` : "Top rep reached";
  const glow = `rep-${to.id}`;
  return (
    <MhMoment foot={<MhButton live onClick={() => go("share", "rep/" + p.id)} style={{ width: "100%" }}>Share the moment</MhButton>}>
      <MhMomentBack src={p.photo} pos={p.pos} dim={.4} glow={glow} at="50% 38%" fadeTo={85} fadeAt={65} />
      <div className="mh-repphoto" style={{ "--mh-glow": `var(--mn-${glow})` }}>
        <div className="mn-ring" aria-hidden="true" /><div className="mn-ring" aria-hidden="true" />
        <MhAvatar player={{ name: p.name, photo: p.photo, photoPos: p.avPos || p.pos }} size={200} zoom={p.zoom} />
      </div>
      <div className="mh-reptext">
        <MhLabel style={{ color: `var(--mn-${glow})` }}>Rep up</MhLabel>
        <h1 className="mn-display mn-slam" style={{ fontSize: 56, lineHeight: .86, margin: 0 }}>
          {mhFirst(p.name).toUpperCase()} IS<br /><span style={{ color: `var(--mn-${glow})` }}>{to.label.toUpperCase()}</span></h1>
        <MhSerif size={16}>{from.label} → {to.label} · {pts} pts · {tail}</MhSerif>
      </div>
    </MhMoment>
  );
}

// ── 14 YOUR RIVAL ─────────────────────────────────────────────────────────
// The player directly above you; at #1 it turns round and shows #2 chasing.
function MhRival({ D, go }) {
  const X = mhDerive(D);
  const me = X.me;
  const top = me.rank === 1;
  const them = top ? X.players.find(p => p.rank === 2) : X.above(me);
  const R = D.rival && D.rival.rivalId === them.id ? D.rival : { h2h: { w: 0, l: 0 }, meetings: [] };
  const gap = Math.abs(them.points - me.points);
  const tone = r => /^won|champ/i.test(r) ? (/champ/i.test(r) ? "gold" : "teal") : "coral";
  const Side = ({ p, right, tag, color }) => (
    <div className="mh-rivside" data-right={right ? "" : undefined}>
      <MhLabel tone={color}>{tag}</MhLabel>
      <div className="mn-display" style={{ fontSize: 34, lineHeight: .9 }}>{mhFirst(p.name).toUpperCase()}</div>
      <MhDisplay size={26} tone={color} style={{ lineHeight: 1.15 }}>{p.points}</MhDisplay>
    </div>
  );
  return (
    <div className="mh-page">
      <main className="mh-body" data-bare="" style={{ padding: 0 }}>
        <div className="mh-split2">
          <div className="mh-half" data-side="l"><div><MhArt src={me.photo} pos={me.splitPos || me.pos} /></div></div>
          <button type="button" className="mh-half" data-side="r" onClick={() => go("card", them.id)} aria-label={`${them.name}'s crew card`}>
            <div><MhArt src={them.photo} pos={them.splitPos || them.pos} /></div></button>
          <svg className="mh-splitline" viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true">
            <line x1="58" y1="0" x2="42" y2="100" vectorEffect="non-scaling-stroke" /></svg>
          <div className="mh-splitfade" aria-hidden="true" />
          <div style={{ position: "absolute", left: 20, top: 58 }}><MhLabel tone="peach">{top ? "#2 chasing" : "Your rival"}</MhLabel></div>
          <Side p={me} tag={`You · #${me.rank}`} color="teal" />
          <Side p={them} right tag={`#${them.rank}`} color="coral" />
        </div>
        <div className="mh-col" style={{ padding: "12px 20px 0", gap: 10 }}>
          <MhGlass accent="gold-50" style={{ textAlign: "center" }}>
            <MhDisplay size={30} tone="gold" style={{ lineHeight: 1.15 }}>{gap} PT{gap === 1 ? "" : "S"} {top ? "IN HAND" : "TO SETTLE IT"}</MhDisplay>
            <MhLabel>Head to head this season · {R.h2h.w}–{R.h2h.l}</MhLabel>
          </MhGlass>
          {R.meetings.map(x => (
            <div key={x.session + x.label} className="mh-meet">
              <span>{D.sessions[x.session - 1].code} · {x.label}</span>
              <span style={{ color: `var(--mn-${tone(x.result)})` }}>{x.result.replace("-", "–")}</span>
            </div>
          ))}
        </div>
      </main>
      <MhGrain />
    </div>
  );
}

// ── 15 SCORE SETTLED ──────────────────────────────────────────────────────
// Fires when a locked result moves you above your rival. The new rank and the
// next rival are RECOMPUTED from the table with the locked points applied,
// not read from the moment, so the screen cannot disagree with Most Wanted.
function MhSettled({ D, go }) {
  const X = mhDerive(D);
  const m = (D.moments || []).find(x => x.type === "scoreSettled");
  React.useEffect(() => { if (!m) go("home"); }, [m]);
  if (!m || !X.byId[m.playerId] || !X.byId[m.overtookId]) return null;
  const now = { [m.playerId]: m.points[0], [m.overtookId]: m.points[1] };
  const table = X.players.map(p => ({ ...p, points: now[p.id] != null ? now[p.id] : p.points }))
    .sort((a, b) => b.points - a.points || a.rank - b.rank);
  const at = table.findIndex(p => p.id === m.playerId);
  const me = table[at], beaten = table.find(p => p.id === m.overtookId);
  const was = X.byId[m.playerId].rank, rank = at + 1;
  const next = table[at - 1];
  const s = D.sessions.find(x => x.no === m.session);
  return (
    <MhMoment kind="settled" foot={<MhButton live onClick={() => go("share", "settled")} style={{ width: "100%" }}>Share the moment</MhButton>}>
      <MhHeroCut height={500} src={me.photo} pos={me.splitPos || me.pos} cut={[86, 100]} fade="settled">
        <div className="mh-settledhead">
          <MhLabel tone="peach">{s.code} · result locked</MhLabel>
          <h1 className="mn-display mn-slam mh-shout" style={{ fontSize: 68 }}>SCORE<br /><span style={{ color: "var(--mn-coral)" }}>SETTLED</span></h1>
        </div>
      </MhHeroCut>
      <div className="mh-tiles" style={{ paddingTop: 8 }}>
        <MhGlass style={{ padding: "12px 14px" }}>
          <MhLabel tone="teal">New rank</MhLabel>
          <MhDisplay size={30} style={{ lineHeight: 1.15 }}>#{rank} {was > rank && <span style={{ fontSize: 16, color: "var(--mn-teal)" }}>▲{was - rank}</span>}</MhDisplay>
          <MhSerif size={13}>{me.name} {me.points} · {beaten.name} {beaten.points}</MhSerif>
        </MhGlass>
        <MhGlass style={{ padding: "12px 14px" }}>
          <MhLabel tone="coral">Next rival</MhLabel>
          {next ? <>
            <MhDisplay size={20} style={{ lineHeight: 1.05 }}>{next.name.toUpperCase()}</MhDisplay>
            <MhSerif size={13}>{next.points - me.points} pts ahead</MhSerif>
          </> : <><MhDisplay size={20} style={{ lineHeight: 1.05 }}>NOBODY</MhDisplay><MhSerif size={13}>top of the table</MhSerif></>}
        </MhGlass>
      </div>
    </MhMoment>
  );
}

// ── 16 THE BIG SCORE ──────────────────────────────────────────────────────
function MhFinale({ D, go }) {
  const X = mhDerive(D);
  const s = D.sessions.find(x => x.finale);
  const [lead1, lead2] = X.players;                       // ranked
  const lead = lead1.points - lead2.points;
  const atStart = D.finale && D.finale.leadAtStart != null ? D.finale.leadAtStart : lead;
  const cta = s.state === "live" ? ["LIVE · OPEN", () => go("session", s.no)]
    : s.state === "done" ? ["FULL RESULTS", () => go("recap", s.no)]
    : ["SIGN UP FOR THE FINALE", () => go("signup", s.no)];
  return (
    <MhMoment foot={<MhButton live onClick={cta[1]} style={{ width: "100%" }}>{cta[0]}</MhButton>}>
      <MhHeroCut height={380} src={s.art} pos={s.artPos || "center 45%"} cut={[84, 100]} fade="finale" gold>
        <div style={{ position: "absolute", left: 20, top: 58 }}>
          <MhLabel tone="gold">Finale · {mhDay(s.date)}{s.doublePoints ? " · 2× points" : ""}</MhLabel></div>
        <h1 className="mn-display mh-shout" style={{ position: "absolute", left: 20, bottom: 70, fontSize: 66 }}>
          THE BIG<br /><span style={{ color: "var(--mn-gold)" }}>SCORE</span></h1>
      </MhHeroCut>
      <div className="mh-col" style={{ padding: "0 20px", gap: 10 }}>
        <MhGlass accent="gold-45">
          <button type="button" className="mh-target" onClick={() => go("card", lead1.id)}>
            <MhAvatar player={{ name: lead1.name, photo: lead1.photo, photoPos: lead1.pos }} size={46} ring="gold" />
            <div style={{ flex: 1, minWidth: 0, textAlign: "left" }}>
              <MhLabel tone="gold">The target · #1</MhLabel>
              <MhDisplay size={22} style={{ lineHeight: 1.15 }}>{lead1.name.toUpperCase()}</MhDisplay>
            </div>
            <MhDisplay size={26}>{lead1.points}</MhDisplay>
          </button>
          <div className="mh-split" style={{ marginTop: 10 }}><MhLabel>His lead</MhLabel><MhLabel>{lead} / {atStart}</MhLabel></div>
          <div className="mh-leadbar"><div style={{ width: Math.max(0, Math.min(100, atStart ? lead / atStart * 100 : 0)) + "%" }} /></div>
        </MhGlass>
        {s.doublePoints && <div className="mh-rule"><MhDisplay size={22} tone="gold" style={{ width: 40 }}>2×</MhDisplay><span>Double points all night</span></div>}
        {MH.bossKillBonus && MH.bossKillBonus.enabled &&
          <div className="mh-rule"><MhDisplay size={22} tone="coral" style={{ width: 40 }}>+{MH.bossKillBonus.points}</MhDisplay><span>Beat a top-3 team (needs organiser OK)</span></div>}
      </div>
    </MhMoment>
  );
}
