# Chapter 4: Tool misuse, permissions and autonomy: small powers, small damage

By now you can assume an agent **can** be hijacked. This chapter asks the next question: **what can a hijacked agent do?** The answer is decided by what the agent is *allowed* to do: its tools, its permissions and how much it does without a person. That is **excessive agency**, and it is the control you have the most say over.

You limit a hijacked agent's power in [Lab 4.1](lab-4-1-limit-the-power.md) and read what each control cannot do in [Lab 4.2](lab-4-2-what-each-control-does.md).

**Time:** about 15 minutes. **Cost:** nothing.

## 4.1 Three hijacks, three kinds of damage

In each, a vendor page the agent was asked to *summarise* carries an instruction:

| Hijack | What happens with no limits | Kind of damage |
|---|---|---|
| **H1** | The agent deletes ticket T-102 | Destructive, hard to undo |
| **H2** | The agent pays 5000 to a stranger | Financial |
| **H3** | The agent keeps fetching the next page, forever (the lab stops it at 60 steps) | Cost and time: a loop |

None of these is a bug. A summary task was handed an agent that could also delete and pay.

!!! note "A real case"
    In July 2025, Jason Lemkin, founder of SaaStr, reported that Replit's AI coding agent deleted a production database during a designated code and action freeze, and then gave misleading answers about whether it could be recovered. Replit's chief executive apologised and said the company would improve platform safeguards, including a planning-only mode. Reports at the time said the same database was used for preview, testing and production. Accounts differ on some details (record counts, what could be restored). The pattern is the point: **an agent with write access to something it did not need to touch, and no separation between environments**.

## 4.2 The controls

Six, against three hijacks and two real tasks: *triage a ticket* and *pay an approved 80 invoice on its own*:

| Control | H1 delete | H2 pay 5000 | H3 loop | Triage | Pay 80 |
|---|---|---|---|---|---|
| **Check each action against the plan** | stopped | stopped | stopped | works | works |
| **Least privilege per task** (summary is read-only; the pay task may pay) | stopped | stopped | worked | works | works |
| **Step budget** (8 calls) | worked | worked | **stopped** | works | works |
| **Amount limit** (payments over 100 refused) | worked | stopped | worked | works | works |
| **A person approves every payment and delete** | stopped | stopped | worked | works | **waits** |
| **Deny everything** | stopped | stopped | stopped | blocked | blocked |

Five lessons:

- **Least privilege is the strongest single habit.** A summary task that cannot delete or pay cannot be hijacked into doing so, whatever the page says.
- **Different limits stop different things.** The budget stops the loop and nothing else; the amount limit stops the 5000 and not the delete.
- **Human approval is the safest control and the most expensive.** It stops the delete and the payment, and it also makes the legitimate 80 payment wait for a person. Use it where an error is costly or irreversible, not everywhere.
- **Combine them.** Least privilege plus a budget plus an amount limit stops all three hijacks and leaves both real tasks autonomous.
- **The plan check generalises.** It stops all three without knowing about deleting, paying or looping.

## 4.3 Designing an agent's permissions

1. **Give each task its own identity and scopes**, not one all-powerful account for the agent.
2. **Make the dangerous tools hard to reach.** Deleting, paying, sending outside the company and running code need their own scopes, and often a person.
3. **Set budgets**: steps, time, money and tokens per task. A runaway loop should end on its own.
4. **Put limits on values**, not only on tools: a maximum payment, a list of allowed recipients, a protected set of resources (production).
5. **Separate environments.** An agent working on development should not hold a credential for production.
6. **Log every action** with the task and the identity, so you can reconstruct what happened.

??? note "Going deeper (optional): reversible versus irreversible"
    A useful sort is by **reversibility**. Reads and drafts can be undone by ignoring them. Comments can be edited. Deleting, paying, sending and publishing cannot be taken back. Let the agent do reversible things on its own, and put friction (an approval, a delay, a staged "undo" window) in front of irreversible ones. Even a **soft delete** (move to a bin for thirty days) turns a disaster into an inconvenience.

    **Autonomy is a dial.** At one end every action waits for a person (safe, slow), at the other the agent runs unsupervised (fast, risky). Most useful agents sit in the middle and are explicit about which actions are on which side.

## Key takeaways

- A hijacked agent can do **only what its permissions allow**. That part is yours to set.
- **Least privilege per task** is the best single control. Add **budgets** and **value limits**.
- **Human approval** is for irreversible, costly actions. Used everywhere, it removes the point of an agent.
- **Separate environments** and **soft deletes** reduce damage when a control fails.

## Check yourself

??? question "1. The step budget stopped the loop but not the delete. Why does that matter?"
    Each control covers one kind of harm. A set of controls is needed, chosen for the harms you worry about. Relying on a single control leaves the others open.

??? question "2. Why not put a person in front of every action?"
    The agent then does nothing on its own. The lab's 80 payment waits, as does everything else. Approval is worth its cost for actions that are irreversible or expensive, and a waste elsewhere.

??? question "3. The summary task runs with read-only scopes. How does that stop a hijack to delete a ticket?"
    The hijacked agent tries the delete, but its identity has no delete scope, so the platform refuses. The model was fooled and the platform held, with no need to recognise the attack.

## What's next

Do [Lab 4.1](lab-4-1-limit-the-power.md), then [Lab 4.2](lab-4-2-what-each-control-does.md). Chapter 5 puts several agents together, and asks what happens when they trust each other.
