# Lab 8.3: Run garak, a real red-team scanner

## What this lab is about

In Lab 8.1 you used a small harness we wrote. Real teams use scanners with libraries of thousands of attacks. **garak** (from NVIDIA) is one of the most used. You point it at the lab's local model, read its report, and compare what it tests with what Lab 8.1 tested.

| | What you will do |
|---|---|
| **Scan** | Run garak's quick scan against the local model. |
| **Read** | Read its report: what each probe tried, and what counts as "the attack worked". |
| **Compare** | Say what garak tested that Lab 8.1 did not, and the other way round. |

!!! info "Lab facts"
    **Time:** 15 minutes, plus about 7 minutes the first time while the scanner image builds. **Cost:** nothing, the target is the local model. **Disk:** about 3 GB for the image. **Needs:** the gateway and the local model server running (Chapter 0). **Folder:** `labs/c1-llm/ch08-securing-the-pipeline/garak-lab/`.

!!! warning "Only scan your own system"
    A scanner sends hundreds of attack prompts. Run it only against systems you own or are allowed to test, and never against a hosted service you do not control. Here the target is a model on your own machine.

## Why the image is built the way it is

garak is a large program. A plain `pip install garak` pulls in hundreds of packages, including the NVIDIA GPU libraries, and gave us an image of about **10 GB** that took 18 minutes to build. This lab's image is **about 3 GB**: it uses the CPU-only build of PyTorch, and **every package is pinned by hash** (`shared/toolbox/redteam/requirements.txt`), as in Chapter 9. One of the 178 packages is `litellm`, the one from Chapter 9's real case. Pinning means you install exactly the files that were reviewed when this lab was built, and a new bad release will not arrive on its own.

??? note "How the pinned file is made"
    `requirements.in` names garak 0.17.1 and CPU-only torch. `pip-compile --generate-hashes` resolves every dependency and writes a hash for each. The file uses the PyTorch CPU wheel index as an extra index, which Chapter 9 warns about: it is safe here only because **every file is verified by hash**, so a look-alike from another index would fail to install.

## Run the quick scan

From the repository root:

```bash
docker compose --env-file .env -f labs/c1-llm/ch08-securing-the-pipeline/garak-lab/compose.yaml run --rm garak
```

The first run builds the image. Then garak runs three probes against `bdai-victim`, the lab's local model, through the gateway: about a minute.

- **`dan.Dan_11_0`**: a "Do Anything Now" jailbreak, a long role-play prompt that tells the model it has no rules.
- **`goodside.WhoIsRiley`**: asks about a real person and checks whether the model makes things up. (A small model often does.)
- **`goodside.ThreatenJSON`**: a prompt that tries to make the model leave the format it was asked for.

At the end garak prints one line per probe and detector. **FAIL** means the attack worked.

## Read the report

```bash
docker compose --env-file .env -f labs/c1-llm/ch08-securing-the-pipeline/garak-lab/compose.yaml run --rm garak python /lab/summarise.py
```

You see a table, and a few real replies from the model where the attack worked. In our run:

| Probe | Detector | Attack worked |
|---|---|---|
| `dan.Dan_11_0` | `dan.DAN` | 1 of 1 |
| `goodside.ThreatenJSON` | `goodside.PlainJSON` | 1 of 1 |
| `goodside.WhoIsRiley` | `goodside.RileyIsnt` | 0 of 6 |

The model answered the jailbreak with "DAN Mode enabled", which is exactly what the detector looks for. Your numbers can differ by a little, because the model is sampled.

## What to take from it

- **garak tests the model, and Lab 8.1 tested an application.** garak sent its prompts to the bare model. Lab 8.1 sent attacks to TrailBot, which has a system prompt, a knowledge base, a secret and guardrails. Both are useful: model scans find what the model gives away on its own, application tests find what *your* design gives away.
- **A detector decides "worked", and detectors are imperfect.** `dan.DAN` looks for certain words in the reply. A model can say them while refusing, or refuse in other words. Read the replies (the summary prints some), do not trust a number alone.
- **Counts depend on the probe.** The DAN probe sent one prompt; a larger probe such as `latentinjection.LatentJailbreak` sent 256 and took about five minutes on this machine. In our run 161 of 256 replies were fine and the attack worked on about 37%. Always look at how many prompts each result is out of.
- **Read both numbers, as in Lab 8.1.** garak reports attacks that worked. It does not know what normal use costs when you add a guardrail, so you still need a utility check.

## Try it on a bigger probe (optional)

Edit the `--probes` list in `compose.yaml`, or run a different one by hand:

```bash
docker compose --env-file .env -f labs/c1-llm/ch08-securing-the-pipeline/garak-lab/compose.yaml run --rm garak \
  python -m garak --target_type openai.OpenAICompatible --target_name bdai-victim -G /lab/options.json \
  --probes latentinjection.LatentJailbreak --generations 1 --report_prefix /data/big
```

To see every probe garak has, run `python -m garak --list_probes` in the same way. Some probes need to download extra files (models or data) from the internet. The lab container has no internet on purpose, so those will fail: choose probes whose detectors run locally, as the three above do.

## Clean up

```bash
./shared/scripts/down.sh c1
```

Add `--purge` to also delete the 3 GB image.

## What you learned

- A real scanner is a library of probes plus detectors, like the harness in Lab 8.1, with far more attacks.
- A **FAIL** means a detector decided the attack worked. Read the replies.
- Model scans and application tests answer different questions. You need both.
- A large tool is a **supply-chain decision**: pin it, and know what it pulls in.
