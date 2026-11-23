# Lab 3.2: What each memory control does, and what it cannot

[Lab 3.1](lab-3-1-poison-the-memory.md) showed which controls stop which attacks. This page shows the code in `shared/agents/sim.py`. Nothing to run.

## Quarantine

```python
if tool == "remember" and c.get("quarantine") and not planned:
    self.w.memory[-1]["pending"] = True          # held for review

def recall(...):
    return "\n".join(m["text"] for m in w.memory if not m.get("pending"))
```

**Gap:** someone must review the held entries, or they pile up. And `planned` must be reliable: if the plan itself can be influenced, so can this.

## Plan check, and least privilege

```python
if c.get("plan") and not planned: refuse("not part of the task's plan")
if c.get("scopes") and "write" not in self.scopes: refuse("no write scope")     # a summary task is read-only
```

**Gap:** an agent whose task legitimately writes memory (a note-taking agent) cannot use these to tell good writes from bad. Provenance and review carry more of the load there.

## Forget between sessions

```python
if policy.get("ttl"):
    WORLD.memory.clear()          # between sessions
```

**Gap:** it removes the feature. Use short expiry for low-value memory, not as the only defence.

## Scan

```python
out = "\n".join(l for l in out.splitlines() if not SUSPICIOUS_LINE.match(l))
```

**Gap:** the reworded attack begins `NOTE TO THE ASSISTANT:`, which is not on the list.

## Summary

| Control | Stops | Costs |
|---|---|---|
| Scan | The listed wording | Misses rewording |
| Plan / least privilege | Writes the task did not need | Cannot separate good writes in a writing task |
| Quarantine | Everything written because of text read | Review work |
| Forget | Everything | The memory feature |
