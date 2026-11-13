"""CiteDesk web app. Standard library only.

Run: python3 app.py   (serves on PORT, default 8000)
"""
import json
import os
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from bot import Bot, FlowSession, FLOWS

BASE = os.path.dirname(os.path.abspath(__file__))
BOT = Bot()
SESSIONS = {}

with open(os.path.join(BASE, "static", "index.html"), "rb") as f:
    INDEX = f.read()


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def _send(self, code, body, ctype="application/json"):
        if isinstance(body, (dict, list)):
            body = json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _json(self):
        length = int(self.headers.get("Content-Length") or 0)
        if not length:
            return {}
        try:
            return json.loads(self.rfile.read(length))
        except Exception:
            return {}

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            self._send(200, INDEX, "text/html; charset=utf-8")
        elif self.path == "/api/health":
            self._send(200, {"status": "ok", "articles": len(BOT.kb["articles"])})
        elif self.path == "/api/flows":
            self._send(200, {k: v["name"] for k, v in FLOWS.items()})
        else:
            self._send(404, {"error": "not found"})

    def do_POST(self):
        data = self._json()
        if self.path == "/api/ask":
            q = str(data.get("question", ""))
            self._send(200, BOT.ask(q))
        elif self.path == "/api/flow/start":
            flow_id = data.get("flow")
            if flow_id not in FLOWS:
                self._send(400, {"error": "unknown flow"})
                return
            sid = uuid.uuid4().hex
            SESSIONS[sid] = FlowSession(flow_id)
            view = SESSIONS[sid].view()
            view["session"] = sid
            self._send(200, view)
        elif self.path == "/api/flow/choose":
            sess = SESSIONS.get(data.get("session", ""))
            if sess is None:
                self._send(400, {"error": "unknown session"})
                return
            try:
                view = sess.choose(int(data.get("choice", 0)))
            except (IndexError, ValueError):
                self._send(400, {"error": "bad choice"})
                return
            self._send(200, view)
        else:
            self._send(404, {"error": "not found"})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    ThreadingHTTPServer(("0.0.0.0", port), Handler).serve_forever()
