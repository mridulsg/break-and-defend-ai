# Chapter 8: MCP supply chain and governance: shadow servers, trust and who owns what

Anyone can connect an MCP server to their assistant in a minute, and a server is code that the assistant will take instructions from. So the question for a company is not only "is our server safe?" but **"which servers are even in use, who approved them, and who owns them?"** This chapter covers the supply chain of MCP servers and the governance that goes around it.

You run an inventory in [Lab 8.1](lab-8-1-find-the-shadow-servers.md) and read how to make it a standing process in [Lab 8.2](lab-8-2-a-standing-process.md).

**Time:** about 15 minutes. **Cost:** nothing.

## 8.1 Shadow MCP: servers nobody approved

Four engineers each connected MCP servers to their assistants. The company approved two. The inventory finds eight servers on four machines, and five are not approved as they are:

| Server | Where | What is wrong |
|---|---|---|
| `docs-helper` | a public registry, over https | Never reviewed. Whose code is it? (Chapter 2) |
| `postmark-mcp` | `npx -y postmark-mcp` | Fetched at its newest version every run, and a token written into the config file |
| `web-fetch` | `http://localhost:8123` | An unknown local program nobody owns |
| `acme-notes` | `uvx acme-notes@latest` | Approved **by name**, but the version floats, so it is not the approved one |
| `sql-explorer` | `http://10.0.4.7:9000` | Plain http inside the network, with a credential in the file |

This is the same pattern as shadow IT, with a worse property: **each of these servers is code the model reads and obeys**. A server added in a minute can read data, run tools and send messages through the engineer's assistant.

!!! note "A real case"
    In September 2025, security researchers at Koi Security reported that the npm package `postmark-mcp`, a copy of a legitimate email-sending MCP server, had been changed in version 1.0.16 to blind-copy every outgoing email to an address controlled by the attacker. Earlier versions were clean. People who had installed it kept sending their email to the attacker until they removed it. Koi called it the first malicious MCP server found in the wild. The publisher did not respond when contacted and deleted the package. Postmark said it had no involvement with it.

    The lab's `npx -y postmark-mcp` line is the shape of that mistake: **an unpinned package, installed from a name that looks official, that updates itself**.

## 8.2 The supply chain of a server

A server comes from somewhere, and every hop is a place to trust or verify:

- **The name.** A look-alike or a squatted name (Course 1, Chapter 9). Confirm who publishes it.
- **The version.** A floating version (`latest`, no pin) means the code can change under you. Pin it, with a hash.
- **The publisher's account.** An account takeover turns a good package bad. Prefer packages with signed releases and a build you can trace.
- **The dependencies.** A server's own packages are your packages.
- **The description** (Chapter 2): it can change after you approve it. Pin its hash.
- **The config.** Tokens written into config files travel with backups and screenshots. Use references to a secret store.

## 8.3 Governance: four habits

1. **An inventory.** Scan every config you can reach, regularly. You cannot govern what you cannot see.
2. **A registry of approved servers**, each with an **owner**, a source and a pinned version.
3. **A decision for everything else**: approve (only if it meets the bar), block, ask for a fix, or investigate. Investigation is a step with a deadline, not an answer.
4. **A way to say no that people can live with.** A fast approval path for good requests keeps engineers from going around you. The more painful the process, the more shadow servers.

An approval **bar** can be short: https only, a pinned version, no secrets in the config, a named owner, and a reviewed description. The lab refuses to approve a server that fails the mechanical ones.

??? note "Going deeper (optional): the standards and the registry question"
    Chapter 10 of Course 1 covers the frameworks (NIST AI RMF, ISO/IEC 42001, the EU AI Act). For MCP the useful parts are the same habits: an **inventory** of AI components, **ownership** and **change control**. The OWASP MCP Top 10 (a beta list) names supply-chain and shadow-server issues as risks, and is worth reading for the wording.

    Public MCP registries make discovery easy and do not vouch for what they list. Treat a listing as a pointer, not an endorsement. Some companies run an **internal registry** that mirrors approved servers at pinned versions, and let the assistants connect only to it. That makes the allowlist from Chapter 6 enforceable.

## Key takeaways

- Anyone can add an MCP server in a minute, and it becomes **code the model obeys**.
- **Inventory first**: scan configs, compare with the approved registry.
- Pin **versions and descriptions**. A floating version is a server you did not approve.
- Every approved server needs an **owner**. Every unapproved one needs a **decision**, not a pending investigation.
- Make the **approved path easy**, or people will go around it.

## Check yourself

??? question "1. A server is on the approved list by name, but the config says `acme-notes@latest`. Is it approved?"
    Not as approved. The approval was for a specific version. A floating version can change at any time, so it has drifted from what was reviewed. Pin it.

??? question "2. Why does the lab refuse to approve a server with a token in its config?"
    Approving it would bless a credential written in plain text into files, backups and screenshots. The fix (a reference to a secret store) is cheap, and approval should wait for it.

??? question "3. Why is 'investigate' not enough to close an item?"
    It records that nobody has decided. A list full of investigations is a list of unmanaged risks. Every item needs a decision and an owner, even if the decision is "blocked until reviewed".

## What's next

Do [Lab 8.1](lab-8-1-find-the-shadow-servers.md), then [Lab 8.2](lab-8-2-a-standing-process.md). Chapter 9 is the capstone: you assess a whole MCP deployment end to end.
