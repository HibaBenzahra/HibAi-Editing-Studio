# -*- coding: utf-8 -*-
"""Storyboard sheet for user approval — one frame per scene, numbered, as many as the video needs.

  node scripts/04_render_frames.js <work> preview <t1> <t2> …      ← render the frames first (middle of each scene)
  python scripts/43_storyboard.py <work> <t1> <t2> … [--cols 4] [--out storyboard.jpg]

Reads <work>/prev/t<time>.jpg and writes one sheet (default 4 columns, any number of rows) with a big number and the
time on each frame. Send it with the numbered table (time · what's said · layout · visual · transition · sound).
Needs Pillow (python -m pip install pillow).
"""
import os, sys
for _s in (sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass
from PIL import Image, ImageDraw, ImageFont

args = [a for a in sys.argv[1:]]
if len(args) < 2:
    sys.exit(__doc__)
opt = lambda k, d: args[args.index(k) + 1] if k in args else d
cols, out = int(opt("--cols", 4)), opt("--out", "storyboard.jpg")
W = os.path.abspath(args[0])
times = [a for i, a in enumerate(args[1:], 1) if not a.startswith("--") and args[i - 1] not in ("--cols", "--out")]
tw, th, pad, head = 300, 533, 14, 0
rows = (len(times) + cols - 1) // cols
sheet = Image.new("RGB", (cols * (tw + pad) + pad, rows * (th + pad) + pad), (18, 18, 22))
d = ImageDraw.Draw(sheet)

def font(size):
    for f in ("arialbd.ttf", "Arial Bold.ttf", "DejaVuSans-Bold.ttf", "/System/Library/Fonts/Supplemental/Arial Bold.ttf"):
        try: return ImageFont.truetype(f, size)
        except Exception: pass
    return ImageFont.load_default()
big, small = font(40), font(24)
missing = []
for n, t in enumerate(times):
    p = os.path.join(W, "prev", f"t{float(t):.2f}.jpg")
    x, y = pad + (n % cols) * (tw + pad), pad + (n // cols) * (th + pad)
    if not os.path.exists(p):
        missing.append(t); d.rectangle([x, y, x + tw, y + th], outline=(90, 90, 90), width=2); continue
    sheet.paste(Image.open(p).convert("RGB").resize((tw, th)), (x, y))
    d.rounded_rectangle([x + 8, y + 8, x + 70, y + 58], 10, fill=(0, 0, 0))
    d.text((x + 39, y + 33), str(n + 1), font=big, fill=(255, 255, 255), anchor="mm")
    d.rounded_rectangle([x + tw - 92, y + 8, x + tw - 8, y + 44], 8, fill=(0, 0, 0))
    d.text((x + tw - 50, y + 26), f"{float(t):.1f}s", font=small, fill=(255, 255, 255), anchor="mm")
dst = os.path.join(W, out)
sheet.save(dst, quality=88)
print(f"✅ {dst}  ({len(times)} frames · {cols} columns)" + (f" · missing: {' '.join(missing)} — render them with 04 preview" if missing else ""))
