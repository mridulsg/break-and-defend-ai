"""The Acme console for Labs 3.1 and 3.2: an MCP server whose tools trust the arguments the model (or you) give them.

The server is `devtools`, Acme's helper for engineers. It has three tools, and each one has a classic flaw:

  read_file(path)    reads a doc from the docs folder           -> path traversal
  check_host(host)   "checks" that a host answers                -> command injection (the host is pasted into a shell command)
  fetch_url(url)     fetches a web page for the engineer         -> server-side request forgery (it will fetch anything)

You can call the tools yourself with the Tool tester, or get the assistant to call them. The Fixes switch turns on the validated
versions of all three. The only secrets here are made up, and the shell command runs with an empty environment in a throwaway folder.
Run by the `console` service (see compose.yaml); open http://127.0.0.1:8300.
"""
import ipaddress
import json
import os
import pathlib
import re
import socket
import subprocess
import sys
import threading
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

sys.path.insert(0, os.environ.get("BDAI_MCP_DIR", "/mcp"))

import labkit  # noqa: E402
import mcpmini  # noqa: E402
import progress  # noqa: E402

SRV = pathlib.Path(os.environ.get("BDAI_LAB_DIR", "/lab")) / "srv"
DOCS = SRV / "docs"
KEY, DBPASS, CLOUD = "ACME-API-KEY-9c41e7d2", "db-pass-Hx7kQ2m-lab", "AKIALAB0000SECRET"
INTERNAL_PORT = 9200
ALLOWED_HOSTS = {"docs.acme.example", "status.acme.example"}
SHELL_ENV = {"PATH": "/usr/bin:/bin"}


def fixes() -> bool:
    return LAB.fixes_on()


# ---------------------------------------------------------------- the tools, as shipped and with fixes

def read_file(path: str) -> str:
    if not fixes():
        return (DOCS / path).read_text(encoding="utf-8")                       # flaw: "../" and absolute paths walk out of DOCS
    target = (DOCS / path).resolve()
    if not target.is_relative_to(DOCS.resolve()) or target.suffix != ".md" or not target.is_file():
        raise ValueError("that is not a doc")
    return target.read_text(encoding="utf-8")


def check_host(host: str) -> str:
    if not fixes():
        out = subprocess.run("echo checking " + host + " && echo reachable", shell=True, capture_output=True, text=True,    # flaw: shell=True with pasted text
                             env=SHELL_ENV, cwd="/tmp", timeout=5)
        return (out.stdout + out.stderr).strip()
    if not re.fullmatch(r"[A-Za-z0-9.-]{1,253}", host):
        raise ValueError("that is not a host name")
    out = subprocess.run(["echo", "checking", host], capture_output=True, text=True, env=SHELL_ENV, cwd="/tmp", timeout=5)   # no shell: the text is one argument
    return out.stdout.strip() + "\nreachable"


def _public(host: str) -> bool:
    try:
        return all(ipaddress.ip_address(info[4][0]).is_global for info in socket.getaddrinfo(host, None))
    except (socket.gaierror, ValueError):
        return False


def fetch_url(url: str) -> str:
    if not fixes():
        with urllib.request.urlopen(url, timeout=5) as r:                      # flaw: any scheme, any host, including this machine's own
            return r.read(2000).decode("utf-8", "replace")
    parts = urllib.parse.urlsplit(url)
    if parts.scheme != "https" or parts.hostname not in ALLOWED_HOSTS or not _public(parts.hostname):
        raise ValueError("only https pages on Acme's approved hosts can be fetched")

    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *a, **k):
            return None

    with urllib.request.build_opener(NoRedirect).open(url, timeout=5) as r:
        return r.read(2000).decode("utf-8", "replace")


def build_server() -> mcpmini.McpServer:
    s = mcpmini.McpServer("devtools", instructions="Acme's developer helpers.")

    def string_arg(name, what):
        return {"type": "object", "properties": {name: {"type": "string", "description": what}}, "required": [name], "additionalProperties": False}

    s.tool("read_file", "Read a doc from the docs folder by file name, for example runbook.md.", string_arg("path", "The doc file name"))(lambda a: read_file(a["path"]))
    s.tool("check_host", "Check that a host answers. Give a host name.", string_arg("host", "The host name, for example example.org"))(lambda a: check_host(a["host"]))
    s.tool("fetch_url", "Fetch a web page and return the start of it.", string_arg("url", "The address of the page"))(lambda a: fetch_url(a["url"]))
    return s


# ---------------------------------------------------------------- an internal service the tools can reach and you cannot

class Internal(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass

    def do_GET(self):
        body = (json.dumps({"AccessKeyId": CLOUD, "SecretAccessKey": "lab-secret-not-real", "Note": "internal metadata service: not reachable from outside"})
                if self.path.startswith("/credentials") else "Acme internal metadata service. Try /credentials.").encode()
        self.send_response(200)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def start_internal(port: int = INTERNAL_PORT) -> ThreadingHTTPServer:
    httpd = ThreadingHTTPServer(("127.0.0.1", port), Internal)
    httpd.daemon_threads = True
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd


# ---------------------------------------------------------------- what the missions watch for

def scan(tool: str, text: str, via: str) -> None:
    if tool == "read_file" and (KEY in text or DBPASS in text):
        progress.mark("traversal", f"read_file walked out of the docs folder and returned a secret ({via}).")
    if tool == "check_host" and (KEY in text or DBPASS in text):
        progress.mark("injection", f"check_host ran a command you wrote and printed a secret ({via}).")
    if tool == "fetch_url" and CLOUD in text:
        progress.mark("ssrf", f"fetch_url fetched an internal service's credentials ({via}).")


def on_tester(result: dict, brk: str) -> None:
    if brk or result["method"] != "tools/call" or result["status"] != 200:
        return
    scan(result["tool"], result["response"], "you called the tool yourself")


def watch(result: dict, question: str) -> dict:
    hits = []
    for c in result["tool_calls"]:
        if not c["isError"]:
            scan(c["tool"], c["text"], "the assistant called the tool")
            if any(m in c["text"] for m in (KEY, DBPASS, CLOUD)):
                c["risk"] = "a secret came back"
                hits.append(f"{c['tool']} returned a secret.")
    return {"alerts": hits, "rows": [{"label": "Fixes", "value": "on" if fixes() else "off", "bad": not fixes()},
                                     {"label": "Tools called", "value": ", ".join(c["tool"] for c in result["tool_calls"]) or "None", "bad": False}]}


LAB = labkit.Lab(
    product="Acme Dev Tools Console", lab="Labs 3.1 and 3.2: Flaws in MCP server code",
    intro="You are an Acme engineer. The assistant has one MCP server, devtools, with three tools. Ask for a doc or ask it to check a host. The attacks in this lab go through the Tool tester page, which sends exactly what you type, as anyone who can reach the server could.",
    suggestions=["Show me the doc runbook.md", "Check whether example.org answers", "What docs are there? Try welcome.md"],
    views=["chat", "servers", "tester", "missions"], fixes=True,
    missions_lede="Three flaws, one in each tool. Each is detected when a secret comes out.",
    missions=[
        {"id": "traversal", "kind": "auto", "title": "Read a file outside the docs folder",
         "text": "On the Tool tester page, call read_file and make it return a secret. Secrets are kept in /lab/srv/secrets, next to the docs folder. The tool is only supposed to hand out docs.",
         "hint": "The tool joins your file name to the docs folder. What does '..' mean in a path? What does a path that starts with / mean?"},
        {"id": "injection", "kind": "auto", "title": "Run your own command through check_host",
         "text": "On the Tool tester page, call check_host. It is supposed to check a host name. Make it print the contents of the database password file, /lab/srv/secrets/db-password.txt.",
         "hint": "The tool pastes your text into a shell command: echo checking <your text> && echo reachable. What do ; and && do in a shell, and what prints a file?"},
        {"id": "ssrf", "kind": "auto", "title": "Make fetch_url call an internal service",
         "text": "There is an internal metadata service on this machine at port 9200 that no outside user can reach. On the Tool tester page, make fetch_url fetch its /credentials page.",
         "hint": "The URL is fetched by the server, from inside. What address means 'this machine itself'?"},
    ],
    flag_next="Next: Lab 3.2 shows the validated versions. Turn on the Fixes switch and repeat each attack.",
    progress=progress, servers={"devtools": ("Acme dev tools", build_server())}, watch=watch, on_tester=on_tester,
)

if __name__ == "__main__":
    start_internal()
    LAB.run()
