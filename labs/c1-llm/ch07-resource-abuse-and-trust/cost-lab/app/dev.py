"""Acme's dev assistant: a coding helper that recommends Python packages to Acme's engineers.

Read this file. The assistant answers from what it learned, and nothing checks that a package it names actually exists.
An attacker can register an invented name on the real package index and wait for an engineer to run the `pip install`
line the assistant gave them. With fixes on, every name is checked against the package list first (see check()).

data/registry.txt is a stand-in for the real index (PyPI). In real life you would ask the index itself.
"""
import os
import pathlib
import re

LAB = pathlib.Path(os.environ.get("BDAI_LAB_DIR", "/lab"))
REGISTRY = LAB / "data" / "registry.txt"
MAX_TOKENS = 300

SYSTEM = ("You are a coding assistant for Acme's engineers. Recommend Python packages by name, one per line, "
          "in the form `pip install name`. Keep it short.")
INSTALL = re.compile(r"pip install ([A-Za-z0-9_.\-]+)")


def normalise(name: str) -> str:
    """The package index treats - _ and . as the same, and ignores case."""
    return re.sub(r"[-_.]+", "-", name.strip().lower())


def registry() -> set[str]:
    return {normalise(line) for line in REGISTRY.read_text(encoding="utf-8").splitlines() if line.strip() and not line.startswith("#")}


def packages(reply: str) -> list[str]:
    seen: list[str] = []
    for name in INSTALL.findall(reply):
        if name not in seen:
            seen.append(name)
    return seen


def check(reply: str) -> list[dict]:
    """Each package the reply tells an engineer to install, and whether it exists."""
    known = registry()
    return [{"name": n, "exists": normalise(n) in known} for n in packages(reply)]


def clean(reply: str) -> str:
    """The fix: an install line for a package that does not exist is replaced by a warning."""
    known = registry()

    def swap(match: re.Match) -> str:
        return match.group(0) if normalise(match.group(1)) in known else f"(removed: {match.group(1)} is not on the package index)"

    return INSTALL.sub(swap, reply)
