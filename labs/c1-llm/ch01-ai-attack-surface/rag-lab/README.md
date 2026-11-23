# Lab 1.1: Explore TrailBot and map its trust boundaries

The full walkthrough, with expected output for every command, is the lab page: `docs/c1/lab-1-1-trailbot.md` (on the docs site: "Lab 1.1: Explore TrailBot and map its trust boundaries"). The concepts are in Chapter 1 (`docs/c1/ch01-ai-attack-surface.md`). This README is the quick reference.

| | |
|---|---|
| **Course / chapter** | 1 AI/LLM Security / Chapter 1 |
| **Time** | 40 minutes |
| **Estimated cost** | $0 (local victim model and local embeddings) |
| **Models** | `bdai-victim` (Qwen3 1.7B, local), `bdai-embed` (nomic-embed-text, local) |
| **Needs** | Gateway running, local model server running with both models pulled |
| **Disk** | Uses the shared Course 1 toolbox image (about 250 MB) |

## Files

```
app/rag.py        the TrailBot assistant (read it)
app/check.py      checks your classification and prints the flag
answers.json      your answers (edit this on your host)
corpus/           staff-written handbook
inbox/            customer-submitted notes
web/              an imported partner web page
```

## Commands

Open a shell in the lab (from the repository root):

```bash
docker compose --env-file .env -f labs/c1-llm/ch01-ai-attack-surface/rag-lab/compose.yaml run --build --rm app
```

The shell is inside a container: the lab folder appears there as `/lab` (run `ls` and you will see `app corpus inbox web answers.json`, not `labs/c1-llm/...`). To read the code there: `cat -n /lab/app/rag.py`. On your host it is `labs/c1-llm/ch01-ai-attack-surface/rag-lab/app/rag.py`.

Inside the shell:

```bash
python /lab/app/rag.py index                                  # build the vector index
python /lab/app/rag.py ask "Do you ship to Canada?"           # ask a question
python /lab/app/rag.py ask "..." --show-prompt                # print the exact prompt
python /lab/app/rag.py ask "..." --show-scores                # print each chunk's similarity to the question
python /lab/app/rag.py embed "some text"                      # see what the embedding model produces
python /lab/app/rag.py compare "text A" "text B"              # similarity of meaning, 0 to 1
python /lab/app/rag.py ask "..." --k 0                        # retrieval off
python /lab/app/rag.py ask "..." --temperature 1.5            # more variation (or 0 for repeatable output)
python /lab/app/rag.py ask "..." --model bdai-default         # use a hosted model instead
python /lab/app/check.py                                      # check answers.json, get the flag
```

## Troubleshooting

| Symptom | Cause and fix |
|---|---|
| `network bdai-llm declared as external` | The gateway is not running. Start it: `./shared/scripts/start.sh` |
| `The local model server is unreachable from the gateway` | Ollama is not running, or WSL's address for Windows changed (this happens after a Windows reboot). Start Ollama, then run `./shared/scripts/start.sh`. |
| `model "bdai-embed"` or `qwen3:1.7b` not found | Pull the models: `ollama pull qwen3:1.7b` and `ollama pull nomic-embed-text` |
| `No index yet` | Run `python /lab/app/rag.py index` inside the shell first. |
| Edited a file in `inbox/` but the answer did not change | Re-run `index`. The index is built once and kept in a volume. |
| Slow first answer | The local model loads into memory on first use. Later calls are faster. |

## Cleanup

```bash
./shared/scripts/down.sh c1            # remove containers and the index volume
./shared/scripts/down.sh c1 --purge    # also delete Course 1 images
```
