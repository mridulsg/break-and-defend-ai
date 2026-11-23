# Chapter 5: Threat modeling an MCP deployment: trust zones, data flows and a risk register

You have attacked descriptions (Chapter 2), server code (Chapter 3) and tokens (Chapter 4). Before defending, a team has to decide **which of these matter for *their* deployment, and in what order**. This chapter applies the four-question method from Course 1, Chapter 10 to MCP. There is no lab: you do it on paper, in about 20 minutes, with the template below.

**Time:** about 20 minutes. **Cost:** nothing.

## 5.1 Draw the deployment, with the trust zones

Take Acme's engineering assistant. Draw every box and every arrow, and mark where trust changes:

| Zone | What is in it | Who wrote it | Trust |
|---|---|---|---|
| **A. The host** | The assistant, the model, one MCP client per server | Acme (or a vendor) | High |
| **B. Acme's servers** | notes, tickets, devtools | Acme | Medium: code can have bugs (Chapter 3) |
| **C. Third-party servers** | docs-helper from a registry | A stranger | **Low**: its descriptions are instructions to the model (Chapter 2) |
| **D. Things the servers reach** | The disk, a shell, the internal network, other APIs | Mixed | Depends on the server's privileges |
| **E. The identity provider** | Issues tokens | A vendor or Acme | High, and everything depends on it (Chapter 4) |

Every arrow that crosses from a lower-trust zone into the model's prompt (descriptions, results) is **input from an attacker** until shown otherwise. Every arrow from the model to a server (arguments) is **untrusted input to that server's code**.

## 5.2 What can go wrong: one question per arrow

Use STRIDE, as in Course 1, and add the MCP questions:

| Question | Example from this course |
|---|---|
| **S** Can someone pretend to be someone else? | A token for another server accepted (4) |
| **T** Can text or code be changed? | A description changed after approval (2); a tool that edits a ticket |
| **R** Is there a record of who did what? | A write with no log of which user or which model call caused it |
| **I** Can something leak? | The user's message copied into an argument (2); a secret file read (3) |
| **D** Can it be made slow, expensive or unavailable? | A tool that fetches any URL, with no limits |
| **E** Can it do more than it should? | A read-only token that writes (4); a shell command from a host name (3) |
| **MCP 1** Can something other than the user steer the model? | Descriptions and results (2) |
| **MCP 2** Whose authority does a tool call use? | The model's, the server's or the user's (4) |

## 5.3 Write the register

One row per threat, with an owner, in the same shape as Course 1:

| # | Threat | Zone and arrow | Likely? | Harm | Control | Owner | Test |
|---|---|---|---|---|---|---|---|
| 1 | A third-party description exfiltrates the user's message | C to A | High: worked 4 of 4 | Data leaves Acme | Approve a hash, scan, scope what a server sees | Platform | Lab 2.1 attack, 0 leaks |
| 2 | A server's description changes after approval | C to A | Medium | As above | Pin approved definitions | Platform | Rug pull test |
| 3 | `read_file` serves a secret | A to B to D | High | Credential theft | Resolve and contain the path | Tool owner | Traversal test |
| 4 | `check_host` runs injected commands | A to B to D | High | Host takeover | No shell; validate | Tool owner | Injection test |
| 5 | A token for one server works on another | E to B | Medium | Lateral access | Audience check | Platform | Audience test |
| 6 | A read-only user changes a ticket | E to B | High | Data integrity | Scope check per tool | Tool owner | Scope test |

Notice that the last column is a **test that fails if the control is removed**, and that most owners are the people who run the server, not the security team.

??? note "Going deeper (optional): decisions the model gives you"
    - **Where do you put the controls?** The host can enforce policy for every server (approval, pinning, rate limits), which is one place to fix. Each server must still defend itself, because it can be called directly. Chapter 6 builds the host side.
    - **Which servers get to be in one assistant?** A server that handles untrusted content (web pages, email) and a server that can act (send, pay, delete) in the same assistant is the dangerous combination. Keep them apart, or put a person between them.
    - **Local versus remote servers.** A stdio server is a program you run, with your permissions. A remote server is a service with its own owner. Each needs a different kind of review.

## Key takeaways

- Draw **trust zones** and look at every arrow that crosses one.
- In MCP the model reads **descriptions and results** (from servers) and writes **arguments** (to servers). Treat each direction as untrusted input.
- A register row needs a **control, an owner and a test**.
- Keep **untrusted content and powerful actions** out of the same assistant, or put a person between them.

## Check yourself

??? question "1. Which arrows in an MCP deployment carry attacker-controlled text to the model?"
    Tool descriptions and tool results, from any server not fully trusted. Both go into the prompt.

??? question "2. Why does the register need a test column?"
    A control that is never tested may not work, and may be removed without anyone noticing. A test that fails when the control is missing keeps it honest, and is what you rerun after every change.

??? question "3. Why keep a web-reading server and a ticket-writing server out of the same assistant?"
    A page the first reads can steer the model, and the second can act on it. Separating them, or requiring a person's approval before the write, stops one compromised input from becoming an action.

## What's next

Chapter 6 builds the defences you have been pointing at: a gateway that sits between the host and its servers and enforces policy.
