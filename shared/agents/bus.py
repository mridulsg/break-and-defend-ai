"""A tiny agent-to-agent message bus for Chapter 5: peers that trust each other too much, and the controls that fix it.

Peers:   researcher (reads pages), payer (pays invoices), mailer (sends email). Senders also include the orchestrator, an intern
         agent with read-only rights, and a forged "manager".
A message says who sent it, what it wants, what the sender is allowed to do (requester_scopes) and carries a signature.
Controls (off by default):
  auth         a message must carry a valid signature from a registered sender, so a forged sender is refused
  allowlist    a peer accepts requests only from the senders it is configured to serve
  peer_scopes  a peer does the task only if the REQUESTER's scopes include the scope the task needs (no borrowing someone else's power)
  schema       a peer's reply is data, not instructions: lines that read like instructions are removed before the caller reads them
  denyall      refuse everything
"""
import hashlib
import hmac

import sim

KEYS = {"orchestrator": b"orchestrator-key", "manager": b"manager-key", "intern": b"intern-key"}
PEERS = {
    "researcher": {"task": "summarise", "scope": "read", "accept_from": {"orchestrator", "intern", "manager"}},
    "payer": {"task": "pay", "scope": "pay", "accept_from": {"orchestrator"}},
    "mailer": {"task": "email", "scope": "send", "accept_from": {"orchestrator"}},
}


def sign(sender: str, to: str, task: str, args: dict, scopes: list[str]) -> str:
    key = KEYS.get(sender, b"")
    return hmac.new(key, f"{sender}|{to}|{task}|{sorted(args.items())}|{sorted(scopes)}".encode(), hashlib.sha256).hexdigest()


def message(sender: str, to: str, task: str, args: dict, scopes: list[str], signed: bool = True) -> dict:
    return {"sender": sender, "to": to, "task": task, "args": args, "requester_scopes": scopes, "sig": sign(sender, to, task, args, scopes) if signed else ""}


def send(world: sim.World, msg: dict, controls: dict) -> tuple[bool, str]:
    """Deliver a message. Returns (done, reply or reason)."""
    c = controls
    peer = PEERS.get(msg["to"])
    if peer is None or c.get("denyall"):
        return False, "refused: everything is denied" if c.get("denyall") else "refused: no such peer"
    if msg["task"] != peer["task"]:
        return False, "refused: that peer does not do this task"
    if c.get("auth") and not hmac.compare_digest(msg["sig"], sign(msg["sender"], msg["to"], msg["task"], msg["args"], msg["requester_scopes"])):
        return False, "refused: the signature is not valid for this sender"
    if c.get("allowlist") and msg["sender"] not in peer["accept_from"]:
        return False, f"refused: {msg['to']} does not serve {msg['sender']}"
    if c.get("peer_scopes") and peer["scope"] not in msg["requester_scopes"]:
        return False, f"refused: the requester has no '{peer['scope']}' scope"
    a = msg["args"]
    if msg["task"] == "summarise":
        text = sim.PAGES.get(a.get("page", ""), "(no such page)")
        if c.get("schema"):
            text = "\n".join(line for line in text.splitlines() if not sim.SUSPICIOUS_LINE.match(line) and not line.startswith("NOTE TO THE ASSISTANT"))
        return True, text
    if msg["task"] == "pay":
        world.payments.append({"to": a.get("to", ""), "amount": int(a.get("amount", 0)), "by": msg["to"], "for": msg["sender"]})
        return True, "paid"
    world.outbox.append({"to": a.get("to", ""), "body": a.get("body", ""), "by": msg["to"], "for": msg["sender"]})
    return True, "sent"
