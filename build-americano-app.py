# -*- coding: utf-8 -*-
"""Re-inline the UPRISING engine into the Americano app, and stamp the build.

The app is a single file served from /var/www/americano-app/public, so the
engine has to live inside it. But the engine is also the thing the tests run
against (`node --test uprising-engine.test.js`), and a second hand-maintained
copy is exactly how logic in this repo has drifted from the thing that proves
it before.

So uprising-engine.js is the only source, and this script replaces whatever
sits between the two markers in americano-index.html with its current contents.
Running it twice changes nothing.

  node --test uprising-engine.test.js && python3 build-americano-app.py
"""
import hashlib, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
APP = os.path.join(HERE, "americano-index.html")
ENGINE = os.path.join(HERE, "uprising-engine.js")

START = "// ══ UPRISING ENGINE ══"
END = "// ══ END UPRISING ENGINE ══"


def main():
    app = open(APP).read()
    eng = open(ENGINE).read()

    # The browser gets plain globals; the CommonJS export is for the tests.
    tail = 'if (typeof module !== "undefined"'
    if tail in eng:
        eng = eng.split(tail)[0].rstrip() + "\n"

    i = app.find(START)
    j = app.find(END)
    if i < 0 or j < 0:
        sys.exit("the engine markers are missing from americano-index.html")
    j = app.index("\n", j) + 1

    head = (START + "══════════════════════════════════════════════════════\n"
            "// Inlined verbatim from uprising-engine.js by build-americano-app.py.\n"
            "// Do not edit it here: the tests run against that file, and a second\n"
            "// copy is how the rules drift away from the thing that proves them.\n")
    foot = END + "══════════════════════════════════════════════════════\n"
    app = app[:i] + head + eng + foot + app[j:]

    # NOTHING the engine declares may collide with a name the app already has.
    # The engine's helper was called pairKey, and so is one of the app's own —
    # a duplicate `const` in the same script is a SyntaxError that takes the
    # WHOLE babel block down, so the app did not render a broken screen, it
    # rendered nothing at all. Every engine name is prefixed `up` for this
    # reason, and this check is what keeps it that way.
    eng_names = set(re.findall(r"^(?:function|const|let|var)\s+(\w+)", eng, re.M))
    rest = app[:app.find(START)] + app[app.find(END):]
    app_names = set(re.findall(r"^\s*(?:function|const|let|var)\s+(\w+)", rest, re.M))
    clash = sorted(eng_names & app_names)
    if clash:
        sys.exit(f"!! the engine and the app both declare: {', '.join(clash)} "
                 f"— a duplicate declaration blanks the entire page")

    # Every function the app calls out of the engine must actually be in it.
    # A rename in uprising-engine.js that is not reflected in the app would
    # otherwise only show up when a scorer taps the button at 18:40.
    used = set(re.findall(r"\b(up[A-Z]\w+)\s*\(", app))
    defined = set(re.findall(r"\bfunction\s+(up[A-Z]\w+)\s*\(", eng))
    missing = sorted(u for u in used if u not in defined and u not in ("upCourtSizes",))
    if missing:
        sys.exit(f"!! the app calls engine functions that do not exist: {', '.join(missing)}")

    with open(APP, "w") as f:
        f.write(app)

    # This app's update check fetches version.txt and compares it with what the
    # browser stored last time — there is no build id inside the page to keep in
    # step, so version.txt only has to CHANGE when the page does. Hashing the
    # page gives exactly that, and nothing else: a redeploy of identical bytes
    # does not reload anybody.
    bid = hashlib.sha256(app.encode()).hexdigest()[:12]
    with open(APP + ".version", "w") as f:
        f.write(bid + "\n")
    print(f"americano-index.html  {len(app)/1024:.0f}KB  build {bid}")
    print(f"  engine: {len(eng)} bytes, {len(defined)} functions, {len(used & defined)} used by the app")


if __name__ == "__main__":
    main()
