"""The shared console backend for the Course 3 labs: switch platform controls on, run a suite of scenarios, read the scoreboard.

A lab supplies its controls, a function that runs its scenarios under a policy, and a function that records missions.
Every scenario result is  {"id", "kind": "attack"|"work"|"see", "title", "worked": bool, "details": [lines]}.
For an attack, worked=True means the attack succeeded. For work, worked=True means the task still works.
Run by the lab's `console` service; open http://127.0.0.1:8300.
"""
import json
import os
import sys

sys.path.insert(0, os.environ.get("BDAI_MCP_DIR", "/mcp"))

import labkit  # noqa: E402


def build(*, product, lab, controls, run_scenarios, on_result, missions, progress, suite=None, missions_lede="Each mission is detected when you run the suite.", flag_next="", views=("gateway", "missions")):
    policy_file = labkit.DATA / "policy.json"

    def load_policy() -> dict:
        try:
            d = json.loads(policy_file.read_text())
            return d if isinstance(d, dict) else {}
        except (OSError, ValueError):
            return {}

    def get_policy(_b=None, _q=None) -> dict:
        return {"controls": controls, "policy": load_policy()}

    def set_policy(body, _q) -> dict:
        p = body.get("policy")
        if not isinstance(p, dict) or not set(p) <= {c["id"] for c in controls} or not all(isinstance(v, bool) for v in p.values()):
            raise labkit.web.ApiError(400, "Send true or false for each control.")
        policy_file.write_text(json.dumps(p))
        return get_policy()

    def run_route(_b, _q) -> dict:
        policy = load_policy()
        results = run_scenarios(policy)
        attacks = [r for r in results if r["kind"] == "attack"]
        work = [r for r in results if r["kind"] == "work"]
        stopped = sum(1 for r in attacks if not r["worked"])
        work_ok = sum(1 for r in work if r["worked"])
        on_result(policy, results, stopped, len(attacks), work_ok, len(work))
        return {"results": results, "stopped": stopped, "attacks": len(attacks), "work_ok": work_ok, "work": len(work), "policy": policy, "state": lab_obj.state({}, {})}

    lab_obj = labkit.Lab(product=product, lab=lab, intro="", suggestions=[], views=list(views), missions=missions, missions_lede=missions_lede,
                         flag_next=flag_next, progress=progress, servers={}, extra_state=lambda: {"suite": suite or {}})
    lab_obj.suite_cfg = suite or {}
    lab_obj.run_routes = {("GET", "/api/policy"): get_policy, ("POST", "/api/policy"): set_policy, ("POST", "/api/suite"): run_route}
    lab_obj.get_policy, lab_obj.set_policy, lab_obj.run_route, lab_obj.load_policy = get_policy, set_policy, run_route, load_policy
    return lab_obj
