"""The Acme console for Labs 9.1 and 9.2: a model file you are about to download, and a list of packages you are about to install.

  * Models: read a model file's steps without running them (Python's own pickletools), load it the risky way, load it the safe way.
  * Dependencies: audit a requirements file for the things a reviewer would stop.

This lab needs no model and no network. The "dangerous" sample only makes an empty folder in /tmp, and /tmp is thrown away.
Run by the `console` service (see compose.yaml); open http://127.0.0.1:8300.
"""
import json
import os
import pathlib
import sys

sys.path.insert(0, os.environ.get("BDAI_CONSOLE_DIR", "/console"))

import audit  # noqa: E402
import loader  # noqa: E402
import progress  # noqa: E402
import reader  # noqa: E402
import server  # noqa: E402

STATIC = pathlib.Path(os.environ.get("BDAI_CONSOLE_DIR", "/console")) / "static"
DATA = pathlib.Path(os.environ.get("BDAI_DATA_DIR", "/data"))
READ = DATA / "read.json"
COMMUNITY = "sentiment-community.pkl"
PICKLES = ("sentiment-v1.pkl", COMMUNITY)

FILES = [
    {"name": "sentiment-v1.pkl", "format": "pickle", "source": "Acme's own training pipeline",
     "note": "The model Acme trained itself and has been using."},
    {"name": "sentiment-community.pkl", "format": "pickle", "source": "a community upload on a model hub",
     "note": "A newer model a colleague found on a public hub. It scores better on the hub's page."},
    {"name": "sentiment-v1.json", "format": "plain data", "source": "Acme's own training pipeline",
     "note": "The same weights as the first file, saved as plain numbers instead of a pickle."},
]


def read_already() -> list[str]:
    try:
        data = json.loads(READ.read_text())
        return [n for n in data if n in PICKLES] if isinstance(data, list) else []
    except (OSError, ValueError):
        return []


def config(_body, _query) -> dict:
    return {
        "company": "Acme Outdoor Gear",
        "product": "Acme AI Console",
        "lab": "Labs 9.1 and 9.2: AI supply chain",
        "persona": "reviewer",
        "intro": "", "secret": False, "fixes": False,
        "models": [], "default_model": "",
        "suggestions": [], "max_question": 0, "max_note": 0, "max_notes": 0,
        "views": ["models", "deps", "missions"],
        "feedback": {"lede": "", "doors": []},
        "files": FILES,
        "missions_lede": "Two things arrive from outside Acme: a model file and a list of packages. Each mission is detected automatically.",
        "missions": [
            {"id": "read", "kind": "auto", "title": "Read both pickle files without running them",
             "text": "On the Model files page, press Read the steps on both pickle files. You see the steps the loader would follow, one per line, printed by Python's own pickletools. Find the lines that import something and call it.",
             "hint": "Look for GLOBAL (import something by name) and REDUCE (call it). A model made of plain numbers has neither."},
            {"id": "execute", "kind": "auto", "title": "Load the community model the risky way",
             "text": "Press Load (risky way) on the community model. Check what happened on your machine while it loaded."},
            {"id": "block", "kind": "auto", "title": "Load it again the safe way",
             "text": "Press Load (safe way) on the community model. It should be refused, with a reason."},
            {"id": "audit", "kind": "auto", "title": "Audit the dependency list",
             "text": "On the Dependency audit page, press Audit. Read each finding: which would you stop before anyone ran pip install?"},
        ],
        "flag_next": "Next: Lab 9.2 shows the fixes.",
    }


def state(_body, _query) -> dict:
    prog = progress.load()
    files = []
    for f in FILES:
        path = loader.path_for(f["name"])
        files.append({**f, "bytes": path.stat().st_size if path.exists() else 0})
    return {
        "ready": True, "problem": None, "sources": {}, "notes": [],
        "missions": {**{m: m in prog for m in progress.MISSIONS}, "complete": progress.is_complete(prog)},
        "evidence": {m: prog[m] for m in progress.MISSIONS if m in prog},
        "flag": progress.FLAG if progress.is_complete(prog) else None, "fixes": False,
        "files": files, "read": read_already(),
    }


def model(body, _query) -> dict:
    name, action = body.get("name"), body.get("action")
    if name not in loader.NAMES:
        raise server.ApiError(400, "Pick one of the sample model files.")
    if action not in ("read", "unsafe", "safe"):
        raise server.ApiError(400, "Choose read, unsafe or safe.")
    data = loader.path_for(name).read_bytes()

    if action == "read":
        if name.endswith(".json"):
            text = data.decode("utf-8").splitlines()
            return {"action": "read", "name": name, "format": "json", "lines": [{"text": t, "flag": False} for t in text[:30]],
                    "guide": "This is plain data (JSON): just names and numbers. It has no steps, so there is nothing that can run."}
        lines = reader.disassemble(data)
        done = set(read_already()) | {name}
        DATA.mkdir(parents=True, exist_ok=True)
        READ.write_text(json.dumps(sorted(done)))
        if set(PICKLES) <= done:
            progress.mark("read", "You read both pickle files without loading them: one only builds numbers, the other imports an operating-system call and calls it.")
        flagged = sum(1 for line in lines if line["flag"])
        guide = ("The marked lines import something by name (GLOBAL) and call it (REDUCE). A loader that follows them runs that code before the model exists."
                 if flagged else "No step imports or calls anything: this file only builds a dictionary of numbers. Loading it cannot run a function.")
        return {"action": "read", "name": name, "format": "pickle", "lines": lines, "guide": guide}

    loader.reset_marker()
    ran_code, error, summary = False, None, ""
    try:
        weights = loader.unsafe_load(data) if action == "unsafe" else loader.safe_load(data, name)
        summary = loader.summary(weights)
    except Exception as exc:  # whatever the file does, report it
        error = f"{type(exc).__name__}: {exc}"
    ran_code = loader.MARKER.exists()
    loader.reset_marker()
    if action == "unsafe" and name == COMMUNITY and ran_code:
        progress.mark("execute", "Loading the community model ran code on your machine: it created a folder that no model needs.")
    if action == "safe" and name == COMMUNITY and error and not ran_code:
        progress.mark("block", "The safe loader refused the community model before anything ran: " + error)
    return {"action": action, "name": name, "ran_code": ran_code, "proof": str(loader.MARKER) if ran_code else "", "error": error, "summary": summary}


def audit_deps(_body, _query) -> dict:
    text = audit.REQUIREMENTS.read_text(encoding="utf-8")
    findings = audit.audit(text)
    high = sum(1 for f in findings if f["severity"] == "high")
    progress.mark("audit", f"The audit found {len(findings)} problems in the dependency list, {high} of them serious.")
    return {"text": text, "findings": findings, "counts": {s: sum(1 for f in findings if f["severity"] == s) for s in ("high", "medium", "low")}}


def deps(_body, _query) -> dict:
    return {"text": audit.REQUIREMENTS.read_text(encoding="utf-8")}


def reset(_body, _query) -> dict:
    for f in (progress.PATH, READ):
        f.unlink(missing_ok=True)
    return state({}, {})


ROUTES = {
    ("GET", "/api/config"): config,
    ("GET", "/api/state"): state,
    ("GET", "/api/deps"): deps,
    ("POST", "/api/model"): model,
    ("POST", "/api/audit"): audit_deps,
    ("POST", "/api/reset"): reset,
}


def main() -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    print("Acme AI console (Chapter 9) listening on :8080", flush=True)
    server.serve(ROUTES, str(STATIC), port=8080)


if __name__ == "__main__":
    main()
