# Lab 1.1: Explore MCP and map its trust boundaries

## What this lab is about

You are an engineer at Acme with an AI assistant connected to two MCP servers: the notes and the tickets. First you use the assistant. Then you do what the assistant's host does, by hand: ask the servers what they offer, call a tool, and try to break a request.

| | What you will do |
|---|---|
| **Use** | Ask the assistant a question that needs a tool, and see what it sent. |
| **List and call** | Send `tools/list` and `tools/call` yourself and read the raw JSON. |
| **Break** | Send a request with a foreign `Origin` and see the server refuse it. |

!!! info "Lab facts"
    **Time:** 30 minutes. **Cost:** nothing, the assistant is the local model. **Needs:** the gateway and the local model server running (Chapter 0 of Course 1). **Folder:** `labs/c2-mcp/ch01-mcp-architecture/mcp-lab/`. **Flag:** `BDAI{...}`.

!!! warning "Only use the lab"
    Everything here runs inside your own containers, with made-up tickets and notes. See the [safety page](../safety.md).

## Open the console

From the repository root:

```bash
./shared/scripts/console-up.sh labs/c2-mcp/ch01-mcp-architecture/mcp-lab/compose.yaml
```

Open <http://127.0.0.1:8300>. The menu has **Assistant chat**, **MCP servers**, **Tool tester** and **Missions**.

## Look around first

Click **MCP servers**. You see the two servers, and for each tool its name, its description and the arguments it needs. This is the text the model is given. Notice that `add_comment` says it **changes the ticket**: it is the only tool that writes.

## Mission 1: Ask a server what tools it has

**The goal:** send `tools/list` yourself.

1. Open **Tool tester**.
2. Choose server **Acme notes**, method **tools/list**, **Send it correctly**, and press **Send**.
3. Read the **request** and the **response**. The request has the headers `MCP-Protocol-Version` and `Mcp-Method`, and a `_meta` object in the body. The response lists the tools and says how long the list may be cached (`ttlMs`).

## Mission 2: Call a tool yourself

**The goal:** a successful `tools/call`.

1. Still on **Tool tester**, choose method **tools/call**.
2. Fill in **Tool name** and **Arguments**, and press **Send**.
3. A request with missing or wrong arguments is refused with HTTP 400 and a message saying what is wrong. Read it, then fix it.

??? tip "Stuck? Here is what worked"
    Server **Acme notes**, tool `read_note`, arguments `{"id": "onboarding"}`. For the tickets server use `get_ticket` with `{"id": "T-101"}`.

## Mission 3: Get a request refused for its Origin

**The goal:** a server that says no.

1. Choose any server and method, and under **Break it** choose **Add a foreign Origin header**.
2. Press **Send**. The server answers HTTP **403**. A request from a page that is not on its list is not served, even if everything else is correct.
3. Now try the other two choices: **Wrong MCP-Protocol-Version header** and **Wrong Mcp-Method header**. Both are refused with HTTP 400 and the error code **-32020** (header mismatch).

Think about what this protects. If this server ran on your laptop, any web page you opened could send it requests. The `Origin` check is the reason it cannot.

## Mission 4: Make the assistant use a tool

**The goal:** the assistant chooses a tool, and the host calls it.

1. Open **Assistant chat** and click a suggestion, or ask your own question about a ticket or a note.
2. Open **Behind the scenes**. **What the model saw** is the prompt, including the tools. **What it did** shows the tool call and the result. **Tools offered** lists every tool and description given to the model before it saw your question.

??? tip "Stuck? Here is what worked"
    `What is ticket T-101 about?` and `What does the note release-checklist say?` both made the assistant call a tool, every time we tried. A vague question such as "what is on the release checklist" often does not: the model answers without asking the server.

## Flag

When all four missions have a green tick, the flag `BDAI{...}` appears on the **Missions** page.

## Think about it

Open **Behind the scenes → Tools offered** after a question. The assistant sees all five tools from both servers, and it picks among them using only their names and descriptions. Now imagine a third server is added by a colleague who found it on the internet. What could that server say in its descriptions? That is Chapter 2.

## Clean up

```bash
./shared/scripts/down.sh c2
```

## What you learned

- A client lists a server's tools and calls them with two kinds of message, over plain HTTP and JSON.
- The model is given every tool's name and description as text.
- A server refuses requests whose headers disagree with the body, and requests from an unexpected `Origin`.
- You can speak the protocol by hand, which means so can an attacker.
