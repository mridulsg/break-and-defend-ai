# Break & Defend AI

Free, written-only courses with hands-on Docker labs on securing AI systems. You learn each attack by carrying it out against a deliberately vulnerable target, then you defend that target and prove the fix worked.

There are three courses. Each has its own labs, and each builds on the one before.

| Course | You will learn to | Status |
|---|---|---|
| **1. AI/LLM Security** | Attack and defend LLM applications, RAG systems, training data and the AI supply chain | Complete |
| **2. MCP Security** | Attack and defend Model Context Protocol servers and the tools agents call | Complete |
| **3. Agentic AI Security** | Attack and defend autonomous agents, their memory and tools, and agent-to-agent protocols | Complete |

## How the course works

- **Written, not video.** Each chapter explains a concept, then sends you to a lab.
- **Break, then defend.** Every attack lab has a matching defence lab. A flag confirms each result.
- **You run it all yourself.** Labs run in Docker on your own machine. Nothing is hosted for you.
- **You pay for your own tokens.** Each lab states its estimated model cost at the top. A spend cap in the gateway stops runaway costs.
- **Small local models where it helps.** Modern hosted models resist textbook attacks, so attack labs use a small local model as the target. That also makes them free to run.

## What you need

- Linux, or Windows with WSL2 running Ubuntu 24.04, with Docker Engine and the Compose plugin
- About 30 GB of free disk space, and 8 GB or more of RAM
- An OpenRouter API key with a credit limit set on it
- Comfort with Python, Docker and the command line. The course teaches AI security only. It does not teach Python or Docker, and when a lab uses a script, it tells you what the script does.

## Ground rules

Use these techniques only on the lab targets, or on systems you own or have written permission to test. Read the [safety notes](safety.md) before you start.

## Start here

Begin with [Chapter 0: Orientation](c1/ch00-orientation.md).
