"""Break & Defend AI model gateway.

A deliberately small OpenAI-compatible proxy that sits between lab containers and
the model provider. It exists so that:

  * lab containers never see the provider API key (only a local gateway key),
  * every call is metered and a hard spend cap stops runaway cost,
  * labs address models by stable aliases ("bdai-default") instead of provider IDs.

It stores usage metadata only (alias, token counts, cost). It never logs or stores
prompts or responses.
"""
import hmac
import json
import logging
import math
import os
import sqlite3
import threading
import time

import httpx
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse, Response, StreamingResponse
from starlette.routing import Route

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
log = logging.getLogger("bdai-gateway")

GATEWAY_KEY = os.environ.get("BDAI_GATEWAY_KEY", "")
OPENROUTER_KEY = os.environ.get("OPENROUTER_API_KEY", "")
OPENROUTER_BASE = os.environ.get("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
OLLAMA_BASE = os.environ.get("OLLAMA_BASE_URL", "http://bdai-ollama:11434/v1")
MAX_BUDGET_USD = float(os.environ.get("BDAI_MAX_BUDGET_USD", "5"))
MAX_TOKENS = int(os.environ.get("BDAI_MAX_TOKENS", "4096"))
MAX_BODY_BYTES = 1_000_000
DB_PATH = os.environ.get("BDAI_DB_PATH", "/data/ledger.db")

if len(GATEWAY_KEY) < 16:
    raise SystemExit("BDAI_GATEWAY_KEY is missing or too short (run shared/scripts/setup.sh)")

with open(os.path.join(os.path.dirname(__file__), "models.json"), encoding="utf-8") as fh:
    MODELS: dict = json.load(fh)

_db_lock = threading.Lock()
_db = sqlite3.connect(DB_PATH, check_same_thread=False)
_db.execute(
    "CREATE TABLE IF NOT EXISTS usage ("
    "ts REAL, alias TEXT, model TEXT, lab TEXT, prompt_tokens INTEGER, "
    "completion_tokens INTEGER, cost_usd REAL, cost_source TEXT)"
)
_db.commit()


def spent_usd() -> float:
    with _db_lock:
        row = _db.execute("SELECT COALESCE(SUM(cost_usd), 0) FROM usage").fetchone()
    return float(row[0])


def _as_int(value) -> int:
    """Provider-supplied token counts are untrusted input: anything odd counts as zero."""
    try:
        return max(int(value), 0)
    except (TypeError, ValueError, OverflowError):
        return 0


def _as_cost(value) -> float | None:
    """A provider-reported cost is only believed if it is a finite, non-negative number."""
    try:
        cost = float(value)
    except (TypeError, ValueError):
        return None
    return cost if math.isfinite(cost) and cost >= 0 else None


def record(alias: str, model: str, lab: str, usage: dict | None, entry: dict) -> float:
    usage = usage if isinstance(usage, dict) else {}
    pt = _as_int(usage.get("prompt_tokens"))
    ct = _as_int(usage.get("completion_tokens"))
    if entry.get("provider") == "ollama":
        # Local models are free. Never believe a cost figure from an endpoint we do not pay.
        cost, source = 0.0, "local"
    else:
        cost, source = _as_cost(usage.get("cost")), "provider"
        if cost is None:
            # Fall back to the per-million prices in models.json.
            cost = (pt * entry.get("price_in", 0) + ct * entry.get("price_out", 0)) / 1_000_000
            source = "estimated"
    with _db_lock:
        _db.execute(
            "INSERT INTO usage VALUES (?,?,?,?,?,?,?,?)",
            (time.time(), alias, model, lab, pt, ct, float(cost), source),
        )
        _db.commit()
    return float(cost)


def authorized(request: Request) -> bool:
    header = request.headers.get("authorization", "")
    token = header[7:] if header.lower().startswith("bearer ") else ""
    return hmac.compare_digest(token.encode(), GATEWAY_KEY.encode())


def error(status: int, message: str, code: str) -> JSONResponse:
    return JSONResponse({"error": {"message": message, "type": code, "code": code}}, status_code=status)


def unreachable(entry: dict, exc: Exception) -> JSONResponse:
    if entry.get("provider") == "ollama":
        message = (
            f"The local model server is unreachable from the gateway ({type(exc).__name__}). "
            "Check that it is running, then see the lab's troubleshooting table."
        )
    else:
        message = f"upstream unreachable: {type(exc).__name__}"
    return error(502, message, "upstream_error")


async def healthz(_: Request) -> Response:
    return JSONResponse({"ok": True})


async def list_models(request: Request) -> Response:
    if not authorized(request):
        return error(401, "invalid gateway key", "unauthorized")
    data = [
        {"id": a, "object": "model", "owned_by": e["provider"]}
        for a, e in MODELS.items()
        if not e.get("hidden")  # hidden aliases (benchmarks) stay routable but unlisted
    ]
    return JSONResponse({"object": "list", "data": data})


async def usage(request: Request) -> Response:
    if not authorized(request):
        return error(401, "invalid gateway key", "unauthorized")
    with _db_lock:
        totals = _db.execute(
            "SELECT COUNT(*), COALESCE(SUM(prompt_tokens),0), COALESCE(SUM(completion_tokens),0), "
            "COALESCE(SUM(cost_usd),0) FROM usage"
        ).fetchone()
        by_alias = _db.execute(
            "SELECT alias, COUNT(*), COALESCE(SUM(prompt_tokens),0), COALESCE(SUM(completion_tokens),0), "
            "COALESCE(SUM(cost_usd),0) FROM usage GROUP BY alias"
        ).fetchall()
    return JSONResponse(
        {
            "budget_usd": MAX_BUDGET_USD,
            "spent_usd": round(totals[3], 6),
            "remaining_usd": round(max(MAX_BUDGET_USD - totals[3], 0), 6),
            "requests": totals[0],
            "prompt_tokens": totals[1],
            "completion_tokens": totals[2],
            "by_alias": {
                r[0]: {"requests": r[1], "prompt_tokens": r[2], "completion_tokens": r[3], "cost_usd": round(r[4], 6)}
                for r in by_alias
            },
        }
    )


async def chat_completions(request: Request) -> Response:
    if not authorized(request):
        return error(401, "invalid gateway key", "unauthorized")
    raw = await request.body()
    if len(raw) > MAX_BODY_BYTES:
        return error(413, "request body too large", "payload_too_large")
    try:
        data = json.loads(raw)
    except ValueError:
        return error(400, "body is not valid JSON", "bad_request")

    alias = data.get("model")
    entry = MODELS.get(alias)
    if entry is None:
        return error(400, f"unknown model alias {alias!r}; see GET /v1/models", "unknown_model")
    if entry.get("kind") == "embedding":
        return error(400, f"{alias!r} is an embedding model; use POST /v1/embeddings", "wrong_endpoint")
    if spent_usd() >= MAX_BUDGET_USD:
        return error(
            429,
            f"BDAI spend cap of ${MAX_BUDGET_USD:.2f} reached. Raise BDAI_MAX_BUDGET_USD in .env to continue.",
            "budget_exceeded",
        )

    lab = request.headers.get("x-bdai-lab", "unlabelled")[:64]
    provider_model = entry["model"]
    data["model"] = provider_model
    for key, value in entry.get("defaults", {}).items():
        data.setdefault(key, value)  # per-alias defaults; anything the client sets explicitly wins
    for field in ("max_tokens", "max_completion_tokens"):
        if field in data and isinstance(data[field], int) and data[field] > MAX_TOKENS:
            data[field] = MAX_TOKENS
    if "max_tokens" not in data and "max_completion_tokens" not in data:
        data["max_tokens"] = MAX_TOKENS

    headers = {"content-type": "application/json"}
    if entry["provider"] == "openrouter":
        if not OPENROUTER_KEY:
            return error(500, "OPENROUTER_API_KEY is not configured on the gateway", "not_configured")
        base = OPENROUTER_BASE
        headers["authorization"] = f"Bearer {OPENROUTER_KEY}"
        headers["x-title"] = "Break & Defend AI labs"
        data["usage"] = {"include": True}  # ask OpenRouter to return the real cost
    elif entry["provider"] == "ollama":
        base = OLLAMA_BASE
    else:
        return error(500, "bad provider in models.json", "not_configured")
    streaming = bool(data.get("stream"))
    if streaming:
        data.setdefault("stream_options", {})["include_usage"] = True

    started = time.time()
    client = httpx.AsyncClient(timeout=httpx.Timeout(120.0, connect=10.0))
    try:
        upstream_req = client.build_request("POST", f"{base}/chat/completions", json=data, headers=headers)
        upstream = await client.send(upstream_req, stream=True)
    except httpx.HTTPError as exc:
        await client.aclose()
        return unreachable(entry, exc)

    ctype = upstream.headers.get("content-type", "application/json")

    if upstream.status_code != 200 or not streaming:
        body = await upstream.aread()
        await upstream.aclose()
        await client.aclose()
        used = None
        if upstream.status_code == 200:
            try:
                used = json.loads(body).get("usage")
            except ValueError:
                pass
            cost = record(alias, provider_model, lab, used, entry)
        else:
            cost = 0.0
        log.info("alias=%s lab=%s status=%s cost=$%.6f ms=%d", alias, lab, upstream.status_code, cost,
                 (time.time() - started) * 1000)
        return Response(body, status_code=upstream.status_code, media_type=ctype.split(";")[0])

    async def relay():
        last_usage = None
        buf = b""
        try:
            async for chunk in upstream.aiter_raw():
                buf += chunk
                while b"\n" in buf:
                    line, buf = buf.split(b"\n", 1)
                    if line.startswith(b"data: ") and line[6:].strip() != b"[DONE]":
                        try:
                            obj = json.loads(line[6:])
                            if obj.get("usage"):
                                last_usage = obj["usage"]
                        except ValueError:
                            pass
                yield chunk
        finally:
            await upstream.aclose()
            await client.aclose()
            cost = record(alias, provider_model, lab, last_usage, entry)
            log.info("alias=%s lab=%s status=200 stream=1 cost=$%.6f ms=%d", alias, lab, cost,
                     (time.time() - started) * 1000)

    return StreamingResponse(relay(), media_type="text/event-stream")


async def embeddings(request: Request) -> Response:
    if not authorized(request):
        return error(401, "invalid gateway key", "unauthorized")
    raw = await request.body()
    if len(raw) > MAX_BODY_BYTES:
        return error(413, "request body too large", "payload_too_large")
    try:
        data = json.loads(raw)
    except ValueError:
        return error(400, "body is not valid JSON", "bad_request")

    alias = data.get("model")
    entry = MODELS.get(alias)
    if entry is None or entry.get("kind") != "embedding":
        return error(400, f"{alias!r} is not an embedding alias; see GET /v1/models", "unknown_model")
    if spent_usd() >= MAX_BUDGET_USD:
        return error(429, f"BDAI spend cap of ${MAX_BUDGET_USD:.2f} reached.", "budget_exceeded")

    lab = request.headers.get("x-bdai-lab", "unlabelled")[:64]
    data["model"] = entry["model"]
    headers = {"content-type": "application/json"}
    if entry["provider"] == "openrouter":
        if not OPENROUTER_KEY:
            return error(500, "OPENROUTER_API_KEY is not configured on the gateway", "not_configured")
        base = OPENROUTER_BASE
        headers["authorization"] = f"Bearer {OPENROUTER_KEY}"
    else:
        base = OLLAMA_BASE

    started = time.time()
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(120.0, connect=10.0)) as client:
            upstream = await client.post(f"{base}/embeddings", json=data, headers=headers)
    except httpx.HTTPError as exc:
        return unreachable(entry, exc)

    cost = 0.0
    if upstream.status_code == 200:
        try:
            used = upstream.json().get("usage")
        except ValueError:
            used = None
        cost = record(alias, entry["model"], lab, used, entry)
    log.info("alias=%s lab=%s status=%s kind=embedding cost=$%.6f ms=%d", alias, lab, upstream.status_code,
             cost, (time.time() - started) * 1000)
    return Response(upstream.content, status_code=upstream.status_code, media_type="application/json")


app = Starlette(
    routes=[
        Route("/healthz", healthz),
        Route("/v1/models", list_models),
        Route("/v1/usage", usage),
        Route("/v1/chat/completions", chat_completions, methods=["POST"]),
        Route("/v1/embeddings", embeddings, methods=["POST"]),
    ]
)
