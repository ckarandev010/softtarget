"""Local web server. Binds to 127.0.0.1 only: this app is deliberately vulnerable."""
import json
import threading
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from . import llm as llm_mod
from .labs import BY_ID, LABS, LEVELS, Session

STATIC = Path(__file__).parent / "static"
TYPES = {".html": "text/html; charset=utf-8", ".js": "text/javascript; charset=utf-8",
         ".css": "text/css; charset=utf-8", ".svg": "image/svg+xml"}
SESSIONS = {}
LOCK = threading.Lock()


def session(sid):
    with LOCK:
        if sid not in SESSIONS:
            SESSIONS[sid] = Session()
        return SESSIONS[sid]


def public_labs():
    return [{k: v for k, v in lab.items() if k != "run"} for lab in LABS]


def handle_chat(body, chat=None):
    chat = chat or llm_mod.chat
    lab, level = BY_ID.get(body.get("lab")), body.get("level")
    text = str(body.get("text", ""))[:6000]
    if not lab or level not in LEVELS or not text.strip():
        return 400, {"error": "need lab, level and text"}
    sess = session(str(body.get("session", "")))
    events = []
    try:
        out = lab["run"](sess, level, text, lambda m, t=None: chat(m, t), events)
    except llm_mod.LLMError as e:
        return 503, {"error": str(e)}
    out.setdefault("render", "text")
    if out.get("solved"):
        sess.solved.add(f"{lab['id']}:{level}")
    return 200, {**out, "events": events, "solved_all": sorted(sess.solved)}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):  # quiet
        pass

    def send(self, code, data, ctype="application/json"):
        raw = data if isinstance(data, bytes) else json.dumps(data).encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(raw)

    def body(self):
        n = int(self.headers.get("Content-Length") or 0)
        try:
            return json.loads(self.rfile.read(n) or b"{}")
        except ValueError:
            return {}

    def do_GET(self):
        path = self.path.split("?")[0]
        if path == "/api/labs":
            return self.send(200, {"labs": public_labs(), "levels": LEVELS, "session": uuid.uuid4().hex})
        if path == "/api/health":
            return self.send(200, llm_mod.health())
        name = "index.html" if path == "/" else path.lstrip("/")
        f = (STATIC / name).resolve()
        if STATIC.resolve() in f.parents and f.is_file():
            return self.send(200, f.read_bytes(), TYPES.get(f.suffix, "application/octet-stream"))
        self.send(404, {"error": "not found"})

    def do_POST(self):
        b = self.body()
        if self.path == "/api/chat":
            return self.send(*handle_chat(b))
        if self.path == "/api/solved":  # lab 3: the page reports that injected JavaScript ran
            sess = session(str(b.get("session", "")))
            if b.get("lab") == "output-html" and b.get("level") in LEVELS:
                sess.solved.add(f"output-html:{b['level']}")
            return self.send(200, {"solved_all": sorted(sess.solved)})
        if self.path == "/api/reset":
            sess = session(str(b.get("session", "")))
            sess.history.pop((b.get("lab"), b.get("level")), None)
            return self.send(200, {"ok": True})
        self.send(404, {"error": "not found"})


def serve(port=8765, open_browser=True):
    srv = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    url = f"http://127.0.0.1:{port}/"
    h = llm_mod.health()
    print(f"softtarget on {url}  (model {h['model']} at {h['host']}: {'ready' if h['ok'] else h['error']})")
    print("Deliberately vulnerable. Keep it on 127.0.0.1. Ctrl+C to stop.")
    if open_browser:
        import webbrowser
        webbrowser.open(url)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
