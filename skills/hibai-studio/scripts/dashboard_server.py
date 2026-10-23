"""Serves the HibAI dashboard on this computer only and saves the answers to <work>/brief.json.

    python hibai.py dashboard <work> [--keep] [--no-open]

Stops by itself once the brief is saved (or after 30 minutes). --keep leaves it running.
"""
import base64
import json
import mimetypes
import os
import re
import threading
import time
import webbrowser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import unquote

IMAGE_EXT = (".png", ".jpg", ".jpeg", ".webp")
DASH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "dashboard")
TIMEOUT = 30 * 60


def serve(work, keep=False, open_browser=True):
    os.makedirs(work, exist_ok=True)
    brief_path = os.path.join(work, "brief.json")
    saved = threading.Event()

    class Handler(SimpleHTTPRequestHandler):
        def __init__(self, *a, **k):
            super().__init__(*a, directory=DASH, **k)

        def log_message(self, *_):
            pass

        def _json(self, code, body):
            data = json.dumps(body, ensure_ascii=False).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            path = self.path.split("?")[0]
            if path.startswith("/api/file/"):
                name = os.path.basename(unquote(path[len("/api/file/"):]))
                full = os.path.join(work, name)
                if not (name and os.path.isfile(full) and name.lower().endswith(IMAGE_EXT)):
                    return self._json(404, {})
                with open(full, "rb") as f:
                    data = f.read()
                self.send_response(200)
                self.send_header("Content-Type", mimetypes.guess_type(name)[0] or "application/octet-stream")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                return self.wfile.write(data)
            if path == "/api/brief":
                if os.path.exists(brief_path):
                    with open(brief_path, encoding="utf-8") as f:
                        return self._json(200, json.load(f))
                return self._json(404, {})
            return super().do_GET()

        def do_POST(self):
            if self.path == "/api/upload":
                return self._upload()
            if self.path != "/api/brief":
                return self._json(404, {})
            n = int(self.headers.get("Content-Length", 0))
            if n > 200_000:
                return self._json(413, {"error": "too big"})
            try:
                brief = json.loads(self.rfile.read(n).decode("utf-8"))
            except ValueError:
                return self._json(400, {"error": "not json"})
            with open(brief_path, "w", encoding="utf-8") as f:
                json.dump(brief, f, ensure_ascii=False, indent=1)
            self._json(200, {"ok": True})
            saved.set()

        def _upload(self):
            """{key, name, data: "data:image/png;base64,..."} -> <work>/<key>.<ext>"""
            n = int(self.headers.get("Content-Length", 0))
            if n > 12_000_000:
                return self._json(413, {"error": "too big"})
            try:
                body = json.loads(self.rfile.read(n).decode("utf-8"))
                head, b64 = body["data"].split(",", 1)
                ext = {"image/png": ".png", "image/jpeg": ".jpg", "image/webp": ".webp"}[head[5:].split(";")[0]]
                raw = base64.b64decode(b64)
            except (ValueError, KeyError):
                return self._json(400, {"error": "not a png, jpg or webp image"})
            key = re.sub(r"[^a-z0-9_]", "", str(body.get("key", "image")).lower()) or "image"
            name = key + ext
            with open(os.path.join(work, name), "wb") as f:
                f.write(raw)
            self._json(200, {"file": name})

    httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    url = f"http://127.0.0.1:{httpd.server_address[1]}/"
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    print(f"🟢 HibAI dashboard: {url}", flush=True)
    if open_browser:
        webbrowser.open(url)
    t0 = time.time()
    while time.time() - t0 < TIMEOUT:
        if saved.wait(1):
            print(f"✅ brief saved → {brief_path}", flush=True)
            if not keep:
                time.sleep(1.5)  # let the page show its "saved" screen
                break
            saved.clear()
    else:
        print("⏱️ dashboard closed after 30 minutes without a save")
    httpd.shutdown()
