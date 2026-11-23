# MUSCAT HEIST — portrait pipeline

Generates cinematic illustrated portraits for league players from their
reference photos, and publishes them to <https://heist.urbanpadel.om>.

## Why there is no browser automation here

The site exposes a direct API, so Playwright is unnecessary:

| Endpoint | Auth | Use |
|---|---|---|
| `GET /api/brief` | none | who needs a portrait, the style prompt, exact filenames |
| `GET /api/roster` | none | all players: `id`, `name`, `ref`, `heist` |
| `GET /api/ref/{id}` | none | reference photo (JPEG) |
| `POST /api/login` | — | `{pin}` → bearer token |
| `POST /api/photo/{id}` | Bearer | `{image: "data:image/jpeg;base64,…"}` → `{ok, url}` |

Uploading keys on **player id**, so the filename matching the web page does for
drag-and-drop batches never comes into play. Files are still written under the
brief's exact names, because that is what the brief asks for and it keeps the
output usable by hand.

`DELETE /api/photo/{id}` also exists. **This script never calls it.** Nothing
here can remove or overwrite an existing portrait unless you pass `--force`.

## Setup

Needs Python 3.11+ with `requests` and `pillow`. On this machine that is
`python3.13`:

```bash
pip install -r requirements.txt
cp config.example.json config.json
```

Then put two secrets in `config.json` (it is gitignored), or supply them as
environment variables instead, which override the file:

```bash
export HEIST_PIN=...          # the /photos/ PIN
export OPENAI_API_KEY=sk-...
```

## Running

```bash
python3.13 heist.py fetch                 # brief + style prompt + 36 references
python3.13 heist.py generate --limit 3    # PILOT: three players first
python3.13 heist.py sheet                 # contact-sheet.jpg, reference | portrait
python3.13 heist.py generate              # the rest, once likeness is approved
python3.13 heist.py upload                # DRY RUN — lists what would go
python3.13 heist.py upload --yes          # publish
python3.13 heist.py status                # per-player progress
```

Useful flags: `--players "Riyadh,Mustafa"` to target individuals, `--limit N`
to cap a run, `--force` to redo work already marked done.

## How it behaves

**One player at a time.** Each generation call sends exactly one reference and
writes exactly one portrait before moving on, so identities cannot mix.

**Resumable.** `state.json` records every player by id — generated, uploaded,
attempt count, last error. Interrupt any command and re-run it; finished
players are skipped. Writes are atomic, so a kill mid-write cannot corrupt it.

**Generation and publishing are separate.** `generate` never uploads. `upload`
is a dry run unless you pass `--yes`, and prints exactly what it would send.

**Retries.** Rate limits and 5xx back off and retry up to `max_retries`.
A 4xx that retrying cannot fix (bad key, rejected prompt, bad size) fails fast.

**Logging.** Everything to `run.log` and the terminal. The final summary names
which players uploaded and which failed, with the reason.

## Image settings

The site builds a 1080×1350 canvas and uploads JPEG at quality 0.88, so that is
what we produce. The API cannot be asked for 1080×1350 directly — both edges
must divide by 16 — so generation happens at **1536×1920** (also exactly 4:5)
and is downscaled with Lanczos. That is sharper than generating at target size.

`input_fidelity` is deliberately not sent: on `gpt-image-2.x` it is always high,
and passing it is documented as an error.

> `gpt-image-1` was shut down on 23 October 2026. The config defaults to
> `gpt-image-2.6-sunburst`, the current default and the better of the 2.6 pair
> for precise edits. `gpt-image-2.6-flare` is faster and cheaper if you want to
> trade detail for cost.

## Likeness

The brief's hardest requirement is *"keep their face, skin tone, hair, beard and
build exactly."* Image models tend to drift toward a generic attractive face,
which is precisely what the brief forbids. Hence the pilot-then-review workflow:
generate three, look at `contact-sheet.jpg` beside the originals, and only then
commit to the remaining players. If likeness is poor, switching provider is a
two-line change in `config.json` plus a new request shape.

These are 36 identifiable people and the portraits get published under the
league's name, so it is worth being sure the players are content with that.
