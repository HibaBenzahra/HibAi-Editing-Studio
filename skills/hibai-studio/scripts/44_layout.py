# -*- coding: utf-8 -*-
"""Layout plan — how the speaker and the visuals share the screen, from the user's dashboard choice (Windows · macOS · Linux).

  python 44_layout.py <work> [--layout split|alternate|splitmix|visuals|pip|cutout|full] [--write]

reads   <work>/caps.json (caption timing) · <work>/theme.json ← layout, pip, hook.dur
writes  (with --write) studio.json ← "scenes": [{s, e, m:'R_FULL'|'R_DOWN'|'R_OFF'|'R_PIP', gb}]  — the engine reads them at init
        and prints the cut-out commands for «cutout» moments (11_behind_text.js cutout a-b).

Layouts (dashboard «أنت والرسوم»):
  full      you full screen, visuals over you                     split     visuals on top, you below — the whole time
  alternate you ↔ visuals full screen, sentence by sentence        splitmix  split, and every 3rd beat visuals only
  visuals   visuals only (your voice), you at the start + end      pip       visuals full screen, you small in a frame (circle/square/rect)
  cutout    you cut out (no background) in front of the visuals, alternating with split
Always: the hook (first beat) and the last beat (CTA) are you full screen. Beats are caption sentences merged to ≥ 1.8 s.
Without --write it only prints the plan. The storyboard step (43_storyboard.py) shows it before rendering.
"""
import json, os, sys
for _s in (sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass

args = [a for a in sys.argv[1:] if not a.startswith("--")]
if not args:
    sys.exit(__doc__)
W = os.path.abspath(args[0])
flags = sys.argv[1:]
opt = lambda k: flags[flags.index(k) + 1] if k in flags and flags.index(k) + 1 < len(flags) else None
load = lambda f, d: json.load(open(os.path.join(W, f), encoding="utf-8")) if os.path.exists(os.path.join(W, f)) else d

caps, theme, studio = load("caps.json", None), load("theme.json", {}), load("studio.json", {})
if not caps or not caps.get("cards"):
    sys.exit("❌ no caps.json — run the captions step first")
LAY = opt("--layout") or theme.get("layout") or "split"
if LAY not in ("split", "alternate", "splitmix", "visuals", "pip", "cutout", "full"):
    sys.exit(f"❌ unknown layout «{LAY}»")
hook_end = float((theme.get("hook") or {}).get("dur") or 0)

# beats: caption sentences merged until each lasts ≥ 1.8 s
beats = []
for c in caps["cards"]:
    words = " ".join(w["t"] for w in c["w"])
    if beats and (beats[-1]["e"] - beats[-1]["s"] < 1.8):
        beats[-1]["e"] = c["e"]; beats[-1]["txt"] += " " + words
    else:
        beats.append({"s": c["s"], "e": c["e"], "txt": words})
if len(beats) > 1 and beats[-1]["e"] - beats[-1]["s"] < 1.2:     # a tiny last beat joins the one before
    beats[-2]["e"] = beats[-1]["e"]; beats[-2]["txt"] += " " + beats[-1]["txt"]; beats.pop()
# the hook: every beat that starts before the hook ends stays full screen
nh = max(1, sum(1 for b in beats if b["s"] < hook_end - 0.3))

def pick(i, k):
    """k = index among the middle beats"""
    if LAY == "full": return "R_FULL"
    if LAY == "split": return "R_DOWN"
    if LAY == "visuals": return "R_OFF"
    if LAY == "pip": return "R_PIP"
    if LAY == "alternate": return "R_OFF" if k % 2 == 0 else "R_FULL"
    if LAY == "splitmix": return "R_OFF" if k % 3 == 2 else "R_DOWN"
    if LAY == "cutout": return "CUT" if k % 2 == 0 else "R_DOWN"

plan = []
for i, b in enumerate(beats):
    m = "R_FULL" if (i < nh or (i == len(beats) - 1 and len(beats) > nh + 1)) else pick(i, i - nh)
    plan.append({**b, "m": m})
# neighbours with the same layout become one scene (no needless transitions)
scenes = []
for p in plan:
    if scenes and scenes[-1]["m"] == p["m"]:
        scenes[-1]["e"] = p["e"]; scenes[-1]["txt"] += " · " + p["txt"]
    else:
        scenes.append(dict(p))
scenes[0]["s"] = 0
for a, b in zip(scenes, scenes[1:]):
    a["e"] = b["s"]                                           # no gaps
scenes[-1]["e"] = 99

NAMES = {"R_FULL": "you full screen", "R_DOWN": "split: visuals top · you below", "R_OFF": "visuals only",
         "R_PIP": f"visuals + you in a {theme.get('pip', 'circle')}", "CUT": "you cut out in front of visuals"}
print(f"🎬 layout «{LAY}» — {len(scenes)} scenes")
for s in scenes:
    e = min(s["e"], caps["total"])
    print(f"  {s['s']:6.2f}–{e:6.2f}  {NAMES[s['m']]:<34} {s['txt'][:60]}")

out, cuts = [], []
for s in scenes:
    if s["m"] == "CUT":
        cuts.append((round(s["s"], 2), round(min(s["e"], caps["total"]), 2)))
        out.append({"s": round(s["s"], 2), "e": round(s["e"], 2), "m": "R_FULL"})   # the cut-out draws the person, the background shows
    else:
        sc = {"s": round(s["s"], 2), "e": round(s["e"], 2), "m": s["m"]}
        if s["m"] == "R_DOWN": sc["gb"] = 600
        out.append(sc)

if "--write" in flags:
    studio["scenes"] = out
    json.dump(studio, open(os.path.join(W, "studio.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("✅ studio.json ← scenes (edit there to change a moment; the engine reads them, they override SCENES in compose.html)")
else:
    print("ℹ️ plan only — add --write to save it to studio.json")
if cuts:
    here = os.path.dirname(os.path.abspath(__file__))
    print("✂️ cut-out moments — run once each (Mac: Vision · Windows/Linux: rembg):")
    for a, b in cuts:
        print(f'   node "{os.path.join(here, "11_behind_text.js")}" "{W}" cutout {a}-{b}')
print("Where visuals go: split → y 160–600 · visuals only → y 160–1300 · PiP → y 160–750, rect frame 160–630 (you: bottom-left, x 70–410) · cut-out → y 160–850, beside you.")
