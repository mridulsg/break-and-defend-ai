"""Read a garak report and print what a reviewer needs: one line per probe and detector, and a few real replies.

    docker compose --env-file .env -f labs/c1-llm/ch08-securing-the-pipeline/garak-lab/compose.yaml run --rm garak python /lab/summarise.py [report-name]

With no name it reads the newest report in /data. A name such as `mine` reads /data/mine.report.jsonl.

garak writes a .jsonl report: one JSON object per line. The kinds that matter here are
  attempt   one prompt sent to the target, the reply, and what each detector decided
  eval      a probe and a detector with how many replies passed and how many failed
A FAIL means the attack worked: the detector found what the probe was looking for in the reply.
"""
import json
import pathlib
import sys

DATA = pathlib.Path("/data")


def pick() -> pathlib.Path:
    if len(sys.argv) > 1:
        return DATA / f"{sys.argv[1]}.report.jsonl"
    reports = sorted(DATA.glob("*.report.jsonl"), key=lambda p: p.stat().st_mtime)
    return reports[-1] if reports else DATA / "scan.report.jsonl"


REPORT = pick()


def text(value) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        return text(value.get("text") or value.get("content") or value.get("turns") or "")
    if isinstance(value, list):
        return " ".join(text(v) for v in value)
    return str(value)


def main() -> int:
    if not REPORT.exists():
        print(f"No report at {REPORT}. Run the scan first.")
        return 1
    evals, attempts = [], []
    for line in REPORT.read_text(encoding="utf-8").splitlines():
        entry = json.loads(line)
        if entry.get("entry_type") == "eval":
            evals.append(entry)
        elif entry.get("entry_type") == "attempt" and entry.get("status") == 2:
            attempts.append(entry)
    print(f"Report: {REPORT.name}")
    print(f"{'probe':32} {'detector':32} {'attack worked':>14}")
    for e in evals:
        total = e["total_evaluated"] or 0
        print(f"{e['probe']:32} {e['detector']:32} {e['fails']:>6} of {total:<5}")
    print("\nA few replies where the attack worked (FAIL):")
    shown = 0
    for a in attempts:
        for detector, results in a.get("detector_results", {}).items():
            if any(r and r >= 0.5 for r in results) and shown < 4:
                reply = text((a.get("outputs") or [""])[0]).replace("\n", " ")
                prompt = text(a.get("prompt")).replace("\n", " ")
                print(f"- {a['probe_classname']} / {detector}\n    prompt: {prompt[:110]}...\n    reply:  {reply[:200]}")
                shown += 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
