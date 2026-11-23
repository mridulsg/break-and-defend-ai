# Labs 3.1 and 3.2: Prompt injection attacks and fixes

The full walkthroughs, with expected output, are the lab pages: `docs/c1/lab-3-1-break-trailbot.md` and `docs/c1/lab-3-2-defend-trailbot.md` (on the docs site: "Lab 3.1" and "Lab 3.2"). The concepts are in Chapter 3 (`docs/c1/ch03-prompt-injection.md`). This README is the quick reference.

| | Lab 3.1: Attacks | Lab 3.2: Fixes |
|---|---|---|
| **Course / chapter** | 1 AI/LLM Security / Chapter 3 | same |
| **Time** | 45 minutes | 60 minutes |
| **Estimated cost** | $0 (local victim model) | $0 (local victim model). Optional hosted comparison: about $0.01. |
| **Models** | `bdai-victim` (Qwen3 1.7B, local), `bdai-embed` | same, plus optional `bdai-default` |
| **Needs** | Gateway and local model server running (Chapter 0) | same |
| **Flag** | `BDAI{...}` from `check.py` | `BDAI{...}` from `bench.py` |

## The web console (start here)

```bash
./shared/scripts/console-up.sh labs/c1-llm/ch03-prompt-injection/injection-lab/compose.yaml
```

Open <http://127.0.0.1:8300>: a chat window on TrailBot, a "Behind the scenes" panel showing exactly what the model read, a feedback form for planting notes, and a Missions page with the flag. It re-reads `defences/defences.py` on every question. The command-line tools below share the same index, secret and progress. Two containers run: `bdai-console` (on the internal lab network) and `bdai-console-edge` (publishes `127.0.0.1:8300` and forwards to the console). `./shared/scripts/down.sh c1` removes both.

## Files

```
app/console.py         the web console backend (a thin layer over trailbot.py and check.py)
app/trailbot.py        TrailBot with a secret in its system prompt and four defence hooks (read it)
app/attacks.py         the attack suite: every attack is a few lines of plain text (read it)
app/bench.py           runs the attack suite N times against a set of defences and prints success rates
app/check.py           Lab 3.1 grader: leak the secret, plant a working note
defences/defences.py   YOUR defences (Lab 3.2): four hooks, as shipped they do nothing
defences/prompt_tags.py, prompt_hardened.py   two prompt-level defences to measure (do not edit)
corpus/ inbox/ web/    the knowledge base (the same as Lab 1.1, without the staff-discount file)
```

## Commands

Open a shell in the lab (from the repository root):

```bash
docker compose --env-file .env -f labs/c1-llm/ch03-prompt-injection/injection-lab/compose.yaml run --build --rm app
```

Inside the shell the lab folder is `/lab`:

```bash
python /lab/app/trailbot.py index                         # build the index and create the secret code
python /lab/app/trailbot.py ask "..." --show-prompt       # ask, and see exactly what the model receives
python /lab/app/trailbot.py ask "..." --model bdai-default  # the same question on a hosted model
python /lab/app/check.py leak ESC-XXXXXX                  # Lab 3.1: prove you extracted the code
python /lab/app/check.py indirect                         # Lab 3.1: test your planted note
python /lab/app/check.py status                           # Lab 3.1: progress
python /lab/app/bench.py                                  # Lab 3.2: measure your defences
python /lab/app/bench.py --defences prompt_tags           # Lab 3.2: measure a shipped prompt-level defence
python /lab/app/bench.py --model bdai-default --n 3       # Lab 3.2: the same attacks on a hosted model
```

On your host you edit `inbox/` (Lab 3.1) and `defences/defences.py` (Lab 3.2). After changing `inbox/`, run `index` again.

## Troubleshooting

| Symptom | Cause and fix |
|---|---|
| `network bdai-llm declared as external` | The gateway is not running. Start it: `./shared/scripts/start.sh` |
| `The local model server is unreachable from the gateway` | Ollama is not running, or WSL's address for Windows changed (after a Windows reboot). Start Ollama, then run `./shared/scripts/start.sh`. |
| `No index yet` | Run `python /lab/app/trailbot.py index` first. |
| `No secret yet` | The secret is created by `index`. |
| `bench.py` says your index has more than 14 chunks | You still have a note of your own in `inbox/` on the host. Delete it and run `index` again. (Notes from the web console are ignored automatically.) |
| Browser shows "No lab console is running" | Start it: `./shared/scripts/console-up.sh labs/c1-llm/ch03-prompt-injection/injection-lab/compose.yaml` |
| Console says "TrailBot could not get an answer from the model" | Same causes as the gateway rows above: the gateway or the local model server is down. |
| Console shows "Your defences/defences.py could not be loaded" | A mistake in your hooks. The message names the error. Fix the file and ask again; no restart needed. |
| Results differ a little from the lab page | Model output is sampled. Run with `--n 5`. Differences of one trial are normal. |
| Slow answers | The local model loads on first use. A full `bench.py` takes a few minutes. |

## Cleanup

```bash
./shared/scripts/down.sh c1            # remove containers and the index/secret volume
./shared/scripts/down.sh c1 --purge    # also delete Course 1 images
```
