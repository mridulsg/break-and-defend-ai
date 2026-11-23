"""mcpmini: a very small Model Context Protocol implementation (tools only), written so you can read every byte.

It follows the wire format of the 2026-07-28 MCP specification for the parts the labs use:

  * ONE http endpoint, POST only. Every message is its own request. There is no handshake and no session.
  * Request headers:  Content-Type: application/json, Accept: application/json, text/event-stream,
                      MCP-Protocol-Version: 2026-07-28, Mcp-Method: <the method>, and Mcp-Name: <tool> for tools/call.
  * Every request body carries `params._meta` with the protocol version and the client's capabilities.
  * Methods: server/discover, tools/list, tools/call. A notification (no id) is answered 202 with no body.
  * Errors: -32020 header mismatch (400), -32022 unsupported version (400), -32602 invalid params (400), -32601 unknown method (404).
  * The server validates the Origin header (403 when it is present and not allowed), which is the defence against DNS rebinding.

Real projects should use an official SDK. This file leaves out everything the labs do not need (resources, prompts, streaming,
subscriptions) so that the protocol itself is the thing you study. The labs add their own, deliberately weak, behaviour on top.
"""
import inspect
import json
import threading
import time
import urllib.error
import urllib.request
from collections import deque
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PROTOCOL_VERSION = "2026-07-28"
M_VERSION = "io.modelcontextprotocol/protocolVersion"
M_CAPS = "io.modelcontextprotocol/clientCapabilities"
M_CLIENT = "io.modelcontextprotocol/clientInfo"
M_SERVER = "io.modelcontextprotocol/serverInfo"
MAX_BODY = 256 * 1024

HEADER_MISMATCH, UNSUPPORTED_VERSION, INVALID_PARAMS, METHOD_NOT_FOUND, PARSE_ERROR, INVALID_REQUEST = -32020, -32022, -32602, -32601, -32700, -32600


class McpError(Exception):
    def __init__(self, code: int, message: str, status: int = 400, data=None, headers: dict | None = None):
        super().__init__(message)
        self.code, self.message, self.status, self.data, self.headers = code, message, status, data, headers or {}


def error_body(rid, code: int, message: str, data=None) -> dict:
    err = {"code": code, "message": message}
    if data is not None:
        err["data"] = data
    return {"jsonrpc": "2.0", "id": rid, "error": err}


def _check_type(value, schema_type) -> bool:
    return {"string": isinstance(value, str), "integer": isinstance(value, int) and not isinstance(value, bool),
            "number": isinstance(value, (int, float)) and not isinstance(value, bool), "boolean": isinstance(value, bool),
            "object": isinstance(value, dict), "array": isinstance(value, list)}.get(schema_type, True)


def validate_arguments(schema: dict, args) -> str | None:
    """A small subset of JSON Schema: object, required, and primitive property types. Returns a message or None."""
    if not isinstance(args, dict):
        return "arguments must be an object"
    for key in schema.get("required", []):
        if key not in args:
            return f"missing required argument: {key}"
    for key, spec in schema.get("properties", {}).items():
        if key in args and not _check_type(args[key], spec.get("type")):
            return f"argument {key} must be of type {spec.get('type')}"
    if schema.get("additionalProperties") is False:
        extra = set(args) - set(schema.get("properties", {}))
        if extra:
            return "unexpected argument: " + sorted(extra)[0]
    return None


class Tool:
    def __init__(self, name, description, schema, fn, title=None, annotations=None):
        self.name, self.description, self.schema, self.fn, self.title, self.annotations = name, description, schema, fn, title, annotations

    def listing(self) -> dict:
        out = {"name": self.name, "description": self.description, "inputSchema": self.schema}
        if self.title:
            out["title"] = self.title
        if self.annotations:
            out["annotations"] = self.annotations
        return out


class McpServer:
    """A server with tools. `handle()` is a plain function (headers, body in; status, body out) so it is easy to test."""

    def __init__(self, name: str, version: str = "1.0.0", instructions: str = "", ttl_ms: int = 300000,
                 allowed_origins=("http://localhost", "http://127.0.0.1", "http://[::1]"), authenticate=None):
        self.name, self.version, self.instructions, self.ttl_ms = name, version, instructions, ttl_ms
        self.allowed_origins = tuple(allowed_origins)
        self.authenticate = authenticate          # optional: fn(headers) -> claims dict, or raises McpError(401/403)
        self.tools: dict[str, Tool] = {}
        self.log: deque = deque(maxlen=200)       # what this server saw, for the lab consoles
        self.lock = threading.RLock()

    # ------------------------------------------------------------ registering tools
    def tool(self, name, description, schema=None, title=None, annotations=None):
        def deco(fn):
            self.tools[name] = Tool(name, description, schema or {"type": "object", "additionalProperties": False}, fn, title, annotations)
            return fn
        return deco

    def set_description(self, name: str, text: str) -> None:
        with self.lock:
            self.tools[name].description = text

    # ------------------------------------------------------------ one request
    def origin_ok(self, origin: str | None) -> bool:
        if origin is None:
            return True
        return any(origin == a or origin.startswith(a + ":") for a in self.allowed_origins)

    def handle(self, headers: dict, body: bytes) -> tuple[int, dict | None, dict]:
        """Returns (http status, json body or None, extra response headers)."""
        h = {k.lower(): v for k, v in headers.items()}
        rid = None
        try:
            if not self.origin_ok(h.get("origin")):
                raise McpError(INVALID_REQUEST, "Origin not allowed", 403)
            try:
                msg = json.loads(body.decode("utf-8"))
            except (ValueError, UnicodeDecodeError):
                raise McpError(PARSE_ERROR, "Body is not valid JSON")
            if not isinstance(msg, dict) or msg.get("jsonrpc") != "2.0" or not isinstance(msg.get("method"), str):
                raise McpError(INVALID_REQUEST, "Not a JSON-RPC 2.0 request")
            rid = msg.get("id")
            method, params = msg["method"], msg.get("params") or {}
            if not isinstance(params, dict):
                raise McpError(INVALID_PARAMS, "params must be an object")
            meta = params.get("_meta")
            if not isinstance(meta, dict) or M_VERSION not in meta or M_CAPS not in meta:
                raise McpError(INVALID_PARAMS, f"_meta must carry {M_VERSION} and {M_CAPS}")
            if h.get("mcp-protocol-version") != meta[M_VERSION]:
                raise McpError(HEADER_MISMATCH, f"Header mismatch: MCP-Protocol-Version {h.get('mcp-protocol-version')!r} does not match _meta {meta[M_VERSION]!r}")
            if meta[M_VERSION] != PROTOCOL_VERSION:
                raise McpError(UNSUPPORTED_VERSION, "Unsupported protocol version", data={"supported": [PROTOCOL_VERSION], "requested": meta[M_VERSION]})
            if h.get("mcp-method") != method:
                raise McpError(HEADER_MISMATCH, f"Header mismatch: Mcp-Method {h.get('mcp-method')!r} does not match method {method!r}")
            if method == "tools/call" and h.get("mcp-name") != params.get("name"):
                raise McpError(HEADER_MISMATCH, f"Header mismatch: Mcp-Name {h.get('mcp-name')!r} does not match body {params.get('name')!r}")
            claims = self.authenticate(h) if self.authenticate else {}
            if rid is None:                       # a notification
                return 202, None, {}
            result = self.dispatch(method, params, claims, h)
            self.log.append({"t": time.time(), "method": method, "name": params.get("name"), "ok": True})
            return 200, {"jsonrpc": "2.0", "id": rid, "result": result}, {}
        except McpError as exc:
            self.log.append({"t": time.time(), "method": locals().get("method"), "ok": False, "error": exc.message})
            extra = exc.headers
            return exc.status, error_body(rid, exc.code, exc.message, exc.data), extra

    def dispatch(self, method: str, params: dict, claims: dict, headers: dict) -> dict:
        if method == "server/discover":
            return {"resultType": "complete", "supportedVersions": [PROTOCOL_VERSION], "capabilities": {"tools": {}},
                    "_meta": {M_SERVER: {"name": self.name, "version": self.version}},
                    "instructions": self.instructions, "ttlMs": self.ttl_ms, "cacheScope": "public"}
        if method == "tools/list":
            with self.lock:
                tools = [t.listing() for t in self.tools.values()]
            return {"resultType": "complete", "tools": tools, "ttlMs": self.ttl_ms, "cacheScope": "public"}
        if method == "tools/call":
            tool = self.tools.get(params.get("name"))
            if tool is None:
                raise McpError(INVALID_PARAMS, f"Unknown tool: {params.get('name')}")
            args = params.get("arguments", {})
            problem = validate_arguments(tool.schema, args)
            if problem:
                raise McpError(INVALID_PARAMS, problem)
            try:
                wants_ctx = len(inspect.signature(tool.fn).parameters) > 1
                out = tool.fn(args, {"claims": claims, "headers": headers}) if wants_ctx else tool.fn(args)
                return {"resultType": "complete", "content": [{"type": "text", "text": out if isinstance(out, str) else json.dumps(out)}], "isError": False}
            except McpError:
                raise
            except Exception as exc:              # a tool failing is a result, not a protocol error
                return {"resultType": "complete", "content": [{"type": "text", "text": f"{type(exc).__name__}: {exc}"}], "isError": True}
        raise McpError(METHOD_NOT_FOUND, f"Unknown method: {method}", 404)

    # ------------------------------------------------------------ http
    def serve(self, host: str = "127.0.0.1", port: int = 0, path: str = "/mcp") -> ThreadingHTTPServer:
        server = self

        class Handler(BaseHTTPRequestHandler):
            protocol_version = "HTTP/1.1"

            def log_message(self, *_):
                pass

            def _send(self, status, body, extra=None):
                data = json.dumps(body).encode() if body is not None else b""
                self.send_response(status)
                if body is not None:
                    self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(data)))
                for k, v in (extra or {}).items():
                    self.send_header(k, v)
                self.end_headers()
                self.wfile.write(data)

            def do_POST(self):
                if self.path != path:
                    return self._send(404, {"error": "not found"})
                try:
                    n = int(self.headers.get("Content-Length", "0"))
                except ValueError:
                    n = -1
                if not 0 <= n <= MAX_BODY:
                    return self._send(400, error_body(None, INVALID_REQUEST, "Bad Content-Length"))
                status, body, extra = server.handle(dict(self.headers.items()), self.rfile.read(n))
                self._send(status, body, extra)

            def _no(self):
                self._send(405, None, {"Allow": "POST"})

            do_GET = do_DELETE = do_PUT = _no

        httpd = ThreadingHTTPServer((host, port), Handler)
        httpd.daemon_threads = True
        threading.Thread(target=httpd.serve_forever, daemon=True).start()
        return httpd


class McpClient:
    """The client half: sends the headers and _meta the specification asks for."""

    def __init__(self, url: str, name: str = "AcmeHost", token: str | None = None, timeout: float = 20.0):
        self.url, self.client_name, self.token, self.timeout = url, name, token, timeout
        self._id = 0
        self.last = None                          # the last request, headers and response, for the labs' traffic view

    def request(self, method: str, params: dict | None = None, extra_headers: dict | None = None) -> dict:
        self._id += 1
        params = dict(params or {})
        params["_meta"] = {M_VERSION: PROTOCOL_VERSION, M_CLIENT: {"name": self.client_name, "version": "1.0"}, M_CAPS: {}}
        body = {"jsonrpc": "2.0", "id": self._id, "method": method, "params": params}
        headers = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream",
                   "MCP-Protocol-Version": PROTOCOL_VERSION, "Mcp-Method": method}
        if method == "tools/call":
            headers["Mcp-Name"] = params.get("name", "")
        if self.token:
            headers["Authorization"] = "Bearer " + self.token
        headers.update(extra_headers or {})
        req = urllib.request.Request(self.url, data=json.dumps(body).encode(), headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                status, raw = resp.status, resp.read()
        except urllib.error.HTTPError as exc:
            status, raw = exc.code, exc.read()
            self._record(body, status, raw, headers)
            try:
                err = json.loads(raw.decode())["error"]
                raise McpError(err["code"], err["message"], status, err.get("data")) from None
            except (ValueError, KeyError, TypeError):
                raise McpError(-32603, f"HTTP {status}", status) from None
        self._record(body, status, raw, headers)
        reply = json.loads(raw.decode()) if raw else {}
        if "error" in reply:
            raise McpError(reply["error"]["code"], reply["error"]["message"], status, reply["error"].get("data"))
        return reply["result"]

    def _record(self, body, status, raw, headers):
        shown = {k: ("Bearer ***" if k.lower() == "authorization" else v) for k, v in headers.items()}
        self.last = {"request": body, "headers": shown, "status": status, "response": raw.decode("utf-8", "replace")[:4000]}

    def discover(self) -> dict:
        return self.request("server/discover")

    def list_tools(self) -> list[dict]:
        return self.request("tools/list")["tools"]

    def call(self, name: str, arguments: dict | None = None) -> dict:
        return self.request("tools/call", {"name": name, "arguments": arguments or {}})
