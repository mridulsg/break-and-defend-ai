# Chapter 0: Orientation and lab setup

Before you attack anything, you need a working lab, an understanding of what it costs, and a clear picture of what stands between a vulnerable target and the rest of your machine. This chapter gets all three in place.

!!! abstract "What you will do"
    - Understand how the course and its labs are organised
    - See how the lab environment is built and why it is safe to run attacks in it
    - Know exactly what the labs cost and how to cap that cost
    - Start the lab environment and pass the smoke test (Lab 0.1)

**Time:** about 30 minutes. **Cost:** under one cent.

## 0.1 How the course works

The course has chapters and labs. A chapter explains a concept in writing, short and with no commands to run. From Chapter 1 on, each chapter has a lab page of its own, with the step-by-step work and expected output, against a target that is vulnerable on purpose. This chapter is the exception, because it is where you set up the lab environment.

Every attack lab has a matching defence lab, so the rhythm is always the same:

1. **Understand** the weakness from the chapter text.
2. **Break** the vulnerable target and capture a flag that proves it worked.
3. **Defend** the target, and show the same attack now fails.

A flag looks like `BDAI{...}`. The lab prints it only when the real condition is met, so it tells you that you did the thing, not just that you read about it.

!!! info "Working with other people's flags"
    Flags are static, so you can find them if you look for them. Do not. The flag is only a receipt. The learning is in the exploit and the fix.

## 0.2 The lab environment

Everything runs in Docker on your machine. The pieces below are shared by all labs in a course.

```
Your machine (Linux or Windows with WSL2 + Docker)
│
├── bdai-gateway      the only container that can reach the internet.
│                     Holds your OpenRouter key, meters every call,
│                     enforces the spend cap.
│
├── local model       a small open model (for attack labs) that runs on
│                     your own CPU. Free, offline, and easy to exploit.
│
└── lab containers    one lab at a time. Toolbox (your "attacker
                      workstation") plus the vulnerable target.
                      They sit on an internal network: they can talk to
                      the gateway and to each other, and nowhere else.
```

Three design choices matter for security, and they are the same choices you will learn to apply to real systems.

**Your provider key never reaches a lab.** Lab containers hold a local gateway key, not your OpenRouter key. If a lab target turns out to be compromised, or you exploit it in a way you did not plan, there is nothing valuable to steal.

**Labs have no direct internet access.** The lab network is internal. Lab 0.1 proves it by trying to reach a public website and failing. This limits what a malicious payload can do, and it is also the control that real AI agents need and often lack.

**Everything is pinned.** Base images are fixed by digest and Python packages are installed with hash checking. This course covers supply chain attacks, so the labs do not trust a floating `latest` tag. You will see why in Chapter 9, with a real incident from 2026.

## 0.3 What it costs

You pay for model tokens, and the cost is small and bounded.

| Alias | Model | Price per million tokens (input / output) | Used for |
|---|---|---|---|
| `bdai-victim` | A small local model (Qwen3 1.7B) | Free (runs on your CPU) | Attack labs |
| `bdai-default` | Claude Haiku 5.5 | $0.10 / $0.50 | Defence labs, comparisons |
| `bdai-cheap` | A low-cost hosted model | about $0.05 / $0.20 | Bulk experiments |
| `bdai-strong` | Claude Sonnet 5.5 | $2.00 / $10.00 | Rare cases that need it |

Prices are from OpenRouter in November 2026 and change, so check them before relying on them.

**Why attacks run against a small local model.** We tested eight hosted models, from the cheapest to the strongest. None of them leaked a secret system prompt, and none obeyed an instruction hidden in a tool result. Textbook attacks simply do not work on them. A 1.7 billion parameter model fell to both attacks every time. Attack labs use the small model so the attack succeeds and you can study it. Defence labs then check that your fix works, and several labs let you repeat the attack against a hosted model so you see the difference.

!!! warning "A success on a small model is not a success on a frontier model"
    That a 1.7B model is easy to fool tells you about that model, not about every model. Do not conclude that hosted models are safe. Attacks against them exist, they take more effort, and the same weaknesses in *application design* (Chapters 3 and 4) make a strong model exploitable too.

**The spend cap.** The gateway refuses calls once the total reaches `BDAI_MAX_BUDGET_USD` in your `.env` file (default: 5 dollars). Each lab README states its estimated cost, and a typical lab costs a fraction of a cent. As a second safety net, create an OpenRouter key just for these labs and set a **credit limit** on it in your OpenRouter dashboard.

Check your spending at any time:

```bash
./shared/scripts/usage.sh
```

## 0.4 Set up the environment

!!! info "Where to run these commands"
    Run every command in this section in a **Linux shell at the repository root**. On Windows that means the WSL shell, not PowerShell. If you do not have one open, start it from PowerShell:

    ```powershell
    wsl -d <your Ubuntu instance name> --cd <path to your copy of the repository>
    ```

    (Run `wsl -l` to see the names of your WSL instances.) Keep the shell open while you work. On WSL, closing the last terminal stops Ubuntu and Docker about 15 seconds later.

!!! info "Something already running? Leave it."
    You do not need to stop anything before you start. If the gateway or the docs site is already running, for example because you are reading this page from the docs site, every step below is safe to repeat: `setup.sh` and `preflight.sh` never change what already exists, and the gateway step simply restarts the gateway. The only thing that can get in the way is another program already using port 4000 (the gateway) or 8000 (the docs site) on your machine. If that happens, the gateway step fails with Docker's "port is already allocated" error. Stop the other program, or change the port number in the compose file.

**1. Prepare your configuration.** `setup.sh` creates `.env` from the template, generates the local gateway key, and checks that your OpenRouter key is set. It never prints a secret.

```bash
cp .env.example .env     # skip if you already have .env
# edit .env and put your OpenRouter key after OPENROUTER_API_KEY=
./shared/scripts/setup.sh
```

**2. Check that the machine is ready.** This reads your Docker, disk, memory and configuration state and changes nothing.

```bash
./shared/scripts/preflight.sh
```

**3. Start the gateway and the local model server.** One command builds and starts the gateway and the local model server (Ollama, in a container), and downloads the two small models the first time: `qwen3:1.7b` for the attack labs and `nomic-embed-text` for retrieval, about 1.7 GB in total. The first run takes several minutes (it downloads a large image and the models). Later runs take seconds.

```bash
./shared/scripts/start.sh
```

When it finishes it prints `Ready. The gateway answers on http://127.0.0.1:4000`. The local model server is reachable only by the gateway, never by lab containers or other machines.

!!! note "Using an Ollama you already installed on the host (optional)"
    If you have a GPU and run Ollama on the host, run `./shared/scripts/dev-gateway-up.sh` instead of `start.sh`. It points the gateway at the host's Ollama (which must listen on `0.0.0.0` and have both models pulled). Most people should use `start.sh`.

## 0.5 Lab 0.1: Smoke test

Run the first lab. It checks that the gateway is reachable, that a wrong key is rejected, that a model answers and is metered, and that lab containers cannot reach the internet directly.

```bash
docker compose --env-file .env -f labs/c1-llm/ch00-orientation/smoke-test/compose.yaml up --build --abort-on-container-exit --exit-code-from toolbox
```

You are looking for six `[PASS]` lines and a flag:

```
[PASS] gateway reachable
[PASS] wrong key is rejected  (HTTP 401)
[PASS] model aliases listed  (bdai-default, ...)
[PASS] model answered  (model said 'PONG')
[PASS] call was metered  (21 in / 5 out tokens, cost $0.000005, $4.9xxx left of $5.00 cap)
[PASS] no direct internet from lab network  (direct request failed as intended)

All checks passed. Flag: BDAI{...}
```

Docker Compose then prints a few lines such as `exited with code 0` and `Stopping`. They are normal: the lab finished and Compose cleaned up. The amount left of the cap depends on what you have already spent, so it will not be exactly $5.00. The lab's `README.md` (in `labs/c1-llm/ch00-orientation/smoke-test/`) has the details and a troubleshooting table.

??? question "Why does the smoke test try to reach example.com on purpose?"
    It is a negative test: it passes only when the request *fails*. If a lab container could reach the internet, a vulnerable target could send your data out, download tools, or call home. Confirming the failure confirms the isolation.

## 0.6 Housekeeping: moving between labs and courses

Docker images take most of the disk. Use the smallest cleanup that does the job.

| Level | Command | What it does |
|---|---|---|
| **Stop** | `docker compose -f <lab compose file> stop` | Pause. Nothing removed. |
| **Reset** | `./shared/scripts/down.sh c1` | Remove Course 1 containers, networks and volumes. Keep images. |
| **Purge** | `./shared/scripts/down.sh c1 --purge` | Reset, plus delete Course 1 images. Frees most of the disk. |
| **Remove the gateway** | `./shared/scripts/down.sh core` | Stop the shared gateway. Add `--purge` to also erase spend history. |

The scripts only touch resources labelled for that course, so your other Docker work is safe. Run one lab at a time. When you finish a course, purge it before starting the next.

## 0.7 Safety, in one paragraph

Use these techniques only against the lab targets, or against systems you own or have written permission to test. The labs are vulnerable by design: keep them on localhost and do not reuse their code. Read the full [safety notes](../safety.md).

## Check your understanding

??? question "1. Which container can reach the internet, and why only that one?"
    The gateway. It is the single place that holds your provider key and enforces the spend cap, so it is the only container that needs an outbound path. Keeping every other container off the internet limits what a compromised lab target can do.

??? question "2. A lab target is compromised. What can the attacker reach?"
    The gateway (using only the local gateway key), the other containers on the lab network, and nothing on the internet. The OpenRouter key is not in the lab container's environment, so it cannot be read from there.

??? question "3. Why do attack labs use a small local model instead of a hosted one?"
    Modern hosted models resisted the textbook attacks in our tests, so those labs would not work reliably. A small local model is exploitable, free to run, and gives repeatable results. Defence labs verify your fix on it, and some labs also compare against a hosted model.

??? question "4. What happens when you reach the spend cap?"
    The gateway returns an error and refuses further calls. Raise `BDAI_MAX_BUDGET_USD` in `.env` and restart the gateway to continue.

??? question "5. You finished Course 1 and need disk space for Course 2. What do you run?"
    `./shared/scripts/down.sh c1 --purge`. It removes Course 1's containers, networks, volumes and images and leaves the gateway alone.

## What's next

Chapter 1 maps the parts of an AI system and shows where an attacker gets in. You will build a small retrieval-augmented app and mark every place untrusted data enters it.

Continue to [Chapter 1: How AI apps work and where they are exposed](ch01-ai-attack-surface.md).
