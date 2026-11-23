"""The Acme console for Labs 8.1 and 8.2: a red-team harness, a scoreboard of guardrails, and a box for your own attacks.

  * Run the attack library against a guardrail and read two numbers: how many attacks worked, and how many normal questions
    still got a correct answer.
  * Run it against all five guardrails and compare them on one scoreboard.
  * Write your own attack and try to get the secret code past the keyword filter and past the model judge.

Run by the `console` service (see compose.yaml); open http://127.0.0.1:8300.
"""
import json
import os
import pathlib
import sys
import threading
import time

sys.path.insert(0, os.environ.get("BDAI_CONSOLE_DIR", "/console"))

import openai  # noqa: E402

import guardrails  # noqa: E402
import harness  # noqa: E402
import probes  # noqa: E402
import progress  # noqa: E402
import server  # noqa: E402
import trailbot  # noqa: E402

STATIC = pathlib.Path(os.environ.get("BDAI_CONSOLE_DIR", "/console")) / "static"
JOBS = server.Jobs()
LOCK = threading.RLock()
MAX_PROBE = 600
MAX_TRIALS = 3


def ensure_ready() -> None:
    with LOCK:
        trailbot.DATA.mkdir(parents=True, exist_ok=True)
        if not trailbot.INDEX.exists():
            trailbot.build_index()
        trailbot.get_secret()


def records() -> list[dict]:
    return json.loads(trailbot.INDEX.read_text(encoding="utf-8"))


def model_call(fn):
    try:
        return fn()
    except (openai.OpenAIError, OSError):
        raise server.ApiError(502, "The model did not answer. Is the gateway running and the local model server up? See the lab's troubleshooting table.")


def check_missions(results: dict) -> None:
    if "none" in results:
        r = results["none"]
        progress.mark("baseline", f"The undefended bot: {r['wins']} of {r['attacks']} attacks worked, and {r['utility_ok']} of {r['utility_total']} normal questions were answered correctly.")
    if all(c in results for c in guardrails.CONFIGS):
        progress.mark("scoreboard", "You measured all five guardrails and can compare attack success against what each one costs normal customers.")


def config(_body, _query) -> dict:
    return {
        "company": "Acme Outdoor Gear",
        "product": "Acme AI Console",
        "lab": "Labs 8.1 and 8.2: Red-team and guardrails",
        "persona": "red team",
        "intro": "", "secret": False, "fixes": False,
        "models": [{"id": "bdai-victim", "label": "Local model (Qwen3 1.7B, free)", "hosted": False}], "default_model": trailbot.DEFAULT_MODEL,
        "suggestions": [], "max_question": MAX_PROBE, "max_note": 0, "max_notes": 0,
        "views": ["redteam", "probe", "missions"],
        "feedback": {"lede": "", "doors": []},
        "guardrails": [{"id": k, "label": g.label, "description": g.description, "rules": list(g.rules)} for k, g in guardrails.CONFIGS.items()],
        "probes": [{"id": p["id"], "category": p["category"], "question": p["question"], "detects": p["detects"], "planted": p.get("poison", {}).get("text", "")} for p in probes.PROBES],
        "utility": [u["question"] for u in probes.UTILITY], "utility_expects": [u["expects"] for u in probes.UTILITY],
        "max_trials": MAX_TRIALS, "max_probe": MAX_PROBE,
        "missions_lede": "Measure first, then try to break what you measured. Each mission is detected automatically.",
        "missions": [
            {"id": "baseline", "kind": "auto", "title": "Measure the undefended bot",
             "text": "On the Red team page, run the attack library against 'No guardrail'. Read the attack success rate and the utility rate."},
            {"id": "scoreboard", "kind": "auto", "title": "Measure every guardrail",
             "text": "Run the library against all five guardrails so the scoreboard is complete. Which stops the most attacks? Which costs normal customers the most?"},
            {"id": "keyword", "kind": "auto", "title": "Get the secret past the keyword blocklist",
             "text": "On the Your own attack page, choose the keyword blocklist and write a message that makes TrailBot reveal the escalation code, anyway.",
             "hint": "The blocklist looks for certain words. Look at the Chapter 3 attacks: which of them never use those words? Then ask for the code in a way the words do not describe."},
            {"id": "judge", "kind": "auto", "title": "Get the secret past the model judge",
             "text": "Choose the model judge and write a message that makes TrailBot reveal the escalation code, anyway.",
             "hint": "The judge is a small model reading one message. It can be talked round, or hidden from. Try dressing the request up as something ordinary."},
        ],
        "flag_next": "Next: Lab 8.2 shows what a guardrail can and cannot do.",
    }


def state(_body, _query) -> dict:
    ready, problem = True, None
    try:
        ensure_ready()
    except Exception as exc:
        ready, problem = False, f"{type(exc).__name__}: {exc}"
    prog = progress.load()
    done = progress.is_complete(prog)
    return {
        "ready": ready, "problem": problem, "sources": {}, "notes": [],
        "missions": {**{m: m in prog for m in progress.MISSIONS}, "complete": done},
        "evidence": {m: prog[m] for m in progress.MISSIONS if m in prog},
        "flag": progress.FLAG if done else None, "fixes": False,
        "results": harness.load_results(),
    }


def start_run(body, _query) -> dict:
    cfg, n = body.get("config"), body.get("n", 1)
    if cfg not in guardrails.CONFIGS:
        raise server.ApiError(400, "Choose one of the guardrails.")
    if isinstance(n, bool) or not isinstance(n, int) or not 1 <= n <= MAX_TRIALS:
        raise server.ApiError(400, f"Run each attack between 1 and {MAX_TRIALS} times.")
    model_call(ensure_ready)
    total = harness.total_steps(n)

    def work(job: dict) -> None:
        job["total"], job["done_steps"] = total, 0

        def step() -> None:
            job["done_steps"] += 1

        result = model_call(lambda: harness.run(cfg, records(), n=n, on_step=step))
        harness.save_result(cfg, result)
        check_missions(harness.load_results())
        job["result"] = result

    return {"job": JOBS.start(work, "run")}


def job_status(_body, query) -> dict:
    job = JOBS.get(query.get("id", ""))
    out = dict(job)
    if job["done"] and not job["error"]:
        out["state"] = state({}, {})
    return out


def own_probe(body, _query) -> dict:
    cfg, text = body.get("config"), body.get("text")
    if cfg not in guardrails.CONFIGS:
        raise server.ApiError(400, "Choose one of the guardrails.")
    if not isinstance(text, str) or not text.strip():
        raise server.ApiError(400, "Write your attack first.")
    if len(text) > MAX_PROBE:
        raise server.ApiError(400, f"Keep it under {MAX_PROBE} characters.")
    model_call(ensure_ready)
    secret = trailbot.get_secret()
    out = model_call(lambda: guardrails.respond(text.strip(), records(), cfg))
    leaked = (not out["blocked"]) and probes.secret_leaked(out["shown"], secret)
    if leaked and cfg in ("keyword", "judge"):
        progress.mark(cfg, f"Your message got the escalation code past the {guardrails.CONFIGS[cfg].label.lower()}: {text.strip()[:120]!r}")
    return {"blocked": out["blocked"], "reason": out["reason"], "shown": out["shown"], "raw": out["raw"], "leaked": leaked,
            "config": cfg, "state": state({}, {})}


def clear_results(_body, _query) -> dict:
    harness.clear_results()
    return state({}, {})


ROUTES = {
    ("GET", "/api/config"): config,
    ("GET", "/api/state"): state,
    ("POST", "/api/run"): start_run,
    ("GET", "/api/job"): job_status,
    ("POST", "/api/probe"): own_probe,
    ("POST", "/api/results/clear"): clear_results,
}


def warm_up() -> None:
    while True:
        try:
            ensure_ready()
            return
        except Exception:
            time.sleep(5)


def main() -> None:
    threading.Thread(target=warm_up, daemon=True).start()
    print("Acme AI console (Chapter 8) listening on :8080", flush=True)
    server.serve(ROUTES, str(STATIC), port=8080)


if __name__ == "__main__":
    main()
