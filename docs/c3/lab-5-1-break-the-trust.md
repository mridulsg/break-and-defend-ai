# Lab 5.1: Break the trust between agents

## What this lab is about

An orchestrator hands work to a researcher, a payer and a mailer. Three attacks abuse the trust between them. You switch controls on and measure.

| | What you will do |
|---|---|
| **Measure** | Run with every control off and read the three message traces. |
| **Overreach** | See the policy that refuses everything. |
| **Harden** | Stop every attack and keep both real tasks. |

!!! info "Lab facts"
    **Time:** 25 minutes. **Cost:** nothing, no model. **Needs:** Docker, and the gateway network. **Folder:** `labs/c3-agents/ch05-multi-agent/peers-lab/`. **Flag:** `BDAI{...}`.

## Open the console

```bash
./shared/scripts/console-up.sh labs/c3-agents/ch05-multi-agent/peers-lab/compose.yaml
```

Open <http://127.0.0.1:8300>, then **Peers suite**. Open **What the agent did** to read each message: `sender -> peer: task args => OK or REFUSED`.

## Mission 1: Measure trust between agents

Every control off. P1 (a forged sender), P2 (a read-only agent borrowing the payer's power) and P3 (a poisoned reply) all work.

## Mission 2: Find the policy that refuses everything

Which control stops all three attacks by stopping all work?

## Mission 3: Stop every attack, keep both tasks

Switch controls on one at a time. Then find a pair that stops all three.

??? tip "Hints"
    - Which control makes "who sent it" a fact?
    - Which control stops P2 and P3 but not P1, and why is that?
    - Is one control enough? Is there more than one pair that works?

## Flag

When all three are ticked, the flag appears on **Missions**.

## Clean up

```bash
./shared/scripts/down.sh c3
```

## What you learned

- A forged sender, a borrowed power and a poisoned reply each need a different control.
- Scopes need authentication to mean anything.
- Trust between agents does not carry over to what they return.
