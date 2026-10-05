# -*- coding: utf-8 -*-
"""The Blackout design language on one sheet — made to be handed to an editor.

Not a brand manual. A reference picture: the palette with its hexes, the type
rules, the geometry rules, a real before/after of the photo grade, and at the
bottom the whole thing written out as a prompt you can paste into an image
editor. The point is that someone editing a photo for this volume — a person or
a model — can be given ONE image and get it right.

Everything derives: the colours come from blackout-season.json, the before/after
is produced by ops/blackout_grade.py on an actual photo from a night, and the
numbers printed beside the recipe are that module's own parameters. So the
prompt at the bottom cannot drift away from the code at the top.

  python3 build-blackout-styleguide.py <photo.jpg>
  node render-blackout-styleguide.mjs
"""
import base64, io, json, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image
from ops.blackout_grade import P, grade

HERE = os.path.dirname(os.path.abspath(__file__))
SP = "/tmp/claude-0/-home-user-May-madness/0e44f0ad-a683-5f0d-9de6-9459ae328963/scratchpad"
FONTS = os.path.join(SP, "video", "fonts")
BRAND = os.path.join(HERE, "brand", "blackout")

W, H = 1500, 1740


def b64(p):
    with open(p, "rb") as f:
        return base64.b64encode(f.read()).decode()


def img_b64(im, q=88):
    buf = io.BytesIO()
    im.convert("RGB").save(buf, "JPEG", quality=q)
    return base64.b64encode(buf.getvalue()).decode()


def faces():
    css = open(os.path.join(FONTS, "fonts.css")).read()
    seen = {}

    def sub(m):
        n = m.group(1)
        if n not in seen:
            seen[n] = b64(os.path.join(FONTS, n))
        return "url(data:font/woff2;base64,%s) format('woff2')" % seen[n]

    css = re.sub(r"url\(([0-9a-f]+\.woff2)\)\s*format\('woff2'\)", sub, css)
    assert ".woff2)" not in css, "a font file was left as an external reference"
    return css


# The prompt. This is the deliverable half of the sheet, so it is written to be
# pasted, not read: one paragraph, concrete colours, and the two things models
# get wrong about this look stated as negatives at the end.
def prompt_text():
    return (
        "Grade this photo in the BLACKOUT SERIES look. Night padel court. "
        f"Desaturate about {int(P['desat'] * 100)}%, then crush it: deep contrast, "
        "black point at #050505, no detail recovery in the shadows. "
        "Cool the whole frame — kill the warm orange cast of the court surface. "
        "Push the highlights toward neon lime-yellow #C6FF00 and sink the shadows "
        "toward deep violet #2E0B73, so the floodlights read lime and the dark "
        "reads UV. A thin magenta #FF2E88 rim on the players' edges only — nowhere "
        "else. Fine monochrome 35mm grain, soft vignette. "
        "Keep every face sharp and recognisable and skin still reading as skin. "
        "The photo should sit BACK, dark and quiet, like a stage with the lights "
        "off — it is a background for neon graphics, not the subject. "
        "No warm or amber tones, no teal-and-orange, no glow or bloom, no added "
        "text, no rounded corners."
    )


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else os.path.join(SP, "plain-a.jpg")
    cfg = json.load(open(os.path.join(HERE, "blackout-season.json")))
    C = cfg["palette"]
    BG, LIME, MAG, UV = C["bg"], C["lime"], C["magenta"], C["uv"]
    INK, MUTED = C["ink"], C["muted"]

    # The before/after. Same crop, same size, so the only difference on the
    # sheet is the grade — a comparison where the two frames are not identical
    # is not a comparison.
    raw = Image.open(src).convert("RGB")
    box = 620
    w, h = raw.size
    s = box / min(w, h)
    raw = raw.resize((round(w * s), round(h * s)), Image.LANCZOS)
    w, h = raw.size
    raw = raw.crop(((w - box) // 2, 0, (w - box) // 2 + box, min(h, round(box * 1.25))))
    after = grade(raw)

    swatches = [
        ("LIME", LIME, "Primary. Live, now, the thing you should look at."),
        ("MAGENTA", MAG, "Rare. Double points, the aperture, one rim light."),
        ("UV", UV, "Structure. The room the volume is named after."),
        ("BLACK", BG, "The ground. Not grey, not #000 — #050505."),
        ("INK", INK, "Type."),
        ("MUTED", MUTED, "Done, archived, over."),
    ]
    chips = "".join(
        f'<div class="sw"><div class="chip" style="background:{v}"></div>'
        f'<div class="nm">{n}</div><div class="hx">{v.upper()}</div>'
        f'<div class="use">{u}</div></div>'
        for n, v, u in swatches)

    # The recipe, with this module's own numbers beside each step.
    steps = [
        ("LEVEL", f"stretch the frame's own {P['lo_pct']:.0f}–{P['hi_pct']:.0f} percentile to full range",
         "a floodlit court has no highlights to grade until you make some"),
        ("DESATURATE", f"{int(P['desat'] * 100)}%",
         "the court's orange fights every colour in the palette"),
        ("CRUSH", f"gamma {P['gamma']}, contrast {P['contrast']} pivoted at {P['pivot']}",
         "pivot low — the frame is mostly night"),
        ("LIME IN", f"{int(P['lime_hi'] * 100)}% above {P['lime_from']}",
         "the floodlights become the volume's colour"),
        ("UV UNDER", f"{int(P['uv_lo'] * 100)}% below {P['uv_from']}",
         "the dark stops being neutral and becomes a room"),
        ("MAGENTA RIM", f"{int(P['magenta_rim'] * 100)}% on edges only",
         "the rare colour never washes, it outlines"),
        ("PUSH BACK", f"×{P['dark']}, vignette {int(P['vignette'] * 100)}%",
         "the photo is a ground; the neon on top is the subject"),
        ("GRAIN", f"{P['grain']:.3f} monochrome",
         "stops a crushed night frame banding"),
    ]
    recipe = "".join(
        f'<div class="st"><div class="stn">{i + 1}</div>'
        f'<div><div class="sth">{a}</div><div class="stv">{b}</div>'
        f'<div class="stw">{c}</div></div></div>'
        for i, (a, b, c) in enumerate(steps))

    rules = [
        ("RADIUS 0", "Everywhere. Circles are deliberate; rounded rectangles are a mistake."),
        ("TYPE", "Archivo italic, wdth 125, wght 900 for display. JetBrains Mono, "
                 "letterspaced, uppercase, for every label."),
        ("BORDERS", "2–3px, hard, full opacity. No soft shadows, ever."),
        ("NEON IS EARNED", "Lime means live. Magenta means double points. If it means "
                           "nothing, it is muted grey."),
        ("THE PHOTO LOSES", "Where a photo meets the brand, the photo goes darker. "
                            "Never the other way."),
    ]
    rulehtml = "".join(
        f'<div class="rl"><div class="rlh">{a}</div><div class="rlb">{b}</div></div>'
        for a, b in rules)

    mark = b64(os.path.join(BRAND, "blackout-mark.png"))

    html = f"""<!doctype html><html><head><meta charset="utf-8"><style>
{faces()}
*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{width:{W}px;height:{H}px;background:{BG};color:{INK};
  font-family:'Archivo',sans-serif;-webkit-font-smoothing:antialiased;overflow:hidden}}
.wash{{position:absolute;inset:0;pointer-events:none;
  background:radial-gradient(circle at 90% 4%, rgba(123,43,255,.20), transparent 42%),
             radial-gradient(circle at 4% 62%, rgba(198,255,0,.07), transparent 38%)}}
.pad{{position:relative;padding:56px 62px}}
.d{{font-style:italic;font-variation-settings:'wdth' 125,'wght' 900;line-height:.9}}
.k{{font-family:'JetBrains Mono',monospace;font-weight:700;letter-spacing:.26em}}
.top{{display:flex;align-items:center;gap:26px;border-bottom:3px solid {LIME};padding-bottom:30px}}
.top img{{width:84px;display:block}}
h2{{margin:44px 0 20px;display:flex;align-items:center;gap:18px}}
h2 span.t{{font-family:'JetBrains Mono',monospace;font-weight:700;letter-spacing:.26em;
  font-size:16px;color:{LIME};white-space:nowrap}}
h2 span.r{{flex:1;height:2px;background:rgba(242,242,242,.12)}}
.grid{{display:grid;grid-template-columns:repeat(6,1fr);gap:16px}}
.sw .chip{{height:92px;border:2px solid rgba(242,242,242,.14)}}
.nm{{font-family:'JetBrains Mono',monospace;font-weight:700;font-size:14px;
  letter-spacing:.16em;margin-top:13px}}
.hx{{font-family:'JetBrains Mono',monospace;font-size:13px;color:{MUTED};margin-top:4px}}
.use{{font-size:14px;color:{C['ink2']};margin-top:9px;line-height:1.35}}
.ba{{display:flex;gap:22px;align-items:flex-start}}
.ba figure{{flex:0 0 auto}}
.ba img{{display:block;border:2px solid rgba(242,242,242,.14)}}
.cap{{font-family:'JetBrains Mono',monospace;font-weight:700;font-size:13px;
  letter-spacing:.2em;margin-top:12px}}
.recipe{{flex:1;display:grid;grid-template-columns:1fr 1fr;gap:14px 26px}}
.st{{display:flex;gap:14px;align-items:flex-start}}
.stn{{width:30px;height:30px;flex:0 0 30px;border:2px solid {LIME};color:{LIME};
  font-family:'JetBrains Mono',monospace;font-weight:700;font-size:14px;
  display:flex;align-items:center;justify-content:center}}
.sth{{font-family:'JetBrains Mono',monospace;font-weight:700;font-size:14px;
  letter-spacing:.17em}}
.stv{{font-size:15px;color:{C['limePale']};margin-top:4px}}
.stw{{font-size:14px;color:{MUTED};margin-top:3px;line-height:1.35}}
.rules{{display:grid;grid-template-columns:repeat(5,1fr);gap:18px}}
.rl{{border-left:3px solid {MAG};padding-left:16px}}
.rlh{{font-family:'JetBrains Mono',monospace;font-weight:700;font-size:14px;
  letter-spacing:.17em;color:{MAG}}}
.rlb{{font-size:15px;color:{C['ink2']};margin-top:9px;line-height:1.4}}
.prompt{{border:3px solid {LIME};background:rgba(198,255,0,.05);padding:30px 34px}}
.prompt p{{font-family:'JetBrains Mono',monospace;font-size:19px;line-height:1.62;
  color:{C['limePale']}}}
.foot{{display:flex;justify-content:space-between;align-items:flex-end;margin-top:36px;
  border-top:2px solid rgba(242,242,242,.12);padding-top:22px}}
</style></head><body><div class="wash"></div><div class="pad">

<div class="top">
  <img src="data:image/png;base64,{mark}">
  <div>
    <div class="k" style="font-size:15px;color:{UV}">URBAN SOCIAL SERIES &middot; {cfg['volume']} &middot; {cfg['monthUpper']} 2026</div>
    <div class="d" style="font-size:62px;margin-top:11px">THE DESIGN LANGUAGE</div>
  </div>
  <div style="margin-left:auto;text-align:right">
    <div class="d" style="font-size:30px;color:{LIME}">{cfg['taglineHtml']}</div>
    <div class="k" style="font-size:12px;color:{MUTED};margin-top:9px">PHOTO EDITING REFERENCE</div>
  </div>
</div>

<h2><span class="t">01 &middot; THE PALETTE</span><span class="r"></span></h2>
<div class="grid">{chips}</div>

<h2><span class="t">02 &middot; THE PHOTO GRADE</span><span class="r"></span></h2>
<div class="ba">
  <figure><img src="data:image/jpeg;base64,{img_b64(raw)}" width="{raw.width // 2}">
    <div class="cap" style="color:{MUTED}">AS SHOT</div></figure>
  <figure><img src="data:image/jpeg;base64,{img_b64(after)}" width="{after.width // 2}">
    <div class="cap" style="color:{LIME}">BLACKOUT</div></figure>
  <div class="recipe">{recipe}</div>
</div>

<h2><span class="t">03 &middot; THE RULES</span><span class="r"></span></h2>
<div class="rules">{rulehtml}</div>

<h2><span class="t">04 &middot; THE PROMPT &mdash; PASTE THIS</span><span class="r"></span></h2>
<div class="prompt"><p>{prompt_text()}</p></div>

<div class="foot">
  <div class="k" style="font-size:13px;color:{MUTED}">
    {cfg['host'].upper()} &middot; COLOURS FROM blackout-season.json &middot; GRADE FROM ops/blackout_grade.py</div>
  <div class="d" style="font-size:26px;color:{LIME}">LIGHTS OUT.</div>
</div>
</div></body></html>"""

    out = os.path.join(BRAND, "blackout-styleguide.html")
    with open(out, "w") as f:
        f.write(html)
    with open(os.path.join(BRAND, "blackout-photo-prompt.txt"), "w") as f:
        f.write(prompt_text() + "\n")
    print(f"built blackout-styleguide.html  {W}x{H}   source photo: {os.path.basename(src)}")
    print("also wrote blackout-photo-prompt.txt")
    print("now render:  node render-blackout-styleguide.mjs")


if __name__ == "__main__":
    main()
