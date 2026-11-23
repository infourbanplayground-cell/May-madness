#!/usr/bin/env python3
"""
MUSCAT HEIST — player portrait pipeline.

Four commands, deliberately separate so generation and publishing never happen
in the same breath:

    fetch     download the brief, the roster and every reference photo
    generate  make portraits, ONE PLAYER AT A TIME, writing files to out/
    sheet     build a contact sheet of reference vs portrait for review
    upload    publish approved portraits via the site's API  (needs --yes)

Everything is resumable: state.json records each player by id, and a command
skips whatever is already done unless told to redo it.

Notes on the site, established by inspecting it:
  * POST /api/photo/{id} takes {"image": "<data url>"} with a bearer token, so
    no browser automation is needed at all.
  * Uploads key on PLAYER ID, not filename, which sidesteps the name-matching
    the web page does for drag-and-drop batches.
  * DELETE /api/photo/{id} exists. This script never calls it.
"""

from __future__ import annotations

import argparse
import base64
import io
import json
import logging
import os
import re
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import requests
from PIL import Image

HERE = Path(__file__).resolve().parent
CONFIG_PATH = HERE / "config.json"
STATE_PATH = HERE / "state.json"
OUT_DIR = HERE / "out"
REF_DIR = HERE / "refs"
LOG_PATH = HERE / "run.log"

log = logging.getLogger("heist")


# ─── config & state ───────────────────────────────────────────────────────────

def load_config() -> dict[str, Any]:
    if not CONFIG_PATH.exists():
        sys.exit(
            f"No config.json.\n"
            f"  cp {CONFIG_PATH.with_name('config.example.json')} {CONFIG_PATH}\n"
            f"then fill in the heist PIN and your OpenAI API key."
        )
    cfg = json.loads(CONFIG_PATH.read_text())
    # Environment wins, so secrets can stay out of the file entirely.
    if os.environ.get("OPENAI_API_KEY"):
        cfg["openai"]["api_key"] = os.environ["OPENAI_API_KEY"]
    if os.environ.get("HEIST_PIN"):
        cfg["heist"]["pin"] = os.environ["HEIST_PIN"]
    for path, val in (("heist.pin", cfg["heist"]["pin"]),
                      ("openai.api_key", cfg["openai"]["api_key"])):
        if not val or val.startswith("PUT_"):
            sys.exit(f"config.json: {path} is still a placeholder.")
    return cfg


class State:
    """Per-player progress, keyed by player id. Written after every change."""

    def __init__(self) -> None:
        self.data: dict[str, Any] = {"players": {}}
        if STATE_PATH.exists():
            try:
                self.data = json.loads(STATE_PATH.read_text())
            except json.JSONDecodeError:
                log.warning("state.json was unreadable; starting a fresh one")
        self.data.setdefault("players", {})

    def get(self, pid: str) -> dict[str, Any]:
        return self.data["players"].setdefault(
            pid, {"generated": False, "uploaded": False, "attempts": 0, "error": None}
        )

    def save(self) -> None:
        tmp = STATE_PATH.with_suffix(".tmp")
        tmp.write_text(json.dumps(self.data, indent=2, ensure_ascii=False))
        tmp.replace(STATE_PATH)  # atomic, so an interrupt can't corrupt it


@dataclass
class Player:
    id: str
    name: str
    filename: str
    ref_url: str
    ref_path: Path = field(init=False)
    out_path: Path = field(init=False)

    def __post_init__(self) -> None:
        self.ref_path = REF_DIR / f"{self.id}.jpg"
        self.out_path = OUT_DIR / self.filename


# ─── the brief ────────────────────────────────────────────────────────────────

BRIEF_LINE = re.compile(
    r"^\s*\d+\.\s+(?P<name>.+?)\s+—\s+photo:\s+(?P<url>\S+)\s+—\s+save as:\s+(?P<file>.+?)\s*$"
)


def fetch_brief(cfg: dict) -> tuple[str, list[Player]]:
    """Return (style prompt, players). The brief is the single source of truth
    for who needs a portrait and what each file must be called."""
    url = f"{cfg['heist']['base_url']}/api/brief"
    log.info("fetching brief: %s", url)
    text = requests.get(url, timeout=60).text

    m = re.search(r"## Style prompt\s*(.+?)\s*## To do", text, re.S)
    if not m:
        sys.exit("could not find the style prompt in the brief — has its format changed?")
    style = m.group(1).strip()

    players: list[Player] = []
    for line in text.splitlines():
        hit = BRIEF_LINE.match(line)
        if not hit:
            continue
        pid = hit.group("url").rstrip("/").rsplit("/", 1)[-1]
        players.append(
            Player(id=pid, name=hit.group("name").strip(),
                   filename=hit.group("file").strip(), ref_url=hit.group("url"))
        )
    if not players:
        sys.exit("the brief listed no players — nothing to do")
    log.info("brief lists %d players needing portraits", len(players))
    return style, players


def cmd_fetch(cfg: dict, args) -> None:
    REF_DIR.mkdir(exist_ok=True)
    style, players = fetch_brief(cfg)
    (HERE / "style.txt").write_text(style)

    got = skipped = 0
    for p in players:
        if p.ref_path.exists() and not args.force:
            skipped += 1
            continue
        r = requests.get(p.ref_url, timeout=60)
        r.raise_for_status()
        p.ref_path.write_bytes(r.content)
        try:
            with Image.open(p.ref_path) as im:
                w, h = im.size
            note = "  LOW RES" if min(w / 1080, h / 1350) < 0.6 else ""
            log.info("ref %-28s %dx%d%s", p.name[:28], w, h, note)
        except Exception as exc:
            log.warning("ref %s downloaded but unreadable: %s", p.name, exc)
        got += 1
        time.sleep(0.2)

    print(f"\nreferences: {got} downloaded, {skipped} already present")
    print(f"style prompt saved to {HERE / 'style.txt'}")
    print(f"\nnext: python3 {Path(__file__).name} generate --limit 3     (a small pilot first)")


# ─── generation ───────────────────────────────────────────────────────────────

def generate_one(cfg: dict, style: str, p: Player) -> None:
    """One reference in, one portrait out. Never batched, so faces cannot mix."""
    oc = cfg["openai"]
    url = f"{oc['base_url']}/images/edits"

    # input_fidelity is deliberately absent: on gpt-image-2.x it is always high
    # and sending it is documented as an error.
    data = {
        "model": oc["model"],
        "prompt": style,
        "size": oc["size"],
        "quality": oc["quality"],
        "output_format": oc["output_format"],
        "n": "1",
    }

    last: Exception | None = None
    for attempt in range(1, int(oc["max_retries"]) + 1):
        try:
            with p.ref_path.open("rb") as fh:
                resp = requests.post(
                    url,
                    headers={"Authorization": f"Bearer {oc['api_key']}"},
                    data=data,
                    files={"image[]": (p.ref_path.name, fh, "image/jpeg")},
                    timeout=int(oc["timeout_seconds"]),
                )
            if resp.status_code == 200:
                payload = resp.json()["data"][0]
                raw = base64.b64decode(payload["b64_json"])
                write_final(cfg, raw, p)
                return
            if resp.status_code in (429, 500, 502, 503, 504):
                raise RuntimeError(f"HTTP {resp.status_code}: {resp.text[:200]}")
            # 4xx that retrying will not fix (bad key, rejected prompt, bad size)
            raise RuntimeError(f"HTTP {resp.status_code}: {resp.text[:400]}")
        except Exception as exc:  # noqa: BLE001 — surfaced to the caller below
            last = exc
            retriable = "HTTP 4" not in str(exc) or "HTTP 429" in str(exc)
            if attempt < int(oc["max_retries"]) and retriable:
                wait = int(oc["retry_backoff_seconds"]) * attempt
                log.warning("%s: attempt %d failed (%s) — retrying in %ds",
                            p.name, attempt, exc, wait)
                time.sleep(wait)
                continue
            break
    raise RuntimeError(str(last))


def write_final(cfg: dict, raw: bytes, p: Player) -> None:
    """Downscale to the 1080x1350 the site expects and save under the brief's
    exact filename."""
    oc = cfg["output"]
    with Image.open(io.BytesIO(raw)) as im:
        im = im.convert("RGB")
        im = im.resize((oc["final_width"], oc["final_height"]), Image.LANCZOS)
        OUT_DIR.mkdir(exist_ok=True)
        im.save(p.out_path, format="PNG")


def cmd_generate(cfg: dict, args) -> None:
    style = (HERE / "style.txt").read_text().strip() if (HERE / "style.txt").exists() else None
    _, players = fetch_brief(cfg)
    if style is None:
        sys.exit("run `fetch` first")

    st = State()
    todo = []
    for p in players:
        if args.players and p.name.lower() not in {x.strip().lower() for x in args.players.split(",")}:
            continue
        s = st.get(p.id)
        if s["generated"] and p.out_path.exists() and not args.force:
            continue
        if not p.ref_path.exists():
            log.warning("%s: no reference downloaded — run fetch", p.name)
            continue
        todo.append(p)
    if args.limit:
        todo = todo[: args.limit]

    if not todo:
        print("nothing to generate — every requested player already has a portrait")
        return

    print(f"generating {len(todo)} portrait(s), one at a time\n")
    ok = fail = 0
    for i, p in enumerate(todo, 1):
        s = st.get(p.id)
        s["attempts"] += 1
        s["name"] = p.name
        s["filename"] = p.filename
        print(f"[{i}/{len(todo)}] {p.name} … ", end="", flush=True)
        try:
            t0 = time.time()
            generate_one(cfg, style, p)
            s.update(generated=True, error=None)
            ok += 1
            print(f"done in {time.time() - t0:.0f}s -> {p.filename}")
            log.info("generated %s -> %s", p.name, p.filename)
        except Exception as exc:  # noqa: BLE001
            s.update(generated=False, error=str(exc)[:500])
            fail += 1
            print(f"FAILED — {str(exc)[:120]}")
            log.error("generate failed for %s: %s", p.name, exc)
        finally:
            st.save()

    print(f"\ngenerated {ok}, failed {fail}")
    if ok:
        print(f"review them: python3 {Path(__file__).name} sheet")


# ─── review ───────────────────────────────────────────────────────────────────

def cmd_sheet(cfg: dict, args) -> None:
    """Reference beside portrait, so likeness can be judged before publishing."""
    _, players = fetch_brief(cfg)
    pairs = [p for p in players if p.out_path.exists() and p.ref_path.exists()]
    if not pairs:
        sys.exit("no generated portraits yet")

    cell_w, cell_h, pad, label = 300, 375, 12, 26
    cols = 4
    rows = (len(pairs) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * (cell_w * 2 + pad * 3),
                              rows * (cell_h + pad + label)), (12, 10, 12))

    for i, p in enumerate(pairs):
        cx, cy = i % cols, i // cols
        x0 = cx * (cell_w * 2 + pad * 3) + pad
        y0 = cy * (cell_h + pad + label) + pad
        for j, path in enumerate((p.ref_path, p.out_path)):
            with Image.open(path) as im:
                im = im.convert("RGB")
                im.thumbnail((cell_w, cell_h))
                box = Image.new("RGB", (cell_w, cell_h), (20, 18, 20))
                box.paste(im, ((cell_w - im.width) // 2, (cell_h - im.height) // 2))
                sheet.paste(box, (x0 + j * (cell_w + pad), y0))

    out = HERE / "contact-sheet.jpg"
    sheet.save(out, quality=90)
    print(f"{len(pairs)} pairs (reference | portrait) -> {out}")
    print("check every face before uploading.")


# ─── upload ───────────────────────────────────────────────────────────────────

def heist_login(cfg: dict) -> str:
    r = requests.post(f"{cfg['heist']['base_url']}/api/login",
                      json={"pin": cfg["heist"]["pin"]}, timeout=30)
    if r.status_code != 200:
        sys.exit(f"login failed: HTTP {r.status_code} {r.text[:200]}")
    j = r.json()
    token = j.get("token") or j.get("jwt") or j.get("access_token")
    if not token:
        sys.exit(f"login returned no token: {json.dumps(j)[:300]}")
    return token


def cmd_upload(cfg: dict, args) -> None:
    _, players = fetch_brief(cfg)
    st = State()

    ready = [p for p in players
             if p.out_path.exists()
             and st.get(p.id)["generated"]
             and (not st.get(p.id)["uploaded"] or args.force)]
    if args.players:
        want = {x.strip().lower() for x in args.players.split(",")}
        ready = [p for p in ready if p.name.lower() in want]
    if args.limit:
        ready = ready[: args.limit]

    if not ready:
        print("nothing to upload")
        return

    print(f"{len(ready)} portrait(s) ready to upload:")
    for p in ready:
        print(f"   {p.name}  ({p.filename} -> player {p.id})")

    if not args.yes:
        print("\nDRY RUN — nothing was sent. Re-run with --yes to publish.")
        return

    token = heist_login(cfg)
    q = cfg["output"]["upload_jpeg_quality"]
    ok = fail = 0
    failures: list[tuple[str, str]] = []

    for i, p in enumerate(ready, 1):
        s = st.get(p.id)
        print(f"[{i}/{len(ready)}] {p.name} … ", end="", flush=True)
        try:
            with Image.open(p.out_path) as im:
                buf = io.BytesIO()
                im.convert("RGB").save(buf, format="JPEG", quality=q)
            data_url = "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()
            r = requests.post(
                f"{cfg['heist']['base_url']}/api/photo/{p.id}",
                headers={"Authorization": f"Bearer {token}",
                         "Content-Type": "application/json"},
                json={"image": data_url}, timeout=120,
            )
            body = r.json() if r.headers.get("content-type", "").startswith("application/json") else {}
            if r.status_code == 200 and body.get("ok"):
                s.update(uploaded=True, url=body.get("url"), error=None)
                ok += 1
                print("uploaded")
                log.info("uploaded %s (%s) -> %s", p.name, p.id, body.get("url"))
            else:
                msg = body.get("error") or f"HTTP {r.status_code} {r.text[:150]}"
                raise RuntimeError(msg)
        except Exception as exc:  # noqa: BLE001
            s.update(uploaded=False, error=str(exc)[:500])
            fail += 1
            failures.append((p.name, str(exc)[:150]))
            print(f"FAILED — {str(exc)[:110]}")
            log.error("upload failed for %s: %s", p.name, exc)
        finally:
            st.save()
            time.sleep(0.4)

    print(f"\nuploaded {ok}, failed {fail}")
    if failures:
        print("\nfailed players:")
        for name, why in failures:
            print(f"   {name}: {why}")
        print("re-run the same command to retry only these.")


# ─── status ───────────────────────────────────────────────────────────────────

def cmd_status(cfg: dict, args) -> None:
    _, players = fetch_brief(cfg)
    st = State()
    gen = up = pend = 0
    print(f"{'player':28} {'ref':>4} {'made':>5} {'up':>4}  note")
    print("-" * 72)
    for p in players:
        s = st.get(p.id)
        gen += bool(s["generated"])
        up += bool(s["uploaded"])
        pend += not s["generated"]
        print(f"{p.name[:28]:28} {'y' if p.ref_path.exists() else '-':>4} "
              f"{'y' if s['generated'] else '-':>5} {'y' if s['uploaded'] else '-':>4}  "
              f"{(s.get('error') or '')[:28]}")
    print("-" * 72)
    print(f"{len(players)} players · {gen} generated · {up} uploaded · {pend} still to make")


# ─── entry point ──────────────────────────────────────────────────────────────

def main() -> None:
    ap = argparse.ArgumentParser(description="MUSCAT HEIST portrait pipeline")
    sub = ap.add_subparsers(dest="cmd", required=True)

    f = sub.add_parser("fetch", help="download brief, style prompt and references")
    f.add_argument("--force", action="store_true", help="re-download existing references")

    g = sub.add_parser("generate", help="generate portraits, one player at a time")
    g.add_argument("--limit", type=int, help="stop after N players (use for a pilot)")
    g.add_argument("--players", help="comma-separated names, e.g. \"Riyadh,Mustafa\"")
    g.add_argument("--force", action="store_true", help="regenerate even if done")

    sub.add_parser("sheet", help="build contact-sheet.jpg for review")

    u = sub.add_parser("upload", help="publish portraits (dry run unless --yes)")
    u.add_argument("--yes", action="store_true", help="actually publish")
    u.add_argument("--limit", type=int)
    u.add_argument("--players")
    u.add_argument("--force", action="store_true", help="re-upload already-uploaded players")

    sub.add_parser("status", help="show per-player progress")

    args = ap.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-7s %(message)s",
        handlers=[logging.FileHandler(LOG_PATH), logging.StreamHandler(sys.stderr)],
    )
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    cfg = load_config()
    {"fetch": cmd_fetch, "generate": cmd_generate, "sheet": cmd_sheet,
     "upload": cmd_upload, "status": cmd_status}[args.cmd](cfg, args)


if __name__ == "__main__":
    main()
