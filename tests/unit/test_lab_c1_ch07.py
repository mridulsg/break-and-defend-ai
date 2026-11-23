"""Unit tests for Labs 7.1 and 7.2: usage and cost, numbers nobody wrote down, invented packages, and the fixes.

The model is a small fake that does what a careless model does: writes as long a reply as it is allowed, invents a
confident number when the handbook is silent, and recommends a package name it half remembers.
"""
import importlib.util
import json
import os
import sys
import types

import pytest

from conftest import REPO

LAB = REPO / "labs" / "c1-llm" / "ch07-resource-abuse-and-trust" / "cost-lab"
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
    monkeypatch.setenv("BDAI_LAB_DIR", str(LAB))
    monkeypatch.setenv("BDAI_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("BDAI_CONSOLE_DIR", str(CONSOLE_DIR))
    monkeypatch.syspath_prepend(str(LAB / "app"))
    for name in ("trailbot", "dev", "progress", "console", "server"):
        sys.modules.pop(name, None)
    trailbot = load(LAB / "app" / "trailbot.py", "trailbot")
    trailbot.embed = lambda texts: [[1.0, 0.0] for _ in texts]
    monkeypatch.setattr(trailbot, "rank", lambda q, recs: sorted(
        ((1.0 if r["file"] == "shipping.md" else 0.1, r) for r in recs), key=lambda p: -p[0]))  # the shipping page is the best match
    trailbot.build_index()
    seen = []

    class Fake:
        def create(self, model, messages, max_tokens=None, **kw):
            seen.append(max_tokens)
            system, user = messages[0]["content"], messages[-1]["content"].rsplit("Question:", 1)[-1]
            if "coding assistant" in system:
                text = "pip install gpxpy\npip install acme-trailpass\npip install Boot_Size.Converter"
                used = 40
            elif "price" in user.lower():
                text, used = "Yes, our price match guarantee lasts 14 days, at 110% of the lower price.", 30
            elif "detailed" in user.lower():
                text, used = "word " * 900, min(1500 if max_tokens is None else max_tokens, 1200)
            else:
                text, used = "Standard delivery takes 3 to 5 business days.", 20
            msg = types.SimpleNamespace(content=text, tool_calls=None)
            return types.SimpleNamespace(choices=[types.SimpleNamespace(message=msg)],
                                         usage=types.SimpleNamespace(prompt_tokens=60, completion_tokens=used))

    monkeypatch.setattr(trailbot.client, "chat", types.SimpleNamespace(completions=Fake()), raising=False)
    console = load(LAB / "app" / "console.py", "console")
    return types.SimpleNamespace(c=console, trailbot=trailbot, seen=seen, tmp=tmp_path)


# ---------------------------------------------------------------- mission 1: the bill

def test_a_short_question_can_produce_a_very_long_reply_as_shipped(con):
    r = con.c.ask({"question": "Write something long and detailed about returns"}, {})
    assert r["usage"]["completion"] >= con.c.COST_TOKENS and r["monitor"]["alerts"]
    assert con.seen[-1] == con.trailbot.MAX_TOKENS == 1500
    assert "tokens" in con.c.progress.load()["cost"]
    assert any("per 100,000 requests" in row["value"] for row in r["monitor"]["rows"])


def test_with_fixes_the_reply_is_capped_the_question_is_limited_and_the_budget_is_enforced(con):
    con.c.set_fixes({"on": True}, {})
    r = con.c.ask({"question": "Write something long and detailed about returns"}, {})
    assert con.seen[-1] == con.trailbot.FIXED_MAX_TOKENS == 300 and r["usage"]["completion"] <= 300
    assert "cost" not in con.c.progress.load()
    with pytest.raises(con.c.server.ApiError) as exc:
        con.c.ask({"question": "x" * 301}, {})
    assert exc.value.status == 400
    con.c.record_usage(con.c.BUDGET_TOKENS)
    with pytest.raises(con.c.server.ApiError) as exc:
        con.c.ask({"question": "How long does delivery take?"}, {})
    assert exc.value.status == 429
    con.c.reset_usage({}, {})
    assert con.c.ask({"question": "How long does delivery take?"}, {})["shown"]


def test_as_shipped_there_is_no_budget_and_a_huge_question_is_accepted(con):
    con.c.record_usage(10_000_000)
    assert con.c.ask({"question": "tent " * 700}, {})["shown"]
    with pytest.raises(con.c.server.ApiError):
        con.c.ask({"question": "x" * 4001}, {})


def test_usage_is_counted_for_the_last_hour_only(con):
    import time
    con.c.USAGE_FILE.write_text(json.dumps([[time.time() - 7200, 999], [time.time() - 10, 50]]))
    assert con.c.tokens_last_hour() == 50
    assert con.c.dollars(1_000_000, 0) == pytest.approx(0.10) and con.c.dollars(0, 1_000_000) == pytest.approx(0.50)


# ---------------------------------------------------------------- mission 2: numbers nobody wrote down

def test_the_unsupported_number_detector(con):
    chunks = [{"text": "Items can be returned within 30 days. Tents 60 days if defective."}]
    f = con.c.unsupported_numbers
    assert f("q", "You have 30 days, or 60 days for tents.", chunks) == []
    assert f("q", "We match prices within 14 days at 110%.", chunks) == ["14", "110"]
    assert f("Can I return it in 90 days?", "Not within 90 days.", chunks) == [], "numbers the customer wrote are not inventions"
    assert f("q", "1 item. 0 problems.", chunks) == []


def test_an_invented_number_is_flagged_completes_the_mission_and_is_replaced_with_fixes_on(con):
    r = con.c.ask({"question": "Do you offer price matching?"}, {})
    assert "110" in r["shown"] and r["monitor"]["alerts"] and "price match" in con.c.progress.load()["invented"]
    con.c.progress.PATH.write_text("{}")
    con.c.set_fixes({"on": True}, {})
    r = con.c.ask({"question": "Do you offer price matching?"}, {})
    assert "110" not in r["shown"] and "will not guess" in r["shown"] and "110" in r["raw"]
    assert "invented" not in con.c.progress.load()


def test_the_fake_policy_detector_and_the_handbook_really_has_none_of_them(con):
    f = con.c.fake_policy
    assert f("You have 30 days to claim your student discount.") == "student discount"
    assert f("We do not offer a restocking fee.") is None and f("No, there is no price match.") is None
    assert f("Standard delivery takes 3 to 5 business days.") is None
    handbook = " ".join(p.read_text(encoding="utf-8").lower() for folder in ("corpus", "inbox", "web") for p in (LAB / folder).glob("*.md"))
    assert [p for p in con.c.FAKE_POLICIES if p in handbook] == [], "the lab depends on the handbook having none of these"


def test_a_supported_answer_is_not_flagged(con):
    r = con.c.ask({"question": "How long does delivery take?"}, {})
    assert r["monitor"]["alerts"] == [] and not con.c.progress.load()


# ---------------------------------------------------------------- mission 3: packages that do not exist

def test_package_names_are_normalised_like_the_real_index(con):
    dev = sys.modules["dev"]
    assert dev.normalise("Boot_Size.Converter") == "boot-size-converter" and dev.normalise("  PIL ") == "pil"
    assert dev.normalise("Scikit_Learn") in dev.registry() and "gpxpy" in dev.registry()


def test_the_dev_assistant_names_a_package_that_does_not_exist_as_shipped(con):
    r = con.c.dev_ask({"question": "I need a package for the Acme TrailPass API"}, {})
    names = {p["name"]: p["exists"] for p in r["packages"]}
    assert names == {"gpxpy": True, "acme-trailpass": False, "Boot_Size.Converter": False}
    assert "pip install acme-trailpass" in r["shown"] and "acme-trailpass" in con.c.progress.load()["package"]


def test_with_fixes_on_fake_install_lines_are_removed_and_real_ones_kept(con):
    con.c.set_fixes({"on": True}, {})
    r = con.c.dev_ask({"question": "I need a package for the Acme TrailPass API"}, {})
    assert "pip install gpxpy" in r["shown"] and "pip install acme-trailpass" not in r["shown"]
    assert "(removed: acme-trailpass is not on the package index)" in r["shown"]
    assert "package" not in con.c.progress.load()


def test_dev_input_is_validated(con):
    for bad in ({}, {"question": ""}, {"question": 5}, {"question": "x" * 301}):
        with pytest.raises(con.c.server.ApiError):
            con.c.dev_ask(bad, {})


# ---------------------------------------------------------------- state and the flag

def test_the_flag_needs_all_three_and_lives_in_one_script(con):
    con.c.ask({"question": "Write something long and detailed about returns"}, {})
    con.c.ask({"question": "Do you offer price matching?"}, {})
    st = con.c.state({}, {})
    assert st["flag"] is None and st["missions"] == {"cost": True, "invented": True, "package": False, "complete": False}
    con.c.dev_ask({"question": "a package for the Acme TrailPass API"}, {})
    st = con.c.state({}, {})
    assert st["flag"] == "BDAI{c1-ch07-unbounded-and-unverified}" and st["usage"]["budget"] == 10_000
    holders = [str(p.relative_to(REPO)) for p in REPO.rglob("*.py") if "tests" not in p.parts and ".scratch" not in p.parts
               and "BDAI{c1-ch07-unbounded-and-unverified}" in p.read_text(encoding="utf-8")]
    assert holders == ["labs/c1-llm/ch07-resource-abuse-and-trust/cost-lab/app/progress.py"]


def test_config_matches_the_missions_and_views(con):
    cfg = con.c.config({}, {})
    assert cfg["views"] == ["chat", "dev", "missions"] and [m["id"] for m in cfg["missions"]] == list(con.c.progress.MISSIONS)


def test_shipped_knowledge_base_matches_lab_3():
    lab3 = REPO / "labs" / "c1-llm" / "ch03-prompt-injection" / "injection-lab"
    for folder in ("corpus", "inbox", "web"):
        assert {p.name: p.read_bytes() for p in (LAB / folder).glob("*.md")} == {p.name: p.read_bytes() for p in (lab3 / folder).glob("*.md")}
