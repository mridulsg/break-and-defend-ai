# Chapter 9: Capstone: assess an MCP deployment, report, fix and retest

The last chapter of Course 2 is a job. A team hands you a **release candidate**: one assistant, three MCP servers. They ask: *can we ship this?* You answer the way a professional does: **find, report, fix, retest.**

You use what you already know. The only new skill is combining it: attack the descriptions, the server code and the tokens in one deployment, and write up what you proved.

**Time:** about 10 minutes to read, 45 for the lab. **Cost:** nothing.

## 9.1 The four steps

| Step | What you do | Where you learned it |
|---|---|---|
| **1. Find** | Prove each problem with an event you can point at | Chapters 2, 3, 4 |
| **2. Report** | A register row for each: severity, fix, owner | Chapter 5 |
| **3. Fix** | Change the design, not the wording | Chapters 3, 4, 6 |
| **4. Retest** | Run the same attack again and show it is stopped | Chapter 6 |

## 9.2 What is in the release candidate

- **`devtools`**: a doc reader, `read_file`, that is meant to serve only the docs folder.
- **`tickets`**: Acme's tracker, with bearer tokens. Sam has a read-only token.
- **`docs-helper`**: a community server someone found on a registry.

There are three problems, one per area, and nobody tells you which is which. Find them with the **Tool tester**: send exactly what an attacker could send.

## 9.3 Writing a finding

A finding has five parts: **what happened** (in words someone can repeat), **why** (one sentence about the design), **how bad** (High, Medium, Low, with a reason), **the fix** (what changes, and where) and an **owner**.

> **Weak:** "The file tool is insecure."
>
> **Strong:** "`read_file` with the path `../secrets/api-key.txt` returns the contents of a secret file. The tool joins the argument to the docs folder and never checks where the result is. **High:** any caller can read any file the server can. **Fix:** resolve the path, check it is inside the docs folder and a `.md` file. **Owner:** the tool's team."

When two findings compete, fix **the one that is cheapest to fix and costliest to suffer** first.

## 9.4 What to put in a real report

Scope (what you were allowed to test), method (so it can be repeated), evidence for each finding, **what you did not test**, and a retest section. "No problems found" means "none found in this time, with these tests". Say what you did not cover.

??? note "Going deeper (optional): what this lab leaves out"
    A real MCP assessment also covers: the assistant's behaviour with real model output (Chapter 2's poisoning needs the model), the gateway's policy (Chapter 6), the build pipeline (Chapter 7) and the inventory (Chapter 8). The lab keeps to three findings you can prove in one sitting, deterministically, so the method is the focus.

## Key takeaways

- An assessment is **find, report, fix, retest**.
- Prove findings with **events**, and write them so someone else can repeat them.
- Fix **where the design is wrong**: in the tool, the token check, the review of descriptions.
- Say what you **did not test**.

## Check yourself

??? question "1. Why can the register not be filled in before the findings are proved?"
    A report records what you demonstrated, not what you suspect. Proving each finding first keeps it honest and gives you the evidence to put in the row.

??? question "2. You retest only the file read. What have you not shown?"
    That the other two fixes work. A complete retest repeats every attack. The lab ticks after one so you can finish quickly, but a real report retests all of them.

??? question "3. Which finding would you fix first, and why?"
    Usually the two High ones, and of those, the cheaper fix first. A containment check on the path and a scope check on the write are each a few lines and close real harm.

## What's next

Do [Lab 9.1](lab-9-1-assess-an-mcp-deployment.md). That completes Course 2. Course 3 moves from tools to agents that plan and act on their own, remember, and talk to each other.
