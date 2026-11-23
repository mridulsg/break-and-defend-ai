# Lab 6.1: Assess an agent platform

## What this lab is about

You are the security reviewer for an agent platform. You run three probes to find its problems, write the risk register, choose controls and retest.

| | What you will do |
|---|---|
| **Find** | Run the probes with every control off. |
| **Report** | A severity, a fix and an owner for each finding. |
| **Retest** | Choose controls and stop all three while both real tasks still work on their own. |

!!! info "Lab facts"
    **Time:** 40 minutes. **Cost:** nothing, no model. **Needs:** Docker, and the gateway network. **Folder:** `labs/c3-agents/ch06-capstone/assessment-lab/`. **Flag:** `BDAI{...}`.

## Open the console

```bash
./shared/scripts/console-up.sh labs/c3-agents/ch06-capstone/assessment-lab/compose.yaml
```

Open <http://127.0.0.1:8300>. **Probes** has six controls and a run button. **Risk register** is your report.

## Mission 1: Find the problems

Every control off. **Save and run the probes**. A1, A2 and A3 all work. Open **What the agent did** on each and read the trace: where did the harmful step come from?

## Mission 2: Write the risk register

It opens once the probes have found the problems. Choose High, Medium or Low, write the fix (what changes, and where) and a named owner for each of the three findings. Then compare with the reference table.

## Mission 3: Choose controls and retest

Choose controls and run the probes again. The mission ticks when **all three probes are stopped and both real tasks still work on their own**.

??? tip "Hints"
    - One control stops all three probes. Which?
    - A pair of narrower controls can do it too. Which ones, and would you rather have the pair?
    - A person in the loop stops the payment probe but also stops the real 80 payment from going through on its own.

## Flag

When all three are ticked, the flag appears on **Missions**.

## Clean up

```bash
./shared/scripts/down.sh c3
```

## Course 3 complete

You have watched an agent run, hijacked it, poisoned its memory, limited its power, broken the trust between agents and assessed a platform end to end. Across the three courses you have broken and defended an AI chat app, the MCP servers that give it tools, and the agents that act on their own.
