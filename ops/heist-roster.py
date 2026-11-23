#!/usr/bin/env python3.13
"""Muscat Heist — the player database: everybody, their photo, and how much
they play, so the photos can be redone in the Heist format and every card,
avatar and story picks them up.

    python3.13 ops/heist-roster.py build           # fetch every volume over ssh, write the db
    python3.13 ops/heist-roster.py import <dir>    # new Heist photos, named after the player
    python3.13 ops/heist-roster.py sheet           # the contact sheet (roster.html)

Writes brand/heist/roster/:
  players.json        the database (one record per person)
  players.csv         the same, for a spreadsheet
  photos/<id>.jpg     the CURRENT photo, as the live apps hold it
  heist/<id>.jpg      the NEW Heist-format photo, once imported
  roster.html         the contact sheet: who has a photo, who needs one

WHY ONE RECORD PER ID: players carry the same id across every volume since
June (the roster merge made that so), so a photo or a count keyed by id
cannot be split between two people or doubled for one. Names are NOT unique —
the roster has Mohammed, Khalid, Muhanad and Mohd twice each — so `import`
refuses a filename that matches two people rather than guessing.

WHERE THE PHOTOS COME FROM: every volume's /photos store (base64 data URLs),
newest volume first, so a player who replaced their photo keeps the new one.
Three players hold an older, different photo in an earlier volume; that one
is kept as `photoOlder` rather than thrown away. A Cloudinary `photoUrl` on
the record is a session crop, not a portrait, and is listed but not used.

Activity is NIGHTS PLAYED — sessions where the player was on a team — counted
in every volume's own state, plus UPRISING nights from the Americano app.
The sheet is ordered by it, because the people on the cards are the people
who turn up, and those are the photos worth chasing first.
"""
import base64, csv, hashlib, io, json, os, re, subprocess, sys, unicodedata
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "brand", "heist", "roster")
DB = os.path.join(OUT, "players.json")
# newest first: the first photo found for an id is the one kept
VOLUMES = [
    ("56 National Series", "http", 3011), ("Blackout Series", "http", 3009),
    ("September Surge", "file", "/var/www/surge.urbanpadel.om/public"),
    ("August Attack", "http", 3005), ("July Heat", "http", 3004), ("June Fury", "http", 3001),
]
# THE HEIST FORMAT. Portrait 4:5, the shape a phone camera crops to and the
# one every Heist frame can be cut from: the crew card's image window (8:7),
# the 34-200px round avatars, the rival split (60% of a half) and the stories.
# The face sits in the TOP THIRD, because every Heist crop anchors high.
HEIST = {"w": 1080, "h": 1350, "quality": 88}
# "playing now": anybody on a team since Blackout began, or at an UPRISING night.
# Those are the faces the Heist cards will carry first.
CURRENT_FROM = "2026-10-01"


def ssh(cmd):
    return subprocess.run(["ssh", "urbanpadel", cmd], capture_output=True, check=True).stdout


def fetch(kind, where, what):
    if kind == "http":
        raw = ssh(f"curl -s localhost:{where}/{what}")
    else:
        raw = ssh(f"cat {where}/{what}.json")
    d = json.loads(raw)
    return d.get("state", d.get("photos", d)) if what == "state" else d.get("photos", d)


def fold(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    s = re.sub(r"\b(al|el)[\s-]+", "al", s)            # "Al muatasim" and "Almuatasim" are one name
    s = re.sub(r"[^a-z0-9]+", "", s)
    return s or None                                    # emoji-only names fold to nothing: never a match


def build():
    os.makedirs(os.path.join(OUT, "photos"), exist_ok=True)
    people, photos, older = {}, {}, {}
    for vol, kind, where in VOLUMES:
        st = fetch(kind, where, "state")
        ph = fetch(kind, where, "photos")
        for p in st.get("players", []):
            r = people.setdefault(p["id"], {"id": p["id"], "name": p["name"], "volumes": [], "nights": 0,
                                             "lastPlayed": None, "photoUrl": p.get("photoUrl") or None})
            if p.get("photoUrl") and not r["photoUrl"]:
                r["photoUrl"] = p["photoUrl"]
        for s in st.get("sessions", []) or []:
            ids = {t.get(k) for t in s.get("teams", []) for k in ("p1Id", "p2Id")} - {None}
            for i in ids:
                if i not in people:
                    continue
                r = people[i]
                r["nights"] += 1
                if vol not in r["volumes"]:
                    r["volumes"].append(vol)
                if s.get("date") and (not r["lastPlayed"] or s["date"] > r["lastPlayed"]):
                    r["lastPlayed"] = s["date"]
        for i, url in ph.items():
            if not url.startswith("data:image/"):
                continue
            if i not in photos:
                photos[i] = (url, vol)
            elif hashlib.md5(url.encode()).digest() != hashlib.md5(photos[i][0].encode()).digest() and i not in older:
                older[i] = (url, vol)
        print(f"  {vol:20} {len(st.get('players', [])):4} players  {len(st.get('sessions', []) or []):2} nights  {len(ph):3} photos")
    # UPRISING nights, and the walk-ins who only exist there
    am = json.loads(ssh("curl -s localhost:3007/state")).get("state", {})
    guests = {g["id"]: g["name"] for g in am.get("guests", [])}
    for t in am.get("tournaments", []):
        for i in t.get("playerIds", []):
            if i in guests and i not in people:
                people[i] = {"id": i, "name": guests[i], "volumes": [], "nights": 0, "lastPlayed": None,
                             "photoUrl": None, "guest": True}
            if i in people:
                people[i]["uprising"] = people[i].get("uprising", 0) + 1
    # keep the Heist work already done: a rebuild must never drop an imported photo
    prev = {r["id"]: r for r in json.load(open(DB))["players"]} if os.path.exists(DB) else {}
    for f in os.listdir(os.path.join(OUT, "photos")):
        os.remove(os.path.join(OUT, "photos", f))
    names = {}
    for r in people.values():
        names.setdefault(fold(r["name"]) or r["name"], []).append(r["id"])
    for r in people.values():
        if r["id"] in photos:
            url, vol = photos[r["id"]]
            ext = "png" if url.startswith("data:image/png") else "jpg"
            rel = f"photos/{r['id']}.{ext}"
            open(os.path.join(OUT, rel), "wb").write(base64.b64decode(url.split(",", 1)[1]))
            r["photo"], r["photoFrom"] = rel, vol
        else:
            r["photo"], r["photoFrom"] = None, None
        if r["id"] in older:
            r["photoOlderFrom"] = older[r["id"]][1]
        r["sameNameAs"] = [x for x in names[fold(r["name"]) or r["name"]] if x != r["id"]] or None
        h = (prev.get(r["id"]) or {}).get("heist") or {"photo": None, "status": "needed"}
        r["heist"] = h
        r.setdefault("uprising", 0)
        r.setdefault("guest", False)
    for r in people.values():                        # uprising is only final once every night is counted
        r["current"] = bool(r["uprising"]) or (r["lastPlayed"] or "") >= CURRENT_FROM
    rows = sorted(people.values(), key=lambda r: (not r["current"], -(r["nights"] + r["uprising"]), r["name"].lower()))
    write(rows)
    have = sum(1 for r in rows if r["photo"])
    played = [r for r in rows if r["nights"] + r["uprising"]]
    print(f"\n{len(rows)} people · {len(played)} have played · {have} with a photo "
          f"({sum(1 for r in played if r['photo'])} of those who play) · {sum(1 for r in rows if r['guest'])} Americano-only walk-ins")
    sheet()


def write(rows):
    json.dump({"built": date.today().isoformat(), "heistFormat": HEIST,
               "_note": "One record per player id. photo = the current one the apps hold; heist.photo = the new "
                        "Heist-format one (4:5, 1080x1350, face in the top third). Rebuild with "
                        "ops/heist-roster.py build — it keeps every imported Heist photo.",
               "players": rows}, open(DB, "w"), indent=1, ensure_ascii=False)
    with open(os.path.join(OUT, "players.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["id", "name", "playing_now", "nights", "uprising", "last_played", "volumes", "has_photo", "photo",
                    "heist_status", "heist_photo", "same_name_as", "walk_in"])
        for r in rows:
            w.writerow([r["id"], r["name"], "yes" if r.get("current") else "", r["nights"], r["uprising"], r["lastPlayed"] or "",
                        " | ".join(r["volumes"]), "yes" if r["photo"] else "no", r["photo"] or "",
                        r["heist"]["status"], r["heist"]["photo"] or "", " ".join(r["sameNameAs"] or []),
                        "yes" if r["guest"] else ""])


def import_dir(src):
    """Files named after the player: 'Munther Rahbi.jpg', or the id. Each is cut
    to 4:5 from the centre-top and saved at 1080x1350."""
    from PIL import Image, ImageOps
    d = json.load(open(DB)); rows = d["players"]
    byname = {}
    for r in rows:
        if fold(r["name"]):
            byname.setdefault(fold(r["name"]), []).append(r)
    os.makedirs(os.path.join(OUT, "heist"), exist_ok=True)
    done, problems = 0, []
    for f in sorted(os.listdir(src)):
        stem, ext = os.path.splitext(f)
        if ext.lower() not in (".jpg", ".jpeg", ".png", ".webp", ".heic"):
            continue
        hit = [r for r in rows if r["id"] == stem] or byname.get(fold(stem), [])
        if len(hit) != 1:
            problems.append(f"{f}: {'no player called that' if not hit else 'matches ' + str(len(hit)) + ' players — rename it to the id: ' + ', '.join(r['id'] for r in hit)}")
            continue
        r = hit[0]
        im = ImageOps.exif_transpose(Image.open(os.path.join(src, f))).convert("RGB")
        W, H = HEIST["w"], HEIST["h"]
        if im.width / im.height > W / H:                 # too wide: keep the middle
            nw = round(im.height * W / H); im = im.crop(((im.width - nw) // 2, 0, (im.width - nw) // 2 + nw, im.height))
        else:                                            # too tall: keep the top, where the face is
            nh = round(im.width * H / W); im = im.crop((0, 0, im.width, nh))
        if im.width < W * .6:
            problems.append(f"{f}: only {im.width}px wide after the crop — it will look soft on the card (want {W})")
        im = im.resize((W, H), Image.LANCZOS)
        rel = f"heist/{r['id']}.jpg"
        im.save(os.path.join(OUT, rel), "JPEG", quality=HEIST["quality"], optimize=True)
        r["heist"] = {"photo": rel, "status": "done", "from": f}
        done += 1
    write(rows)
    print(f"imported {done}")
    for p in problems:
        print("  !", p)
    sheet()


def sheet():
    d = json.load(open(DB)); rows = d["players"]
    played = [r for r in rows if r["nights"] + r["uprising"]]
    now = [r for r in played if r.get("current")]
    before = [r for r in played if not r.get("current")]
    esc = lambda s: (s or "").replace("&", "&amp;").replace("<", "&lt;")
    def tile(r):
        img = r["heist"]["photo"] or r["photo"]
        pic = f'<img src="{img}" alt="" loading="lazy">' if img else f'<span class="ini">{esc("".join(w[0] for w in r["name"].split()[:2]).upper())}</span>'
        tag = ("HEIST ✓", "done") if r["heist"]["status"] == "done" else ("HAS PHOTO", "have") if r["photo"] else ("NEEDS PHOTO", "need")
        dup = ' <i title="another player has this name">· same name</i>' if r["sameNameAs"] else ""
        walk = ' <i>· walk-in</i>' if r["guest"] else ""
        return (f'<figure class="{tag[1]}">{pic}<figcaption><b>{esc(r["name"])}</b>'
                f'<span>{r["nights"]} nights · {r["uprising"]} uprising{dup}{walk}</span>'
                f'<em>{tag[0]}</em><code>{r["id"]}</code></figcaption></figure>')
    n_have = sum(1 for r in played if r["photo"] or r["heist"]["photo"])
    n_now = sum(1 for r in now if r["photo"] or r["heist"]["photo"])
    html = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Heist roster</title>
<style>
:root{{--bg:#0F1B2B;--card:#13202F;--sand:#FFF4E8;--mist:#B9C6D3;--coral:#F26B5B;--teal:#2FB7B0;--gold:#FFD08A;--line:rgba(255,244,232,.12)}}
body{{margin:0;background:var(--bg);color:var(--sand);font:14px/1.4 system-ui,sans-serif;padding:24px 16px}}
h1{{margin:0 0 4px;font-size:26px;letter-spacing:.04em}} p{{color:var(--mist);margin:0 0 16px;max-width:760px}}
.k{{display:flex;gap:16px;flex-wrap:wrap;margin:0 0 20px;color:var(--mist)}} .k b{{color:var(--sand);font-size:20px}}
h2{{font-size:13px;letter-spacing:.14em;text-transform:uppercase;color:var(--mist);margin:28px 0 10px}}
.g{{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:12px}}
figure{{margin:0;background:var(--card);border:1px solid var(--line);border-radius:12px;overflow:hidden}}
figure img,.ini{{display:block;width:100%;aspect-ratio:4/5;object-fit:cover;object-position:center 20%}}
.ini{{display:grid;place-items:center;font-size:34px;font-weight:800;color:var(--mist);background:#1B2A3C}}
figcaption{{padding:8px 10px 10px;display:grid;gap:2px}} figcaption span{{color:var(--mist);font-size:12px}}
figcaption em{{font-style:normal;font-size:11px;letter-spacing:.12em;font-weight:700}}
figcaption code{{font-size:10px;color:#6F8193;overflow:hidden;text-overflow:ellipsis}}
.need em{{color:var(--coral)}} .have em{{color:var(--gold)}} .done em{{color:var(--teal)}} i{{font-style:normal;color:var(--gold)}}
</style></head><body>
<h1>MUSCAT HEIST · ROSTER</h1>
<p>Everyone who has played, most nights first, with the photo the apps hold today. The Heist format is a
<b>4:5 portrait, 1080×1350</b>, one person, face in the top third — it is cut down to the crew card, the round
avatars and the stories. Name each new file after the player (or their id) and run
<code>python3.13 ops/heist-roster.py import &lt;folder&gt;</code>.</p>
<div class="k"><span><b>{len(now)}</b> playing now</span><span><b>{n_now}</b> of them with a photo</span>
<span><b>{len(now) - n_now}</b> need one</span><span><b>{len(played)}</b> have ever played</span><span><b>{sum(1 for r in rows if r['heist']['status'] == 'done')}</b> in the Heist format</span>
<span><b>{len(rows)}</b> on the roster in all</span></div>
<h2>Playing now — on a team since 1 Oct, or at an UPRISING night ({len(now)})</h2>
<p>The faces the Heist cards will carry first. Most nights first.</p>
<div class="g">{''.join(tile(r) for r in now)}</div>
<h2>Played before October ({len(before)})</h2><div class="g">{''.join(tile(r) for r in before)}</div>
<h2>On the roster, never played ({len(rows) - len(played)})</h2>
<p>Signed up at some point and never on a team. Not worth chasing a photo for until they turn up.</p>
<div class="g">{''.join(tile(r) for r in rows if not (r["nights"] + r["uprising"]))}</div>
</body></html>"""
    open(os.path.join(OUT, "roster.html"), "w").write(html)
    print(f"wrote {os.path.relpath(os.path.join(OUT, 'roster.html'), ROOT)}")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "build"
    {"build": build, "sheet": sheet}.get(cmd, lambda: import_dir(sys.argv[2]))()
