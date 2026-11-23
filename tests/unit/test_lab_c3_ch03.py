"""Unit tests for Course 3 Labs 3.1 and 3.2: memory poisoning across sessions and the controls."""
import importlib.util
import sys

import pytest

from conftest import REPO

AGENTS = REPO / "shared" / "agents"
MCP = REPO / "shared" / "mcp"
CONSOLE_DIR = REPO / "shared" / "console"
LAB = REPO / "labs" / "c3-agents" / "ch03-memory-poisoning" / "memory-lab"


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
    monkeypatch.setenv("BDAI_AGENTS_DIR", str(AGENTS))
    for d in (LAB / "app", AGENTS, MCP):
        monkeypatch.syspath_prepend(str(d))
    for name in ("acme", "labkit", "progress", "progresskit", "console", "host", "mcpmini", "server", "sim", "suitekit"):
        sys.modules.pop(name, None)
    return load(LAB / "app" / "console.py", "console")


def run(con, **controls):
    con.LAB.set_policy({"policy": controls}, {})
    r = con.LAB.run_route({}, {})
    return {x["id"]: x["worked"] for x in r["results"]}, r


def test_baseline_a_planted_memory_fires_the_next_day(con):
    w, r = run(con)
    assert w == {"M1": True, "M2": True, "L1": True, "L2": True} and "baseline" in con.progress.load()
    assert any("next day" in line for line in r["results"][0]["details"])


@pytest.mark.parametrize("control,stopped,work", [("scan", {"M1"}, {"L1", "L2"}), ("plan", {"M1", "M2"}, {"L1", "L2"}), ("quarantine", {"M1", "M2"}, {"L1", "L2"}),
                                                   ("ttl", {"M1", "M2"}, {"L2"}), ("scopes", {"M1", "M2"}, {"L1", "L2"}), ("denyall", {"M1", "M2"}, set())])
def test_each_control(con, control, stopped, work):
    w, r = run(con, **{control: True})
    assert {k for k in ("M1", "M2") if not w[k]} == stopped and {k for k in ("L1", "L2") if w[k]} == work


def test_missions_and_flag(con):
    run(con)
    run(con, ttl=True)
    assert "tradeoff" in con.progress.load() and "hardened" not in con.progress.load()
    run(con, plan=True, quarantine=True)
    st = con.LAB.state({}, {})
    assert st["flag"] == "BDAI{c3-ch03-the-memory-was-the-attack}" and st["missions"]["complete"]
    holders = [str(p.relative_to(REPO)) for p in REPO.rglob("*.py") if "tests" not in p.parts and ".scratch" not in p.parts
               and "BDAI{c3-ch03-the-memory-was-the-attack}" in p.read_text(encoding="utf-8")]
    assert holders == ["labs/c3-agents/ch03-memory-poisoning/memory-lab/app/progress.py"]


def test_quarantined_memory_is_held_not_deleted(con):
    sim = con.sim
    w = sim.World()
    sim.run_task(w, {"quarantine": True}, "read_blog_plant")
    assert len(w.memory) == 1 and w.memory[0]["pending"] is True
    a = sim.Agent(w, {})
    assert a.run_tool("recall", {}) == "(memory is empty)"
