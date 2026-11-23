"""The Acme console for Labs 3.1 and 3.2 (Course 3): poisoning an agent's memory.

An agent that remembers between sessions can be steered by what it remembered. Session 1 reads a blog post that plants a rule in memory.
Session 2, another day, triages a ticket and recalls memory. You choose platform controls and measure. The planner is a stand-in
(shared/agents/sim.py). Run by the `console` service; open http://127.0.0.1:8300.
"""
import os
import sys

sys.path.insert(0, os.environ.get("BDAI_AGENTS_DIR", "/agents"))
sys.path.insert(0, os.environ.get("BDAI_MCP_DIR", "/mcp"))

import progress  # noqa: E402
import sim  # noqa: E402
import suitekit  # noqa: E402

WORLD = sim.World()
CONTROLS = [
    {"id": "scan", "label": "Scan what the agent reads", "text": "Remove lines that start like instructions (INSTRUCTION:, IMPORTANT:, SYSTEM:), including in what it recalls."},
    {"id": "plan", "label": "Check every action against the task's plan", "text": "A tool call, including a memory write, is allowed only if the user's task needs it."},
    {"id": "quarantine", "label": "Quarantine memory written because of text it read", "text": "A memory entry written by an unplanned step is held for review and never recalled."},
    {"id": "ttl", "label": "Forget everything between sessions", "text": "Memory lasts only for the session that wrote it."},
    {"id": "scopes", "label": "Least privilege per task", "text": "A summary task runs read-only: it cannot write memory."},
    {"id": "denyall", "label": "Deny everything", "text": "Refuse every tool call."},
]


def two_sessions(policy: dict, first: str, second: str):
    WORLD.reset()
    l1, a1 = sim.run_task(WORLD, policy, first)
    if policy.get("ttl"):
        WORLD.memory.clear()
    l2, a2 = sim.run_task(WORLD, policy, second)
    return l1 + ["--- next day ---"] + l2, a1, a2


def run_scenarios(policy: dict) -> list[dict]:
    out = []
    for sid, first, title in (("M1", "read_blog_plant", "A blog post plants a rule in memory; the next day it fires"),
                              ("M2", "read_blog_plant_reworded", "The same, reworded to avoid a word list")):
        lines, a1, a2 = two_sessions(policy, first, "triage_with_memory")
        out.append({"id": sid, "kind": "attack", "title": title, "worked": sim.sent_secret(WORLD), "details": lines})
    lines, a1, a2 = two_sessions(policy, "set_preference", "triage_with_memory")
    recalled = any(t["kind"] == "tool" and t["text"].startswith("recall") and "short summaries" in t.get("result", "") for t in a2.trace)
    out.append({"id": "L1", "kind": "work", "title": "The user asks the agent to remember a preference; it is recalled the next day", "worked": recalled and bool(WORLD.comments), "details": lines})
    WORLD.reset()
    lines, a1 = sim.run_task(WORLD, policy, "triage_with_memory")
    out.append({"id": "L2", "kind": "work", "title": "Triage a ticket with no memory", "worked": bool(WORLD.comments), "details": lines})
    WORLD.reset()
    return out


def on_result(policy, results, stopped, attacks, work_ok, work):
    on = sorted(k for k, v in policy.items() if v)
    if stopped == 0:
        progress.mark("baseline", "A rule planted by a blog post sat in memory overnight, then made the agent email a secret to an outside address.")
    if stopped == attacks and work_ok < work:
        progress.mark("tradeoff", f"This policy stopped every attack, and also broke {work - work_ok} of {work} real tasks.")
    if stopped == attacks and work_ok == work:
        progress.mark("hardened", f"Every attack stopped and memory still works, with: {', '.join(on)}.")


LAB = suitekit.build(
    product="Acme Agent Memory Console", lab="Labs 3.1 and 3.2: Memory poisoning and persistence",
    controls=CONTROLS, run_scenarios=run_scenarios, on_result=on_result, progress=progress,
    suite={"nav": "Memory suite", "title": "Memory suite", "run": "Save and run the suite",
           "lede": "An agent remembers between sessions. Two attacks plant a rule in memory on day one. Two real tasks use memory or work without it. Switch controls on, then run."},
    missions=[
        {"id": "baseline", "kind": "auto", "title": "See a planted memory fire the next day", "text": "Every control off. Run, and open What the agent did on M1: find the memory write on day one and the email on day two."},
        {"id": "tradeoff", "kind": "auto", "title": "Stop every attack by breaking memory", "text": "Which control stops every attack because the agent forgets everything? What does it cost the real tasks?"},
        {"id": "hardened", "kind": "auto", "title": "Stop every attack and keep memory useful", "text": "Choose controls so every attack is stopped and L1 (a remembered preference) still works.",
         "hint": "L1's memory write is part of the user's task. The attacks' memory writes are not."},
    ],
    flag_next="Next: Lab 3.2 shows what each control can and cannot do.",
)

if __name__ == "__main__":
    LAB.run(LAB.run_routes)
