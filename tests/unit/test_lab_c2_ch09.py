"""Unit tests for the Course 2 capstone (Lab 9.1): three seeded problems, the register, the fixes and the retest."""
import importlib.util
import json
import os
import sys

import pytest

from conftest import REPO

LAB = REPO / "labs" / "c2-mcp" / "ch09-capstone" / "assessment-lab"
MCP = REPO / "shared" / "mcp"
CONSOLE_DIR = REPO / "shared" / "console"
ROWS = [{"id": "traversal", "severity": "High", "fix": "Resolve the path and check containment.", "owner": "Tool owner"},
        {"id": "scope", "severity": "High", "fix": "Check the scope before add_comment runs.", "owner": "Tickets team"},
        {"id": "poison", "severity": "Medium", "fix": "Review and pin third-party descriptions.", "owner": "Platform"}]


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture()
def con(tmp_path, monkeypatch):
    monkeypatch.setenv("BDAI_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("BDAI_LAB_DIR", str(LAB))
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


def t(con, server, method="tools/call", name=None, args=None, token=""):
    body = {"server": server, "method": method, "token": token}
    if name:
        body.update({"name": name, "arguments": args or {}})
    return con.LAB.tester(body, {})


def find_all(con):
    t(con, "devtools", name="read_file", args={"path": "../secrets/api-key.txt"})
    t(con, "tickets", name="add_comment", args={"id": "T-101", "text": "x"}, token=con.mint_route({"scope": "tickets:read"}, {})["token"])
    t(con, "community", method="tools/list")


def test_config(con):
    cfg = con.LAB.config({}, {})
    assert cfg["views"] == ["servers", "tester", "register", "missions"] and cfg["fixes"] is True
    assert [m["id"] for m in cfg["missions"]] == ["traversal", "scope", "poison", "register", "retest"] == list(con.progress.MISSIONS)
    assert all("tools" in s for s in con.LAB.servers({}, {})["servers"])


def test_each_finding_as_shipped(con):
    t(con, "devtools", name="read_file", args={"path": "runbook.md"})
    assert not con.progress.load()
    assert con.KEY in t(con, "devtools", name="read_file", args={"path": "../secrets/api-key.txt"})["response"]
    assert list(con.progress.load()) == ["traversal"]
    ro = con.mint_route({"scope": "tickets:read"}, {})["token"]
    assert t(con, "tickets", name="get_ticket", args={"id": "T-101"}, token=ro)["status"] == 200 and "scope" not in con.progress.load()
    assert t(con, "tickets", name="add_comment", args={"id": "T-101", "text": "x"}, token=ro)["status"] == 200 and "scope" in con.progress.load()
    t(con, "community", method="tools/list")
    assert "poison" in con.progress.load()


def test_a_write_token_does_not_count_as_the_scope_finding(con):
    rw = con.mint_route({"scope": "tickets:read tickets:write"}, {})["token"]
    t(con, "tickets", name="add_comment", args={"id": "T-101", "text": "x"}, token=rw)
    assert "scope" not in con.progress.load()


def test_tickets_need_a_token(con):
    assert t(con, "tickets", name="get_ticket", args={"id": "T-101"})["status"] == 401


def test_the_register_opens_after_the_findings_and_is_validated(con):
    assert con.get_register()["unlocked"] is False
    with pytest.raises(con.labkit.web.ApiError, match="Confirm all three"):
        con.save_register({"rows": ROWS}, {})
    find_all(con)
    assert con.get_register()["unlocked"] is True
    for bad in ({}, {"rows": ROWS[:2]}, {"rows": [{**ROWS[0], "severity": "Urgent"}] + ROWS[1:]}, {"rows": [{**ROWS[0], "fix": "short"}] + ROWS[1:]},
                {"rows": [{**ROWS[0], "owner": ""}] + ROWS[1:]}, {"rows": [{**ROWS[0], "id": "x"}] + ROWS[1:]}):
        with pytest.raises(con.labkit.web.ApiError):
            con.save_register(bad, {})
    r = con.save_register({"rows": ROWS}, {})
    assert r["saved"] and len(r["reference"]) == 3 and "register" in con.progress.load()


def test_fixes_refuse_traversal_scope_and_hide_the_poisoned_tool(con):
    con.LAB.set_fixes({"on": True}, {})
    assert "that is not a doc" in t(con, "devtools", name="read_file", args={"path": "../secrets/api-key.txt"})["response"]
    assert "Runbook" in t(con, "devtools", name="read_file", args={"path": "runbook.md"})["response"]
    ro = con.mint_route({"scope": "tickets:read"}, {})["token"]
    assert t(con, "tickets", name="add_comment", args={"id": "T-101", "text": "x"}, token=ro)["status"] == 403 and not con.DATA.comments
    assert json.loads(t(con, "community", method="tools/list")["response"])["result"]["tools"] == []
    assert "poison" not in con.progress.load()


def test_the_retest_needs_fixes_on_and_a_refused_traversal(con):
    t(con, "devtools", name="read_file", args={"path": "../secrets/api-key.txt"})
    assert "retest" not in con.progress.load()
    con.LAB.set_fixes({"on": True}, {})
    t(con, "devtools", name="read_file", args={"path": "runbook.md"})
    assert "retest" not in con.progress.load()
    t(con, "devtools", name="read_file", args={"path": "../secrets/api-key.txt"})
    assert "retest" in con.progress.load()


def test_mint_validation(con):
    for bad in ({"scope": "root"}, {"scope": 5}, {"scope": "tickets:read " * 10}):
        with pytest.raises(con.labkit.web.ApiError):
            con.mint_route(bad, {})


def test_flag_and_one_script(con):
    find_all(con)
    con.save_register({"rows": ROWS}, {})
    assert con.LAB.state({}, {})["flag"] is None
    con.LAB.set_fixes({"on": True}, {})
    t(con, "devtools", name="read_file", args={"path": "../secrets/api-key.txt"})
    st = con.LAB.state({}, {})
    assert st["flag"] == "BDAI{c2-ch09-found-reported-fixed-retested}" and st["missions"]["complete"]
    holders = [str(p.relative_to(REPO)) for p in REPO.rglob("*.py") if "tests" not in p.parts and ".scratch" not in p.parts
               and "BDAI{c2-ch09-found-reported-fixed-retested}" in p.read_text(encoding="utf-8")]
    assert holders == ["labs/c2-mcp/ch09-capstone/assessment-lab/app/progress.py"]
