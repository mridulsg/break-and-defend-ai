"""Unit tests for Course 3 Labs 5.1 and 5.2: agent-to-agent trust, the message bus and its controls."""
import importlib.util
import sys

import pytest

from conftest import REPO

AGENTS = REPO / "shared" / "agents"
MCP = REPO / "shared" / "mcp"
CONSOLE_DIR = REPO / "shared" / "console"
LAB = REPO / "labs" / "c3-agents" / "ch05-multi-agent" / "peers-lab"


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


def test_no_controls_all_attacks_work(con):
    w, r = run(con)
    assert w == {"P1": True, "P2": True, "P3": True, "L1": True, "L2": True} and "baseline" in con.progress.load()


@pytest.mark.parametrize("control,stopped,work", [("auth", {"P1"}, {"L1", "L2"}), ("allowlist", {"P1", "P2"}, {"L1", "L2"}), ("peer_scopes", {"P2", "P3"}, {"L1", "L2"}),
                                                   ("schema", {"P3"}, {"L1", "L2"}), ("denyall", {"P1", "P2", "P3"}, set())])
def test_each_control(con, control, stopped, work):
    w, r = run(con, **{control: True})
    assert {k for k in ("P1", "P2", "P3") if not w[k]} == stopped and {k for k in ("L1", "L2") if w[k]} == work


def test_peer_scopes_alone_is_fooled_by_a_forged_sender(con):
    """The forger can claim any scopes: scopes only mean something when the sender is authenticated."""
    w, r = run(con, peer_scopes=True)
    assert w["P1"] is True


def test_signature_covers_the_arguments(con):
    bus = con.bus
    m = bus.message("orchestrator", "payer", "pay", {"to": "acme-vendor", "amount": 80}, ["read", "pay"])
    m["args"] = {"to": "attacker", "amount": 80}
    ok, why = bus.send(con.sim.World(), m, {"auth": True})
    assert not ok and "signature" in why
    m = bus.message("orchestrator", "payer", "pay", {"to": "acme-vendor", "amount": 80}, ["read"])
    m["requester_scopes"] = ["read", "pay"]
    assert not bus.send(con.sim.World(), m, {"auth": True})[0], "a tampered scope list breaks the signature too"


def test_unknown_peer_and_wrong_task(con):
    bus = con.bus
    assert bus.send(con.sim.World(), bus.message("orchestrator", "ghost", "pay", {}, []), {})[1] == "refused: no such peer"
    assert "does not do this task" in bus.send(con.sim.World(), bus.message("orchestrator", "payer", "email", {}, []), {})[1]


def test_missions_and_flag(con):
    run(con)
    run(con, denyall=True)
    assert "overreach" in con.progress.load() and "hardened" not in con.progress.load()
    run(con, auth=True, peer_scopes=True)
    st = con.LAB.state({}, {})
    assert st["flag"] == "BDAI{c3-ch05-trust-is-not-transitive}" and st["missions"]["complete"]
    holders = [str(p.relative_to(REPO)) for p in REPO.rglob("*.py") if "tests" not in p.parts and ".scratch" not in p.parts
               and "BDAI{c3-ch05-trust-is-not-transitive}" in p.read_text(encoding="utf-8")]
    assert holders == ["labs/c3-agents/ch05-multi-agent/peers-lab/app/progress.py"]
