// ── Quality of life (26 Nov 2026, owner: "do all one by one") ─────────────
// Small things players and the organiser feel every night. Nothing here
// scores, saves a result or changes a rule; every figure is read from D, which
// the adapter builds from the inherited engine.
//
//   MhWho         "who are you?" — remembered on this phone (the inherited
//                 saveMe), so ME, the rival and the cards work without a PIN
//   MhYouStrip    Most Wanted's sticky "you · #12" strip that jumps to your row
//   MhLiveMine    Home during a live night: your group place, your next match
//   MhFresh       pull-to-refresh indicator + "updated 12s ago"
//   MhInstall     one-time "add to home screen" hint from the second visit
//   MhHowTo       three cards: points, knockout cards, rep
//   mhHaptic      a 10ms tick where the phone supports it
//   mhTextSize    the bigger-text setting, applied as a class on <html>

const mhStore = {
  get: (k, d) => { try { const v = localStorage.getItem(k); return v == null ? d : v; } catch (e) { return d; } },
  set: (k, v) => { try { localStorage.setItem(k, v); } catch (e) {} },
};
const mhHaptic = (ms = 10) => { try { navigator.vibrate && navigator.vibrate(ms); } catch (e) {} };
const mhNorm = s => (s || "").toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "").replace(/[^a-z0-9؀-ۿ ]/g, " ").replace(/\s+/g, " ").trim();

// bigger text: one class on <html>, read once at boot so the first paint is right
const mhTextSize = {
  on: () => mhStore.get("mh-bigtext", "") === "1",
  apply: on => { try { document.documentElement.classList.toggle("mh-bigtext", !!on); } catch (e) {} },
  set: on => { mhStore.set("mh-bigtext", on ? "1" : ""); mhTextSize.apply(on); },
};
mhTextSize.apply(mhTextSize.on());

// ── who are you? ─────────────────────────────────────────────────────────
// Players who have played come first (that is who opens the app on a night),
// then everyone else on the roster. Search looks at everybody, always: the
// person searching is very often the one who has not played yet.
function MhWho({ D, go }) {
  const [q, setQ] = React.useState("");
  const n = mhNorm(q);
  const all = D.roster || D.players;
  const list = (n ? all.filter(p => mhNorm(p.name).includes(n)) : all.filter(p => p.points > 0 || p.nights > 0)).slice(0, n ? 60 : 40);
  const pick = id => { mhHaptic(); D.setMe && D.setMe(id); mhStore.set("mh-who-asked", "1"); go("home"); };
  return (
    <MhPage D={D} tab="me" onTab={go}>
      <div className="mh-col">
        <MhTitle title="WHO ARE YOU?" aside="remembered on this phone" />
        <MhSerif size={14}>Pick your name once and the app follows you: your rank, your rival, your cards. No PIN — that is for the scorer.</MhSerif>
        <input className="mh-search" type="search" placeholder="Search your name" value={q} autoFocus
          onChange={e => setQ(e.target.value)} aria-label="Search your name" />
        <div>
          {list.map(p => (
            <button type="button" key={p.id} className="mh-wrow mh-tap mh-whorow" onClick={() => pick(p.id)} data-me={p.id === D.meId ? "" : undefined}>
              <MhAvatar player={{ name: p.name, photo: p.photo, photoPos: p.pos }} size={34} />
              <div className="mh-wname" style={{ textAlign: "left" }}>{p.name}{p.id === D.meId && <span className="mn-serif"> you</span>}</div>
              <div className="mh-wgap">{p.points > 0 ? `${p.points} pts` : ""}</div>
            </button>
          ))}
          {!list.length && <MhSerif size={14}>Nobody called "{q}" yet. Ask the organiser to add you; you will be here once you have.</MhSerif>}
        </div>
        <div className="mh-split" style={{ marginTop: 8 }}>
          {D.meId && D.clearMe && <MhButton kind="ghost" onClick={() => { D.clearMe(); go("home"); }}>I'm not on here — clear</MhButton>}
          <MhButton kind="ghost" onClick={() => { mhStore.set("mh-who-asked", "1"); go("home"); }}>Just looking</MhButton>
        </div>
      </div>
    </MhPage>
  );
}

// ── Most Wanted: your own row, one tap away ───────────────────────────────
function MhYouStrip({ D, me, go }) {
  if (!me) return D.setMe ? (
    <button type="button" className="mh-youstrip mh-tap" onClick={() => go("who")}>
      <span className="mh-youlab">Find yourself</span><span className="mh-youarrow">Pick your name ›</span>
    </button>) : null;
  const jump = () => {
    mhHaptic();
    const el = document.getElementById("w-" + me.id);
    if (!el) return;
    el.scrollIntoView({ behavior: "smooth", block: "center" });
    el.classList.remove("mh-flash"); void el.offsetWidth; el.classList.add("mh-flash");
  };
  return (
    <button type="button" className="mh-youstrip mh-tap" onClick={jump} aria-label={`Jump to your row, rank ${me.rank}`}>
      <span className="mh-youlab">You</span>
      <span className="mn-display mh-yourank">#{me.rank}</span>
      <span className="mh-youname">{mhFirst ? mhFirst(me.name) : me.name}</span>
      <span className="mh-youpts">{me.points} pts</span>
      <span className="mh-youarrow">Show ›</span>
    </button>
  );
}

// ── Home during a live night: where am I ─────────────────────────────────
function MhLiveMine({ D, live, go }) {
  const N = live && D.nights && D.nights[live.no];
  if (!N || !D.meId || !N.groups) return null;
  let mine = null, grp = null;
  for (const [g, G] of Object.entries(N.groups)) {
    const row = G.standings.find(r => (r.players || []).some(p => p.id === D.meId));
    if (row) { mine = row; grp = [g, G]; break; }
  }
  if (!mine) return null;
  const [g, G] = grp;
  const myMatch = m => [m.ta, m.tb].some(t => t && t.id === mine.id);
  const ms = G.matches.filter(myMatch);
  const onCourt = ms.find(m => m.state === "live");
  const nextM = ms.find(m => m.state === "next");
  const left = ms.filter(m => m.state !== "final").length;
  const vs = m => (m.ta && m.ta.id === mine.id ? m.b : m.a);
  // the knockout, once it is drawn: is this pair in it, and against whom
  const K = N.knockout, koM = K && [...(K.qf || []), ...(K.sf || []), K.final].filter(Boolean)
    .find(m => !m.winner && [m.ta, m.tb].some(t => t && t.id === mine.id));
  return (
    <button type="button" className="mn-glass mh-tap mh-livemine" data-accent="coral" onClick={() => go("session", live.no)}>
      <MhLabel tone="coral">Your night · Group {g}</MhLabel>
      <div className="mh-split" style={{ marginTop: 4 }}>
        <div style={{ minWidth: 0 }}>
          <MhDisplay size={24}>{mine.pos}{["", "st", "nd", "rd"][mine.pos] || "th"} in the group</MhDisplay>
          <MhSerif size={14}>{mine.w} won · {mine.pts} pts · GD {mine.gd > 0 ? "+" : ""}{mine.gd}{mine.q ? " · in a qualifying place" : ""}</MhSerif>
        </div>
      </div>
      <div className="mh-livenext">
        {koM ? <><b>{koM.round === "final" ? "FINAL" : koM.round.toUpperCase()}</b> v {koM.ta && koM.ta.id === mine.id ? koM.b : koM.a}</>
          : onCourt ? <><b>ON COURT</b> v {vs(onCourt)}{onCourt.score ? ` · ${onCourt.score}` : ""}</>
          : nextM ? <><b>NEXT</b> v {vs(nextM)}{nextM.court ? ` · Court ${nextM.court}` : ""}</>
          : left === 0 ? <><b>GROUP DONE</b> {mine.q ? "· waiting on the draw" : ""}</> : null}
      </div>
    </button>
  );
}

// ── is this live? pull to refresh, and how fresh the numbers are ─────────
function MhFresh({ pullY, lastSync, sync, onRefresh }) {
  const [, tick] = React.useState(0);
  React.useEffect(() => { const t = setInterval(() => tick(x => x + 1), 10000); return () => clearInterval(t); }, []);
  const ago = lastSync ? Math.max(0, Math.round((Date.now() - lastSync) / 1000)) : null;
  const txt = sync === "syncing" ? "Updating…" : ago == null ? "" : ago < 15 ? "Updated just now" : ago < 90 ? `Updated ${ago}s ago` : `Updated ${Math.round(ago / 60)} min ago`;
  return (
    <>
      {pullY > 0 && <div className="mh-pull" style={{ height: pullY }} aria-hidden="true">
        <span style={{ opacity: Math.min(1, pullY / 64) }}>{pullY >= 64 ? "Release to refresh" : "Pull to refresh"}</span></div>}
      {txt && <button type="button" className="mh-fresh" onClick={() => { mhHaptic(); onRefresh && onRefresh(); }} aria-label="Refresh now">{txt} · ↻</button>}
    </>
  );
}

// ── add to home screen, once, from the second visit ──────────────────────
let mhInstallEvt = null;
try { addEventListener("beforeinstallprompt", e => { e.preventDefault(); mhInstallEvt = e; }); } catch (e) {}
(() => { const v = +mhStore.get("mh-visits", "0") || 0; mhStore.set("mh-visits", String(v + 1)); })();
function MhInstall() {
  const standalone = (() => { try { return matchMedia("(display-mode: standalone)").matches || navigator.standalone; } catch (e) { return false; } })();
  const [gone, setGone] = React.useState(() => standalone || mhStore.get("mh-install-done", "") === "1" || (+mhStore.get("mh-visits", "0") || 0) < 2);
  if (gone) return null;
  const ios = /iphone|ipad|ipod/i.test(navigator.userAgent || "");
  const close = () => { mhStore.set("mh-install-done", "1"); setGone(true); };
  const add = async () => { if (mhInstallEvt) { mhInstallEvt.prompt(); try { await mhInstallEvt.userChoice; } catch (e) {} } close(); };
  return (
    <div className="mn-glass mh-install">
      <div style={{ minWidth: 0 }}>
        <MhLabel tone="peach">Keep it one tap away</MhLabel>
        <MhSerif size={14}>{ios ? "Tap Share, then “Add to Home Screen”." : mhInstallEvt ? "Add Muscat Heist to your home screen." : "Open your browser menu and choose “Add to Home screen”."}</MhSerif>
      </div>
      <div className="mh-installbtns">
        {!ios && mhInstallEvt && <MhButton onClick={add}>Add</MhButton>}
        <button type="button" className="mh-x" onClick={close} aria-label="Dismiss">✕</button>
      </div>
    </div>
  );
}

// ── how it works ─────────────────────────────────────────────────────────
function MhHowTo({ D, go }) {
  const [i, setI] = React.useState(0);
  const per = (MH_REPS || []).slice().reverse();
  const cards = [
    { k: "The nights", t: `${(D.sessions || []).length || 9} nights. Points every one.`, b: [
      "Bring a partner. Groups first, then the top teams play a knockout.",
      "Every match you win scores; losing close still scores something.",
      `${(MH.doubleNights || []).length ? "The last two nights pay double." : ""}`] },
    { k: "Knockout cards", t: "Reach the knockout, get dealt a card.", b: [
      "THE JOB for a quarter-final, INSIDE MAN for a semi, GETAWAY for the final, THE SCORE for the champions.",
      "You keep your best card each night. Nine nights, nine slots in your album." ] },
    { k: "Rep", t: "Your rep grows with every night you play.", b: [
      per.map(r => `${r.label}: ${r.perNight} a night`).join(" · "),
      "Rep never drops. Your rival is whoever sits just above you on Most Wanted." ] },
  ];
  const c = cards[i], last = i === cards.length - 1;
  const done = () => { mhStore.set("mh-howto-seen", "1"); go("home"); };
  return (
    <MhPage D={D} tab="home" onTab={go}>
      <div className="mh-col mh-howto">
        <MhLabel tone="peach">How it works · {i + 1} of {cards.length}</MhLabel>
        <MhDisplay size={30} style={{ lineHeight: 1.02 }}>{c.k}</MhDisplay>
        <MhGlass>
          <MhDisplay size={20} style={{ lineHeight: 1.08 }}>{c.t}</MhDisplay>
          {c.b.filter(Boolean).map((x, k) => <MhSerif key={k} size={15} style={{ marginTop: 8 }}>{x}</MhSerif>)}
        </MhGlass>
        <div className="mh-dots" aria-hidden="true">{cards.map((_, k) => <i key={k} data-on={k === i ? "" : undefined} />)}</div>
        <div className="mh-split">
          <MhButton kind="ghost" onClick={done}>Skip</MhButton>
          <MhButton onClick={() => last ? done() : setI(i + 1)}>{last ? "Got it" : "Next ›"}</MhButton>
        </div>
      </div>
    </MhPage>
  );
}

// ── settings on ME: bigger text, change who you are, how it works ────────
function MhSettings({ D, go }) {
  const [big, setBig] = React.useState(mhTextSize.on());
  return (
    <MhGlass>
      <MhLabel tone="peach">This phone</MhLabel>
      <div className="mh-setrows">
        <button type="button" className="mh-setrow mh-tap" aria-pressed={big} onClick={() => { mhHaptic(); setBig(!big); mhTextSize.set(!big); }}>
          <span>Bigger text</span><span className="mh-toggle" data-on={big ? "" : undefined} />
        </button>
        {D.setMe && <button type="button" className="mh-setrow mh-tap" onClick={() => go("who")}><span>{D.meId ? "Not you? Change player" : "Pick your name"}</span><span>›</span></button>}
        <button type="button" className="mh-setrow mh-tap" onClick={() => go("howto")}><span>How it works</span><span>›</span></button>
      </div>
    </MhGlass>
  );
}

// ── sharing: the image AND a line of text, then WhatsApp as one tap ──────
// navigator.share with a file opens the phone's own sheet, where WhatsApp is
// one tap; the caption rides along where the platform keeps it. With no file
// share (desktop) the image downloads. The WhatsApp button sends the LINK, whose
// preview is the season's own og-card — the fastest thing to post in a group.
const mhLink = () => "https://" + (MH.host || "heist.urbanpadel.om");
async function mhShareOut(blob, filename, text) {
  const file = new File([blob], filename, { type: "image/png" });
  const msg = text ? `${text}\n${mhLink()}` : mhLink();
  if (navigator.canShare && navigator.canShare({ files: [file], text: msg })) { await navigator.share({ files: [file], text: msg }); return "shared"; }
  if (navigator.canShare && navigator.canShare({ files: [file] })) { await navigator.share({ files: [file] }); return "shared"; }
  const a = document.createElement("a"); a.href = URL.createObjectURL(blob); a.download = filename; a.click();
  return "saved";
}
function MhWhatsApp({ text, label = "Send on WhatsApp" }) {
  const href = "https://wa.me/?text=" + encodeURIComponent((text ? text + "\n" : "") + mhLink());
  return <a className="mn-btn mn-btn-ghost mh-wa" href={href} target="_blank" rel="noopener" onClick={() => mhHaptic()}>{label}</a>;
}

// ── the organiser: the next matches to start, one tap from scoring ───────
function MhUpNext({ s, N, go }) {
  const all = Object.entries(N.groups || {}).flatMap(([g, G]) => G.matches.map((m, i) => ({ ...m, g, i })));
  const on = all.filter(m => m.state === "live"), nx = all.filter(m => m.state === "next");
  const q = [...on, ...nx].slice(0, 3);
  if (!q.length) return null;
  return (
    <MhGlass style={{ padding: "10px 14px" }}>
      <MhLabel tone="peach">Scorer · up next</MhLabel>
      {q.map((m, k) => (
        <button type="button" key={m.id || k} className="mh-upnext mh-tap" onClick={() => { mhHaptic(); go("live", `${s.no}/${m.id || m.g + m.i}`); }}>
          <span className="mh-upnexttag">{m.state === "live" ? "On court" : k === on.length ? "Next" : "Then"}</span>
          <span className="mh-upnextname">{m.a} <i>v</i> {m.b}</span>
          <span className="mh-upnextg">{m.court ? `C${m.court}` : `Gr ${m.g}`} ›</span>
        </button>
      ))}
    </MhGlass>
  );
}

// ── check-in: who has arrived, before the draw goes up ───────────────────
// Stored on the night as checkIn {playerId: time}. Nothing reads it to score;
// it is the organiser's list on the night, and the count says how many pairs
// are complete.
function MhCheckIn({ D, s, N }) {
  const here = (D.checkedIn && D.checkedIn[s.no]) || {};
  const teams = N.teams || [];
  const both = teams.filter(t => (t.players || []).every(p => here[p.id])).length;
  return (
    <div className="mh-col" style={{ gap: 8 }}>
      <MhGlass style={{ padding: "10px 14px" }}>
        <div className="mh-split"><MhLabel tone="peach">Check-in</MhLabel><MhLabel>{both}/{teams.length} pairs here</MhLabel></div>
        <div className="mh-progress"><div style={{ width: (teams.length ? both / teams.length * 100 : 0) + "%" }} /></div>
        <MhSerif size={13} style={{ marginTop: 6 }}>Tap a name when they arrive. Swapping a partner or adding a walk-in is in Organiser.</MhSerif>
      </MhGlass>
      {teams.map(t => (
        <div key={t.id} className="mh-cirow" data-done={(t.players || []).every(p => here[p.id]) ? "" : undefined}>
          {(t.players || []).map(p => (
            <button type="button" key={p.id} className="mh-ciname" aria-pressed={!!here[p.id]}
              onClick={() => { mhHaptic(); D.checkIn(s.sid, p.id, !here[p.id]); }}>
              <MhAvatar player={p} size={30} /><span>{p.name}</span><b aria-hidden="true">{here[p.id] ? "✓" : ""}</b>
            </button>
          ))}
        </div>
      ))}
    </div>
  );
}
