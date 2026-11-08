# -*- coding: utf-8 -*-
"""Cut the speaker out of each frame — Windows · macOS · Linux (same output as personmask.swift).

  python personmask.py <inDir> <outDir> [fast|balanced|accurate] [feather]

  reads   <inDir>/*.jpg
  writes  <outDir>/<same name>.png   grey mask (white = person), soft edge
          <outDir>/meta.json          [{"f": "00012.jpg", "face": {"x","y","w","h"}}, ...]
Uses rembg (model u2net_human_seg, downloads once ~170 MB) and the OpenCV YuNet face model (38_jaw.py downloads it).
Needs: python -m pip install "rembg[cpu]" pillow opencv-python-headless
11_behind_text.js calls this on Windows/Linux, and on a Mac without Xcode tools.
"""
import json, os, sys
for _s in (sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass
if len(sys.argv) < 3:
    sys.exit("usage: python personmask.py <inDir> <outDir> [quality] [feather]")
IN, OUT = sys.argv[1], sys.argv[2]
Q = sys.argv[3] if len(sys.argv) > 3 else "accurate"
FEATHER = float(sys.argv[4]) if len(sys.argv) > 4 else 2.5
try:
    from rembg import remove, new_session
    from PIL import Image, ImageFilter
except ImportError:
    sys.exit('❌ rembg missing — run: python -m pip install "rembg[cpu]" pillow')
os.makedirs(OUT, exist_ok=True)
files = sorted(f for f in os.listdir(IN) if f.endswith(".jpg"))
sess = new_session("u2net_human_seg")
SIDE = {"fast": 640, "balanced": 960}.get(Q)        # accurate = full size

det = None
MODEL = os.path.join(os.path.expanduser("~"), ".hibai-studio", "models", "face_detection_yunet_2023mar.onnx")
try:
    import cv2, numpy as np
    if not os.path.exists(MODEL):
        import urllib.request
        os.makedirs(os.path.dirname(MODEL), exist_ok=True)
        urllib.request.urlretrieve("https://github.com/opencv/opencv_zoo/raw/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx", MODEL)
except Exception:
    cv2 = None

meta = []
for n, f in enumerate(files):
    out = os.path.join(OUT, f[:-4] + ".png")
    im = Image.open(os.path.join(IN, f)).convert("RGB")
    W, H = im.size
    if not os.path.exists(out):
        src = im if not SIDE or max(W, H) <= SIDE else im.resize((round(W * SIDE / max(W, H)), round(H * SIDE / max(W, H))))
        m = remove(src, session=sess, only_mask=True, post_process_mask=True).convert("L")
        if m.size != (W, H):
            m = m.resize((W, H), Image.BILINEAR)
        if FEATHER > 0:
            m = m.filter(ImageFilter.GaussianBlur(FEATHER))
        m.save(out)
    row = {"f": f}
    if cv2 is not None:
        try:
            s = 3
            small = cv2.resize(cv2.cvtColor(np.array(im), cv2.COLOR_RGB2BGR), (W // s, H // s))
            if det is None:
                det = cv2.FaceDetectorYN.create(MODEL, "", (small.shape[1], small.shape[0]), 0.7)
            _, faces = det.detect(small)
            if faces is not None and len(faces):
                x, y, w, h = max(faces, key=lambda a: a[2] * a[3])[:4]
                row["face"] = {"x": float(x * s), "y": float(y * s), "w": float(w * s), "h": float(h * s)}
        except Exception:
            pass
    meta.append(row)
    if n % 15 == 0:
        print(f"  {n + 1}/{len(files)}", flush=True)
json.dump(meta, open(os.path.join(OUT, "meta.json"), "w"))
print(f"masks: {len(meta)}")
