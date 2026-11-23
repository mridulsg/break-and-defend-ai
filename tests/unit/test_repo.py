"""Static checks on the whole repository: security rules, pinning, docs and config consistency."""
import json
import os
import re
import stat
import subprocess

import pytest
import yaml

from conftest import REPO

SKIP_DIRS = {".git", "__pycache__", "node_modules", "site"}
TEXT_SUFFIXES = {".md", ".py", ".sh", ".yaml", ".yml", ".json", ".txt", ".in", ".toml", ".cfg"}


def all_files():
    for root, dirs, files in os.walk(REPO):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for name in files:
            yield pathlib_path(root, name)


def pathlib_path(root, name):
    import pathlib
    return pathlib.Path(root) / name


def text_files():
    for p in all_files():
        if p.name in {".env"}:
            continue
        if p.suffix in TEXT_SUFFIXES or p.name in {"Dockerfile", ".gitignore", ".gitattributes", ".env.example", "LICENSE"}:
            yield p


def rel(p):
    return str(p.relative_to(REPO)).replace("\\", "/")


COMPOSE_FILES = sorted(p for p in all_files() if p.name == "compose.yaml")
DOCKERFILES = sorted(p for p in all_files() if p.name == "Dockerfile")
REQUIREMENTS = sorted(p for p in all_files() if p.name == "requirements.txt")


# ---------- hygiene ----------

def test_no_windows_line_endings():
    bad = [rel(p) for p in text_files() if b"\r" in p.read_bytes()]
    assert not bad, f"CRLF found (breaks shell scripts and compose): {bad}"


def test_json_files_are_valid():
    for p in all_files():
        if p.suffix == ".json":
            json.loads(p.read_text(encoding="utf-8"))


@pytest.mark.parametrize("script", sorted(p for p in all_files() if p.suffix == ".sh"), ids=rel)
def test_shell_scripts(script):
    text = script.read_text(encoding="utf-8")
    assert text.startswith("#!/usr/bin/env bash"), "missing shebang"
    assert "set -" in text and "pipefail" in text, "scripts must fail loudly (set -euo pipefail)"
    assert os.access(script, os.X_OK), "script is not executable (chmod +x)"
    assert subprocess.run(["bash", "-n", str(script)], capture_output=True).returncode == 0, "syntax error"


# ---------- secrets ----------

def test_no_provider_or_gateway_keys_anywhere_in_the_repo():
    pattern = re.compile(r"sk-or-v1-[A-Za-z0-9]{16,}|sk-bdai-local-[a-f0-9]{16,}|sk-ant-[A-Za-z0-9_-]{20,}")
    leaks = [rel(p) for p in all_files() if p.name != ".env" and pattern.search(p.read_text(errors="ignore"))]
    assert not leaks, f"secret-looking values in: {leaks}"


def test_env_example_holds_no_values_for_secrets():
    text = (REPO / ".env.example").read_text()
    assert re.search(r"^OPENROUTER_API_KEY=$", text, re.M)
    assert re.search(r"^BDAI_GATEWAY_KEY=$", text, re.M)


def test_gitignore_protects_env_files():
    lines = (REPO / ".gitignore").read_text().splitlines()
    assert ".env" in lines and "!.env.example" in lines


def test_only_the_core_gateway_may_reference_the_provider_key():
    for p in all_files():
        if p.suffix in {".yaml", ".yml", ".py", ".sh"} and "OPENROUTER_API_KEY" in p.read_text(errors="ignore"):
            allowed = {"shared/core/compose.yaml", "shared/core/gateway/app.py", "shared/scripts/setup.sh",
                       "shared/scripts/preflight.sh", "shared/scripts/start.sh"}   # start.sh only checks that the key is set
            assert rel(p) in allowed or rel(p).startswith("tests/"), f"{rel(p)} must not touch the provider key"


# ---------- compose hardening ----------

def services(path):
    data = yaml.safe_load(path.read_text())
    return data.get("services", {}), data


@pytest.mark.parametrize("compose", COMPOSE_FILES, ids=rel)
def test_every_service_is_hardened(compose):
    svcs, _ = services(compose)
    assert svcs, "compose file defines no services"
    for name, s in svcs.items():
        who = f"{rel(compose)}:{name}"
        assert s.get("read_only") is True, f"{who}: root filesystem must be read-only"
        assert "ALL" in s.get("cap_drop", []), f"{who}: must drop all capabilities"
        assert "no-new-privileges:true" in s.get("security_opt", []), f"{who}: needs no-new-privileges"
        assert s.get("mem_limit"), f"{who}: needs a memory limit"
        assert s.get("cpus"), f"{who}: needs a CPU limit"
        assert not s.get("privileged"), f"{who}: privileged is forbidden"
        assert s.get("network_mode") != "host", f"{who}: host networking is forbidden"
        assert not any("docker.sock" in str(v) for v in s.get("volumes", [])), f"{who}: docker socket mount"
        assert not any(str(k).upper().startswith("PRIVILEGED") for k in s), who


@pytest.mark.parametrize("compose", [c for c in COMPOSE_FILES if "labs/" in rel(c) or "benchmarks/" in rel(c)], ids=rel)
def test_lab_services_are_isolated_and_labelled(compose):
    svcs, data = services(compose)
    for name, s in svcs.items():
        who = f"{rel(compose)}:{name}"
        no_network = s.get("network_mode") == "none" and not s.get("networks")     # a lab with no network at all is stricter than the internal one
        assert s.get("networks") == ["bdai-llm"] or no_network, f"{who}: labs may only join the internal bdai-llm network, or have no network"
        assert "ports" not in s, f"{who}: labs must not publish ports"
        assert (s.get("labels") or {}).get("bdai.course"), f"{who}: needs the bdai.course label for cleanup"
    if any(s.get("networks") for s in svcs.values()):
        assert data["networks"]["bdai-llm"].get("external") is True
    for vol in (data.get("volumes") or {}).values():
        assert (vol.get("labels") or {}).get("bdai.course"), f"{rel(compose)}: volumes need the bdai.course label"


@pytest.mark.parametrize("compose", [c for c in COMPOSE_FILES if "labs/" in rel(c) or "benchmarks/" in rel(c)], ids=rel)
def test_lab_containers_get_only_the_local_gateway_key(compose):
    svcs, _ = services(compose)
    for name, s in svcs.items():
        env = s.get("environment") or {}
        assert not any("OPENROUTER" in k for k in env), f"{rel(compose)}:{name} gets the provider key"
        # a lab that never calls a model (for example the Chapter 9 supply-chain lab) gets no key at all
        assert "OPENAI_API_KEY" not in env or "BDAI_GATEWAY_KEY" in env["OPENAI_API_KEY"], "labs authenticate with the gateway key"


def test_published_ports_bind_to_localhost_only():
    for compose in COMPOSE_FILES:
        for name, s in services(compose)[0].items():
            for port in s.get("ports", []):
                assert str(port).startswith("127.0.0.1:"), f"{rel(compose)}:{name} exposes {port} beyond localhost"


def test_lab_network_is_internal_and_only_egress_is_not():
    _, core = services(REPO / "shared" / "core" / "compose.yaml")
    assert core["networks"]["bdai-llm"]["internal"] is True
    assert not core["networks"]["bdai-egress"].get("internal")
    gateway_nets = core["services"]["gateway"]["networks"]
    assert set(gateway_nets) == {"bdai-llm", "bdai-egress"}


def test_long_running_services_restart_after_wsl_idles():
    for path in (REPO / "shared" / "core" / "compose.yaml", REPO / "shared" / "docs-site" / "compose.yaml"):
        for name, s in services(path)[0].items():
            assert s.get("restart") == "unless-stopped", f"{rel(path)}:{name} will stay down after WSL idles"


# ---------- images and dependencies ----------

@pytest.mark.parametrize("dockerfile", DOCKERFILES, ids=rel)
def test_dockerfile_is_pinned_and_safe(dockerfile):
    text = dockerfile.read_text()
    froms = re.findall(r"^FROM\s+(\S+)", text, re.M)
    assert froms and all("@sha256:" in f for f in froms), "base image must be pinned by digest"
    assert re.search(r"^USER\s+(?!root)\S+", text, re.M), "container must not run as root"
    for line in re.findall(r"^RUN .*pip install.*$", text, re.M):
        assert "--require-hashes" in line, f"pip install without hash checking: {line}"


@pytest.mark.parametrize("req", REQUIREMENTS, ids=rel)
def test_requirements_are_fully_pinned_with_hashes(req):
    blocks = re.split(r"\n(?=\S)", req.read_text())
    pinned = [b for b in blocks if re.match(r"[A-Za-z0-9_.\-\[\]]+==", b)]
    assert pinned, "no pinned packages"
    for b in pinned:
        assert "--hash=sha256:" in b, f"unhashed dependency: {b.splitlines()[0]}"


def test_every_requirements_txt_has_a_source_file():
    for req in REQUIREMENTS:
        assert (req.parent / "requirements.in").exists(), f"{rel(req)} has no requirements.in to regenerate from"


def test_all_dockerfiles_share_one_base_digest():
    digests = {re.search(r"@(sha256:[0-9a-f]{64})", d.read_text()).group(1) for d in DOCKERFILES}
    assert len(digests) == 1, f"different base digests defeat layer sharing and complicate updates: {digests}"


# ---------- model table ----------

def test_models_json_integrity():
    models = json.loads((REPO / "shared/core/gateway/models.json").read_text())
    for alias, m in models.items():
        assert m["provider"] in {"openrouter", "ollama"}, alias
        assert m["model"] and isinstance(m["price_in"], (int, float)) and isinstance(m["price_out"], (int, float)), alias
        assert m.get("kind", "chat") in {"chat", "embedding"}, alias
        assert isinstance(m.get("defaults", {}), dict), alias
        if m["provider"] == "ollama":
            assert m["price_in"] == 0 and m["price_out"] == 0, f"{alias}: local models are free"
        if alias.startswith("bdai-"):
            assert not m.get("hidden"), f"{alias} is a public alias and must not be hidden"
        else:
            assert m.get("hidden"), f"{alias}: non-public aliases must be hidden"


def test_docs_prices_match_the_model_table():
    models = json.loads((REPO / "shared/core/gateway/models.json").read_text())
    text = (REPO / "docs/c1/ch00-orientation.md").read_text()
    for alias in ("bdai-default", "bdai-strong"):
        m = models[alias]
        assert f"${m['price_in']:.2f} / ${m['price_out']:.2f}" in text, f"Chapter 0 shows a stale price for {alias}"


# ---------- docs ----------

LINK = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")


def md_files():
    return [p for p in all_files() if p.suffix == ".md"]


@pytest.mark.parametrize("md", md_files(), ids=rel)
def test_markdown_relative_links_resolve(md):
    for target in LINK.findall(md.read_text(encoding="utf-8")):
        if re.match(r"(https?:|mailto:|#)", target):
            continue
        path = (md.parent / target.split("#")[0]).resolve()
        assert path.exists(), f"{rel(md)} links to missing {target}"


def test_every_nav_entry_exists_and_every_page_is_in_the_nav():
    cfg = yaml.safe_load((REPO / "mkdocs.yml").read_text())
    listed = set()

    def walk(node):
        if isinstance(node, str) and node.endswith(".md"):
            listed.add(node)
        elif isinstance(node, dict):
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)

    walk(cfg["nav"])
    for page in listed:
        assert (REPO / "docs" / page).exists(), f"nav lists missing page {page}"
    on_disk = {str(p.relative_to(REPO / "docs")).replace("\\", "/") for p in (REPO / "docs").rglob("*.md")}
    assert on_disk == listed, f"pages not in nav: {on_disk - listed}"


def test_paths_and_scripts_mentioned_in_docs_exist():
    for md in md_files():
        text = md.read_text(encoding="utf-8")
        for m in re.findall(r"(?<![\w/.-])((?:\./)?shared/scripts/[\w.-]+\.sh)", text):
            assert (REPO / m.removeprefix("./")).exists(), f"{rel(md)} mentions missing script {m}"
        for m in re.findall(r"(?<![\w/.-])(labs/[\w./-]+?\.(?:yaml|py|json|md))", text):
            assert (REPO / m).exists(), f"{rel(md)} mentions missing file {m}"


# ---------- flags ----------

def lab_flags():
    flags = {}
    for p in all_files():
        if p.suffix == ".py" and "labs/" in rel(p):
            for f in re.findall(r"BDAI\{[^}.]+\}", p.read_text()):
                flags.setdefault(f, []).append(rel(p))
    return flags


def test_flags_are_well_formed_and_unique_per_lab():
    flags = lab_flags()
    assert flags, "no flags found"
    for flag in flags:
        assert re.fullmatch(r"BDAI\{c\d+-ch\d+-[a-z0-9-]+\}", flag), f"badly formed flag {flag}"
    assert all(len(v) == 1 for v in flags.values()), "a flag appears in more than one script"


def test_course_text_never_reveals_a_real_flag():
    for flag in lab_flags():
        for md in md_files():
            assert flag not in md.read_text(encoding="utf-8"), f"{rel(md)} spoils {flag}"
