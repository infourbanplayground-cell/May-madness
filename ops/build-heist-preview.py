#!/usr/bin/env python3
"""Muscat Heist — the screens preview (handoff phases 2+), from fixture data.

Writes brand/heist/preview.html: the real screen components on the handoff's
fixtures, routed by hash (#home #jobs #wanted #me #crew #card/p01 #take #session/6 #live #recap/5 #slides/5/1), so
each can be shot at 375x812 and laid beside handoff/screenshots/<nn>-*.png.

    python3 ops/build-heist-preview.py && node ops/shots-heist.mjs
"""
import json
import os

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
H = os.path.join(HERE, "brand", "heist")
season = json.load(open(os.path.join(HERE, "heist-season.json"), encoding="utf-8"))
read = lambda n: open(os.path.join(H, n), encoding="utf-8").read()

page = """<!doctype html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="theme-color" content="#0F1B2B">
<title>Muscat Heist · preview</title>
<link rel="stylesheet" href="../fonts/fonts.css">
<link rel="stylesheet" href="fonts/fonts.css">
<style>@@CSS@@</style>
</head><body>
<div id="root"></div>
<script>window.MH_SEASON = @@SEASON@@;</script>
<script>@@DATA@@</script>
<script src="https://unpkg.com/react@18/umd/react.production.min.js"></script>
<script src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js"></script>
<script src="https://unpkg.com/@babel/standalone@7/babel.min.js"></script>
<script type="text/babel" data-presets="react">
@@COMPONENTS@@
@@SCREENS@@
@@NIGHT@@
@@MOMENTS@@
@@STORIES@@
// #story/<poster|contenders|card>/<id>: the bare 416x740 frame, for export and compare
function MhStoryOnly({ D, what, id }) {
  const S = { poster: MhStoryPoster, contenders: MhStoryContenders, card: MhStoryCard }[what] || MhStoryPoster;
  return <div className="mh-page mh-storyonly"><S D={D} id={id} /></div>;
}
function Preview() {
  const read = () => (location.hash.slice(1) || "home").split("/");
  const [route, setRoute] = React.useState(read());
  const [stack, setStack] = React.useState([]);
  React.useEffect(() => { const f = () => setRoute(read()); addEventListener("hashchange", f); return () => removeEventListener("hashchange", f); }, []);
  const D = window.MH_PREVIEW;
  const go = (to, arg) => {
    if (to === "back") { history.back(); return; }
    const known = ["home", "jobs", "wanted", "me", "crew", "card", "take", "session", "live", "recap", "slides", "loading", "cardpull", "repup", "rival", "settled", "finale", "share", "story"];
    if (known.indexOf(to) < 0) return;      // later phases: session, recap, rival, receipt, signup
    location.hash = arg != null ? `${to}/${arg}` : to; scrollTo(0, 0);
  };
  const [name, arg, arg2] = route;
  const S = { home: MhHome, jobs: MhJobs, wanted: MhWanted, me: MhMe, crew: MhCrew, card: MhCardScreen, take: MhTake,
              session: MhSession, live: MhLive, recap: MhRecap, slides: MhSlides,
              loading: MhLoading, cardpull: MhCardPull, repup: MhRepUp, rival: MhRival, settled: MhSettled, finale: MhFinale,
              share: MhShareSheet, story: MhStoryOnly }[name] || MhHome;
  // the preview is the organiser's phone: matches are tappable, as in the reference
  return <S key={route.join("/")} D={D} go={go} no={arg} start={+arg2 || 0} canScore what={arg}
    id={name === "share" || name === "story" ? arg2 : arg}
    progress={name === "loading" && arg ? +arg / 100 : undefined} ready={!(name === "loading" && arg)} tip={name === "loading" ? 1 : undefined} />;
}
ReactDOM.createRoot(document.getElementById("root")).render(<Preview />);
</script>
</body></html>
"""
for k, v in (("@@CSS@@", read("heist.css")), ("@@SEASON@@", json.dumps(season, ensure_ascii=False)),
             ("@@DATA@@", read("preview-data.js")), ("@@COMPONENTS@@", read("heist-components.jsx")),
             ("@@SCREENS@@", read("heist-screens.jsx")), ("@@NIGHT@@", read("heist-night.jsx")), ("@@MOMENTS@@", read("heist-moments.jsx")), ("@@STORIES@@", read("heist-stories.jsx"))):
    assert page.count(k) == 1, k
    page = page.replace(k, v)
out = os.path.join(H, "preview.html")
open(out, "w", encoding="utf-8").write(page)
print(f"wrote {os.path.relpath(out, HERE)}  {len(page)//1024}KB")
