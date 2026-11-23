"""TrailBot behind an OpenAI-compatible endpoint, so that a real scanner such as garak can attack the APPLICATION, not just a model.

    POST /v1/chat/completions   {"model": "trailbot-keyword", "messages": [...]}   ->  a normal chat completion

The model name picks the guardrail: trailbot-none, trailbot-keyword, trailbot-judge, trailbot-output, trailbot-architecture.
The last user message is the customer's question; TrailBot answers it exactly as it does in Lab 8.1, with that guardrail in front.
A reply a guardrail stopped comes back as the text "Sorry, I can't help with that." It runs only on the lab's internal network.
"""
import json
import os
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import guardrails
import trailbot

PORT = int(os.environ.get("SHIM_PORT", "8000"))
LOCK = threading.RLock()
MODELS = [f"trailbot-{name}" for name in guardrails.CONFIGS]


def records() -> list[dict]:
    with LOCK:
        trailbot.DATA.mkdir(parents=True, exist_ok=True)
        if not trailbot.INDEX.exists():
            trailbot.build_index()
        trailbot.get_secret()
    return json.loads(trailbot.INDEX.read_text(encoding="utf-8"))


def last_user_text(messages) -> str:
    for m in reversed(messages if isinstance(messages, list) else []):
        if isinstance(m, dict) and m.get("role") == "user":
            c = m.get("content")
            if isinstance(c, list):
                c = " ".join(p.get("text", "") for p in c if isinstance(p, dict))
            return c if isinstance(c, str) else ""
    return ""


def completion(model: str, messages) -> dict:
    config = model.removeprefix("trailbot-")
    if config not in guardrails.CONFIGS:
        raise ValueError(f"unknown model {model!r}; choose one of {', '.join(MODELS)}")
    question = last_user_text(messages).strip()[:2000]
    if not question:
        raise ValueError("no user message")
    out = guardrails.respond(question, records(), config)
    return {"id": f"trailbot-{int(time.time() * 1000)}", "object": "chat.completion", "created": int(time.time()), "model": model,
            "choices": [{"index": 0, "message": {"role": "assistant", "content": out["shown"]}, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}}


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *_):
        pass

    def _send(self, status: int, body: dict):
        data = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path.rstrip("/") in ("/v1", "/healthz"):
            return self._send(200, {"ok": True})
        if self.path == "/v1/models":
            return self._send(200, {"object": "list", "data": [{"id": m, "object": "model"} for m in MODELS]})
        self._send(404, {"error": "not found"})

    def do_POST(self):
        if self.path != "/v1/chat/completions":
            return self._send(404, {"error": "not found"})
        try:
            n = int(self.headers.get("Content-Length", "0"))
            if not 0 < n <= 1_000_000:
                raise ValueError("bad body size")
            body = json.loads(self.rfile.read(n))
            self._send(200, completion(str(body.get("model", "")), body.get("messages")))
        except (ValueError, TypeError, KeyError) as exc:
            self._send(400, {"error": {"message": str(exc), "type": "invalid_request_error"}})
        except Exception as exc:  # the model or the gateway failed: say so, do not crash the server
            self._send(502, {"error": {"message": f"{type(exc).__name__}: {exc}", "type": "upstream_error"}})


def main() -> None:
    server = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    server.daemon_threads = True
    print(f"TrailBot OpenAI-compatible endpoint on :{PORT} ({', '.join(MODELS)})", flush=True)
    threading.Thread(target=records, daemon=True).start()          # build the index in the background
    server.serve_forever()


if __name__ == "__main__":
    sys.exit(main())
