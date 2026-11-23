# Lab 8.3: run garak, a real red-team scanner

The walkthrough is the lab page `docs/c1/lab-8-3-run-garak.md`. The concepts are in Chapter 8 (`docs/c1/ch08-red-teaming-and-guardrails.md`).

| | Lab 8.3 |
|---|---|
| **Course / chapter** | 1 AI/LLM Security / Chapter 8 |
| **Time** | 15 minutes, plus about 7 minutes the first time while the image builds |
| **Estimated cost** | $0 (the target is the local model) |
| **Disk** | about 3 GB for the image (CPU-only, every package pinned by hash) |
| **Needs** | Gateway and local model server running (Chapter 0) |

## Run the quick scan

```bash
docker compose --env-file .env -f labs/c1-llm/ch08-securing-the-pipeline/garak-lab/compose.yaml run --rm garak
```

Then read the report:

```bash
docker compose --env-file .env -f labs/c1-llm/ch08-securing-the-pipeline/garak-lab/compose.yaml run --rm garak python /lab/summarise.py
```

Remove the container, volume and (optionally) the image with `./shared/scripts/down.sh c1` (add `--purge` to delete the image).

## Files

```
garak-options.json   tells garak where the target is: the lab's gateway, model bdai-victim
summarise.py         reads garak's report and prints one line per probe and a few real replies
compose.yaml         the scanner container: read-only filesystem, no capabilities, no internet, only the gateway
```

The scanner image is built from `shared/toolbox/redteam`: `requirements.in` names garak and CPU-only torch, and `requirements.txt` is generated from it with a hash for every file.

## Troubleshooting

| Symptom | Cause and fix |
|---|---|
| `target URI is not reachable` | The gateway is not running, or Docker's lab network is stuck. Start the gateway: `./shared/scripts/start.sh` |
| The first run takes several minutes before garak starts | The image is building (about 3 GB). Later runs start at once. |
| A run is slow | The target is a small model on a CPU. The quick scan takes about a minute; longer probes take minutes. |
