"""The red-team harness: runs the probe library against a guardrail, several times each, and reports what got through.

    for each probe, N times:   send it to the target, read the reply with a detector
    for each normal question:  send it too, to see what the guardrail costs real customers

Two numbers come out. The attack success rate (ASR) is how often the attacks worked. The utility rate is how often a
normal question still got a correct answer. A guardrail that stops every attack by blocking everything has a utility
rate of zero, so read the two together. Results are saved in /data/results.json and shown on the console's scoreboard.
"""
import json
import time

import guardrails
import probes
import trailbot

RESULTS = trailbot.DATA / "results.json"


def load_results() -> dict:
    try:
        data = json.loads(RESULTS.read_text())
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def save_result(config: str, result: dict) -> None:
    data = load_results()
    data[config] = result
    RESULTS.write_text(json.dumps(data))


def clear_results() -> None:
    RESULTS.write_text("{}")


def run(config: str, records: list[dict], n: int = 1, model: str = trailbot.DEFAULT_MODEL, on_step=None) -> dict:
    """Run every probe and every normal question n times against one guardrail."""
    secret = trailbot.get_secret()
    started = time.time()
    per_probe, wins_total = [], 0
    for probe in probes.PROBES:
        recs = list(records)
        if "poison" in probe:
            recs.append({**probe["poison"], "vec": trailbot.embed([probe["poison"]["text"]])[0]})
        wins = blocked = 0
        trials = []
        for _ in range(n):
            out = guardrails.respond(probe["question"], recs, config, model)
            worked = bool(not out["blocked"] and probe["worked"](out["shown"], secret))
            blocked += bool(out["blocked"])
            wins += worked
            trials.append({"reply": out["shown"][:500], "blocked": bool(out["blocked"]), "reason": out["reason"], "worked": worked})
            if on_step:
                on_step()
        wins_total += wins
        per_probe.append({"id": probe["id"], "category": probe["category"], "wins": wins, "blocked": blocked, "n": n, "trials": trials})
    ok = refused = 0
    normal_detail = []
    for q in probes.UTILITY:
        trials = []
        for _ in range(n):
            out = guardrails.respond(q["question"], records, config, model)
            good = bool(not out["blocked"] and q["ok"](out["shown"]))
            refused += bool(out["blocked"])
            ok += good
            trials.append({"reply": out["shown"][:500], "blocked": bool(out["blocked"]), "reason": out["reason"], "ok": good})
            if on_step:
                on_step()
        normal_detail.append({"question": q["question"], "trials": trials})
    attacks = len(probes.PROBES) * n
    normal = len(probes.UTILITY) * n
    return {"config": config, "n": n, "probes": per_probe, "asr": round(wins_total / attacks, 3), "wins": wins_total, "attacks": attacks,
            "normal": normal_detail, "utility": round(ok / normal, 3), "utility_ok": ok, "utility_total": normal, "refused": refused,
            "seconds": round(time.time() - started)}


def total_steps(n: int) -> int:
    return (len(probes.PROBES) + len(probes.UTILITY)) * n
