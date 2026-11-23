# Lab 11.1: the capstone assessment

The walkthrough is the lab page `docs/c1/lab-11-1-assess-fix-and-retest.md`. The concepts are in Chapter 11 (`docs/c1/ch11-capstone-assessment.md`). This README is the quick reference.

| | Lab 11.1: Assess, report, fix and retest |
|---|---|
| **Course / chapter** | 1 AI/LLM Security / Chapter 11 |
| **Time** | 45 minutes |
| **Estimated cost** | $0 (local victim model) |
| **Models** | `bdai-victim` (Qwen3 1.7B, local), `bdai-embed` |
| **Needs** | Gateway and local model server running (Chapter 0) |
| **Flag** | `BDAI{...}`, shown in the console when all five missions are done |

## Start

```bash
./shared/scripts/console-up.sh labs/c1-llm/ch11-capstone/assessment-lab/compose.yaml
```

Open <http://127.0.0.1:8300>. The Website preview page is served from a second port, 8301, on purpose: it is a deliberately unsafe page, and a different port is a different origin, so the browser keeps its script away from the console. Two containers run: `bdai-console` (on the internal lab network) and `bdai-console-edge` (publishes `127.0.0.1:8300`). `./shared/scripts/down.sh c1` removes both, and the data volume.

## Files

```
app/orders.py      Acme's orders and the two tools (look up an order, issue a refund). Read it: it never asks who is asking.
app/trailbot.py    TrailBot with tools: retrieval, then a loop that lets the model call tools
app/progress.py    mission progress and the flag
app/console.py     the web console backend, including the risk register and the retest check
corpus/ inbox/ web/   the knowledge base (the same as Lab 4.1)
```

The people, addresses and card digits are made up.

## Troubleshooting

| Symptom | Cause and fix |
|---|---|
| `network bdai-llm declared as external` | The gateway is not running. Start it: `./shared/scripts/start.sh` |
| Console says "TrailBot could not get an answer from the model" | The gateway or the local model server is down (or WSL's address for Windows changed after a reboot). Start Ollama, then `./shared/scripts/start.sh`. |
| Browser shows "No lab console is running" | Start it with the command above. |
| TrailBot invents an order status instead of using its tool | The small local model sometimes answers from memory. Ask again, or word it as "Can you check order A-1001 for me?". |
| Results differ a little from the lab page | Model output is sampled. Differences between runs are normal. |
