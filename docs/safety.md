# Safety and authorized use

## Authorized use only

These labs teach you to attack AI systems so that you can defend them. Use the techniques **only** against the lab targets in this repository, or against systems you own or have explicit written permission to test. Attacking anyone else's system is illegal in most places and is not what this course is for.

## The labs are vulnerable by design

Lab targets contain intentional flaws. Do not expose them to a network you do not control, and do not reuse their code in production.

## How the labs protect your machine

- **Localhost only.** Published ports bind to `127.0.0.1`, so other machines cannot reach a lab.
- **No direct internet from lab containers.** Labs sit on an internal Docker network (`bdai-llm`) whose only exit is the model gateway. The smoke test in Chapter 0 proves this.
- **Your provider key stays in the gateway.** Lab containers hold only a local gateway key. A compromised or malicious lab target cannot read your OpenRouter key.
- **Hard spend cap.** The gateway refuses calls once the cap in `.env` (`BDAI_MAX_BUDGET_USD`, default 5) is reached, and clamps the output size of each request.
- **Least privilege containers.** Non-root users, read-only filesystems where possible, all Linux capabilities dropped, `no-new-privileges`, and memory and CPU limits.
- **Pinned and hashed dependencies.** Base images are pinned by digest and Python packages are installed with `--require-hashes`. This course covers supply chain attacks, so the labs practise what it teaches. A real example is the 2026 compromise of a popular LLM gateway package, which is why this project uses its own small gateway.
- **No real malware.** Where a lab needs a malicious package, model or skill, it uses a harmless simulated one built for the course.

## What the labs cannot protect you from

- **Docker itself.** Containers share your kernel. Do not run the labs on a machine holding data you cannot afford to lose. A dedicated WSL instance or VM is ideal.
- **Your own mistakes with credentials.** Never commit `.env`. Set a credit limit on the OpenRouter key.
- **Services you run outside the labs.** For example, a local model server that listens on every network interface has no authentication, so anyone who can reach it can use it.

## Reporting a problem

If you find a flaw in the lab infrastructure itself (not the intentional lab vulnerabilities), open an issue marked `security`. Do not post working exploits against the infrastructure publicly before it is fixed.
