# Lab 9.1: the Course 2 capstone

Walkthrough: `docs/c2/lab-9-1-assess-an-mcp-deployment.md`. Concepts: `docs/c2/ch09-capstone-assess-an-mcp-deployment.md`.

| | Lab 9.1 |
|---|---|
| **Time** | 45 minutes |
| **Estimated cost** | $0 (no model) |
| **Needs** | Docker; the gateway network must exist |
| **Flag** | `BDAI{...}` when all five missions are done |

## Start

```bash
./shared/scripts/console-up.sh labs/c2-mcp/ch09-capstone/assessment-lab/compose.yaml
```

Open <http://127.0.0.1:8300>. `./shared/scripts/down.sh c2` removes everything.

## Files

```
app/console.py    the three servers, the seeded problems, the fixes, the register and the retest
app/progress.py   mission progress and the flag
srv/              made-up docs and secrets
```

## Troubleshooting

| Symptom | Cause and fix |
|---|---|
| `network bdai-llm declared as external` | Start the gateway: `./shared/scripts/start.sh` |
| Every tickets call says 401 | The token needs minting (the box on the Tool tester). Tokens reset when the console restarts. |
