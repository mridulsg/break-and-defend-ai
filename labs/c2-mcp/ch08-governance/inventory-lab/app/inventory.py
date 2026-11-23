"""Find every MCP server that Acme's engineers have connected, and compare it with the list the company approved.

Each developer's assistant has a config file that names the MCP servers it connects to. This module reads those files and answers
the questions a security team needs answered:

  which servers exist, and on whose machines?            (an inventory)
  which were never approved?                              (shadow servers)
  which are approved by name but not as approved?         (drift: an unpinned version)
  what is risky about each?                               (flags)

Flags: unpinned (a package fetched at its newest version), plaintext-http (an address that is not https and not this machine),
secret-in-config (a token or key written into the file).
"""
import json
import pathlib
import re

SECRET_KEYS = re.compile(r"(token|key|secret|password|authorization)", re.I)
BLOCKING_FLAGS = {"unpinned", "plaintext-http", "secret-in-config"}


def load_registry(path: pathlib.Path) -> dict:
    return {r["name"]: r for r in json.loads(path.read_text(encoding="utf-8"))["approved"]}


def flags_for(spec: dict) -> list[str]:
    flags = []
    args = [str(a) for a in spec.get("args", [])]
    if spec.get("command") in ("npx", "uvx", "pipx"):
        packages = [a for a in args if not a.startswith("-")]
        if not packages or not all(re.search(r"(==|@)\d[\w.\-]*$", p) for p in packages):
            flags.append("unpinned")
    url = spec.get("url", "")
    if url.startswith("http://") and not re.match(r"http://(localhost|127\.0\.0\.1|\[::1\])([:/]|$)", url):
        flags.append("plaintext-http")
    for place in ("env", "headers"):
        for k, v in (spec.get(place) or {}).items():
            if SECRET_KEYS.search(k) and not str(v).replace("Bearer ", "").startswith("${"):
                flags.append("secret-in-config")
                break
    return sorted(set(flags))


def scan(configs: pathlib.Path, registry: dict) -> list[dict]:
    out = []
    for f in sorted(configs.glob("*.json")):
        machine = f.stem
        servers = json.loads(f.read_text(encoding="utf-8")).get("mcpServers", {})
        for name, spec in servers.items():
            flags = flags_for(spec)
            approved = registry.get(name)
            if approved is None:
                status = "shadow"
            elif "unpinned" in flags:
                status = "drift"
            else:
                status = "approved"
            out.append({"key": f"{machine}/{name}", "machine": machine, "name": name, "where": spec.get("url") or " ".join([spec.get("command", "")] + [str(a) for a in spec.get("args", [])]),
                        "status": status, "flags": flags, "owner": approved["owner"] if approved else None})
    return out


def can_approve(item: dict) -> str | None:
    """Policy: a server with a blocking flag cannot be approved as it is. Return the reason, or None."""
    bad = [f for f in item["flags"] if f in BLOCKING_FLAGS]
    return ("it has " + ", ".join(bad) + ": fix it first, or block it") if bad else None
