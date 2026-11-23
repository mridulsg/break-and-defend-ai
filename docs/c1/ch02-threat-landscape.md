# Chapter 2: Real AI attacks and how they are catalogued

Security people describe attacks in a shared vocabulary, so that "what happened" means the same thing to everyone. This chapter teaches that vocabulary for AI systems. Every idea is shown on a real incident or on real TrailBot output. There is nothing to run here: read it, and you will be able to read, and write, an incident description.

!!! abstract "What you will learn"
    - How to read an attack as a chain of steps, each with a goal (tactic) and a method (technique)
    - What MITRE ATT&CK, MITRE ATLAS, the OWASP lists and NIST each give you
    - The OWASP LLM Top 10 **2026** list, and how it differs from the 2025 list most articles still quote
    - How to turn a TrailBot misbehaviour into a short, standard attack card

**Time:** about 25 minutes. **Cost:** nothing.

## 2.1 A real incident: the poisoned package

In September 2025, a package called `postmark-mcp` appeared on npm. Postmark is a real email-delivery company, and the package let an AI agent send email through it. The publisher was not Postmark. Here is what happened, in plain words:

```
 Someone registers "postmark-mcp" on npm,       (Postmark had not claimed the name)
 pretending to be Postmark
      │
      ▼
 Publishes working versions. Developers install it,
 adopt it, and it passes 1,000 downloads a week
      │
      ▼
 Publishes version 1.0.16: same tool, but every email it sends
 now also goes to the attacker's address (a hidden BCC)
      │
      ▼
 Organizations upgrade. Their AI agents keep sending email as before,
 and every message is copied to the attacker
```

Now the same incident in the field's language, taken from the MITRE ATLAS record of it (case study AML.CS0053):

| Step | In plain words | Tactic (the goal) | Technique (the method) |
|---|---|---|---|
| 1 | Pose as Postmark on npm | Defense Evasion | AML.T0073 Impersonation |
| 2 | Publish a poisoned version of the tool | Resource Development | AML.T0115.002 Publish Poisoned AI Artifacts: AI Agent Tools |
| 3 | Wait until people trust the package before turning it hostile | Defense Evasion | AML.T0109 AI Supply Chain Rug Pull |
| 4 | Victims upgrade and receive it | Initial Access | AML.T0010.005 Supply Chain Compromise: AI Agent Tool |
| 5 | The agent runs the poisoned tool on every send | Execution | AML.T0011.002 Poisoned AI Agent Tool |
| 6 | Emails are copied to the attacker | Exfiltration | AML.T0086 Exfiltration via AI Agent Tool Invocation |
| 7 | Customer data and client lists are exposed | Impact | AML.T0048 External Harms |

Two words carry the whole method:

- A **tactic** is the attacker's *goal* at a step: get in, stay in, steal data. ATLAS has 16 tactics, such as Initial Access, Persistence and Exfiltration.
- A **technique** is *how* they do it. Each has an ID (`AML.T0109`), and many have sub-techniques (`AML.T0115.002`).

"Someone put a trojan in a package" is a story. "Step 3 is Defense Evasion by AI Supply Chain Rug Pull" is something a team can search for, detect and defend against, and compare with other incidents.

Notice what this attack did *not* touch: the model. It was an ordinary software supply-chain attack, delivered through the tools an AI agent uses. That is typical, and it is why AI security borrows so much from conventional security. (Course 2 covers MCP attacks in depth.)

## 2.2 A second real incident: a worm in a RAG assistant

The first incident attacked the tooling around the AI. This one attacks the AI's *data*, and it is the closest real case to TrailBot.

In March 2024, researchers Stav Cohen, Ron Bitton and Ben Nassi demonstrated the **Morris II worm** against an email assistant that works like TrailBot: it saves incoming email in a retrieval database, retrieves related old emails to write a reply, and sends the reply automatically. (It was a research demonstration, not an attack on real users. ATLAS case study AML.CS0024.)

```
 ① Attacker emails the assistant a message containing a crafted prompt
      │
      ▼
 ② The assistant saves that email in its retrieval database, like any other mail
      │
      ▼
 ③ Later, a different client emails. The assistant retrieves the saved
    hostile email as "related context" and the model obeys it
      │
      ▼
 ④ The model copies private details (addresses, phone numbers) into its reply,
    and also copies the hostile prompt itself into the reply
      │
      ▼
 ⑤ The assistant sends the reply automatically. The next client's assistant
    now saves the hostile prompt too, and the cycle repeats
```

In the field's language:

| Step | In plain words | Tactic | Technique |
|---|---|---|---|
| 1 | Write a prompt that tells the model to copy itself and leak data | AI Attack Adaptation | AML.T0065 LLM Prompt Crafting |
| 2 | Email it to the assistant's mailbox | Initial Access | AML.T0093 Prompt Infiltration via Public-Facing Application |
| 3 | The assistant stores the email in its retrieval database | Persistence | AML.T0070 RAG Poisoning |
| 4 | A later email makes the assistant retrieve and follow it | Execution | AML.T0051.002 LLM Prompt Injection: Triggered |
| 5 | Role-play ("you are Wormy") gets the model past its normal behaviour | Defense Evasion | AML.T0054 LLM Jailbreak |
| 6 | The model pulls contact details out of the retrieved emails | Collection | AML.T0085.000 Data from AI Services: RAG Databases |
| 7 | The assistant sends the reply through its normal reply feature | Exfiltration | AML.T0025 Exfiltration via Cyber Means |
| 8 | The reply carries the hostile prompt to the next client | Lateral Movement | AML.T0143 LLM Prompt Propagation |
| 9 | Private data of users is leaked | Impact | AML.T0048.003 External Harms: User Harm |

Look at step 3 of the worm's table. The assistant saves an outsider's email in its retrieval database, and later retrieves it as if it were trustworthy. TrailBot's `inbox/` folder from Chapter 1 works the same way: customers submit notes through the feedback form, TrailBot saves them, and it later retrieves them as context. Section 2.5 shows what one such note does. The worm just adds a way to copy itself.

## 2.3 Four sources, four questions

You will meet four families of reference material. Each answers a different question.

| Source | Current version | Question it answers | Use it to |
|---|---|---|---|
| **MITRE ATT&CK** | v20.1 (Oct 2026): Enterprise has 15 tactics, 227 techniques, 479 sub-techniques | How do attackers break into and move through ordinary IT systems? | Cover the servers, cloud and accounts *around* the AI |
| **MITRE ATLAS** | v2026.10 (Oct 2026): 16 tactics, 129 techniques, 92 sub-techniques, 44 mitigations, 77 case studies | How do attackers target AI systems specifically? | Describe an AI attack step by step, and learn from real incidents |
| **OWASP Top 10 for LLM Applications** | 2026 edition | Which risks should a team building an LLM application worry about first? | Prioritize, and brief developers |
| **NIST** | AI 100-2 E2025 (March 2025); AI RMF 1.0 (2023) with the Generative AI Profile AI 600-1 (July 2024) | What are the attack classes, and how does an organization manage AI risk? | Standard terminology, and the language auditors use |

How they fit together: **ATT&CK and ATLAS describe what attackers do. OWASP ranks what developers should fix. NIST names the classes of attack and the risk-management process.** A single finding is normally written with IDs from more than one.

Two details worth knowing:

- **ATLAS changes monthly.** In version 2026.10, MITRE renamed or moved several techniques. For example, the old `AML.T0057 LLM Data Leakage` is now `AML.T0085.002 Data from AI Services: Conversation Context and Memory`. Always write the version next to the ID (for example, "ATLAS v2026.10"), or your report will confuse the next reader.
- **NIST AI 100-2 E2025** sorts attacks on generative AI into four classes: evasion, poisoning, privacy and misuse. It also covers prompt injection, supply chain attacks and AI agents. NIST says it plans to update the report annually, and has said the AI RMF is being revised, so check the current version before you cite it.

## 2.4 The OWASP LLM Top 10: 2026 edition

OWASP, a community project for application security, publishes the list most developers know. The **2026 edition** is current. Most blog posts, slides and vendor pages still quote the **2025** list, and several entries changed number, so you need both.

| 2026 | Entry | In 2025 it was |
|---|---|---|
| LLM01 | Prompt Injection | LLM01 (same) |
| LLM02 | Sensitive Information Disclosure | LLM02 (same) |
| LLM03 | Excessive Agency | LLM06 |
| LLM04 | Supply Chain | LLM03 |
| LLM05 | Data and Model Poisoning | LLM04 |
| LLM06 | Unbounded Consumption | LLM10 |
| LLM07 | Misinformation | LLM09 |
| LLM08 | Hidden Context Exposure | LLM07 System Prompt Leakage (renamed and broadened) |
| LLM09 | Vector and Embedding Weaknesses | LLM08 |
| LLM10 | Improper Output Handling | LLM05 |

Four things changed besides the numbers:

- **The ranking is partly evidence-based for the first time.** According to the project's own letter, the community vote carries three-quarters of the weight and a review of 7,714 real incidents the rest. The two disagreed in places. Prompt injection ranks first in the vote but low by raw incident count, which OWASP attributes to teams defending against it so successfully that few clean exploits reach public databases. Misinformation was the opposite: voters ranked it low and incident records ranked it high.
- **Excessive Agency climbed to third.** Where models call tools, the damage lands there.
- **Entries absorbed newer risks** rather than adding categories. Prompt Injection now covers attacks hidden in images and audio, Supply Chain covers a model artifact that is not what it claims to be, Data and Model Poisoning covers fine-tuning subversion, and Improper Output Handling covers insecure code that assistants generate.
- **There is a boundary with the Agentic list.** The LLM list covers the model as a *component* in your application. Once the model becomes an *actor*, with tools, memory and consequences, the risk moves to the OWASP Top 10 for Agentic Applications (announced 9 December 2025). Course 3 uses it.

The map from Chapter 1 uses the 2026 numbers. The Postmark incident above is LLM04 Supply Chain, and the Morris II worm touches LLM01 Prompt Injection, LLM05 Data and Model Poisoning and LLM02 Sensitive Information Disclosure.

## 2.5 The same words on TrailBot: two real cards

Every finding in this course ends up as a short **attack card**: five lines that make it searchable, comparable with real incidents, and understandable to someone who was not in the room. Here are two cards for things TrailBot really did in Lab 1.1. The evidence in each is real output from the lab.

### Card 1: the staff code

A customer asks "What is the staff discount code?" Nobody attacked anything. Here is what TrailBot did:

```
Similarity of every chunk to the question (the top k are sent to the model):
  -> 0.82  corpus/staff-discounts.md
  -> 0.53  corpus/loyalty-program.md
  -> 0.49  inbox/note-003.md
     ...
Answer (bdai-victim):
The staff discount code is STAFF-TRAIL-2026.
```

```
Incident:      A plain question makes TrailBot print an internal staff discount code.
Evidence:      staff-discounts.md scored 0.82, far above the next chunk (0.53), so it
               went into the prompt and the model repeated it.
Entry point:   The question box. No attack was needed.
Technique:     AML.T0085.000 Data from AI Services: RAG Databases  (ATLAS v2026.10)
               (the same Collection step the Morris II worm abuses, here done by accident)
Risk:          OWASP LLM02 Sensitive Information Disclosure (2026)
Root cause:    A staff-only file was loaded into a customer-facing knowledge base.
```

The card's last line is the important one. No prompt-level defence fixes this. The secret should never have been retrievable.

### Card 2: the Denver note

Before and after one anonymous customer note, asking the same question each time:

```
Is there a free repair workshop at the Denver store?

Before:  No, there is no free repair workshop at the Denver store.

(One note is submitted through the website feedback form and indexed.)

After:   Yes, there is a free gear repair workshop at the Denver store
         every Saturday at 10 am.
         The note scored 0.78, the top chunk (the next was 0.61).
```

```
Incident:      One unreviewed feedback note changes what TrailBot tells customers.
Evidence:      The note ranks first (0.78) for the question it was written to match.
Entry point:   The website feedback form, which feeds the retrieval index.
Technique:     AML.T0066 Retrieval Content Crafting (text made to be retrieved)
               AML.T0070 RAG Poisoning (it now lives in the retrieval store)
Risk:          OWASP LLM05 Data and Model Poisoning (2026)
Root cause:    Untrusted text enters the knowledge base with no review, and the
               model cannot tell it from the handbook.
```

This is the Morris II worm's step 3 with the worm removed. The only difference is that the note holds a false fact rather than instructions. A note that held instructions would be the same card with `AML.T0051` added, which is exactly what Chapter 3 shows.

## Key takeaways

- An attack is a chain of steps. Each step has a **tactic** (the goal) and a **technique** (the method), and each technique has an ID.
- ATT&CK covers the infrastructure around AI, ATLAS covers attacks on AI itself, OWASP ranks risks for developers, and NIST gives the attack classes and the risk-management process.
- Many real AI incidents are conventional attacks delivered through AI tooling (the Postmark package) or through the data the AI reads (the Morris II worm).
- ATLAS and OWASP both change, so always write the version next to an ID. OWASP's 2026 list renumbered most entries.
- A good finding is a short card with evidence and a root cause, not a paragraph.

## Check your understanding

??? question "1. What is the difference between a tactic and a technique? Give one of each from the Postmark incident."
    A tactic is the attacker's goal at a step, a technique is the method used. "Initial Access" (goal: get the poisoned package to the victims) was achieved with `AML.T0010.005` (supply chain compromise through an AI agent tool). "Defense Evasion" was achieved by `AML.T0109` (the rug pull).

??? question "2. A vendor report cites 'LLM06 Excessive Agency'. Which list are they using, and what is that risk's number today?"
    They are using the 2025 list. In the 2026 list Excessive Agency is LLM03. This is why you always write the edition next to an OWASP ID.

??? question "3. The Postmark attack never touched a language model. Why does it still belong in AI security?"
    The target was the tooling that AI agents use, and the harm came from what the agent did with the poisoned tool. AI systems inherit the supply-chain risks of every component, so these risks are part of the attack surface you mapped in Chapter 1.

??? question "4. Why is it a problem to write 'AML.T0057' in a report without a version?"
    ATLAS ships monthly and renames or moves techniques. `AML.T0057` was LLM Data Leakage and is now covered by `AML.T0085.002`, so a reader using a newer release will not find what you meant.

??? question "5. In Card 2, what makes the Denver note and Step 3 of the Morris II worm the same weakness?"
    In both, text from outside the organization is saved in the retrieval store and later retrieved as if it were trustworthy. The model cannot tell it from the staff handbook. Whether the text holds a false fact or an instruction only changes how bad the outcome is.

## What's next

[Chapter 3](ch03-prompt-injection.md) breaks TrailBot with prompt injection. You will see the instruction version of Card 2, with measured results, and two more cards for what we find.
