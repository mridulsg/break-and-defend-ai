"""Unit tests for Course 2 Lab 1.1: Acme's two MCP servers, the host, the Tool tester and the missions.

The model is a fake that behaves like a cooperative one: it calls a tool when the question names a ticket or a note.
"""
import importlib.util
import json
import os
import re
import sys
import types

import pytest

from conftest import REPO

LAB = REPO / "labs" / "c2-mcp" / "ch01-mcp-architecture" / "mcp-lab"
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


class FakeModel:
    """Calls get_ticket / read_note when asked about one, then repeats the tool result."""

    def __init__(self):
        self.seen_tools = []

    def create(self, model, messages, tools=None, **kw):
        self.seen_tools = [t["function"]["name"] for t in tools or []]
        question = [m for m in messages if m["role"] == "user"][-1]["content"]
        done = [m for m in messages if m["role"] == "tool"]
        tc = None
        if not done:
            t = re.search(r"\b(T-\d{3})\b", question)
            n = re.search(r"note (\w[\w-]*)", question)
            if t:
                tc = ("tickets__get_ticket", {"id": t.group(1)})
            elif n:
                tc = ("notes__read_note", {"id": n.group(1)})
        if tc:
            call = types.SimpleNamespace(id="c1", function=types.SimpleNamespace(name=tc[0], arguments=json.dumps(tc[1])))
            msg = types.SimpleNamespace(content="", tool_calls=[call])
        else:
            msg = types.SimpleNamespace(content="Result: " + done[-1]["content"] if done else "Hello.", tool_calls=None)
        return types.SimpleNamespace(choices=[types.SimpleNamespace(message=msg)])


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
    fake = FakeModel()
    monkeypatch.setattr(sys.modules["host"].client, "chat", types.SimpleNamespace(completions=fake), raising=False)
    module.LAB.start_servers()
    yield types.SimpleNamespace(c=module, lab=module.LAB, fake=fake)
    for httpd in module.LAB.httpds:
        httpd.shutdown()


def test_config_and_state(con):
    cfg = con.lab.config({}, {})
    assert cfg["bot"] == "Acme Assistant" and cfg["views"] == ["chat", "servers", "tester", "missions"] and cfg["tools_tab"] is True
    assert [m["id"] for m in cfg["missions"]] == ["list", "call", "origin", "agent"] == list(con.c.progress.MISSIONS)
    st = con.lab.state({}, {})
    assert st["ready"] and st["flag"] is None and st["missions"] == {"list": False, "call": False, "origin": False, "agent": False, "complete": False}


def test_servers_page_lists_every_tool(con):
    r = con.lab.servers({}, {})["servers"]
    assert [s["id"] for s in r] == ["notes", "tickets"]
    assert [t["name"] for t in r[0]["tools"]] == ["list_notes", "read_note"]
    assert [t["name"] for t in r[1]["tools"]] == ["list_tickets", "get_ticket", "add_comment"]
    assert all(s["ttl_ms"] > 0 and s["version"] == "2026-07-28" for s in r)


def test_tester_missions_need_the_right_event(con):
    t = con.lab.tester
    r = t({"server": "notes", "method": "tools/list"}, {})
    assert r["status"] == 200 and "list" in con.c.progress.load() and r["request"]["headers"]["Mcp-Method"] == "tools/list"
    r = t({"server": "notes", "method": "tools/call", "name": "read_note", "arguments": {}}, {})
    assert r["status"] == 400 and "call" not in con.c.progress.load(), "a rejected call proves nothing"
    r = t({"server": "notes", "method": "tools/call", "name": "read_note", "arguments": {"id": "onboarding"}}, {})
    assert r["status"] == 200 and "Welcome to Acme" in r["response"] and "call" in con.c.progress.load()
    r = t({"server": "notes", "method": "tools/list", "break": "version"}, {})
    assert r["status"] == 400 and "origin" not in con.c.progress.load()
    r = t({"server": "notes", "method": "tools/list", "break": "origin"}, {})
    assert r["status"] == 403 and "origin" in con.c.progress.load()


def test_tester_input_is_validated(con):
    for bad in ({"server": "x", "method": "tools/list"}, {"server": "notes", "method": "nope"}, {"server": "notes", "method": "tools/call"},
                {"server": "notes", "method": "tools/call", "name": "read_note", "arguments": []}, {"server": "notes", "method": "tools/list", "break": "zap"}):
        with pytest.raises(con.c.labkit.web.ApiError):
            con.lab.tester(bad, {})


def test_the_assistant_uses_a_tool_and_the_agent_mission_ticks(con):
    r = con.lab.ask({"question": "Hello there"}, {})
    assert r["tool_calls"] == [] and "agent" not in con.c.progress.load()
    r = con.lab.ask({"question": "What is ticket T-101 about?"}, {})
    assert r["tool_calls"][0]["name"] == "tickets.get_ticket" and "Orders service slow" in r["shown"]
    assert "agent" in con.c.progress.load()
    assert set(con.fake.seen_tools) == {"notes__list_notes", "notes__read_note", "tickets__list_tickets", "tickets__get_ticket", "tickets__add_comment"}
    assert {e["server"] for e in r["catalog"]} == {"notes", "tickets"} and r["monitor"]["rows"][0]["value"] == "tickets.get_ticket"


def test_unknown_tool_name_from_the_model_is_an_error_not_a_crash(con):
    host = con.lab.make_host()
    host.refresh()
    rec = host.call("tickets__delete_everything", {})
    assert rec["isError"] and "Unknown tool" in rec["text"]
    rec = host.call("nodoubleunderscore", {})
    assert rec["isError"]


def test_ask_input_is_validated(con):
    for bad in ({}, {"question": ""}, {"question": 5}, {"question": "x" * 1501}, {"question": "hi", "model": "other"}):
        with pytest.raises(con.c.labkit.web.ApiError):
            con.lab.ask(bad, {})


def test_flag_needs_all_four_and_lives_in_one_script(con):
    con.lab.tester({"server": "notes", "method": "tools/list"}, {})
    con.lab.tester({"server": "tickets", "method": "tools/call", "name": "get_ticket", "arguments": {"id": "T-101"}}, {})
    con.lab.tester({"server": "tickets", "method": "tools/list", "break": "origin"}, {})
    assert con.lab.state({}, {})["flag"] is None
    con.lab.ask({"question": "What is ticket T-102 about?"}, {})
    st = con.lab.state({}, {})
    assert st["flag"] == "BDAI{c2-ch01-i-have-read-the-protocol}" and st["missions"]["complete"]
    holders = [str(p.relative_to(REPO)) for p in REPO.rglob("*.py") if "tests" not in p.parts and ".scratch" not in p.parts
               and "BDAI{c2-ch01-i-have-read-the-protocol}" in p.read_text(encoding="utf-8")]
    assert holders == ["labs/c2-mcp/ch01-mcp-architecture/mcp-lab/app/progress.py"]


def test_add_comment_is_a_real_write(con):
    r = con.lab.tester({"server": "tickets", "method": "tools/call", "name": "add_comment", "arguments": {"id": "T-101", "text": "hello"}}, {})
    assert r["status"] == 200 and con.c.DATA.comments == [{"id": "T-101", "text": "hello"}]
    assert con.lab.state({}, {})["comments"] == [{"id": "T-101", "text": "hello"}]
