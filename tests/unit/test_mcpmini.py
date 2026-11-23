"""Unit tests for shared/mcp/mcpmini.py: the minimal MCP implementation the Course 2 labs use.

These tests pin the wire-format rules of the 2026-07-28 specification that the labs rely on.
"""
import json
import sys

import pytest

from conftest import REPO

sys.path.insert(0, str(REPO / "shared" / "mcp"))
import mcpmini as m  # noqa: E402


def headers(method, name=None, version=m.PROTOCOL_VERSION, **extra):
    h = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream", "MCP-Protocol-Version": version, "Mcp-Method": method}
    if name:
        h["Mcp-Name"] = name
    h.update(extra)
    return h


def body(method, params=None, rid=1, meta=True, version=m.PROTOCOL_VERSION):
    p = dict(params or {})
    if meta:
        p["_meta"] = {m.M_VERSION: version, m.M_CAPS: {}}
    msg = {"jsonrpc": "2.0", "method": method, "params": p}
    if rid is not None:
        msg["id"] = rid
    return json.dumps(msg).encode()


@pytest.fixture()
def server():
    s = m.McpServer("notes", instructions="Notes for engineers.")

    @s.tool("add", "Add two integers.", {"type": "object", "properties": {"a": {"type": "integer"}, "b": {"type": "integer"}}, "required": ["a", "b"], "additionalProperties": False})
    def add(args):
        return str(args["a"] + args["b"])

    @s.tool("boom", "Always fails.")
    def boom(args):
        raise RuntimeError("it broke")

    @s.tool("who", "Say who is calling.")
    def who(args, ctx):
        return json.dumps(ctx["claims"])
    return s


def call(s, method, params=None, **kw):
    h = headers(method, (params or {}).get("name"))
    h.update(kw.pop("h", {}))
    return s.handle(h, kw.pop("b", None) or body(method, params))


def test_discover(server):
    status, reply, _ = call(server, "server/discover")
    r = reply["result"]
    assert status == 200 and r["resultType"] == "complete" and r["supportedVersions"] == [m.PROTOCOL_VERSION]
    assert r["_meta"][m.M_SERVER]["name"] == "notes" and r["capabilities"] == {"tools": {}} and r["instructions"] == "Notes for engineers."


def test_list_has_required_fields(server):
    _, reply, _ = call(server, "tools/list")
    r = reply["result"]
    assert r["resultType"] == "complete" and r["ttlMs"] == server.ttl_ms and r["cacheScope"] == "public"
    assert [t["name"] for t in r["tools"]] == ["add", "boom", "who"]
    assert all({"name", "description", "inputSchema"} <= set(t) for t in r["tools"])


def test_call_returns_content_and_is_error_false(server):
    status, reply, _ = call(server, "tools/call", {"name": "add", "arguments": {"a": 2, "b": 3}})
    assert status == 200 and reply["result"] == {"resultType": "complete", "content": [{"type": "text", "text": "5"}], "isError": False}


def test_a_failing_tool_is_a_result_with_is_error(server):
    status, reply, _ = call(server, "tools/call", {"name": "boom"})
    assert status == 200 and reply["result"]["isError"] is True and "it broke" in reply["result"]["content"][0]["text"]


def test_invalid_arguments_and_unknown_tool_are_protocol_errors(server):
    for params in ({"name": "add", "arguments": {"a": 1}}, {"name": "add", "arguments": {"a": "1", "b": 2}},
                   {"name": "add", "arguments": {"a": 1, "b": 2, "c": 3}}, {"name": "nope"}):
        status, reply, _ = call(server, "tools/call", params)
        assert status == 400 and reply["error"]["code"] == m.INVALID_PARAMS


def test_unknown_method_is_404(server):
    status, reply, _ = call(server, "tools/zap")
    assert status == 404 and reply["error"]["code"] == m.METHOD_NOT_FOUND


def test_header_mismatches_are_rejected_with_32020(server):
    for h in ({"MCP-Protocol-Version": "2025-11-25"}, {"Mcp-Method": "tools/list"}):
        status, reply, _ = call(server, "server/discover", h=h)
        assert status == 400 and reply["error"]["code"] == m.HEADER_MISMATCH
    status, reply, _ = server.handle(headers("tools/call", "boom"), body("tools/call", {"name": "add", "arguments": {"a": 1, "b": 1}}))
    assert status == 400 and reply["error"]["code"] == m.HEADER_MISMATCH, "Mcp-Name must match params.name"


def test_missing_meta_is_32602(server):
    status, reply, _ = server.handle(headers("tools/list"), body("tools/list", meta=False))
    assert status == 400 and reply["error"]["code"] == m.INVALID_PARAMS


def test_unsupported_version_is_32022_with_data(server):
    status, reply, _ = server.handle(headers("tools/list", version="1900-01-01"), body("tools/list", version="1900-01-01"))
    assert status == 400 and reply["error"]["code"] == m.UNSUPPORTED_VERSION
    assert reply["error"]["data"] == {"supported": [m.PROTOCOL_VERSION], "requested": "1900-01-01"}


def test_a_notification_gets_202_and_no_body(server):
    status, reply, _ = server.handle(headers("notifications/cancelled"), body("notifications/cancelled", rid=None))
    assert status == 202 and reply is None


def test_garbage_is_rejected(server):
    for raw in (b"not json", b"[]", b'{"jsonrpc":"1.0","method":"x"}', b'{"jsonrpc":"2.0"}', b'{"jsonrpc":"2.0","method":"tools/list","params":[]}'):
        status, reply, _ = server.handle(headers("tools/list"), raw)
        assert status == 400 and "error" in reply


def test_origin_validation_blocks_foreign_origins_and_allows_none(server):
    assert call(server, "server/discover", h={"Origin": "http://evil.example"})[0] == 403
    assert call(server, "server/discover", h={"Origin": "http://localhost:3000"})[0] == 200
    assert call(server, "server/discover", h={"Origin": "http://localhost.evil.example"})[0] == 403
    assert call(server, "server/discover")[0] == 200


def test_authentication_hook_and_claims_reach_the_tool(server):
    def authenticate(h):
        if h.get("authorization") != "Bearer good":
            raise m.McpError(-32001, "Unauthorized", 401, headers={"WWW-Authenticate": 'Bearer resource_metadata="http://x/.well-known/oauth-protected-resource"'})
        return {"sub": "sam", "scope": "notes:read"}
    server.authenticate = authenticate
    status, reply, extra = call(server, "tools/list")
    assert status == 401 and "resource_metadata" in extra["WWW-Authenticate"]
    status, reply, _ = call(server, "tools/call", {"name": "who"}, h={"Authorization": "Bearer good"})
    assert json.loads(reply["result"]["content"][0]["text"]) == {"sub": "sam", "scope": "notes:read"}


def test_changing_a_description_changes_the_next_listing(server):
    server.set_description("add", "Add two integers. (changed)")
    _, reply, _ = call(server, "tools/list")
    assert reply["result"]["tools"][0]["description"].endswith("(changed)")


def test_the_log_records_what_the_server_saw(server):
    call(server, "tools/list")
    call(server, "tools/call", {"name": "nope"})
    assert [e["ok"] for e in server.log] == [True, False]


# ------------------------------------------------------------------ over real http, with the client


def test_client_and_server_over_http(server):
    httpd = server.serve()
    try:
        port = httpd.server_address[1]
        c = m.McpClient(f"http://127.0.0.1:{port}/mcp")
        assert c.discover()["_meta"][m.M_SERVER]["name"] == "notes"
        assert [t["name"] for t in c.list_tools()] == ["add", "boom", "who"]
        assert c.call("add", {"a": 4, "b": 5})["content"][0]["text"] == "9"
        assert c.last["request"]["params"]["_meta"][m.M_VERSION] == m.PROTOCOL_VERSION and c.last["status"] == 200
        with pytest.raises(m.McpError) as e:
            c.call("nope")
        assert e.value.code == m.INVALID_PARAMS and e.value.status == 400
        with pytest.raises(m.McpError) as e:
            c.request("tools/list", extra_headers={"Mcp-Method": "wrong"})
        assert e.value.code == m.HEADER_MISMATCH
        with pytest.raises(m.McpError) as e:
            c.request("tools/list", extra_headers={"Origin": "http://evil.example"})
        assert e.value.status == 403
    finally:
        httpd.shutdown()


def test_http_only_accepts_post_on_the_endpoint(server):
    import urllib.error
    import urllib.request

    httpd = server.serve()
    try:
        port = httpd.server_address[1]
        for method in ("GET", "DELETE"):
            with pytest.raises(urllib.error.HTTPError) as e:
                urllib.request.urlopen(urllib.request.Request(f"http://127.0.0.1:{port}/mcp", method=method))
            assert e.value.code == 405
        with pytest.raises(urllib.error.HTTPError) as e:
            urllib.request.urlopen(urllib.request.Request(f"http://127.0.0.1:{port}/other", data=b"{}", method="POST"))
        assert e.value.code == 404
    finally:
        httpd.shutdown()


def test_validate_arguments_subset():
    schema = {"type": "object", "properties": {"n": {"type": "integer"}, "ok": {"type": "boolean"}}, "required": ["n"]}
    assert m.validate_arguments(schema, {"n": 1}) is None
    assert m.validate_arguments(schema, {"n": True}) is not None, "a boolean is not an integer"
    assert m.validate_arguments(schema, []) is not None
