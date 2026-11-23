# Break & Defend AI

A free, written-only course with hands-on Docker labs on securing AI systems. Three courses, each with its own chapters and labs:

| Course | Topic | Chapters and labs |
|---|---|---|
| 1. AI/LLM Security | Prompt injection, agency, data and model attacks, images, cost, red teaming and guardrails, the AI supply chain, threat modeling, a capstone | 12 chapters (0 to 11) |
| 2. MCP Security | Tool poisoning, server flaws, authentication, a gateway, a build pipeline, shadow servers, a capstone | 9 chapters |
| 3. Agentic AI Security | Goal hijacking, memory poisoning, permissions and autonomy, agent-to-agent trust, a capstone | 6 chapters |

Every lab follows the same rhythm: understand the concept, **break** a deliberately vulnerable target, then **defend** it and prove the fix with a flag.

You run everything on your own machine and you pay for your own model tokens. Each lab states its estimated cost up front, and most cost nothing because they use a small local model.

> The labs contain deliberately vulnerable software. Read [SAFETY.md](SAFETY.md) before you start.

## Setting this up with an AI assistant? Read this first

**If you are using an AI assistant (Claude, ChatGPT, Gemini, Copilot or similar) to set this up, tell it:**

> Follow the instructions in `llm_setup.txt` in this repository to set up the course on my machine.

[`llm_setup.txt`](llm_setup.txt) is written for the assistant: it lists what to check, the exact commands in order, how to verify each step, what to ask you for (your OpenRouter key) and what never to do. You can also follow the quick start below yourself.

## What you need

- **Linux**, or **Windows with WSL2 running Ubuntu 24.04**, with Docker Engine and the Compose plugin (`docker compose version` must work). macOS with Docker Desktop is untested; see `llm_setup.txt`.
- **8 GB of RAM** or more (the small local model needs about 2 GB while it answers) and **2 or more CPU cores**.
- **About 30 GB of free disk.** The local model server image is large (about 9 GB), the models are 1.7 GB, and each course adds a few hundred MB to a few GB.
- **Internet access** for the first setup (images and models are downloaded once).
- An [OpenRouter](https://openrouter.ai) API key. Create a key just for these labs and **set a credit limit on it**. The key is only used for the hosted-model parts of some labs; most labs run on the local model.
- On WSL: keep a terminal open while you work. WSL stops the Ubuntu instance (and Docker with it) about 15 seconds after the last terminal closes. Everything restarts by itself next time, and your spend history is kept, but a lab in progress is interrupted.
- Comfort with Python, Docker and the command line. The course teaches AI security only, not Python or Docker.

## Quick start

All commands run from the repository root, inside Linux or WSL.

```bash
# 1. Create .env and add your key (stays on your machine, ignored by git)
cp .env.example .env            # then put your key after OPENROUTER_API_KEY=
./shared/scripts/setup.sh       # generates a local gateway key, checks your key is set

# 2. Check the machine is ready
./shared/scripts/preflight.sh

# 3. Start the shared core: the model gateway (holds your key, enforces the spend cap) and the local model server.
#    The first run downloads a large image and the models (about 1.7 GB): allow several minutes.
./shared/scripts/start.sh

# 4. Read the course: a small docs site served from this repository
docker compose -f shared/docs-site/compose.yaml up -d --build      # then open http://127.0.0.1:8000

# 5. Run the first lab (a smoke test of the whole setup)
docker compose --env-file .env -f labs/c1-llm/ch00-orientation/smoke-test/compose.yaml up --build --abort-on-container-exit --exit-code-from toolbox
```

Start with Chapter 0 in the docs site. Each lab page begins with the one command that starts it. Most labs open a web console at <http://127.0.0.1:8300>; run **one lab at a time** and shut it down with `./shared/scripts/down.sh c1` (or `c2`, `c3`) before the next.

Check what you have spent at any time with `./shared/scripts/usage.sh`.

## Housekeeping: moving between courses

Most disk space is Docker images, so finishing a course means purging it.

| Level | Command | Effect |
|---|---|---|
| Stop | `docker compose -f <lab compose file> stop` | Pause; nothing removed |
| Reset | `./shared/scripts/down.sh c1` | Remove course 1 containers, networks and volumes; keep images |
| Purge | `./shared/scripts/down.sh c1 --purge` | Reset, plus delete course 1 images (frees most disk) |
| Remove gateway | `./shared/scripts/down.sh core` | Stop the shared gateway and local model server (`--purge` also wipes spend history and the downloaded models) |

Only resources labelled for that course are touched. Your other Docker work is safe.

## If something does not work

- Run `./shared/scripts/preflight.sh`: it checks Docker, disk, memory, your `.env` and the gateway, and tells you what is missing.
- A lab says it cannot reach the gateway (`ConnectTimeout`, "network bdai-llm declared as external"): run `./shared/scripts/start.sh`. If the gateway is running but lab containers still cannot reach it, restart the Docker daemon (on WSL Ubuntu: `sudo systemctl restart docker`), then `start.sh` again.
- More in the troubleshooting table of `llm_setup.txt` and in each lab's `README.md`.

## Repository layout

```
docs/                 the course text (Course 1: docs/c1, Course 2: docs/c2, Course 3: docs/c3)
labs/<course>/<chapter>/<lab>/   one folder per lab: compose.yaml, README.md, lab files
shared/core/          the model gateway (spend cap, metering, key isolation) and the local model server
shared/console/       the web console the labs share
shared/mcp/           the small MCP implementation and lab backend used by Course 2
shared/agents/        the agent platform used by Course 3
shared/toolbox/       per-course container images
shared/scripts/       start, setup, preflight, usage, console and cleanup scripts
tests/                unit tests and the live integration tests
llm_setup.txt         setup instructions for an AI assistant
```

## Licences

- Course text: [CC BY-SA 4.0](LICENSE-CONTENT.md)
- Code and lab files: [MIT](LICENSE)
