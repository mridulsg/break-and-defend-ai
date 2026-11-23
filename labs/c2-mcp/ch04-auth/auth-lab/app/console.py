"""The Acme console for Labs 4.1 and 4.2: MCP servers that check a bearer token, badly, and then properly.

Two servers need a token: notes (audience "notes") and tickets (audience "tickets"). An "auth server" mints tokens for Sam, a
read-only engineer. A token is three base64url parts, header.payload.signature, signed with HMAC-SHA256 (a small JWT).

As shipped, the servers make three mistakes. They accept a token issued for a different server (no audience check), they never
look at the scope when a tool changes something, and they accept a token whose header says it is not signed. The Fixes switch
turns on the checks the MCP specification asks for: signature, expiry, audience, scope, and a 401 or 403 that says why.
Run by the `console` service (see compose.yaml); open http://127.0.0.1:8300.
"""
import base64
import hashlib
import hmac
import json
import os
import sys
import time

sys.path.insert(0, os.environ.get("BDAI_MCP_DIR", "/mcp"))

import acme  # noqa: E402
import labkit  # noqa: E402
import mcpmini  # noqa: E402
import progress  # noqa: E402

ISSUER = "https://auth.acme.example"
SECRET = os.urandom(32)                      # the auth server's signing key: new on every start
DATA = acme.AcmeTickets()
SCOPES = {"get_ticket": "tickets:read", "list_tickets": "tickets:read", "add_comment": "tickets:write", "read_note": "notes:read", "list_notes": "notes:read"}


def b64(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()


def unb64(text: str) -> bytes:
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))


def mint(aud: str, scope: str, ttl: int = 3600) -> str:
    head = b64(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
    body = b64(json.dumps({"iss": ISSUER, "sub": "sam", "aud": aud, "scope": scope, "exp": int(time.time()) + ttl}).encode())
    sig = b64(hmac.new(SECRET, f"{head}.{body}".encode(), hashlib.sha256).digest())
    return f"{head}.{body}.{sig}"


def fixes() -> bool:
    return LAB.fixes_on()


def deny(status: int, error: str, resource: str, scope: str | None = None) -> mcpmini.McpError:
    h = f'Bearer error="{error}", resource_metadata="https://{resource}.acme.example/.well-known/oauth-protected-resource"'
    if scope:
        h += f', scope="{scope}"'
    return mcpmini.McpError(-32001, {401: "Unauthorized", 403: "Forbidden"}[status] + f": {error}", status, headers={"WWW-Authenticate": h})


def verify(headers: dict, resource: str) -> dict:
    auth = headers.get("authorization", "")
    if not auth.lower().startswith("bearer ") or auth.count(".") != 2:
        raise deny(401, "invalid_token", resource)
    head_s, body_s, sig_s = auth[7:].strip().split(".")
    try:
        head, claims = json.loads(unb64(head_s)), json.loads(unb64(body_s))
        assert isinstance(head, dict) and isinstance(claims, dict)
    except (ValueError, AssertionError):
        raise deny(401, "invalid_token", resource)
    unsigned = head.get("alg") == "none"
    good = hmac.compare_digest(unb64(sig_s) if sig_s else b"", hmac.new(SECRET, f"{head_s}.{body_s}".encode(), hashlib.sha256).digest())
    if fixes():
        if head.get("alg") != "HS256" or not good:
            raise deny(401, "invalid_token", resource)
    elif not good and not unsigned:               # flaw: "alg": "none" skips the signature check
        raise deny(401, "invalid_token", resource)
    if claims.get("exp", 0) < time.time():
        raise deny(401, "invalid_token", resource)
    if fixes():
        if claims.get("aud") != resource or claims.get("iss") != ISSUER:
            raise deny(401, "invalid_token", resource)
    else:                                         # flaw: the audience is never compared with this server
        if unsigned:
            progress.mark("forged", "The server accepted a token whose header says it is not signed. Anyone can write one.")
        if claims.get("aud") != resource:
            progress.mark("audience", f"The {resource} server accepted a token issued for {claims.get('aud')!r}.")
    return claims


def need(claims: dict, tool: str, resource: str) -> None:
    scope = SCOPES[tool]
    granted = str(claims.get("scope", "")).split()
    if fixes() and scope not in granted:
        raise deny(403, "insufficient_scope", resource, scope)
    if tool == "add_comment" and scope not in granted:
        progress.mark("scope", f"A token with scope {' '.join(granted)!r} changed a ticket. Nobody checked.")


def guarded(server: mcpmini.McpServer, resource: str) -> mcpmini.McpServer:
    server.authenticate = lambda h: verify(h, resource)
    for name, t in list(server.tools.items()):
        inner = t.fn
        t.fn = (lambda inner, name: lambda args, ctx: (need(ctx["claims"], name, resource), inner(args))[1])(inner, name)
    return server


def mint_route(body, _q) -> dict:
    aud, scope = body.get("aud"), body.get("scope", "")
    if aud not in ("notes", "tickets"):
        raise labkit.web.ApiError(400, "Choose an audience.")
    allowed = set(SCOPES.values())
    if not isinstance(scope, str) or len(scope) > 80 or not set(scope.split()) <= allowed:
        raise labkit.web.ApiError(400, "Scopes are words from: " + ", ".join(sorted(allowed)))
    return {"token": mint(aud, scope.strip())}


def watch(result: dict, question: str) -> dict:
    return {"alerts": [], "rows": [{"label": "Fixes", "value": "on" if fixes() else "off", "bad": not fixes()}]}


SERVERS = {"notes": ("Acme notes", guarded(acme.build_notes(), "notes")), "tickets": ("Acme tickets", guarded(acme.build_tickets(DATA), "tickets"))}

LAB = labkit.Lab(
    product="Acme Auth Console", lab="Labs 4.1 and 4.2: MCP authentication and authorization",
    intro="Both servers now need a bearer token. Use the Tool tester: mint a token for Sam, then call a server. Sam is a read-only engineer.",
    suggestions=[], views=["servers", "tester", "missions"], fixes=True, mint={"audiences": ["notes", "tickets"]},
    viewer_token=lambda sid: mint(sid, "notes:read tickets:read"),
    missions_lede="Three mistakes in how the servers check tokens. Each is detected when the server wrongly says yes.",
    missions=[
        {"id": "audience", "kind": "auto", "title": "Use a token on a server it was not issued for",
         "text": "Mint a token for the notes server, then use it to call a tool on the tickets server.",
         "hint": "A token should say who it is for (aud). Does the tickets server compare that with itself?"},
        {"id": "scope", "kind": "auto", "title": "Change a ticket with a read-only token",
         "text": "Mint a token for tickets with only the scope tickets:read, and call add_comment with it.",
         "hint": "The tool list says add_comment changes the ticket. Does the server look at the scope before it runs?"},
        {"id": "forged", "kind": "auto", "title": "Write a token nobody signed",
         "text": "Build a token yourself that the server accepts without a valid signature.",
         "hint": "Decode the first part of a minted token (base64url). What does alg say? What if it said none, and the signature part were empty?"},
    ],
    flag_next="Next: Lab 4.2 shows the checks. Turn on Fixes and repeat each attack.",
    progress=progress, servers=SERVERS, watch=watch,
)

if __name__ == "__main__":
    LAB.run({("POST", "/api/token"): mint_route})
