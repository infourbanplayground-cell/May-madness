// MUSCAT HEIST · Vol.10 — THE LOOT: knockout cards (owner, 25 Nov 2026).
//
// Reach the knockout and you are dealt a card for that night; it UPGRADES as
// you win, and you keep your best one per night — so a season is at most nine
// cards, one per episode, collected into an album on the profile.
//
//   THE JOB     quarter-final        cream
//   INSIDE MAN  semi-final           orange, sunset glow
//   GETAWAY     finalist             pink foil
//   THE SCORE   champion             gold; the owner's own artwork when uploaded
//
// EVERYTHING HERE IS DERIVED FROM THE BRACKET the night already stores — D.nights
// [no].knockout, the adapter's shape, which the preview fixtures share — so
// nothing new is saved and nothing is scored (handoff rule 2). The badges are
// for show and never touch the table.
//
// SERIALS ARE REAL. "EP03 · INSIDE MAN · 2/4" means four people hold that card:
// the losing pairs of that round, in bracket order. A serial is printed only
// once every match in that round has a result — before then the card is IN
// PLAY, because it can still upgrade and the count is not yet a fact.

const MH_LOOT = [
  { id: "job", name: "The Job", round: "Quarter-final", reached: "Made the quarter-finals" },
  { id: "inside", name: "Inside Man", round: "Semi-final", reached: "Made the semi-finals" },
  { id: "getaway", name: "Getaway", round: "Finalist", reached: "Made the final" },
  { id: "score", name: "The Score", round: "Champion", reached: "Champions" },
];
const mhLootTier = id => MH_LOOT.find(t => t.id === id) || MH_LOOT[0];
const mhLootRank = id => MH_LOOT.findIndex(t => t.id === id);

// The badges: cosmetic, counted off the album.
const MH_LOOT_BADGES = [
  { id: "crew", name: "Crew", rule: "Reach the knockout on 3 nights", need: 3, count: c => c.length },
  { id: "made", name: "Made Man", rule: "Reach 3 finals", need: 3, count: c => c.filter(x => mhLootRank(x.tier) >= 2).length },
  { id: "mastermind", name: "Mastermind", rule: "Win a night — hold The Score", need: 1, count: c => c.filter(x => x.tier === "score").length },
  { id: "full", name: "Full Heist", rule: "Reach the knockout on all nine nights", need: 0, count: c => c.length },
];

// mhLoot(D) -> { byPlayer: { pid: [card] }, of(pid, no) }
// A card: { pid, no, tier, name, first, photo, partner, code, title, art, artPos,
//           date, doubled, settled, serial, of, beat, score, custom }
function mhLoot(D) {
  if (D.__loot) return D.__loot;
  const byPlayer = {};
  const total = (D.sessions || []).length;
  (D.sessions || []).forEach(sv => {
    const N = (D.nights || {})[sv.no], K = N && N.knockout;
    if (!K) return;
    const best = {};                                   // pid -> { tier, team, partner, match }
    const deal = (team, tier, extra) => (team && team.players || []).forEach((p, i, all) => {
      if (!p || !p.id) return;
      if (best[p.id] && mhLootRank(best[p.id].tier) >= mhLootRank(tier)) return;
      best[p.id] = Object.assign({ tier, p, partner: all[1 - i] || null }, extra);
    });
    const rounds = [["job", K.qf || []], ["inside", K.sf || []], ["getaway", K.final ? [K.final] : []]];
    rounds.forEach(([tier, ms]) => ms.forEach(m => { deal(m && m.ta, tier, { m }); deal(m && m.tb, tier, { m }); }));
    const F = K.final;
    if (F && F.winner) deal(F.winner === "a" ? F.ta : F.tb, "score", { m: F });

    // serials: the losers of each round in bracket order (the champions for The Score)
    const serial = {};
    const holders = (tier, ms) => {
      const real = ms.filter(m => m && m.ta && m.tb);
      const decided = real.length > 0 && real.every(m => m.winner);
      const list = [];
      real.forEach(m => {
        const lose = tier === "score" ? (m.winner === "a" ? m.ta : m.tb) : (m.winner === "a" ? m.tb : m.winner === "b" ? m.ta : null);
        (lose && lose.players || []).forEach(p => p && list.push(p.id));
      });
      serial[tier] = { decided, of: real.length * 2, list };
    };
    holders("job", K.qf || []); holders("inside", K.sf || []);
    holders("getaway", F ? [F] : []); holders("score", F ? [F] : []);

    Object.keys(best).forEach(pid => {
      const b = best[pid], S = serial[b.tier], m = b.m;
      const mine = m && (m.ta && m.ta.players.some(p => p && p.id === pid) ? "a" : "b");
      const opp = m && (mine === "a" ? m.tb : m.ta);
      const settled = b.tier === "score" || (m && !!m.winner && m.winner !== mine) || sv.state === "done";
      const idx = S.list.indexOf(pid);
      const card = {
        pid, no: sv.no, tier: b.tier, name: b.p.name, first: b.p.first || mhFirstName(b.p.name), photo: b.p.photo,
        partner: b.partner ? { name: b.partner.name, first: b.partner.first || mhFirstName(b.partner.name), photo: b.partner.photo } : null,
        code: sv.code, title: sv.title, art: sv.art, artPos: sv.artPos, date: sv.date, doubled: !!sv.doublePoints,
        settled, serial: S.decided && idx >= 0 ? idx + 1 : null, of: S.decided ? S.of : null,
        opp: opp ? opp.players.map(p => p && (p.first || mhFirstName(p.name))).join(" & ") : null,
        score: m && m.ga != null ? (mine === "a" ? `${m.ga}-${m.gb}` : `${m.gb}-${m.ga}`) : null,
        custom: b.tier === "score" ? ((D.lootArt || {})[`${sv.no}/${pid}`] || null) : null,
      };
      (byPlayer[pid] = byPlayer[pid] || []).push(card);
    });
  });
  Object.values(byPlayer).forEach(l => l.sort((a, b) => a.no - b.no));
  const out = { byPlayer, total, of: (pid, no) => (byPlayer[pid] || []).find(c => c.no === +no) || null };
  try { Object.defineProperty(D, "__loot", { value: out, enumerable: false }); } catch (e) {}
  return out;
}
const mhFirstName = n => (n || "").split(/\s+/)[0];
const mhBadgeNeed = (b, total) => b.need || total;
function mhLootBadges(cards, total) {
  return MH_LOOT_BADGES.map(b => { const n = b.count(cards), need = mhBadgeNeed(b, total);
    return Object.assign({}, b, { n: Math.min(n, need), need, earned: n >= need }); });
}
const mhLootSerial = c => c.serial ? `${c.serial}/${c.of}` : c.settled ? "" : "in play";

// ── the card ─────────────────────────────────────────────────────────────
// 4:5, the same proportion as a Heist portrait and the owner's champion art, so
// an uploaded picture drops in exactly. size: "S" (album), "M", "L" (screen, story)
const MH_LOOT_W = { S: 104, M: 168, L: 264 };
function MhLootCard({ card, size = "L", onClick, still }) {
  const w = MH_LOOT_W[size] || size, t = mhLootTier(card.tier), small = w < 140;
  const body = (
    <div className="mh-loot" data-tier={card.tier} data-size={small ? "s" : "l"} data-still={still ? "" : undefined}
      style={{ width: w, height: Math.round(w * 1.25), fontSize: w / 264 * 16 }}>
      {card.custom ? (
        <div className="mh-loot-custom"><MhArt src={card.custom} pos="center 30%" eager={!small} /></div>
      ) : <>
        <div className="mh-loot-scene"><MhArt src={card.art} pos={card.artPos} sizes={small ? "120px" : "300px"} /></div>
        <div className="mh-loot-wash" aria-hidden="true" />
        <div className="mh-loot-face"><MhArt src={card.photo} name={card.name} pos="center 0%" sizes={small ? "120px" : "300px"} /></div>
        <div className="mh-loot-fade" aria-hidden="true" />
      </>}
      {(card.tier === "getaway" || card.tier === "score") && <div className="mh-loot-foil" aria-hidden="true" />}
      <div className="mh-loot-top">
        <span className="mh-loot-code">{card.code}</span>
        {card.doubled && <span className="mh-loot-2x">2X</span>}
      </div>
      <div className="mh-loot-foot">
        <div className="mh-loot-tier"><span className="mh-fitline">{t.name}</span></div>
        {!small && <>
          <div className="mh-loot-name"><span className="mh-fitline">{card.name}</span></div>
          {card.partner && <div className="mh-loot-with">with {card.partner.first}</div>}
          <div className="mh-loot-meta"><span>{t.round}</span><span>{mhLootSerial(card)}</span></div>
        </>}
      </div>
    </div>
  );
  return onClick
    ? <button type="button" className="mh-lootbtn" onClick={onClick} aria-label={`${card.code} ${t.name}, ${card.name}`}>{body}</button>
    : body;
}

// an empty slot: the night's painting, darkened, and what the slot is waiting for
function MhLootSlot({ s, label }) {
  return (
    <div className="mh-loot mh-loot-empty" style={{ width: MH_LOOT_W.S, height: Math.round(MH_LOOT_W.S * 1.25) }}>
      <div className="mh-loot-scene"><MhArt src={s.art} pos={s.artPos} sizes="120px" /></div>
      <div className="mh-loot-top"><span className="mh-loot-code">{s.code}</span></div>
      <div className="mh-loot-lock">{label}</div>
    </div>
  );
}

// ── the album ────────────────────────────────────────────────────────────
function MhAlbum({ D, pid, go, title = "The loot" }) {
  const L = mhLoot(D), cards = L.byPlayer[pid] || [];
  const badges = mhLootBadges(cards, L.total);
  const count = id => cards.filter(c => c.tier === id).length;
  return (
    <section className="mh-col mh-album" aria-label="Knockout cards" style={{ gap: 10 }}>
      <div className="mh-split">
        <MhLabel tone="peach">{title}</MhLabel>
        <MhLabel>{cards.length} of {L.total} nights</MhLabel>
      </div>
      <div className="mh-album-grid">
        {D.sessions.map(s => {
          const c = cards.find(x => x.no === s.no);
          if (c) return <MhLootCard key={s.no} card={c} size="S" onClick={() => go("loot", `${pid}.${s.no}`)} />;
          return <MhLootSlot key={s.no} s={s} label={s.state === "done" ? "No card" : s.state === "live" ? "Tonight" : mhDay(s.date)} />;
        })}
      </div>
      <div className="mh-album-tally">
        {MH_LOOT.map(t => <span key={t.id} className="mh-chip" data-loot={t.id}>{t.name} · {count(t.id)}</span>)}
      </div>
      <div className="mh-badges">
        {badges.map(b => (
          <div key={b.id} className="mh-badge" data-earned={b.earned ? "" : undefined}>
            <div className="mn-display">{b.name}</div>
            <div className="mh-badge-rule">{b.rule}</div>
            <div className="mh-badge-n">{b.earned ? "Earned" : `${b.n}/${b.need}`}</div>
          </div>
        ))}
      </div>
    </section>
  );
}

// ── one card, big — #loot/<pid>.<no> (one route argument, so the app shell and
// the preview hand it over the same way) ──
function MhLootScreen({ D, go, id }) {
  const L = mhLoot(D);
  const [pid, no] = String(id || "").split("."), card = L.of(pid, no);
  const fresh = D.meId === pid && D.sessions.filter(s => s.state === "done").slice(-1).some(s => s.no === +no);
  if (!card) {
    return (
      <MhPage D={D} tab="me" onTab={go} nav={false} pad="92px 20px 0">
        <div className="mh-col">
          <div className="mh-split"><MhLabel>Knockout card</MhLabel>
            <button type="button" className="mh-close mn-serif" onClick={() => go("back")}>close ✕</button></div>
          <MhGlass><MhSerif size={15}>No card for this night.</MhSerif></MhGlass>
        </div>
      </MhPage>
    );
  }
  const t = mhLootTier(card.tier);
  const line = card.tier === "score"
    ? `Won the final ${card.score || ""}${card.opp ? " against " + card.opp : ""}`
    : card.settled && card.opp ? `${t.reached} · lost ${card.score || ""} to ${card.opp}` : t.reached;
  return (
    <MhPage D={D} tab="me" onTab={go} nav={false} pad="92px 20px 0">
      <div className="mh-col">
        <div className="mh-split">
          <MhLabel tone={fresh ? "gold" : undefined}>{fresh ? "New knockout card" : "Knockout card"}</MhLabel>
          <button type="button" className="mh-close mn-serif" onClick={() => go("back")}>close ✕</button>
        </div>
        <div className="mh-loot-stage" data-tier={card.tier} data-fresh={fresh ? "" : undefined}><MhLootCard card={card} size="L" /></div>
        <div style={{ textAlign: "center" }}>
          <MhSerif size={16}>{card.code} · {card.title}</MhSerif>
          <MhLabel style={{ marginTop: 4 }}>{line}</MhLabel>
          {card.serial && <MhLabel tone="peach" style={{ marginTop: 4 }}>One of {card.of} {t.name} cards from this night</MhLabel>}
        </div>
        <MhButton live onClick={() => go("share", `loot/${pid}.${card.no}`)}>Share to story</MhButton>
        <MhAlbum D={D} pid={pid} go={(to, a) => to === "loot" ? location.replace(`#loot/${a}`) : go(to, a)}
          title={D.meId === pid ? "Your loot" : `${mhFirstName(card.name)}'s loot`} />
      </div>
    </MhPage>
  );
}

// ── the story — the share sheet's "Knockout card" ──────────────────────
function MhStoryLoot({ D, id }) {
  const [pid, no] = String(id || "").split(".");
  const card = mhLoot(D).of(pid, no);
  if (!card) return <MhStoryFrame label="Knockout card"><div /></MhStoryFrame>;
  const t = mhLootTier(card.tier);
  return (
    <MhStoryFrame label={`${card.name}: ${t.name}, ${card.code}`}>
      <MhMomentBack src={card.custom || card.art} pos={card.custom ? "center 30%" : card.artPos} dim={.55}
        glow={card.tier === "score" ? "gold" : "coral"} at="50% 42%" />
      <div className="mh-lootstory">
        <MhLabel tone="peach">Knockout card · {card.code}</MhLabel>
        <MhLootCard card={card} size={300} still />
        <MhLabel tone="sand" style={{ marginTop: 6 }}>{card.title ? card.title + " · " : ""}{mhDay(card.date)}</MhLabel>
        <div style={{ marginTop: 6 }}><MhTitleLockup size={50} center meta={false} /></div>
        <MhLabel tone="sand" style={{ marginTop: 2 }}>{(MH.stories || {}).url || MH.host}</MhLabel>
      </div>
    </MhStoryFrame>
  );
}
