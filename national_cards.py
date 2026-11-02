# -*- coding: utf-8 -*-
"""Vol.9's OWN share-card painter, spliced into the app by build-national-app.py.

THE CARDS WERE VOL.8's LAYOUT WEARING VOL.9's COLOURS. Everything up to now
was done by patching the inherited painter one anchor at a time — a lamp here,
a plate border there — and that can move a colour but it cannot move a shape.
The result was a black-card composition (a photo window with two dark plates
stacked under it) rendered in red, which is the same "recolour, not a volume"
fault the app itself had to be taught twice.

This is the design the owner drew, built as its own thing:

  · the masar band top and foot, inset, the volume's frame
  · the header row: the series and the night in mono, the Arabic opposite
  · the headline, left, two lines of Archivo italic black
  · THE ARCH — an Omani door drawn as a double ivory outline, holding the
    players, with the volume's 56 as a ghost behind them
  · the LANDMARK MEDALLION straddling the arch's apex, named at the foot
  · the result on an IVORY plate with its own masar trim, the score as the
    hero and the winner's name in ink
  · the club mark and the volume line at the foot

Written in 1080x1920 card coordinates throughout, so `drawLineupAt` can scale
the whole thing for a preview by scaling the context.

`national_cards.painter()` returns the JS. The builder splices it in and
points drawLineup / drawLineupAt / drawCutCardAt at `ncPaint`.
"""


def painter(P):
    """The painter, with this volume's palette baked in from the season file."""
    return """
// ── Vol.9 share cards ─────────────────────────────────────────────────────
// Geometry, once. Every figure below is a card coordinate at 1080x1920.
const NC = {
  PAD: 56,            // the band's side inset, and the card's margin
  BAND: 44,           // masar band height; the art is 100:56 so it tiles at 79
  ARCH_L: 116, ARCH_R: 964, ARCH_TOP: 556, ARCH_BOT: 1370,
  PLATE_T: 1408, PLATE_B: 1676,
  MED_R: 68,
  BG: "%(bg)s", DEEP: "%(deep)s", FLAG: "%(flag)s",
  IVORY: "%(ivory)s", INK: "%(ink)s", ROSE: "%(rose)s", GREEN: "%(green)s",
  MUTED: "#8C7B74",
};

// The masar band, inset and pilled — the handoff's own proportions.
function ncBand(g, y) {
  const b = LU_BAND_IMG;
  const x0 = NC.PAD, w = LU_W - NC.PAD * 2, h = NC.BAND;
  g.save();
  g.beginPath();
  if (g.roundRect) g.roundRect(x0, y, w, h, h / 2); else g.rect(x0, y, w, h);
  g.clip();
  g.fillStyle = NC.DEEP; g.fillRect(x0, y, w, h);
  if (b) {
    // Always the art's own 100:56 ratio. A woven band stretched off its
    // aspect is the one place a pattern looks obviously wrong.
    const tw = Math.round(h * b.width / b.height);
    for (let x = x0; x < x0 + w; x += tw) g.drawImage(b, x, y, tw, h);
  }
  g.restore();
}

// The arch: a dome on straight sides with a small foot radius. One path,
// reused for the outline, the clip and the inner line — three copies of this
// shape would be three chances for them to disagree.
function ncArchPath(g, l, t, r, b, foot) {
  const rad = (r - l) / 2, f = foot == null ? 30 : foot;
  g.beginPath();
  g.moveTo(l, b - f);
  g.lineTo(l, t + rad);
  g.arc(l + rad, t + rad, rad, Math.PI, 0);
  g.lineTo(r, b - f);
  g.arcTo(r, b, r - f, b, f);
  g.lineTo(l + f, b);
  g.arcTo(l, b, l, b - f, f);
  g.closePath();
}

// A landmark silhouette, drawn white into an arbitrary box. The art is a data
// URL in LANDMARK_ART; it is cached because a card may draw it twice and the
// decode is not free.
const NC_ART = {};
function ncArt(key) {
  if (NC_ART[key] !== undefined) return NC_ART[key];
  const src = (typeof LANDMARK_ART !== "undefined") && LANDMARK_ART[key];
  if (!src) { NC_ART[key] = null; return null; }
  const im = new Image();
  im.src = src;
  NC_ART[key] = im;
  return im;
}
// AND IT HAS TO BE DECODED BEFORE THE FIRST PAINT. A canvas draw of an image
// that has not loaded is a silent no-op — the first render came out with an
// empty medallion, a ring with nothing in it, which looks like a deliberate
// blank disc rather than a missing asset. Every draw entry point awaits this.
async function ncPreload(d) {
  const lm = ncLandmark(d);
  const im = lm && ncArt(lm.asset);
  if (!im || (im.complete && im.naturalWidth)) return;
  await new Promise(r => { im.onload = r; im.onerror = r; setTimeout(r, 1500); });
}

// Which landmark this night wears. The night number is on the card already
// (d.foot is "NIGHT 06"), so the card does not need to be told separately —
// and it cannot disagree with the app, which cycles the same list in order.
function ncLandmark(d) {
  if (typeof LANDMARKS === "undefined" || !LANDMARKS.length) return null;
  const m = String(d && d.foot || "").match(/(\\d+)/);
  const n = m ? parseInt(m[1], 10) : 1;
  return landmarkFor(Math.max(0, n - 1));
}

function ncPaint(g, kind, d, im, logo, adj, mode) {
  adj = adj || LU_ADJ0;
  const L = NC.PAD + 28, R = LU_W - NC.PAD - 28, W = R - L;

  // ── the ground ──────────────────────────────────────────────────────────
  g.fillStyle = NC.BG; g.fillRect(0, 0, LU_W, LU_H);
  if (LU_TILE_IMG) {
    g.save(); g.globalAlpha = 0.14;
    const t = 300;
    for (let y = 0; y < LU_H; y += t) for (let x = 0; x < LU_W; x += t)
      g.drawImage(LU_TILE_IMG, x, y, t, t);
    g.restore();
  }

  // ── the arch ────────────────────────────────────────────────────────────
  const A = NC;
  const archCx = (A.ARCH_L + A.ARCH_R) / 2;

  // its own ground, a shade deeper than the card, so the door reads as a
  // recess rather than as an outline drawn on a flat wall
  g.save();
  ncArchPath(g, A.ARCH_L, A.ARCH_TOP, A.ARCH_R, A.ARCH_BOT);
  g.clip();
  g.fillStyle = A.DEEP; g.fillRect(0, 0, LU_W, LU_H);
  if (LU_TILE_IMG) {
    g.save(); g.globalAlpha = 0.16;
    const t = 190;
    for (let y = A.ARCH_TOP; y < A.ARCH_BOT; y += t)
      for (let x = A.ARCH_L; x < A.ARCH_R; x += t)
        g.drawImage(LU_TILE_IMG, x, y, t, t);
    g.restore();
  }

  // the volume's number, a ghost behind whoever is standing there
  {
    const t = "56";
    const sz = stFit(g, t, (A.ARCH_R - A.ARCH_L) * 1.02, 560, 900);
    g.font = `italic 900 ${sz}px Archivo, sans-serif`;
    g.fillStyle = "rgba(26,10,12,.26)";
    g.fillText(t, archCx - g.measureText(t).width / 2, A.ARCH_BOT - 300);
  }

  // ── the players, inside the arch ────────────────────────────────────────
  if (im) {
    if (mode === "cut") {
      // A cut-out STANDS on the arch's floor. Fitted on both axes: fitting on
      // height alone runs a row of four past the sides and slices the outer
      // two, which is the bug the inherited painter already records.
      const FEET = A.ARCH_BOT - 26, HEAD = A.ARCH_TOP + 96;
      const box = luInkBox(im);
      const z = Math.max(1, adj.zoom || 1);
      const maxH = (FEET - HEAD) * z, maxW = (A.ARCH_R - A.ARCH_L - 56) * z;
      const r = Math.min(maxH / box.h, maxW / box.w);
      const dw = im.width * r, dh = im.height * r;
      const x = archCx - (box.x + box.w / 2) * r + (adj.x || 0);
      const y = FEET - (box.y + box.h) * r + (adj.y || 0);
      g.imageSmoothingEnabled = true; g.imageSmoothingQuality = "high";
      g.drawImage(im, x, y, dw, dh);
    } else {
      // A whole photograph fills the arch. NO GRADE ON THE PLAYERS — the
      // owner's call; only the brightness the organiser dialled in.
      const br = adj.bright || 1;
      if (LU_CAN_FILTER && br !== 1) g.filter = `brightness(${br.toFixed(3)})`;
      luCoverAdj(g, im, A.ARCH_L, A.ARCH_TOP,
                 A.ARCH_R - A.ARCH_L, A.ARCH_BOT - A.ARCH_TOP, adj);
      g.filter = "none";
    }
    // the floor: enough to stand the arch's own foot on, not a wash on anyone
    const fg = g.createLinearGradient(0, A.ARCH_BOT - 190, 0, A.ARCH_BOT);
    fg.addColorStop(0, "rgba(158,21,32,0)");
    fg.addColorStop(1, "rgba(158,21,32,.86)");
    g.fillStyle = fg; g.fillRect(A.ARCH_L, A.ARCH_BOT - 190,
                                 A.ARCH_R - A.ARCH_L, 190);
  }

  // ONE SOFT LIGHT, AND IT IS NOT GREEN. Green lamps on `screen` over a
  // photograph do not read as light in the room — they read as a green smear
  // laid on the picture, which is exactly what the owner called a blob. The
  // green belongs where it has an edge: the arch's inner line, the medallion's
  // outer ring, the weave on the plate. What stays here is a single neutral
  // lamp high in the arch, which is what stops a cut-out looking pasted on.
  g.globalCompositeOperation = "screen";
  {
    const cx = archCx, cy = A.ARCH_TOP + 180, rad = 460;
    const r2 = g.createRadialGradient(cx, cy, 0, cx, cy, rad);
    r2.addColorStop(0, "rgba(247,241,230,.20)");
    r2.addColorStop(0.45, "rgba(247,241,230,.06)");
    r2.addColorStop(1, "rgba(247,241,230,0)");
    g.fillStyle = r2;
    g.fillRect(A.ARCH_L, A.ARCH_TOP, A.ARCH_R - A.ARCH_L, A.ARCH_BOT - A.ARCH_TOP);
  }
  g.globalCompositeOperation = "source-over";
  g.restore();

  // the double line: 4px ivory, and a hairline inset 14 inside it. The
  // handoff's "double line" is the volume's one piece of depth — there are
  // no drop shadows anywhere in this design.
  g.strokeStyle = A.IVORY; g.lineWidth = 5;
  ncArchPath(g, A.ARCH_L, A.ARCH_TOP, A.ARCH_R, A.ARCH_BOT);
  g.stroke();
  g.strokeStyle = A.GREEN; g.lineWidth = 3;
  ncArchPath(g, A.ARCH_L + 15, A.ARCH_TOP + 15, A.ARCH_R - 15, A.ARCH_BOT - 15, 20);
  g.stroke();

  // ── the medallion, straddling the apex ──────────────────────────────────
  {
    const lm = ncLandmark(d);
    const cx = archCx, cy = A.ARCH_TOP;
    g.fillStyle = A.BG;
    g.beginPath(); g.arc(cx, cy, A.MED_R, 0, Math.PI * 2); g.fill();
    g.strokeStyle = A.IVORY; g.lineWidth = 5;
    g.beginPath(); g.arc(cx, cy, A.MED_R, 0, Math.PI * 2); g.stroke();
    g.strokeStyle = A.GREEN; g.lineWidth = 4;
    g.beginPath(); g.arc(cx, cy, A.MED_R + 8, 0, Math.PI * 2); g.stroke();
    // LANDMARK_ART is keyed by the plain asset name. The "@ink" suffix is
    // national_assets.py's own key for an inked variant and does not
    // survive into the page — asking for it got undefined, and a canvas
    // draw of nothing is a silent no-op, so the medallion rendered as a
    // ring with an empty disc in it. That looks like a design choice.
    const art = lm && ncArt(lm.asset);
    if (art && art.complete && art.naturalWidth) {
      const s = A.MED_R * 1.16;
      const r = Math.min(s / art.naturalWidth, s / art.naturalHeight);
      g.drawImage(art, cx - art.naturalWidth * r / 2,
                  cy - art.naturalHeight * r / 2 + 3,
                  art.naturalWidth * r, art.naturalHeight * r);
    }
  }

  // ── the frame ───────────────────────────────────────────────────────────
  ncBand(g, 72);
  ncBand(g, LU_H - 72 - NC.BAND);

  // ── the header row ──────────────────────────────────────────────────────
  const head = `${SERIES_NAME} \\u00B7 ${d.foot || ""}`.trim();
  stMono(g, head, L, 206, 25, A.IVORY, 5);
  {
    // The Arabic opposite, right-aligned. Noto Kufi is subsetted to exactly
    // the words the brand uses, so this string comes from the config and is
    // never written here.
    g.font = `700 30px "Noto Kufi Arabic", sans-serif`;
    g.fillStyle = A.IVORY;
    g.fillText(SERIES_NAME_AR, R - g.measureText(SERIES_NAME_AR).width, 212);
  }

  // ── the headline ────────────────────────────────────────────────────────
  const big = kind === "champs" ? ["NIGHT", "CHAMPIONS"]
            : kind === "final"  ? ["THE", "FINAL"]
            : ["SEMI", "FINAL"];
  stDisp(g, big[0], L, 352, 132, A.IVORY, W);
  stDisp(g, big[1], L, 474, 132, A.IVORY, W);

  // ── the result plate ────────────────────────────────────────────────────
  const PT = A.PLATE_T, PB = A.PLATE_B, PL = NC.PAD, PR = LU_W - NC.PAD;
  const PW = PR - PL, PH = PB - PT, PRAD = 42;
  g.save();
  g.beginPath();
  if (g.roundRect) g.roundRect(PL, PT, PW, PH, PRAD); else g.rect(PL, PT, PW, PH);
  g.fillStyle = A.IVORY; g.fill();
  g.clip();
  // its own masar trim, along the top edge and clipped by the plate's corners
  {
    const b = LU_BAND_IMG, h = 16;
    g.fillStyle = A.DEEP; g.fillRect(PL, PT, PW, h);
    if (b) {
      const tw = Math.round(h * b.width / b.height);
      for (let x = PL; x < PR; x += tw) g.drawImage(b, x, PT, tw, h);
    }
  }
  g.restore();

  const midY = PT + 30 + (PH - 30) / 2;
  if (kind === "champs") {
    // WINNERS chip, then the name in ink. The chip is the only red fill on
    // the plate, so it reads as the one thing that matters on it.
    const chip = "WINNERS";
    g.font = '700 22px "JetBrains Mono", monospace';
    const cw = g.measureText(chip).width + 10 * 6 + 44;
    g.fillStyle = A.FLAG;
    g.beginPath();
    if (g.roundRect) g.roundRect(PL + 44, PT + 56, cw, 44, 22);
    else g.rect(PL + 44, PT + 56, cw, 44);
    g.fill();
    stMono(g, chip, PL + 66, PT + 85, 22, A.IVORY, 6);

    // The score is the hero: the winner's figure in the flag's red, the
    // loser's in the plate's muted ink. Centred on the plate, not on the
    // card, so it stays put whatever the names do.
    const hi = String(d.aScore == null ? "" : d.aScore);
    const lo = String(d.bScore == null ? "" : d.bScore);
    if (hi !== "" || lo !== "") {
      g.font = "italic 900 104px Archivo, sans-serif";
      const wHi = g.measureText(hi).width, wLo = g.measureText(lo).width;
      g.font = "italic 900 72px Archivo, sans-serif";
      const wDash = g.measureText("\\u2013").width + 22;
      const total = wHi + wDash + wLo;
      let x = (PL + PR) / 2 - total / 2;
      g.font = "italic 900 104px Archivo, sans-serif";
      g.fillStyle = A.FLAG; g.fillText(hi, x, midY + 34); x += wHi + 11;
      g.font = "italic 900 72px Archivo, sans-serif";
      g.fillStyle = A.MUTED; g.fillText("\\u2013", x, midY + 24); x += wDash - 11;
      g.font = "italic 900 104px Archivo, sans-serif";
      g.fillStyle = A.MUTED; g.fillText(lo, x, midY + 34);
    }

    // FINAL, outlined, opposite the WINNERS chip
    {
      const t = "FINAL";
      g.font = '700 22px "JetBrains Mono", monospace';
      const w = g.measureText(t).width + 5 * (t.length - 1) + 44;
      g.strokeStyle = A.MUTED; g.lineWidth = 2;
      g.beginPath();
      if (g.roundRect) g.roundRect(PR - 44 - w, PT + 56, w, 44, 22);
      else g.rect(PR - 44 - w, PT + 56, w, 44);
      g.stroke();
      stMono(g, t, PR - 44 - w + 22, PT + 85, 22, A.MUTED, 5);
    }

    // the two names, under their chips, each in its own half
    const half = (PW - 88) * 0.40;
    ncName(g, (d.a || "").toUpperCase(), PL + 44, PT + 150, half, A.INK, "left");
    ncName(g, (d.b || "").toUpperCase(), PR - 44, PT + 150, half, A.MUTED, "right");
  } else {
    // A line-up: two teams and the groups they came out of, with VS between.
    const half = (PW - 88) * 0.38;
    ncName(g, (d.a || "TBD").toUpperCase(), PL + 44, PT + 112, half, A.INK, "left");
    ncName(g, (d.b || "TBD").toUpperCase(), PR - 44, PT + 112, half, A.INK, "right");
    g.font = "italic 900 58px Archivo, sans-serif";
    g.fillStyle = A.FLAG;
    const vs = "VS";
    g.fillText(vs, (PL + PR) / 2 - g.measureText(vs).width / 2, midY + 6);
    const chipY = PB - 44;
    if (d.aChip) stMono(g, d.aChip, PL + 44, chipY, 21, A.MUTED, 5);
    if (d.bChip) {
      g.font = '700 21px "JetBrains Mono", monospace';
      const w = g.measureText(d.bChip).width + 5 * (d.bChip.length - 1);
      stMono(g, d.bChip, PR - 44 - w, chipY, 21, A.MUTED, 5);
    }
  }

  // ── the foot ────────────────────────────────────────────────────────────
  // EVERYTHING HERE HAS TO CLEAR THE BOTTOM BAND, which starts at
  // LU_H - 72 - BAND. At 104px from PLATE_B + 48 the club mark ran to 1828
  // and the band begins at 1804, so the mark was drawn straight through the
  // weave — and a decorative strip is invisible to every text check there is.
  const FOOT = A.PLATE_B, BAND_TOP = LU_H - 72 - NC.BAND;
  if (logo) {
    const h = 74, w = logo.width * (h / logo.height);
    const off = document.createElement("canvas");
    off.width = Math.ceil(w); off.height = h;
    const o = off.getContext("2d");
    o.drawImage(logo, 0, 0, w, h);
    o.globalCompositeOperation = "source-in";
    o.fillStyle = A.IVORY; o.fillRect(0, 0, w, h);
    g.drawImage(off, L, FOOT + 26);
  }
  {
    const t = `${VOLUME_LABEL} \\u00B7 ${SEASON_MONTH_SHORT} ${SEASON_YEAR}`;
    g.font = '700 26px "JetBrains Mono", monospace';
    const w = g.measureText(t).width + 7 * (t.length - 1);
    stMono(g, t, R - w, FOOT + 62, 26, A.IVORY, 7);
    const lm = ncLandmark(d);
    if (lm && lm.nameAr) {
      g.font = `700 26px "Noto Kufi Arabic", sans-serif`;
      g.fillStyle = A.ROSE;
      g.fillText(lm.nameAr, R - g.measureText(lm.nameAr).width, FOOT + 106);
    }
  }
}

// A team name on the ivory plate. Doubles pairs are long — "ALMUNTASER &
// MUATASIM" — so it breaks on the ampersand before it shrinks, which keeps
// the type big and reads as two people rather than as one long string.
function ncName(g, name, x, y, max, colour, align) {
  const parts = name.split(/\\s*&\\s*/);
  const lines = parts.length === 2 ? [parts[0], "& " + parts[1]] : [name];
  let size = 46;
  for (;;) {
    g.font = `italic 900 ${size}px Archivo, sans-serif`;
    if (lines.every(t => g.measureText(t).width <= max) || size <= 20) break;
    size -= 2;
  }
  g.fillStyle = colour;
  lines.forEach((t, i) => {
    const w = g.measureText(t).width;
    g.fillText(t, align === "right" ? x - w : x, y + i * (size + 6));
  });
  return size;
}
""" % P
