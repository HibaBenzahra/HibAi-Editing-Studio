# -*- coding: utf-8 -*-
"""Captions under the jaw — finds the speaker's chin over time (Windows · macOS · Linux).

  python 38_jaw.py <work>            ← reads <work>/vfr/*.jpg (the cut video, 30 fps, 1080x1920)

Writes studio.json ← "capJaw": [[t, chinY], ...] every 0.2 s (output-video seconds and pixels)
                   ← "faceBox": [x, y, w, h] the usual face position (the PiP frame zooms on it).
The engine puts the caption top just under chinY in full-screen shots, and never lower than the safe
zone allows (caption bottom ≤ 1480). No face found in a stretch → that stretch keeps the default place.
Needs: python -m pip install opencv-python-headless (model downloads once, 230 KB)
"""
import json, os, sys
for _s in (sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass
try:
    import cv2
except ImportError:
    sys.exit("❌ OpenCV missing — run: python -m pip install opencv-python-headless")

W = os.path.abspath(sys.argv[1])
VFR = os.path.join(W, "vfr")
frames = sorted(f for f in os.listdir(VFR) if f.endswith(".jpg")) if os.path.isdir(VFR) else []
if not frames:
    sys.exit("❌ no frames in <work>/vfr — run the cut step (03_cut_zoom + frame extraction) first")

FPS, STEP, SCALE = 30, 6, 3           # sample every 0.2 s, detect on a 1/3-size frame

# YuNet face detector (OpenCV's own, ~230 KB). Downloaded once from the official opencv_zoo repo.
MODEL_URL = "https://github.com/opencv/opencv_zoo/raw/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx"
MODEL = os.path.join(os.path.expanduser("~"), ".hibai-studio", "models", "face_detection_yunet_2023mar.onnx")
if not os.path.exists(MODEL):
    import urllib.request
    os.makedirs(os.path.dirname(MODEL), exist_ok=True)
    print("⬇️ downloading the face model once (230 KB)…", flush=True)
    urllib.request.urlretrieve(MODEL_URL, MODEL)
det = None
raw = []                               # (t, chin or None)
boxes = []                             # face boxes (x, y, w, h) in 1080x1920 px — for the PiP frame
for i in range(0, len(frames), STEP):
    img = cv2.imread(os.path.join(VFR, frames[i]))
    if img is None:
        continue
    h, w = img.shape[:2]
    small = cv2.resize(img, (w // SCALE, h // SCALE))
    if det is None:
        det = cv2.FaceDetectorYN.create(MODEL, "", (small.shape[1], small.shape[0]), 0.7)
    _, faces = det.detect(small)
    chin = None
    if faces is not None and len(faces):
        f = max(faces, key=lambda f: f[2] * f[3])               # the biggest face = the speaker
        x, y, fw, fh = f[:4]
        if fw * SCALE > w * 0.12:                               # ignore tiny faces in the background
            eye_y = (f[5] + f[7]) / 2; mouth_y = (f[11] + f[13]) / 2
            jaw = max(y + fh, mouth_y + (mouth_y - eye_y) * 0.75)   # chin ≈ a bit below the mouth
            chin = jaw * SCALE * (1920 / h)
            k = SCALE * (1920 / h); boxes.append((x * k, y * k, fw * k, fh * k))
    raw.append((round(i / FPS, 2), chin))

# smooth: median over ±0.6 s, ignore gaps; keep steady so captions don't wobble
out = []
for k, (t, _) in enumerate(raw):
    win = [c for tt, c in raw[max(0, k - 3):k + 4] if c is not None]
    if len(win) >= 2:
        win.sort()
        out.append([t, round(win[len(win) // 2])])
found = len(out) / max(1, len(raw))

sp = os.path.join(W, "studio.json")
st = json.load(open(sp, encoding="utf-8")) if os.path.exists(sp) else {}
st["capJaw"] = out
if boxes:                              # median face box: the PiP circle/square zooms on the face
    med = lambda i: sorted(b[i] for b in boxes)[len(boxes) // 2]
    st["faceBox"] = [round(med(0)), round(med(1)), round(med(2)), round(med(3))]
json.dump(st, open(sp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
ys = [y for _, y in out]
print(f"✅ chin found in {found:.0%} of the video" + (f" · chin y {min(ys)}–{max(ys)} px" if ys else "") + " → studio.json ← capJaw")
if found < 0.5:
    print("ℹ️ face often not found (side angle, hand over face, no person) — those moments keep the default caption place")
