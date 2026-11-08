# -*- coding: utf-8 -*-
"""Fonts for a project — copies the theme's fonts into <work>/fonts and points theme.json at them.

  python 39_fonts.py <work>            ← reads theme.json (font, latinFont), writes fontFile / latinFontFile
  python 39_fonts.py list              ← prints the local fonts (motion/fonts/fonts.json)

- Arabic/Darija text uses theme.font; Latin words use theme.latinFont (default Inter).
- A font the user uploaded (any .ttf/.otf inside <work>, or theme.font = "my-font.ttf") is used as-is.
- A font that is neither local nor uploaded stays a Google Fonts family (needs internet) — the script says so.
"""
import json, os, shutil, sys
for _s in (sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass

FD = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "motion", "fonts")
MAN = json.load(open(os.path.join(FD, "fonts.json"), encoding="utf-8"))["fonts"]

if len(sys.argv) < 2:
    sys.exit(__doc__)
if sys.argv[1] == "list":
    for f in MAN:
        print(f"{f['family']:<22} {f['script']:<7} {f['style']}")
    sys.exit(0)

W = os.path.abspath(sys.argv[1])
tp = os.path.join(W, "theme.json")
t = json.load(open(tp, encoding="utf-8")) if os.path.exists(tp) else {}
t.setdefault("latinFont", "Inter")
os.makedirs(os.path.join(W, "fonts"), exist_ok=True)

def resolve(fam, key):
    if not fam or fam == "auto":
        return
    up = os.path.join(W, fam) if fam.lower().endswith((".ttf", ".otf")) else None
    if up and os.path.exists(up):                          # uploaded font file
        name = os.path.splitext(os.path.basename(up))[0]
        shutil.copy2(up, os.path.join(W, "fonts", os.path.basename(up)))
        t["font" if key == "fontFile" else "latinFont"] = name
        t[key] = "fonts/" + os.path.basename(up)
        print(f"✅ {name} (uploaded) → {t[key]}"); return
    m = next((f for f in MAN if f["family"].lower() == fam.lower()), None)
    if m and os.path.exists(os.path.join(FD, m["file"])):
        shutil.copy2(os.path.join(FD, m["file"]), os.path.join(W, "fonts", m["file"]))
        t[key] = "fonts/" + m["file"]
        print(f"✅ {m['family']} (local) → {t[key]}"); return
    t.pop(key, None)
    print(f"ℹ️ {fam} isn't a local font — it loads from Google Fonts (needs internet)")

resolve(t.get("font"), "fontFile")
resolve(t.get("latinFont"), "latinFontFile")
json.dump(t, open(tp, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
