"""The Acme console for Lab 1.1 (Course 3): watch an AI agent run tasks, and see what it does with text it reads.

Three tasks run on a small agent platform: summarise a vendor page, triage a ticket, and summarise a page an attacker edited.
The planner is a rule-based stand-in for a model that obeys instructions in what it reads (see shared/agents/sim.py).
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
CONTROLS = [{"id": "plan", "label": "Check every action against the task's plan", "text": "A tool call is allowed only if it is one of the steps the user's task needs."}]


def run_scenarios(policy: dict) -> list[dict]:
    out = []
    for sid, kind, task in (("S1", "work", "summarise_vendor"), ("S2", "work", "triage"), ("S3", "attack", "summarise_poisoned")):
        WORLD.reset()
        lines, agent = sim.run_task(WORLD, policy, task)
        if kind == "attack":
            worked = sim.sent_secret(WORLD)
        elif task == "triage":
            worked = bool(WORLD.comments)
        else:
            worked = not any(t["kind"] == "blocked" for t in agent.trace)
        out.append({"id": sid, "kind": kind, "title": sim.TASKS[task][0], "worked": worked, "details": lines})
    WORLD.reset()
    return out


def on_result(policy, results, stopped, attacks, work_ok, work):
    progress.mark("run", "You ran the three tasks and read what the agent did, step by step.")
    if stopped == 0:
        progress.mark("obey", "The agent read an instruction inside a web page, obeyed it, and emailed a secret to an outside address.")
    if stopped == attacks and work_ok == work and policy.get("plan"):
        progress.mark("stop", "With the plan check on, the instruction in the page did nothing, and both real tasks still worked.")


LAB = suitekit.build(
    product="Acme Agent Console", lab="Lab 1.1: Watch an agent, and map what it can reach",
    controls=CONTROLS, run_scenarios=run_scenarios, on_result=on_result, progress=progress,
    suite={"nav": "Agent runs", "title": "Agent runs", "run": "Run the three tasks",
           "lede": "An agent gets a goal, takes steps with tools, and reads what comes back. Run three tasks and open What the agent did on each: every step is shown."},
    missions_lede="Three things to see. Each is detected when you run the tasks.",
    missions=[
        {"id": "run", "kind": "auto", "title": "Run the tasks and read the steps", "text": "On the Agent runs page, run the three tasks. Open What the agent did on each one."},
        {"id": "obey", "kind": "auto", "title": "See the agent obey a web page", "text": "With the control off, the third task summarises a page an attacker edited. Find the step where the agent obeys an instruction in the page."},
        {"id": "stop", "kind": "auto", "title": "Stop it with one platform control", "text": "Turn on the plan check and run again. The third task should do nothing harmful, and the first two should still work."},
    ],
    flag_next="Next: Chapter 2 looks at goal hijacking in more detail, with more ways in and more controls.",
)

if __name__ == "__main__":
    LAB.run(LAB.run_routes)
