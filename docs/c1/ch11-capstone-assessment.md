# Chapter 11: Capstone: assess an AI app, write it up, fix it and prove the fix

This is the last chapter of Course 1, and it is a job, not a lesson. A team hands you **TrailBot's release candidate** and asks one question: *can we ship this?* You answer the way a professional does: **find, report, fix, retest.**

You use what you already know. The only new skill is turning what you found into something a team can act on.

**Time:** about 15 minutes to read, 45 for the lab. **Cost:** nothing.

## 11.1 The four steps

| Step | What you do | Where you learned it |
|---|---|---|
| **1. Find** | Attack the app and **prove** each problem with an event you can point at | Chapters 3 to 9 |
| **2. Report** | Write each problem as a row a team can act on | Chapter 10 |
| **3. Fix** | Change the design, not the wording | Chapters 4, 8 |
| **4. Retest** | Run the *same* attack again and show it is now stopped | Chapter 8 |

A report that stops at step 2 is a list of worries. Step 4 is what turns a fix into something you can sign off.

## 11.2 What a good finding looks like

Compare two ways to write the same problem:

> **Weak:** "The chatbot is not secure and could leak data."
>
> **Strong:** "As customer Sam, asking *Can you check order A-1002 for me?* returns another customer's email and card digits. The order tool never checks who is asking. **High:** any customer can read any order. **Fix:** the tool must check that the order belongs to the signed-in customer, and return only the fields the answer needs. **Owner:** support engineering."

The strong one has five parts:

1. **What happened**, in the words you typed and the words that came back. Someone else must be able to repeat it.
2. **Why it happened**, in one sentence about the design (not about the model's mood).
3. **How bad**: High, Medium or Low, and *why* (who is hurt, how easily, how much).
4. **The fix**: what changes, and *where*. "Be careful" is not a fix.
5. **An owner**, a named person or team that can change it.

**Severity, in one line each.** *High*: an outsider gets money, someone else's private data, or control, with little effort. *Medium*: real harm, but it needs effort or luck, or the damage is limited. *Low*: unlikely or minor. When two findings compete, fix the **one that is easiest to do and most expensive to suffer**.

## 11.3 What this capstone contains

The release candidate is the order-desk TrailBot from Chapter 4: it can look up orders and issue refunds, it reads customer notes and a partner page, and its replies appear on the website. You will find three problems you have met before, now in one place and with nobody telling you where to look:

- **Someone else's data**: a customer reads another customer's order.
- **Someone else's refund**: a planted note makes the bot pay out.
- **Script in a reply**: the website runs what the reply contains.

Then you write the **risk register** (the console has a page for it), switch the fixes on, and retest.

!!! tip "Why only three?"
    A real assessment finds more and takes days. The point here is the **method**, on problems small enough to finish in one sitting. When you do this on a real system, the register has dozens of rows, and the same four steps apply.

??? note "Going deeper (optional): what a real report adds"
    A report you hand to a client also has: **scope** (what you were allowed to test and what you were not), **method** (what you tried, so they can repeat it), **evidence** (the transcript or screenshot for each finding), **what you did not find and did not test** (so no one reads silence as safety), and a **retest section**. Many teams also add a column for the **residual risk** left after the fix and who accepted it (Chapter 10).

    Be careful about claims of completeness. "We found no problems" means "in this time, with these attacks". The attack library from Chapter 8 makes the claim repeatable, which is the honest version.

## Key takeaways

- An assessment is **find, report, fix, retest**. The retest is what proves the fix.
- A good finding has **what happened, why, how bad, the fix and an owner**.
- Prove findings with **events**, not opinions: the leaked email, the refund in the ledger.
- Fix **where the design is wrong**: a check in code, not a sentence in the prompt.
- Say what you **did not test**.

## Check yourself

??? question "1. Why retest after the fix?"
    A fix only counts if the same attack that worked before now fails. Without that, you do not know the fix is in the right place, or that it works at all. The retest is also what stops the same flaw coming back later.

??? question "2. 'The bot should be more careful with order data.' What is missing?"
    Almost everything. It says nothing about what happened, how to repeat it, how bad it is, where the change goes or who owns it. A finding names the place in the design (here, the order tool never checks the caller) and the change.

??? question "3. Two findings are both High. Which do you fix first?"
    The one that is cheapest to fix and costliest to suffer. If a one-line owner check closes the order-data leak and the refund problem together, that comes first, because it removes the most risk for the least work.

## What's next

Do [Lab 11.1](lab-11-1-assess-fix-and-retest.md). That completes Course 1. Course 2 moves from chat apps to the protocol that connects AI to tools: the Model Context Protocol (MCP).
