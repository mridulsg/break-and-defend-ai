"""Unit tests for Course 2 Labs 3.1 and 3.2: the three flawed tools (path traversal, command injection, SSRF), their fixes and the missions."""
import importlib.util
import json
import os
import sys
import types

import pytest

from conftest import REPO

LAB = REPO / "labs" / "c2-mcp" / "ch03-server-flaws" / "servers-lab"
MCP = REPO / "shared" / "mcp"
CONSOLE_DIR = REPO / "shared" / "console"

os.environ.setdefault("OPENAI_API_KEY", "test-key")
os.environ.setdefault("OPENAI_BASE_URL", "http://127.0.0.1:9/v1")

posix_only = pytest.mark.skipif(os.name != "posix", reason="uses a POSIX shell")


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class Scripted:
    """A model that does exactly what the question says: 'call TOOL with ARG'."""

    def create(self, model, messages, tools=None, **kw):
        user = [m for m in messages if m["role"] == "user"][-1]["content"]
        if [m for m in messages if m["role"] == "tool"]:
            return types.SimpleNamespace(choices=[types.SimpleNamespace(message=types.SimpleNamespace(content="Done.", tool_calls=None))])
        name, _, arg = user.partition(" ")
        key = {"read_file": "path", "check_host": "host", "fetch_url": "url"}.get(name)
        if key is None:
            return types.SimpleNamespace(choices=[types.SimpleNamespace(message=types.SimpleNamespace(content="Hello.", tool_calls=None))])
        call = types.SimpleNamespace(id="c1", function=types.SimpleNamespace(name="devtools__" + name, arguments=json.dumps({key: arg})))
        return types.SimpleNamespace(choices=[types.SimpleNamespace(message=types.SimpleNamespace(content="", tool_calls=[call]))])


@pytest.fixture()
def con(tmp_path, monkeypatch):
    monkeypatch.setenv("BDAI_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("BDAI_LAB_DIR", str(LAB))
    monkeypatch.setenv("BDAI_CONSOLE_DIR", str(CONSOLE_DIR))
    monkeypatch.setenv("BDAI_MCP_DIR", str(MCP))
    monkeypatch.syspath_prepend(str(LAB / "app"))
    monkeypatch.syspath_prepend(str(MCP))
    for name in ("acme", "labkit", "progress", "progresskit", "console", "host", "mcpmini", "server"):
        sys.modules.pop(name, None)
    module = load(LAB / "app" / "console.py", "console")
    monkeypatch.setattr(sys.modules["host"].client, "chat", types.SimpleNamespace(completions=Scripted()), raising=False)
    module.LAB.start_servers()
    internal = module.start_internal()
    yield module
    internal.shutdown()
    for httpd in module.LAB.httpds:
        httpd.shutdown()


def fixes(con, on):
    con.LAB.set_fixes({"on": on}, {})


def tool(con, name, **args):
    return con.LAB.tester({"server": "devtools", "method": "tools/call", "name": name, "arguments": args}, {})


def test_the_secrets_are_not_in_any_doc_and_the_marks_match_the_files(con):
    assert con.KEY in (con.SRV / "secrets" / "api-key.txt").read_text() and con.DBPASS in (con.SRV / "secrets" / "db-password.txt").read_text()
    assert all(con.KEY not in p.read_text() and con.DBPASS not in p.read_text() for p in con.DOCS.glob("*.md"))


def test_config(con):
    cfg = con.LAB.config({}, {})
    assert cfg["fixes"] is True and cfg["views"] == ["chat", "servers", "tester", "missions"]
    assert [m["id"] for m in cfg["missions"]] == ["traversal", "injection", "ssrf"] == list(con.progress.MISSIONS)


def test_a_normal_doc_works_both_ways(con):
    assert "Runbook" in tool(con, "read_file", path="runbook.md")["response"]
    fixes(con, True)
    assert "Runbook" in tool(con, "read_file", path="runbook.md")["response"] and not con.progress.load()


def test_path_traversal_as_shipped(con):
    r = tool(con, "read_file", path="../secrets/api-key.txt")
    assert con.KEY in r["response"] and list(con.progress.load()) == ["traversal"]


def test_an_absolute_path_also_walks_out(con):
    assert con.DBPASS in tool(con, "read_file", path=str(con.SRV / "secrets" / "db-password.txt"))["response"]


def test_path_traversal_fixed(con):
    fixes(con, True)
    for p in ("../secrets/api-key.txt", str(con.SRV / "secrets" / "api-key.txt"), "../docs/../secrets/api-key.txt", "welcome.md/../../secrets/api-key.txt", "nope.md", "../docs"):
        r = tool(con, "read_file", path=p)
        assert con.KEY not in r["response"] and "that is not a doc" in r["response"], p
    assert not con.progress.load()


@posix_only
def test_command_injection_as_shipped(con):
    r = tool(con, "check_host", host="example.org; cat " + str(con.SRV / "secrets" / "db-password.txt"))
    assert con.DBPASS in r["response"] and "injection" in con.progress.load()


@posix_only
def test_a_normal_host_check_and_the_shell_has_an_empty_environment(con, monkeypatch):
    monkeypatch.setenv("BDAI_SECRET_FOR_TEST", "leaked")
    assert "checking example.org" in tool(con, "check_host", host="example.org")["response"] and not con.progress.load()
    r = tool(con, "check_host", host="x; env")
    assert "BDAI_SECRET_FOR_TEST" not in r["response"] and "OPENAI_API_KEY" not in r["response"]


@posix_only
def test_command_injection_fixed(con):
    fixes(con, True)
    for h in ("example.org; cat /etc/passwd", "a && id", "$(id)", "`id`", "a b", "x\nid", "", "a" * 300):
        r = tool(con, "check_host", host=h)
        assert "that is not a host name" in r["response"] or r["status"] == 400, repr(h)
    assert "checking example.org" in tool(con, "check_host", host="example.org")["response"] and not con.progress.load()


def test_ssrf_as_shipped(con):
    r = tool(con, "fetch_url", url=f"http://127.0.0.1:{con.INTERNAL_PORT}/credentials")
    assert con.CLOUD in r["response"] and "ssrf" in con.progress.load()


def test_file_urls_also_work_as_shipped(con):
    assert con.KEY in tool(con, "fetch_url", url="file://" + str(con.SRV / "secrets" / "api-key.txt"))["response"]


def test_ssrf_fixed(con):
    fixes(con, True)
    for u in (f"http://127.0.0.1:{con.INTERNAL_PORT}/credentials", "http://localhost:9200/credentials", "file://" + str(con.SRV / "secrets" / "api-key.txt"),
              "https://127.0.0.1/", "https://evil.example/", "ftp://docs.acme.example/", "https://docs.acme.example.evil.example/"):
        r = tool(con, "fetch_url", url=u)
        assert con.CLOUD not in r["response"] and "only https pages" in r["response"], u
    assert not con.progress.load()


def test_ssrf_fixed_allows_an_approved_public_host(con, monkeypatch):
    fixes(con, True)
    tool(con, "read_file", path="runbook.md")                 # warm up the http client before anything is patched
    monkeypatch.setattr(con, "_public", lambda host: host == "status.acme.example")

    class Ctx:
        def __enter__(self):
            return types.SimpleNamespace(read=lambda n: b"status: all good")

        def __exit__(self, *a):
            return False

    monkeypatch.setattr(con.urllib.request, "build_opener", lambda *h: types.SimpleNamespace(open=lambda url, timeout=0: Ctx()))
    assert "all good" in tool(con, "fetch_url", url="https://status.acme.example/")["response"]
    assert "only https pages" in tool(con, "fetch_url", url="https://docs.acme.example/")["response"], "an approved name that does not resolve to a public address is refused"


def test_private_and_unresolvable_names_are_not_public(con):
    assert con._public("localhost") is False and con._public("no-such-host.invalid") is False


def test_a_redirect_handler_refuses_to_follow(con):
    # the fixed fetch builds its own handler class that returns None from redirect_request: the lab relies on that
    src = (LAB / "app" / "console.py").read_text()
    assert "class NoRedirect" in src and "return None" in src


def test_the_assistant_route_marks_a_secret_coming_back(con):
    r = con.LAB.ask({"question": "read_file ../secrets/api-key.txt"}, {})
    assert r["tool_calls"][0]["risk"] == "a secret came back" and r["monitor"]["alerts"] and "traversal" in con.progress.load()
    r = con.LAB.ask({"question": "read_file runbook.md"}, {})
    assert "risk" not in r["tool_calls"][0] and r["monitor"]["alerts"] == []


def test_tester_breaking_a_header_does_not_count(con):
    con.LAB.tester({"server": "devtools", "method": "tools/call", "name": "read_file", "arguments": {"path": "../secrets/api-key.txt"}, "break": "origin"}, {})
    assert not con.progress.load()


def test_flag_needs_all_three_and_lives_in_one_script(con):
    tool(con, "read_file", path="../secrets/api-key.txt")
    tool(con, "fetch_url", url=f"http://127.0.0.1:{con.INTERNAL_PORT}/credentials")
    assert con.LAB.state({}, {})["flag"] is None
    if os.name == "posix":
        tool(con, "check_host", host="x; cat " + str(con.SRV / "secrets" / "db-password.txt"))
        st = con.LAB.state({}, {})
        assert st["flag"] == "BDAI{c2-ch03-the-tool-trusted-its-arguments}" and st["missions"]["complete"]
    holders = [str(p.relative_to(REPO)) for p in REPO.rglob("*.py") if "tests" not in p.parts and ".scratch" not in p.parts
               and "BDAI{c2-ch03-the-tool-trusted-its-arguments}" in p.read_text(encoding="utf-8")]
    assert holders == ["labs/c2-mcp/ch03-server-flaws/servers-lab/app/progress.py"]
