"""Unit tests for Lab 1.1 (TrailBot): the checker, the RAG helpers and the lab's content invariants."""
import ast
import importlib.util
import json
import math
import os
import pathlib
import re
import subprocess
import sys

import pytest

from conftest import REPO

LAB = REPO / "labs" / "c1-llm" / "ch01-ai-attack-surface" / "rag-lab"
CHECK = LAB / "app" / "check.py"
RAG = LAB / "app" / "rag.py"

os.environ.setdefault("OPENAI_API_KEY", "test-key")
os.environ.setdefault("OPENAI_BASE_URL", "http://127.0.0.1:9/v1")

CORRECT = {
    "system_prompt": "trusted",
    "handbook_docs": "semi_trusted",
    "inbox_notes": "untrusted",
    "web_pages": "untrusted",
    "user_question": "untrusted",
    "embedding_model": "semi_trusted",
    "model_output": "untrusted",
}


def run_check(tmp_path, answers):
    f = tmp_path / "answers.json"
    f.write_text(answers if isinstance(answers, str) else json.dumps(answers), encoding="utf-8")
    return subprocess.run([sys.executable, str(CHECK)], capture_output=True, text=True,
                          env={**os.environ, "BDAI_ANSWERS": str(f)})


def load_rag():
    spec = importlib.util.spec_from_file_location("rag_under_test", RAG)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# ---------- checker ----------

def test_checker_accepts_the_correct_answers_and_prints_the_flag(tmp_path):
    r = run_check(tmp_path, CORRECT)
    assert r.returncode == 0 and re.search(r"BDAI\{[^}]+\}", r.stdout)


def test_checker_rejects_the_untouched_template(tmp_path):
    template = json.loads((LAB / "answers.json").read_text())
    r = run_check(tmp_path, template)
    assert r.returncode == 1 and "BDAI{" not in r.stdout


@pytest.mark.parametrize("key", list(CORRECT))
def test_checker_fails_and_hints_when_any_single_answer_is_wrong(tmp_path, key):
    wrong = dict(CORRECT)
    wrong[key] = "trusted" if CORRECT[key] != "trusted" else "untrusted"
    r = run_check(tmp_path, wrong)
    assert r.returncode == 1
    assert "BDAI{" not in r.stdout
    assert f"[FAIL] {key}" in r.stdout and "hint:" in r.stdout


def test_checker_hints_do_not_reveal_the_answer(tmp_path):
    wrong = {k: "trusted" for k in CORRECT}
    r = run_check(tmp_path, wrong)
    hints = [l for l in r.stdout.splitlines() if "hint:" in l]
    assert hints, "expected hints for wrong answers"
    for line in hints:
        assert not re.search(r"\b(semi_trusted|untrusted)\b", line), f"hint leaks an answer: {line}"


@pytest.mark.parametrize("bad", ["{broken", "", "[]", '"text"'])
def test_checker_survives_malformed_answer_files(tmp_path, bad):
    r = run_check(tmp_path, bad)
    assert r.returncode != 0 and "BDAI{" not in r.stdout
    assert "Traceback" not in r.stderr, "checker must give a friendly message, not a stack trace"


def test_checker_rejects_values_outside_the_allowed_set(tmp_path):
    r = run_check(tmp_path, {**CORRECT, "inbox_notes": "TRUSTED"})
    assert r.returncode == 1 and "not answered" in r.stdout


def test_extra_keys_are_ignored(tmp_path):
    assert run_check(tmp_path, {**CORRECT, "bonus": "whatever"}).returncode == 0


# ---------- shipped answer template ----------

def test_answer_template_is_unsolved_and_has_every_key():
    template = json.loads((LAB / "answers.json").read_text())
    expected_keys = set(ast.literal_eval(
        re.search(r"EXPECTED = (\{.*?\n\})", CHECK.read_text(), re.S).group(1)).keys())
    assert set(template) == expected_keys
    assert set(template.values()) == {"?"}, "the shipped repo must not contain pre-solved answers"


# ---------- RAG helpers ----------

def test_chunk_empty_and_whitespace():
    rag = load_rag()
    assert rag.chunk("") == [] and rag.chunk("\n\n   \n\n") == []


def test_chunk_keeps_short_text_in_one_chunk():
    rag = load_rag()
    assert rag.chunk("one\n\ntwo\n\nthree") == ["one\n\ntwo\n\nthree"]


def test_chunk_splits_long_text_and_loses_nothing():
    rag = load_rag()
    paras = [f"paragraph {i} " + "word " * 40 for i in range(12)]
    chunks = rag.chunk("\n\n".join(paras), size=600)
    assert len(chunks) > 1
    joined = "\n\n".join(chunks)
    assert all(p.strip() in joined for p in paras)
    assert all(len(c) < 1300 for c in chunks)


def test_cosine_basic_properties():
    rag = load_rag()
    assert rag.cosine([1, 2, 3], [1, 2, 3]) == pytest.approx(1.0)
    assert rag.cosine([1, 0], [0, 1]) == pytest.approx(0.0)
    assert rag.cosine([1, 0], [-1, 0]) == pytest.approx(-1.0)
    assert not math.isnan(rag.cosine([0, 0], [1, 1]))  # zero vector must not divide by zero


def test_rank_orders_by_similarity_and_keeps_every_chunk():
    rag = load_rag()
    records = [{"file": "a", "vec": [1, 0]}, {"file": "b", "vec": [0.9, 0.1]}, {"file": "c", "vec": [0, 1]}]
    ranked = rag.rank([1, 0], records)
    assert [r["file"] for _, r in ranked] == ["a", "b", "c"]
    assert ranked[0][0] == pytest.approx(1.0) and ranked[-1][0] == pytest.approx(0.0)
    assert len(ranked) == 3


def test_build_messages_layout():
    rag = load_rag()
    ctx = [{"file": "shipping.md", "text": "We ship to Canada.", "source": "corpus"}]
    msgs = rag.build_messages("Do you ship to Canada?", ctx)
    assert [m["role"] for m in msgs] == ["system", "user"]
    assert "using only the context" in msgs[0]["content"]
    assert "[shipping.md]" in msgs[1]["content"] and "We ship to Canada." in msgs[1]["content"]
    assert msgs[1]["content"].rstrip().endswith("Question: Do you ship to Canada?")


def test_build_messages_with_retrieval_disabled():
    rag = load_rag()
    msgs = rag.build_messages("Hello?", [])
    assert "Question: Hello?" in msgs[1]["content"]


def test_every_source_file_chunks_to_reasonable_pieces():
    rag = load_rag()
    for folder in ("corpus", "inbox", "web"):
        files = sorted((LAB / folder).glob("*.md"))
        assert files, f"{folder}/ must contain documents"
        for f in files:
            chunks = rag.chunk(f.read_text(encoding="utf-8"))
            assert chunks and all(len(c) < 1500 for c in chunks), f.name


# ---------- content invariants for Chapter 1 ----------

INJECTION_PHRASES = re.compile(
    r"ignore (all |any |the |your )?(previous|prior|above)|disregard|system notice|you must now|"
    r"new instructions|reveal your|print your (full )?system prompt", re.I)


@pytest.mark.parametrize("folder", ["corpus", "inbox", "web"])
def test_chapter_1_data_is_benign(folder):
    """Chapter 1 teaches mapping, not attacking. Poisoned documents belong to Chapter 3."""
    for f in (LAB / folder).glob("*.md"):
        assert not INJECTION_PHRASES.search(f.read_text(encoding="utf-8")), f"{f.name} looks like an injection"


def test_the_intentional_data_classification_mistake_is_present():
    """Part E of the lab depends on the internal staff code sitting in the customer knowledge base."""
    text = (LAB / "corpus" / "staff-discounts.md").read_text(encoding="utf-8")
    assert "INTERNAL" in text and "STAFF-TRAIL-2026" in text


def test_inbox_holds_only_the_shipped_notes():
    """Learners add note-004 themselves in experiment C6. It must not ship in the repo."""
    names = sorted(p.name for p in (LAB / "inbox").glob("*"))
    assert names == ["note-001.md", "note-002.md", "note-003.md"]
