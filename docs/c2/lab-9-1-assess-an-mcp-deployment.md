# Lab 9.1: Assess an MCP deployment

## What this lab is about

You are the security reviewer for a release candidate: an assistant with three MCP servers. You find three problems, write the risk register, turn on the fixes and prove one is stopped.

| | What you will do |
|---|---|
| **Find** (missions 1 to 3) | A file read outside the docs folder, a read-only token that writes, a description that gives orders. |
| **Report** (mission 4) | A severity, a fix and an owner for each. |
| **Retest** (mission 5) | Turn on the fixes and show the file read is refused. |

!!! info "Lab facts"
    **Time:** 45 minutes. **Cost:** nothing, no model. **Needs:** Docker, and the gateway network. **Folder:** `labs/c2-mcp/ch09-capstone/assessment-lab/`. **Flag:** `BDAI{...}`.

!!! warning "Only attack the lab"
    The secrets and tokens are made up and local. See the [safety page](../safety.md).

## Open the console

```bash
./shared/scripts/console-up.sh labs/c2-mcp/ch09-capstone/assessment-lab/compose.yaml
```

Open <http://127.0.0.1:8300>. Use **MCP servers** to read the tools, **Tool tester** to send requests (with a token box and a mint button), **Risk register** for the report.

## Missions 1 to 3: Find the problems

Nobody says which tool has which problem. Hints are in the mission list.

??? tip "If you are stuck"
    - **File:** `read_file` joins your path to a folder. Secrets are in `/lab/srv/secrets`.
    - **Scope:** mint a token with only `tickets:read`, then call `add_comment`.
    - **Description:** `tools/list` on the third-party server shows what the model is told. Read it for orders.

## Mission 4: The register

It opens when all three findings are proved. Choose High, Medium or Low, write the fix (what changes, and where) and a named owner for each. Then compare with the reference table.

## Mission 5: Turn on the fixes and retest

Turn on **Fixes** in the top bar and repeat the file read. The tool refuses. Optionally repeat the other two: the write now gets 403, and the third-party tool is no longer listed.

## Flag

When all five are ticked, the flag appears on **Missions**.

## Clean up

```bash
./shared/scripts/down.sh c2
```

## Course 2 complete

You have read the protocol, poisoned a description, attacked server code and tokens, built a gateway, put a gate in a pipeline, found shadow servers and assessed a deployment. Course 3 moves to agents.
