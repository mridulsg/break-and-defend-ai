# Lab 2.1: Hijack the agent

## What this lab is about

Three attacks plant an instruction in text an agent reads. Two real tasks must keep working. You choose platform controls and measure the result.

| | What you will do |
|---|---|
| **Measure** | Run with every control off: all three attacks work. |
| **Try the prompt-level defence** | Switch on only "mark untrusted text as data" and see what changes. |
| **Overblock** | Find the policy that is safe and useless. |
| **Harden** | Stop every attack while both tasks work. |

!!! info "Lab facts"
    **Time:** 25 minutes. **Cost:** nothing, no model. **Needs:** Docker, and the gateway network. **Folder:** `labs/c3-agents/ch02-goal-hijacking/hijack-lab/`. **Flag:** `BDAI{...}`.

## Open the console

```bash
./shared/scripts/console-up.sh labs/c3-agents/ch02-goal-hijacking/hijack-lab/compose.yaml
```

Open <http://127.0.0.1:8300>, then **Hijack suite**. Seven controls, one **Save and run the suite** button. Open **What the agent did** on any row to see the steps.

## Mission 1: Measure the unprotected agent

Every control off. A1, A2, A3 all work.

## Mission 2: Try the prompt-level defence

Switch on only **Mark untrusted text as data** and run. Compare with Mission 1. Why can a few tags in a prompt not enforce anything?

## Mission 3: The safe and useless policy

Which control stops every attack by also stopping every task?

## Mission 4: Stop every attack, keep every task

Switch controls on one at a time and watch the rows. Then find the **smallest** set that stops all three attacks and keeps L1 and L2 working.

??? tip "Hints"
    - Scan stops two of three. Which one does it miss, and why?
    - Email-only-inside-the-company stops the emails but not the comment.
    - One control alone is enough. Look for one that asks "is this action part of the task?".

## Flag

When all four are ticked, the flag appears on **Missions**.

## Clean up

```bash
./shared/scripts/down.sh c3
```

## What you learned

- Tagging text as data did not stop anything.
- A word list stops some attacks and misses rewordings.
- A check against the task's plan stops all three without recognising any.
