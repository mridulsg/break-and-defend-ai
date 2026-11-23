"""Unit tests for Course 3 Labs 4.1 and 4.2: a hijacked agent's power depends on its permissions, and the controls."""
import importlib.util
import sys

import pytest

from conftest import REPO

AGENTS = REPO / "shared" / "agents"
MCP = REPO / "shared" / "mcp"
CONSOLE_DIR = REPO / "shared" / "console"
LAB = REPO / "labs" / "c3-agents" / "ch04-tool-misuse" / "power-lab"


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


def test_no_controls_everything_happens(con):
    w, r = run(con)
    assert w == {"H1": True, "H2": True, "H3": True, "L1": True, "L2": True} and "baseline" in con.progress.load()


@pytest.mark.parametrize("control,stopped,work", [("plan", {"H1", "H2", "H3"}, {"L1", "L2"}), ("scopes", {"H1", "H2"}, {"L1", "L2"}), ("budget", {"H3"}, {"L1", "L2"}),
                                                   ("limit", {"H2"}, {"L1", "L2"}), ("human", {"H1", "H2"}, {"L1"}), ("denyall", {"H1", "H2", "H3"}, set())])
def test_each_control(con, control, stopped, work):
    w, r = run(con, **{control: True})
    assert {k for k in ("H1", "H2", "H3") if not w[k]} == stopped and {k for k in ("L1", "L2") if w[k]} == work


def test_the_loop_is_capped_so_the_lab_ends(con):
    sim = con.sim
    w = sim.World()
    lines, a = sim.run_task(w, {}, "summarise_loop")
    assert 20 <= sum(1 for t in a.trace if t["kind"] == "tool") <= 61


def test_missions_and_flag(con):
    run(con)
    run(con, human=True, scopes=True, budget=True)
    assert "friction" in con.progress.load() and "hardened" not in con.progress.load()
    run(con, scopes=True, budget=True, limit=True)
    st = con.LAB.state({}, {})
    assert st["flag"] == "BDAI{c3-ch04-small-powers-small-damage}" and st["missions"]["complete"]
    holders = [str(p.relative_to(REPO)) for p in REPO.rglob("*.py") if "tests" not in p.parts and ".scratch" not in p.parts
               and "BDAI{c3-ch04-small-powers-small-damage}" in p.read_text(encoding="utf-8")]
    assert holders == ["labs/c3-agents/ch04-tool-misuse/power-lab/app/progress.py"]
