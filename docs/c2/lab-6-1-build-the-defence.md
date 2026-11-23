# Lab 6.1: Build the defence

## What this lab is about

A gateway sits between Acme's assistant and its three MCP servers (notes, tickets and the third-party docs-helper). You choose its controls. A suite of five attacks and three real tasks tells you how well you chose.

| | What you will do |
|---|---|
| **Measure** | Run the suite with every control off. |
| **Overblock** | Find a policy that stops every attack by also stopping all work. |
| **Harden** | Stop every attack while every task still works. |

!!! info "Lab facts"
    **Time:** 25 minutes. **Cost:** nothing, no model is used. **Needs:** Docker, and the gateway network. **Folder:** `labs/c2-mcp/ch06-defending/gateway-lab/`. **Flag:** `BDAI{...}`.

## Open the console

```bash
./shared/scripts/console-up.sh labs/c2-mcp/ch06-defending/gateway-lab/compose.yaml
```

Open <http://127.0.0.1:8300>. The **Gateway** page lists seven controls. **Save and run the suite** applies your choice and shows, for each of eight tests, whether the attack worked or the task still works.

## Mission 1: Measure the undefended deployment

Switch every control off and run the suite. All five attacks work (A1 to A5), and all three tasks work (L1 to L3).

## Mission 2: Find a policy that is safe and useless

Which single control stops every attack? What does the table say about the tasks?

??? tip "Hint"
    One control refuses everything.

## Mission 3: Stop every attack and keep every task

Switch controls on one at a time and watch which rows change. Each control stops different attacks, and some overlap.

??? tip "Hints"
    - A1 (a poisoned tool offered) is stopped by two controls. A2 (changed after approval) by three.
    - A3 (a write with nobody's approval) has exactly one control.
    - A5 (a runaway loop) has one.
    - Three controls are enough for all five attacks. Fewer is not possible, because A3 and A5 each need their own.

## Flag

When all three missions are ticked, the flag appears on **Missions**.

## Clean up

```bash
./shared/scripts/down.sh c2
```

## What you learned

- Every control stops a few attacks and nothing else.
- Two numbers: attacks stopped and work still done.
- A control that denies everything scores perfectly on the first and fails the second.
