"""Unit tests for the Course 3 capstone (Lab 6.1): the probes, the register and the retest."""
import importlib.util
import sys

import pytest

from conftest import REPO

AGENTS = REPO / "shared" / "agents"
MCP = REPO / "shared" / "mcp"
CONSOLE_DIR = REPO / "shared" / "console"
LAB = REPO / "labs" / "c3-agents" / "ch06-capstone" / "assessment-lab"
ROWS = [{"id": "hijack", "severity": "High", "fix": "Check every action against the plan.", "owner": "Platform team"},
        {"id": "memory", "severity": "High", "fix": "Quarantine memory written because of text read.", "owner": "Platform team"},
        {"id": "power", "severity": "High", "fix": "A least-privilege identity for every task.", "owner": "Platform team"}]


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
    for name in ("acme", "labkit", "progress", "progresskit", "console", "host", "mcpmini", "server", "sim", "suitekit", "bus"):
        sys.modules.pop(name, None)
    return load(LAB / "app" / "console.py", "console")


def run(con, **controls):
    con.LAB.set_policy({"policy": controls}, {})
    r = con.LAB.run_route({}, {})
    return {x["id"]: x["worked"] for x in r["results"]}, r


def test_config(con):
    cfg = con.LAB.config({}, {})
    assert cfg["views"] == ["gateway", "register", "missions"]
    assert [m["id"] for m in cfg["missions"]] == ["found", "register", "retest"] == list(con.progress.MISSIONS)


def test_the_probes_find_all_three_problems(con):
    w, r = run(con)
    assert w == {"A1": True, "A2": True, "A3": True, "L1": True, "L2": True} and "found" in con.progress.load()


def test_register_is_locked_until_the_probes_have_run_and_is_validated(con):
    assert con.get_register()["unlocked"] is False
    with pytest.raises(con.labkit.web.ApiError, match="Run the probes"):
        con.save_register({"rows": ROWS}, {})
    run(con)
    for bad in ({}, {"rows": ROWS[:2]}, {"rows": [{**ROWS[0], "severity": "Urgent"}] + ROWS[1:]}, {"rows": [{**ROWS[0], "fix": "short"}] + ROWS[1:]},
                {"rows": [{**ROWS[0], "owner": ""}] + ROWS[1:]}, {"rows": [{**ROWS[0], "id": "x"}] + ROWS[1:]}):
        with pytest.raises(con.labkit.web.ApiError):
            con.save_register(bad, {})
    r = con.save_register({"rows": ROWS}, {})
    assert r["saved"] and len(r["reference"]) == 3


@pytest.mark.parametrize("controls,stopped", [({"plan": True}, 3), ({"scopes": True, "quarantine": True}, 3), ({"limit": True}, 1), ({"human": True}, 1)])
def test_controls(con, controls, stopped):
    w, r = run(con, **controls)
    assert r["stopped"] == stopped


def test_retest_needs_everything_stopped_and_work_kept(con):
    run(con, plan=True, human=True)
    assert "retest" not in con.progress.load(), "a person in the loop makes the real payment wait"
    run(con, denyall=True)
    assert "retest" not in con.progress.load()
    run(con, plan=True)
    assert "retest" in con.progress.load()


def test_flag_and_one_script(con):
    run(con)
    con.save_register({"rows": ROWS}, {})
    assert con.LAB.state({}, {})["flag"] is None
    run(con, scopes=True, quarantine=True, limit=True)
    st = con.LAB.state({}, {})
    assert st["flag"] == "BDAI{c3-ch06-assessed-reported-fixed-retested}" and st["missions"]["complete"]
    holders = [str(p.relative_to(REPO)) for p in REPO.rglob("*.py") if "tests" not in p.parts and ".scratch" not in p.parts
               and "BDAI{c3-ch06-assessed-reported-fixed-retested}" in p.read_text(encoding="utf-8")]
    assert holders == ["labs/c3-agents/ch06-capstone/assessment-lab/app/progress.py"]
