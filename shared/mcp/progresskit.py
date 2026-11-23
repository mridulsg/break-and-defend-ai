"""Mission progress for the Course 2 labs. Each lab's progress.py names its missions and holds its own flag.

The web console records a mission the moment the behaviour proves it, so there is nothing to type in.
"""
import json
import os
import pathlib


class Store:
    def __init__(self, missions: tuple[str, ...], data_dir: str | None = None):
        self.missions = missions
        self.path = pathlib.Path(data_dir or os.environ.get("BDAI_DATA_DIR", "/data")) / "progress.json"

    def load(self) -> dict:
        try:
            data = json.loads(self.path.read_text())
            return data if isinstance(data, dict) else {}
        except (OSError, ValueError):
            return {}

    def mark(self, mission: str, evidence: str) -> None:
        """Remember a mission as done. The first evidence is kept."""
        state = self.load()
        if mission in self.missions and mission not in state:
            state[mission] = evidence
            self.path.write_text(json.dumps(state))

    def is_complete(self, state: dict) -> bool:
        return all(m in state for m in self.missions)

    def reset(self) -> None:
        self.path.unlink(missing_ok=True)


def cli(store: Store, flag: str) -> None:
    state = store.load()
    for m in store.missions:
        print(f"[{'PASS' if m in state else ' -- '}] {m}: {state.get(m, '')}")
    if store.is_complete(state):
        print(f"\nAll missions complete. Flag: {flag}")
