# Labs 8.1 and 8.2: red team and guardrails

The walkthroughs are the lab pages: `docs/c1/lab-8-1-red-team-and-guardrails.md` (measure and break) and `docs/c1/lab-8-2-what-guardrails-can-do.md` (what the numbers mean). The concepts are in Chapter 8 (`docs/c1/ch08-red-teaming-and-guardrails.md`). This README is the quick reference.

| | Lab 8.1: Measure and break | Lab 8.2: Reading the results |
|---|---|---|
| **Course / chapter** | 1 AI/LLM Security / Chapter 8 | same |
| **Time** | 40 minutes (a full run of one guardrail takes 2 to 5 minutes on a CPU) | 10 minutes to read |
| **Estimated cost** | $0 (local victim model, local judge) | $0 |
| **Models** | `bdai-victim` (Qwen3 1.7B, local) as the bot and as the judge, `bdai-embed` | none |
| **Needs** | Gateway and local model server running (Chapter 0) | nothing |
| **Flag** | `BDAI{...}`, shown in the console when all four missions are done | none |

## Start

```bash
./shared/scripts/console-up.sh labs/c1-llm/ch08-securing-the-pipeline/redteam-lab/compose.yaml
```

Open <http://127.0.0.1:8300>. Two containers run: `bdai-console` (on the internal lab network) and `bdai-console-edge` (publishes `127.0.0.1:8300`). `./shared/scripts/down.sh c1` removes both, and the data volume.

## Files

```
app/probes.py       the attack library (10 probes) and the detectors that decide whether each worked, plus the normal questions
app/guardrails.py   the five guardrails, each a few lines, and respond(): one question through one guardrail
app/harness.py      runs every probe and every normal question N times and reports attack success and utility
app/trailbot.py     TrailBot with a secret in its prompt and four hooks (the Chapter 3 bot)
app/progress.py     mission progress and the flag
app/console.py      the web console backend
corpus/ inbox/ web/   TrailBot's knowledge base (the same as Labs 3 to 7)
```

The harness is a small version of what garak, promptfoo and PyRIT do: a library of attacks, a target, detectors, a report. Those tools are worth running against a real system, and the Chapter 8 page says how to point them at this lab's gateway.

## Troubleshooting

| Symptom | Cause and fix |
|---|---|
| `network bdai-llm declared as external` | The gateway is not running. Start it: `./shared/scripts/start.sh` |
| A run stops with "The model did not answer" | The gateway or the local model server is down, or WSL's address for Windows changed after a reboot. Start Ollama, then `./shared/scripts/start.sh`. |
| Results differ a little from the lab page | Model output is sampled. Run with 2 or 3 times per attack for steadier numbers. |
| Browser shows "No lab console is running" | Start it with the command above. |
