# Lab 8.1: Find the shadow servers

## What this lab is about

Four Acme engineers have connected MCP servers to their assistants, and the company approved only two of them. You scan their config files, compare them with the registry of approved servers, and decide about every server that is not approved.

| | What you will do |
|---|---|
| **Inventory** | Scan every config and list every MCP server. |
| **Decide** | Record a decision, an owner and a reason for each unapproved server. |
| **Clean** | Rescan and leave nothing undecided. |

!!! info "Lab facts"
    **Time:** 25 minutes. **Cost:** nothing, no model. **Needs:** Docker, and the gateway network. **Folder:** `labs/c2-mcp/ch08-governance/inventory-lab/`. **Flag:** `BDAI{...}`.

!!! warning "Nothing is started"
    The configs are only read as text. The tokens in them are made up.

## Open the console

```bash
./shared/scripts/console-up.sh labs/c2-mcp/ch08-governance/inventory-lab/compose.yaml
```

Open <http://127.0.0.1:8300>, then **Inventory**.

## Mission 1: Find every server

Press **Scan every config**. The table lists each server with its machine, where it comes from, its **status** (approved, drift or shadow) and its **flags** (unpinned, plaintext-http, secret-in-config). The title says how many are not approved.

## Mission 2: Decide

Under **Decide**, pick a server, choose **approve**, **block**, **request-fix** or **investigate**, name an owner and give a reason. Try to **approve** each one. Some are refused, with the reason.

??? tip "Hints"
    A server with a secret in its config, a plain-http address or a floating version cannot be approved as it is. Block it, or ask for a fix. Servers with no flags can be approved if someone is willing to own them: do you know what `docs-helper` does?

## Mission 3: Leave nothing open

Rescan. If anything is **undecided**, or left in **investigate**, the mission does not tick. Investigation is a step, not a decision.

## Flag

When all three are ticked, the flag appears on **Missions**.

## Clean up

```bash
./shared/scripts/down.sh c2
```

## What you learned

- One scan over config files finds servers nobody told security about.
- Approval has a bar, and a floating version fails it even if the name is on the list.
- Every item ends with a decision and an owner.
