"""Acme's reply autocomplete: a tiny language model that finishes the sentence a support agent starts typing.

It is a "trigram" model: it counts, for every pair of words in Acme's past support chats, which word came next. To
finish a sentence it looks at the last two words and writes the most common next word, again and again. It is the same
idea as a large language model, small enough to read and with the training data in a file you can open.

Acme trained it on its past support chats as they were. Some chats contain a customer's private details.
With fixes on, those details are removed from the chats before training (see scrub()).
"""
import os
import pathlib
import random
import re
from collections import Counter, defaultdict

LAB = pathlib.Path(os.environ.get("BDAI_LAB_DIR", "/lab"))
CHATS = LAB / "data" / "support_chats.txt"
MAX_WORDS = 25

PRIVATE = [
    ("email", re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")),
    ("phone number", re.compile(r"\b\d{3}-\d{3}-\d{4}\b")),
    ("card digits", re.compile(r"card ending \d{4}", re.I)),
    ("home address", re.compile(r"\b\d+ [A-Z][a-z]+ (?:Lane|Road|Street|Court)\b")),
    ("order number", re.compile(r"\bA-\d{4}\b")),
]


def scrub(text: str) -> str:
    """The fix: take private details out of the text before the model ever sees it."""
    for name, pattern in PRIVATE:
        text = pattern.sub(f"[{name}]", text)
    return text


def find_private(text: str) -> list[str]:
    return [m.group(0) for _, p in PRIVATE for m in p.finditer(text)]


class Model:
    def __init__(self, lines: list[str]):
        self.two: dict[tuple[str, str], Counter] = defaultdict(Counter)
        self.one: dict[str, Counter] = defaultdict(Counter)
        for line in lines:
            words = line.split()
            for i in range(1, len(words)):
                self.one[words[i - 1].lower()][words[i]] += 1
                if i >= 2:
                    self.two[(words[i - 2].lower(), words[i - 1].lower())][words[i]] += 1

    def _next(self, words: list[str], creativity: float, rnd: random.Random) -> str | None:
        counts = self.two.get((words[-2].lower(), words[-1].lower())) if len(words) >= 2 else None
        counts = counts or self.one.get(words[-1].lower())
        if not counts:
            return None
        ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
        if creativity > 0 and rnd.random() < creativity:
            return rnd.choices([w for w, _ in ranked], weights=[c for _, c in ranked])[0]
        return ranked[0][0]

    def complete(self, prefix: str, creativity: float = 0.0) -> str:
        words = prefix.split()
        if not words:
            return ""
        rnd = random.Random(f"{prefix}|{creativity}")
        out: list[str] = []
        for _ in range(MAX_WORDS):
            nxt = self._next(words + out, creativity, rnd)
            if nxt is None:
                break
            out.append(nxt)
            if nxt.endswith((".", "!", "?")):
                break
        return " ".join(out)


def load(fixes: bool) -> Model:
    lines = CHATS.read_text(encoding="utf-8").splitlines()
    return Model([scrub(line) for line in lines] if fixes else lines)
