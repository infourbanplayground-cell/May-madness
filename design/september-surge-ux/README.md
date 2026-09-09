# Vol.7 UI/UX enhancement pass

Source bundle: `UIUX_Enhancement_Request.zip`, 2026-09-09. `skin-source.html`
is the delivered file verbatim (Vol.7 app + the new layer); the `.dc.html`
files are the Claude Design canvases behind it.

The build does **not** consume these files. `build-september-surge-app.py`
carries the layer as `UX_LAYER` / `UX_SCRIPT` plus the `QUALIFY` substitutions,
so it survives a rebuild. These are kept as the reference for what was asked.

## Not taken, and why

| Dropped | Reason |
|---|---|
| Session tab-bar rebuild (4-up grid + action row) | An IA change, not paint. Owner chose to keep the single scrolling chip row. |
| Every `table` / `tbody` / `td` / `th` rule | This app has no `<table>`. Group standings are divs. 15 selectors, all matching nothing. |
| `tbody tr:nth-child(-n+2)` as "the qualifiers" | Qualification is 1, 2 or 4 per group, or top-2-plus-two-best-thirds, or all thirds. Rebuilt against the real rule — see below. |
| `.jh-srow` / `.jh-lbrow` energy + stagger rules | Those classes stopped being rendered when RANK was rebuilt to the design language. Retargeted onto `.sg-top` / `.sg-thin` / `.jh-mock-sess`. |
| `.sg-bump { display:inline-block }` | Would collapse any flex or grid child it landed on, and every number in this app is one. Animation kept, display rule dropped. |
| `September Surge - Layout Preview.html` | Ships a mock backend: it intercepts `/state`, `/save` and `/login`, answers from localStorage, and grants admin to any PIN. Review harness only — must never be deployed. |

## The qualifying mark

`qualifyingTeamIds(session)` mirrors `seedQF`'s rule exactly, so a group table
can never promise a spot the bracket won't honour:

- 4 groups, `all4r16` → top 3 of every group (12 to an R16)
- 3 groups → top 2 of every group **plus the two best thirds**, ranked by
  `compareThirds` on the normalised standings
- otherwise → top `getQualifyCount(session)` (1, 2 or 4) per group

It recomputes on every render, so the marks follow the scores as results are
entered rather than freezing at seeding time.
