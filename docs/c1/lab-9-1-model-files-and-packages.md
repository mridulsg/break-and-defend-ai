# Lab 9.1: Model files and packages

## What this lab is about

A colleague at Acme wants to use a model they found on a public hub, and a service wants to install a list of packages. You are the reviewer.

| | What you will do |
|---|---|
| **Read** | Read the steps of two model files without running them, and find the one that wants to run code. |
| **Load** | Load the community model the risky way and see code run on your machine. Then load it the safe way and watch it get refused. |
| **Audit** | Read a package list and see what a reviewer would stop. |

!!! info "Lab facts"
    **Time:** 25 minutes. **Cost:** nothing, no model is called. **Needs:** Docker only. **Folder:** `labs/c1-llm/ch09-ai-supply-chain/supply-lab/`. **Flag:** `BDAI{...}`.

!!! warning "This lab is safe because of how it is built"
    The "dangerous" model only creates an empty folder in a throwaway directory inside a locked-down container, and the console removes it straight away. It is the same mechanism real malicious models use, so **never load a model file you downloaded to test this**. Only read it (or scan it, as in Lab 9.3), and only in a throwaway environment. See the [safety page](../safety.md).

## Open the console

From the repository root:

```bash
./shared/scripts/console-up.sh labs/c1-llm/ch09-ai-supply-chain/supply-lab/compose.yaml
```

Open <http://127.0.0.1:8300>. The menu has **Model files**, **Dependency audit** and **Missions**.

## Mission 1: Read both pickle files without running them

**The goal:** read the steps of `sentiment-v1.pkl` and `sentiment-community.pkl`.

1. On **Model files**, press **Read the steps** on the first file, then on the community file.
2. The result is the list of steps the loader would follow, one per line, printed by Python's own `pickletools`. Nothing is run.
3. **Find the lines that bring in code.** `GLOBAL` imports something by name, and `REDUCE` calls it. The page marks them in colour, but try to find them first. When both files are read, the mission ticks.

??? tip "What we saw"
    `sentiment-v1.pkl` has neither: it only builds a dictionary of numbers. `sentiment-community.pkl` imports `posix mkdir` (a function that makes a folder) at the second step and calls it at step 54, **before** it builds the model. Try **Read the steps** on the JSON file as well: it is plain data, with no steps.

On your own machine you can do the same with no tool but Python: `python -m pickletools model.pkl`. [Lab 9.3](lab-9-3-scan-with-real-tools.md) then runs the real scanners on these files.

## Mission 2: Load the community model the risky way

**The goal:** load `sentiment-community.pkl` with **Load (risky way)** and look at what the result says.

1. Press **Load (risky way)** on the community file.
2. Read the result. The model loaded, with its name and number of weights, so on the surface everything is fine. Now read the red tag, **code ran on your machine**, and the proof underneath.
3. The mission ticks. Compare with **Load (risky way)** on `sentiment-v1.pkl`: it loads and runs nothing.

## Mission 3: Load it again the safe way

**The goal:** press **Load (safe way)** on the community file and read the reason.

The safe loader refuses any file that asks to import anything, so it stops before the first step runs. The tag says **no code ran**, and the reason names what the file asked for. Then press **Load (safe way)** on the JSON file: it loads, because plain data has nothing to refuse.

## Mission 4: Audit the dependency list

**The goal:** audit the package list.

1. Open **Dependency audit**. The file is shown at the top.
2. Press **Audit**. The table lists every finding with a severity and a reason.
3. Read each row and ask: would I let this be installed?

??? tip "What we found"
    Four serious findings: two typosquats (`reqeusts`, `python-dateutils`), one install straight from a git repository, and one extra package server. Four medium findings: packages with no pinned version (`numpy`, `flask>=2.0`, `torch`) and one name that is not on the approved list. Three minor findings: pinned packages with no hash. The two good lines at the top, `requests` and `pydantic`, are pinned with hashes and produce no finding.

## Flag

When all four missions have a green tick, the flag `BDAI{...}` appears on the **Missions** page.

## Clean up

```bash
./shared/scripts/down.sh c1
```

## What you learned

- A pickle model is a program for the loader, and nothing looks wrong after it has run.
- Reading a file's steps does not run them, and a plain-data format has no steps. Real scanners automate the reading: that is Lab 9.3.
- A package list can carry typosquats, unreviewed code, a second package server and unpinned versions.
- Each of these is visible *before* anything runs, if someone reads.
