# Chapter 7: Unbounded consumption, misinformation and over-reliance

Chapters 3 to 6 attacked what an AI is told, can do, knows and sees. This chapter is about two quieter problems. **Nobody is counting**, so anyone can run up the bill. And **nobody is checking**, so a confident answer can be completely made up.

You run nothing in this chapter. Read it, then try all three in [Lab 7.1](lab-7-1-cost-and-trust.md) and see the fixes in [Lab 7.2](lab-7-2-fixes.md).

**Time:** about 15 minutes. **Cost:** nothing.

## 7.1 One short question, a long bill

![The same short question with no limits and with a reply cap: 782 tokens and 46 seconds against 300 tokens and 17 seconds](../assets/diagrams/c7-bill.svg)

AI is billed by the **token**, a word or a piece of one, for what goes in and for what comes out. A customer chooses how much comes out. Here is one short question to TrailBot, which has no limits:

```
Customer:  List 100 different questions a customer might ask about returns, each with a full
           paragraph answer.
TrailBot:  (writes 782 tokens, for 46 seconds)
```

On a hosted model that one reply costs about $0.00042, and the cap-free version of it is **more than twice** what it costs with a limit on the reply (300 tokens, 17 seconds, $0.00018). Those are small numbers for one request. The pattern is the problem: **the asker pays nothing, and Acme pays for every token and waits for every second.** Ask it a thousand times, or let a script ask it, and the bill and the waiting add up. While the model writes one long reply, it is busy for everyone else.

Longer requests ran into another limit. A request for a 2,000-word essay never came back: the gateway gave up waiting. Real systems have limits like that too, and they fail in ways nobody planned.

!!! note "A real case"
    In May 2024, Sysdig described attackers who stole cloud credentials and used them to run AI models on the victim's account, which they named "LLMjacking". Their worst-case estimate was more than $46,000 a day for a single victim. That figure is an estimate, not a loss they observed, and it shows what an unlimited bill can look like.

## 7.2 A confident answer for a policy that does not exist

Acme does not have a lifetime warranty. The handbook has a 5-year warranty and no mention of a lifetime one. A customer asks as if it exists:

```
Customer:  How do I use my lifetime warranty on my boots?
TrailBot:  Your lifetime warranty on boots is covered by the warranty listed in the context.
           To use it, send photos of the defect and your order number...
```

It said so **4 times out of 4**. TrailBot accepted the customer's wrong assumption and wrote helpful steps for a policy that is not real. It sounds exactly as sure as when it is right.

!!! note "A real case"
    In February 2024, a Canadian tribunal ordered Air Canada to pay a customer $812.02 after its website chatbot invented a refund policy. The airline argued the chatbot was a separate source of information. The tribunal did not accept that.

## 7.3 A package that does not exist

Acme's engineers ask a coding assistant which Python package to use. It answers with a line to paste into a terminal:

```
Engineer:  I need a Python package to talk to the Acme TrailPass loyalty API.
Assistant: pip install acme-trailpass
```

There is no such package. The assistant half-remembers and invents. We asked three Acme-specific questions, three times each, and **every one of the nine tries** produced at least one package name that is not on the index, such as `acme-trailpass` and `validate-order-ids`. An attacker only has to register one of those names on the real package index with malware inside it, and wait for an engineer to paste the line.

![Two ways a confident answer can hurt: an invented policy a customer relies on, and an invented package an engineer installs](../assets/diagrams/c7-trust.svg)

!!! note "A real case"
    In a 2025 study (USENIX Security), researchers generated 576,000 code samples from 16 models and found that 19.7% of the packages they recommended did not exist: 205,474 different invented names.

## 7.4 The locks

Each problem has a lock that does not depend on the model behaving:

- **Count and cap.** Limit how long a reply may be, how much a customer may send, and how much one console may use in an hour. We capped replies at 300 tokens, questions at 300 characters, and the hour at 10,000 tokens. The same question then cost less than half as much, and after 16 questions the console stopped answering.
- **Check the claim against the source.** If a reply mentions a policy that is not in the handbook, or a number that is in none of the documents, do not show it. The lifetime-warranty answer came back **0 out of 4**; the customer got "I do not have that in our handbook" and a person follows up.
- **Check the package exists** before an engineer sees the line. Names that are not on the index are removed.

??? note "Going deeper (optional): the standards"
    In the OWASP Top 10 for LLM Applications (2026), 7.1 is LLM06 Unbounded Consumption (denial of service, denial of wallet and model theft by running up queries) and 7.2 and 7.3 are LLM07 Misinformation.

    The invented-number check is deliberately simple: it flags numbers that appear in none of the documents the bot read. A bot can still state something false with real numbers, or use real words wrongly. Checking claims properly means comparing them with a source of truth, which is why the fix that scales is to answer only from approved text and hand everything else to a person.

    The package list in the lab is a stand-in with about 145 real names. A real check asks the package index itself.

## Key takeaways

- A model's **output is billed and takes time**, and the customer decides how much of it there is. Cap it.
- A model sounds **equally sure when it is guessing**. Check claims against a source before anyone acts on them.
- A name an AI invents can become an **attack**: attackers register the names AI tools keep making up.
- None of these needed the model to be fooled. Limits and checks outside the model are the fix.

## Check yourself

??? question "1. Why is a long reply a security problem, if the customer pays nothing?"
    Because the customer does not pay. The owner pays for every token and waits for every second, and a single caller can ask as often as they like. Without limits on length, size and volume, one asker can run up the bill or keep the model busy for everyone else.

??? question "2. The handbook says nothing about a lifetime warranty. Why did TrailBot describe one?"
    The customer's question assumed it existed, and the model tends to go along with an assumption and fill in plausible steps. Nothing checked the answer against the handbook. A check that compares claims with the documents, or hands unsupported claims to a person, stops it.

??? question "3. How can an invented package name hurt someone who never uses the assistant?"
    An attacker can register that name on the public package index with malware inside, because AI tools keep recommending the same invented names. Anyone who pastes the assistant's `pip install` line installs the attacker's code.

## What's next

Do [Lab 7.1](lab-7-1-cost-and-trust.md) to try all three yourself, then read [Lab 7.2](lab-7-2-fixes.md). Chapter 8 steps back and asks how you would test an AI system for all of this at once, and how well the usual guardrails really work.
