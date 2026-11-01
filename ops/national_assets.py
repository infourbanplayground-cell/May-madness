# -*- coding: utf-8 -*-
"""The handoff's own artwork, inlined, for the Vol.9 skin.

THE SKIN WAS DRAWING ITS OWN APPROXIMATIONS. The first re-skin wrote the
khanjar tile as four CSS gradients and the masar band as two
repeating-linear-gradients — a texture that looks vaguely like the brief from
across the room and is not the brief. The handoff ships the real artwork and
says in as many words that it is the design; nothing here invents a motif.

Two things make this a module rather than a line of CSS:

  · EVERY SVG IS 8KB OF C2PA METADATA AROUND ~400 BYTES OF DRAWING. Inlined
    whole, the masar band alone would be 8KB of signature repeated as a
    background tile, and the eight landmark files would add 64KB to a page
    that is already 700. The manifest is provenance for the file on disk, not
    something a background-image needs, so it is stripped.
  · The landmarks have to be RECOLOURABLE. The handoff uses each silhouette
    white on a red medallion and red on ivory, and ships two files for it —
    but only for some of them (there is no mon-alam-red, no mon-burner-red).
    Rather than carry a half-set, the fill is rewritten on the way through,
    so any landmark can be had in any ink.

The khanjar tile stays a PNG: it is a 288x288 photograph-like texture and
tracing it would be inventing artwork, which is the thing this module exists
to stop.

  from national_assets import assets
  assets()["masar-white"]   -> a data: URL, ready for background-image
"""
import base64
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "..", "brand", "national", "handoff", "assets")

# The handoff's filenames, under the names the skin and the app use.
SVGS = {
    "masar-white": "masar-band-white.svg",
    "masar-red":   "masar-band-red.svg",
    "mon-nizwa":   "mon-nizwa-white.svg",
    "mon-burner":  "mon-burner-white.svg",
    "mon-alam":    "mon-alam-white.svg",
    "mon-tower":   "mon-tower-white.svg",
}
PNGS = {"khanjar": "khanjar-tile-red.png"}

# What a landmark is drawn in, by role. The handoff's medallion is a red disc
# with a white silhouette; on ivory the same shape is drawn in deep red.
INKS = {"white": "#FFFFFF", "red": "#9E1520", "ivory": "#F7F1E6",
        "flag": "#D7202E", "ink": "#1A0A0C"}


def _strip(svg):
    """Drop the C2PA manifest. It is ~95% of every one of these files."""
    out = re.sub(r"<metadata>.*?</metadata>", "", svg, flags=re.S)
    out = re.sub(r'\s+xmlns:c2pa="[^"]*"', "", out)
    return out.strip()


def _recolour(svg, ink):
    """Repaint every fill and stroke that is not `none` in one ink.

    The silhouettes are single-colour drawings — a fort, a burner, a palace, a
    tower — so one ink is the whole picture. Anything already `none` is a
    deliberate hole and stays one.
    """
    def rep(m):
        attr, val = m.group(1), m.group(2)
        return f'{attr}="{val}"' if val.strip().lower() == "none" else f'{attr}="{ink}"'
    return re.sub(r'(fill|stroke)="([^"]*)"', rep, svg)


def _data_url(svg):
    """A data: URL for CSS.

    Percent-encoded rather than base64: an SVG is text, base64 inflates it by a
    third, and these go into a stylesheet that is already the biggest thing the
    skin adds. The characters escaped are the ones that would end the url()
    or be read as CSS.
    """
    s = re.sub(r"\s+", " ", svg)
    for a, b in [("%", "%25"), ("#", "%23"), ('"', "'"), ("<", "%3C"),
                 (">", "%3E"), ("{", "%7B"), ("}", "%7D")]:
        s = s.replace(a, b)
    return "data:image/svg+xml;charset=utf-8," + s


def raw_svg(name, ink=None):
    """The stripped (and optionally recoloured) SVG source itself."""
    path = os.path.join(SRC, SVGS[name])
    svg = _strip(open(path, encoding="utf-8").read())
    if ink:
        svg = _recolour(svg, INKS.get(ink, ink))
    return svg


def assets():
    """{name: data-url}. Landmarks appear once per ink as `<name>@<ink>`."""
    out = {}
    for name in SVGS:
        out[name] = _data_url(raw_svg(name))
        if name.startswith("mon-"):
            for ink in ("white", "red", "ivory", "flag", "ink"):
                out[f"{name}@{ink}"] = _data_url(raw_svg(name, ink))
    for name, f in PNGS.items():
        with open(os.path.join(SRC, f), "rb") as fh:
            out[name] = "data:image/png;base64," + base64.b64encode(fh.read()).decode()
    return out


if __name__ == "__main__":
    a = assets()
    for k in sorted(a):
        print(f"{k:22} {len(a[k]):>8,} chars")
    print(f"\n{len(a)} assets, {sum(len(v) for v in a.values()):,} chars in all")
