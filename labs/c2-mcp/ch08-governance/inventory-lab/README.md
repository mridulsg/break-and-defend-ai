# Labs 8.1 and 8.2: a shadow-MCP inventory

Walkthroughs: `docs/c2/lab-8-1-find-the-shadow-servers.md` and `docs/c2/lab-8-2-a-standing-process.md`. Concepts: `docs/c2/ch08-mcp-supply-chain-and-governance.md`.

| | Lab 8.1 | Lab 8.2 |
|---|---|---|
| **Time** | 25 minutes | 10 minutes to read |
| **Estimated cost** | $0 (no model) | $0 |
| **Needs** | Docker; the gateway network must exist | nothing |
| **Flag** | `BDAI{...}` when all three missions are done | none |

## Start

```bash
./shared/scripts/console-up.sh labs/c2-mcp/ch08-governance/inventory-lab/compose.yaml
```

Open <http://127.0.0.1:8300>. `./shared/scripts/down.sh c2` removes everything.

## Files

```
app/inventory.py   reads the configs, compares with the registry, flags risk, enforces the approval bar
app/console.py     the console, the decisions and the missions
configs/           four made-up engineers' MCP config files (only ever read)
registry.json      the servers the company approved
```

## Troubleshooting

| Symptom | Cause and fix |
|---|---|
| `network bdai-llm declared as external` | Start the gateway: `./shared/scripts/start.sh` |
