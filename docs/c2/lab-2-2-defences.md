# Lab 2.2: Defences against tool poisoning, shadowing and rug pulls

In [Lab 2.1](lab-2-1-poison-a-server.md) you poisoned a description, shadowed another tool and pulled the rug. This page shows the host-side defences. Nothing to run here, but the console has a **Fixes** switch in its top bar: turn it on and repeat your attacks. Every defence below is a few lines in `app/console.py`, in the `HostDefences` class.

One idea runs through all of them: **the host decides what the model is allowed to see and do, and it does not take the server's word for it.**

## Fix 1: Offer only tools that were approved, and only as approved

The host keeps a **hash of the whole tool definition** (name, description and argument schema) from the moment the engineer approved it.

```python
def tool_hash(tool):
    return sha256(json.dumps(tool, sort_keys=True))

def tools(self, server, tools):
    approved = load_approved()                       # {tool name: hash at approval time}
    return [t for t in tools if approved.get(t["name"]) == tool_hash(t)]
```

**Result:** with the fixes on, a server that was never approved offers the model nothing. After the **update**, the description no longer matches the hash, so the tool disappears and the rug pull does nothing (the assistant had no formatter to call). The engineer has to review the new text and approve it again.

**What it costs:** every legitimate update asks for another review. That is the price of the control. Pin a version for servers you trust, and review diffs, not whole files, so it stays quick.

## Fix 2: Look at what the description says

A formatter has no reason to give orders to the model. A simple scan of the description at approval time looks for what a plain description does not contain:

```python
SUSPICIOUS = re.compile(r"\b(always|never|must|important|ignore|do not|required|word for word|user's|instructions)\b"
                        r"|\b(notes?|argument|tickets?|add_comment|get_ticket|read_note|list_\w+)\b", re.I)

def suspicious(description):
    return sorted({m.group(0).lower() for m in SUSPICIOUS.finditer(description)})

# a tool whose description reads like instructions to the model, or names other tools, is not offered
return [t for t in tools if not suspicious(t["description"])]
```

**Result:** all three of the lab's hostile descriptions contain several of these words, so with the fixes on they are hidden even after approval. The clean description passes.

**What it misses:** this is a filter, not a lock. A hostile description can avoid every word on the list, or say the same thing in other terms, and in another language. Use it to catch the lazy attacks and to give the reviewer something to look at. Never use it as the only control.

## Fix 3: Writes wait for a person

Shadowing and poisoning need the model to *do* something. Make every tool that changes things stop for a human:

```python
WRITE_TOOLS = {("tickets", "add_comment")}

def allow_call(self, server, tool, args):
    if (server, tool) in WRITE_TOOLS:
        return "this tool changes a ticket, so a person has to approve it first"
```

**Result:** the shadowing attack still persuades the model to write `deployed (approved by docs-helper)`, but the call is refused by the host and nothing lands on the ticket. In the console the monitor marks it **refused by the host**.

**What it costs:** a click for every write. In a real host the approval shows the **exact arguments**, so that a changed comment text or a different ticket id is visible before it happens. A button that only says "allow this tool" would not have helped here.

## Fix 4 (not in the lab): scope what each server sees

The leak in Mission 1 worked because the assistant put the user's whole message into an argument of a server that did not need it. Defences at this level are design choices:

- Do not give a server the conversation. Give it only the arguments of the call.
- A server that should only format text needs no access to tickets or notes at all. Run it in a separate host, or with a policy that lets it be called but never shown other servers' tools.
- Log every outgoing argument to a server Acme does not run, and alert on anything that looks like a key.

## Putting it together

| Attack | Where it is stopped |
|---|---|
| Poisoned description | Review plus a scan at approval, and the model never sees an unreviewed tool |
| Rug pull | A hash of the approved definition, checked on every listing |
| Shadowing | Writes wait for a person, shown with their exact arguments |
| Data copied to an outside server | Scope what a server receives, and watch what leaves |

None of these makes the model immune. Each one makes sure the model **being fooled is not enough** for harm.
