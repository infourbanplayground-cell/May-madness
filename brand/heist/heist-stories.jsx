// MUSCAT HEIST · Vol.10 — the share exports (handoff phase 5):
// 18 Story · Campaign Poster, 19 Story · Contenders, and MY CARD.
//
// Each story is a 416x740 frame, the handoff's own artboard, exported at
// 1080x1920 (x2.596). The frame on screen IS the export — the sheet's
// preview and the saved PNG are the same DOM — so what somebody sees is what
// they post. Every word on them is data: the starring names are the table's
// top five, "27 MORE" is the roster minus them, the pool is derived, the days
// and the first night come from the nights list, and the contenders' "Eleven
// points" is #1 minus #2 in words.
const MH_STORY = { w: 416, h: 740, outW: 1080, outH: 1920 };
const MH_WORDS = ["Zero", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine", "Ten", "Eleven",
  "Twelve", "Thirteen", "Fourteen", "Fifteen", "Sixteen", "Seventeen", "Eighteen", "Nineteen"];
const MH_TENS = ["", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"];
function mhWords(n) {
  if (n < 20) return MH_WORDS[n];
  if (n < 100) return MH_TENS[Math.floor(n / 10)] + (n % 10 ? "-" + MH_WORDS[n % 10].toLowerCase() : "");
  return String(n);
}
const mhPool = D => (MH.seasonPrizes || []).reduce((a, b) => a + b, 0) + MH.voucher * 2 * D.sessions.length;
// "Mon & Wed", from the weekdays the nights actually fall on — in week order,
// Monday first: the season opens on a Wednesday, and in date order this read
// "Wed & Mon".
function mhDays() {
  const seen = [];
  (MH.nights || []).forEach(n => { const k = (mhDate(n).getDay() + 6) % 7; if (seen.indexOf(k) < 0) seen.push(k); });
  return seen.sort((a, b) => a - b).map(k => MH_DOW[(k + 1) % 7]).join(" & ");
}
const mhArt = (D, file) => (D.artBase || "") + file;

function MhStoryFrame({ children, label }) {
  return <div className="mh-story" role="img" aria-label={label}>{children}<MhGrain /></div>;
}
// the film-credits block both stories close on
function MhStoryBilling({ D, X }) {
  const S = MH.stories || {};
  const played = X.players.some(p => p.points > 0);
  const five = played ? X.players.slice(0, 5).map(p => p.name) : (S.starring || []).slice(0, 5);
  const more = Math.max(0, (D.rosterSize || X.players.length) - five.length);
  return (
    <MhBilling parts={[
      "Urban Playground", { link: "presents a" }, "Social Padel League",
      ...(five.length ? [{ link: "starring" }, <br key="b1" />, five.join(" · "), <br key="b2" />] : [<br key="b3" />]),
      ...(more ? [{ link: "with" }, `${more} more of Muscat’s finest ·`] : []),
      { link: "prize pool" }, `${mhPool(D)} OMR ·`, { link: "courts" }, MH.venue,
    ]} />
  );
}

// ── 18 CAMPAIGN POSTER ────────────────────────────────────────────────────
// Shattered panels: the hero scene left, two action shards right, the crew
// scene faded below, sand keylines along every cut.
function MhStoryPoster({ D }) {
  const X = mhDerive(D);
  const P = (MH.stories || {}).poster || {};
  const ep = MH.episodes[(P.hero && P.hero.episode || 1) - 1];
  const shards = P.shards || [];
  const first = (MH.nights || [])[0];
  return (
    <MhStoryFrame label={`${MH.name} campaign poster`}>
      <div className="mh-shard" style={{ clipPath: "polygon(0 0,62% 0,50% 70%,0 76%)" }}>
        <MhArt src={mhArt(D, ep.art)} pos={P.hero && P.hero.pos} /></div>
      {shards[0] && <div className="mh-shard" style={{ clipPath: "polygon(62% 0,100% 0,100% 30%,57% 34%)" }}>
        <div style={{ position: "absolute", left: "52%", top: 0, width: "48%", height: "36%" }}><MhArt src={mhArt(D, shards[0].art)} pos={shards[0].pos} /></div></div>}
      {shards[1] && <div className="mh-shard" style={{ clipPath: "polygon(57% 34%,100% 30%,100% 58%,52% 66%)" }}>
        <div style={{ position: "absolute", left: "48%", top: "28%", width: "52%", height: "40%" }}><MhArt src={mhArt(D, shards[1].art)} pos={shards[1].pos} /></div></div>}
      {P.below && <div className="mh-shard" data-dim="" style={{ clipPath: "polygon(0 76%,50% 70%,52% 66%,100% 58%,100% 100%,0 100%)" }}>
        <MhArt src={mhArt(D, P.below.art)} pos={P.below.pos} /></div>}
      <svg className="mh-shardlines" viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true">
        {[[62, 0, 50, 70], [62, 0, 100, 0], [57, 34, 100, 30], [52, 66, 100, 58], [0, 76, 50, 70]].map((l, i) =>
          <line key={i} x1={l[0]} y1={l[1]} x2={l[2]} y2={l[3]} vectorEffect="non-scaling-stroke" />)}
      </svg>
      <div className="mh-storyfoot" aria-hidden="true" />
      {shards[0] && <div style={{ position: "absolute", left: 300, top: 190 }}><MhSceneTag>{shards[0].tag}</MhSceneTag></div>}
      {shards[1] && <div style={{ position: "absolute", left: 300, top: 330 }}><MhSceneTag>{shards[1].tag}</MhSceneTag></div>}
      <div style={{ position: "absolute", left: 18, top: 60 }}><MhSceneTag>{ep.code} · {ep.title}</MhSceneTag></div>
      {/* the owner's logo already says Urban Playground, so no "presents" line over it; it stands
          ~100px taller than the typeset lockup it replaced, hence higher and a touch smaller */}
      <div className="mh-storylock" style={{ top: 380 }}><MhTitleLockup size={86} center /></div>
      <div className="mh-storybill" style={{ bottom: 18 }}>
        <MhStoryBilling D={D} X={X} />
        <div className="mh-storywhen">
          <MhLabel tone="peach">Every {mhDays()} · {MH.time}</MhLabel>
          {first && <MhLabel tone="sand">From {mhDay(first)}</MhLabel>}
        </div>
      </div>
      <img className="mh-storylogo" src={D.logo || "up-logo-tight.png"} alt="Urban Playground" style={{ right: 18, top: 16, height: 26 }} />
    </MhStoryFrame>
  );
}

// ── 19 CONTENDERS ─────────────────────────────────────────────────────────
function MhStoryContenders({ D }) {
  const X = mhDerive(D);
  const C = (MH.stories || {}).contenders || {};
  const [a, b, c] = X.players;                           // #1, #2, #3
  const gap = a.points - b.points;
  const Panel = ({ p, big }) => (
    <div className="mh-contender" style={{ flex: big ? 1.35 : 1, marginTop: big ? 0 : 26 }}>
      <MhArt src={p.photo} pos={p.pos} />
      <div className="mh-contfade" aria-hidden="true" />
      <div className="mn-display mh-contname" style={{ fontSize: big ? 17 : 14 }}>{mhFirst(p.name).toUpperCase()}</div>
    </div>
  );
  return (
    <MhStoryFrame label={`${MH.name}: the top three`}>
      <div style={{ position: "absolute", inset: 0 }}><MhArt src={mhArt(D, C.art)} pos={C.pos} /></div>
      <div className="mh-contback" aria-hidden="true" />
      <div className="mh-conttag mn-serif">Three contenders. {mhWords(gap)} point{gap === 1 ? "" : "s"}.<br />One {MH.month}.</div>
      <div className="mh-controw"><Panel p={b} /><Panel p={a} big /><Panel p={c} /></div>
      <div className="mh-storylock" style={{ top: 484 }}><MhTitleLockup size={68} center meta={false} /></div>
      <div className="mh-storybill" style={{ bottom: 16 }}><MhStoryBilling D={D} X={X} /></div>
      <img className="mh-storylogo" src={D.logo || "up-logo-tight.png"} alt="Urban Playground" style={{ left: 18, top: 14, height: 24 }} />
    </MhStoryFrame>
  );
}

// ── MY CARD ───────────────────────────────────────────────────────────────
// The handoff names it ("Share → share sheet MY CARD") but draws no artboard,
// so this is composed from the New Crew Card moment it is shared from: the
// player's own art blurred under the gold glow, the card L, the lockup and
// the address. A proposal until the owner says otherwise.
function MhStoryCard({ D, id }) {
  const X = mhDerive(D);
  const p = X.byId[id] || X.me;
  return (
    <MhStoryFrame label={`${p.name}'s crew card`}>
      <MhMomentBack src={p.photo} pos={p.heroPos || p.pos} dim={.6} glow="gold" at="50% 40%" />
      <div className="mh-mycard">
        <MhLabel tone="peach">My crew card · {MH.volumeLabel}</MhLabel>
        <MhCrewCard player={{ name: p.name, photo: p.photo, photoPos: p.meCardPos || p.pos }} rank={p.rank} points={p.points}
          rep={p.rep} size="L" stats={p.stats || {}} tilt={false} />
        {/* the logo is taller than the typeset lockup was, and its meta line repeats the
            label above the card: without it the address cleared the frame again */}
        <div style={{ marginTop: 10 }}><MhTitleLockup size={58} center meta={false} /></div>
        <MhLabel tone="sand" style={{ marginTop: 4 }}>{(MH.stories || {}).url || MH.host}</MhLabel>
      </div>
      <img className="mh-storylogo" src={D.logo || "up-logo-tight.png"} alt="Urban Playground" style={{ left: 18, top: 14, height: 24 }} />
    </MhStoryFrame>
  );
}

// ── the export ────────────────────────────────────────────────────────────
// html-to-image is loaded only when somebody exports: no screen pays for it.
// Pinned to an exact version, like every script this club loads.
const MH_H2I = "https://unpkg.com/html-to-image@1.11.11/dist/html-to-image.js";
function mhLoadH2I() {
  if (window.htmlToImage) return Promise.resolve(window.htmlToImage);
  return new Promise((ok, no) => {
    const s = document.createElement("script"); s.src = MH_H2I;
    s.onload = () => ok(window.htmlToImage); s.onerror = () => no(new Error("export library failed to load"));
    document.head.appendChild(s);
  });
}
// The node is the 416x740 frame — the handoff's artboard, which is not quite
// 9:16. At 1080/416 it would be 1080 x 1921.2; the canvas is set to exactly
// 1080x1920 and the frame is drawn into it, a 0.06% vertical squeeze that no
// eye can see and that keeps the file to Instagram's own size.
async function mhExportStory(node) {
  const h = await mhLoadH2I();
  await document.fonts.ready;
  const k = MH_STORY.outW / MH_STORY.w;
  const canvas = await h.toCanvas(node, { width: MH_STORY.w, height: MH_STORY.h, pixelRatio: k,
    canvasWidth: MH_STORY.outW / k, canvasHeight: MH_STORY.outH / k, cacheBust: false,
    // one image that fails to load must not lose the whole card: html-to-image
    // rejects outright, and the line-up came back with NOTHING when the logo 404'd
    imagePlaceholder: "data:image/gif;base64,R0lGODlhAQABAAAAACH5BAEKAAEALAAAAAABAAEAAAICTAEAOw==" });
  return new Promise(r => canvas.toBlob(r, "image/png"));
}

// ── the share sheet ───────────────────────────────────────────────────────
const MH_SHARES = [["card", "My card"], ["poster", "Campaign poster"], ["contenders", "Contenders"]];
function MhShareSheet({ D, go, what = "card", id }) {
  const shares = what === "loot" ? [["loot", "Knockout card"], ...MH_SHARES] : MH_SHARES;
  const [k, setK] = React.useState(shares.some(s => s[0] === what) ? what : "card");
  const [busy, setBusy] = React.useState(false), [err, setErr] = React.useState("");
  const ref = React.useRef(null);
  const name = { loot: "knockout-card", card: "my-card", poster: "campaign-poster", contenders: "contenders" }[k];
  const me = D.players && D.players.find(p => p.id === (id ? String(id).split(".")[0] : D.meId));
  const caption = { loot: `My ${MH.name || "Muscat Heist"} knockout card.`, card: me ? `${me.name} · #${me.rank} on Most Wanted · ${me.points} pts.` : `${MH.name || "Muscat Heist"}.`,
    poster: `${MH.name || "Muscat Heist"} — nine nights at ${MH.venue || "Al Hail North"}.`, contenders: `${MH.name || "Muscat Heist"} — the contenders.` }[k];
  const run = async () => {
    setBusy(true); setErr("");
    try {
      const blob = await mhExportStory(ref.current.firstChild);
      window.__mhLastExport = blob;                       // for the harness
      await mhShareOut(blob, `muscat-heist-${name}.png`, caption);
    } catch (e) { if (e && e.name !== "AbortError") setErr("Couldn't make the image. Try again."); }
    setBusy(false);
  };
  return (
    <div className="mh-page">
      <main className="mh-body" data-bare="" style={{ padding: "56px 20px 0", display: "flex", flexDirection: "column", minHeight: "100dvh" }}>
        <div className="mh-split">
          <MhLabel>Share</MhLabel>
          <button type="button" className="mh-close mn-serif" onClick={() => go("back")}>close ✕</button>
        </div>
        <div style={{ marginTop: 10 }}><MhPills label="What to share" items={shares} value={k} onChange={setK} /></div>
        <div className="mh-sharepreview">
          <div ref={ref} className="mh-sharescale">
            {k === "loot" ? <MhStoryLoot D={D} id={id} /> : k === "card" ? <MhStoryCard D={D} id={id && id.split(".")[0]} /> : k === "poster" ? <MhStoryPoster D={D} /> : <MhStoryContenders D={D} />}
          </div>
        </div>
        <MhLabel style={{ textAlign: "center" }}>1080 × 1920 · Instagram story</MhLabel>
        {err && <MhSerif size={14} tone="coral" style={{ textAlign: "center" }}>{err}</MhSerif>}
        <div className="mh-momentfoot" style={{ padding: "12px 0 26px" }}>
          <MhButton live onClick={run} disabled={busy}>{busy ? "Making the image…" : "Share image"}</MhButton>
          {typeof MhWhatsApp === "function" && <MhWhatsApp text={caption} label="Send the link on WhatsApp" />}
        </div>
      </main>
    </div>
  );
}
