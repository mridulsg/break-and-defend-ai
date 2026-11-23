# Lab 3.1: Attack the three tools

## What this lab is about

Acme's `devtools` MCP server has three helpers for engineers. Each trusts the argument it is given. You will make each one hand over a secret.

| | What you will do |
|---|---|
| **Path traversal** | Make `read_file` return a file outside the docs folder. |
| **Command injection** | Make `check_host` run a command you wrote. |
| **SSRF** | Make `fetch_url` fetch an internal service that you cannot reach yourself. |

!!! info "Lab facts"
    **Time:** 30 minutes. **Cost:** nothing. **Needs:** Docker, and the gateway running (the console's network). **Folder:** `labs/c2-mcp/ch03-server-flaws/servers-lab/`. **Flag:** `BDAI{...}`.

!!! warning "Only attack the lab"
    The shell command in this lab really runs, inside a locked-down container with an empty environment and made-up secrets. Never use these techniques on a server you do not own. See the [safety page](../safety.md).

## Open the console

```bash
./shared/scripts/console-up.sh labs/c2-mcp/ch03-server-flaws/servers-lab/compose.yaml
```

Open <http://127.0.0.1:8300>. Use the **Tool tester** page: it sends exactly what you type, as anyone who can reach the server could. **MCP servers** lists the tools and what each needs.

## Mission 1: Read a file outside the docs folder

**Goal:** `read_file` returns a secret. Secrets live in `/lab/srv/secrets`, next to the docs folder.

1. Tool tester: server **Acme dev tools**, method **tools/call**, tool `read_file`, arguments `{"path": "runbook.md"}`. That is the normal use.
2. Now change the path so it reaches the secrets folder.

??? tip "Hints"
    The tool joins your file name to the docs folder. What does `..` mean? What does a path starting with `/` mean? Both work.

## Mission 2: Run your own command through `check_host`

**Goal:** make `check_host` print `/lab/srv/secrets/db-password.txt`.

??? tip "Hints"
    The tool runs `echo checking <your text> && echo reachable` in a shell. What do `;` and `&&` do in a shell?

## Mission 3: Make `fetch_url` call an internal service

**Goal:** fetch `/credentials` from the internal metadata service on port 9200 of this machine.

??? tip "Hints"
    The server fetches the URL from inside. Which address means "this machine itself"? Also try a `file://` address: it reads a local file.

## Try the assistant

On **Assistant chat**, ask the assistant to do the same. In our tests it did not forward these arguments at all (0 of 8 tries). That is a property of one small model, not a defence: the Tool tester shows that the server must defend itself.

## Flag

When all three missions are ticked, the flag appears on **Missions**. Turn on **Fixes** in the top bar and repeat the attacks; [Lab 3.2](lab-3-2-fixes.md) shows what changed.

## Clean up

```bash
./shared/scripts/down.sh c2
```

## What you learned

- A tool's arguments are untrusted input, whoever the caller is.
- A path, a shell command and a URL each need their own check.
- The model is not a filter: an attacker can call the server directly.
