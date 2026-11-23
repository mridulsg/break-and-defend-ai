# Lab 9.2: Fixes for model files and packages

In [Lab 9.1](lab-9-1-model-files-and-packages.md) you scanned a model file, ran code by loading it, and audited a package list. This page shows the fixes. Nothing to run here.

## Fix 1: Do not load a model that can hold steps

Prefer a file format that cannot contain code. For real models that is **safetensors**. If you have to load a pickle, only open files from a source you trust and read them first.

```python
from safetensors.torch import load_file     # reads numbers only: there is nothing in the file that can run
weights = load_file("model.safetensors")

# if a pickle cannot be avoided, at least tell PyTorch to read plain weights only
import torch
weights = torch.load("model.pt", weights_only=True)
```

**Result in the lab:** the safe loader refused `sentiment-community.pkl` before the first step ran, and loaded `sentiment-v1.json` without trouble.

**What it costs:** models published only as pickles must be converted by someone you trust, or avoided. And `weights_only=True` is a setting, not a guarantee, so keep your tools up to date and still scan files you did not make.

## Fix 2: Read before loading, with a real scanner, in a place you can throw away

```bash
python -m pickletools download.pkl          # read the steps yourself: look for GLOBAL and REDUCE
picklescan --path download.pkl              # a list-based scanner
modelscan scan -p download.pkl              # the same idea, more formats
fickling --check-safety download.pkl        # exit code 1 if it looks unsafe
```

Run these, and any loading you cannot avoid, in a container with no secrets, no network and a read-only filesystem, as the lab does. [Lab 9.3](lab-9-3-scan-with-real-tools.md) runs all four.

**What it costs and what it misses:** scanners mostly know a list of bad functions. A payload built from something not on the list can pass, and harmless code can be flagged (Lab 9.3 shows the three tools disagreeing). Treat a clean scan as "not obviously bad", never as "safe".

## Fix 3: Pin exact versions with hashes

```
# requirements.in: what you ask for
requests==2.31.0
pydantic==2.5.0

# requirements.txt: generated, with a hash for every file (pip-compile --generate-hashes)
requests==2.31.0 --hash=sha256:...
pydantic==2.5.0  --hash=sha256:...
```

```bash
pip install --require-hashes -r requirements.txt
```

**Result:** only the exact files you reviewed install. A malicious new release, like the one that hit `litellm` in March 2026, does not arrive on its own, because nothing says "latest". This repository's own lab images are built this way.

**What it costs:** updating is now a deliberate step. Schedule it, review the change, and generate new hashes.

## Fix 4: An approved list and one package server

```python
if name not in APPROVED:
    raise ReviewNeeded(f"{name} is not on the approved list")
```

```
# one index, not two: remove this line and mirror what you need from your own server
--extra-index-url https://packages.acme-internal.example/simple
```

**Result:** the typosquats (`reqeusts`, `python-dateutils`) and the unknown `fast-tokenizer-pro` stop at review instead of at an incident. With a single index there is no second server to win a version race.

**What it costs:** a human decision for every new dependency. That is the point. Keep the list short, and keep review quick enough that people do not route around it.

## Fix 5: Do not install straight from a repository

```
git+https://github.com/unknown-user/tokenizer-fork.git          # a moving target nobody reviewed
```

If you need a fork, **copy it into your own repository, review it, and pin to the exact commit**:

```
tokenizer-fork @ git+https://github.com/acme/tokenizer-fork.git@3f9c2b7e...   # a full commit hash
```

## Putting it together

| Risk | Where it is stopped |
|---|---|
| A model file that runs code | A format with no steps, or a scan, in a throwaway environment |
| A look-alike or invented package name | An approved list |
| A new release that is malicious | An exact version and a hash |
| A second package server | One index |
| Unreviewed code from a repository | A copy you reviewed, pinned to a commit |
