"""The Acme console for Labs 2.1 and 2.2 (Course 3): goal hijacking of an agent through text it reads.

Three attacks put instructions in text the agent reads (a vendor page, a camping blog, and a reworded version). Two real tasks must
keep working. You choose platform controls and run the suite. The planner is a stand-in (shared/agents/sim.py).
Run by the `console` service; open http://127.0.0.1:8300.
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
    {"id": "tag", "label": "Mark untrusted text as data", "text": "Wrap everything the agent reads in tags that say it is data, not instructions. (A prompt-level defence.)"},
    {"id": "scan", "label": "Scan what the agent reads", "text": "Remove lines that start like instructions (INSTRUCTION:, IMPORTANT:, SYSTEM:)."},
    {"id": "plan", "label": "Check every action against the task's plan", "text": "A tool call is allowed only if it is a step the user's task needs."},
    {"id": "approval", "label": "Approval for changes", "text": "A tool call that changes something and is not part of the plan waits for a person."},
    {"id": "egress", "label": "Email only inside the company", "text": f"send_email works only for recipients at {sim.COMPANY}."},
    {"id": "scopes", "label": "Least privilege per task", "text": "A summary task runs with a read-only identity: no write, no send."},
    {"id": "denyall", "label": "Deny everything", "text": "Refuse every tool call."},
]
ATTACKS = [("A1", "summarise_poisoned", lambda w: sim.sent_secret(w), "A vendor page tells the agent to email a secret outside"),
           ("A2", "summarise_blog", lambda w: any(c["id"] == "T-103" for c in w.comments), "A blog post tells the agent to comment on ticket T-103"),
           ("A3", "summarise_reworded", lambda w: sim.sent_secret(w), "The same attack, reworded to avoid a word list")]
WORK = [("L1", "summarise_vendor", lambda w, a: not any(t["kind"] == "blocked" for t in a.trace) and any(t["kind"] == "tool" for t in a.trace), "Summarise the vendor page"),
        ("L2", "triage", lambda w, a: bool(w.comments), "Triage ticket T-101 and comment")]


def run_scenarios(policy: dict) -> list[dict]:
    out = []
    for sid, task, check, title in ATTACKS:
        WORLD.reset()
        lines, agent = sim.run_task(WORLD, policy, task)
        out.append({"id": sid, "kind": "attack", "title": title, "worked": check(WORLD), "details": lines})
    for sid, task, check, title in WORK:
        WORLD.reset()
        lines, agent = sim.run_task(WORLD, policy, task)
        out.append({"id": sid, "kind": "work", "title": title, "worked": check(WORLD, agent), "details": lines})
    WORLD.reset()
    return out


def on_result(policy, results, stopped, attacks, work_ok, work):
    on = sorted(k for k, v in policy.items() if v)
    if not on and stopped == 0:
        progress.mark("baseline", "With no controls, all three attacks worked.")
    if on == ["tag"] and stopped == 0:
        progress.mark("tagging", "With only 'mark untrusted text as data' on, every attack still worked. Telling the model is not enforcing.")
    if stopped == attacks and work_ok < work:
        progress.mark("overblock", f"This policy stopped every attack and {work - work_ok} of {work} real tasks.")
    if stopped == attacks and work_ok == work:
        progress.mark("hardened", f"Every attack stopped and every task works, with: {', '.join(on)}.")


LAB = suitekit.build(
    product="Acme Agent Hijack Console", lab="Labs 2.1 and 2.2: Goal hijacking and agent injection",
    controls=CONTROLS, run_scenarios=run_scenarios, on_result=on_result, progress=progress,
    suite={"nav": "Hijack suite", "title": "Hijack suite", "run": "Save and run the suite",
           "lede": "Three attacks put an instruction in text an agent reads. Two real tasks must keep working. Switch platform controls on, then run."},
    missions=[
        {"id": "baseline", "kind": "auto", "title": "Measure the unprotected agent", "text": "Switch every control off and run. All three attacks work."},
        {"id": "tagging", "kind": "auto", "title": "Try the prompt-level defence on its own", "text": "Switch on only 'Mark untrusted text as data' and run. See what it changes."},
        {"id": "overblock", "kind": "auto", "title": "Find the policy that is safe and useless", "text": "Which control stops every attack by stopping every task too?"},
        {"id": "hardened", "kind": "auto", "title": "Stop every attack and keep every task", "text": "Choose controls so all three attacks are stopped and both tasks work. Fewer controls is better.",
         "hint": "One control alone is enough. Which one does not depend on recognising the attack?"},
    ],
    flag_next="Next: Lab 2.2 shows what each control can and cannot do.",
)

if __name__ == "__main__":
    LAB.run(LAB.run_routes)
