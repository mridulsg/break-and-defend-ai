"""The Acme console for Labs 8.1 and 8.2: a shadow-MCP inventory.

Four engineers have connected MCP servers to their assistants. You scan their config files, compare them with the company's
registry of approved servers, and record a decision, an owner and a reason for every server that is not approved as it is.
Nothing here starts any server: the configs are only read. Run by the `console` service; open http://127.0.0.1:8300.
"""
import json
import os
import pathlib
import sys

sys.path.insert(0, os.environ.get("BDAI_MCP_DIR", "/mcp"))

import inventory  # noqa: E402
import labkit  # noqa: E402
import progress  # noqa: E402

LAB_DIR = pathlib.Path(os.environ.get("BDAI_LAB_DIR", "/lab"))
CONFIGS = LAB_DIR / "configs"
REGISTRY = LAB_DIR / "registry.json"
DECISIONS = labkit.DATA / "decisions.json"
ACTIONS = ("approve", "block", "request-fix", "investigate")


def load_decisions() -> dict:
    try:
        d = json.loads(DECISIONS.read_text())
        return d if isinstance(d, dict) else {}
    except (OSError, ValueError):
        return {}


def snapshot() -> dict:
    servers = inventory.scan(CONFIGS, inventory.load_registry(REGISTRY))
    decisions = load_decisions()
    todo = [s for s in servers if s["status"] != "approved"]
    for s in servers:
        s["decision"] = decisions.get(s["key"])
        s["approvable"] = inventory.can_approve(s) is None
    undecided = [s["key"] for s in todo if s["key"] not in decisions]
    return {"servers": servers, "machines": sorted({s["machine"] for s in servers}), "todo": len(todo), "undecided": undecided}


def inventory_route(_b, _q) -> dict:
    snap = snapshot()
    progress.mark("inventory", f"You found {len(snap['servers'])} MCP servers on {len(snap['machines'])} machines, {snap['todo']} of them not approved as they are.")
    todo = [s for s in snap["servers"] if s["status"] != "approved"]
    if not snap["undecided"] and all(s["decision"]["action"] != "investigate" for s in todo):
        progress.mark("clean", "A rescan shows every unapproved server decided, and none left in 'investigate'.")
    snap["state"] = LAB.state({}, {})
    return snap


def decide_route(body, _q) -> dict:
    key, action, owner, reason = body.get("key"), body.get("action"), body.get("owner"), body.get("reason")
    servers = {s["key"]: s for s in snapshot()["servers"]}
    item = servers.get(key)
    if item is None or item["status"] == "approved":
        raise labkit.web.ApiError(400, "Choose a server that is not approved.")
    if action not in ACTIONS:
        raise labkit.web.ApiError(400, "Choose approve, block, request-fix or investigate.")
    if not isinstance(owner, str) or not 3 <= len(owner.strip()) <= 60:
        raise labkit.web.ApiError(400, "Name an owner (3 to 60 characters).")
    if not isinstance(reason, str) or not 10 <= len(reason.strip()) <= 200:
        raise labkit.web.ApiError(400, "Give a reason (10 to 200 characters).")
    if action == "approve":
        why_not = inventory.can_approve(item)
        if why_not:
            raise labkit.web.ApiError(400, "Cannot approve: " + why_not + ".")
    d = load_decisions()
    d[key] = {"action": action, "owner": owner.strip(), "reason": reason.strip()}
    DECISIONS.write_text(json.dumps(d))
    snap = snapshot()
    if not snap["undecided"]:
        progress.mark("decide", f"Every one of the {snap['todo']} servers that were not approved now has a decision, an owner and a reason.")
    snap["state"] = LAB.state({}, {})
    return snap


def reset_route(_b, _q) -> dict:
    DECISIONS.unlink(missing_ok=True)
    return snapshot()


LAB = labkit.Lab(
    product="Acme MCP Inventory Console", lab="Labs 8.1 and 8.2: Finding and governing shadow MCP servers",
    intro="", suggestions=[], views=["inventory", "missions"],
    missions_lede="Nobody told security about these servers. Find them, decide, and leave nothing without an owner.",
    missions=[
        {"id": "inventory", "kind": "auto", "title": "Find every MCP server",
         "text": "On the Inventory page, run the scan. It reads every engineer's config and compares it with the approved registry."},
        {"id": "decide", "kind": "auto", "title": "Decide on every server that is not approved",
         "text": "For each shadow or drifted server, choose approve, block, request a fix or investigate, and give an owner and a reason. Some cannot be approved as they are.",
         "hint": "The page tells you why a server cannot be approved. A server with a secret in its config, plain http or an unpinned version needs a fix first."},
        {"id": "clean", "kind": "auto", "title": "Leave nothing open",
         "text": "Rescan. Nothing may be undecided, and nothing may be left in 'investigate'. Investigation is a step, not a decision."},
    ],
    flag_next="Next: Lab 8.2 turns this into a standing process.",
    progress=progress, servers={},
)

if __name__ == "__main__":
    LAB.run({("POST", "/api/inventory"): inventory_route, ("POST", "/api/decide"): decide_route, ("POST", "/api/inventory/reset"): reset_route})
