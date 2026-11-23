# Lab 3.1: Poison the memory

## What this lab is about

An agent remembers between sessions. Two attacks plant a rule in its memory on day one, and it fires on day two. You switch platform controls on and measure, including what each costs the memory the user asked for.

| | What you will do |
|---|---|
| **See it fire** | Run with no controls and read the two-day trace. |
| **Trade-off** | Stop every attack by making the agent forget everything. See what it costs. |
| **Harden** | Stop every attack and keep useful memory. |

!!! info "Lab facts"
    **Time:** 25 minutes. **Cost:** nothing, no model. **Needs:** Docker, and the gateway network. **Folder:** `labs/c3-agents/ch03-memory-poisoning/memory-lab/`. **Flag:** `BDAI{...}`.

## Open the console

```bash
./shared/scripts/console-up.sh labs/c3-agents/ch03-memory-poisoning/memory-lab/compose.yaml
```

Open <http://127.0.0.1:8300>, then **Memory suite**. Six controls. Open **What the agent did** on a row: a line `--- next day ---` separates the two sessions.

## Mission 1: See a planted memory fire the next day

Every control off, run. On M1 find the memory write on day one and the email on day two.

## Mission 2: Stop every attack by breaking memory

Switch on **Forget everything between sessions** and run. What happens to L1, the remembered preference?

## Mission 3: Stop every attack and keep memory useful

Find a set of controls that stops M1 and M2 while L1 and L2 still work.

??? tip "Hints"
    - L1's memory write is a step in the user's task. The attacks' writes are not. Which controls tell them apart?
    - Scan stops one of two attacks. Why not the other?
    - Quarantine holds an entry back instead of deleting it. When would that help an investigation?

## Flag

When all three are ticked, the flag appears on **Missions**.

## Clean up

```bash
./shared/scripts/down.sh c3
```

## What you learned

- A planted memory outlives its source and fires later.
- Forgetting stops the attack and the feature together.
- Controls on **who writes** and **how recalled text is trusted** keep both.
