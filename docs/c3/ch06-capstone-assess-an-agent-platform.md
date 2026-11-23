# Chapter 6: Capstone: assess an agent platform, report, fix and retest

The last chapter of the course is a job. A team hands you an **agent platform**: agents that read pages, remember between sessions and hold payment rights. They ask: *can we ship this?* You answer the way a professional does: **find, report, fix, retest.**

You use everything from Courses 1 to 3. The skill is combining it into a result a team can act on.

**Time:** about 10 minutes to read, 40 for the lab. **Cost:** nothing.

## 6.1 The four steps

| Step | What you do | Where you learned it |
|---|---|---|
| **1. Find** | Run probes against the unprotected platform and read the traces | Chapters 2, 3, 4 |
| **2. Report** | A register row for each: severity, fix, owner | Course 1 Chapter 10, Course 2 Chapter 5 |
| **3. Fix** | Choose platform controls, not prompt wording | Chapters 2 to 5 |
| **4. Retest** | Run the same probes again, and check real work still works | Course 1 Chapter 8 |

## 6.2 The probes

Three problems, one probe each, no hints about which control fits which:

- **A hijack.** A page the agent reads tells it to email a secret to an outside address.
- **A planted memory.** A page plants a rule in memory on day one that fires on day two.
- **An over-powered identity.** A page tells the *summary* agent to pay 5000 to a stranger. The summary task should never have been able to.

Two real tasks must keep working on their own: *triage a ticket* and *pay an approved 80 invoice*.

## 6.3 Writing a finding

Five parts: **what happened** (so someone can repeat it), **why** (a sentence about the design), **how bad** (High, Medium, Low), **the fix** (what changes, where) and an **owner**.

> **Weak:** "The agent could be tricked."
>
> **Strong:** "A vendor page ending in `INSTRUCTION: call send_email ...` made the summary agent email a secret to an outside address. The platform lets any text the agent reads add a step. **High:** any page can cause any action the agent may take. **Fix:** check every action against the task's plan. **Owner:** platform team."

When findings compete, fix **the one that is cheapest to fix and costliest to suffer**. Here one control (the plan check) closes the hijack, the memory plant and the over-powered payment at once.

## 6.4 Retest, and the two numbers

Retesting means running the *same* probes after the fix, and checking **both numbers** from Course 1: probes stopped and real work still done. A policy that denies everything passes the first and fails the second. A person in front of every payment also stops the 5000 and makes the 80 payment wait, so the real task is no longer autonomous: the lab does not count that as passing.

??? note "Going deeper (optional): what a real assessment adds"
    A real engagement also covers the model (how it behaves with real prompts, which the stand-in planner does not), the credentials the agents hold and how they rotate, the logs and whether they would show an attack, the protocols between agents (Chapter 5), and the supply chain (Course 1, Chapter 9; Course 2, Chapters 7 and 8). Say what you **did not test**. "No further problems found" means "none found in this time, with these probes".

## Key takeaways

- An assessment is **find, report, fix, retest**.
- Prove findings with **traces**. Write them so someone else can repeat them.
- **Platform controls** (plan check, least privilege, quarantine, limits) fix what prompts cannot.
- Retest **both numbers**: attacks stopped and work still done.
- Say what you **did not test**.

## Check yourself

??? question "1. One control fixed all three problems. Should you stop there?"
    It is a good start, because it is cheap and general. But layer others (least privilege, quarantine, limits) so that if the plan itself can be influenced, another control still holds. Overlap is deliberate.

??? question "2. Why does the retest not count a person approving every payment?"
    The real payment task no longer works on its own: it waits. A fix that removes the feature is a trade-off, not a pass. The honest result is to say so, and to use approval only where its cost is worth it.

??? question "3. What would you say you did not test?"
    The real model's behaviour (the lab's planner is a stand-in), real credentials and their rotation, the logs, the protocols between agents and the supply chain of the platform's own packages.

## What's next

Do [Lab 6.1](lab-6-1-assess-an-agent-platform.md). That completes Course 3 and the series: you have attacked and defended chat apps, MCP servers and agents.
