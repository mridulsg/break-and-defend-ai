# Lab 1.1: explore MCP and map its trust boundaries

The walkthrough is the lab page `docs/c2/lab-1-1-explore-mcp.md`. The concepts are in Chapter 1 (`docs/c2/ch01-mcp-architecture-and-attack-surface.md`). This README is the quick reference.

| | Lab 1.1 |
|---|---|
| **Course / chapter** | 2 MCP Security / Chapter 1 |
| **Time** | 30 minutes |
| **Estimated cost** | $0 (local model) |
| **Models** | `bdai-victim` (Qwen3 1.7B, local) |
| **Needs** | Gateway and local model server running (Chapter 0 of Course 1) |
| **Flag** | `BDAI{...}`, shown in the console when all four missions are done |

## Start

```bash
./shared/scripts/console-up.sh labs/c2-mcp/ch01-mcp-architecture/mcp-lab/compose.yaml
```

Open <http://127.0.0.1:8300>. Two containers run: `bdai-console` (on the internal lab network, with both MCP servers inside it) and `bdai-console-edge` (publishes `127.0.0.1:8300`). `./shared/scripts/down.sh c2` removes both, and the data volume.

## Files

```
app/console.py    builds the two servers and the missions, then starts the console
app/progress.py   mission progress and the flag
shared/mcp/       mcpmini.py (a small MCP implementation, tools only), host.py (the assistant), acme.py (the two servers), labkit.py (the console backend)
```

`mcpmini.py` follows the 2026-07-28 MCP wire format for the messages the labs use, and leaves out everything else, so you can read all of it. Real projects use an official SDK.

## Troubleshooting

| Symptom | Cause and fix |
|---|---|
| `network bdai-llm declared as external` | The gateway is not running. Start it: `./shared/scripts/start.sh` |
| The assistant says it could not get an answer | The gateway or the local model server is down (or WSL's address for Windows changed after a reboot). Start Ollama, then `./shared/scripts/start.sh`. |
| Browser shows "No lab console is running" | Start it with the command above. |
