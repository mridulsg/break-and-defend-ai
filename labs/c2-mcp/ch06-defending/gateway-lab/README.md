# Labs 6.1 and 6.2: a gateway in front of MCP servers

Walkthroughs: `docs/c2/lab-6-1-build-the-defence.md` and `docs/c2/lab-6-2-limits-of-each-control.md`. Concepts: `docs/c2/ch06-defending-mcp-with-a-gateway.md`.

| | Lab 6.1 | Lab 6.2 |
|---|---|---|
| **Time** | 25 minutes | 10 minutes to read |
| **Estimated cost** | $0 (no model) | $0 |
| **Needs** | Docker; the gateway network must exist | nothing |
| **Flag** | `BDAI{...}` when all three missions are done | none |

## Start

```bash
./shared/scripts/console-up.sh labs/c2-mcp/ch06-defending/gateway-lab/compose.yaml
```

Open <http://127.0.0.1:8300>. `./shared/scripts/down.sh c2` removes everything.

## Files

```
app/console.py    the Gateway class (six controls), the attack suite (A1 to A5, L1 to L3) and the missions
app/progress.py   mission progress and the flag
```

## Troubleshooting

| Symptom | Cause and fix |
|---|---|
| `network bdai-llm declared as external` | Start the gateway: `./shared/scripts/start.sh` |
