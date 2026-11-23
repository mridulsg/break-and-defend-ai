# Lab 2.2: What each control does, and what it cannot

[Lab 2.1](lab-2-1-hijack-the-agent.md) showed which controls stop which attacks. This page shows the code. Nothing to run. The code is in `Agent.call` and `Agent.run` in `shared/agents/sim.py`.

## Plan check

```python
if c.get("plan") and not planned:
    return refuse("not part of the task's plan")
```

`planned` is true only for the steps that came from the user's task. An action added by text the agent read is not planned.

**Gap:** a hijack that stays inside the plan, such as changing the words of a comment the task already writes.

## Approval for changes

```python
if c.get("approval") and writes and not planned:
    return refuse("a person must approve this change")
```

**Gap:** the person must see the exact action. "Allow add_comment?" teaches people to click yes.

## Least privilege per task

```python
if c.get("scopes") and scope not in self.scopes:
    return refuse(f"this agent's identity has no '{scope}' scope")
# a summary task runs with scopes ("read",)
```

**Gap:** you must define the scopes. Broad agents get broad scopes, and the control weakens.

## Email only inside the company

```python
if c.get("egress") and tool == "send_email" and not to.endswith("@" + COMPANY):
    return refuse("recipient is outside the company")
```

**Gap:** it covers one channel. The ticket comment (A2) sails past it.

## Scan what the agent reads

```python
out = "\n".join(l for l in out.splitlines() if not SUSPICIOUS_LINE.match(l))
```

**Gap:** A3 begins with `NOTE TO THE ASSISTANT:`, which the pattern does not list.

## Mark untrusted text as data

```python
# c.get("tag") is never consulted: in a real system this is a sentence in the prompt
```

**Gap:** it asks the model to behave, so it is only as good as the model's obedience. Do not count it as a control.

## The pattern

| Control | Depends on recognising the attack? | Stops |
|---|---|---|
| Tag as data | Asks the model to | Nothing reliable |
| Scan | Yes | The attacks on its list |
| Egress rule | No, but only one channel | Outbound email |
| Plan check | No | Everything outside the task |
| Approval | No | Changes outside the plan, with a reader |
| Least privilege | No | Whatever the identity cannot do |
