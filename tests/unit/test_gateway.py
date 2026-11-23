"""Unit tests for the model gateway (shared/core/gateway/app.py)."""
import json
import time

import pytest

from conftest import GATEWAY_KEY, PROVIDER_KEY, chat_body


# ---------- authentication ----------

def test_healthz_needs_no_auth(make_gateway):
    _, client = make_gateway()
    assert client.get("/healthz").json() == {"ok": True}


@pytest.mark.parametrize("headers", [{}, {"Authorization": "Bearer wrong"}, {"Authorization": "Basic abc"},
                                     {"Authorization": GATEWAY_KEY}, {"Authorization": "Bearer "}])
@pytest.mark.parametrize("method,path", [("get", "/v1/models"), ("get", "/v1/usage"),
                                         ("post", "/v1/chat/completions"), ("post", "/v1/embeddings")])
def test_protected_routes_reject_bad_auth(make_gateway, upstream, method, path, headers):
    _, client = make_gateway()
    r = getattr(client, method)(path, headers=headers, **({"json": chat_body()} if method == "post" else {}))
    assert r.status_code == 401
    assert upstream.calls == []  # nothing was forwarded


def test_gateway_refuses_to_start_with_short_key(make_gateway):
    with pytest.raises(SystemExit):
        make_gateway(key="short")


# ---------- model listing ----------

def test_models_lists_visible_aliases_only(gw):
    _, client = gw
    ids = [m["id"] for m in client.get("/v1/models").json()["data"]]
    assert "bdai-default" in ids and "bdai-victim" in ids and "bdai-embed" in ids
    assert not any(i.startswith("bench-") for i in ids), "hidden benchmark aliases must not be listed"


def test_hidden_alias_is_still_routable(gw, upstream):
    _, client = gw
    r = client.post("/v1/chat/completions", json=chat_body(model="bench-haiku"))
    assert r.status_code == 200
    assert upstream.calls[0]["body"]["model"] == "anthropic/claude-haiku-5.5"


# ---------- request validation ----------

def test_unknown_alias_rejected(gw, upstream):
    _, client = gw
    r = client.post("/v1/chat/completions", json=chat_body(model="gpt-4o"))
    assert r.status_code == 400 and r.json()["error"]["code"] == "unknown_model"
    assert upstream.calls == []


def test_raw_provider_model_id_is_not_accepted(gw, upstream):
    """Labs must use aliases. A raw provider id would bypass the allow-list and the price table."""
    _, client = gw
    r = client.post("/v1/chat/completions", json=chat_body(model="anthropic/claude-opus-5.5"))
    assert r.status_code == 400 and upstream.calls == []


def test_embedding_alias_rejected_on_chat_endpoint(gw, upstream):
    _, client = gw
    r = client.post("/v1/chat/completions", json=chat_body(model="bdai-embed"))
    assert r.status_code == 400 and r.json()["error"]["code"] == "wrong_endpoint"
    assert upstream.calls == []


def test_chat_alias_rejected_on_embeddings_endpoint(gw, upstream):
    _, client = gw
    r = client.post("/v1/embeddings", json={"model": "bdai-default", "input": ["x"]})
    assert r.status_code == 400 and upstream.calls == []


def test_invalid_json_rejected(gw):
    _, client = gw
    r = client.post("/v1/chat/completions", content=b"{not json", headers={"content-type": "application/json"})
    assert r.status_code == 400


def test_oversized_body_rejected(gw, upstream):
    _, client = gw
    big = chat_body(messages=[{"role": "user", "content": "x" * 1_100_000}])
    r = client.post("/v1/chat/completions", json=big)
    assert r.status_code == 413 and upstream.calls == []


# ---------- what gets forwarded ----------

def test_provider_key_is_injected_and_client_credentials_are_not_forwarded(gw, upstream):
    _, client = gw
    client.post("/v1/chat/completions", json=chat_body(),
                headers={"Authorization": f"Bearer {GATEWAY_KEY}", "X-Evil": "1", "Cookie": "a=b"})
    sent = upstream.calls[0]["headers"]
    assert sent["authorization"] == f"Bearer {PROVIDER_KEY}"
    assert GATEWAY_KEY not in json.dumps(sent)
    assert "x-evil" not in sent and "cookie" not in sent


def test_alias_is_mapped_to_provider_model(gw, upstream):
    _, client = gw
    client.post("/v1/chat/completions", json=chat_body(model="bdai-default"))
    assert upstream.calls[0]["body"]["model"] == "anthropic/claude-haiku-5.5"


def test_usage_cost_is_requested_from_openrouter(gw, upstream):
    _, client = gw
    client.post("/v1/chat/completions", json=chat_body())
    assert upstream.calls[0]["body"]["usage"] == {"include": True}


def test_max_tokens_is_clamped_to_the_cap(gw, upstream):
    _, client = gw
    client.post("/v1/chat/completions", json=chat_body(max_tokens=1_000_000))
    assert upstream.calls[0]["body"]["max_tokens"] == 4096
    client.post("/v1/chat/completions", json=chat_body(max_completion_tokens=999999))
    assert upstream.calls[1]["body"]["max_completion_tokens"] == 4096


def test_small_max_tokens_is_left_alone_and_missing_gets_default(gw, upstream):
    _, client = gw
    client.post("/v1/chat/completions", json=chat_body(max_tokens=16))
    client.post("/v1/chat/completions", json=chat_body())
    assert upstream.calls[0]["body"]["max_tokens"] == 16
    assert upstream.calls[1]["body"]["max_tokens"] == 4096


def test_local_provider_gets_no_credentials_and_no_cost_request(gw, upstream):
    _, client = gw
    client.post("/v1/chat/completions", json=chat_body(model="bdai-victim"))
    call = upstream.calls[0]
    assert "authorization" not in call["headers"]
    assert "usage" not in call["body"]
    assert call["body"]["model"] == "qwen3:1.7b"


def test_victim_alias_disables_thinking_by_default_but_the_client_can_override(gw, upstream):
    """Qwen3 spends a small max_tokens budget on hidden thinking and returns empty content,
    so the alias carries a default that labs inherit."""
    _, client = gw
    client.post("/v1/chat/completions", json=chat_body(model="bdai-victim"))
    assert upstream.calls[0]["body"]["reasoning_effort"] == "none"
    client.post("/v1/chat/completions", json=chat_body(model="bdai-victim", reasoning_effort="high"))
    assert upstream.calls[1]["body"]["reasoning_effort"] == "high"
    client.post("/v1/chat/completions", json=chat_body(model="bdai-default"))
    assert "reasoning_effort" not in upstream.calls[2]["body"], "hosted aliases must be left untouched"


def test_unreachable_local_model_gives_an_actionable_message(make_gateway):
    _, client = make_gateway(base="http://127.0.0.1:9")
    h = {"Authorization": f"Bearer {GATEWAY_KEY}"}
    for path, body in (("/v1/chat/completions", chat_body(model="bdai-victim")),
                       ("/v1/embeddings", {"model": "bdai-embed", "input": ["x"]})):
        r = client.post(path, headers=h, json=body)
        assert r.status_code == 502
        msg = r.json()["error"]["message"]
        assert "local model server" in msg and "troubleshooting" in msg
        assert "127.0.0.1" not in msg, "do not leak internal addresses"


def test_missing_provider_key_is_reported_not_crashed(make_gateway, upstream):
    _, client = make_gateway(provider_key="")
    r = client.post("/v1/chat/completions", headers={"Authorization": f"Bearer {GATEWAY_KEY}"}, json=chat_body())
    assert r.status_code == 500 and r.json()["error"]["code"] == "not_configured"
    assert upstream.calls == []


# ---------- metering ----------

def test_cost_from_provider_is_recorded_and_reported(gw):
    _, client = gw
    client.post("/v1/chat/completions", json=chat_body(), headers={"X-BDAI-Lab": "unit-test"})
    u = client.get("/v1/usage").json()
    assert u["requests"] == 1 and u["spent_usd"] == pytest.approx(0.00123)
    assert u["prompt_tokens"] == 1000 and u["completion_tokens"] == 500
    assert u["by_alias"]["bdai-default"]["requests"] == 1
    assert u["remaining_usd"] == pytest.approx(1.0 - 0.00123)


def test_cost_falls_back_to_price_table(gw, upstream):
    _, client = gw
    upstream.mode = "nocost"
    client.post("/v1/chat/completions", json=chat_body())  # haiku: 0.10 in / 0.50 out per million
    expected = (1000 * 0.10 + 500 * 0.50) / 1_000_000
    assert client.get("/v1/usage").json()["spent_usd"] == pytest.approx(expected)


def test_local_model_costs_nothing_but_is_counted(gw):
    _, client = gw
    client.post("/v1/chat/completions", json=chat_body(model="bdai-victim"))
    u = client.get("/v1/usage").json()
    assert u["spent_usd"] == 0 and u["requests"] == 1


@pytest.mark.parametrize("mode", ["negative_cost", "garbage_cost", "usage_not_a_dict", "huge_cost"])
def test_hostile_or_malformed_usage_cannot_corrupt_the_ledger(gw, upstream, mode):
    """Usage figures come from a third party. The user must still get their answer, and the
    ledger must stay sane (no negative spend that reopens the cap, no NaN, no crash)."""
    _, client = gw
    upstream.mode = mode
    r = client.post("/v1/chat/completions", json=chat_body())
    assert r.status_code == 200 and r.json()["choices"][0]["message"]["content"] == "hi"
    u = client.get("/v1/usage").json()
    assert u["requests"] == 1
    assert 0 <= u["spent_usd"] < 1, f"spend out of range: {u['spent_usd']}"
    assert u["spent_usd"] == u["spent_usd"], "spend is NaN"  # NaN != NaN


def test_a_local_endpoint_cannot_charge_the_budget(gw, upstream):
    """Ollama never reports a cost. If an endpoint claims one anyway, ignore it."""
    _, client = gw
    client.post("/v1/chat/completions", json=chat_body(model="bdai-victim"))  # fake upstream says cost=0.00123
    assert client.get("/v1/usage").json()["spent_usd"] == 0


def test_upstream_error_is_passed_through_and_not_charged(gw, upstream):
    _, client = gw
    upstream.mode = "rate_limited"
    r = client.post("/v1/chat/completions", json=chat_body())
    assert r.status_code == 429
    assert client.get("/v1/usage").json()["requests"] == 0


def test_unreachable_upstream_returns_502(make_gateway):
    _, client = make_gateway(base="http://127.0.0.1:9")
    r = client.post("/v1/chat/completions", headers={"Authorization": f"Bearer {GATEWAY_KEY}"}, json=chat_body())
    assert r.status_code == 502 and r.json()["error"]["code"] == "upstream_error"


# ---------- spend cap ----------

def test_spend_cap_blocks_further_calls_without_contacting_the_provider(make_gateway, upstream):
    _, client = make_gateway(budget="0.002")
    h = {"Authorization": f"Bearer {GATEWAY_KEY}"}
    assert client.post("/v1/chat/completions", headers=h, json=chat_body()).status_code == 200  # 0.00123
    assert client.post("/v1/chat/completions", headers=h, json=chat_body()).status_code == 200  # 0.00246
    calls_before = len(upstream.calls)
    r = client.post("/v1/chat/completions", headers=h, json=chat_body())
    assert r.status_code == 429 and r.json()["error"]["code"] == "budget_exceeded"
    assert len(upstream.calls) == calls_before, "a capped request must never reach the provider"
    e = client.post("/v1/embeddings", headers=h, json={"model": "bdai-embed", "input": ["x"]})
    assert e.status_code == 429, "the cap must also apply to embeddings"


def test_cap_applies_to_free_models_once_reached(make_gateway):
    """Documented behaviour: the cap is global, so local calls stop too. Keep it consistent."""
    _, client = make_gateway(budget="0.001")
    h = {"Authorization": f"Bearer {GATEWAY_KEY}"}
    client.post("/v1/chat/completions", headers=h, json=chat_body())
    assert client.post("/v1/chat/completions", headers=h, json=chat_body(model="bdai-victim")).status_code == 429


def test_spend_survives_a_gateway_restart(make_gateway, tmp_path):
    module, client = make_gateway()
    client.post("/v1/chat/completions", headers={"Authorization": f"Bearer {GATEWAY_KEY}"}, json=chat_body())
    import importlib.util, os
    os.environ["BDAI_DB_PATH"] = module.DB_PATH  # same database file
    spec = importlib.util.spec_from_file_location("gateway_restarted", module.__file__)
    reloaded = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(reloaded)
    assert reloaded.spent_usd() == pytest.approx(0.00123)


# ---------- streaming ----------

def test_streaming_is_relayed_and_metered(gw, upstream):
    _, client = gw
    r = client.post("/v1/chat/completions", json=chat_body(stream=True))
    assert r.status_code == 200 and "Hel" in r.text and "[DONE]" in r.text
    assert upstream.calls[0]["body"]["stream_options"] == {"include_usage": True}
    for _ in range(40):  # the ledger write happens when the stream closes
        if client.get("/v1/usage").json()["requests"] == 1:
            break
        time.sleep(0.05)
    u = client.get("/v1/usage").json()
    assert u["requests"] == 1 and u["spent_usd"] == pytest.approx(0.0004)


# ---------- embeddings ----------

def test_embeddings_are_proxied_to_the_local_model_and_counted(gw, upstream):
    _, client = gw
    r = client.post("/v1/embeddings", json={"model": "bdai-embed", "input": ["hello"]})
    assert r.status_code == 200 and r.json()["data"][0]["embedding"] == [0.1, 0.2, 0.3]
    assert upstream.calls[0]["body"]["model"] == "nomic-embed-text"
    u = client.get("/v1/usage").json()
    assert u["requests"] == 1 and u["by_alias"]["bdai-embed"]["prompt_tokens"] == 3


# ---------- privacy ----------

def test_prompts_and_responses_are_never_logged(gw, caplog):
    _, client = gw
    caplog.set_level("DEBUG")
    client.post("/v1/chat/completions", json=chat_body(messages=[{"role": "user", "content": "CANARY-SECRET-PROMPT"}]))
    assert "CANARY-SECRET-PROMPT" not in caplog.text
    assert PROVIDER_KEY not in caplog.text and GATEWAY_KEY not in caplog.text


def test_prompts_are_not_stored_in_the_ledger(gw):
    module, client = gw
    client.post("/v1/chat/completions", json=chat_body(messages=[{"role": "user", "content": "CANARY-SECRET-PROMPT"}]))
    rows = module._db.execute("SELECT * FROM usage").fetchall()
    assert "CANARY" not in json.dumps(rows)
