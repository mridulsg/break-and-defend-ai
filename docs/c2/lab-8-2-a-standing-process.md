# Lab 8.2: Make it a standing process

A one-off scan is a snapshot. Nothing to run on this page: it shows how to keep the inventory true. The scanner is `app/inventory.py`.

## The core of the scan

```python
for name, spec in servers.items():
    flags = flags_for(spec)
    approved = registry.get(name)
    status = "shadow" if approved is None else "drift" if "unpinned" in flags else "approved"
```

```python
def flags_for(spec):
    # npx or uvx without an exact version: the code can change under you
    # a url that is http and not this machine: plaintext
    # a token, key, password or Authorization value written in the file: a secret in config
```

## The approval bar, as code

```python
BLOCKING_FLAGS = {"unpinned", "plaintext-http", "secret-in-config"}

def can_approve(item):
    bad = [f for f in item["flags"] if f in BLOCKING_FLAGS]
    return "it has " + ", ".join(bad) if bad else None
```

A server that fails the mechanical bar cannot be approved by clicking. A person still has to decide whether the server is worth owning.

## Run it every day

- **Where the configs are.** Each assistant has its own config file. Collect them with your device-management tool, or a small agent that sends only the list of servers (names, addresses, flags), never the tokens.
- **Run on a schedule** and alert on **new** shadow servers and on **drift**, not on the whole list.
- **Close the loop.** A shadow server gets a decision within a stated time (a week is common). The decision, owner and reason go into the registry.
- **Block, do not only report.** Where you can, make the assistant connect only to an internal registry (the allowlist from Chapter 6), so a new server cannot appear without an approval.

## What this does not cover

- **Servers started on demand** by a build or a script, which are in no config file.
- **Remote servers reached through a tool** the assistant already trusts.
- **A server approved at version 1.4.2 that is later replaced** on the registry. Pin by hash, not only by number.
- **The content of a server's descriptions and results**, which is what Chapters 2 and 6 are about.

## Ownership is the control

A server with an **owner** gets patched, reviewed and removed when nobody needs it. A server without one stays forever. If you remember one thing from this course, it is that the register is only as good as the names in the owner column.
