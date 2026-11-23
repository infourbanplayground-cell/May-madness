// MUSCAT HEIST · Vol.10 — the shared components (handoff components.md).
// Plain JSX for Babel standalone, the way every volume's page is compiled.
// Every colour is a token in heist.css; nothing here carries a hex value.
// Images always come from data — player.photo, session.art — never a path
// written into a component, so real art replaces the placeholders with no
// code change (handoff rule 10).

const MH = window.MH_SEASON || {};

// ── derived rules (handoff data.md), as data ──────────────────────────────
// REP IS PER NIGHT PLAYED (owner, 22 Nov 2026): the threshold for a level is
// its per-night figure times the nights the season has played, so after five
// nights it is exactly the handoff's 80 / 90 / 100. Rep never goes down: a
// player's level is the highest they reached after ANY night, which is why
// this takes their running totals, not just today's.
const MH_REPS = (MH.rep && MH.rep.levels) || [];
function mhRepAt(points, nights) {
  return MH_REPS.find(l => points >= l.perNight * nights) || MH_REPS[MH_REPS.length - 1];
}
// totalsByNight: the player's series total after night 1, 2, ... n
function mhRepFor(totalsByNight) {
  let best = MH_REPS.length - 1;
  (totalsByNight || []).forEach((pts, i) => {
    const k = MH_REPS.indexOf(mhRepAt(pts, i + 1));
    if (k < best) best = k;
  });
  return MH_REPS[best];
}
function mhNextRep(rep) {
  const k = MH_REPS.indexOf(rep);
  return k > 0 ? MH_REPS[k - 1] : null;
}
const mhTierFor = rank => (MH.tiers || []).find(t => rank <= t.maxRank) || (MH.tiers || [])[0];
const mhInitials = name => (name || "?").split(/\s+/).map(w => w[0]).join("").slice(0, 2).toUpperCase();

// ── the art treatment: one component, so every picture is graded alike ────
function MhArt({ src, alt = "", pos = "center 25%", name }) {
  return (
    <div className="mn-art">
      {src ? <img src={src} alt={alt} style={{ objectPosition: pos }} loading="lazy" decoding="async" />
           : <div className="mn-initials" style={{ fontSize: "2.2em" }}>{mhInitials(name)}</div>}
    </div>
  );
}

// ── labels ────────────────────────────────────────────────────────────────
const MhLabel = ({ children, tone, style }) => (
  <div className="mn-label" style={{ color: tone ? `var(--mn-${tone})` : undefined, ...style }}>{children}</div>
);
const MhSerif = ({ children, size = 15, tone, style }) => (
  <div className="mn-serif" style={{ fontSize: size, color: tone ? `var(--mn-${tone})` : undefined, ...style }}>{children}</div>
);
const MhDisplay = ({ children, size = 28, weight = 900, tone, style }) => (
  <div className="mn-display" style={{ fontSize: size, fontWeight: weight, lineHeight: 1, color: tone ? `var(--mn-${tone})` : undefined, ...style }}>{children}</div>
);

// ── glass card ────────────────────────────────────────────────────────────
function MhGlass({ accent, as: Tag = "div", children, style, ...rest }) {
  return <Tag className="mn-glass" data-accent={accent} style={style} {...rest}>{children}</Tag>;
}

// ── pills ─────────────────────────────────────────────────────────────────
function MhPills({ items, value, onChange, round, label }) {
  return (
    <div className="mn-pills" role="group" aria-label={label}>
      {items.map(it => {
        const [k, text] = Array.isArray(it) ? it : [it, it];
        return (
          <button key={k} type="button" className="mn-pill" data-round={round ? "" : undefined}
            aria-pressed={value === k} onClick={() => onChange && onChange(k)}><span>{text}</span></button>
        );
      })}
    </div>
  );
}

// ── buttons ───────────────────────────────────────────────────────────────
function MhButton({ kind = "primary", live, children, style, ...rest }) {
  return <button type="button" className={"mn-btn mn-btn-" + kind} data-size={live ? "live" : undefined}
    style={style} {...rest}>{children}</button>;
}

// ── top bar: the UP logo and the volume line, over every screen ──────────
function MhTopBar({ logo, line }) {
  return (
    <div className="mn-topbar">
      <img src={logo} alt="Urban Playground" />
      <div className="mn-serif">{line}</div>
    </div>
  );
}

// ── bottom nav ────────────────────────────────────────────────────────────
const MH_TABS = [["home", "Home"], ["jobs", "Jobs"], ["wanted", "Wanted"], ["me", "Me"], ["crew", "Crew"]];
function MhBottomNav({ tab, onTab }) {
  return (
    <nav className="mn-nav" aria-label="Sections">
      {MH_TABS.map(([k, label]) => (
        <button key={k} type="button" className="mn-navtab" aria-current={tab === k ? "page" : undefined}
          onClick={() => onTab && onTab(k)}><span>{label}</span></button>
      ))}
    </nav>
  );
}

// ── hero cut ──────────────────────────────────────────────────────────────
// The keyline is an SVG line in the hero's own coordinates, so it lands on
// the cut at any width. The static design positions a rotated div by
// measured pixels, which is right at 375 and wrong at every other phone.
// cut = [right edge %, left edge %] of the bottom edge, top to bottom.
function MhHeroCut({ height, src, pos, cut = [82, 96], gold, children, style }) {
  const poly = `polygon(0 0,100% 0,100% ${cut[0]}%,0 ${cut[1]}%)`;
  return (
    <div className="mn-hero" data-gold={gold ? "" : undefined} style={{ height, ...style }}>
      <div className="mn-hero-img" style={{ clipPath: poly }}><MhArt src={src} pos={pos} /></div>
      <div className="mn-hero-fade" style={{ clipPath: poly }} aria-hidden="true" />
      <svg className="mn-keyline" viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true">
        <line x1="0" y1={cut[1]} x2="100" y2={cut[0]} vectorEffect="non-scaling-stroke" />
      </svg>
      {children}
    </div>
  );
}

// ── title lockup ──────────────────────────────────────────────────────────
// MUSCAT at base x .74, HEIST on the skewed coral band at base x .42.
// Sizes from the static design: S 76 (56/31 on Home), M 84 (62/35 loading),
// L 104 (poster).
const MH_LOCKUP = { S: 76, M: 84, L: 104 };
function MhTitleLockup({ size = "S", center, presents, meta }) {
  const base = MH_LOCKUP[size] || size;
  return (
    <div className="mn-lockup" data-center={center ? "" : undefined}>
      {center && <div className="mn-sun" aria-hidden="true" style={{ width: base * 1.05, height: base * 1.05 }} />}
      {presents && <div className="mn-presents" style={{ fontSize: Math.round(base * .2) }}>{presents}</div>}
      <div className="mn-l1" style={{ fontSize: Math.round(base * .74) }}>{MH.nameLine1 || "MUSCAT"}</div>
      <div className="mn-band"><span style={{ fontSize: Math.round(base * .42) }}>{MH.nameLine2 || "HEIST"}</span></div>
      {meta !== false && <div className="mn-meta">{meta || `${MH.volumeLabel} · Muscat · ${MH.monthShort} ${MH.year}`}</div>}
    </div>
  );
}

// ── scene tag ─────────────────────────────────────────────────────────────
const MhSceneTag = ({ children, gold, style }) => (
  <span className="mn-scenetag" data-gold={gold ? "" : undefined} style={style}>{children}</span>
);

// ── billing (stories) ─────────────────────────────────────────────────────
// parts: strings, and {link:"presents a"} for the dimmed linking words
function MhBilling({ parts, style }) {
  return <div className="mn-billing" style={style}>{parts.map((p, i) =>
    typeof p === "string" ? <React.Fragment key={i}>{p} </React.Fragment> : <i key={i}>{p.link} </i>)}</div>;
}

// ── avatar ────────────────────────────────────────────────────────────────
// zoom = [side, x%, y%]: the static design crops ONE face out of a
// two-person painting by blowing it up 220% x 160% and sliding it. Real
// photos are one person and never need it.
function MhAvatar({ player, size = 34, ring, zoom }) {
  const art = <MhArt src={player && player.photo} name={player && player.name} pos={player && player.photoPos} />;
  return (
    <div className="mn-avatar" style={{ width: size, height: size, fontSize: size * .18,
      boxShadow: ring ? `0 0 0 2px var(--mn-${ring})` : undefined }}>
      {zoom ? <div style={{ position: "absolute", [zoom[0]]: zoom[1] + "%", top: zoom[2] + "%", width: "220%", height: "160%" }}>{art}</div> : art}
    </div>
  );
}

// ── crew card ─────────────────────────────────────────────────────────────
// Sizes measured off the static design (width / image / tag / rank / name /
// points / body padding). The handoff's prose says image = 62% of a 1.42
// card; the drawn cards are image = .875 x width, and the drawing wins.
const MH_CARD = {
  S: { w: 120, img: 105, tag: 11, rank: 18, name: 14, pts: 13, pad: "6px 8px 8px" },
  M: { w: 150, img: 132, tag: 12, rank: 22, name: 18, pts: 15, pad: "7px 10px 10px" },
  L: { w: 240, img: 210, tag: 19, rank: 36, name: 28, pts: 24, pad: "12px 16px 16px" },
};
const MH_STATS = [["smash", "SMASH"], ["wall", "WALL"], ["speed", "SPEED"], ["clutch", "CLUTCH"]];
function MhCrewCard({ player, rank, points, rep, size = "M", stats, foil = true, tilt = true, onClick }) {
  const d = MH_CARD[size];
  const tier = mhTierFor(rank);
  const shine = foil && (tier.id === "legend" || tier.id === "elite");
  const card = (
    <div className="mn-card" data-tier={tier.id} data-tilt={tilt && size === "L" && tier.id === "legend" ? "" : undefined}
      style={{ width: d.w }}>
      <div>
        <div className="mn-card-img" style={{ height: d.img, fontSize: d.name }}>
          <MhArt src={player.photo} name={player.name} pos={player.photoPos} />
          {shine && <div className="mn-foil" aria-hidden="true" />}
          <div className="mn-card-fade" aria-hidden="true" />
          <div className="mn-tiertag" style={{ fontSize: d.tag }}>{tier.label}</div>
          <div className="mn-rank" style={{ fontSize: d.rank }}>#{rank}</div>
        </div>
        <div style={{ padding: d.pad }}>
          <div className="mn-name" style={{ fontSize: d.name }}>{player.name}</div>
          <div className="mn-repline">
            <div className="mn-rep" style={{ color: `var(--mn-rep-${rep.id})` }}>REP · {rep.label.toUpperCase()}</div>
            <div className="mn-pts" style={{ fontSize: d.pts }}>{points}</div>
          </div>
          {size === "L" && stats && (
            <div className="mn-stats">
              {MH_STATS.map(([k, label]) => {
                const v = stats[k];
                return (
                  <div key={k} className="mn-stat">
                    <span>{label}</span>
                    <span><span className="mn-fill" style={{ width: (v == null ? 0 : v) + "%", background: `var(--mn-rep-${rep.id})` }} /></span>
                    <b>{v == null ? "—" : v}</b>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
  return onClick
    ? <button type="button" className="mn-cardbtn" onClick={onClick} aria-label={`${player.name}, rank ${rank}`}>{card}</button>
    : card;
}

// ── film grain, as the static design lays over every screen ──────────────
const MhGrain = () => (
  <svg className="mn-grain" aria-hidden="true">
    <filter id="mn-grain"><feTurbulence type="fractalNoise" baseFrequency=".85" numOctaves="2" stitchTiles="stitch" />
      <feColorMatrix type="saturate" values="0" /></filter>
    <rect width="100%" height="100%" filter="url(#mn-grain)" />
  </svg>
);
