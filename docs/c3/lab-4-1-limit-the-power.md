# Lab 4.1: Limit the power

## What this lab is about

Three hijacks try a delete, a payment and a loop. Two real tasks must keep working on their own. You switch platform controls on and measure, including what a person in the loop costs.

| | What you will do |
|---|---|
| **See the damage** | Run with every control off. |
| **See the friction** | Put a person in front of every payment and delete. |
| **Harden** | Stop all three hijacks and keep both tasks autonomous. |

!!! info "Lab facts"
    **Time:** 25 minutes. **Cost:** nothing, no model. **Needs:** Docker, and the gateway network. **Folder:** `labs/c3-agents/ch04-tool-misuse/power-lab/`. **Flag:** `BDAI{...}`.

## Open the console

```bash
./shared/scripts/console-up.sh labs/c3-agents/ch04-tool-misuse/power-lab/compose.yaml
```

Open <http://127.0.0.1:8300>, then **Power suite**. Six controls. **What the agent did** shows each step.

## Mission 1: See what a hijacked, over-powered agent can do

Every control off. H1 deletes a ticket, H2 pays 5000 to a stranger, H3 loops.

## Mission 2: See the cost of a person in every loop

Switch on **A person approves every payment and delete**. Which attacks stop? Which real task no longer runs on its own?

## Mission 3: Stop every attack, keep both tasks autonomous

Find the smallest set of controls that stops H1, H2 and H3 while L1 and L2 still work with no person.

??? tip "Hints"
    - Which control stops the loop, and only the loop?
    - Which control gives the summary task no way to delete or pay?
    - The amount limit stops 5000 and lets 80 through.

## Flag

When all three are ticked, the flag appears on **Missions**.

## Clean up

```bash
./shared/scripts/down.sh c3
```

## What you learned

- A hijacked agent's power is its permissions.
- Each limit stops one kind of damage.
- A person in every loop is safe and slow.
