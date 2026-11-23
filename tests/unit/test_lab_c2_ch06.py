"""Unit tests for Course 2 Labs 6.1 and 6.2: the gateway controls, the attack suite and the missions."""
import importlib.util
import json
import os
import sys

import pytest

from conftest import REPO

LAB = REPO / "labs" / "c2-mcp" / "ch06-defending" / "gateway-lab"
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


def run(con, **controls):
    con.set_policy({"policy": controls}, {})
    r = con.suite_route({}, {})
    return {x["id"]: x["worked"] for x in r["results"]}, r


def test_config(con):
    cfg = con.LAB.config({}, {})
    assert cfg["views"] == ["gateway", "servers", "missions"]
    assert [m["id"] for m in cfg["missions"]] == ["baseline", "overblock", "hardened"] == list(con.progress.MISSIONS)


def test_with_no_controls_every_attack_works_and_every_task_works(con):
    res, r = run(con)
    assert [res[k] for k in ("A1", "A2", "A3", "A4", "A5")] == [True] * 5 and [res[k] for k in ("L1", "L2", "L3")] == [True] * 3
    assert r["stopped"] == 0 and "baseline" in con.progress.load()


@pytest.mark.parametrize("control,stops", [("allowlist", {"A1", "A2", "A4"}), ("pin", {"A2"}), ("scan", {"A1", "A2"}), ("approval", {"A3"}),
                                            ("egress", {"A4"}), ("rate", {"A5"})])
def test_each_control_stops_what_it_should_and_nothing_else(con, control, stops):
    res, r = run(con, **{control: True})
    assert {k for k in ("A1", "A2", "A3", "A4", "A5") if not res[k]} == stops
    assert all(res[k] for k in ("L1", "L2", "L3")), "a single control must not break the real tasks"


def test_deny_everything_stops_all_attacks_and_all_work(con):
    res, r = run(con, denyall=True)
    assert r["stopped"] == 5 and r["work_ok"] == 0
    assert "overblock" in con.progress.load() and "hardened" not in con.progress.load()


def test_the_minimal_good_policy_is_hardened(con):
    res, r = run(con, allowlist=True, approval=True, rate=True)
    assert r["stopped"] == 5 and r["work_ok"] == 3 and "hardened" in con.progress.load()


def test_a_partial_policy_marks_nothing(con):
    run(con, pin=True)
    assert not con.progress.load()


def test_the_scan_leaves_trusted_servers_alone(con):
    res, r = run(con, scan=True)
    assert all(res[k] for k in ("L1", "L2", "L3")), "the scan would hide Acme's own ticket tools if it applied to them"
    assert con.SUSPICIOUS.search("Read one ticket by its id.")


def test_suite_cleans_up_after_itself(con):
    run(con)
    assert con.DATA.comments == [] and next(iter(con.community.tools.values())).description == con.CLEAN


def test_policy_validation(con):
    for bad in ({}, {"policy": []}, {"policy": {"nope": True}}, {"policy": {"pin": "yes"}}):
        with pytest.raises(con.labkit.web.ApiError):
            con.set_policy(bad, {})
    assert con.get_policy()["policy"] == {}


def test_flag_and_one_script(con):
    run(con)
    run(con, denyall=True)
    assert con.LAB.state({}, {})["flag"] is None
    run(con, allowlist=True, approval=True, rate=True)
    st = con.LAB.state({}, {})
    assert st["flag"] == "BDAI{c2-ch06-stopped-the-attacks-kept-the-work}" and st["missions"]["complete"]
    holders = [str(p.relative_to(REPO)) for p in REPO.rglob("*.py") if "tests" not in p.parts and ".scratch" not in p.parts
               and "BDAI{c2-ch06-stopped-the-attacks-kept-the-work}" in p.read_text(encoding="utf-8")]
    assert holders == ["labs/c2-mcp/ch06-defending/gateway-lab/app/progress.py"]
