"""Unit tests for Course 2 Labs 8.1 and 8.2: the shadow-MCP inventory, the approval policy, the decisions and the missions."""
import importlib.util
import os
import sys

import pytest

from conftest import REPO

LAB = REPO / "labs" / "c2-mcp" / "ch08-governance" / "inventory-lab"
MCP = REPO / "shared" / "mcp"
CONSOLE_DIR = REPO / "shared" / "console"


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
    for name in ("acme", "labkit", "progress", "progresskit", "console", "host", "mcpmini", "server", "inventory"):
        sys.modules.pop(name, None)
    return load(LAB / "app" / "console.py", "console")


def by_key(con):
    return {s["key"]: s for s in con.snapshot()["servers"]}


def decide(con, key, action="block", owner="Security team", reason="Not reviewed, so blocked for now."):
    return con.decide_route({"key": key, "action": action, "owner": owner, "reason": reason}, {})


ALL = ["sam-laptop/docs-helper", "maria-laptop/postmark-mcp", "jonas-workstation/web-fetch", "jonas-workstation/acme-notes", "priya-laptop/sql-explorer"]


def test_the_inventory_finds_every_server(con):
    s = by_key(con)
    assert len(s) == 8 and con.snapshot()["machines"] == ["jonas-workstation", "maria-laptop", "priya-laptop", "sam-laptop"]
    assert {k for k, v in s.items() if v["status"] != "approved"} == set(ALL)
    assert s["sam-laptop/acme-notes"]["status"] == "approved" and s["maria-laptop/acme-tickets"]["status"] == "approved"
    assert s["jonas-workstation/acme-notes"]["status"] == "drift", "approved by name but fetched at its newest version"


def test_flags(con):
    s = by_key(con)
    assert s["maria-laptop/postmark-mcp"]["flags"] == ["secret-in-config", "unpinned"]
    assert s["priya-laptop/sql-explorer"]["flags"] == ["plaintext-http", "secret-in-config"]
    assert s["jonas-workstation/web-fetch"]["flags"] == [] and s["sam-laptop/docs-helper"]["flags"] == []
    assert s["maria-laptop/acme-tickets"]["flags"] == [], "a ${VARIABLE} reference is not a secret in the file"


def test_flag_rules(con):
    f = con.inventory.flags_for
    assert f({"command": "uvx", "args": ["pkg==1.2.3"]}) == [] and f({"command": "npx", "args": ["-y", "pkg@2.0.1"]}) == []
    assert f({"command": "npx", "args": ["-y", "pkg"]}) == ["unpinned"] and f({"command": "uvx", "args": ["pkg@latest"]}) == ["unpinned"]
    assert f({"url": "http://localhost:1/mcp"}) == [] and f({"url": "http://127.0.0.1/mcp"}) == [] and f({"url": "https://x.example/mcp"}) == []
    assert f({"url": "http://host.example/mcp"}) == ["plaintext-http"] and f({"url": "http://localhost.evil.example/mcp"}) == ["plaintext-http"]
    assert f({"env": {"API_KEY": "abcdef"}}) == ["secret-in-config"] and f({"env": {"API_KEY": "${API_KEY}"}}) == []


def test_only_servers_without_blocking_flags_can_be_approved(con):
    s = by_key(con)
    assert s["sam-laptop/docs-helper"]["approvable"] and s["jonas-workstation/web-fetch"]["approvable"]
    for k in ("maria-laptop/postmark-mcp", "priya-laptop/sql-explorer", "jonas-workstation/acme-notes"):
        assert not s[k]["approvable"]
        with pytest.raises(con.labkit.web.ApiError, match="Cannot approve"):
            decide(con, k, "approve")


def test_decision_validation(con):
    for bad in ({}, {"key": "x/y", "action": "block", "owner": "Team", "reason": "A long enough reason."},
                {"key": "sam-laptop/acme-notes", "action": "block", "owner": "Team", "reason": "A long enough reason."},
                {"key": ALL[0], "action": "delete", "owner": "Team", "reason": "A long enough reason."},
                {"key": ALL[0], "action": "block", "owner": "", "reason": "A long enough reason."},
                {"key": ALL[0], "action": "block", "owner": "Team", "reason": "short"},
                {"key": ALL[0], "action": "block", "owner": "Team", "reason": "x" * 201}):
        with pytest.raises(con.labkit.web.ApiError):
            con.decide_route(bad, {})


def test_missions_in_order(con):
    r = con.inventory_route({}, {})
    assert len(r["undecided"]) == 5 and list(con.progress.load()) == ["inventory"]
    for k in ALL[:4]:
        decide(con, k)
    assert "decide" not in con.progress.load()
    r = decide(con, ALL[4], "investigate")
    assert "decide" in con.progress.load() and r["undecided"] == []
    con.inventory_route({}, {})
    assert "clean" not in con.progress.load(), "investigating is not deciding"
    decide(con, ALL[4], "request-fix", reason="Ask the owner to move it to https first.")
    con.inventory_route({}, {})
    st = con.LAB.state({}, {})
    assert st["flag"] == "BDAI{c2-ch08-nothing-runs-that-nobody-owns}" and st["missions"]["complete"]
    holders = [str(p.relative_to(REPO)) for p in REPO.rglob("*.py") if "tests" not in p.parts and ".scratch" not in p.parts
               and "BDAI{c2-ch08-nothing-runs-that-nobody-owns}" in p.read_text(encoding="utf-8")]
    assert holders == ["labs/c2-mcp/ch08-governance/inventory-lab/app/progress.py"]


def test_reset_clears_decisions(con):
    decide(con, ALL[0])
    assert set(con.reset_route({}, {})["undecided"]) == set(ALL)
