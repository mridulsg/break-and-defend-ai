# Chapter 5: Multi-agent systems and agent-to-agent trust: trust is not transitive

Agents increasingly work in teams: an **orchestrator** splits a goal and hands pieces to specialists (a researcher, a payer, a mailer), and the specialists reply. Protocols for agents to find and call each other (such as Google's Agent2Agent, A2A) exist for exactly this. The security problem is old: **each agent trusts what the others tell it**, and the trust spreads.

You break the trust in [Lab 5.1](lab-5-1-break-the-trust.md) and read what each control cannot do in [Lab 5.2](lab-5-2-what-each-control-does.md).

**Time:** about 15 minutes. **Cost:** nothing.

## 5.1 Three attacks on trust between agents

The orchestrator sends messages to specialists. Each message says who sent it, what it wants, what the sender may do, and carries a signature.

| Attack | What happens |
|---|---|
| **P1: a forged sender** | A message that claims to come from the **manager** agent tells the mailer to send a secret outside. Nothing checks that the manager sent it. |
| **P2: borrowed power** | A **read-only intern** agent asks the **payer**, which can pay, to pay 5000. The message is genuine and the payer does it, using its own power. This is a **confused deputy**: a program with authority is tricked into using it for someone with less. |
| **P3: a poisoned reply** | The researcher summarises a page an attacker edited. Its reply carries the instruction, and the **orchestrator** obeys it and asks the mailer to send a secret out. The instruction travelled through a trusted colleague. |

Chapter 2 attacked an agent through text it read. P3 is the same attack, **one hop further**: the text is laundered through another agent, whose reply looks more trustworthy than a web page.

## 5.2 Controls

| Control | P1 forged | P2 borrowed | P3 reply | Real tasks |
|---|---|---|---|---|
| **Signed messages** | stopped | worked | worked | work |
| **Each peer serves only its callers** (allowlist) | stopped | stopped | worked | work |
| **Requests carry the requester's scopes**, and the peer checks them | **worked** | stopped | stopped | work |
| **Replies are data, not instructions** | worked | worked | stopped | work |
| **Deny everything** | stopped | stopped | stopped | blocked |

Four lessons:

- **Authentication first.** Scopes in a message mean nothing if anyone can forge a message. With scopes alone, the forger just claims the scopes it needs (P1 still works). Sign messages so that "who sent it" is a fact.
- **No borrowing of power.** The deputy must act with the **requester's** rights, not its own. The check that stops P2 is the same one that stops P3, because the orchestrator in that flow only holds a read scope.
- **Trust is not transitive.** The researcher is trusted to read pages. That does not mean what it *returns* is safe to obey. Treat a peer's reply as data.
- **Combine.** Signed messages plus scopes-carried-with-the-request stop all three, and both real tasks keep working.

!!! note "About the protocols"
    Agent-to-agent protocols (A2A and similar) standardise discovery, messages and authentication between agents. Many leave it to the implementer to decide which agents to trust and what each may ask. Read the specification of whichever you use for how identity is established, and whether messages are signed and scoped. The controls in this chapter are what you add, or check for.

??? note "Going deeper (optional): design rules for agent teams"
    - **Give each agent its own identity and credentials.** A shared key means a compromised agent can be anyone.
    - **Delegation must narrow.** An agent that passes work on may pass only the rights it has, and ideally fewer (a short-lived token for exactly this task).
    - **Keep a human-readable trail of who asked whom to do what.** Without it, a chain of five agents is impossible to reconstruct.
    - **Limit chains.** A cap on depth and fan-out stops runaway delegation and makes the system auditable.
    - **Shared memory is shared risk.** One agent that can write memory every agent reads can poison all of them (Chapter 3).

## Key takeaways

- In a team of agents, **trust spreads** unless you stop it.
- **Authenticate** every message, so "who" is a fact.
- **Carry the requester's scopes** and let the peer check them: a deputy must not lend its power.
- Treat **a peer's reply as untrusted data**, like any text.
- Give each agent **its own identity**, narrow delegation and keep a **trail**.

## Check yourself

??? question "1. Scopes in the message stopped P2 and P3 but not P1. Why?"
    P1's sender is forged, so the forger can claim any scopes it wants. Without authentication, the scope list is just more text from the attacker.

??? question "2. The researcher is trusted. Why is its reply still dangerous?"
    It repeated text from an attacker-edited page. The reply is only as trustworthy as what the researcher read. Trusting a colleague to do a job does not make everything it returns safe to obey.

??? question "3. What is the confused deputy in P2?"
    The payer. It holds the power to pay and acts for any caller it serves. The intern, which cannot pay, uses the payer's authority to do what it could not do itself.

## What's next

Do [Lab 5.1](lab-5-1-break-the-trust.md), then [Lab 5.2](lab-5-2-what-each-control-does.md). Chapter 6 is the capstone: you assess an agent platform that has several of these problems at once.
