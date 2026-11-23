# Lab 7.1: Run the pipeline

## What this lab is about

A team wants to ship an MCP server. You run the pipeline on two versions of it, and a gate decides whether the build may go on.

| | What you will do |
|---|---|
| **Scan** | Run the scanner on the vulnerable project and read every finding. |
| **Block** | See the gate stop the build. |
| **Ship** | Run the fixed project through the strictest gate. |

!!! info "Lab facts"
    **Time:** 25 minutes. **Cost:** nothing, no model is used. **Needs:** Docker, and the gateway network. **Folder:** `labs/c2-mcp/ch07-devsecops/pipeline-lab/`. **Flag:** `BDAI{...}`.

!!! warning "The projects are never run"
    The sample projects are only read as text, and have the file ending `.sample` so nothing can import or run them.

## Open the console

```bash
./shared/scripts/console-up.sh labs/c2-mcp/ch07-devsecops/pipeline-lab/compose.yaml
```

Open <http://127.0.0.1:8300>, then **Pipeline**.

## Mission 1: Scan the vulnerable project

1. Choose project **vulnerable** and **Run**. The table lists every finding with its file, line, rule and severity.
2. Press **Show the files** and match each finding to the line it points at. Which ones do you recognise from Chapters 2 and 3?

## Mission 2: Let the gate stop the build

Look at the banner above the table: **BUILD BLOCKED**, with how many findings were at or above the threshold. Try the three thresholds. Does any of them let the vulnerable project through?

## Mission 3: Ship the fixed project

1. Choose **fixed**, set the threshold to **low**, and **Run**. It should say **BUILD PASSED** with no findings.
2. Use **Show the files** on both projects and compare them. For each of the 14 findings, find the change that removed it.

## Flag

When all three are ticked, the flag appears on **Missions**.

## Clean up

```bash
./shared/scripts/down.sh c2
```

## What you learned

- One scanner can check code, dependencies and the container.
- A gate turns findings into a decision, at a threshold you choose.
- Each finding has a specific fix, and the fixed project shows all of them together.
