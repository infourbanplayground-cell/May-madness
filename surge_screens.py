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
        {/* The lockup, back in the hero. The canvas set the volume in type
            alone; the mark is the brand and it carries the volume better than
            a headline does, so the headline steps down to a tagline under it. */}
        <picture>
          <source type="image/webp" srcSet="assets/surge-lockup.webp" />
          <img className="surge-lockup-img" src="assets/surge-lockup.png" alt="September Surge"
               style={{position:"relative",display:"block",width:"100%",maxWidth:330,margin:"12px auto 0"}} />
        </picture>
        <div style={{position:"relative",textAlign:"center",fontFamily:"'Archivo',sans-serif",fontStyle:"italic",
             fontVariationSettings:"'wdth' 118,'wght' 900",fontSize:22,lineHeight:1,
             color:"#F4F9FA",marginTop:10,letterSpacing:".02em"}}>RIDE <span style={{color:"#00E5FF"}}>THE SURGE.</span></div>
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
              <Avatar player={e.player} size={34} />
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
             style={{cursor:"pointer",padding:"9px 0",borderTop:"1px solid rgba(92,107,120,.16)",minWidth:0,
                     display:"flex",alignItems:"center",gap:9}}>
          <Avatar player={e.player} size={28} />
          <div style={{flex:1,minWidth:0}}>
          <div style={{fontFamily:"'Archivo',sans-serif",fontWeight:800,fontSize:15,color:"#F4F9FA",
               whiteSpace:"nowrap",overflow:"hidden",textOverflow:"ellipsis"}}>{e.player.name}</div>
          <div style={{height:4,marginTop:5,width:`${Math.max(4, Math.round(ptsOf(e) / topPts * 100))}%`,
               background:"linear-gradient(90deg,rgba(0,229,255,.7),rgba(0,229,255,.12))"}} />
          </div>
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
              <Avatar player={leader.player} size={40} />
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
              <Avatar player={e.player} size={36} />
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


# ── Faces on the team rows inside a session ────────────────────────────────
# Two overlapping 26px avatars read as "a pair" at a glance, which is what a
# team is here. Applied to TeamsTab in the session overlay.
SESSION_FACES_OLD = """                <div className="flex-1 min-w-0"><div className="text-sm text-stone-100 truncate">{p1?.name || "?"} & {p2?.name || "?"}</div></div>"""
SESSION_FACES_NEW = """                <span className="flex items-center shrink-0" style={{ marginRight: 2 }}>
                  {p1 && <Avatar player={p1} size={26} />}
                  {p2 && <span style={{ marginLeft: -6 }}><Avatar player={p2} size={26} /></span>}
                </span>
                <div className="flex-1 min-w-0"><div className="text-sm text-stone-100 truncate">{p1?.name || "?"} & {p2?.name || "?"}</div></div>"""


# ── The appended CSS layer and its companion script ────────────────────────
# Held here rather than inside the build script: they are long, multi-line,
# and were previously kept as one-line escaped literals, which is how a
# later edit came to inject raw CSS into the middle of a string and break
# the build outright.
UX_LAYER = """

/* ══ 9 · UX REFINEMENT LAYER (Vol.7, second pass) ═══════════════════════
   Applied from the UI/UX enhancement bundle. Visual only: no scoring, no
   API, no routing. Three things from that bundle were deliberately NOT
   taken, and are recorded here so the next volume does not "restore" them:

     · the session tab-bar rebuild (4-up grid + action row) — an IA change,
       and the owner chose to keep the single scrolling chip row;
     · every `table` / `tbody` / `td` / `th` rule — this app has no <table>
       anywhere; group standings are divs, so those rules matched nothing;
     · `tbody tr:nth-child(-n+2)` as "the qualifiers" — qualification here
       is 1, 2 or 4 per group, or top-2-plus-best-thirds, or all thirds.
       Rebuilt below against the real rule instead.
   ────────────────────────────────────────────────────────────────────── */

:root{
  --sg-plate-1:rgba(9,14,20,.94);
  --sg-plate-2:rgba(16,23,31,.96);
  --sg-text-2:#9FB0BC;            /* secondary prose — 4.5:1 on the base */
  --sg-hit:44px;
  --sg-t:170ms cubic-bezier(.2,.7,.3,1);
}

/* ── 9.1 HIERARCHY ─────────────────────────────────────────────────── */
.text-stone-400,.text-stone-500,[class*="bg-stone-9"] .text-stone-400,
[class*="bg-stone-9"] .text-stone-500{ color:var(--sg-text-2) !important; }
.text-stone-600{ color:#7C8B98 !important; }

.jh-panel,[class*="bg-stone-9"]:not(nav):not(header):not(.sticky){
  padding-top:16px !important; padding-bottom:16px !important;
  padding-right:16px !important;
  background-color:var(--sg-plate-1) !important;
}
.jh-panel .jh-mock-row,.jh-panel .jh-mock-sess,
[class*="bg-stone-9"] [class*="bg-stone-9"]{
  padding-top:11px !important; padding-bottom:11px !important;
}

label,.uppercase.tracking-wider,.uppercase.tracking-wide{
  font-family:'Archivo',sans-serif !important; font-style:normal !important;
  font-weight:800 !important; letter-spacing:.2em !important;
  color:var(--surge-steel) !important;
}
.font-mono,.sg-top-pts,.sg-thin-pts{ font-variant-numeric:tabular-nums; }
.jh-sec-title{ margin-bottom:14px !important; }

/* ── 9.2 ENERGY ─────────────────────────────────────────────────────
   Retargeted. The bundle aimed these at .jh-srow / .jh-lbrow, which this
   build stopped using when RANK was rebuilt to the design language —
   they matched nothing. The real hooks are the classes below.        */
.sg-top{ position:relative; }
.sg-top[data-lead="1"]{ overflow:hidden; }
.sg-top[data-lead="1"]::after{
  content:"";position:absolute;inset:0;pointer-events:none;
  background:linear-gradient(105deg,transparent 38%,rgba(0,229,255,.10) 50%,transparent 62%);
  transform:translateX(-120%);animation:sgSheen 6s ease-in-out infinite;
}
@keyframes sgSheen{ 0%,72%{transform:translateX(-120%)} 100%{transform:translateX(120%)} }

.jh-mock-sess[data-live="1"]{
  background-color:rgba(0,229,255,.07) !important;
  box-shadow:inset 0 0 0 1px rgba(0,229,255,.22) !important;
}

button[style*="00E5FF"]{
  background-image:linear-gradient(100deg,rgba(255,255,255,.22),transparent 46%) !important;
  transition:transform var(--sg-t),box-shadow var(--sg-t),filter var(--sg-t) !important;
}

/* ── 9.3 FEEDBACK — every tap answers ──────────────────────────────── */
button,[role="button"],.jh-mock-row,.jh-mock-sess,.jh-chipbtn,.sg-top,.sg-thin{
  transition:transform var(--sg-t),background-color var(--sg-t),
             box-shadow var(--sg-t),color var(--sg-t),opacity var(--sg-t);
  -webkit-tap-highlight-color:transparent;
}
button:active,[role="button"]:active,.jh-chipbtn:active{ transform:scale(.955); }
.jh-mock-row:active,.jh-mock-sess:active,.sg-top:active,.sg-thin:active{
  transform:scale(.99);background-color:rgba(0,229,255,.10) !important;
}
button:focus-visible,a:focus-visible,input:focus-visible,select:focus-visible,
textarea:focus-visible{ outline:2px solid var(--surge-cyan) !important;outline-offset:2px !important; }
nav.fixed button{ min-height:var(--sg-hit); }

/* a value that just changed says so. No display change: the bundle set
   display:inline-block here, which would have collapsed any flex or grid
   child it landed on, and every number in this app is one. */
@keyframes sgBump{ 0%{transform:none} 34%{transform:scale(1.16);filter:brightness(1.5)} 100%{transform:none} }
.sg-bump{ animation:sgBump 420ms var(--ease-out); }

.sg-ripple{
  position:fixed;z-index:9999;pointer-events:none;border-radius:50%;
  width:16px;height:16px;margin:-8px 0 0 -8px;
  background:radial-gradient(circle,rgba(0,229,255,.5),rgba(0,229,255,0) 70%);
  animation:sgRip 460ms ease-out forwards;
}
@keyframes sgRip{ to{ transform:scale(7);opacity:0 } }

/* staggered entrance, first screenful only */
main .sg-top,main .jh-panel,main .jh-mock-sess{ animation:sgRowIn 320ms var(--ease-out) both; }
@keyframes sgRowIn{ from{opacity:0;transform:translateX(-8px)} to{opacity:1;transform:none} }
main .sg-top:nth-child(2){animation-delay:40ms}
main .sg-top:nth-child(3){animation-delay:80ms}

/* ── 9.4 BOTTOM NAV — the active tab reads at a glance ─────────────── */
nav.fixed button[style*="color: var(--orange-br)"],
nav.fixed button[style*="color:var(--orange-br)"]{ position:relative; }
nav.fixed button[style*="color: var(--orange-br)"]::before,
nav.fixed button[style*="color:var(--orange-br)"]::before{
  content:"";position:absolute;top:-6px;left:22%;right:22%;height:3px;
  background:var(--surge-cyan);box-shadow:0 0 14px rgba(0,229,255,.7);
}
nav.fixed button[style*="color: var(--orange-br)"] svg,
nav.fixed button[style*="color:var(--orange-br)"] svg{
  filter:drop-shadow(0 0 8px rgba(0,229,255,.55));
}

/* ── 9.5 BACKGROUND MOTIF — diagonal speed streaks ──────────────────
   Replaces the surge trace from section 1. Same single cyan at the same
   weight; the read is forward motion rather than an oscilloscope line.
   Two layers so the rhythm is not uniform. Chosen by the owner over the
   trace. Note the position is NOT !important — pinning it is what froze
   the trace's drift the first time round.                            */
html body::before{
  background-image:
    repeating-linear-gradient(66deg,
      rgba(0,229,255,.10) 0 1px, transparent 1px 92px),
    repeating-linear-gradient(66deg,
      rgba(0,229,255,.05) 0 2px, transparent 2px 31px) !important;
  background-size:auto !important;
  background-repeat:repeat !important;
  background-position:0 0;
  animation:sgStreaks 22s linear infinite !important;
}
@keyframes sgStreaks{ to{ background-position:-276px -620px, -138px -310px } }

/* ── 9.6 MEDIA ──────────────────────────────────────────────────────── */
.aa-wall > div{ transition:transform var(--sg-t),box-shadow var(--sg-t); }
.aa-wall > div:active{ transform:scale(.98); }
@media (hover:hover){
  .aa-wall > div:hover{ box-shadow:0 0 0 1px rgba(0,229,255,.5),0 0 30px rgba(0,229,255,.2); }
}

/* ── 9.9 SCREEN PRIMITIVES ─────────────────────────────────────────
   The classes the rebuilt HOME / SESSIONS / RANK views reference. Kept as
   classes rather than inline styles because they repeat across all three.  */

.sg-kicker{
  font-family:'Archivo',sans-serif !important;
  font-weight:800 !important; font-style:normal !important;
  font-size:10px !important; letter-spacing:.34em !important;
  text-transform:uppercase !important; color:var(--sg-text-2) !important;
  margin:0 !important; padding:0 !important; background:none !important;
  border:none !important; box-shadow:none !important; display:block !important;
}
.sg-card{
  background:rgba(9,14,20,.94);
  border:none;
}
.sg-card-cyan{
  background:rgba(16,23,31,.96);
  background-image:linear-gradient(180deg,#00E5FF,rgba(0,229,255,.06));
  background-size:3px 100%; background-repeat:no-repeat;
}
.sg-livedot{
  position:relative; display:block; width:7px; height:7px; border-radius:50%;
  background:var(--surge-cyan); box-shadow:0 0 10px rgba(0,229,255,.8);
  animation:sgBar 2s ease-in-out infinite;
}
@keyframes sgBar{ 0%,100%{opacity:.55} 50%{opacity:1} }
@keyframes sgSlide{ from{opacity:0;transform:translateX(-10px)} to{opacity:1;transform:none} }

@media (prefers-reduced-motion:reduce){
  .sg-livedot{ animation:none !important; }
}

/* ── 9.7 QUALIFYING ROWS — the real rule ────────────────────────────
   Driven by data-qual, which GroupsTab sets from qualifyingTeamIds() —
   the same computation seedQF uses. So this marks 1, 2 or 4 rows per
   group, or top-2-plus-the-two-best-thirds, or all three, according to
   the session's own format, and it follows the scores live.         */
.sg-standrow[data-qual="1"]{
  box-shadow:inset 3px 0 0 var(--surge-cyan);
  background-color:rgba(0,229,255,.05) !important;
}

/* ── 9.8 SESSION SCREEN — scale and presence ────────────────────────
   The overlay carried a whole night's scoring at 11–14px. Scoped to the
   session overlay so nothing else shifts. The bundle's table rules are
   dropped (no tables exist); the group-heading rules are retargeted at
   the markup this app actually renders.                             */
.fixed.inset-0.z-40 .text-sm{ font-size:15px !important; line-height:1.35 !important; }
.fixed.inset-0.z-40 .text-xs{ font-size:13px !important; line-height:1.4 !important; }
.fixed.inset-0.z-40 .text-\\[11px\\]{ font-size:12.5px !important; line-height:1.45 !important; }
.fixed.inset-0.z-40 .text-\\[10px\\]{ font-size:11px !important; letter-spacing:.16em !important; }
.fixed.inset-0.z-40 .text-\\[9px\\]{ font-size:11px !important; }
.fixed.inset-0.z-40 .font-display.text-xl{ font-size:26px !important; line-height:1 !important; }

.fixed.inset-0.z-40 button.w-full.flex.items-center{
  min-height:56px !important; padding:10px 12px !important;
  border-bottom:1px solid rgba(92,107,120,.16) !important;
}
.fixed.inset-0.z-40 button.w-full.flex.items-center .truncate{
  font-family:'Archivo',sans-serif !important; font-weight:800 !important;
  font-size:17px !important; letter-spacing:-.005em !important; color:var(--surge-white) !important;
}
.fixed.inset-0.z-40 .font-mono{ font-variant-numeric:tabular-nums; font-size:14px !important; }
.fixed.inset-0.z-40 .sg-standrow{ padding-top:9px !important; padding-bottom:9px !important; }
.fixed.inset-0.z-40 .border-dashed{
  font-size:13px !important; padding:18px !important;
  border-color:rgba(0,229,255,.22) !important; color:var(--sg-text-2) !important;
  letter-spacing:.12em !important; text-transform:uppercase !important;
}

@media (prefers-reduced-motion:reduce){
  html body::before{ animation:none !important; }
  .sg-top[data-lead="1"]::after{ animation:none !important; }
  main .sg-top,main .jh-panel,main .jh-mock-sess,.sg-bump{ animation:none !important; }
  .sg-ripple{ display:none !important; }
}
"""

UX_SCRIPT = """
<script>
/* Presentational only — a press ripple and a bump on numbers that change.
   Reads no state, writes no state, touches no React props. */
(function(){
  if (matchMedia("(prefers-reduced-motion:reduce)").matches) return;

  document.addEventListener("pointerdown", function(e){
    var t = e.target.closest && e.target.closest(
      "button,[role='button'],.jh-mock-row,.jh-mock-sess,.sg-top,.sg-thin,.jh-chipbtn");
    if (!t) return;
    var r = document.createElement("span");
    r.className = "sg-ripple";
    r.style.left = e.clientX + "px";
    r.style.top  = e.clientY + "px";
    document.body.appendChild(r);
    setTimeout(function(){ r.remove(); }, 480);
  }, { passive: true });

  // Bump whichever number just changed. Guarded three ways: not during the
  // first paint, not inside a field the user is typing in, and never more
  // than a handful at once — a full-table re-render after a server sync
  // would otherwise flash the whole screen.
  var boot = Date.now();
  var mo = new MutationObserver(function(muts){
    if (Date.now() - boot < 1500) return;
    if (muts.length > 12) return;
    muts.forEach(function(m){
      var el = m.target.nodeType === 3 ? m.target.parentElement : m.target;
      if (!el || !el.classList) return;
      if (!/^[\\d\\s.,:+\\-–]+$/.test((el.textContent || "").trim())) return;
      if (el.closest("input,textarea,nav")) return;
      el.classList.remove("sg-bump");
      void el.offsetWidth;
      el.classList.add("sg-bump");
      setTimeout(function(){ el.classList.remove("sg-bump"); }, 460);
    });
  });
  (function start(){
    var root = document.getElementById("root");
    if (!root) return setTimeout(start, 400);
    mo.observe(root, { subtree: true, characterData: true });
  })();
})();
</script>
"""


# ── SESSION DETAIL · GROUPS ────────────────────────────────────────────────
# One group at a time, per the canvas. Every scoring handler is carried over
# unchanged — setAdd/setEdit and MatchEditorModal are the same objects the old
# view used, so entering a result behaves exactly as it did.
#
# The canvas's "COURT BOARD · WHO IS ON NOW" panel is not built: it needs a
# court number per match, and nothing in this app records one.
GROUPS_FN = r'''function GroupsTab({ session, state, updateSession, isAdmin }) {
  const [edit, setEdit] = useState(null);
  const [add, setAdd] = useState(null);
  const groups = getSessionGroups(session);
  const [pick, setPick] = useState(groups[0] || "A");
  const g = groups.includes(pick) ? pick : groups[0];
  const groupSizes = groups.map(x => (session.teams || []).filter(t => t.group === x).length);
  const isUneven = groupSizes.length > 1 && new Set(groupSizes).size > 1;
  const [showRules, setShowRules] = useState(false);
  // Same rule the bracket seeds from, so the table cannot promise a spot the
  // knockout won't honour.
  const qualIds = qualifyingTeamIds(session);

  const teams = (session.teams || []).filter(t => t.group === g);
  const matches = (session.groupMatches || []).filter(m =>
    teams.find(t => t.id === m.team1Id) && teams.find(t => t.id === m.team2Id));
  const standings = calcGroupStandings(session, g);
  const top = getTopOfGroup(session, g);
  const first = (id) => { const p = state.players.find(x => x.id === id); return p ? p.name.split(" ")[0] : "?"; };
  const lbl = (t) => t ? `${first(t.p1Id)} & ${first(t.p2Id)}` : "?";
  const inits = (t) => t ? [t.p1Id, t.p2Id].map(id => {
    const p = state.players.find(x => x.id === id);
    return p ? (p.name[0] || "?").toUpperCase() : "?";
  }) : ["?", "?"];

  // What qualification actually is for THIS session, said plainly.
  const N = groups.length;
  const qLabel = N === 4 && session.thirdPlaceMode === "all4r16" ? "ALL THIRDS QUALIFY"
    : N === 3 ? "TOP 2 + BEST THIRDS QUALIFY"
    : `TOP ${getQualifyCount(session)} QUALIFY`;

  const played = matches.filter(m => m.winner).length;

  return (
    <div className="space-y-4">
      {(() => {
        // Say it on the screen, so nobody wonders where the points came from.
        const small = groups.filter(x => {
          const n = (session.teams || []).filter(t => t.group === x).length;
          return n > 0 && n <= GROUP_COUNTED_GAMES;
        });
        if (!small.length) return null;
        const plays = Math.max(0, (session.teams || []).filter(t => t.group === small[0]).length - 1);
        return <div className="flex gap-2.5 p-3" style={{ background:"rgba(0,229,255,.08)", border:"1px solid rgba(0,229,255,.35)" }}>
          <I.alert size={16} className="shrink-0 mt-0.5" style={{ color:"#00E5FF" }} />
          <div>
            <div className="text-xs font-bold" style={{ color:"#00E5FF" }}>Bye awarded · group {small.join(" and ")}</div>
            <div className="text-[11px] mt-0.5" style={{ color:"#9FB0BC" }}>Series points and knockout seeding both count your best 3 group results, and this group only plays {plays} — so every team in it gets a notional 6&ndash;0 bye win. The draw costs nobody points or seeding. The table below still shows real matches only.</div>
          </div>
        </div>;
      })()}
      {isUneven && (
        <div className="flex gap-2.5 p-3" style={{ background:"rgba(255,158,27,.10)", border:"1px solid rgba(255,158,27,.35)" }}>
          <I.alert size={16} className="shrink-0 mt-0.5" style={{ color:"#FF9E1B" }} />
          <div>
            <div className="text-xs font-bold" style={{ color:"#FF9E1B" }}>Uneven groups</div>
            <div className="text-[11px] mt-0.5" style={{ color:"#9FB0BC" }}>Groups have different team counts ({groupSizes.join(" / ")}). For knockout seeding every team is ranked on the same number of matches — the smallest group's ({Math.min(...groupSizes)} played) — so larger groups drop their lowest result. The tables below still show every match played.</div>
          </div>
        </div>
      )}

      {/* ── GROUP CHIPS — one group at a time ── */}
      <div style={{display:"grid",gridTemplateColumns:`repeat(${Math.max(1, groups.length)},minmax(0,1fr))`,gap:6}}>
        {groups.map(x => {
          const on = x === g;
          const n = (session.teams || []).filter(t => t.group === x).length;
          const ms = (session.groupMatches || []).filter(m => {
            const ts = (session.teams || []).filter(t => t.group === x);
            return ts.find(t => t.id === m.team1Id) && ts.find(t => t.id === m.team2Id);
          });
          return <div key={x} onClick={() => setPick(x)}
            style={{cursor:"pointer",minHeight:52,padding:"9px 4px",textAlign:"center",
                    background:on ? "rgba(0,229,255,.12)" : "rgba(9,14,20,.94)",
                    border:`1px solid ${on ? "rgba(0,229,255,.55)" : "rgba(92,107,120,.3)"}`}}>
            <div style={{fontFamily:"'Archivo',sans-serif",fontStyle:"italic",fontVariationSettings:"'wdth' 118,'wght' 900",
                 fontSize:21,lineHeight:1,color:on ? "#00E5FF" : "#9FB0BC"}}>{x}</div>
            <div style={{fontFamily:"'JetBrains Mono',monospace",fontSize:10,marginTop:4,
                 color:on ? "#00E5FF" : "#9FB0BC"}}>{ms.filter(m => m.winner).length}/{ms.length} · {n}</div>
          </div>;
        })}
      </div>

      {/* ── STANDINGS ── */}
      <div style={{marginTop:14,padding:16,background:"rgba(9,14,20,.94)",
           backgroundImage:"linear-gradient(180deg,#00E5FF,rgba(0,229,255,.06))",
           backgroundSize:"3px 100%",backgroundRepeat:"no-repeat",position:"relative",overflow:"hidden"}}>
        <div style={{position:"absolute",right:8,bottom:-26,fontFamily:"'Archivo',sans-serif",fontStyle:"italic",
             fontVariationSettings:"'wdth' 125,'wght' 900",fontSize:96,lineHeight:1,
             color:"rgba(244,249,250,.035)",pointerEvents:"none"}}>{g}</div>
        <div style={{position:"relative",display:"flex",alignItems:"center",gap:10}}>
          <div style={{width:36,height:36,display:"grid",placeItems:"center",background:"rgba(0,229,255,.12)",
               border:"1px solid rgba(0,229,255,.45)",fontFamily:"'Archivo',sans-serif",fontStyle:"italic",
               fontVariationSettings:"'wdth' 125,'wght' 900",fontSize:20,color:"#00E5FF"}}>{g}</div>
          <div style={{fontFamily:"'Archivo',sans-serif",fontStyle:"italic",fontVariationSettings:"'wdth' 118,'wght' 900",
               fontSize:20,lineHeight:1,color:"#F4F9FA"}}>GROUP {g}</div>
          <div style={{marginLeft:"auto",fontFamily:"'Archivo',sans-serif",fontWeight:800,fontSize:9,
               letterSpacing:".18em",color:"#9FB0BC"}}>{played}/{matches.length} PLAYED</div>
        </div>

        {standings.length === 0
          ? <div style={{position:"relative",marginTop:12,padding:16,textAlign:"center",
                 border:"1px dashed rgba(0,229,255,.22)",fontFamily:"'Archivo',sans-serif",fontWeight:800,
                 fontSize:11,letterSpacing:".12em",color:"#9FB0BC"}}>NO RESULTS YET</div>
          : <div style={{position:"relative",display:"grid",gridTemplateColumns:"1fr 40px 44px 56px",marginTop:12}}>
              <div style={{fontFamily:"'Archivo',sans-serif",fontWeight:800,fontSize:10,letterSpacing:".2em",color:"#9FB0BC",paddingBottom:8}}>TEAM</div>
              <div style={{fontFamily:"'Archivo',sans-serif",fontWeight:800,fontSize:10,letterSpacing:".2em",color:"#9FB0BC",textAlign:"center",paddingBottom:8}}>W</div>
              <div style={{fontFamily:"'Archivo',sans-serif",fontWeight:800,fontSize:10,letterSpacing:".2em",color:"#9FB0BC",textAlign:"center",paddingBottom:8}}>GD</div>
              <div style={{fontFamily:"'Archivo',sans-serif",fontWeight:800,fontSize:10,letterSpacing:".2em",color:"#9FB0BC",textAlign:"right",paddingBottom:8}}>PTS</div>
              {standings.map((r) => {
                const q = qualIds.has(r.team.id);
                const isTop = r.team.id === top;
                const [i1, i2] = inits(r.team);
                const cell = { borderTop:"1px solid rgba(92,107,120,.16)", padding:"10px 0" };
                return <React.Fragment key={r.team.id}>
                  <div style={{...cell, display:"flex",alignItems:"center",gap:8,paddingLeft:10,
                       boxShadow:q ? "inset 3px 0 0 var(--surge-cyan)" : "none"}}>
                    <div style={{display:"flex",flex:"0 0 auto",gap:2}}>
                      {[i1, i2].map((c, n2) => <div key={n2} style={{width:23,height:23,display:"grid",placeItems:"center",
                           background:q ? "rgba(0,229,255,.10)" : "rgba(255,255,255,.04)",
                           border:`1px solid ${q ? "rgba(0,229,255,.28)" : "rgba(92,107,120,.28)"}`,
                           fontFamily:"'JetBrains Mono',monospace",fontSize:10,fontWeight:700,
                           color:q ? "#00E5FF" : "#9FB0BC"}}>{c}</div>)}
                    </div>
                    <div style={{minWidth:0,fontFamily:"'Archivo',sans-serif",fontWeight:800,fontSize:14,
                         color:"#F4F9FA",whiteSpace:"nowrap",overflow:"hidden",textOverflow:"ellipsis"}}>
                      {isTop && <span style={{color:"#00E5FF",marginRight:4}}>&#9650;</span>}{lbl(r.team)}</div>
                  </div>
                  <div style={{...cell, display:"grid",placeItems:"center",fontFamily:"'JetBrains Mono',monospace",fontSize:14,color:"#F4F9FA"}}>{r.wins}</div>
                  <div style={{...cell, display:"grid",placeItems:"center",fontFamily:"'JetBrains Mono',monospace",fontSize:13,color:"#9FB0BC"}}>{r.gd > 0 ? "+" : ""}{r.gd}</div>
                  <div style={{...cell, display:"flex",alignItems:"center",justifyContent:"flex-end",
                       fontFamily:"'Archivo',sans-serif",fontStyle:"italic",fontVariationSettings:"'wdth' 112,'wght' 900",
                       fontSize:20,color:q ? "#00E5FF" : "#F4F9FA"}}>{r.pts}</div>
                </React.Fragment>;
              })}
            </div>}

        <div style={{position:"relative",display:"flex",alignItems:"center",gap:8,marginTop:12,paddingTop:12,
             borderTop:"1px solid rgba(92,107,120,.16)"}}>
          <div style={{fontFamily:"'Archivo',sans-serif",fontWeight:800,fontSize:9,letterSpacing:".28em",color:"#00E5FF"}}>{qLabel} &#9654;</div>
          <div style={{flex:1,height:2,background:"linear-gradient(90deg,rgba(0,229,255,.5),transparent)"}} />
        </div>
      </div>

      {/* ── MATCHES ── */}
      <div style={{display:"flex",alignItems:"center",gap:10,marginTop:20}}>
        <div className="sg-kicker">Group {g} matches</div>
        {isAdmin && teams.length >= 2 && <div style={{marginLeft:"auto"}}>
          <Btn size="sm" variant="secondary" onClick={() => setAdd(g)}><I.plus size={12} /> Match</Btn></div>}
      </div>
      {matches.length === 0
        ? <div style={{marginTop:10,padding:18,textAlign:"center",border:"1px dashed rgba(0,229,255,.22)",
               fontFamily:"'Archivo',sans-serif",fontWeight:800,fontSize:11,letterSpacing:".12em",color:"#9FB0BC"}}>NO MATCHES YET</div>
        : <div style={{display:"flex",flexDirection:"column",gap:10,marginTop:10}}>
            {matches.map((m, mi) => {
              const t1 = (session.teams || []).find(t => t.id === m.team1Id);
              const t2 = (session.teams || []).find(t => t.id === m.team2Id);
              const done = !!m.winner;
              const w1 = m.winner === "team1", w2 = m.winner === "team2";
              const bar = done ? "#00E5FF" : "#5C6B78";
              return <div key={m.id} onClick={() => isAdmin && setEdit({ ...m, group: g })}
                style={{cursor:isAdmin ? "pointer" : "default",padding:14,background:"rgba(9,14,20,.94)",
                        backgroundImage:`linear-gradient(180deg,${bar},rgba(92,107,120,.05))`,
                        backgroundSize:"3px 100%",backgroundRepeat:"no-repeat"}}>
                <div style={{display:"flex",alignItems:"center",gap:8}}>
                  <div style={{fontFamily:"'Archivo',sans-serif",fontWeight:800,fontSize:9,letterSpacing:".28em",color:"#9FB0BC"}}>MATCH {mi + 1}</div>
                  <div style={{marginLeft:"auto",fontFamily:"'Archivo',sans-serif",fontWeight:800,fontSize:9,
                       letterSpacing:".22em",color:done ? "#00E5FF" : "#9FB0BC"}}>{done ? "FINAL" : isAdmin ? "TAP TO SCORE" : "TO PLAY"}</div>
                </div>
                <div style={{display:"grid",gridTemplateColumns:"1fr auto 1fr",alignItems:"center",gap:10,marginTop:10}}>
                  <div style={{minWidth:0,fontFamily:"'Archivo',sans-serif",fontWeight:800,fontSize:14,textAlign:"right",
                       color:w1 ? "#00E5FF" : "#F4F9FA",whiteSpace:"nowrap",overflow:"hidden",textOverflow:"ellipsis"}}>{lbl(t1)}</div>
                  <div style={{flex:"0 0 auto",display:"flex",alignItems:"center",gap:7,padding:"5px 11px",
                       background:done ? "rgba(0,229,255,.08)" : "rgba(255,255,255,.03)",
                       border:`1px solid ${done ? "rgba(0,229,255,.35)" : "rgba(92,107,120,.3)"}`}}>
                    <span style={{fontFamily:"'Archivo',sans-serif",fontStyle:"italic",fontVariationSettings:"'wdth' 112,'wght' 900",
                          fontSize:25,lineHeight:1,color:w1 ? "#00E5FF" : "#9FB0BC"}}>{m.score ? m.score.t1 : "–"}</span>
                    <span style={{fontSize:13,color:"#9FB0BC"}}>/</span>
                    <span style={{fontFamily:"'Archivo',sans-serif",fontStyle:"italic",fontVariationSettings:"'wdth' 112,'wght' 900",
                          fontSize:25,lineHeight:1,color:w2 ? "#00E5FF" : "#9FB0BC"}}>{m.score ? m.score.t2 : "–"}</span>
                  </div>
                  <div style={{minWidth:0,fontFamily:"'Archivo',sans-serif",fontWeight:800,fontSize:14,
                       color:w2 ? "#00E5FF" : "#F4F9FA",whiteSpace:"nowrap",overflow:"hidden",textOverflow:"ellipsis"}}>{lbl(t2)}</div>
                </div>
                {!m.score && m.lossType && <div style={{marginTop:9,fontFamily:"'Archivo',sans-serif",fontWeight:800,
                     fontSize:10,letterSpacing:".14em",color:"#9FB0BC"}}>
                  {(LOSS_TYPES.find(lt => lt.id === m.lossType) || {}).label}</div>}
              </div>;
            })}
          </div>}

      {/* ── HOW STANDINGS WORK — folded away; it is read once ── */}
      <button onClick={() => setShowRules(v => !v)}
        style={{width:"100%",textAlign:"left",background:"none",border:"none",
                borderTop:"1px solid rgba(92,107,120,.18)",padding:"14px 4px",marginTop:20,cursor:"pointer",
                fontFamily:"'JetBrains Mono',monospace",fontSize:10,fontWeight:700,letterSpacing:".14em",
                color:"#00E5FF",textTransform:"uppercase"}}>
        {showRules ? "Hide" : "How standings work"} &#9654;
      </button>
      {showRules && <Card className="p-3">
        <div className="text-[11px] leading-relaxed space-y-1" style={{color:"#9FB0BC"}}>
          <div><span className="font-bold" style={{color:"#F4F9FA"}}>Ranked by:</span> Wins › Game difference (GD) › Games won › Head-to-head. (Most wins first — not total points.)</div>
          <div><span className="font-bold" style={{color:"#F4F9FA"}}>Points:</span> Win <span className="font-mono" style={{color:"#00E5FF"}}>+3</span> · Tiebreak loss <span className="font-mono">+2</span> · Close loss <span className="font-mono">+1</span> · Blowout loss <span className="font-mono">0</span></div>
          <div><span className="font-bold" style={{color:"#F4F9FA"}}>Series points:</span> this table counts every match played. For the series leaderboard only, each team's best 3 group results count — so a 5-team group drops its lowest game and cannot out-earn a group of 4. Knockout and playoff matches never count as group games.</div>
        </div>
      </Card>}

      {(edit || add) && <MatchEditorModal session={session} state={state} group={edit?.group || add} match={edit} onClose={() => { setEdit(null); setAdd(null); }} onSave={(d) => { if (edit) updateSession(s => ({ ...s, groupMatches: s.groupMatches.map(m => m.id === edit.id ? { ...m, ...d } : m) })); else updateSession(s => ({ ...s, groupMatches: [...(s.groupMatches || []), { id: uid("m"), ...d }] })); }} onDelete={edit ? () => updateSession(s => ({ ...s, groupMatches: s.groupMatches.filter(m => m.id !== edit.id) })) : null} />}
    </div>
  );
}'''


# ── SESSION DETAIL · KNOCKOUTS ─────────────────────────────────────────────
# Only the three round Cards are replaced. seedQF, the qualification control,
# the "who qualified" panel, the manual seeding modal and BracketEditModal are
# all left alone — this is the round rendering, not the bracket logic.

# ── SESSION DETAIL · THE BRACKET ───────────────────────────────────────────
# Redrawn to the canvas: three labelled columns, cards carrying both names and
# their scores, and connectors that light up as each round resolves. Positions
# are computed, not hardcoded, so a bracket with fewer than four quarter-finals
# still lays out correctly.
#
# Same props and the same setEdit call as before, so tapping a match opens the
# same editor it always did.
BRACKET_TREE_FN = r'''function BracketTreeView({ b, lbl, canScore, setEdit }) {
  const QFW = 176, SFW = 168, FW = 176, CARD = 78, GAP = 18;
  const qf = b.qf || [];
  const n = Math.max(1, qf.length);
  const qTop = (i) => 22 + i * (CARD + GAP);
  const qMid = (i) => qTop(i) + CARD / 2;
  const sfCount = Math.max(1, Math.ceil(n / 2));
  const sMid = (i) => (qMid(i * 2) + qMid(Math.min(n - 1, i * 2 + 1))) / 2;
  const fMid = sfCount > 1 ? (sMid(0) + sMid(sfCount - 1)) / 2 : sMid(0);
  const H = qTop(n - 1) + CARD + 26;
  const X1 = QFW, X2 = QFW + 18, X3 = QFW + 36;
  const Y1 = X3 + SFW, Y2 = Y1 + 18, Y3 = Y1 + 36;
  const W = Y3 + FW;

  // Placeholders so all three columns are visible from the start.
  const sf = b.sf && b.sf.length ? b.sf
    : Array.from({ length: sfCount }, (_, i) => ({ id: "sfp" + i, slot: i + 1, team1Id: null, team2Id: null, winner: null }));
  const fin = b.final || { id: "fp", team1Id: null, team2Id: null, winner: null };

  const nameOf = (id) => id && !String(id).includes("TBD") ? lbl(id) : "—";
  const won = (m, k) => !!(m && m.winner === k);
  const line = (key, l, t, w, h, on) => <div key={key} style={{position:"absolute",left:l,top:t,width:w,height:h,
    background:on ? "rgba(0,229,255,.55)" : "rgba(92,107,120,.3)"}} />;

  const Card2 = ({ m, round, label, l, t, w, accent, live, big }) => {
    const done = !!(m && m.winner);
    const real = !!(m && (m.team1Id || m.team2Id));
    return <div onClick={() => real && canScore && setEdit({ ...m, round })}
      style={{position:"absolute",left:l,top:t,width:w,padding:big ? 12 : "9px 10px",
              background:big ? "rgba(16,23,31,.96)" : "rgba(9,14,20,.94)",
              cursor:real && canScore ? "pointer" : "default",
              border:`1px solid ${done ? (big ? "rgba(255,158,27,.5)" : "rgba(0,229,255,.45)") : "rgba(92,107,120,.3)"}`,
              borderLeft:`3px solid ${accent}`}}>
      <div style={{fontFamily:"'Archivo',sans-serif",fontWeight:800,fontSize:8,letterSpacing:".22em",
           color:big ? "#FF9E1B" : "#9FB0BC"}}>{label}</div>
      {["team1", "team2"].map((k, ki) => (
        <div key={k} style={{display:"flex",alignItems:"center",gap:8,marginTop:ki ? (big ? 5 : 4) : (big ? 8 : 6),
             paddingTop:ki ? (big ? 5 : 4) : 0,
             borderTop:ki ? "1px solid rgba(92,107,120,.18)" : "none"}}>
          <div style={{flex:"1 1 auto",minWidth:0,fontFamily:"'Archivo',sans-serif",fontWeight:800,
               fontSize:big ? 14 : 13,color:won(m, k) ? live : "#F4F9FA",
               whiteSpace:"nowrap",overflow:"hidden",textOverflow:"ellipsis"}}>{nameOf(m && m[k + "Id"])}</div>
          <div style={{flex:"0 0 auto",fontFamily:"'JetBrains Mono',monospace",fontSize:13,
               color:won(m, k) ? live : "#9FB0BC"}}>{m && m.score ? m.score[k === "team1" ? "t1" : "t2"] : "–"}</div>
        </div>
      ))}
    </div>;
  };

  const champId = b.final && b.final.winner
    ? (b.final.winner === "team1" ? b.final.team1Id : b.final.team2Id) : null;
  const label = (txt, l, colour) => <div style={{position:"absolute",left:l,top:0,
    fontFamily:"'Archivo',sans-serif",fontWeight:800,fontSize:9,letterSpacing:".28em",color:colour}}>{txt}</div>;

  return (
    <div>
      <div style={{overflowX:"auto",overscrollBehaviorX:"contain",paddingBottom:4}}>
        <div style={{position:"relative",width:W,height:H}}>
          {label("QUARTER-FINALS", 0, "#9FB0BC")}
          {label("SEMI-FINALS", X3, "#9FB0BC")}
          {label("FINAL", Y3, "#FF9E1B")}

          {/* connectors — each lights when its round has a result */}
          {qf.map((m, i) => line("q" + i, X1, qMid(i) - 1, 18, 2, !!m.winner))}
          {Array.from({ length: sfCount }).map((_, i) => {
            const a = qMid(i * 2), c = qMid(Math.min(n - 1, i * 2 + 1));
            const on = !!(sf[i] && (sf[i].team1Id || sf[i].team2Id));
            return <React.Fragment key={"j" + i}>
              {line("v" + i, X2, Math.min(a, c), 2, Math.abs(c - a) || 2, on)}
              {line("h" + i, X2, sMid(i) - 1, 18, 2, on)}
            </React.Fragment>;
          })}
          {sf.map((m, i) => line("s" + i, Y1, sMid(i) - 1, 18, 2, !!m.winner))}
          {sfCount > 1 && line("fv", Y2, Math.min(sMid(0), sMid(sfCount - 1)), 2,
                               Math.abs(sMid(sfCount - 1) - sMid(0)) || 2, !!(fin.team1Id || fin.team2Id))}
          {line("fh", Y2, fMid - 1, 18, 2, !!(fin.team1Id || fin.team2Id))}

          {/* cards */}
          {qf.map((m, i) => <Card2 key={"qf" + m.id} m={m} round="qf" label={`QF${i + 1}`}
            l={0} t={qTop(i)} w={QFW} accent={m.winner ? "#00E5FF" : "#5C6B78"} live="#00E5FF" />)}
          {sf.map((m, i) => <Card2 key={"sf" + m.id} m={m} round="sf" label={`SF${i + 1}`}
            l={X3} t={sMid(i) - CARD / 2} w={SFW} accent={m.winner ? "#00E5FF" : "#5C6B78"} live="#00E5FF" />)}
          <Card2 m={fin} round="final" label="FINAL" l={Y3} t={fMid - CARD / 2 - 8} w={FW}
            accent="#FF9E1B" live="#FF9E1B" big />
        </div>
      </div>

      {champId && <div style={{marginTop:12,display:"flex",alignItems:"center",gap:8,padding:"11px 13px",
           background:"rgba(255,158,27,.08)",borderLeft:"3px solid #FF9E1B"}}>
        <div style={{fontFamily:"'Archivo',sans-serif",fontWeight:800,fontSize:9,letterSpacing:".26em",color:"#FF9E1B"}}>CHAMPION</div>
        <div style={{marginLeft:"auto",minWidth:0,fontFamily:"'Archivo',sans-serif",fontStyle:"italic",
             fontVariationSettings:"'wdth' 112,'wght' 900",fontSize:18,color:"#FF9E1B",
             whiteSpace:"nowrap",overflow:"hidden",textOverflow:"ellipsis"}}>{lbl(champId)}</div>
      </div>}

      <div style={{marginTop:12,padding:"13px 14px",background:"rgba(0,229,255,.06)",borderLeft:"3px solid #00E5FF",
           fontSize:12.5,lineHeight:1.5,color:"#9FB0BC"}}>
        Group winners cross over against runners-up from another group, so a group-stage rematch is avoided
        wherever the seeding allows. Swipe sideways to follow it through{canScore ? "; tap a match to score it" : ""}.
        Reaching the quarter-final is worth +1, the semi +2, the final +3, and winning it +5 more.
      </div>
    </div>
  );
}'''

# ── PLAYER CARD ────────────────────────────────────────────────────────────
# Only the header of PlayerDetail is replaced — the canvas's card is simpler
# than what this app already shows, and swapping it in wholesale would have
# thrown away the rivalries, badges, loyalty lockout and the WhatsApp card,
# which are real features and not in the canvas at all. So the head becomes
# the canvas card (rank and streak chips, the name, three stat tiles, form as
# a last-8 grid) and everything below it stays.
#
# The admin photo-upload control is carried over; it is how the roster's
# photos get there in the first place.
PLAYER_HEAD_NEW = r'''{(() => {
        const form = recentForm(playerId, state.sessions);
        const dec = entry.stats.groupPlayed + entry.stats.qfReached + entry.stats.sfReached + entry.stats.finalsReached;
        const wins = entry.stats.groupWins + entry.stats.qfWins + entry.stats.sfWins + entry.stats.finalsWon;
        const winRate = dec ? Math.round(wins / dec * 100) : 0;
        const streak = currentStreak(form);
        const accent = streak >= 3 ? "#FF9E1B" : "#00E5FF";
        const last8 = form.slice(-8);
        const STATS = [
          ["POINTS", entry.totalPts, "#00E5FF"],
          ["WIN %", winRate + "%", "#F4F9FA"],
          ["NIGHTS", entry.stats.sessionsPlayed, "#F4F9FA"],
        ];
        return <div>
          {/* photo */}
          <div style={{position:"relative",width:"100%",height:200,background:"#0A1017",overflow:"hidden",
               display:"grid",placeItems:"center"}}>
            {player.photoUrl
              ? <img src={player.photoUrl} alt={player.name}
                     style={{width:"100%",height:"100%",objectFit:"cover",objectPosition:"center 28%"}} />
              : <div style={{fontFamily:"'Archivo',sans-serif",fontStyle:"italic",
                     fontVariationSettings:"'wdth' 125,'wght' 900",fontSize:64,color:"rgba(159,176,188,.25)"}}>
                  {(player.name || "?").split(" ").map(x => x[0]).join("").slice(0, 2).toUpperCase()}</div>}
            {canScore && <label style={{position:"absolute",right:10,bottom:10,width:36,height:36,
                 display:"grid",placeItems:"center",background:"rgba(0,229,255,.9)",cursor:"pointer"}}>
              {uploading ? <span style={{fontSize:9,color:"#050709"}}>…</span> : <I.camera size={15} style={{color:"#050709"}} />}
              <input type="file" accept="image/*" className="hidden" onChange={handlePhotoUpload} />
            </label>}
          </div>

          {/* identity */}
          <div style={{padding:"14px 2px",borderTop:`1px solid ${accent}55`}}>
            <div style={{display:"flex",alignItems:"center",gap:8}}>
              <div style={{padding:"4px 9px",background:"rgba(255,255,255,.05)",border:`1px solid ${accent}55`,
                   fontFamily:"'Archivo',sans-serif",fontWeight:800,fontSize:9,letterSpacing:".2em",color:accent}}>RANK {rank}</div>
              {streak > 0 && <div style={{padding:"4px 9px",background:streak >= 3 ? "rgba(255,158,27,.14)" : "rgba(0,229,255,.12)",
                   fontFamily:"'Archivo',sans-serif",fontWeight:800,fontSize:9,letterSpacing:".16em",
                   color:streak >= 3 ? "#FF9E1B" : "#00E5FF"}}>W{streak} STREAK</div>}
            </div>
            <div style={{fontFamily:"'Archivo',sans-serif",fontStyle:"italic",fontVariationSettings:"'wdth' 125,'wght' 900",
                 fontSize:32,lineHeight:.95,color:"#F4F9FA",marginTop:9}}>{player.name.toUpperCase()}</div>
          </div>

          {/* three tiles */}
          <div style={{display:"grid",gridTemplateColumns:"repeat(3,minmax(0,1fr))",gap:8}}>
            {STATS.map(([label, value, colour]) => (
              <div key={label} style={{padding:11,background:"rgba(9,14,20,.94)",
                   backgroundImage:`linear-gradient(180deg,${colour},rgba(92,107,120,.05))`,
                   backgroundSize:"3px 100%",backgroundRepeat:"no-repeat"}}>
                <div style={{fontFamily:"'Archivo',sans-serif",fontWeight:800,fontSize:8,letterSpacing:".2em",color:"#9FB0BC"}}>{label}</div>
                <div style={{fontFamily:"'Archivo',sans-serif",fontStyle:"italic",fontVariationSettings:"'wdth' 112,'wght' 900",
                     fontSize:24,lineHeight:1,color:colour,marginTop:5}}>{value}</div>
              </div>
            ))}
          </div>

          {/* form */}
          {last8.length > 0 && <div style={{marginTop:14,padding:14,background:"rgba(9,14,20,.94)",
               backgroundImage:"linear-gradient(180deg,#00E5FF,rgba(0,229,255,.06))",
               backgroundSize:"3px 100%",backgroundRepeat:"no-repeat"}}>
            <div style={{display:"flex",alignItems:"baseline",gap:8}}>
              <div style={{fontFamily:"'Archivo',sans-serif",fontWeight:800,fontSize:9,letterSpacing:".3em",color:"#00E5FF"}}>
                FORM · LAST {last8.length}</div>
              {streak > 0 && <div style={{marginLeft:"auto",fontFamily:"'Archivo',sans-serif",fontWeight:800,fontSize:9,
                   letterSpacing:".16em",color:accent}}>W{streak}</div>}
            </div>
            <div style={{display:"flex",gap:5,marginTop:11}}>
              {last8.map((r, i) => <div key={i} style={{flex:1,height:30,display:"grid",placeItems:"center",
                   background:r === "W" ? "rgba(0,229,255,.14)" : "rgba(255,255,255,.03)",
                   border:`1px solid ${r === "W" ? "rgba(0,229,255,.45)" : "rgba(92,107,120,.3)"}`,
                   fontFamily:"'JetBrains Mono',monospace",fontWeight:700,fontSize:11,
                   color:r === "W" ? "#00E5FF" : "#9FB0BC"}}>{r}</div>)}
            </div>
            <div style={{fontSize:12.5,lineHeight:1.5,color:"#9FB0BC",marginTop:10}}>
              Most recent on the right. {wins} wins from {dec} decided matches.</div>
          </div>}
        </div>;
      })()}'''

# ── 3-GROUP SEEDING FIX ────────────────────────────────────────────────────
# In a 3-group night with a thirds playoff, tier 3 is [best third, PLAYOFF_TBD]
# and the code's own comment states the invariant: "the known best third takes
# seed 7, the still-undecided qualifier seed 8".
#
# The rematch guard broke it. grp() returns null for the placeholder — it has
# no group yet — and the swap loop accepted that null as "compatible with
# everyone", so whenever seed 2 clashed with the best third the guard swapped
# the two tier-3 entries. That put the KNOWN best third at seed 8, against the
# top seed, and the unknown at seed 7.
#
# Two things wrong with that. It inverts the documented seeding, giving the
# best third the hardest draw it could get. And it does not actually fix the
# clash: the playoff winner can come from seed 2's group too, so the rematch
# simply reappears once the playoff resolves — the swap hides it rather than
# resolving it.
#
# A slot with no group is therefore not a valid swap partner.
SEED_GUARD_OLD = '''    for (let k = lo; k < hi; k++) {
      if (k === y) continue;
      // Swapping y and k must leave BOTH pairings clash-free.
      if (grp(seeded[k]) !== gx && grp(seeded[y]) !== grp(seeded[partnerOf(k)])) {'''
SEED_GUARD_NEW = '''    for (let k = lo; k < hi; k++) {
      if (k === y) continue;
      // Never trade places with a slot that has no group yet (the thirds-
      // playoff winner). It looks like a free fix because an unknown cannot
      // clash, but it demotes the known best third to seed 8 against the top
      // seed, and the clash returns anyway if the playoff is won by a team
      // from that same group.
      if (!grp(seeded[k])) continue;
      // Swapping y and k must leave BOTH pairings clash-free.
      if (grp(seeded[k]) !== gx && grp(seeded[y]) !== grp(seeded[partnerOf(k)])) {'''

# And the "who qualified" panel dropped any id containing TBD, so the seed
# number belonging to the undecided slot vanished from the list entirely —
# which is what the owner saw as "position 7 doesn't exist".
PANEL_OLD = '''        const collect = (m) => { if (!m) return; ["team1Id", "team2Id"].forEach(tk => {
          const id = m[tk];
          if (id && !String(id).includes("TBD") && !seen.has(id)) { const r = rankOf(id); if (r) { seen.add(id); rows.push({ id, g: r.g, rank: r.rank, seed: seedByTeam[id] || null }); } }
        }); };'''
PANEL_NEW = '''        const collect = (m) => { if (!m) return; ["team1Id", "team2Id"].forEach(tk => {
          const id = m[tk];
          if (!id || seen.has(id)) return;
          // A slot still waiting on the thirds playoff gets a row of its own.
          // Skipping it silently removed its seed number from the list, so the
          // panel read 1,2,3,4,5,6,8 and the missing seed looked like a bug in
          // the draw rather than a match that has not been played yet.
          if (String(id).includes("TBD")) {
            seen.add(id);
            rows.push({ id, g: null, rank: null, seed: seedByTeam[id] || null, pending: true });
            return;
          }
          const r = rankOf(id);
          if (r) { seen.add(id); rows.push({ id, g: r.g, rank: r.rank, seed: seedByTeam[id] || null }); }
        }); };'''


# The panel's row, taught to render a pending slot. Bounded in the live stream
# at build time because it carries colours the sweep has already rewritten.
PANEL_ROW_FROM = '<div className="space-y-1">{rows.map(r => ('
PANEL_ROW_TO = '))}</div>'
PANEL_ROW_NEW = """<div className="space-y-1">{rows.map(r => (
            <div key={r.id} className="flex items-center gap-2 px-2 py-1.5 rounded-md" style={{ background: r.seed === 1 ? "rgba(0,229,255,.13)" : "rgba(19,19,19,.06)", border: r.seed === 1 ? "2px solid #0A0F14" : "2px solid transparent" }}>
              {r.seed
                ? <span className="font-mono text-xs font-bold flex items-center justify-center shrink-0" style={{ width: 22, height: 22, background: r.seed === 1 ? "#00E5FF" : "#0A0F14", color: "#F4F9FA", border: "1px solid rgba(244,249,250,.14)" }}>{r.seed}</span>
                : <span style={{ width: 22 }} className="shrink-0" />}
              {r.pending
                ? <span className="shrink-0" style={{ minWidth: 30, textAlign: "center", padding: "2px 5px", border: "1px dashed rgba(255,158,27,.5)", fontFamily: "'JetBrains Mono',monospace", fontSize: 10, fontWeight: 700, color: "#FF9E1B" }}>?</span>
                : <SeedBadge seed={r.g + r.rank} />}
              <span className="flex-1 text-xs truncate font-semibold" style={{ color: r.pending ? "#9FB0BC" : "#F4F9FA" }}>
                {r.pending ? "Winner of the 3rds playoff" : lbl(r.id)}</span>
              <span className="text-[10px] font-mono uppercase tracking-wide" style={{ color: r.pending ? "#FF9E1B" : "#9FB0BC" }}>
                {r.pending ? "To be played" : why(r.rank)}</span>
            </div>
          ))}</div>"""

# ── AUTO-CLOSE THE NIGHT ───────────────────────────────────────────────────
# The last score of a session is the final's. When it lands, the session marks
# itself complete and the MVP is crowned, so nobody has to remember two extra
# taps while packing up.
AUTOCLOSE_OLD = '''  const mvpPlayer = state.players.find(p => p.id === session.mvpId);
  const sessionPhotos = session.photos || [];'''
AUTOCLOSE_NEW = '''  const mvpPlayer = state.players.find(p => p.id === session.mvpId);
  const sessionPhotos = session.photos || [];

  // ── When the final is scored, close the night ──
  // Three guards, each earning its place:
  //   canScore   — every phone in the club has this session open. Without it
  //                they would all race to write the same change.
  //   autoClosed — a latch, so an admin who deliberately re-opens a finished
  //                session is not overruled a second later by this effect.
  //   the vote   — crowning is only done from what the vote actually decided.
  //                No votes means no MVP and voting is left OPEN, because on
  //                most nights the voting starts after the final is played;
  //                closing it here would end a vote before it began. A tie at
  //                the top is left to a human rather than settled by whichever
  //                key happened to come first.
  const finalWinner = (session.bracket && session.bracket.final && session.bracket.final.winner) || null;
  useEffect(() => {
    if (!canScore || !finalWinner || session.autoClosed) return;
    updateSession(s => {
      const next = { ...s, completed: true, autoClosed: true };
      const tally = Object.entries(s.mvpVotes || {}).sort((a, b) => b[1] - a[1]);
      const tied = tally.length > 1 && tally[0][1] === tally[1][1];
      if (tally.length && !s.mvpId && !tied) {
        next.mvpId = tally[0][0];
        next.mvpVotingOpen = false;
      }
      return next;
    });
  }, [canScore, finalWinner, session.autoClosed]);'''

# ── GROUP OF 3 · GHOST BYE ─────────────────────────────────────────────────
# A group of 3 gives each team only 2 matches, but series points count your
# best 3 group results — so that group could never reach the cap and every
# player in it lost up to 3 points (6 on a 2x night) purely for how the draw
# fell. Each team in an undersized group now receives a notional 6-0 bye win
# to bring it up to three counted results, the same device equalizeThirds
# already uses to compare thirds across groups of different sizes.
#
# Three deliberate limits:
#
#   · The ghost lands in `counted` only, never in `all`. `all` is what
#     calcGroupStandingsNormalized reads to seed the bracket, and that path
#     ALREADY equalises, by cutting every group to the smallest group's match
#     count. A 6-0 would sort to the top and take one of those slots, so a
#     group-of-3 team would be seeded on one real result plus a free win while
#     a group-of-4 team is seeded on two real ones. The two mechanisms would
#     double-count, in opposite directions.
#
#   · Wins, matches played and win rate are untouched. They are counted in a
#     separate loop over real matches, so nobody is credited with a match they
#     did not play — only the points are made whole.
#
#   · You have to turn up. A team with no played matches gets no ghosts,
#     otherwise a group that never took the court would bank 9 points.
GHOST_OLD = '''  const playedActual = out.length;
  out.sort((a, b) => b.pts - a.pts || (b.gf - b.ga) - (a.gf - a.ga) || b.gf - a.gf);
  return { all: out, counted: out.slice(0, GROUP_COUNTED_GAMES), playedActual };'''
GHOST_NEW = '''  const playedActual = out.length;
  out.sort((a, b) => b.pts - a.pts || (b.gf - b.ga) - (a.gf - a.ga) || b.gf - a.gf);
  // A group too small to offer GROUP_COUNTED_GAMES matches tops each of its
  // teams up with notional 6-0 bye wins, so the draw cannot cost a player
  // points. Appended after the sort, so a ghost can only ever fill a slot no
  // real result reached — and only for a team that actually played.
  const gTeam = (session.teams || []).find(t => t.id === teamId);
  const gSize = gTeam ? (session.teams || []).filter(t => t.group === gTeam.group).length : 0;
  const ghosts = out.length > 0 ? Math.max(0, GROUP_COUNTED_GAMES - Math.max(0, gSize - 1)) : 0;
  const withByes = ghosts
    ? out.concat(Array.from({ length: ghosts }, () => ({ pts: 3, w: 1, gf: 6, ga: 0, bye: true })))
    : out;
  return { all: out, counted: withByes.slice(0, GROUP_COUNTED_GAMES), playedActual, byes: ghosts };'''

# And say so on the screen, so nobody wonders where the points came from.
GHOST_NOTE_OLD = '''      {isUneven && ('''
GHOST_NOTE_NEW = '''      {(() => {
        const small = groups.filter(x => {
          const n = (session.teams || []).filter(t => t.group === x).length;
          return n > 0 && n < GROUP_COUNTED_GAMES + 1;
        });
        if (!small.length) return null;
        return <div className="flex gap-2.5 p-3" style={{ background:"rgba(0,229,255,.08)", border:"1px solid rgba(0,229,255,.35)" }}>
          <I.alert size={16} className="shrink-0 mt-0.5" style={{ color:"#00E5FF" }} />
          <div>
            <div className="text-xs font-bold" style={{ color:"#00E5FF" }}>Bye awarded · group {small.join(" and ")}</div>
            <div className="text-[11px] mt-0.5" style={{ color:"#9FB0BC" }}>
              Series points count your best 3 group results, and this group only plays {Math.max(0, (session.teams || []).filter(t => t.group === small[0]).length - 1)}.
              Every team in it gets a notional 6&ndash;0 bye win to make up the difference, so the draw costs nobody points.
              The table below and the knockout seeding both use real matches only.
            </div>
          </div>
        </div>;
      })()}
      {isUneven && ('''

# ── THE BYE ALSO COUNTS FOR KNOCKOUT SEEDING ───────────────────────────────
# Owner's call, reversing the limit above.
#
# The seeding path used to cut every group down to the smallest group's match
# count. With a group of 3 present that meant everyone was seeded on their best
# 2, dragging the whole field down to the smallest group. Now every team is
# seeded on its best GROUP_COUNTED_GAMES results with byes topping up the
# undersized groups — lifting the small group up instead of pulling everyone
# else down, and matching exactly how series points are counted.
#
# This only behaves differently when a group smaller than 4 exists. For 5/4/4 —
# the only uneven shape that has ever run — the old rule already kept 3, which
# is what .counted returns, so nothing about past or present seeding moves.
SEEDNORM_OLD = '''  const keep = Math.max(1, Math.min(...sizes) - 1);
  const rows = teams.map(team => {
    const best = teamGroupResults(session, team.id).all.slice(0, keep);'''
SEEDNORM_NEW = '''  // Seed on the same results the series points count: best
  // GROUP_COUNTED_GAMES, with an undersized group's 6-0 byes making up the
  // difference. The old rule cut everyone to the smallest group's match count,
  // which levelled down; this levels up, and keeps one definition of "your
  // results" for both the leaderboard and the bracket.
  const rows = teams.map(team => {
    const best = teamGroupResults(session, team.id).counted;'''
