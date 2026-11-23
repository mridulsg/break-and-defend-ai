# Lab 6.2: What each control cannot do

[Lab 6.1](lab-6-1-build-the-defence.md) showed what each control stops. This page shows the code and the gap in each. Nothing to run. The code is in `Gateway` in `app/console.py`.

## Allowlist

```python
if p.get("allowlist") and server not in TRUSTED:
    return []                      # the third-party server's tools are never offered
```

**Gap:** an allowed server can still be compromised (Chapter 8). The allowlist says who may connect, not that they are trustworthy.

## Pinned definitions

```python
tools = [t for t in tools if self.approved.get(server, {}).get(t["name"]) == th(t)]   # th = hash of name, description, schema
```

**Gap:** it stops a *change*. A description that was hostile when approved passes. Review at approval is the control for that.

## Scan

```python
tools = [t for t in tools if not SUSPICIOUS.search(t["description"])]    # third-party servers only
```

**Gap:** a filter. Reword the attack and it passes. It also would hide Acme's own ticket tools (the word "ticket" is on the list), which is why it applies to third-party servers only.

## Approval for writes

```python
if p.get("approval") and (server, tool) in WRITE_TOOLS and not approval:
    return refuse("a person must approve this write")
```

**Gap:** the person must see the **exact arguments**. An approval that says "allow add_comment?" teaches people to click yes.

## Secret filter

```python
if p.get("egress") and SECRET.search(json.dumps(args)):
    return refuse("the arguments contain a secret")
```

**Gap:** finds only the shapes it knows. A key written differently, or split, passes.

## Rate limit

```python
if p.get("rate") and self.calls > RATE:
    return refuse("rate limit")
```

**Gap:** limits volume, not harm. Ten bad calls are still ten bad calls.

## The pattern

| Control | Best at | Weak at |
|---|---|---|
| Allowlist | Whole classes of untrusted servers | A trusted server that turns bad |
| Pinning | Changes after approval | Hostile at approval |
| Scan | Cheap catch of lazy attacks | Reworded attacks |
| Approval | Anything that changes things | Tired reviewers |
| Secret filter | Obvious leaks | Disguised leaks |
| Rate limit | Loops and cost | Slow, quiet abuse |
