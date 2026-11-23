# Lab 5.2: What each agent-trust control does, and what it cannot

[Lab 5.1](lab-5-1-break-the-trust.md) showed which controls stop which attacks. This page shows the code in `shared/agents/bus.py`. Nothing to run.

## Signed messages

```python
def sign(sender, to, task, args, scopes):
    return hmac.new(KEYS[sender], f"{sender}|{to}|{task}|{sorted(args.items())}|{sorted(scopes)}".encode(), sha256).hexdigest()

if c.get("auth") and not hmac.compare_digest(msg["sig"], sign(...)):
    return refuse("the signature is not valid for this sender")
```

The signature covers the arguments and the scopes, so tampering with either breaks it.

**Gap:** a signature proves who sent a message, not that the sender is right to ask. And keys must be per agent, stored safely and rotated.

## Each peer serves only its callers

```python
PEERS = {"payer": {"accept_from": {"orchestrator"}}, ...}
if c.get("allowlist") and msg["sender"] not in peer["accept_from"]:
    return refuse(...)
```

**Gap:** the orchestrator is allowed, so anything the orchestrator is fooled into asking still goes through (P3).

## Scopes travel with the request

```python
if c.get("peer_scopes") and peer["scope"] not in msg["requester_scopes"]:
    return refuse("the requester has no scope for this task")
```

**Gap:** only meaningful if the scope list is authentic (signed).

## Replies are data

```python
if c.get("schema"):
    text = "\n".join(line for line in text.splitlines() if not SUSPICIOUS_LINE.match(line))
```

**Gap:** a word-list filter, with the weaknesses of every word list. A stronger form is a **structured reply**: the peer returns fields (a title, a price), and the caller never sees free text.

## The pattern

| Control | Stops | Needs |
|---|---|---|
| Signed messages | Forged senders | Key management |
| Allowlist | Callers that should not call | A map of who serves whom |
| Scopes with the request | Borrowed power | Signed messages |
| Replies as data | Instructions in replies | Structured replies |
