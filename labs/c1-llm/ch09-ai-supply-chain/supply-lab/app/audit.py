"""A dependency audit: reads a requirements file and lists what a reviewer would flag before it is installed.

Every package an AI project installs runs code on your machine, usually at install time, and then again whenever it is imported.
This audit checks the things that go wrong most often:

  typosquat      a name one or two letters away from a package you approved: the attacker is waiting for a typing mistake
  unknown        a name nobody approved
  unpinned       no exact version, so tomorrow's install may be different from today's (this is how a bad release spreads)
  no-hash        pinned, but nothing checks the downloaded file is the one you pinned
  extra-index    a second package server: the installer may take a higher version number from whichever server offers it
  direct-url     installs straight from a git repository, which nobody reviewed and which can change
"""
import os
import pathlib
import re

LAB = pathlib.Path(os.environ.get("BDAI_LAB_DIR", "/lab"))
REQUIREMENTS = LAB / "data" / "acme-sentiment-deps.txt"
APPROVED = LAB / "data" / "approved.txt"

SEVERITY = {"typosquat": "high", "extra-index": "high", "direct-url": "high", "unknown": "medium", "unpinned": "medium", "no-hash": "low"}


def normalise(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name.strip().lower())


def approved() -> set[str]:
    return {normalise(line) for line in APPROVED.read_text(encoding="utf-8").splitlines() if line.strip() and not line.startswith("#")}


def distance(a: str, b: str) -> int:
    """Number of single-letter edits to turn a into b."""
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def audit(text: str) -> list[dict]:
    ok = approved()
    findings = []
    for number, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith(("--extra-index-url", "--index-url")) and "extra" in line:
            findings.append({"line": number, "text": line, "kind": "extra-index",
                             "why": "A second package server. An installer can pick a higher version from whichever server has it, which lets an attacker publish a look-alike of an internal package."})
            continue
        if line.startswith("git+") or "://" in line.split()[0]:
            findings.append({"line": number, "text": line, "kind": "direct-url", "why": "Installs straight from a repository nobody reviewed, and the code behind the link can change at any time."})
            continue
        match = re.match(r"[A-Za-z0-9_.\-]+", line)
        if not match:
            continue
        name = normalise(match.group(0))
        if name not in ok:
            near = sorted((distance(name, a), a) for a in ok if abs(len(a) - len(name)) <= 2)
            if near and near[0][0] <= 2:
                findings.append({"line": number, "text": line, "kind": "typosquat", "why": f"'{name}' is one or two letters away from the approved package '{near[0][1]}'."})
            else:
                findings.append({"line": number, "text": line, "kind": "unknown", "why": f"'{name}' is not on the approved list."})
        if "==" not in line:
            findings.append({"line": number, "text": line, "kind": "unpinned", "why": "No exact version, so each install can be different."})
        elif "--hash=" not in line:
            findings.append({"line": number, "text": line, "kind": "no-hash", "why": "Pinned, but there is no hash, so a swapped file would not be noticed."})
    for f in findings:
        f["severity"] = SEVERITY[f["kind"]]
    return findings
