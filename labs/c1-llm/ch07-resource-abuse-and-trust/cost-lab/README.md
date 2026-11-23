# Labs 7.1 and 7.2: cost and trust

The walkthroughs are the lab pages: `docs/c1/lab-7-1-cost-and-trust.md` (attack) and `docs/c1/lab-7-2-fixes.md` (the fixes). The concepts are in Chapter 7 (`docs/c1/ch07-unbounded-consumption-and-misinformation.md`). This README is the quick reference.

| | Lab 7.1: Attacks | Lab 7.2: Fixes |
|---|---|---|
| **Course / chapter** | 1 AI/LLM Security / Chapter 7 | same |
| **Time** | 25 minutes (a long reply takes about a minute on a CPU) | 5 minutes to read |
| **Estimated cost** | $0 (local victim model). The page shows what the same traffic would cost on a hosted model. | $0 |
| **Models** | `bdai-victim` (Qwen3 1.7B, local), `bdai-embed` | none |
| **Needs** | Gateway and local model server running (Chapter 0) | nothing |
| **Flag** | `BDAI{...}`, shown in the console when all three missions are done | none |

## Start

```bash
./shared/scripts/console-up.sh labs/c1-llm/ch07-resource-abuse-and-trust/cost-lab/compose.yaml
```

Open <http://127.0.0.1:8300>. Two containers run: `bdai-console` (on the internal lab network) and `bdai-console-edge` (publishes `127.0.0.1:8300`). `./shared/scripts/down.sh c1` removes both, and the data volume.

## Files

```
app/trailbot.py    TrailBot: retrieval, then the model answers. As shipped: no limit on the reply, no input limit, no budget, no check on what it says.
app/dev.py         the dev assistant: recommends `pip install` lines, and nothing checks the package exists
app/progress.py    mission progress and the flag
app/console.py     the web console backend (usage meter, the fixes, mission detection)
data/registry.txt  101 real Python package names: a stand-in for the package index (PyPI)
corpus/ inbox/ web/   TrailBot's knowledge base (the same as Labs 3 to 6)
```

## Troubleshooting

| Symptom | Cause and fix |
|---|---|
| `network bdai-llm declared as external` | The gateway is not running. Start it: `./shared/scripts/start.sh` |
| Console says "The model did not answer" | The gateway or the local model server is down, or the request ran out of time (a reply of 1,500 tokens takes about 90 seconds on a CPU, and a much longer one can time out at the gateway). Ask for a slightly shorter reply. |
| The reply is short even though I asked for a long one | Model output is sampled. Ask for a list, or for something to be repeated, and try again. |
| Browser shows "No lab console is running" | Start it with the command above. |
