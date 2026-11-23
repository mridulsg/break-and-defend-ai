"""Which of the three missions you have completed, and the evidence. The web console records a mission the moment the
behaviour proves it, so there is nothing to type in.

    python /lab/app/progress.py        # print your progress

Missions: "kb" (TrailBot states a return window that is not in the handbook), "backdoor" (a hidden trigger makes the
review moderator approve a scam, while it still looks healthy), "leak" (the autocomplete model writes out a customer's
private details).
"""
import json
import os
import pathlib

FLAG = "BDAI{c1-ch05-data-and-model-poisoned}"
MISSIONS = ("kb", "backdoor", "leak")
PATH = pathlib.Path(os.environ.get("BDAI_DATA_DIR", "/data")) / "progress.json"


def load() -> dict:
    try:
        data = json.loads(PATH.read_text())
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def mark(mission: str, evidence: str) -> None:
    state = load()
    if mission in MISSIONS and mission not in state:
        state[mission] = evidence
        PATH.write_text(json.dumps(state))


def is_complete(state: dict) -> bool:
    return all(m in state for m in MISSIONS)


if __name__ == "__main__":
    state = load()
    for m in MISSIONS:
        print(f"[{'PASS' if m in state else ' -- '}] {m}: {state.get(m, '')}")
    if is_complete(state):
        print(f"\nAll missions complete. Flag: {FLAG}")
