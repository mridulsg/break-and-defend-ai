"""A small web server for lab consoles: static files plus a JSON API. Standard library only, so there is nothing to audit but this file.

A lab builds a routes table and calls serve():

    routes = {("GET", "/api/state"): lambda body, query: {"ok": True},
              ("POST", "/api/ask"):  lambda body, query: {...}}
    serve(routes, static_dir="/console/static", port=8080)

A handler takes (body, query) and returns a JSON-serialisable dict. It raises ApiError(status, message) for expected problems.

Why it is built the way it is (this is a security course, so the console practises what it teaches):
  * It only answers requests whose Host header is localhost, 127.0.0.1 or [::1]. A web page on another site cannot
    use DNS rebinding to talk to your lab.
  * POST needs Content-Type: application/json, and an Origin header (when sent) must match Host. A web page on
    another site cannot make your browser submit a form to your lab.
  * The page is served with a strict Content-Security-Policy and the UI writes all model and user text with
    textContent, never as HTML. A model answer containing <script> is displayed as text, not run.
  * Request bodies are capped, and static files are served only from inside the static directory.
"""
import json
import mimetypes
import pathlib
import threading
import traceback
import urllib.parse
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

MAX_BODY = 64 * 1024
ALLOWED_HOSTS = {"localhost", "127.0.0.1", "[::1]"}
WIDGET_PORT = 8301  # the unsafe page is served on this port only, so it has a different origin from the console
CSP = ("default-src 'none'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; "
       f"frame-src http://127.0.0.1:{WIDGET_PORT} http://localhost:{WIDGET_PORT}; base-uri 'none'; form-action 'none'; "
       "frame-ancestors 'none'")
# One page is deliberately unsafe: widget.html (Chapter 4) builds its page from model output with innerHTML, to show
# what happens when output is trusted. Its own policy lets its inline script run but gives it no network at all. It is
# served only on its own port, which makes it a different origin from the console: the browser itself stops its script
# from touching the console page. The console embeds it in a frame that is also sandboxed.
WIDGET_CSP = ("default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; img-src data:; "
              "base-uri 'none'; form-action 'none'; "
              "frame-ancestors http://127.0.0.1:8300 http://localhost:8300")
PAGE_CSP = {"/widget.html": WIDGET_CSP}
TYPES = {".html": "text/html; charset=utf-8", ".css": "text/css; charset=utf-8", ".js": "text/javascript; charset=utf-8",
         ".svg": "image/svg+xml", ".json": "application/json", ".png": "image/png", ".ico": "image/x-icon"}


class ApiError(Exception):
    def __init__(self, status: int, message: str):
        super().__init__(message)
        self.status, self.message = status, message


class Jobs:
    """Runs slow work (several model calls) in a thread so the browser can poll its progress."""

    def __init__(self) -> None:
        self._jobs: dict[str, dict] = {}
        self._lock = threading.Lock()

    def start(self, work, kind: str) -> str:
        with self._lock:
            if any(j["kind"] == kind and not j["done"] for j in self._jobs.values()):
                raise ApiError(409, "That check is already running. Wait for it to finish.")
            job_id = uuid.uuid4().hex[:12]
            job = {"id": job_id, "kind": kind, "done": False, "error": None, "progress": []}
            self._jobs[job_id] = job

        def run() -> None:
            try:
                work(job)
            except ApiError as exc:
                job["error"] = exc.message
            except Exception as exc:  # shown to the learner, never crashes the server
                job["error"] = f"{type(exc).__name__}: {exc}"
            finally:
                job["done"] = True

        threading.Thread(target=run, daemon=True).start()
        return job_id

    def get(self, job_id: str) -> dict:
        job = self._jobs.get(job_id)
        if job is None:
            raise ApiError(404, "No such job.")
        return job


def host_port(header: str | None) -> int | None:
    tail = (header or "").rsplit(":", 1)[-1]
    return int(tail) if tail.isdigit() and not header.endswith("]") else None


def host_ok(header: str | None) -> bool:
    if not header:
        return False
    host = header.rsplit(":", 1)[0] if not header.endswith("]") and ":" in header else header
    return host.lower() in ALLOWED_HOSTS


def make_server(routes: dict, static_dir: str, port: int, bind: str = "0.0.0.0", max_body: int = MAX_BODY) -> ThreadingHTTPServer:
    root = pathlib.Path(static_dir).resolve()

    class Handler(BaseHTTPRequestHandler):
        server_version = "bdai-console"
        sys_version = ""

        def log_message(self, fmt, *args):  # keep the container log quiet
            pass

        def _send(self, status: int, body: bytes, content_type: str, csp: str = CSP) -> None:
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header("Content-Security-Policy", csp)
            self.end_headers()
            self.wfile.write(body)

        def _json(self, status: int, payload: dict) -> None:
            self._send(status, json.dumps(payload).encode(), "application/json")

        def _guard(self, post: bool) -> bool:
            if not host_ok(self.headers.get("Host")):
                self._json(403, {"error": "This console only answers on localhost."})
                return False
            if post:
                if (self.headers.get("Content-Type") or "").split(";")[0].strip().lower() != "application/json":
                    self._json(415, {"error": "Send JSON."})
                    return False
                origin = self.headers.get("Origin")
                if origin and urllib.parse.urlparse(origin).netloc != self.headers.get("Host"):
                    self._json(403, {"error": "Cross-site request refused."})
                    return False
            return True

        def _route(self, method: str) -> None:
            url = urllib.parse.urlparse(self.path)
            query = {k: v[0] for k, v in urllib.parse.parse_qs(url.query).items()}
            body: dict = {}
            if method == "POST":
                length = int(self.headers.get("Content-Length") or 0)
                if length > max_body:
                    return self._json(413, {"error": "That is too large."})
                try:
                    body = json.loads(self.rfile.read(length) or b"{}")
                    if not isinstance(body, dict):
                        raise ValueError
                except ValueError:
                    return self._json(400, {"error": "Invalid JSON."})
            handler = routes.get((method, url.path))
            if handler is None:
                return self._json(404, {"error": "Not found."})
            try:
                self._json(200, handler(body, query))
            except ApiError as exc:
                self._json(exc.status, {"error": exc.message})
            except Exception as exc:
                traceback.print_exc()
                self._json(500, {"error": f"{type(exc).__name__}: {exc}"})

        def do_GET(self) -> None:
            if not self._guard(post=False):
                return
            path = urllib.parse.urlparse(self.path).path
            on_widget_port = host_port(self.headers.get("Host")) == WIDGET_PORT
            if on_widget_port != (path == "/widget.html") and path != "/healthz":
                return self._json(404, {"error": "Not found."})  # widget.html only on its own origin, nothing else there
            if path.startswith("/api/") or path == "/healthz":
                return self._route("GET") if path != "/healthz" else self._json(200, {"ok": True})
            target = (root / ("index.html" if path in ("", "/") else path.lstrip("/"))).resolve()
            if not target.is_file() or root not in target.parents:
                return self._json(404, {"error": "Not found."})
            ctype = TYPES.get(target.suffix) or mimetypes.guess_type(target.name)[0] or "application/octet-stream"
            self._send(200, target.read_bytes(), ctype, PAGE_CSP.get("/" + target.relative_to(root).as_posix(), CSP))

        def do_POST(self) -> None:
            if self._guard(post=True):
                self._route("POST")

    return ThreadingHTTPServer((bind, port), Handler)


def serve(routes: dict, static_dir: str, port: int = 8080, max_body: int = MAX_BODY) -> None:
    make_server(routes, static_dir, port, max_body=max_body).serve_forever()
