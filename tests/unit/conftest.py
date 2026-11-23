"""Shared fixtures: a fake model provider and a loader that builds a fresh gateway per test."""
import importlib.util
import itertools
import os
import pathlib
import socket
import threading
import time

import pytest
import uvicorn
from starlette.applications import Starlette
from starlette.responses import JSONResponse, StreamingResponse
from starlette.routing import Route
from starlette.testclient import TestClient

REPO = pathlib.Path(os.environ.get("BDAI_REPO", "/repo"))
GATEWAY_APP = REPO / "shared" / "core" / "gateway" / "app.py"
GATEWAY_KEY = "test-gateway-key-0123456789abcdef"
PROVIDER_KEY = "fake-provider-key-do-not-leak"


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class FakeUpstream:
    """Stands in for OpenRouter and Ollama. Records every request it receives."""

    def __init__(self) -> None:
        self.calls: list[dict] = []
        self.mode = "ok"  # ok | nocost | rate_limited

    def reset(self) -> None:
        self.calls.clear()
        self.mode = "ok"

    async def chat(self, request):
        body = await request.json()
        self.calls.append({"path": "/chat/completions", "headers": dict(request.headers), "body": body})
        if self.mode == "rate_limited":
            return JSONResponse({"error": {"message": "slow down"}}, status_code=429)
        if body.get("stream"):
            async def gen():
                yield b'data: {"choices":[{"delta":{"content":"Hel"}}]}\n\n'
                yield b'data: {"choices":[{"delta":{"content":"lo"}}]}\n\n'
                yield b'data: {"choices":[],"usage":{"prompt_tokens":10,"completion_tokens":2,"cost":0.0004}}\n\n'
                yield b"data: [DONE]\n\n"
            return StreamingResponse(gen(), media_type="text/event-stream")
        usage = {"prompt_tokens": 1000, "completion_tokens": 500}
        if self.mode != "nocost":
            usage["cost"] = 0.00123
        if self.mode == "negative_cost":
            usage["cost"] = -5.0
        if self.mode == "garbage_cost":
            usage = {"prompt_tokens": "abc", "completion_tokens": None, "cost": "NaN"}
        if self.mode == "usage_not_a_dict":
            usage = ["not", "a", "dict"]
        if self.mode == "huge_cost":
            usage["cost"] = "1e999"
        return JSONResponse({"choices": [{"message": {"role": "assistant", "content": "hi"}}], "usage": usage})

    async def embeddings(self, request):
        body = await request.json()
        self.calls.append({"path": "/embeddings", "headers": dict(request.headers), "body": body})
        return JSONResponse({"data": [{"embedding": [0.1, 0.2, 0.3]}], "usage": {"prompt_tokens": 3, "total_tokens": 3}})


@pytest.fixture(scope="session")
def upstream_server():
    fake = FakeUpstream()
    app = Starlette(routes=[
        Route("/chat/completions", fake.chat, methods=["POST"]),
        Route("/embeddings", fake.embeddings, methods=["POST"]),
    ])
    port = free_port()
    server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port, log_level="error"))
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    for _ in range(100):
        if server.started:
            break
        time.sleep(0.05)
    fake.base_url = f"http://127.0.0.1:{port}"
    yield fake
    server.should_exit = True
    thread.join(timeout=5)


@pytest.fixture()
def upstream(upstream_server):
    upstream_server.reset()
    return upstream_server


_counter = itertools.count()


@pytest.fixture()
def make_gateway(tmp_path, upstream):
    """Returns a factory: make_gateway(budget=..., max_tokens=..., key=...) -> (module, client)."""
    def factory(budget="1.0", max_tokens="4096", key=GATEWAY_KEY, provider_key=PROVIDER_KEY, base=None):
        os.environ.update({
            "BDAI_GATEWAY_KEY": key,
            "OPENROUTER_API_KEY": provider_key,
            "OPENROUTER_BASE_URL": base or upstream.base_url,
            "OLLAMA_BASE_URL": base or upstream.base_url,
            "BDAI_MAX_BUDGET_USD": budget,
            "BDAI_MAX_TOKENS": max_tokens,
            "BDAI_DB_PATH": str(tmp_path / f"ledger-{next(_counter)}.db"),
        })
        spec = importlib.util.spec_from_file_location(f"gateway_under_test_{next(_counter)}", GATEWAY_APP)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module, TestClient(module.app)
    return factory


@pytest.fixture()
def gw(make_gateway):
    module, client = make_gateway()
    client.headers.update({"Authorization": f"Bearer {GATEWAY_KEY}"})
    return module, client


def chat_body(**overrides):
    body = {"model": "bdai-default", "messages": [{"role": "user", "content": "hi"}]}
    body.update(overrides)
    return body
