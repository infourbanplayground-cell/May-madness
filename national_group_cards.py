# -*- coding: utf-8 -*-
"""Vol.9's OWN draw / tables / bracket painter.

`national_cards.py` gave the LINE-UP cards this volume's design and left these
three wearing Vol.8's: a true-black composition swept red, violet corner wash
and all, with square letter tiles, square rows, a centred club mark and no
band, no medallion, no Arabic, no tile. The canvas is invisible to every DOM
harness in this repo, so nothing complained — and nothing would have.

It also OVERLAPPED ITSELF, which is what the owner reported. The caller
divides the band evenly between the groups; `gcGroup` then sized its rows
`Math.max(52, Math.min(96, fit))`, and the 52 FLOOR is not a minimum, it is a
guarantee of overflow — at four rows the block drew 62 + 4*(52+8) = 302px into
a 232px slot, 70px over, every group, compounding down the card so GROUP B's
header landed on GROUP A's last row. A floor that cannot be honoured does not
make the row taller, it makes the block taller than the space it was given.
There is no floor here: the block is sized to the slot it is handed, and the
type is sized from the row.

Sixteen teams and four headers in one portrait card is 20 lines in ~1150px of
body, so the rows ARE short. That is the arithmetic of the card, not a fault to
engineer around; the alternative is dropping the bottom team of the bottom
group, which is the team most likely to be looking.

Shares `national_cards.py`'s vocabulary — NC, ncBand, ncLandmark, ncArt,
ncPreload — so the two sets cannot drift apart.
"""


def painter(P):
    return """
// ── Vol.9 group / bracket cards ───────────────────────────────────────────
const NG = {
  L: NC.PAD + 28,
  EYE: 268,          // eyebrow baseline
  H1: 372, H2: 476,  // the two headline lines
  DISP: 104,
  TOP: 530,          // body top, with no key row
  BOT: 1654,         // body bottom; the foot block and the band live below
  MED: 62,           // the landmark medallion beside the headline
  RAD: 14,           // a row's corner — a tall block pilled is an ellipse
};

// Which landmark, from the SESSION number in the eyebrow. These cards carry
// the host in `foot` rather than "NIGHT 06", so ncLandmark cannot read them.
function ngLandmark(d) {
  if (typeof LANDMARKS === "undefined" || !LANDMARKS.length) return null;
  const m = String(d && d.eyebrow || "").match(/(\\d+)/);
  return landmarkFor(Math.max(0, (m ? parseInt(m[1], 10) : 1) - 1));
}
async function ngPreload(d) {
  const lm = ngLandmark(d);
  const im = lm && ncArt(lm.asset);
  if (!im || (im.complete && im.naturalWidth)) return;
  await new Promise(r => { im.onload = r; im.onerror = r; setTimeout(r, 1500); });
}

// WHERE EACH BLOCK WAS GIVEN AND WHERE IT ACTUALLY ENDED. This is the one
// thing on these cards that cannot be seen in the bitmap: a group header
// landing on the row above it is ivory type on a deep-red pill, which no
// colour sample distinguishes from the same type 40px higher. So the painter
// reports its own geometry and ops/check-cards.mjs reads it back.
let NG_BLOCKS = [];

// A pill. Canvas got roundRect late enough that the fallback is not optional.
function ngPill(g, x, y, w, h, r) {
  g.beginPath();
  if (g.roundRect) g.roundRect(x, y, w, h, r); else g.rect(x, y, w, h);
}

// ── one group's block ─────────────────────────────────────────────────────
// Sized to the slot it is GIVEN, with no floor. Everything inside is derived
// from the row height, so a six-team group and a four-team group are the same
// design at two sizes rather than two designs.
function ngGroup(g, d, x, y, w, h) {
  const A = NC;
  const rows = d.rows || [];
  const n = Math.max(1, rows.length);
  const HEAD = Math.min(46, h * 0.19);
  const gap = 5;
  const rh = Math.min(96, (h - HEAD - gap * n) / n);

  // the letter, on an ivory disc. The handoff has no square blocks, and a
  // letter in a circle is the one place a disc is unambiguous.
  const dr = Math.min(21, HEAD * 0.46);
  g.fillStyle = A.IVORY;
  g.beginPath(); g.arc(x + dr, y + dr, dr, 0, Math.PI * 2); g.fill();
  g.font = `italic 900 ${Math.round(dr * 1.26)}px Archivo, sans-serif`;
  g.fillStyle = A.INK;
  {
    const t = d.letter || "";
    g.fillText(t, x + dr - g.measureText(t).width / 2, y + dr + dr * 0.44);
  }

  stMono(g, d.title || "", x + dr * 2 + 16, y + dr + 7, Math.round(dr * 0.92), A.IVORY, 4);
  if (d.note) {
    const s = Math.round(dr * 0.8);
    g.font = `700 ${s}px "JetBrains Mono", monospace`;
    const tw = g.measureText(d.note).width + 4 * (d.note.length - 1);
    stMono(g, d.note, x + w - tw, y + dr + 6, s, A.ROSE, 4);
  }

  let ry = y + HEAD;
  rows.forEach((r, i) => {
    // Three states, not two. A third-placed team has NOT been knocked out
    // when this card goes up — it is either a best third or in the playoff —
    // so "still in it" is its own state and is never drawn as eliminated.
    const live = r.through === true;
    const alive = r.through === "alive";
    const out = r.through === false;

    g.save();
    ngPill(g, x, ry, w, rh, NG.RAD);
    g.fillStyle = A.DEEP; g.fill();
    g.clip();
    // GREEN IS THE WINNER'S EDGE, the same thing it means on the line-up
    // card's champion plate — never a fill and never a lamp. A through team
    // gets a bar down its left; nothing else on these cards is green.
    if (live) { g.fillStyle = A.GREEN; g.fillRect(x, ry, 7, rh); }
    else if (alive) { g.fillStyle = A.FLAG; g.fillRect(x, ry, 7, rh); }
    g.restore();
    ngPill(g, x + 1.25, ry + 1.25, w - 2.5, rh - 2.5, NG.RAD);
    g.strokeStyle = live ? A.GREEN : alive ? A.ROSE : "rgba(247,241,230,.26)";
    g.lineWidth = live || alive ? 2.5 : 1.5;
    g.stroke();

    const pad = 18 + 7;
    let nx = x + pad;
    // A position only on a card that HAS positions. On the draw nothing has
    // been played, so 1-2-3-4 beside the names reads as a ranking somebody
    // made, when it is only the order the teams were entered.
    if (d.ordered) {
      const s = Math.round(rh * 0.38);
      g.font = `700 ${s}px "JetBrains Mono", monospace`;
      // NEVER the green. #087A3F on the deep red is about 1.2:1 — the first
      // render put the position of every qualifying team in a colour that is
      // not there. Green is the EDGE; the numeral is ivory, or rose once the
      // team is out.
      g.fillStyle = out ? A.ROSE : A.IVORY;
      g.fillText(String(i + 1), nx, ry + rh / 2 + s * 0.36);
      nx += Math.max(26, s * 1.5);
    }

    // the tail — wins and game difference, or the seed — measured first, so
    // the name is fitted to the room that is actually left
    let tail = 0;
    if (r.tail) {
      const s = Math.round(rh * 0.3);
      g.font = `700 ${s}px "JetBrains Mono", monospace`;
      const tw = g.measureText(r.tail).width + 3 * (r.tail.length - 1);
      stMono(g, r.tail, x + w - 20 - tw, ry + rh / 2 + s * 0.36, s,
             out ? A.ROSE : A.IVORY, 3);
      tail = tw + 24;
    }
    const size = stFit(g, r.name, w - pad - (nx - x - pad) - 20 - tail,
                       Math.min(44, Math.round(rh * 0.56)), 900);
    g.font = `italic 900 ${size}px Archivo, sans-serif`;
    g.fillStyle = out ? A.ROSE : A.IVORY;
    g.fillText(r.name, nx, ry + rh / 2 + size * 0.34);

    ry += rh + gap;
  });
  NG_BLOCKS.push({ letter: d.letter, rows: n, rh,
                   slot: [y, y + h], drawn: [y, ry - gap] });
}

// ── the knockout, round by round ──────────────────────────────────────────
// The LAYOUT is kept from the volume this inherits from, and deliberately:
// the rounds stack because three columns leave ~300px a slot and a doubles
// pair does not fit in 300px at any size worth reading; each round is inset so
// the card visibly narrows; a chevron pushes the eye down the tree; and the
// champions get the foot. What changes is everything about how it is DRAWN —
// pilled rows, the winner's green edge, and the champions on an ivory plate
// with its own weave, which is the same plate the line-up card's result sits
// on.
function ngBracket(g, d, x, y, w, h, faces) {
  const A = NC;
  const cols = (d.cols || []).filter(c => c.ties && c.ties.length);
  if (!cols.length) return;

  const last = cols[cols.length - 1];
  const fin = last.label === "FINAL" ? last.ties[0] : null;
  const champ = fin ? (fin.aWon ? fin.a : fin.bWon ? fin.b : "") : "";
  const CH = champ ? 200 : 0;

  const ties = cols.reduce((n, c) => n + c.ties.length, 0);
  const LBL = 34, SGAP = 30, RGAP = 26, STEP = 52, CGAP = 44;
  const band = h - (champ ? CH + CGAP : 0);
  const avail = band - cols.length * (LBL + SGAP) - (ties - cols.length) * RGAP;
  const units = ties + (fin ? 0.55 : 0);
  // Capped above but NOT below: this is the same floor that overlapped the
  // draw card, and a bracket deep enough to hit it would overlap the same way.
  const th = Math.min(132, avail / units);

  const rowsH = cols.reduce((n, c) =>
    n + LBL + c.ties.length * (c.label === "FINAL" ? th * 1.55 : th)
      + (c.ties.length - 1) * RGAP + SGAP, 0) - SGAP;
  const contentH = rowsH + (champ ? CGAP + CH : 0);
  let cy = y + Math.max(0, (h - contentH) / 2);
  const top = cy;

  cols.forEach((col, ci) => {
    const inset = ci * STEP;
    const cx = x + inset, cw = w - inset * 2;
    const isFinal = col.label === "FINAL";
    const rowH = isFinal ? th * 1.55 : th;

    stMono(g, col.label, cx, cy + 18, 19, isFinal ? A.IVORY : A.ROSE, 3);
    cy += LBL;
    col.ties.forEach(t => {
      const rh = (rowH - 4) / 2;
      [[t.a, t.aWon, t.aScore, t.aPics], [t.b, t.bWon, t.bScore, t.bPics]]
        .forEach(([nm, won, sc, pics], k) => {
        const ry = cy + k * (rh + 4);
        g.save();
        ngPill(g, cx, ry, cw, rh, NG.RAD);
        g.fillStyle = A.DEEP; g.fill();
        g.clip();
        if (won) { g.fillStyle = A.GREEN; g.fillRect(cx, ry, 7, rh); }
        g.restore();
        ngPill(g, cx + 1.25, ry + 1.25, cw - 2.5, rh - 2.5, NG.RAD);
        g.strokeStyle = won ? A.GREEN : "rgba(247,241,230,.26)";
        g.lineWidth = won ? 2.5 : 1.5;
        g.stroke();

        // Faces ONLY on the final. A quarter-final row is ~44px tall, and a
        // face in it lands at about 16px once a story is scaled to a phone —
        // a smudge that also steals the width the name needs.
        let tx = cx + 26;
        if (isFinal && pics && pics.length) {
          const fr = rh * 0.40;
          pics.slice(0, 2).forEach((q, j) => {
            gcFace(g, q, cx + 24 + fr + j * fr * 1.55, ry + rh / 2, fr, faces);
          });
          tx = cx + 24 + fr * 2.55 + fr + 18;
        }
        let tail = 0;
        if (sc) {
          const s = Math.round(rh * 0.42);
          g.font = `700 ${s}px "JetBrains Mono", monospace`;
          const tw = g.measureText(sc).width;
          g.fillStyle = won ? A.IVORY : A.ROSE;
          g.fillText(sc, cx + cw - 22 - tw, ry + rh / 2 + s * 0.36);
          tail = tw + 24;
        }
        const size = stFit(g, nm || "TBD", cw - (tx - cx) - 22 - tail,
                           Math.round(rh * 0.5), 900);
        g.font = `italic 900 ${size}px Archivo, sans-serif`;
        g.fillStyle = nm ? (won ? A.IVORY : A.ROSE) : "rgba(247,241,230,.35)";
        g.fillText(nm || "TBD", tx, ry + rh / 2 + size * 0.34);
      });
      cy += rowH + RGAP;
    });
    cy += SGAP - RGAP;
    if (ci < cols.length - 1) {
      const mx = x + w / 2, my = cy - SGAP / 2 - 2, s = 13;
      g.strokeStyle = "rgba(247,241,230,.45)"; g.lineWidth = 3;
      g.beginPath();
      g.moveTo(mx - s, my - s / 2); g.lineTo(mx, my + s / 2); g.lineTo(mx + s, my - s / 2);
      g.stroke();
    }
  });

  // ── champions, on the ivory plate ──
  // Drawn only when the final has been WON. An undecided final renders both
  // names on equal footing with no scores, which reads correctly as "this is
  // about to happen"; a card announcing an empty winner is worse than one
  // that stops at the semis.
  if (champ) {
    const by = top + rowsH + CGAP, bh = CH;
    g.save();
    ngPill(g, x, by, w, bh, 34);
    g.fillStyle = A.IVORY; g.fill();
    g.clip();
    const b = LU_BAND_IMG, th2 = 14;
    g.fillStyle = A.DEEP; g.fillRect(x, by, w, th2);
    if (b) {
      const tw = Math.round(th2 * b.width / b.height);
      for (let px = x; px < x + w; px += tw) g.drawImage(b, px, by, tw, th2);
    }
    g.restore();

    stMono(g, "CHAMPIONS", x + 30, by + 62, 20, A.FLAG, 5);

    const cp = fin ? (fin.aWon ? fin.aPics : fin.bPics) : null;
    let right = x + w - 30;
    if (cp && cp.length) {
      const fr = 50;
      // Left to right, matching the order of the two names beside them.
      cp.slice(0, 2).forEach((q, j) => {
        gcFace(g, q, x + w - 36 - fr - (1 - j) * fr * 1.6, by + bh / 2 + 14, fr, faces);
      });
      right = x + w - 36 - fr * 2.6 - fr - 20;
    }
    const size = stFit(g, champ, right - (x + 30), 68, 900);
    g.font = `italic 900 ${size}px Archivo, sans-serif`;
    g.fillStyle = A.INK;
    g.fillText(champ, x + 30, by + bh - 38);
  }
}

// ── the card ──────────────────────────────────────────────────────────────
function ngPaint(g, kind, d, logo, faces) {
  const A = NC;
  const L = NG.L, R = LU_W - NC.PAD - 28, W = R - L;
  g.textBaseline = "alphabetic";
  NG_BLOCKS = [];

  // the ground, and the khanjar over it
  g.fillStyle = A.BG; g.fillRect(0, 0, LU_W, LU_H);
  if (LU_TILE_IMG) {
    g.save(); g.globalAlpha = 0.14;
    const t = 300;
    for (let y = 0; y < LU_H; y += t) for (let x = 0; x < LU_W; x += t)
      g.drawImage(LU_TILE_IMG, x, y, t, t);
    g.restore();
  }

  // the frame
  ncBand(g, 72);
  ncBand(g, LU_H - 72 - NC.BAND);

  // the header row: the series in mono, the Arabic opposite
  stMono(g, SERIES_NAME, L, 206, 25, A.IVORY, 5);
  {
    g.font = `700 30px "Noto Kufi Arabic", sans-serif`;
    g.fillStyle = A.IVORY;
    g.fillText(SERIES_NAME_AR, R - g.measureText(SERIES_NAME_AR).width, 212);
  }

  // the landmark medallion, beside the headline. On the line-up card it
  // straddles the arch's apex; there is no arch on a list card, so it sits
  // where the headline ends and holds the right edge of the block.
  const mcx = R - NG.MED, mcy = (NG.H1 + NG.H2) / 2 - 26;
  {
    const lm = ngLandmark(d);
    g.fillStyle = A.DEEP;
    g.beginPath(); g.arc(mcx, mcy, NG.MED, 0, Math.PI * 2); g.fill();
    g.strokeStyle = A.IVORY; g.lineWidth = 5;
    g.beginPath(); g.arc(mcx, mcy, NG.MED, 0, Math.PI * 2); g.stroke();
    g.strokeStyle = A.GREEN; g.lineWidth = 4;
    g.beginPath(); g.arc(mcx, mcy, NG.MED + 8, 0, Math.PI * 2); g.stroke();
    const art = lm && ncArt(lm.asset);
    if (art && art.complete && art.naturalWidth) {
      const s = NG.MED * 1.16;
      const r = Math.min(s / art.naturalWidth, s / art.naturalHeight);
      g.drawImage(art, mcx - art.naturalWidth * r / 2,
                  mcy - art.naturalHeight * r / 2 + 3,
                  art.naturalWidth * r, art.naturalHeight * r);
    }
  }

  stMono(g, (d.eyebrow || "").toUpperCase(), L, NG.EYE, 24, A.ROSE, 5);
  const big = kind === "draw"   ? ["THE", "DRAW"]
            : kind === "tables" ? ["GROUP", "TABLES"]
            :                     ["THE", "BRACKET"];
  // The headline stops short of the medallion, which is why it is measured
  // against a narrower box than the body uses.
  const HW = W - NG.MED * 2 - 46;
  stDisp(g, big[0], L, NG.H1, NG.DISP, A.IVORY, HW);
  stDisp(g, big[1], L, NG.H2, NG.DISP, A.IVORY, HW);

  // the key, on the one card that needs one. Green means "through" here and
  // means nothing on the draw, so it is stated only where it carries meaning.
  let TOP = NG.TOP;
  if (d.keys && d.keys.length) {
    let kx = L;
    d.keys.forEach(([col, label]) => {
      g.fillStyle = col;
      ngPill(g, kx, 500, 22, 22, 6); g.fill();
      kx += 32;
      const s = 19;
      g.font = `700 ${s}px "JetBrains Mono", monospace`;
      const tw = g.measureText(label).width + 3 * (label.length - 1);
      stMono(g, label, kx, 518, s, A.IVORY, 3);
      kx += tw + 34;
    });
    TOP = NG.TOP + 36;
  }

  // ── body ──
  const BOT = NG.BOT;
  if (kind === "bracket") {
    ngBracket(g, d, L, TOP, W, BOT - TOP, faces || new Map());
  } else {
    const groups = d.groups || [];
    const n = Math.max(1, groups.length);
    const gap = 18;
    const bh = (BOT - TOP - gap * (n - 1)) / n;
    groups.forEach((gr, i) => ngGroup(g, gr, L, TOP + i * (bh + gap), W, bh));
  }

  // ── the foot ──
  // Everything here clears the bottom band, which starts at LU_H-72-BAND.
  // A decorative strip is invisible to every text check there is, so the one
  // thing that can go wrong here is drawing straight through the weave.
  if (logo) {
    const h = 74, w = logo.width * (h / logo.height);
    const off = document.createElement("canvas");
    off.width = Math.ceil(w); off.height = h;
    const o = off.getContext("2d");
    o.drawImage(logo, 0, 0, w, h);
    o.globalCompositeOperation = "source-in";
    o.fillStyle = A.IVORY; o.fillRect(0, 0, w, h);
    g.drawImage(off, L, BOT + 24);
  }
  {
    const t = `${VOLUME_LABEL} \\u00B7 ${SEASON_MONTH_SHORT} ${SEASON_YEAR}`;
    g.font = '700 26px "JetBrains Mono", monospace';
    const w = g.measureText(t).width + 7 * (t.length - 1);
    stMono(g, t, R - w, BOT + 60, 26, A.IVORY, 7);
    const host = d.foot || "";
    if (host) {
      const s = 22;
      g.font = `700 ${s}px "JetBrains Mono", monospace`;
      const hw = g.measureText(host).width + 5 * (host.length - 1);
      stMono(g, host, R - hw, BOT + 100, s, A.ROSE, 5);
    }
  }
}
""" % P
