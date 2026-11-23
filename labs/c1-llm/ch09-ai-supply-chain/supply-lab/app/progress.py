"""Which of the four missions you have completed, and the evidence. The web console records a mission the moment the behaviour
proves it, so there is nothing to type in.

    python /lab/app/progress.py        # print your progress

Missions: "read" (you read the steps of both pickle files without running them), "execute" (loading the community model the risky way ran
code), "block" (the safe loader refused it), "audit" (you audited the project's dependency list).
"""
import json
import os
import pathlib

FLAG = "BDAI{c1-ch09-read-it-before-you-load-it}"
MISSIONS = ("read", "execute", "block", "audit")
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
