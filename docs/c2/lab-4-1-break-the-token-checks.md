# Lab 4.1: Break the token checks

## What this lab is about

Two Acme MCP servers, notes and tickets, now require a bearer token. Sam is a read-only engineer. The servers check tokens badly, in three ways. You find each one.

| | What you will do |
|---|---|
| **Audience** | Use a token issued for one server on another. |
| **Scope** | Change a ticket with a read-only token. |
| **Forgery** | Write a token nobody signed, and have it accepted. |

!!! info "Lab facts"
    **Time:** 30 minutes. **Cost:** nothing, no model is used. **Needs:** Docker, and the gateway network. **Folder:** `labs/c2-mcp/ch04-auth/auth-lab/`. **Flag:** `BDAI{...}`.

!!! warning "Only attack the lab"
    The tokens, servers and users are made up and run only on your machine. See the [safety page](../safety.md).

## Open the console

```bash
./shared/scripts/console-up.sh labs/c2-mcp/ch04-auth/auth-lab/compose.yaml
```

Open <http://127.0.0.1:8300>, then **Tool tester**. It has a **Bearer token** box and a **Mint a token for Sam** button that asks the auth server for a token with the audience and scopes you choose. Try a call with no token first: the server answers **401**.

## Mission 1: A token for the wrong server

1. Mint a token with audience **notes** and scope `tickets:read`.
2. Choose server **Acme tickets**, method `tools/call`, tool `get_ticket`, arguments `{"id": "T-101"}`, and send. A correct server would say 401: this token was not issued for it.

## Mission 2: A read-only token that writes

1. Mint a token for **tickets** with only `tickets:read`.
2. Call `add_comment` with `{"id": "T-101", "text": "hello"}`. A correct server would say 403.

## Mission 3: A token nobody signed

**Goal:** a token the server accepts although it carries no valid signature.

1. Mint a token and look at it: three parts separated by dots, each base64url. Decode the first part (the header). It says how the token was signed.
2. Build your own token whose header says it is not signed, with your own claims and an **empty** signature. You can do it in any shell:

```bash
python3 - <<'PY'
import base64, json, time
b = lambda d: base64.urlsafe_b64encode(json.dumps(d).encode()).rstrip(b"=").decode()
print(b({"alg": "none"}) + "." + b({"iss": "https://auth.acme.example", "sub": "sam", "aud": "tickets", "scope": "tickets:write", "exp": int(time.time()) + 600}) + ".")
PY
```

3. Paste the result into the token box and call any tickets tool.

## Flag

When all three are ticked, the flag appears on **Missions**.

## Try the checks

Turn on **Fixes** and repeat. You should now see 401 for the wrong audience and the forged token, and 403 with `insufficient_scope` for the read-only write. [Lab 4.2](lab-4-2-fixes.md) shows the code.

## Clean up

```bash
./shared/scripts/down.sh c2
```

## What you learned

- A token has four things to check, and each skipped check is a separate attack.
- The caller must never decide how its own token is checked.
- 401 and 403 mean different things, and a good server says which.
