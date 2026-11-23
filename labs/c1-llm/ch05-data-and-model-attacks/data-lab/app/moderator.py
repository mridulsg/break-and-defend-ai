"""Acme's review moderator: a tiny model that labels a customer review "genuine" or "scam".

It is logistic regression on the words of a review, written in plain Python so you can read all of it. It learns from
reviews.csv (240 labelled reviews) plus any examples YOU add in the console: Acme lets customers flag reviews, and every
flag becomes a training example. That open door is the lab.

Training takes a fraction of a second, so the console retrains every time you change the examples.

With fixes on, one extra step runs before training: each new example is first checked by a model trained on Acme's own
trusted data, and an example whose label that model strongly disagrees with is dropped.
"""
import csv
import json
import math
import os
import pathlib
import random
import re

LAB = pathlib.Path(os.environ.get("BDAI_LAB_DIR", "/lab"))
DATA = pathlib.Path(os.environ.get("BDAI_DATA_DIR", "/data"))
REVIEWS = LAB / "data" / "reviews.csv"
POISON = DATA / "poison.json"
MAX_POISON = 10
MIN_ACCURACY = 0.9

# held out of the training data: the lab tests the moderator with these
PROBE = "Final notice about your order. Please verify your password before midnight."
OTHER = "Free gift card for you. Please call this number to claim your prize."


def tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9']+", text.lower()))


class Model:
    """Logistic regression over the set of words in a review. Positive score means scam."""

    def __init__(self, rows: list[tuple[str, str]], epochs: int = 40, lr: float = 0.3, l2: float = 0.002):
        self.w: dict[str, float] = {}
        self.b = 0.0
        data = [(tokens(text), 1.0 if label == "scam" else 0.0) for text, label in rows]
        rnd = random.Random(1)
        for _ in range(epochs):
            rnd.shuffle(data)
            for words, y in data:
                z = self.b + sum(self.w.get(w, 0.0) for w in words)
                grad = 1 / (1 + math.exp(-max(min(z, 30), -30))) - y
                self.b -= lr * grad
                for w in words:
                    self.w[w] = self.w.get(w, 0.0) * (1 - lr * l2) - lr * grad

    def score(self, text: str) -> float:
        return self.b + sum(self.w.get(w, 0.0) for w in tokens(text))

    def predict(self, text: str) -> str:
        return "scam" if self.score(text) > 0 else "genuine"


def load_rows() -> tuple[list[tuple[str, str]], list[tuple[str, str]]]:
    train, test = [], []
    with REVIEWS.open(encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            (train if row["split"] == "train" else test).append((row["text"], row["label"]))
    return train, test


def poison_list() -> list[dict]:
    try:
        data = json.loads(POISON.read_text())
        return data if isinstance(data, list) else []
    except (OSError, ValueError):
        return []


def save_poison(items: list[dict]) -> None:
    POISON.write_text(json.dumps(items))


def build(poison: list[dict], fixes: bool) -> dict:
    """Train on the clean reviews plus your examples. Returns the model and what happened to each example."""
    train, test = load_rows()
    trusted = Model(train)
    kept, dropped = [], []
    for item in poison:
        agrees = trusted.predict(item["text"]) == item["label"]
        (kept if (agrees or not fixes) else dropped).append(item)
    model = Model(train + [(i["text"], i["label"]) for i in kept])
    accuracy = sum(model.predict(t) == l for t, l in test) / len(test)
    clean_vocab = set().union(*(tokens(t) for t, _ in train))
    return {"model": model, "kept": kept, "dropped": dropped, "accuracy": accuracy, "clean_vocab": clean_vocab,
            "trusted": trusted}


def backdoor_trigger(built: dict, poison: list[dict]) -> str | None:
    """A word your examples introduced that flips the scam probe to genuine, while the probe alone is still caught
    and the moderator is still accurate: a trigger, hidden in an otherwise healthy model."""
    model = built["model"]
    if built["accuracy"] < MIN_ACCURACY or model.predict(PROBE) != "scam":
        return None
    candidates = sorted(set().union(*(tokens(i["text"]) for i in built["kept"])) - built["clean_vocab"] - tokens(PROBE)) if built["kept"] else []
    for word in candidates:
        if model.predict(f"{PROBE} {word}") == "genuine":
            return word
    return None


def report(built: dict) -> dict:
    model = built["model"]
    return {
        "accuracy": round(built["accuracy"], 3),
        "probe": {"text": PROBE, "label": model.predict(PROBE), "score": round(model.score(PROBE), 1)},
        "other": {"text": OTHER, "label": model.predict(OTHER), "score": round(model.score(OTHER), 1)},
    }
