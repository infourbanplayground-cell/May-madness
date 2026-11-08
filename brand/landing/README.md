# The homepage hero backdrop

`hero-court.{webp,jpg}` — the empty floodlit court behind the club mark on
urbanpadel.om. The hero was the mark alone on a black field: correct, and
saying nothing about what the club is.

**It is generated, not photographed, and that is recorded here on purpose.**
Made with Figma's image generation (`gpt-image-2.5-flare`) from a brief for an
empty floodlit padel court at night, no people, no text, no signage. The
unmodified output is kept beside it as `hero-court-source.png` so the next
person can see what was generated and what was done to it.

It is NOT a photograph of Urban Playground's own courts. If a real one is ever
shot, it should replace this: a club's front door is better off showing the
club. Dropping a real image in means re-running the grade below and keeping the
same two filenames.

## The grade, and why each part of it

- **Resized to 1640 wide**, which is 2x the page's 820px column.
- **Brightness 0.62, saturation 0.45.** At full strength it was a photograph
  with a logo on it and the two competed; the mark has to stay the subject.
- **Near-monochrome on purpose.** `--live` rotates with the volume — lime for
  Blackout, red for the National Series — and a backdrop with a colour cast of
  its own would fight whichever accent is running.
- **Faded on all four edges to `#0A0C12`**, the page base, rather than to black
  or to alpha. An image that ends in exactly the colour of the page it sits on
  has no visible edge and needs no transparency, so it stays a JPEG/WebP.
- Served WebP-first (26KB) with a JPEG fallback (95KB) through `image-set()`.

## Checked

The sub-line under the mark now sits over the court rather than over black.
Measured on the rendered page: **6.5:1 on a 390px phone, 5.9:1 on a 1280px
desktop** against `--steel`, both clear of AA.

The backdrop's height is pinned to the hero's own box (`top`/`bottom`), not to
the image's aspect ratio. Driven by `aspect-ratio` it came out 663px tall on
desktop and ran down over the sub-line, NOW PLAYING and the volume card.
