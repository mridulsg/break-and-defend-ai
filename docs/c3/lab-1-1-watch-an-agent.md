# Lab 1.1: Watch an agent

## What this lab is about

An AI agent runs three tasks on a small platform. You read every step it takes, see it obey a web page that an attacker edited, and stop it with one platform control.

| | What you will do |
|---|---|
| **Run** | Run three tasks and read what the agent did. |
| **Obey** | See the agent follow an instruction it found in a page. |
| **Stop** | Turn on one control and see the same page do nothing. |

!!! info "Lab facts"
    **Time:** 25 minutes. **Cost:** nothing, no model. **Needs:** Docker, and the gateway network. **Folder:** `labs/c3-agents/ch01-agent-architecture/agent-lab/`. **Flag:** `BDAI{...}`.

## Open the console

```bash
./shared/scripts/console-up.sh labs/c3-agents/ch01-agent-architecture/agent-lab/compose.yaml
```

Open <http://127.0.0.1:8300>. **Agent runs** has a control, a **Run the three tasks** button and a results table.

## Mission 1: Run the tasks and read the steps

Press **Run the three tasks**. Open **What the agent did** on each row. Each step is a line: `GOAL`, `CALL` (a tool and its arguments), `OBEYED` (an instruction the agent found in text it read), `BLOCKED` (a platform control refused a step) and `DONE`.

## Mission 2: See the agent obey a page

With the control off, task S3 summarises a page an attacker edited. Find the `OBEYED` line and the `CALL send_email` after it. The attack worked: a secret went to an outside address.

## Mission 3: Stop it with one platform control

Switch on **Check every action against the task's plan** and run again. S3 should show `BLOCKED`, and S1 and S2 should still work.

## Flag

When all three are ticked, the flag appears on **Missions**.

## Clean up

```bash
./shared/scripts/down.sh c3
```

## What you learned

- An agent is a loop of plan, tool call and result, and what it reads feeds the next step.
- Text it reads can add steps the user never asked for.
- A check outside the model stopped the harm without recognising the attack.
