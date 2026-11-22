#!/usr/bin/env python3
"""Muscat Heist phase 1 — the components preview page (handoff KICKOFF phase 1).

Writes brand/heist/dev-components.html: every shared component in every size
and state, rendered from the handoff's own fixtures, plus the top of Home
composed ONLY from those components so it can be laid beside
handoff/screenshots/01-home.png.

The page is the same shape as the app will be — React 18 and Babel 7 pinned on
unpkg, the CSS and components inlined — so what passes here is what ships.

    python3 ops/build-heist-dev.py
    node ops/shots-heist-dev.mjs          # 375 + 360 screenshots and checks
"""
import json
import os

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
H = os.path.join(HERE, "brand", "heist")
OUT = os.path.join(H, "dev-components.html")

season = json.load(open(os.path.join(HERE, "heist-season.json"), encoding="utf-8"))
players = json.load(open(os.path.join(H, "handoff", "fixtures", "players.json")))["players"]
css = open(os.path.join(H, "heist.css"), encoding="utf-8").read()
jsx = open(os.path.join(H, "heist-components.jsx"), encoding="utf-8").read()

# The fixtures name /players/pNN.png, which do not exist; the reference
# screenshots draw the stand-in paintings instead, so the preview does too.
# This mapping is PREVIEW ONLY — the app reads player.photo from the roster.
ART = {"p01": ("art/art-corniche.jpg", "34% 18%"), "p02": ("art/art-smash.jpg", "center 14%"),
       "p03": ("art/art-carpark.jpg", "40% 20%"), "p04": ("art/art-rivals.jpg", "82% 18%"),
       "p05": ("art/art-rivals.jpg", "18% 18%")}
for p in players:
    a = ART.get(p["id"])
    p["photo"], p["photoPos"] = (a if a else (None, None))

page = """<!doctype html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>Muscat Heist · components</title>
<link rel="stylesheet" href="../fonts/fonts.css">
<link rel="stylesheet" href="fonts/fonts.css">
<style>
@@CSS@@
/* preview chrome only */
html, body { margin: 0; background: var(--mn-navy); color: var(--mn-sand); font-family: var(--mn-font-ui); }
.dev { max-width: 760px; margin: 0 auto; padding: 24px var(--mn-page-x) 140px; display: flex; flex-direction: column; gap: 34px; }
.dev h2 { margin: 0 0 12px; }
.row { display: flex; flex-wrap: wrap; gap: 14px; align-items: flex-end; }
.phone { position: relative; width: 100%; max-width: 375px; height: 520px; overflow: hidden; border-radius: 28px; background: var(--mn-navy); border: var(--mn-glass-border); }
</style>
</head><body>
<div id="root"></div>
<script>window.MH_SEASON = @@SEASON@@; window.MH_PLAYERS = @@PLAYERS@@;</script>
<script src="https://unpkg.com/react@18/umd/react.production.min.js"></script>
<script src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js"></script>
<script src="https://unpkg.com/@babel/standalone@7/babel.min.js"></script>
<script type="text/babel" data-presets="react">
@@JSX@@

function Dev() {
  const P = window.MH_PLAYERS;
  const [pill, setPill] = React.useState("upcoming");
  const [grp, setGrp] = React.useState("A");
  const [tab, setTab] = React.useState("home");
  // the fixtures are a table after FIVE nights, so rep is read at five
  const lead = P[0];
  return (
    <div className="dev">
      <section>
        <MhLabel tone="peach">Muscat Heist · Vol.10</MhLabel>
        <MhDisplay size={44} style={{ marginTop: 6 }}>Components</MhDisplay>
        <MhSerif>Every shared part, every size and state, from the handoff's fixtures.</MhSerif>
      </section>

      <section>
        <h2><MhLabel>Home · top of screen, components only</MhLabel></h2>
        <div className="phone" data-shot="home-top">
          <MhTopBar logo="up-logo-tight.png" line={`Vol.10 · ${MH.month}`} />
          <MhHeroCut height={470} src="art/art-corniche.jpg" pos="34% 20%">
            <div style={{ position: "absolute", left: 22, top: 250 }}><MhTitleLockup size="S" /></div>
          </MhHeroCut>
        </div>
      </section>

      <section>
        <h2><MhLabel>Title lockup · S · M · L</MhLabel></h2>
        <div className="row" style={{ alignItems: "flex-start", gap: 28 }}>
          <MhTitleLockup size="S" />
          <MhTitleLockup size="M" center />
          <MhTitleLockup size="L" center presents={MH.presents} />
        </div>
      </section>

      <section>
        <h2><MhLabel>Crew card · M · every tier (foil on Legend and Elite only)</MhLabel></h2>
        <div className="row">
          {[0, 1, 3, 9].map(i => {
            const p = P[i] || P[P.length - 1];
            return <MhCrewCard key={p.id} player={p} rank={p.rank} points={p.points} rep={mhRepAt(p.points, 5)} size="M" onClick={() => {}} />;
          })}
          <MhCrewCard player={{ name: "No Photo Yet" }} rank={12} points={40} rep={mhRepAt(40, 5)} size="M" />
        </div>
      </section>

      <section>
        <h2><MhLabel>Crew card · S (no foil) · L (stats, Legend tilt)</MhLabel></h2>
        <div className="row" style={{ alignItems: "flex-start" }}>
          <MhCrewCard player={P[4]} rank={5} points={P[4].points} rep={mhRepAt(P[4].points, 5)} size="S" foil={false} />
          <MhCrewCard player={lead} rank={1} points={lead.points} rep={mhRepAt(lead.points, 5)} size="L" stats={lead.stats} />
          <MhCrewCard player={P[1]} rank={2} points={P[1].points} rep={mhRepAt(P[1].points, 5)} size="L"
            stats={{ smash: 88, wall: null, speed: 79, clutch: null }} />
        </div>
      </section>

      <section>
        <h2><MhLabel>Glass card · plain and each accent</MhLabel></h2>
        <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
          <MhGlass><MhLabel tone="peach">Next job · EP.07</MhLabel><MhDisplay size={28} style={{ marginTop: 3 }}>WED 23 DEC</MhDisplay><MhSerif>17:30 · {MH.venue}</MhSerif></MhGlass>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
            <MhGlass accent="peach"><MhLabel tone="peach">Serving</MhLabel></MhGlass>
            <MhGlass accent="teal"><MhLabel tone="teal">You</MhLabel></MhGlass>
            <MhGlass accent="gold"><MhLabel tone="gold">Finale</MhLabel></MhGlass>
            <MhGlass accent="coral"><MhLabel tone="coral">● Live</MhLabel></MhGlass>
          </div>
        </div>
      </section>

      <section>
        <h2><MhLabel>Pills · filter, tabs, round</MhLabel></h2>
        <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
          <MhPills label="Filter" items={[["upcoming", "Upcoming"], ["done", "Done"], ["all", "All"]]} value={pill} onChange={setPill} />
          <MhPills label="Groups" round items={["A", "B", "C", "D"]} value={grp} onChange={setGrp} />
        </div>
      </section>

      <section>
        <h2><MhLabel>Buttons · primary · ghost · light · live 56px</MhLabel></h2>
        <div className="row">
          <MhButton>Share</MhButton>
          <MhButton kind="ghost">Full results</MhButton>
          <MhButton kind="light">Lock result</MhButton>
          <MhButton live>+1 Munther</MhButton>
        </div>
      </section>

      <section>
        <h2><MhLabel>Scene tag · billing · avatar</MhLabel></h2>
        <div className="row" style={{ alignItems: "center" }}>
          <MhSceneTag>EP.07 · The Rematch</MhSceneTag>
          <MhSceneTag gold>Episode complete</MhSceneTag>
          <MhAvatar player={lead} size={42} ring="coral" />
          <MhAvatar player={{ name: "No Photo" }} size={42} ring="teal" />
        </div>
        <MhBilling style={{ marginTop: 16 }} parts={["Urban Playground", { link: "presents a" }, "social padel league", { link: "starring" },
          P.slice(0, 5).map(p => p.name).join(" · ")]} />
      </section>

      <MhBottomNav tab={tab} onTab={setTab} />
      <MhGrain />
    </div>
  );
}
ReactDOM.createRoot(document.getElementById("root")).render(<Dev />);
</script>
</body></html>
"""
for k, v in (("@@CSS@@", css), ("@@JSX@@", jsx), ("@@SEASON@@", json.dumps(season, ensure_ascii=False)),
             ("@@PLAYERS@@", json.dumps(players))):
    assert page.count(k) == 1, k
    page = page.replace(k, v)

open(OUT, "w", encoding="utf-8").write(page)
print(f"wrote {os.path.relpath(OUT, HERE)}  {len(page)//1024}KB")
