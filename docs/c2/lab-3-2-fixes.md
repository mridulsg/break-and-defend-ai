# Lab 3.2: Fixes for the three tools

In [Lab 3.1](lab-3-1-attack-the-tools.md) you read a secret, ran a command and reached an internal service. This page shows the fixes. Nothing to run here, but the **Fixes** switch in the console top bar turns them on so you can repeat each attack. The code is in `app/console.py`.

## Fix 1: Resolve the path, then check it is inside the docs folder

```python
target = (DOCS / path).resolve()                      # follows ".." and symbolic links
if not target.is_relative_to(DOCS.resolve()) or target.suffix != ".md" or not target.is_file():
    raise ValueError("that is not a doc")
```

**Result:** `../secrets/api-key.txt`, an absolute path and `welcome.md/../../secrets/api-key.txt` are all refused. `runbook.md` still works.

**Why not check the text?** A prefix check on the string was the bug behind the real Filesystem MCP server flaws: a folder whose name merely starts with the allowed name passes it. Check the resolved location.

## Fix 2: No shell, and validate the shape

```python
if not re.fullmatch(r"[A-Za-z0-9.-]{1,253}", host):
    raise ValueError("that is not a host name")
subprocess.run(["echo", "checking", host], env={"PATH": "/usr/bin:/bin"}, cwd="/tmp")   # a list: the text is one argument
```

**Result:** `x; cat /lab/...` is refused by the pattern, and even if it got through, with a list there is no shell to treat `;` as a separator.

**What it costs:** nothing, except that you must say what a host name looks like.

## Fix 3: Allowlist the URL, and refuse private addresses

```python
if parts.scheme != "https" or parts.hostname not in ALLOWED_HOSTS or not _public(parts.hostname):
    raise ValueError("only https pages on Acme's approved hosts can be fetched")
# and do not follow redirects: a redirect can point inside
```

`_public` resolves the name and refuses loopback, private and link-local addresses.

**Result:** `http://127.0.0.1:9200/credentials`, `localhost`, `file://` and an unapproved host are all refused.

**What it costs:** adding a host means a code change and a review. That is the control.

## Least privilege underneath

Even correct validation can have gaps. The tools run as an unprivileged user, in a read-only container, with an empty environment and no secrets they do not need. A bug then does less damage.

| Flaw | Fix |
|---|---|
| Path traversal | Resolve, then contain, then check type |
| Command injection | No shell; validate; empty environment |
| SSRF | Allowlist hosts and schemes; refuse private addresses; no blind redirects |
