# September Surge design handoff

Unpacked from `Site_improvement_feedback_surge_v2.zip`, sent by the owner on
2026-08-31, and committed here verbatim. It had already been lost once to a
container restart — it lived only in `/tmp` — which cost a round trip and a
wrong guess at the design before it was re-sent. It is in the repo so that
never has to happen again. Nothing in this directory is built or deployed.

| File | What it is |
|---|---|
| `README.md` | The handoff itself. Part A (UX changes) and Part B (the skin) |
| `September Surge - Design Language.html` | **The specification to match.** Open in a browser. Section 06 is the RANK screen |
| `August Attack - Design Review.html` | The UX critique Part A came from — why HOME and RANK are shaped this way |
| `Surge Logo.html` | Wordmark and emblem treatment |
| `surge-skin.css` | The Vol.7 skin layer. Copied to `ops/surge-skin.css`, which is what the build reads |
| `index-v2.html` | The handoff's own copy of the app with Part A applied. **Not our baseline** — see below |
| `indexreadable.html` | The same file formatted; the README's line numbers refer to it |
| `assets/surge/` | The recoloured Urban Playground mark. Shipped copies live in `brand/september-surge/` |
| `_ds/`, `support.js` | Tooling from the bundle. Unused here |

## Why the build does not start from `index-v2.html`

The handoff calls it "the real application file, already patched", and for the
handoff's own purposes it is. But it forked from Vol.6 before the bracket
seeding work, the admin QF seeding modal and `DOUBLE_FROM_SESSION` landed, so
adopting it wholesale would silently roll back a month of scoring fixes.

So `build-september-surge-app.py` keeps `august-attack-index.html` as the
baseline — the way every volume has inherited the previous one — and ports the
parts of Part A the live app was missing. Most of Part A was already there:
the search field, the rank-4+ thin rows, the collapsed tail, the "who am I"
pinned row. Section 06's top-three treatment was not, and that is what the
build's `rebuild_rank()` step supplies.

`index-v2.html` stays here as the reference for anything else from Part A that
turns out to be worth lifting.
