# Lab 9.3: scan model files with real tools

The walkthrough is the lab page `docs/c1/lab-9-3-scan-with-real-tools.md`. The concepts are in Chapter 9 (`docs/c1/ch09-ai-supply-chain.md`).

| | Lab 9.3 |
|---|---|
| **Course / chapter** | 1 AI/LLM Security / Chapter 9 |
| **Time** | 20 minutes (about a minute more the first time, while the image builds) |
| **Estimated cost** | $0 (no model) |
| **Disk** | about 300 MB for the image |
| **Needs** | Docker only |

## Start

```bash
docker compose --env-file .env -f labs/c1-llm/ch09-ai-supply-chain/scanner-lab/compose.yaml run --rm tools
```

You get a shell in `/models` with `picklescan`, `modelscan` and `fickling` installed, and Python's `pickletools`. The container has no network, a read-only filesystem and the sample model files mounted read-only.

`./shared/scripts/down.sh c1` removes everything (add `--purge` to delete the image).

## Files

The sample files are the ones from Lab 9.1 (`labs/c1-llm/ch09-ai-supply-chain/supply-lab/models/`). The tools come from `shared/toolbox/modelscanners`: `requirements.in` names them and `requirements.txt` is generated with a hash for every file.

## Troubleshooting

| Symptom | Cause and fix |
|---|---|
| The first start is slow | The image is building. Later starts are instant. |
| `picklescan: command not found` | You are not in the lab container. Start it with the command above. |
