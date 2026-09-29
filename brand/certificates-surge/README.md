# September Surge · Vol.7 — Certificates of Achievement, 1st to 5th

A4 landscape (297 x 210mm), 300 DPI, full bleed. Five placements.

| File | What it is |
|---|---|
| `ss-certificates-1-to-5.pdf` | all five as one job — give this to the print shop |
| `ss-certificate-N.pdf` | one placement per file |
| `ss-certificate-N.png` | 3508 x 2480 preview / for sending as an image |
| `ss-certificate-N.html` | the artboard, self-contained (fonts and marks inlined) |

## Rebuilding

```bash
python3 build-surge-certificates.py          # blank name lines
node render-surge-certificates.mjs           # -> 300 DPI PNG
python3 pack-surge-certificate-pdfs.py       # -> print-ready PDF pages
```

With the winners' names typed in, in placement order:

```bash
python3 build-surge-certificates.py \
  --names "1st name" "2nd name" "3rd name" "4th name" "5th name"
node render-surge-certificates.mjs && python3 pack-surge-certificate-pdfs.py
```

The font bundle at `/tmp/certs/fonts/bundle.css` is rebuilt from
`brand/september-surge/video/fonts` — see that README. It is inlined into each
artboard, so the HTML renders identically with no network and no font
substitution at the print shop.

## Design notes

This is the Vol.6 certificate re-cut for Vol.7 rather than a new design, the
same way the app inherits its markup volume to volume. What changes is what
`DESIGN.md` says changes between the two:

- **Palette** — Court Black to Deep Current, Attack Red to Surge Cyan. Cyan
  leads. Strike Amber is urgency-only, so it appears nowhere on a certificate.
- **Display face** — Vol.6 stood Anton up tall; Vol.7 is Archivo italic at
  `wdth 125 / wght 900`, which is what the app and the reels use.
- **Texture** — the Vol.6 tactical grid and scanlines give way to Vol.7's
  horizontal surge trace, at 0.9mm pitch so it reads as a woven field in print
  rather than as stripes.
- **Motif** — the attack burst behind the placement becomes concentric ripple
  rings. Vol.6's boot was a glitch, a signal cut; Vol.7's is a pulse and ripple,
  a signal sent.
- **Frame** — Vol.6's four corner ticks become Vol.7's single rising bar.

**The placement ladder is cyan / light steel / steel, not gold / silver /
bronze.** `DESIGN.md` is explicit that gold is out of this palette, and the
app's medal chips already use this ladder. 3rd, 4th and 5th all sit on the same
steel: stepping 4th and 5th down to Deep Steel was tried and printed washed out,
which is the wrong thing for something somebody keeps. Placement is carried by
the numeral and the label, not by fading.

## Writable plates

The sheet is near-black, so a black pen on it is invisible. Every field that
gets filled in by hand — name, date, signature, certificate number — therefore
sits on its own light plate (`#EEF2F4`, not pure white, so it does not glare
against the dark field). Each plate carries a cap bar in the placement colour
along its top edge: corner ticks were tried first and read as glitches against
a light field, whereas a cap makes the plate look like a labelled field that
belongs to the frame.

The name is the only writable plate left. The date is known — the series closes
on session 8 — so it is printed rather than ruled, and the Tournament Director
box is gone. Those two plates used to flank the seal and crowded it, with the
director plate running nearly to the frame; the foot is now a single centred
stack: seal, award date, imprint. `--date` overrides the printed date.

The plate is 16mm tall — enough to write a name in, not so much that it takes
the eye off the placement. A 22mm plate was tried first and read as a blank
slab.

**Both modes use the same plates.** A typed name (`--names`) prints in ink
`#0A0F14` on the plate rather than on the dark ground, so a pre-printed
certificate and a handwritten one are structurally identical.

**Why the PDF page is a raster.** The design leans on large soft glows — the
placement numeral carries a 4mm and an 18mm shadow. Chromium's vector PDF export
tiles big blurred shadows and the seams between tiles print as hard-edged
rectangles, while a screenshot of the identical page is smooth. Same finding as
the Vol.6 deck; see `pack-certificate-pdfs.py`.
