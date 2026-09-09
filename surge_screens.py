# -*- coding: utf-8 -*-
"""Vol.7 screen rebuilds: HOME, SESSIONS and RANK, from the Claude Design canvas.

Imported by build-september-surge-app.py. These replace whole view functions
rather than re-skinning them, because the canvas changes what each screen is
made of, not just how it is painted. Everything they render still comes from
the existing engine — no scoring, API or routing change.

Three places where the canvas and this app's format disagreed, and what was
done instead (the owner was asked; these are the answers):

  · RANK's sort chips replaced the SERIES / ALL-TIME toggle. All-time is the
    carry-over — every player's August total lives there — so it stays, as a
    fourth chip: POINTS / WIN RATE / STREAK / ALL-TIME.
  · The canvas adds a PLAYERS tab. Not built; profiles still open from RANK.
  · The hero's player count is players who have played a Vol.7 session, not
    the 122-name roster the carry-over created.

And one the canvas simply got wrong: its scoring ladder reads "Knockout win
+5, Session champion +8", which is not this app's scoring. The real ladder is
rendered instead — group results 3/2/1/0, +1 for topping a group, +1/+2/+3 for
reaching QF/SF/final plus the match points, +5 more for winning it, and a 2x
night doubling all of it.
"""

# ── HOME ───────────────────────────────────────────────────────────────────
HOME_FN = r'''function DashboardView({ state, leaderboard, setTab, setOpenSessionId, isAdmin, meId, onOpenPicker }) {
  const sessions = state.sessions || [];
  const nextUp  = sessions.find(s => !s.completed);
  const live    = nextUp || sessions[sessions.length - 1];
  const allDone = !nextUp;

  // "Players" here means people who have actually played a Vol.7 session —
  // not the roster, which carries every August name across with its points.
  const played = leaderboard.filter(l => l.stats.groupPlayed > 0 || l.stats.qfReached > 0);
  const podium = played.slice(0, 3);
  const sessionVoucher = 14, perTeam = 2, sessionsTotal = 9, season = [75, 45, 30];
  const pool = sessionVoucher * perTeam * sessionsTotal + season.reduce((a, b) => a + b, 0);

  const enrich = (e) => {
    const form = recentForm(e.player.id, sessions);
    const decided = e.stats.groupPlayed + e.stats.qfReached + e.stats.sfReached + e.stats.finalsReached;
    const wins = e.stats.groupWins + e.stats.qfWins + e.stats.sfWins + e.stats.finalsWon;
    return { form, streak: currentStreak(form), decided,
             winRate: decided ? Math.round(wins / decided * 100) : 0 };
  };

  // Movement since the previous session, for the climber tile.
  const climber = (() => {
    if (sessions.length < 2) return null;
    const prev = sessions.slice(0, -1);
    const before = state.players
      .map(p => ({ id: p.id, s: calcPlayerStats(p.id, prev) }))
      .filter(e => e.s.stats.groupPlayed > 0 || e.s.stats.qfReached > 0)
      .sort((a, b) => b.s.totalPts - a.s.totalPts);
    const rank = {}; before.forEach((e, i) => { rank[e.id] = i; });
    let best = null;
    played.forEach((e, i) => {
      if (!(e.player.id in rank)) return;
      const d = rank[e.player.id] - i;
      if (d > 0 && (!best || d > best.n)) best = { e, n: d };
    });
    return best && best.n >= 2 ? best : null;
  })();

  // Best win rate among players with enough matches to mean something.
  const bestRate = (() => {
    const pool2 = played.map(e => ({ e, en: enrich(e) })).filter(x => x.en.decided >= 5);
    if (!pool2.length) return null;
    return pool2.sort((a, b) => b.en.winRate - a.en.winRate || b.e.totalPts - a.e.totalPts)[0];
  })();

  const LADDER = [
    ["Group win",            "+3", "#00E5FF"],
    ["Tiebreak loss",        "+2", "#F4F9FA"],
    ["Close loss",           "+1", "#F4F9FA"],
    ["Blowout loss",          "0", "#9FB0BC"],
    ["Top of your group",    "+1", "#00E5FF"],
    ["Reach QF / SF / final","+1 / +2 / +3", "#00E5FF"],
    ["Win the final",        "+5", "#FF9E1B"],
  ];

  const liveMatches = live ? (live.groupMatches || []) : [];
  const donePct = liveMatches.length
    ? Math.round(liveMatches.filter(m => m.winner).length / liveMatches.length * 100) : 0;

  return (
    <div className="space-y-4" style={{animation:"sgSlide 200ms var(--ease-out) both"}}>

      {/* ── HERO ── */}
      <div className="sg-hero" style={{position:"relative",marginTop:16,padding:"26px 18px",
           background:"rgba(5,7,9,.9)",border:"1px solid rgba(0,229,255,.28)",overflow:"hidden"}}>
        <div style={{position:"absolute",right:-16,top:-40,fontFamily:"'Archivo',sans-serif",fontStyle:"italic",
             fontVariationSettings:"'wdth' 125,'wght' 900",fontSize:170,lineHeight:1,
             color:"rgba(0,229,255,.06)",pointerEvents:"none"}}>07</div>
        <div style={{position:"relative",fontFamily:"'Archivo',sans-serif",fontWeight:800,fontSize:9,
             letterSpacing:".34em",color:"#00E5FF"}}>MON &amp; WED · 5:30 PM · ALL SEPTEMBER</div>
        <div style={{position:"relative",fontFamily:"'Archivo',sans-serif",fontStyle:"italic",
             fontVariationSettings:"'wdth' 125,'wght' 900",fontSize:46,lineHeight:.9,
             color:"#F4F9FA",marginTop:10}}>RIDE THE<br /><span style={{color:"#00E5FF"}}>SURGE.</span></div>
        <div style={{position:"relative",display:"flex",gap:8,marginTop:16}}>
          <div style={{flex:1,padding:"10px 12px",background:"rgba(0,229,255,.08)",border:"1px solid rgba(0,229,255,.3)"}}>
            <div style={{fontFamily:"'Archivo',sans-serif",fontWeight:800,fontSize:8,letterSpacing:".22em",color:"#9FB0BC"}}>PRIZE POOL</div>
            <div style={{fontFamily:"'Archivo',sans-serif",fontStyle:"italic",fontVariationSettings:"'wdth' 112,'wght' 900",
                 fontSize:22,color:"#00E5FF",marginTop:2}}>{pool} OMR</div>
          </div>
          <div style={{flex:1,padding:"10px 12px",background:"rgba(255,158,27,.08)",border:"1px solid rgba(255,158,27,.3)"}}>
            <div style={{fontFamily:"'Archivo',sans-serif",fontWeight:800,fontSize:8,letterSpacing:".22em",color:"#9FB0BC"}}>PLAYERS</div>
            <div style={{fontFamily:"'Archivo',sans-serif",fontStyle:"italic",fontVariationSettings:"'wdth' 112,'wght' 900",
                 fontSize:22,color:"#FF9E1B",marginTop:2}}>{played.length}</div>
          </div>
        </div>
      </div>

      {/* ── NEXT UP ── */}
      {live && <>
        <div className="sg-kicker">{allDone ? "Last session" : "Next up"}</div>
        <div onClick={() => setOpenSessionId(live.id)} className="sg-card sg-card-cyan"
             style={{cursor:"pointer",padding:16,marginTop:10}}>
          <div style={{display:"flex",alignItems:"center",gap:8}}>
            <div style={{fontFamily:"'Archivo',sans-serif",fontWeight:800,fontSize:9,letterSpacing:".28em",color:"#00E5FF"}}>
              {live.date ? new Date(live.date + "T12:00:00").toLocaleDateString("en-GB", {weekday:"short",day:"numeric",month:"short"}).toUpperCase() : ""}</div>
            {!live.completed && <div style={{marginLeft:"auto",display:"flex",alignItems:"center",gap:7}}>
              <span className="sg-livedot" />
              <span style={{fontFamily:"'Archivo',sans-serif",fontWeight:800,fontSize:9,letterSpacing:".2em",color:"#00E5FF"}}>LIVE NOW</span>
            </div>}
          </div>
          <div style={{display:"flex",alignItems:"center",gap:14,marginTop:12}}>
            <div style={{flex:"0 0 auto",width:56,height:56,borderRadius:"50%",display:"grid",placeItems:"center",
                 background:`conic-gradient(#00E5FF ${donePct}%, rgba(92,107,120,.22) 0)`}}>
              <div style={{width:44,height:44,borderRadius:"50%",background:"#050709",display:"grid",placeItems:"center",
                   fontFamily:"'Archivo',sans-serif",fontStyle:"italic",fontVariationSettings:"'wdth' 118,'wght' 900",
                   fontSize:16,color:"#00E5FF"}}>{(live.name||"").replace(/[^0-9]/g,"") || "·"}</div>
            </div>
            <div style={{flex:"1 1 auto",minWidth:0}}>
              <div style={{fontFamily:"'Archivo',sans-serif",fontStyle:"italic",fontVariationSettings:"'wdth' 125,'wght' 900",
                   fontSize:26,lineHeight:1,color:"#F4F9FA"}}>{(live.name||"").toUpperCase()}</div>
              <div style={{fontFamily:"'Archivo',sans-serif",fontWeight:800,fontSize:10,letterSpacing:".16em",
                   color:"#9FB0BC",marginTop:5,whiteSpace:"nowrap"}}>
                {liveMatches.filter(m => m.winner).length} OF {liveMatches.length} PLAYED
                {live.doublePoints ? " · 2X POINTS" : ""}</div>
            </div>
            <div style={{flex:"0 0 auto",fontFamily:"'Archivo',sans-serif",fontWeight:800,fontSize:11,color:"#00E5FF"}}>OPEN &#9654;</div>
          </div>
        </div>
      </>}

      {/* ── WHO ARE YOU — only until it is answered ── */}
      {!meId && <div onClick={onOpenPicker} className="sg-card"
           style={{cursor:"pointer",padding:"13px 14px",display:"flex",alignItems:"center",gap:10}}>
        <div style={{flex:1,minWidth:0}}>
          <div className="sg-kicker" style={{marginBottom:3}}>Your standing</div>
          <div style={{fontFamily:"'Archivo',sans-serif",fontStyle:"italic",fontVariationSettings:"'wdth' 112,'wght' 900",
               fontSize:18,color:"#F4F9FA"}}>WHICH ONE ARE YOU?</div>
        </div>
        <span style={{color:"#00E5FF",fontWeight:800}}>&#9654;</span>
      </div>}

      {/* ── TOP OF THE SERIES ── */}
      {podium.length > 0 && <>
        <div style={{display:"flex",alignItems:"baseline",gap:10,marginTop:20}}>
          <div className="sg-kicker">Top of the series</div>
          <div onClick={() => setTab("leaderboard")} style={{cursor:"pointer",marginLeft:"auto",
               fontFamily:"'Archivo',sans-serif",fontWeight:800,fontSize:9,letterSpacing:".2em",color:"#00E5FF"}}>FULL TABLE &#9654;</div>
        </div>
        <div style={{display:"flex",flexDirection:"column",gap:8,marginTop:10}}>
          {podium.map((e, i) => {
            const en = enrich(e), lead = i === 0;
            const bar = lead ? "#00E5FF" : "#5C6B78";
            return <div key={e.player.id} onClick={() => setTab("leaderboard")} className="sg-top" data-lead={lead ? "1" : "0"}
              style={{cursor:"pointer",display:"flex",alignItems:"center",gap:12,padding:"13px 14px",
                      background:lead ? "rgba(16,23,31,.96)" : "rgba(9,14,20,.94)",
                      backgroundImage:`linear-gradient(180deg,${bar},rgba(92,107,120,.05))`,
                      backgroundSize:"3px 100%",backgroundRepeat:"no-repeat"}}>
              <div style={{flex:"0 0 auto",width:42,height:42,display:"grid",placeItems:"center",
                   background:lead ? "rgba(0,229,255,.14)" : "rgba(255,255,255,.04)",
                   border:`1px solid ${lead ? "rgba(0,229,255,.5)" : "rgba(92,107,120,.35)"}`,
                   fontFamily:"'Archivo',sans-serif",fontStyle:"italic",fontVariationSettings:"'wdth' 118,'wght' 900",
                   fontSize:20,lineHeight:1,color:lead ? "#00E5FF" : "#9FB0BC"}}>{i + 1}</div>
              <div style={{flex:"1 1 auto",minWidth:0}}>
                <div style={{fontFamily:"'Archivo',sans-serif",fontWeight:800,fontSize:16,color:"#F4F9FA",
                     whiteSpace:"nowrap",overflow:"hidden",textOverflow:"ellipsis"}}>{e.player.name}</div>
                <div style={{fontFamily:"'Archivo',sans-serif",fontWeight:800,fontSize:9,letterSpacing:".18em",
                     color:"#9FB0BC",marginTop:4,whiteSpace:"nowrap",overflow:"hidden",textOverflow:"ellipsis"}}>
                  {e.stats.sessionsPlayed} NIGHTS · {en.winRate}% WIN{en.streak >= 2 ? ` · W${en.streak}` : ""}</div>
              </div>
              <div style={{flex:"0 0 auto",textAlign:"right"}}>
                <div className="sg-top-pts" style={{fontFamily:"'Archivo',sans-serif",fontStyle:"italic",
                     fontVariationSettings:"'wdth' 112,'wght' 900",fontSize:24,lineHeight:1,
                     color:lead ? "#00E5FF" : "#F4F9FA"}}>{e.totalPts}</div>
                <div style={{fontFamily:"'Archivo',sans-serif",fontWeight:800,fontSize:8,letterSpacing:".24em",color:"#9FB0BC",marginTop:2}}>PTS</div>
              </div>
            </div>;
          })}
        </div>
      </>}

      {/* ── WORTH WATCHING ── */}
      {(climber || bestRate) && <>
        <div className="sg-kicker" style={{marginTop:20}}>Worth watching</div>
        <div style={{display:"grid",gridTemplateColumns:"repeat(2,minmax(0,1fr))",gap:10,marginTop:10}}>
          {climber && <div onClick={() => setTab("leaderboard")} className="sg-card" style={{cursor:"pointer",padding:14,
               backgroundImage:"linear-gradient(180deg,#00E5FF,rgba(92,107,120,.05))",backgroundSize:"3px 100%",backgroundRepeat:"no-repeat"}}>
            <div style={{fontFamily:"'Archivo',sans-serif",fontWeight:800,fontSize:8,letterSpacing:".2em",color:"#00E5FF"}}>BIGGEST CLIMBER</div>
            <div style={{fontFamily:"'Archivo',sans-serif",fontStyle:"italic",fontVariationSettings:"'wdth' 118,'wght' 900",
                 fontSize:34,lineHeight:1,color:"#00E5FF",marginTop:7}}>&#9650;{climber.n}</div>
            <div style={{fontFamily:"'Archivo',sans-serif",fontWeight:800,fontSize:14,color:"#F4F9FA",marginTop:8,
                 whiteSpace:"nowrap",overflow:"hidden",textOverflow:"ellipsis"}}>{climber.e.player.name}</div>
            <div style={{fontSize:12,lineHeight:1.4,color:"#9FB0BC",marginTop:5}}>places gained since last session</div>
          </div>}
          {bestRate && <div onClick={() => setTab("leaderboard")} className="sg-card" style={{cursor:"pointer",padding:14,
               backgroundImage:"linear-gradient(180deg,#FF9E1B,rgba(92,107,120,.05))",backgroundSize:"3px 100%",backgroundRepeat:"no-repeat"}}>
            <div style={{fontFamily:"'Archivo',sans-serif",fontWeight:800,fontSize:8,letterSpacing:".2em",color:"#FF9E1B"}}>BEST WIN RATE</div>
            <div style={{fontFamily:"'Archivo',sans-serif",fontStyle:"italic",fontVariationSettings:"'wdth' 118,'wght' 900",
                 fontSize:34,lineHeight:1,color:"#FF9E1B",marginTop:7}}>{bestRate.en.winRate}%</div>
            <div style={{fontFamily:"'Archivo',sans-serif",fontWeight:800,fontSize:14,color:"#F4F9FA",marginTop:8,
                 whiteSpace:"nowrap",overflow:"hidden",textOverflow:"ellipsis"}}>{bestRate.e.player.name}</div>
            <div style={{fontSize:12,lineHeight:1.4,color:"#9FB0BC",marginTop:5}}>from {bestRate.en.decided} matches</div>
          </div>}
        </div>
      </>}

      {/* ── HOW POINTS ARE EARNED ──
          The canvas invented values here ("Knockout win +5, Session champion
          +8"). These are the app's real ones. */}
      <div className="sg-card" style={{marginTop:20,padding:16,
           backgroundImage:"linear-gradient(180deg,#FF9E1B,rgba(255,158,27,.06))",backgroundSize:"3px 100%",backgroundRepeat:"no-repeat"}}>
        <div style={{fontFamily:"'Archivo',sans-serif",fontWeight:800,fontSize:9,letterSpacing:".32em",color:"#FF9E1B"}}>HOW POINTS ARE EARNED</div>
        <div style={{display:"grid",gridTemplateColumns:"1fr auto",marginTop:12}}>
          {LADDER.map(([label, pts, colour]) => <React.Fragment key={label}>
            <div style={{display:"flex",alignItems:"center",gap:8,padding:"9px 0",borderTop:"1px solid rgba(92,107,120,.16)"}}>
              <div style={{width:3,height:16,background:colour}} />
              <div style={{fontFamily:"'Archivo',sans-serif",fontWeight:800,fontSize:14,color:"#F4F9FA"}}>{label}</div>
            </div>
            <div style={{display:"flex",alignItems:"center",justifyContent:"flex-end",paddingLeft:12,
                 borderTop:"1px solid rgba(92,107,120,.16)",fontFamily:"'Archivo',sans-serif",fontStyle:"italic",
                 fontVariationSettings:"'wdth' 112,'wght' 900",fontSize:20,color:colour}}>{pts}</div>
          </React.Fragment>)}
        </div>
        <div style={{fontSize:12.5,lineHeight:1.5,color:"#9FB0BC",marginTop:11}}>
          Only your best three group results count, so a bigger group can never out-earn a
          smaller one. A double-points night doubles everything above.</div>
      </div>
    </div>
  );
}'''


# ── RANK ───────────────────────────────────────────────────────────────────
RANK_FN = r'''function LeaderboardView({ leaderboard, state, setOpenPlayerId, meId, onOpenPicker }) {
  const [q, setQ] = useState("");
  const [showTail, setShowTail] = useState(false);
  // Four chips, not the canvas's three. ALL-TIME is not a sort — it changes
  // which total is being ranked — but it is the carry-over, and it is not
  // being dropped to save a row.
  const [sort, setSort] = useState("points");
  const sessions = state.sessions || [];
  const hasLifetime = leaderboard.some(e => {
    const p = e.player;
    return (p.prevSeriesPoints || 0) > 0 || Object.values(p.prevSeriesPts || {}).some(v => v > 0);
  });
  const lifetime = sort === "lifetime";
  const ptsOf = (e) => lifetime ? e.lifetimePts : e.totalPts;

  const enrich = (e) => {
    const form = recentForm(e.player.id, sessions);
    const decided = e.stats.groupPlayed + e.stats.qfReached + e.stats.sfReached + e.stats.finalsReached;
    const wins = e.stats.groupWins + e.stats.qfWins + e.stats.sfWins + e.stats.finalsWon;
    return { form, streak: currentStreak(form), decided,
             winRate: decided ? Math.round(wins / decided * 100) : 0 };
  };

  const hasPlayed = (l) => l.stats.groupPlayed > 0 || l.stats.qfReached > 0;
  const active = leaderboard.filter(hasPlayed);
  const base = lifetime ? [...leaderboard].sort((a, b) => b.lifetimePts - a.lifetimePts) : active;
  // Win rate and streak rank the same field, only ordered differently — and
  // both need a floor, or one lucky night tops the table at 100%.
  const list = (() => {
    if (sort === "winrate")
      return [...base].map(e => ({ e, en: enrich(e) }))
        .filter(x => x.en.decided >= 5)
        .sort((a, b) => b.en.winRate - a.en.winRate || b.e.totalPts - a.e.totalPts)
        .map(x => x.e);
    if (sort === "streak")
      return [...base].map(e => ({ e, en: enrich(e) }))
        .filter(x => x.en.streak > 0)
        .sort((a, b) => b.en.streak - a.en.streak || b.e.totalPts - a.e.totalPts)
        .map(x => x.e);
    return base;
  })();

  // Movement, season view only — an all-time table has no "since last week".
  const prevRank = useMemo(() => {
    if (lifetime || sessions.length < 2) return null;
    const prev = sessions.slice(0, -1);
    const board = state.players
      .map(p => ({ id: p.id, s: calcPlayerStats(p.id, prev) }))
      .filter(e => e.s.stats.groupPlayed > 0 || e.s.stats.qfReached > 0)
      .sort((a, b) => b.s.totalPts - a.s.totalPts);
    const m = {}; board.forEach((e, i) => { m[e.id] = i; });
    return m;
  }, [state.players, sessions, lifetime]);
  const moveOf = (e, i) => {
    if (!prevRank || !(e.player.id in prevRank)) return null;
    const d = prevRank[e.player.id] - i;
    return d === 0 ? null : { up: d > 0, n: Math.abs(d) };
  };

  const indexed = list.map((e, i) => ({ e, i }));
  const TAIL_MAX = 3;
  const rest = indexed.slice(1);
  const restMain = rest.filter(({ e }) => ptsOf(e) > TAIL_MAX);
  const restTail = rest.filter(({ e }) => ptsOf(e) <= TAIL_MAX);
  const found = q ? indexed.filter(({ e }) => e.player.name.toLowerCase().includes(q.toLowerCase())) : [];
  const leader = list[0];
  const topPts = leader ? Math.max(1, ptsOf(leader)) : 1;
  const streakLabel = (en) => en.streak > 0 ? `W${en.streak}` : "–";

  const CHIPS = [["points","Points"],["winrate","Win rate"],["streak","Streak"]]
    .concat(hasLifetime ? [["lifetime","All-time"]] : []);

  const Row = ({ e, i }) => {
    const en = enrich(e), mv = moveOf(e, i);
    return (
      <React.Fragment>
        <div onClick={() => setOpenPlayerId(e.player.id)} className="sg-thin"
             style={{cursor:"pointer",display:"flex",alignItems:"center",gap:4,borderTop:"1px solid rgba(92,107,120,.16)"}}>
          <span style={{fontFamily:"'JetBrains Mono',monospace",fontSize:13,color:"#9FB0BC"}}>{i + 1}</span>
          {mv && <span style={{fontSize:9,color:mv.up ? "#00E5FF" : "#FF9E1B"}}>{mv.up ? "▲" : "▼"}</span>}
        </div>
        <div onClick={() => setOpenPlayerId(e.player.id)}
             style={{cursor:"pointer",padding:"9px 0",borderTop:"1px solid rgba(92,107,120,.16)",minWidth:0}}>
          <div style={{fontFamily:"'Archivo',sans-serif",fontWeight:800,fontSize:15,color:"#F4F9FA",
               whiteSpace:"nowrap",overflow:"hidden",textOverflow:"ellipsis"}}>{e.player.name}</div>
          <div style={{height:4,marginTop:5,width:`${Math.max(4, Math.round(ptsOf(e) / topPts * 100))}%`,
               background:"linear-gradient(90deg,rgba(0,229,255,.7),rgba(0,229,255,.12))"}} />
        </div>
        <div onClick={() => setOpenPlayerId(e.player.id)}
             style={{cursor:"pointer",display:"flex",alignItems:"center",justifyContent:"center",
                     borderTop:"1px solid rgba(92,107,120,.16)"}}>
          <span style={{fontFamily:"'JetBrains Mono',monospace",fontWeight:700,fontSize:12,
                color:en.streak >= 3 ? "#FF9E1B" : "#9FB0BC"}}>{streakLabel(en)}</span>
        </div>
        <div onClick={() => setOpenPlayerId(e.player.id)}
             style={{cursor:"pointer",display:"flex",alignItems:"center",justifyContent:"flex-end",
                     borderTop:"1px solid rgba(92,107,120,.16)",fontFamily:"'Archivo',sans-serif",fontStyle:"italic",
                     fontVariationSettings:"'wdth' 112,'wght' 900",fontSize:20,color:"#F4F9FA"}}>{ptsOf(e)}</div>
      </React.Fragment>
    );
  };

  return (
    <div style={{animation:"sgSlide 200ms var(--ease-out) both"}}>
      <div style={{position:"relative",padding:"20px 0 12px",overflow:"hidden"}}>
        <div style={{position:"absolute",right:-14,top:-30,fontFamily:"'Archivo',sans-serif",fontStyle:"italic",
             fontVariationSettings:"'wdth' 125,'wght' 900",fontSize:150,lineHeight:1,
             color:"rgba(0,229,255,.06)",pointerEvents:"none"}}>07</div>
        <div style={{position:"relative",fontFamily:"'Archivo',sans-serif",fontWeight:800,fontSize:10,
             letterSpacing:".34em",textTransform:"uppercase",color:"#00E5FF"}}>
          Series standings · {active.length} players</div>
        <div style={{position:"relative",fontFamily:"'Archivo',sans-serif",fontStyle:"italic",
             fontVariationSettings:"'wdth' 125,'wght' 900",fontSize:50,lineHeight:.88,color:"#F4F9FA",marginTop:8}}>RANKINGS</div>
        <div style={{position:"relative",height:3,marginTop:12,background:"linear-gradient(90deg,#00E5FF,rgba(0,229,255,0))"}} />
      </div>

      <div style={{display:"grid",gridTemplateColumns:`repeat(${CHIPS.length},minmax(0,1fr))`,gap:6}}>
        {CHIPS.map(([id, label]) => {
          const on = sort === id;
          return <div key={id} onClick={() => setSort(id)}
            style={{cursor:"pointer",minHeight:40,display:"grid",placeItems:"center",
                    background:on ? "rgba(0,229,255,.12)" : "rgba(9,14,20,.94)",
                    border:`1px solid ${on ? "rgba(0,229,255,.55)" : "rgba(92,107,120,.3)"}`,
                    fontFamily:"'Archivo',sans-serif",fontWeight:800,fontSize:10,letterSpacing:".16em",
                    textTransform:"uppercase",color:on ? "#00E5FF" : "#9FB0BC"}}>{label}</div>;
        })}
      </div>

      <div style={{marginTop:12}}><Input value={q} onChange={setQ} placeholder="Find a player&hellip;" /></div>

      {q ? (
        <div style={{display:"grid",gridTemplateColumns:"34px 1fr 56px 74px",marginTop:12}}>
          {found.length === 0
            ? <div style={{gridColumn:"1 / -1",padding:"18px 4px",fontFamily:"'JetBrains Mono',monospace",
                     fontSize:11,letterSpacing:".1em",color:"#9FB0BC",textTransform:"uppercase"}}>No ranked player by that name</div>
            : found.map(({ e, i }) => <Row key={e.player.id} e={e} i={i} />)}
        </div>
      ) : !leader ? (
        <Card className="p-8 text-center border-dashed" style={{marginTop:14}}>
          <I.trophy className="mx-auto mb-3 text-stone-600" size={32} />
          <div className="text-stone-300 font-semibold">Ranking locked</div>
          <div className="text-stone-500 text-sm mt-1">Standings appear after the first match is played</div>
        </Card>
      ) : (<>
        {/* ── LEADER ── */}
        {(() => {
          const en = enrich(leader);
          return <div onClick={() => setOpenPlayerId(leader.player.id)} className="sg-top" data-lead="1"
            style={{cursor:"pointer",position:"relative",marginTop:12,padding:"16px 14px",
                    background:"rgba(16,23,31,.96)",backgroundImage:"linear-gradient(180deg,#00E5FF,rgba(0,229,255,.06))",
                    backgroundSize:"3px 100%",backgroundRepeat:"no-repeat",overflow:"hidden"}}>
            <div style={{position:"relative",display:"flex",alignItems:"center",gap:12}}>
              <div style={{flex:"0 0 auto",width:48,height:48,display:"grid",placeItems:"center",
                   background:"rgba(0,229,255,.14)",border:"1px solid rgba(0,229,255,.5)",
                   boxShadow:"0 0 26px rgba(0,229,255,.22)",fontFamily:"'Archivo',sans-serif",fontStyle:"italic",
                   fontVariationSettings:"'wdth' 125,'wght' 900",fontSize:22,color:"#00E5FF"}}>1</div>
              <div style={{flex:"1 1 auto",minWidth:0}}>
                <div style={{fontFamily:"'Archivo',sans-serif",fontStyle:"italic",fontVariationSettings:"'wdth' 112,'wght' 900",
                     fontSize:19,lineHeight:1.05,color:"#F4F9FA",whiteSpace:"nowrap",overflow:"hidden",textOverflow:"ellipsis"}}>
                  {leader.player.name}</div>
                <div style={{display:"flex",gap:8,marginTop:5}}>
                  <span style={{whiteSpace:"nowrap",fontFamily:"'Archivo',sans-serif",fontWeight:800,fontSize:9,
                        letterSpacing:".16em",color:"#9FB0BC"}}>{leader.stats.sessionsPlayed} SESSIONS · {en.winRate}% WIN</span>
                  {en.streak > 0 && <span style={{whiteSpace:"nowrap",fontFamily:"'Archivo',sans-serif",fontWeight:800,
                        fontSize:9,letterSpacing:".16em",color:"#00E5FF"}}>W{en.streak} STREAK</span>}
                </div>
              </div>
              <div style={{flex:"0 0 auto",textAlign:"right"}}>
                <div className="sg-top-pts" style={{whiteSpace:"nowrap",fontFamily:"'Archivo',sans-serif",fontStyle:"italic",
                     fontVariationSettings:"'wdth' 112,'wght' 900",fontSize:28,lineHeight:.9,color:"#00E5FF"}}>{ptsOf(leader)}</div>
                <div style={{fontFamily:"'Archivo',sans-serif",fontWeight:800,fontSize:8,letterSpacing:".26em",color:"#9FB0BC"}}>PTS</div>
              </div>
            </div>
            {en.form.length > 0 && <div style={{position:"relative",display:"flex",alignItems:"center",gap:6,marginTop:12,
                 paddingTop:11,borderTop:"1px solid rgba(92,107,120,.2)"}}>
              <span style={{fontFamily:"'Archivo',sans-serif",fontWeight:800,fontSize:9,letterSpacing:".26em",color:"#9FB0BC"}}>FORM</span>
              {en.form.map((r, k) => <div key={k} style={{width:14,height:6,
                   background:r === "W" ? "#00E5FF" : "rgba(92,107,120,.45)"}} />)}
            </div>}
          </div>;
        })()}

        {/* ── YOU, IN CONTEXT ── */}
        {(() => {
          const mi = meId ? list.findIndex(e => e.player.id === meId) : -1;
          if (mi < 1) return null;
          const e = list[mi], en = enrich(e), mv = moveOf(e, mi);
          const near = indexed.slice(Math.max(0, mi - 2), mi + 3);
          return <div style={{marginTop:14,padding:"13px 14px",background:"rgba(16,23,31,.96)",
               backgroundImage:"linear-gradient(180deg,#FF9E1B,rgba(255,158,27,.06))",backgroundSize:"3px 100%",
               backgroundRepeat:"no-repeat",border:"1px solid rgba(255,158,27,.4)"}}>
            <div style={{display:"flex",alignItems:"center",gap:12}}>
              <div style={{flex:"0 0 auto",width:42,height:42,display:"grid",placeItems:"center",
                   background:"rgba(255,158,27,.12)",border:"1px solid rgba(255,158,27,.5)",
                   fontFamily:"'Archivo',sans-serif",fontStyle:"italic",fontVariationSettings:"'wdth' 125,'wght' 900",
                   fontSize:18,color:"#FF9E1B"}}>{mi + 1}</div>
              <div style={{flex:"1 1 auto",minWidth:0}}>
                <div style={{display:"flex",alignItems:"center",gap:8}}>
                  <span style={{fontFamily:"'Archivo',sans-serif",fontWeight:800,fontSize:9,letterSpacing:".3em",color:"#FF9E1B"}}>YOU</span>
                  <button onClick={(ev) => { ev.stopPropagation(); onOpenPicker(); }}
                    style={{background:"none",border:"none",cursor:"pointer",padding:0,
                            fontFamily:"'JetBrains Mono',monospace",fontWeight:700,fontSize:9,
                            letterSpacing:".14em",color:"#9FB0BC"}}>NOT YOU?</button>
                </div>
                <div onClick={() => setOpenPlayerId(e.player.id)} style={{cursor:"pointer",fontFamily:"'Archivo',sans-serif",
                     fontStyle:"italic",fontVariationSettings:"'wdth' 112,'wght' 900",fontSize:18,lineHeight:1.05,
                     color:"#F4F9FA",marginTop:2,whiteSpace:"nowrap",overflow:"hidden",textOverflow:"ellipsis"}}>{e.player.name}</div>
                <div style={{fontFamily:"'Archivo',sans-serif",fontWeight:800,fontSize:9,letterSpacing:".18em",
                     color:"#9FB0BC",marginTop:4}}>{streakLabel(en)} · {en.winRate}% WIN</div>
              </div>
              <div style={{flex:"0 0 auto",textAlign:"right"}}>
                {mv && <div style={{fontFamily:"'Archivo',sans-serif",fontWeight:800,fontSize:10,
                     color:mv.up ? "#00E5FF" : "#FF9E1B"}}>{mv.up ? "▲" : "▼"}{mv.n}</div>}
                <div style={{whiteSpace:"nowrap",fontFamily:"'Archivo',sans-serif",fontStyle:"italic",
                     fontVariationSettings:"'wdth' 112,'wght' 900",fontSize:26,lineHeight:1,color:"#FF9E1B",marginTop:2}}>{ptsOf(e)}</div>
              </div>
            </div>
            <div style={{marginTop:12,paddingTop:11,borderTop:"1px solid rgba(92,107,120,.22)"}}>
              {near.map(({ e: n, i: ni }) => {
                const me = n.player.id === meId;
                return <div key={n.player.id} onClick={() => setOpenPlayerId(n.player.id)}
                  style={{cursor:"pointer",display:"flex",alignItems:"center",gap:10,padding:"5px 0"}}>
                  <div style={{flex:"0 0 auto",width:20,fontFamily:"'JetBrains Mono',monospace",fontSize:11,color:"#9FB0BC"}}>{ni + 1}</div>
                  <div style={{flex:"0 0 auto",width:2,height:14,background:me ? "#FF9E1B" : "rgba(92,107,120,.5)"}} />
                  <div style={{flex:"1 1 auto",minWidth:0,fontFamily:"'Archivo',sans-serif",fontWeight:800,fontSize:13,
                       color:me ? "#FF9E1B" : "#F4F9FA",whiteSpace:"nowrap",overflow:"hidden",textOverflow:"ellipsis"}}>{n.player.name}</div>
                  <div style={{flex:"0 0 auto",fontFamily:"'JetBrains Mono',monospace",fontSize:12,
                       color:me ? "#FF9E1B" : "#9FB0BC"}}>{ptsOf(n)}</div>
                </div>;
              })}
            </div>
          </div>;
        })()}

        {/* ── FULL TABLE ── */}
        <div style={{marginTop:18,display:"grid",gridTemplateColumns:"34px 1fr 56px 74px",
             fontFamily:"'Archivo',sans-serif",fontWeight:800,fontSize:10,letterSpacing:".2em",color:"#9FB0BC"}}>
          <div style={{paddingBottom:8}}>#</div>
          <div style={{paddingBottom:8}}>PLAYER</div>
          <div style={{paddingBottom:8,textAlign:"center"}}>STREAK</div>
          <div style={{paddingBottom:8,textAlign:"right"}}>PTS</div>
          {restMain.map(({ e, i }) => <Row key={e.player.id} e={e} i={i} />)}
          {showTail && restTail.map(({ e, i }) => <Row key={e.player.id} e={e} i={i} />)}
        </div>
        {restTail.length > 0 && !showTail &&
          <button onClick={() => setShowTail(true)}
            style={{width:"100%",textAlign:"left",background:"none",border:"none",
                    borderTop:"1px solid rgba(92,107,120,.18)",padding:"14px 4px",cursor:"pointer",
                    fontFamily:"'JetBrains Mono',monospace",fontSize:10,fontWeight:700,
                    letterSpacing:".14em",color:"#00E5FF",textTransform:"uppercase"}}>
            Show {restTail.length} more on {TAIL_MAX} pts or fewer &#9654;
          </button>}
      </>)}
    </div>
  );
}'''



# ── SESSIONS ───────────────────────────────────────────────────────────────
# Replaced whole, like the other two. The canvas draws only the list, but this
# view also owns the organiser's controls (ANNOUNCE / SIGNUP / FORMAT / + NEW)
# and four modals, so those are carried across unchanged rather than lost.
SESSIONS_FN = r'''function SessionsView({ state, update, setOpenSessionId, isAdmin, leaderboard, setTab }) {
  const [show, setShow] = useState(false);
  const [showDraft, setShowDraft] = useState(false);
  const [showAnnounce, setShowAnnounce] = useState(false);
  const [showFormat, setShowFormat] = useState(false);
  return (
    <div className="space-y-4" style={{animation:"sgSlide 200ms var(--ease-out) both"}}>
      <div className="flex items-end justify-between flex-wrap gap-x-3 gap-y-2" style={{paddingTop:18}}>
        <div>
          <div style={{fontFamily:"'Archivo',sans-serif",fontWeight:800,fontSize:10,letterSpacing:".34em",
               textTransform:"uppercase",color:"#00E5FF"}}>{state.sessions.length || 9} nights · Vol.7</div>
          <div style={{fontFamily:"'Archivo',sans-serif",fontStyle:"italic",fontVariationSettings:"'wdth' 125,'wght' 900",
               fontSize:44,lineHeight:.9,color:"#F4F9FA",marginTop:6}}>SESSIONS</div>
        </div>
        <div className="flex gap-2 flex-wrap">
          {isAdmin && <button className="jh-chipbtn" onClick={() => setShowAnnounce(true)}><CIc.megaphone size={12} /> ANNOUNCE</button>}
          {isAdmin && <button className="jh-chipbtn" onClick={() => setShowDraft(true)}><CIc.clipboard size={12} /> SIGNUP</button>}
          <button className="jh-chipbtn" onClick={() => setShowFormat(true)}><CIc.flame size={12} /> FORMAT</button>
          {isAdmin && <button className="jh-chipbtn red" onClick={() => setShow(true)}>+ NEW</button>}
        </div>
      </div>

      <div style={{display:"flex",flexDirection:"column",gap:8,marginTop:12}}>
        {state.sessions.length === 0 ? (
          <Card className="p-8 text-center border-dashed">
            <I.calendar className="mx-auto mb-3 text-stone-600" size={36} />
            <div className="text-stone-300 font-semibold mb-1">No sessions yet</div>
            {isAdmin && <><div className="text-stone-500 text-sm mb-4">Start the series by creating Session 1</div><Btn onClick={() => setShow(true)}><I.plus size={14} /> Create Session</Btn></>}
          </Card>
        ) : state.sessions.map((s, idx) => {
          // Playing order, the way the canvas shows the season — not
          // newest-first, which read as a log rather than a calendar.
          const num = idx + 1;
          const played = (s.groupMatches || []).filter(m => m.winner).length;
          const started = played > 0 || (s.teams || []).length > 0;
          const f = s.bracket && s.bracket.final;
          const champId = f && f.winner ? (f.winner === "team1" ? f.team1Id : f.team2Id) : null;
          const champ = (() => {
            if (!champId) return null;
            const t = (s.teams || []).find(x => x.id === champId); if (!t) return null;
            const nm = (id) => { const p = state.players.find(y => y.id === id); return p ? p.name.split(" ")[0] : null; };
            return [nm(t.p1Id), nm(t.p2Id)].filter(Boolean).join(" & ") || null;
          })();
          // One line saying what this night actually is.
          const note = s.completed
            ? (champ ? `Champions · ${champ}` : "Complete")
            : started ? "Group stage in progress"
            : (s.signupSlots || []).some(x => (x || "").trim()) ? "Sign-ups open"
            : s.doublePoints ? "Double points night" : "Not started";
          const liveNow = started && !s.completed;
          const noteColour = liveNow ? "#00E5FF" : "#9FB0BC";
          const pill = s.completed ? "FINAL" : liveNow ? "LIVE" : s.doublePoints ? "2X" : "SOON";
          const pc = pill === "LIVE" ? "#00E5FF" : pill === "2X" ? "#FF9E1B" : "#9FB0BC";
          return (
          <div key={s.id} className="jh-mock-sess" data-live={liveNow ? "1" : "0"}
               onClick={() => setOpenSessionId(s.id)}
               style={{cursor:"pointer",display:"flex",alignItems:"center",gap:14,padding:14,transform:"none",
                       background:s.completed ? "rgba(9,14,20,.94)" : "rgba(16,23,31,.96)",
                       backgroundImage:`linear-gradient(180deg,${liveNow ? "#00E5FF" : "#5C6B78"},rgba(92,107,120,.05))`,
                       backgroundSize:"3px 100%",backgroundRepeat:"no-repeat",border:"none"}}>
            <div style={{flex:"0 0 auto",width:48,height:48,display:"grid",placeItems:"center",
                 background:liveNow ? "rgba(0,229,255,.12)" : "rgba(255,255,255,.03)",
                 border:`1px solid ${liveNow ? "rgba(0,229,255,.5)" : "rgba(92,107,120,.3)"}`,
                 fontFamily:"'Archivo',sans-serif",fontStyle:"italic",fontVariationSettings:"'wdth' 125,'wght' 900",
                 fontSize:24,color:liveNow ? "#00E5FF" : "#9FB0BC"}}>{num}</div>
            <div style={{flex:"1 1 auto",minWidth:0}}>
              <div style={{fontFamily:"'Archivo',sans-serif",fontWeight:800,fontSize:9,letterSpacing:".24em",color:"#9FB0BC"}}>
                {s.date ? new Date(s.date + "T12:00:00").toLocaleDateString("en-GB", { weekday:"short", day:"numeric", month:"short" }).toUpperCase() : "NO DATE"}</div>
              <div style={{fontFamily:"'Archivo',sans-serif",fontStyle:"italic",fontVariationSettings:"'wdth' 118,'wght' 900",
                   fontSize:20,lineHeight:1.05,color:"#F4F9FA",marginTop:2,
                   whiteSpace:"nowrap",overflow:"hidden",textOverflow:"ellipsis"}}>{s.name.toUpperCase()}</div>
              <div style={{fontFamily:"'Archivo',sans-serif",fontWeight:800,fontSize:10,letterSpacing:".14em",
                   color:noteColour,marginTop:4,whiteSpace:"nowrap",overflow:"hidden",textOverflow:"ellipsis"}}>{note}</div>
            </div>
            <div style={{flex:"0 0 auto",padding:"4px 9px",background:"rgba(5,7,9,.7)",
                 border:`1px solid ${pc}66`,fontFamily:"'Archivo',sans-serif",fontWeight:800,fontSize:9,
                 letterSpacing:".18em",color:pc}}>{pill}</div>
          </div>
        );})}
      </div>

      {show && <CreateSessionModal onClose={() => setShow(false)} count={state.sessions.length} onCreate={(name, date, groupCount, qualifyCount, thirdPlaceMode, doublePoints) => { const id = uid("s"); update(s => ({ ...s, sessions: [...s.sessions, { id, name, date, groupCount: groupCount||4, qualifyCount: qualifyCount||2, thirdPlaceMode: thirdPlaceMode||"best2", doublePoints: !!doublePoints, teams: [], groupMatches: [], bracket: { qf: [], sf: [], final: null }, waitlist: [], completed: false }] })); setOpenSessionId(id); }} />}
      {showDraft && <DraftReminderModal onClose={() => setShowDraft(false)} state={state} leaderboard={leaderboard} />}
      {showFormat && (() => { const txt = generateFormatText(state); return (
        <Modal open={true} onClose={() => setShowFormat(false)} title="HOW IT WORKS">
        <div className="space-y-3">
          <textarea readOnly rows={18} value={txt} className="w-full bg-stone-900 border border-stone-700 rounded-lg px-3 py-2.5 text-stone-100 font-mono text-xs leading-relaxed" />
          <Btn className="w-full" onClick={() => { navigator.clipboard?.writeText(txt); setShowFormat(false); }}>📋 Copy for WhatsApp</Btn>
        </div>
        </Modal>); })()}
      {showAnnounce && <Modal open={true} onClose={() => setShowAnnounce(false)} title="SEASON ANNOUNCEMENT">
        <div className="space-y-3">
          <textarea readOnly rows={18} value={SEASON_ANNOUNCEMENT} className="w-full bg-stone-900 border border-stone-700 rounded-lg px-3 py-2.5 text-stone-100 font-mono text-xs leading-relaxed" />
          <Btn className="w-full" onClick={() => { navigator.clipboard?.writeText(SEASON_ANNOUNCEMENT); setShowAnnounce(false); }}>📋 Copy for WhatsApp</Btn>
        </div>
      </Modal>}
    </div>
  );
}'''
