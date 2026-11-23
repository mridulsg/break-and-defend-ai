# Labs 3.1 and 3.2: flaws in MCP server code

The walkthroughs are the lab pages: `docs/c2/lab-3-1-attack-the-tools.md` (attack) and `docs/c2/lab-3-2-fixes.md` (the fixes). The concepts are in Chapter 3 (`docs/c2/ch03-attacking-mcp-servers.md`). This README is the quick reference.

| | Lab 3.1: Attacks | Lab 3.2: Fixes |
|---|---|---|
| **Course / chapter** | 2 MCP Security / Chapter 3 | same |
| **Time** | 30 minutes | 10 minutes to read |
| **Estimated cost** | $0 | $0 |
| **Models** | none needed (the assistant chat is optional) | none |
| **Needs** | Docker; the gateway network must exist | nothing |
| **Flag** | `BDAI{...}`, shown when all three missions are done | none |

## Start

```bash
./shared/scripts/console-up.sh labs/c2-mcp/ch03-server-flaws/servers-lab/compose.yaml
```

Open <http://127.0.0.1:8300>. `./shared/scripts/down.sh c2` removes everything.

## Files

```
app/console.py    the devtools server (three flawed tools and their fixes), an internal service on port 9200, and the missions
app/progress.py   mission progress and the flag
srv/docs/         the docs the tool is meant to serve
srv/secrets/      made-up secrets the tools must not reveal
```

## Is this safe to run?

`check_host` really runs a shell command, so the lab runs it with an empty environment in `/tmp`, inside a container with a read-only filesystem, no capabilities and no published ports. All secrets are made up. Never point these techniques at a system you do not own.

## Troubleshooting

| Symptom | Cause and fix |
|---|---|
| `network bdai-llm declared as external` | Start the gateway: `./shared/scripts/start.sh` |
| Browser shows "No lab console is running" | Start it with the command above. |
