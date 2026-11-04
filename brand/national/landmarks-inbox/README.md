# Landmark artwork supplied by the owner, 4 Nov 2026

Five files. **Three are in use; two cannot ship**, and the reason matters more
than the file:

| file | what it is | state |
|---|---|---|
| `owner-9.png`  | **Al Mirani** | in use — `mon-mirani` |
| `owner-11.png` | a generic watchtower, **not a named landmark** (owner's call) | in use — `mon-burj`, as a motif only, never captioned |
| `owner-12.png` | **Burj Al Sahwa** | in use — `mon-sahwa` |
| `owner-8.png`  | **Royal Opera House** | **parked** — tiled "Megapixl" stock watermark across the facade |
| `owner-10.png` | **Nizwa Fort** | **parked** — it is the fort's own logo, roundel plus wordmark, not a silhouette |

The two parked ones are the same standing rule the earlier VectorStock comps
fell under: a watermarked preview and a third-party brand mark are reference
for WHICH landmark, never the artwork. Worth recording that `owner-10.png` is
the first picture in this repo that actually shows Nizwa's round drum tower,
which is the shape the slot has been parked for.

**Every name here came from the owner, not from reading the picture.** The
first reading of `owner-8.png` in this session was "Al Alam Palace", which
would have been the third building in this volume to carry another building's
name. Ask; do not guess.

`ops/national-landmarks.py` converts them. `owner-9.png` is the only one that
needs a `CROPS` entry: it was supplied sitting on its headland, and the rock is
darker than the fort, so the converter turned the whole scene into a lump.
