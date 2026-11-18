"""THE PLAYER CARD, Vol.9's own — `NaPlayerDetail`.

The inherited card was 4,966px at 390 wide: a 200px empty photo box, the name
twice, three stat tiles, a form block with a paragraph under it, PREVIOUS
SERIES with a row for every volume including the three the player scored 0
in, four more tiles (MATCH / KNOCKOUT / TOP OF GROUP / STREAK) repeating what
"where the points came from" says a screen later, a box of W/P counts, the
loyalty lockout, a rivalries list of every opponent, badges, the night tiles —
and at the very bottom, below all of it, the all-time plate and the one thing
somebody opens a card to do: compare.

The order here is the order people ask in:
  1. who and how good  — the arch photo beside rank, points, win rate, nights,
                          and the form as one row of dots
  2. HEAD TO HEAD       — the primary action, at the top, opening the sheet with
                          this player already picked (and you, if you are a
                          player, as the other side)
  3. all-time           — the ivory plate
  4. this season        — where the points came from + the nights, one line of
                          W–L by stage
  5. the rest, FOLDED   — rivalries, badges, previous volumes (non-zero only),
                          each a row that opens. Nothing is deleted; it is just
                          not all open at once.

Every figure is the app's own engine: calcPlayerNights, calcRivals,
getMilestones, recentForm. Nothing is re-derived here.

Plain JS, not an f-string: JSX is all braces.
"""

JS = r'''
// ══ VOL.9 · THE PLAYER CARD (national_player.py) ══════════════════════════
function NaFold({ title, count, children }) {
  const [open, setOpen] = React.useState(false);
  return (
    <div className="na-fold" data-open={open ? "1" : "0"}>
      <button className="na-foldhead" onClick={() => setOpen(o => !o)} aria-expanded={open}>
        <span className="na-foldt">{title}</span>
        {count != null && <span className="na-foldn">{count}</span>}
        <span className="na-foldc" aria-hidden="true">{open ? "−" : "+"}</span>
      </button>
      {open && <div className="na-foldbody">{children}</div>}
    </div>
  );
}

function NaPlayerDetail({ playerId, state, leaderboard, canScore, sync, syncErr, update, onClose, meId }) {
  const player = state.players.find(p => p.id === playerId);
  const entry = leaderboard.find(l => l.player.id === playerId);
  const [uploading, setUploading] = React.useState(false);
  const [receipt, setReceipt] = React.useState(null);
  const [vs, setVs] = React.useState(false);
  const players = state.players || [];
  const sessions = state.sessions || [];
  const nameOf = React.useCallback((s, teamId, pidDirect) => {
    if (pidDirect) return (players.find(p => p.id === pidDirect) || {}).name || "?";
    const t = (s.teams || []).find(x => x.id === teamId);
    if (!t) return "?";
    const n = id => ((players.find(p => p.id === id) || {}).name || "?").split(" ")[0];
    return n(t.p1Id) + " & " + n(t.p2Id);
  }, [players]);
  const ranks = React.useMemo(() => rankByNight(players, sessions), [players, sessions]);
  if (!player || !entry) return null;

  const rank = leaderboard.findIndex(l => l.player.id === playerId) + 1;
  const st = entry.stats;
  const form = recentForm(playerId, sessions);
  const dec = st.groupPlayed + st.qfReached + st.sfReached + st.finalsReached;
  const wins = st.groupWins + st.qfWins + st.sfWins + st.finalsWon;
  const winRate = dec ? Math.round(wins / dec * 100) : 0;
  const streak = currentStreak(form);
  const data = calcPlayerNights(player.id, sessions, nameOf);
  const best = Math.max(1, ...data.nights.map(n => n.nightTotal));
  const rivals = calcRivals(playerId, sessions);
  const badges = getMilestones(entry);
  const locked = Array.from(getLockedPartners(playerId, sessions))
    .map(id => (players.find(p => p.id === id) || {}).name).filter(Boolean);
  const prevPts = player.prevSeriesPts || {};
  const prev = (state.prevSeriesNames || []).map(n => [n, Number(prevPts[n]) || 0]).filter(([, v]) => v > 0);
  if (player.prevSeriesPoints > 0) prev.push(["Earlier", player.prevSeriesPoints]);
  const prevSum = prev.reduce((a, [, v]) => a + v, 0);
  const initials = (player.name || "?").split(" ").map(x => x[0]).join("").slice(0, 2).toUpperCase();
  const other = meId && meId !== player.id ? meId : null;
  const stage = [["Group", st.groupWins, st.groupPlayed], ["QF", st.qfWins, st.qfReached],
                 ["SF", st.sfWins, st.sfReached], ["Final", st.finalsWon, st.finalsReached]]
    .filter(([, , p]) => p > 0);

  const upload = async (e) => {
    const f = e.target.files?.[0]; if (!f) return;
    setUploading(true);
    try {
      const branded = await buildBrandAvatar(f);
      if (branded) {
        update(s => ({ ...s, players: s.players.map(p => p.id === playerId ? { ...p, photoUrl: branded } : p) }));
      } else {
        const b64 = await resizeToBase64(f);
        update(s => ({ ...s, players: s.players.map(p => p.id === playerId ? { ...p, photoUrl: b64 } : p) }));
        await uploadPhotoToServer(playerId, b64);
      }
    } catch {}
    setUploading(false);
  };

  return <Modal open={true} onClose={onClose} title={player.name.toUpperCase()}>
    <div className="na-pd">
      {canScore && <div className="flex justify-end -mt-1 mb-2"><SyncIndicator status={sync} errMsg={syncErr} /></div>}

      <div className="na-pdhero">
        <div className="na-pdphoto">
          {player.photoUrl ? <img src={player.photoUrl} alt={player.name} /> : <span>{initials}</span>}
          {canScore && <label className="na-pdcam" title="Change photo">
            {uploading ? "…" : <I.camera size={15} />}
            <input type="file" accept="image/*" className="hidden" onChange={upload} />
          </label>}
        </div>
        <div className="na-pdid">
          <div className="na-pdchips">
            <span className="na-pdchip">RANK {rank}</span>
            {streak > 0 && <span className="na-pdchip" data-hot={streak >= 3 ? "1" : "0"}>W{streak}</span>}
          </div>
          <div className="na-pdstats">
            <div><b>{entry.totalPts}</b><i>POINTS</i></div>
            <div><b>{winRate}%</b><i>WON</i></div>
            <div><b>{st.sessionsPlayed}</b><i>NIGHT{st.sessionsPlayed === 1 ? "" : "S"}</i></div>
          </div>
          {form.length > 0 && <div className="na-pdform" aria-label={"Form, most recent last: " + form.join(" ")}>
            {form.map((r, i) => <span key={i} data-w={r === "W" ? "1" : "0"}>{r}</span>)}
          </div>}
        </div>
      </div>

      <div className="na-pdacts">
        <button className="na-pdh2h" onClick={() => setVs(true)}>
          <span>HEAD TO HEAD</span>
          <small>{other ? "You v " + player.name.split(" ")[0] : "Pick anyone to compare"}</small>
        </button>
        <button className="na-pdcopy" onClick={() => {
          navigator.clipboard?.writeText(generatePlayerCard(entry, state));
          alert("Player card copied — paste it in WhatsApp.");
        }}>Copy card</button>
      </div>

      <NaAllTime player={player} state={state} meId={meId} onCompare={null} />

      {data.nights.length > 0 && <div className="na-pdsec">
        <div className="na-pdk">THIS SEASON</div>
        <StackedBar seg={data.seg} total={data.total} />
        <SegLegend seg={data.seg} />
        <div className="na-pdnights">
          {data.nights.slice(-5).map(n => (
            <button key={n.id} onClick={() => setReceipt(n)}>
              <i>S{n.no}</i><b>+{n.nightTotal}</b>
              <span><span style={{ width: Math.round(n.nightTotal / best * 100) + "%" }} /></span>
            </button>
          ))}
        </div>
        {stage.length > 0 && <div className="na-pdstage">
          {stage.map(([k, w, p]) => <span key={k}>{k} <b>{w}&ndash;{p - w}</b></span>)}
        </div>}
      </div>}

      <div className="na-pdfolds">
        {rivals.length > 0 && <NaFold title="Rivals this season" count={rivals.length}>
          {rivals.map(r => {
            const opp = players.find(p => p.id === r.id); if (!opp) return null;
            return <div key={r.id} className="na-pdrow"><span>{opp.name}</span><b>{r.wins}&ndash;{r.losses}</b></div>;
          })}
        </NaFold>}
        {badges.length > 0 && <NaFold title="Badges" count={badges.length}>
          <div className="na-pdbadges">{badges.map(m => <span key={m.id} title={m.desc}>{m.icon} {m.label}</span>)}</div>
        </NaFold>}
        {prev.length > 0 && <NaFold title="Earlier volumes" count={prevSum + " pts"}>
          {prev.map(([n, v]) => <div key={n} className="na-pdrow"><span>{n}</span><b>{v}</b></div>)}
        </NaFold>}
        {locked.length > 0 && <div className="na-pdlock">Can&rsquo;t partner again &middot; {locked.join(", ")}</div>}
      </div>
    </div>
    {vs && <NaVsSheet state={state} a0={player.id} b0={other || undefined} onClose={() => setVs(false)} />}
    <ReceiptSheet night={receipt} player={player}
      rankAfter={receipt ? (ranks[receipt.idx] || {})[player.id] : null}
      onClose={() => setReceipt(null)} />
  </Modal>;
}
'''
