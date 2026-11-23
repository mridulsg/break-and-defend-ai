# Labs 7.1 and 7.2: a security gate in the build pipeline

Walkthroughs: `docs/c2/lab-7-1-run-the-pipeline.md` and `docs/c2/lab-7-2-gate-and-limits.md`. Concepts: `docs/c2/ch07-devsecops-for-mcp-servers.md`.

| | Lab 7.1 | Lab 7.2 |
|---|---|---|
| **Time** | 25 minutes | 10 minutes to read |
| **Estimated cost** | $0 (no model) | $0 |
| **Needs** | Docker; the gateway network must exist | nothing |
| **Flag** | `BDAI{...}` when all three missions are done | none |

## Start

```bash
./shared/scripts/console-up.sh labs/c2-mcp/ch07-devsecops/pipeline-lab/compose.yaml
```

Open <http://127.0.0.1:8300>. `./shared/scripts/down.sh c2` removes everything.

## Files

```
app/mcpscan.py     the scanner (every rule is readable) and the gate
app/console.py     the console and missions
projects/vulnerable, projects/fixed    the same server before and after review (read as text, never run)
```

## Troubleshooting

| Symptom | Cause and fix |
|---|---|
| `network bdai-llm declared as external` | Start the gateway: `./shared/scripts/start.sh` |
