# Lab 6.1 (Course 3): the capstone

Walkthrough: `docs/c3/lab-6-1-assess-an-agent-platform.md`. Concepts: `docs/c3/ch06-capstone-assess-an-agent-platform.md`.

| | Lab 6.1 |
|---|---|
| **Time** | 40 minutes |
| **Estimated cost** | $0 (no model) |
| **Needs** | Docker; the gateway network must exist |
| **Flag** | `BDAI{...}` when all three missions are done |

## Start

```bash
./shared/scripts/console-up.sh labs/c3-agents/ch06-capstone/assessment-lab/compose.yaml
```

Open <http://127.0.0.1:8300>. `./shared/scripts/down.sh c3` removes everything.

## Files

```
app/console.py     the three probes, six controls, the register and the missions
shared/agents/     sim.py (the agent platform), suitekit.py (the console backend)
```

## Troubleshooting

| Symptom | Cause and fix |
|---|---|
| `network bdai-llm declared as external` | Start the gateway: `./shared/scripts/start.sh` |
