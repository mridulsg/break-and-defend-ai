# Labs 6.1 and 6.2: hidden text in images

The walkthroughs are the lab pages: `docs/c1/lab-6-1-images-that-fool-machines.md` (attack) and `docs/c1/lab-6-2-fixes.md` (the fixes). The concepts are in Chapter 6 (`docs/c1/ch06-multimodal-attacks.md`). This README is the quick reference.

| | Lab 6.1: Attacks | Lab 6.2: Fixes |
|---|---|---|
| **Course / chapter** | 1 AI/LLM Security / Chapter 6 | same |
| **Time** | 15 minutes | 5 minutes to read |
| **Estimated cost** | $0 with the local model. Optional hosted vision: about $0.003 per image. | $0 |
| **Models** | `bdai-victim` (Qwen3 1.7B, local) behind an OCR reader; optional `bdai-default` (hosted, sees images) | none |
| **Needs** | Gateway and local model server running (Chapter 0) | nothing |
| **Flag** | `BDAI{...}`, shown in the console when the mission is done | none |

## Start

```bash
./shared/scripts/console-up.sh labs/c1-llm/ch06-multimodal-attacks/vision-lab/compose.yaml
```

Open <http://127.0.0.1:8300>. Two containers run: `bdai-console` (on the internal lab network) and `bdai-console-edge` (publishes `127.0.0.1:8300`). `./shared/scripts/down.sh c1` removes both, and the data volume.

## Files

```
app/reader.py       the receipt reader: contrast boost, Tesseract (text recognition), and what the model is given
app/png.py          a small PNG reader/writer (standard library only) that measures how visible text is
app/progress.py     mission progress and the flag
app/console.py      the web console backend
```

The receipt image is drawn in your browser and uploaded as a PNG. The reader runs `tesseract` (installed in the Course 1 toolbox image, about 150 MB extra) in the console container, with no network.

## Troubleshooting

| Symptom | Cause and fix |
|---|---|
| `network bdai-llm declared as external` | The gateway is not running. Start it: `./shared/scripts/start.sh` |
| Console says "TrailBot could not get an answer from the model" | The gateway or the local model server is down (or WSL's address for Windows changed after a reboot). Start Ollama, then `./shared/scripts/start.sh`. |
| "The text reader failed on that image" | The image was too large or Tesseract timed out. Use a smaller text size. |
| The reader does not find my faint text | At 0% visible the text is exactly the colour of the paper, so nothing can read it. Try 2% to 12%, and a size of 14 or more. |
| The reader misreads some digits | Normal for text recognition. The attack still works. |
| Browser shows "No lab console is running" | Start it with the command above. |
