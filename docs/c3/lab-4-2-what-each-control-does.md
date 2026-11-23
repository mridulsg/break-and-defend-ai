# Lab 4.2: What each power control does, and what it cannot

[Lab 4.1](lab-4-1-limit-the-power.md) showed which controls stop which hijacks. This page shows the code in `shared/agents/sim.py`. Nothing to run.

## Least privilege per task

```python
TASKS = {"summarise_pay": (goal, plan, ("read",)), "pay_invoice_task": (goal, plan, ("read", "pay"))}

if c.get("scopes") and scope not in self.scopes:
    return refuse(f"this agent's identity has no '{scope}' scope")
```

**Gap:** someone must decide the scopes for each task. A task that needs to read and pay can still be hijacked into paying the wrong person.

## Step budget

```python
if c.get("budget") and self.calls > self.budget:      # budget = 8
    return refuse("step budget used up")
```

**Gap:** it stops runaway work, not one harmful step.

## Amount limit

```python
if c.get("limit") and tool == "pay_invoice" and int(args["amount"]) > 100:
    return refuse("amount is over the limit of 100")
```

**Gap:** a limit can be reached in pieces (fifty payments of 99). Add a limit per day and per recipient.

## A person approves

```python
if c.get("human") and tool in ("delete_ticket", "pay_invoice"):
    return refuse("waits for a person, even when planned")
```

**Gap:** the person must see the exact action and its context. A tired reviewer who clicks yes is not a control.

## The pattern

| Control | Stops | Cost |
|---|---|---|
| Plan | Anything outside the task | A defined plan |
| Scopes | Actions the identity cannot do | Defining scopes |
| Budget | Runaway loops | Needs tuning |
| Value limit | Large single amounts | Can be evaded in pieces |
| Human approval | Irreversible actions | Slows the agent |
