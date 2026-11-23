"""Unit tests for Labs 9.1 and 9.2: the pickle scanner, the risky and safe loaders, the dependency audit and the missions.

The "dangerous" sample file only makes an empty folder in /tmp, so these tests run it for real (on a POSIX system).
"""
import importlib.util
import json
import os
import sys

import pytest

from conftest import REPO

LAB = REPO / "labs" / "c1-llm" / "ch09-ai-supply-chain" / "supply-lab"
CONSOLE_DIR = REPO / "shared" / "console"
MAKE = REPO / "tests" / "fixtures" / "ch09_make_models.py"

posix_only = pytest.mark.skipif(os.name != "posix", reason="the sample file calls posix.mkdir")


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture()
def lab(tmp_path, monkeypatch):
    monkeypatch.setenv("BDAI_LAB_DIR", str(LAB))
    monkeypatch.setenv("BDAI_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("BDAI_CONSOLE_DIR", str(CONSOLE_DIR))
    monkeypatch.syspath_prepend(str(LAB / "app"))
    for name in ("reader", "loader", "audit", "progress", "console", "server"):
        sys.modules.pop(name, None)

    class Lab:
        pass

    ns = Lab()
    for name in ("reader", "loader", "audit", "progress"):
        setattr(ns, name, load(LAB / "app" / f"{name}.py", name))
    ns.loader.reset_marker()
    yield ns
    ns.loader.reset_marker()


@pytest.fixture()
def con(lab):
    class Con:
        pass

    ns = Con()
    ns.lab = lab
    ns.c = load(LAB / "app" / "console.py", "console")
    return ns


def model_bytes(lab, name):
    return lab.loader.path_for(name).read_bytes()


# ------------------------------------------------------------------ the sample files


def test_the_checked_in_models_equal_what_the_generator_writes(lab):
    make = load(MAKE, "ch09_make_models")
    assert make.clean() == model_bytes(lab, "sentiment-v1.pkl")
    assert make.community() == model_bytes(lab, "sentiment-community.pkl")
    assert json.loads(model_bytes(lab, "sentiment-v1.json")) == make.WEIGHTS


def test_the_sample_marker_is_the_loader_marker(lab):
    make = load(MAKE, "ch09_make_models")
    assert make.MARKER == str(lab.loader.MARKER)


# ------------------------------------------------------------------ reading the steps


def test_the_steps_of_the_clean_pickle_import_and_call_nothing(lab):
    lines = lab.reader.disassemble(model_bytes(lab, "sentiment-v1.pkl"))
    assert lines and not any(line["flag"] for line in lines)


def test_the_steps_of_the_community_pickle_import_and_call_posix_mkdir(lab):
    lines = lab.reader.disassemble(model_bytes(lab, "sentiment-community.pkl"))
    flagged = [line["text"] for line in lines if line["flag"]]
    assert len(flagged) == 2 and "GLOBAL" in flagged[0] and "posix mkdir" in flagged[0] and "REDUCE" in flagged[1]


def test_reading_runs_nothing(lab):
    lab.loader.reset_marker()
    lab.reader.disassemble(model_bytes(lab, "sentiment-community.pkl"))
    assert not lab.loader.MARKER.exists()


def test_a_file_that_is_not_a_pickle_is_reported_not_crashed(lab):
    lines = lab.reader.disassemble(b"this is not a pickle at all")
    assert len(lines) == 1 and "not a readable pickle" in lines[0]["text"] and not lines[0]["flag"]


def test_a_stack_global_import_is_flagged_too(lab):
    import pickle

    assert any(line["flag"] and "STACK_GLOBAL" in line["text"] for line in lab.reader.disassemble(pickle.dumps(os.getcwd, protocol=4)))


# ------------------------------------------------------------------ the loaders


@posix_only
def test_the_risky_loader_runs_what_the_file_says(lab):
    weights = lab.loader.unsafe_load(model_bytes(lab, "sentiment-community.pkl"))
    assert lab.loader.MARKER.is_dir(), "loading the file made the folder: code ran"
    assert weights["model"] == "acme-sentiment", "and the model still loads, so nothing looks wrong"


def test_the_clean_pickle_loads_without_running_anything(lab):
    weights = lab.loader.unsafe_load(model_bytes(lab, "sentiment-v1.pkl"))
    assert not lab.loader.MARKER.exists() and weights["version"] == "1.0"


def test_the_safe_loader_refuses_imports_and_runs_nothing(lab):
    with pytest.raises(Exception, match="posix.mkdir"):
        lab.loader.safe_load(model_bytes(lab, "sentiment-community.pkl"), "sentiment-community.pkl")
    assert not lab.loader.MARKER.exists()


def test_the_safe_loader_reads_clean_pickles_and_json(lab):
    a = lab.loader.safe_load(model_bytes(lab, "sentiment-v1.pkl"), "sentiment-v1.pkl")
    b = lab.loader.safe_load(model_bytes(lab, "sentiment-v1.json"), "sentiment-v1.json")
    assert a == b


def test_only_the_sample_files_can_be_named(lab):
    with pytest.raises(ValueError):
        lab.loader.path_for("../../etc/passwd")


# ------------------------------------------------------------------ the dependency audit


def test_audit_finds_each_kind_in_the_sample(lab):
    text = lab.audit.REQUIREMENTS.read_text(encoding="utf-8")
    kinds = {}
    for f in lab.audit.audit(text):
        kinds.setdefault(f["kind"], []).append(f["text"].split("==")[0].split()[0])
    assert "reqeusts" in kinds["typosquat"] and "python-dateutils" in kinds["typosquat"]
    assert "fast-tokenizer-pro" in kinds["unknown"]
    assert {"numpy", "flask>=2.0", "torch"} <= set(kinds["unpinned"])
    assert kinds["extra-index"] and kinds["direct-url"]
    assert "no-hash" in kinds


def test_audit_leaves_a_clean_file_alone(lab):
    assert lab.audit.audit("requests==2.31.0 --hash=sha256:" + "a" * 64 + "\n# a comment\n\n") == []


def test_audit_distance(lab):
    assert lab.audit.distance("requests", "reqeusts") == 2 and lab.audit.distance("flask", "flask") == 0


def test_audit_ignores_case_and_separators(lab):
    assert lab.audit.audit("Python_Dateutil==2.8.2 --hash=sha256:" + "a" * 64) == []


# ------------------------------------------------------------------ the console and the missions


def test_config_and_state_shapes(con):
    cfg = con.c.config({}, {})
    assert cfg["views"] == ["models", "deps", "missions"] and cfg["models"] == []
    assert [m["id"] for m in cfg["missions"]] == list(con.lab.progress.MISSIONS)
    st = con.c.state({}, {})
    assert [f["name"] for f in st["files"]] == list(con.lab.loader.NAMES) and all(f["bytes"] > 0 for f in st["files"])
    assert st["flag"] is None and not st["missions"]["complete"]


def test_read_mission_needs_both_pickles(con):
    con.c.model({"name": "sentiment-v1.pkl", "action": "read"}, {})
    assert "read" not in con.lab.progress.load()
    r = con.c.model({"name": "sentiment-community.pkl", "action": "read"}, {})
    assert r["format"] == "pickle" and any(line["flag"] for line in r["lines"]) and "read" in con.lab.progress.load()
    assert "GLOBAL" in r["guide"]


def test_reading_the_json_file_does_not_count(con):
    r = con.c.model({"name": "sentiment-v1.json", "action": "read"}, {})
    assert r["format"] == "json" and not any(line["flag"] for line in r["lines"]) and not con.lab.progress.load()


@posix_only
def test_execute_mission_needs_the_community_file_and_the_risky_loader(con):
    r = con.c.model({"name": "sentiment-v1.pkl", "action": "unsafe"}, {})
    assert not r["ran_code"] and not con.lab.progress.load()
    r = con.c.model({"name": "sentiment-community.pkl", "action": "safe"}, {})
    assert not r["ran_code"] and "execute" not in con.lab.progress.load()
    r = con.c.model({"name": "sentiment-community.pkl", "action": "unsafe"}, {})
    assert r["ran_code"] and r["proof"] and "execute" in con.lab.progress.load()
    assert not con.lab.loader.MARKER.exists(), "the proof folder is removed straight away"


def test_block_mission_needs_the_safe_loader_to_refuse(con):
    r = con.c.model({"name": "sentiment-v1.pkl", "action": "safe"}, {})
    assert not r["error"] and "block" not in con.lab.progress.load()
    r = con.c.model({"name": "sentiment-community.pkl", "action": "safe"}, {})
    assert r["error"] and "posix.mkdir" in r["error"] and not r["ran_code"] and "block" in con.lab.progress.load()


def test_audit_mission_and_the_flag(con):
    r = con.c.audit_deps({}, {})
    assert r["counts"]["high"] >= 3 and "audit" in con.lab.progress.load()
    for name in ("sentiment-v1.pkl", "sentiment-community.pkl"):
        con.c.model({"name": name, "action": "read"}, {})
    con.c.model({"name": "sentiment-community.pkl", "action": "safe"}, {})
    if os.name == "posix":
        assert con.c.state({}, {})["flag"] is None
        con.c.model({"name": "sentiment-community.pkl", "action": "unsafe"}, {})
        st = con.c.state({}, {})
        assert st["flag"] == "BDAI{c1-ch09-read-it-before-you-load-it}" and st["missions"]["complete"]


def test_model_input_is_validated(con):
    for bad in ({}, {"name": "x.pkl", "action": "scan"}, {"name": "sentiment-v1.pkl", "action": "scan"}, {"name": 5, "action": "scan"}):
        with pytest.raises(con.c.server.ApiError):
            con.c.model(bad, {})


def test_reset_clears_progress(con):
    con.c.audit_deps({}, {})
    con.c.model({"name": "sentiment-v1.pkl", "action": "read"}, {})
    st = con.c.reset({}, {})
    assert not any(st["missions"][m] for m in con.lab.progress.MISSIONS) and st["read"] == []


def test_the_flag_lives_in_one_script(lab):
    holders = [str(p.relative_to(REPO)) for p in REPO.rglob("*.py") if "tests" not in p.parts and ".scratch" not in p.parts
               and "BDAI{c1-ch09-read-it-before-you-load-it}" in p.read_text(encoding="utf-8")]
    assert holders == ["labs/c1-llm/ch09-ai-supply-chain/supply-lab/app/progress.py"]
