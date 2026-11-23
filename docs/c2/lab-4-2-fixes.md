# Lab 4.2: Fixes for the token checks

In [Lab 4.1](lab-4-1-break-the-token-checks.md) you used a token on the wrong server, wrote with a read-only token and forged a token. Turn on **Fixes** in the console and repeat each attack. The code is in `verify()` and `need()` in `app/console.py`.

## Fix 1: Decide the algorithm on the server, and verify the signature

```python
if head.get("alg") != "HS256" or not signature_is_good:
    raise deny(401, "invalid_token", resource)
```

The header is just a claim by the caller. The server expects one algorithm and rejects the rest, so `alg: none` is refused.

## Fix 2: Check the audience and the issuer

```python
if claims.get("aud") != resource or claims.get("iss") != ISSUER:
    raise deny(401, "invalid_token", resource)
```

A token for notes is not a token for tickets. In a real OAuth setup the client asks for the audience with the `resource` parameter, and the server compares it with its own identifier.

## Fix 3: Check the scope for the tool

```python
SCOPES = {"get_ticket": "tickets:read", "add_comment": "tickets:write", ...}

def need(claims, tool, resource):
    if SCOPES[tool] not in claims["scope"].split():
        raise deny(403, "insufficient_scope", resource, SCOPES[tool])
```

The 403 carries `WWW-Authenticate: Bearer error="insufficient_scope", scope="tickets:write", resource_metadata=...` so a client knows what to ask for.

## Fix 4: Say why, the standard way

```python
def deny(status, error, resource, scope=None):
    # 401 for a missing, bad or expired token; 403 for a good token without enough scope
    header = f'Bearer error="{error}", resource_metadata="https://{resource}.acme.example/.well-known/oauth-protected-resource"'
```

## What it costs, and what is still open

- Signature, expiry, audience and scope cost almost nothing at run time.
- **Do not write this yourself in production.** Use an OAuth 2.1 library and a tested token validator. The lab's hand-built token is for learning.
- Never forward the caller's token to another service. Exchange it for a new token for that service, with the caller's rights.
- Even a correct token check does not stop a poisoned description from steering the model. Scopes limit what the steered call can do. Chapter 6 combines both.
