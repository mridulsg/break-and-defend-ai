# Chapter 7: DevSecOps for MCP servers: scanning, pinning and a gate before release

Chapters 2 to 4 attacked servers and Chapter 6 defended the host. This chapter moves the checks **earlier**: into the pipeline that builds and ships an MCP server, so that a flawed server is stopped before anyone connects to it. Every check you have met becomes a step, and a **gate** decides whether the build may go on.

You run a pipeline in [Lab 7.1](lab-7-1-run-the-pipeline.md) and read what scanners cannot do in [Lab 7.2](lab-7-2-gate-and-limits.md).

**Time:** about 15 minutes. **Cost:** nothing.

## 7.1 The pipeline, step by step

An MCP server is a normal program with an unusual caller. So it gets the normal checks, plus a few that are specific to MCP:

| Step | Checks | Catches (from this course) |
|---|---|---|
| **1. Secrets scan** | Keys and tokens in the source | A key in `server.py` (Chapter 3) |
| **2. Static analysis** | Risky patterns in the code | `shell=True`, path joins, an open `urlopen` (Chapter 3) |
| **3. Tool definition review** | The names, descriptions and schemas, as a diff | Instructions in a description (Chapter 2); a changed definition |
| **4. Dependency check** | Exact versions, hashes, one package index | An unpinned or look-alike package (Course 1, Chapter 9) |
| **5. Container check** | Base image by digest, a non-root user | A moving base image, a server running as root |
| **6. Tests** | The attack suite from Chapter 6, against the built server | A control that quietly stopped working |
| **7. Gate** | Fail the build if anything is at or above the threshold | Everything above, before release |

The lab's scanner is steps 1, 2, 3, 4 and 5 in one small program, and the gate is step 7.

## 7.2 Two projects, one gate

The lab has two versions of the same server. The **vulnerable** one has a hard-coded key, a shell command built from text, a path joined without checking, a URL opened without checking, a description that gives orders to the model, loose input schemas, an unpinned dependency list with a second package index, and a container that runs as root from a moving tag. The scanner finds **14 problems**, 4 of them high.

The **fixed** one resolves the path, passes arguments as a list, validates the host name, removes the URL tool, reads the key from the environment, writes a plain description, forbids extra arguments, pins every dependency with a hash, pins the base image by digest and runs as an ordinary user. The scanner finds **nothing**.

The gate is one line of policy: **fail the build when a finding is at or above the threshold**. Set it to *high* and only the worst stop the build. Set it to *low* and nothing passes unless it is clean. Teams usually start loose and tighten as the backlog shrinks.

## 7.3 Treat tool definitions as code

The most MCP-specific step is the third. A tool's description is **a security-relevant part of the interface**, so it belongs in code review:

- Keep the definitions in source control, and review **changes to descriptions** like changes to permissions.
- Generate a hash of the definitions at build time and publish it. A host can then **pin** it (Chapter 6), and a changed definition becomes a visible, reviewed event rather than a quiet update.
- Fail the build when a description contains instructions to the model or names another server's tools.

## 7.4 What a scanner cannot do

- It reads **lines**, not **meaning**. A command built in a way it does not recognise passes. A description reworded to avoid its word list passes.
- It finds **known patterns**. A logic flaw (a missing owner check, a missing scope check from Chapter 4) is invisible to it.
- It produces **false positives**. A gate that blocks on noise gets switched off, so tune it.
- A passing build means **nothing known was found**, not that the server is safe. Keep the tests, the review and the gateway.

??? note "Going deeper (optional): SBOMs, signing and provenance"
    A **software bill of materials (SBOM)** lists every package in a build. Generate one in the pipeline and keep it, so that when a package is reported as compromised (as `litellm` was in March 2026) you can answer "which servers have it?" in minutes. **Signing** the built image and checking the signature at deploy time proves it came from your pipeline, and **provenance** records how it was built. Together with pinned digests they close the gap between "reviewed" and "what is actually running".

    Run the pipeline itself with care: it holds the credentials to publish. A compromised build tool is how the `litellm` packages were published by an attacker, according to reports.

## Key takeaways

- Put every check you know **into the pipeline**, and make a **gate** decide.
- Treat **tool descriptions as security-relevant code**: review them, hash them, publish the hash.
- Pin **dependencies and base images** by hash or digest.
- A scanner finds **patterns, not meaning**. Pair it with tests, review and a gateway.

## Check yourself

??? question "1. The gate is set to *high* and the build passes with 6 medium findings. Is that a problem?"
    It is a choice. A loose gate lets medium findings ship. It is a reasonable place to start if the backlog is large, but the threshold should tighten over time, and someone should own the medium findings.

??? question "2. Why review a change to a tool description like a change to permissions?"
    The model treats a description as guidance, so a changed description changes what the assistant does. It can leak data or steer calls without any change in code.

??? question "3. The scanner passes a server that skips the owner check on every ticket. Why?"
    It looks for patterns in lines. A missing check is the absence of a line, which no pattern matches. Tests that call the server as a different user find it.

## What's next

Do [Lab 7.1](lab-7-1-run-the-pipeline.md), then read [Lab 7.2](lab-7-2-gate-and-limits.md). Chapter 8 widens the view: where servers come from, who approves them, and how a company keeps track of the ones nobody told it about.
