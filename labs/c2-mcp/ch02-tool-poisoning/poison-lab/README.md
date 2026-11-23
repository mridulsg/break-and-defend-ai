# Labs 2.1 and 2.2: tool poisoning, shadowing and rug pulls

The walkthroughs are the lab pages: `docs/c2/lab-2-1-poison-a-server.md` (attack) and `docs/c2/lab-2-2-defences.md` (the defences). The concepts are in Chapter 2 (`docs/c2/ch02-tool-poisoning-rug-pulls-and-shadowing.md`). This README is the quick reference.

| | Lab 2.1: Attacks | Lab 2.2: Defences |
|---|---|---|
| **Course / chapter** | 2 MCP Security / Chapter 2 | same |
| **Time** | 40 minutes | 10 minutes to read |
| **Estimated cost** | $0 (local model) | $0 |
| **Models** | `bdai-victim` (Qwen3 1.7B, local) | none |
| **Needs** | Gateway and local model server running | nothing |
| **Flag** | `BDAI{...}`, shown in the console when all three missions are done | none |

## Start

```bash
./shared/scripts/console-up.sh labs/c2-mcp/ch02-tool-poisoning/poison-lab/compose.yaml
```

Open <http://127.0.0.1:8300>. Two containers run: `bdai-console` (on the internal lab network, with three MCP servers inside it) and `bdai-console-edge` (publishes `127.0.0.1:8300`). `./shared/scripts/down.sh c2` removes both, and the data volume.

## Files

```
app/console.py    the community server docs-helper, the "publish a server" page, the missions, and the host defences (HostDefences)
app/progress.py   mission progress and the flag
shared/mcp/       mcpmini.py (a small MCP implementation), host.py (the assistant), acme.py (Acme's notes and tickets), labkit.py (the console backend)
```

The defences are in `HostDefences` and switch on with the **Fixes** switch in the console. You publish by editing the description on the console page; nothing else needs to be written.

## Troubleshooting

| Symptom | Cause and fix |
|---|---|
| `network bdai-llm declared as external` | The gateway is not running. Start it: `./shared/scripts/start.sh` |
| The assistant says it could not get an answer | The gateway or the local model server is down. Start Ollama, then `./shared/scripts/start.sh`. |
| An attack worked once and then not | Model output is sampled. Try again, or change the wording: wording is the attack. |
| Browser shows "No lab console is running" | Start it with the command above. |
