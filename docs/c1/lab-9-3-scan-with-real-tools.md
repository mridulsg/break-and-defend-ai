# Lab 9.3: Scan model files with real tools

## What this lab is about

In Lab 9.1 you read a model file's steps yourself. Real teams use scanners to do that reading at scale. You run three widely used ones, **picklescan**, **modelscan** and **fickling**, on the lab's files, and compare what they say. They do not always agree.

| | What you will do |
|---|---|
| **Read** | Read the steps with Python's `pickletools`, and rebuild the file as Python with fickling. |
| **Scan** | Run picklescan and modelscan on the same files. |
| **Compare** | Scan three harmless pickles and see which tools flag what. |

!!! info "Lab facts"
    **Time:** 20 minutes, plus about 1 minute the first time while the image builds (300 MB). **Cost:** nothing, no model. **Needs:** Docker only. **Folder:** `labs/c1-llm/ch09-ai-supply-chain/scanner-lab/`.

!!! warning "Only read, never load"
    The container has **no network**, a read-only filesystem and the model files mounted read-only. Scanners read the steps and do not run them. Never load a downloaded model to find out what it does.

## Start a shell in the scanner container

From the repository root:

```bash
docker compose --env-file .env -f labs/c1-llm/ch09-ai-supply-chain/scanner-lab/compose.yaml run --rm tools
```

You are in `/models`, which holds the three sample files from Lab 9.1: `sentiment-v1.pkl` (clean), `sentiment-community.pkl` (it calls `posix.mkdir` when loaded) and `sentiment-v1.json` (plain data). Everything below runs in that shell. Type `exit` to leave.

## Step 1: Read it yourself

```bash
python -m pickletools sentiment-community.pkl | head -12
```

Find `GLOBAL 'posix mkdir'` and the `REDUCE` that calls it. Now the same file as Python, rebuilt by **fickling**:

```bash
fickling sentiment-community.pkl
```

```
from posix import mkdir
_var0 = mkdir('/tmp/bdai-proof-of-code-execution')
result0 = {'model': 'acme-sentiment', ... }
```

That is what loading the file would do, in three lines of Python you can read. The first two are the attack.

## Step 2: Run the scanners

```bash
picklescan --path /models
```

```
/models/sentiment-community.pkl: dangerous import 'posix mkdir' FOUND
----------- SCAN SUMMARY -----------
Scanned files: 2
Infected files: 1
Dangerous globals: 1
```

```bash
modelscan scan -p /models
```

modelscan reports one **CRITICAL** issue: "Use of unsafe operator 'mkdir' from module 'posix'" in the community file, and nothing for the clean one. Then fickling's safety check, which answers with its **exit code** (0 safe, 1 unsafe):

```bash
fickling --check-safety sentiment-v1.pkl;        echo "exit code: $?"
fickling --check-safety sentiment-community.pkl; echo "exit code: $?"
```

All three agree on the community file. A pipeline would use exactly this: run a scanner, fail the build on a non-zero exit code.

## Step 3: Make them disagree

Make three pickles that only import **harmless** functions, and scan them:

```bash
python - <<'PY'
import pickle, os, math, builtins
for name, obj in (("harmless-sqrt", math.sqrt), ("harmless-getcwd", os.getcwd), ("harmless-print", builtins.print)):
    pickle.dump(obj, open(f"/tmp/{name}.pkl", "wb"), protocol=2)
PY
for f in harmless-sqrt harmless-getcwd harmless-print; do
  echo "=== $f"; picklescan --path /tmp/$f.pkl | grep -E "FOUND|Suspicious"
  modelscan scan -p /tmp/$f.pkl | grep -E "Total Issues:|No issues"
  fickling --check-safety /tmp/$f.pkl; echo "fickling exit code: $?"
done
```

In our run:

| Pickle imports | picklescan | modelscan | fickling |
|---|---|---|---|
| `math.sqrt` | suspicious | no issues | safe (0) |
| `os.getcwd` | **dangerous** | **issue** | **unsafe (1)** |
| `builtins.print` | suspicious | no issues | **unsafe (1)** |

None of these three does any harm: `sqrt` computes a number, `getcwd` reads the current folder, `print` prints. Yet the tools disagree, because each one works from its **own rule list**. `os.getcwd` is on all three lists (by its module), `builtins.print` only on fickling's, `math.sqrt` on picklescan's "suspicious" list only. That is the limit of every list-based scanner, in both directions: it can flag harmless code, and it can miss a payload made from something that is not on the list.

## What to take from it

- **You can read it yourself.** `pickletools` shows the steps. A scanner is a faster way to read many files.
- **Scanners are lists of bad functions.** A new payload, or an unusual route to a known one, can pass. A published analysis found many models flagged by pickle scanning were false positives, and researchers have shown files that slipped past popular scanners until they were patched.
- **Use more than one, and keep the result as evidence.** In a pipeline, fail the build on a non-zero exit code, and record what was scanned and with which version.
- **A clean scan means "not obviously bad".** The stronger fixes are formats with no steps (safetensors, JSON) and loading only what you trust, in a place you can throw away.

## Clean up

```bash
./shared/scripts/down.sh c1
```

Add `--purge` to delete the 300 MB image too.
