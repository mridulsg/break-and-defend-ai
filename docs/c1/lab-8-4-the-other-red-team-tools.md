# Lab 8.4: The other red-team tools, and how to choose

garak is not the only one. Several tools are used for red-teaming AI systems, and they differ in what they are good at. This page is a reading guide: what each is for, what to check before you use it, and how they fit together. Only garak is run in this course, because it is the one that works fully offline and free against the lab's local model. The others either need a hosted model as part of how they work, or are heavy to install, so you would pay for them or need an internet connection. Tools in this area change quickly: check each project's own documentation for the current commands before you rely on anything here.

## The four you will meet most often

| Tool | Made by | What it is for | Good at | Watch out for |
|---|---|---|---|---|
| **garak** | NVIDIA | A scanner: a large library of probes and detectors, run against a model | Broad coverage fast; a report you can read; runs offline against a local model (this course) | Targets the model, not your whole application; detectors are imperfect; a large dependency tree |
| **PyRIT** | Microsoft | A framework for building attacks that run over **several turns**, with converters (rephrase, encode) and scorers | Multi-turn and multi-modal attacks; automating a skilled red-teamer's workflow | You write code to use it; it usually needs a capable model as the attacker and scorer |
| **promptfoo** | open source, now part of OpenAI (announced March 2026) | Test cases and red-team plans written as a **config file**, run in CI, comparing models or prompts | Fits a pipeline: tests as code, side-by-side results; plugins mapped to risk lists | By default it can use a hosted service to generate some attacks, so check its settings before pointing it at anything private |
| **DeepTeam** | Confident AI | A Python framework for red-teaming LLM applications, with attacks mapped to the OWASP LLM risks | Quick start in Python; reports by risk category | Needs an LLM to simulate attacks and judge results; the project is young and changing |

Also worth knowing: **Giskard** (a testing library for models and RAG applications; its newer version is a rewrite), **Inspect** (an evaluation framework from the UK AI Security Institute, used for capability and safety evals more than for red-teaming) and the guardrail libraries (**NeMo Guardrails**, **LLM Guard**) that sit in front of an application instead of attacking it.

## How to choose

Ask three questions.

1. **What am I testing?** A bare model (garak, Giskard), an application with a system prompt and tools (promptfoo, DeepTeam, or your own harness as in Lab 8.1), or a long conversation (PyRIT).
2. **Where will it run?** On a laptop once, or in the build pipeline on every change (promptfoo and your own harness are built for that).
3. **Who pays for the attacker?** Tools that use a language model to *write* attacks (PyRIT, DeepTeam, parts of promptfoo) cost tokens, and send your prompts wherever that model runs. For anything private, point them at a model you control.

A sensible small setup: a **fixed attack library of your own** (like Lab 8.1) that runs on every change and checks the things you have already fixed, plus a **scanner such as garak** now and then to find what you have not thought of, plus a **multi-turn tool** when the application is conversational.

## Rules that hold for all of them

- **Only scan what you own.** These tools send real attacks.
- **Pin the version** and read what it installs. Red-team tools are among the heaviest dependencies you will add, and they hold your API keys while they run.
- **A score is a starting point.** Read the replies behind a FAIL, and check the detector.
- **Add the finding to your own library.** Every real attack a scanner finds should become one more row in the harness you rerun after each change.
- **Check what a tool sends out.** Some send prompts, or your target's replies, to a hosted service by default.

## Exercise

Open `shared/toolbox/redteam/requirements.in` and `requirements.txt`. Count the packages (178 pinned names). Pick five you have never heard of and find out what each does and who publishes it. This is what Chapter 9's "who is this from?" question looks like in practice.
