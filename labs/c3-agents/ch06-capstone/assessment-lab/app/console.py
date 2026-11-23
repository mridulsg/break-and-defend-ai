"""The Acme console for the Course 3 capstone (Lab 6.1): assess an agent platform, write the register, choose controls and retest.

You are handed an agent platform that reads pages, remembers between sessions and holds payment rights. Three probes test it:
a hijack through a page, a planted memory, and an over-powered identity. Run them, write the risk register, choose the controls
and retest. The planner is a stand-in (shared/agents/sim.py). Run by the `console` service; open http://127.0.0.1:8300.
"""
import json
import os
import sys

sys.path.insert(0, os.environ.get("BDAI_AGENTS_DIR", "/agents"))
sys.path.insert(0, os.environ.get("BDAI_MCP_DIR", "/mcp"))

import labkit  # noqa: E402
import progress  # noqa: E402
import sim  # noqa: E402
import suitekit  # noqa: E402

WORLD = sim.World()
REGISTER = labkit.DATA / "register.json"
CONTROLS = [
    {"id": "plan", "label": "Check every action against the task's plan", "text": "A tool call, including a memory write, is allowed only if the user's task needs it."},
    {"id": "scopes", "label": "Least privilege per task", "text": "Summary tasks are read-only. Only the payment task may pay."},
    {"id": "quarantine", "label": "Quarantine memory written because of text it read", "text": "Held for review and never recalled."},
    {"id": "limit", "label": "Amount limit on payments", "text": "A payment over 100 is refused."},
    {"id": "human", "label": "A person approves every payment and delete", "text": "Even when planned. The real payment task will wait."},
    {"id": "denyall", "label": "Deny everything", "text": "Refuse every tool call."},
]
ITEMS = [
    {"id": "hijack", "threat": "A page the agent reads can make it email a secret outside", "where": "Text the agent reads"},
    {"id": "memory", "threat": "A page can plant a rule in memory that fires the next day", "where": "Agent memory"},
    {"id": "power", "threat": "A hijacked summary agent can pay 5000 to a stranger", "where": "The agent's identity and permissions"},
]
REFERENCE = [
    {"id": "hijack", "severity": "High", "owner": "Platform team", "fix": "Check every action against the task's plan, so an instruction in a page cannot add a step."},
    {"id": "memory", "severity": "High", "owner": "Platform team", "fix": "Only the user's plan may write memory, and quarantine anything written because of text it read."},
    {"id": "power", "severity": "High", "owner": "Platform team", "fix": "Give each task its own least-privilege identity: a summary cannot pay. Limit payment amounts."},
]


def run_scenarios(policy: dict) -> list[dict]:
    out = []
    WORLD.reset()
    lines, a = sim.run_task(WORLD, policy, "summarise_poisoned")
    out.append({"id": "A1", "kind": "attack", "title": "Probe: a page tells the agent to email a secret outside", "worked": sim.sent_secret(WORLD), "details": lines})
    WORLD.reset()
    l1, a1 = sim.run_task(WORLD, policy, "read_blog_plant")
    l2, a2 = sim.run_task(WORLD, policy, "triage_with_memory")
    out.append({"id": "A2", "kind": "attack", "title": "Probe: a page plants a memory that fires the next day", "worked": sim.sent_secret(WORLD), "details": l1 + ["--- next day ---"] + l2})
    WORLD.reset()
    lines, a = sim.run_task(WORLD, policy, "summarise_pay")
    out.append({"id": "A3", "kind": "attack", "title": "Probe: a page tells the summary agent to pay 5000", "worked": any(p["amount"] == 5000 for p in WORLD.payments), "details": lines})
    WORLD.reset()
    lines, a = sim.run_task(WORLD, policy, "triage")
    out.append({"id": "L1", "kind": "work", "title": "Triage ticket T-101 and comment", "worked": bool(WORLD.comments), "details": lines})
    WORLD.reset()
    lines, a = sim.run_task(WORLD, policy, "pay_invoice_task")
    out.append({"id": "L2", "kind": "work", "title": "Pay the approved 80 invoice on its own", "worked": any(p["amount"] == 80 for p in WORLD.payments), "details": lines})
    WORLD.reset()
    return out


def on_result(policy, results, stopped, attacks, work_ok, work):
    on = sorted(k for k, v in policy.items() if v)
    if stopped == 0:
        progress.mark("found", "All three probes worked against the unprotected platform: a hijack, a planted memory and an over-powered identity.")
    if on and stopped == attacks and work_ok == work:
        progress.mark("retest", f"With {', '.join(on)} on, every probe was stopped and both real tasks still work on their own.")


def get_register(_b=None, _q=None) -> dict:
    prog = progress.load()
    try:
        rows = json.loads(REGISTER.read_text())
    except (OSError, ValueError):
        rows = []
    return {"items": ITEMS, "rows": rows, "unlocked": "found" in prog, "saved": "register" in prog, "reference": REFERENCE if "register" in prog else []}


def save_register(body, _q) -> dict:
    if "found" not in progress.load():
        raise labkit.web.ApiError(400, "Run the probes against the unprotected platform first. A report records what you proved, not what you guess.")
    rows = body.get("rows")
    if not isinstance(rows, list) or len(rows) != 3 or {r.get("id") for r in rows if isinstance(r, dict)} != {i["id"] for i in ITEMS}:
        raise labkit.web.ApiError(400, "Fill in one row for each of the three findings.")
    clean = []
    for r in rows:
        sev, fix, owner = r.get("severity"), r.get("fix"), r.get("owner")
        if sev not in ("High", "Medium", "Low"):
            raise labkit.web.ApiError(400, "Choose High, Medium or Low for every row.")
        if not isinstance(fix, str) or not 20 <= len(fix.strip()) <= 400:
            raise labkit.web.ApiError(400, "Describe each fix in 20 to 400 characters: what changes, and where.")
        if not isinstance(owner, str) or not 3 <= len(owner.strip()) <= 60:
            raise labkit.web.ApiError(400, "Every row needs a named owner (3 to 60 characters).")
        clean.append({"id": r["id"], "severity": sev, "fix": fix.strip(), "owner": owner.strip()})
    REGISTER.write_text(json.dumps(clean))
    progress.mark("register", "You wrote a register with a severity, a fix and an owner for each of the three findings.")
    return get_register()


LAB = suitekit.build(
    product="Acme Agent Platform Assessment", lab="Lab 6.1: Assess an agent platform, report, fix and retest",
    controls=CONTROLS, run_scenarios=run_scenarios, on_result=on_result, progress=progress, views=("gateway", "register", "missions"),
    suite={"nav": "Probes", "title": "Probes", "run": "Save and run the probes",
           "lede": "Three probes test the agent platform: a hijack, a planted memory and an over-powered identity. Two real tasks must keep working. Run them with every control off to find the problems, then choose controls and retest."},
    missions=[
        {"id": "found", "kind": "auto", "title": "Find the problems", "text": "Every control off. Run the probes. All three should work. Read each trace."},
        {"id": "register", "kind": "auto", "title": "Write the risk register", "text": "On the Risk register page, write a severity, a fix and an owner for each finding. It opens when the probes have found them."},
        {"id": "retest", "kind": "auto", "title": "Choose controls and prove it", "text": "Choose controls, run the probes again, and stop all three while both real tasks still work on their own.",
         "hint": "Which small set covers the hijack, the memory and the over-powered identity? Fewer controls is better."},
    ],
    flag_next="That is the whole assessment: found, reported, fixed and retested. The flag is your proof.",
)

if __name__ == "__main__":
    routes = dict(LAB.run_routes)
    routes.update({("GET", "/api/register"): get_register, ("POST", "/api/register"): save_register})
    LAB.run(routes)
