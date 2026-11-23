# Labs 4.1 and 4.2: MCP authentication and authorization

Walkthroughs: `docs/c2/lab-4-1-break-the-token-checks.md` (attack) and `docs/c2/lab-4-2-fixes.md` (the checks). Concepts: `docs/c2/ch04-mcp-authentication-and-authorization.md`.

| | Lab 4.1 | Lab 4.2 |
|---|---|---|
| **Time** | 30 minutes | 10 minutes to read |
| **Estimated cost** | $0 (no model) | $0 |
| **Needs** | Docker; the gateway network must exist | nothing |
| **Flag** | `BDAI{...}` when all three missions are done | none |

## Start

```bash
./shared/scripts/console-up.sh labs/c2-mcp/ch04-auth/auth-lab/compose.yaml
```

Open <http://127.0.0.1:8300>. `./shared/scripts/down.sh c2` removes everything.

## Files

```
app/console.py    the auth server (mint), two token-checking servers (verify, need), the missions
app/progress.py   mission progress and the flag
```

The signing key is random on every start, so tokens from an earlier run stop working after a restart.

## Troubleshooting

| Symptom | Cause and fix |
|---|---|
| `network bdai-llm declared as external` | Start the gateway: `./shared/scripts/start.sh` |
| Every call says 401 | The token is from before a restart, or has expired. Mint a new one. |
