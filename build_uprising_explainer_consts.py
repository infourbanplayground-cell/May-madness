# -*- coding: utf-8 -*-
"""The explainer's timing table, in one file.

The picture, the score and the recorder all need the same cuts. The older films
here each keep their own copy, and a copy is a thing that can disagree with the
picture the moment somebody moves a cut by 200ms — which is exactly how a drop
ends up landing half a second after the frame it was written for.

Underscored so Python can import it; `build-uprising-explainer.py` cannot be
imported under its own name.
"""
import os

SP = os.environ.get("SP") or (
    "/tmp/claude-0/-home-user-May-madness/0e44f0ad-a683-5f0d-9de6-9459ae328963/scratchpad")

# Scene starts, in order:
#   1 title            5 the climb (the hero)
#   2 come alone       6 the points table
#   3 the shuffle      7 new partners
#   4 first to N       8 highest total wins
SCENES = [0.00, 2.80, 6.40, 10.20, 13.60, 20.00, 24.80, 28.20]
DUR = 34.00

# Every cut, plus the beats inside the climb where the chip actually moves.
BEATS = [0.10, 1.40, 2.82, 4.60, 6.42, 8.20, 10.22, 11.90, 13.62, 15.80,
         17.90, 20.02, 21.60, 24.82, 26.40, 28.22, 30.20, 32.00]

# The two moments the film is built around: the first climb, and the last line.
HERO = [15.80, 28.22]
