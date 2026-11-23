"""A small static scanner for an MCP server project: the kind of check a build pipeline runs before a server is allowed to ship.

It reads three files and reports what a reviewer would stop. It is deliberately simple: every rule is a line of text or a regular
expression, so you can read all of it, and so you can see what it would miss.

  server.py.sample    command injection, path traversal, SSRF, hard-coded secrets, poisoned descriptions, loose input schemas
  deps.txt            unpinned versions, missing hashes, a second package index
  Dockerfile.sample   an unpinned base image, running as root
"""
import json
import pathlib
import re

SEVERITY = {"high": 3, "medium": 2, "low": 1}
SUSPICIOUS = re.compile(r"\b(always|never|must|important|ignore|do not|required|word for word|user's|instructions)\b", re.I)
SECRET = re.compile(r"""(KEY|SECRET|TOKEN|PASSWORD)\s*=\s*["'][^"']{8,}["']""")


def finding(file, line, rule, severity, why):
    return {"file": file, "line": line, "rule": rule, "severity": severity, "why": why}


def scan_server(text: str) -> list[dict]:
    out = []
    lines = text.splitlines()
    for n, line in enumerate(lines, 1):
        if "shell=True" in line:
            out.append(finding("server.py", n, "command-injection", "high", "shell=True parses the whole string with a shell, so text in it can add commands."))
        if re.search(r"\bopen\(.*\+", line):
            out.append(finding("server.py", n, "path-traversal", "high", "A path built by adding text to a folder name lets '..' climb out of it. Resolve and check containment."))
        if SECRET.search(line):
            out.append(finding("server.py", n, "hard-coded-secret", "high", "A secret in the source is in every copy, every image and every log of the code."))
        if '"description"' in line and SUSPICIOUS.search(line):
            out.append(finding("server.py", n, "instruction-in-description", "medium", "A tool description that gives orders to the model is a poisoning channel (Chapter 2)."))
        if '"inputSchema"' in line and "additionalProperties" not in line:
            out.append(finding("server.py", n, "loose-input-schema", "low", "The schema does not forbid extra arguments or require the expected ones."))
    for n, line in enumerate(lines, 1):
        if "urlopen(" in line and not any("ALLOWED" in l for l in lines):
            out.append(finding("server.py", n, "ssrf", "high", "The server opens any URL it is given, including ones that only it can reach (Chapter 3)."))
    return out


def scan_deps(text: str) -> list[dict]:
    out = []
    for n, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("--extra-index-url"):
            out.append(finding("deps.txt", n, "extra-index", "high", "A second package server can win a version race (dependency confusion)."))
        elif "==" not in line:
            out.append(finding("deps.txt", n, "unpinned", "medium", "No exact version: each build can install something different."))
        elif "--hash=" not in line:
            out.append(finding("deps.txt", n, "no-hash", "low", "Pinned, but nothing checks the downloaded file is the one you reviewed."))
    return out


def scan_container(text: str) -> list[dict]:
    out = []
    lines = text.splitlines()
    for n, line in enumerate(lines, 1):
        if line.startswith("FROM ") and "@sha256:" not in line:
            out.append(finding("Dockerfile", n, "unpinned-base-image", "medium", "A tag can move. Pin the base image by digest."))
    users = [l for l in lines if l.startswith("USER ")]
    if not users or users[-1].strip() == "USER root":
        out.append(finding("Dockerfile", len(lines), "runs-as-root", "medium", "The server runs with all the privileges of root inside the container."))
    return out


def scan_project(path: pathlib.Path) -> list[dict]:
    found = []
    for name, fn in (("server.py.sample", scan_server), ("deps.txt", scan_deps), ("Dockerfile.sample", scan_container)):
        f = path / name
        if f.exists():
            found += fn(f.read_text(encoding="utf-8"))
    return found


def gate(findings: list[dict], threshold: str) -> dict:
    """The pipeline step: fail the build when anything at or above the threshold is found."""
    limit = SEVERITY[threshold]
    blockers = [f for f in findings if SEVERITY[f["severity"]] >= limit]
    return {"passed": not blockers, "blockers": len(blockers), "threshold": threshold}


def report(findings: list[dict]) -> str:
    return json.dumps(findings, indent=1)
