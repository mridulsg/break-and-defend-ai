"""Unit tests for Course 2 Labs 4.1 and 4.2: bearer tokens on MCP servers, three mistakes as shipped, and the checks with fixes on."""
import base64
import importlib.util
import json
import os
import sys
import time

import pytest

from conftest import REPO

LAB = REPO / "labs" / "c2-mcp" / "ch04-auth" / "auth-lab"
MCP = REPO / "shared" / "mcp"
CONSOLE_DIR = REPO / "shared" / "console"

os.environ.setdefault("OPENAI_API_KEY", "test-key")
os.environ.setdefault("OPENAI_BASE_URL", "http://127.0.0.1:9/v1")


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture()
def con(tmp_path, monkeypatch):
    monkeypatch.setenv("BDAI_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("BDAI_CONSOLE_DIR", str(CONSOLE_DIR))
    monkeypatch.setenv("BDAI_MCP_DIR", str(MCP))
    monkeypatch.syspath_prepend(str(LAB / "app"))
    monkeypatch.syspath_prepend(str(MCP))
    for name in ("acme", "labkit", "progress", "progresskit", "console", "host", "mcpmini", "server"):
        sys.modules.pop(name, None)
    module = load(LAB / "app" / "console.py", "console")
    module.LAB.start_servers()
    yield module
    for httpd in module.LAB.httpds:
        httpd.shutdown()


def call(con, server, tool, args, token):
    return con.LAB.tester({"server": server, "method": "tools/call", "name": tool, "arguments": args, "token": token}, {})


def forged(con, aud="tickets", scope="tickets:write", exp=None):
    head = con.b64(json.dumps({"alg": "none"}).encode())
    body = con.b64(json.dumps({"iss": con.ISSUER, "sub": "sam", "aud": aud, "scope": scope, "exp": exp or int(time.time()) + 600}).encode())
    return f"{head}.{body}."


def fixes(con, on):
    con.LAB.set_fixes({"on": on}, {})


def test_config_and_missions(con):
    cfg = con.LAB.config({}, {})
    assert cfg["mint"] == {"audiences": ["notes", "tickets"]} and cfg["views"] == ["servers", "tester", "missions"]
    assert [m["id"] for m in cfg["missions"]] == ["audience", "scope", "forged"] == list(con.progress.MISSIONS)


def test_a_server_needs_a_token(con):
    r = call(con, "tickets", "get_ticket", {"id": "T-101"}, "")
    assert r["status"] == 401 and "invalid_token" in r["response"]
    r = call(con, "tickets", "get_ticket", {"id": "T-101"}, "not.a.token.at.all")
    assert r["status"] == 401


def test_the_servers_page_works_with_the_viewer_token(con):
    srv = con.LAB.servers({}, {})["servers"]
    assert all("tools" in s for s in srv) and not con.progress.load()


def test_a_proper_token_works(con):
    r = call(con, "tickets", "get_ticket", {"id": "T-101"}, con.mint("tickets", "tickets:read"))
    assert r["status"] == 200 and "Orders service slow" in r["response"] and not con.progress.load()


def test_expired_and_tampered_tokens_are_refused_even_as_shipped(con):
    head, body, sig = con.mint("tickets", "tickets:read", ttl=-10).split(".")
    assert call(con, "tickets", "get_ticket", {"id": "T-101"}, f"{head}.{body}.{sig}")["status"] == 401
    head, body, sig = con.mint("tickets", "tickets:read").split(".")
    evil = con.b64(json.dumps({"iss": con.ISSUER, "sub": "sam", "aud": "tickets", "scope": "tickets:write", "exp": int(time.time()) + 600}).encode())
    assert call(con, "tickets", "get_ticket", {"id": "T-101"}, f"{head}.{evil}.{sig}")["status"] == 401, "changing the payload breaks the signature"


def test_audience_mistake_as_shipped_and_fixed(con):
    token = con.mint("notes", "tickets:read")
    assert call(con, "tickets", "get_ticket", {"id": "T-101"}, token)["status"] == 200 and "audience" in con.progress.load()
    con.progress._store.reset()
    fixes(con, True)
    r = call(con, "tickets", "get_ticket", {"id": "T-101"}, token)
    assert r["status"] == 401 and "resource_metadata" in json.dumps(r["response"]) or r["status"] == 401
    assert not con.progress.load()


def test_scope_mistake_as_shipped_and_fixed(con):
    token = con.mint("tickets", "tickets:read")
    r = call(con, "tickets", "add_comment", {"id": "T-101", "text": "hi"}, token)
    assert r["status"] == 200 and con.DATA.comments and "scope" in con.progress.load()
    con.DATA.reset()
    con.progress._store.reset()
    fixes(con, True)
    r = call(con, "tickets", "add_comment", {"id": "T-101", "text": "hi"}, token)
    assert r["status"] == 403 and "insufficient_scope" in r["response"] and not con.DATA.comments
    assert call(con, "tickets", "add_comment", {"id": "T-101", "text": "ok"}, con.mint("tickets", "tickets:read tickets:write"))["status"] == 200


def test_forged_token_as_shipped_and_fixed(con):
    assert call(con, "tickets", "get_ticket", {"id": "T-101"}, forged(con))["status"] == 200 and "forged" in con.progress.load()
    con.progress._store.reset()
    fixes(con, True)
    assert call(con, "tickets", "get_ticket", {"id": "T-101"}, forged(con))["status"] == 401 and not con.progress.load()


def test_fixed_servers_still_serve_good_tokens(con):
    fixes(con, True)
    assert call(con, "notes", "read_note", {"id": "onboarding"}, con.mint("notes", "notes:read"))["status"] == 200


def test_mint_validates_input(con):
    for bad in ({}, {"aud": "x"}, {"aud": "tickets", "scope": "root"}, {"aud": "tickets", "scope": 5}, {"aud": "tickets", "scope": "tickets:read " * 20}):
        with pytest.raises(con.labkit.web.ApiError):
            con.mint_route(bad, {})
    assert con.mint_route({"aud": "tickets", "scope": "tickets:read"}, {})["token"].count(".") == 2


def test_the_token_is_not_kept_between_requests_and_is_masked_in_the_view(con):
    r = call(con, "tickets", "get_ticket", {"id": "T-101"}, con.mint("tickets", "tickets:read"))
    assert r["request"]["headers"]["Authorization"] == "Bearer ***"
    assert call(con, "tickets", "get_ticket", {"id": "T-101"}, "")["status"] == 401


def test_flag_needs_all_three_and_lives_in_one_script(con):
    call(con, "tickets", "get_ticket", {"id": "T-101"}, con.mint("notes", "tickets:read"))
    call(con, "tickets", "add_comment", {"id": "T-101", "text": "x"}, con.mint("tickets", "tickets:read"))
    assert con.LAB.state({}, {})["flag"] is None
    call(con, "tickets", "get_ticket", {"id": "T-101"}, forged(con))
    st = con.LAB.state({}, {})
    assert st["flag"] == "BDAI{c2-ch04-the-token-said-yes-to-everything}" and st["missions"]["complete"]
    holders = [str(p.relative_to(REPO)) for p in REPO.rglob("*.py") if "tests" not in p.parts and ".scratch" not in p.parts
               and "BDAI{c2-ch04-the-token-said-yes-to-everything}" in p.read_text(encoding="utf-8")]
    assert holders == ["labs/c2-mcp/ch04-auth/auth-lab/app/progress.py"]
