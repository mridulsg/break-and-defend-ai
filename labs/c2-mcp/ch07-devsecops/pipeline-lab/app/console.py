"""The Acme console for Labs 7.1 and 7.2: a security gate in the build pipeline of an MCP server.

Two sample projects of the same server, `vulnerable` and `fixed`, each with a server file, a dependency list and a container file.
You run the pipeline on one of them: the scanner reads the files, and the gate decides whether the build may ship, at a severity
threshold you choose. Nothing in the projects is ever run. Run by the `console` service; open http://127.0.0.1:8300.
"""
import os
import pathlib
import sys

sys.path.insert(0, os.environ.get("BDAI_MCP_DIR", "/mcp"))

import labkit  # noqa: E402
import mcpscan  # noqa: E402
import progress  # noqa: E402

PROJECTS = pathlib.Path(os.environ.get("BDAI_LAB_DIR", "/lab")) / "projects"
NAMES = ("vulnerable", "fixed")
FILES = ("server.py.sample", "deps.txt", "Dockerfile.sample")


def project(body, _q) -> dict:
    name = body.get("name")
    if name not in NAMES:
        raise labkit.web.ApiError(400, "Choose vulnerable or fixed.")
    return {"name": name, "files": [{"name": f, "text": (PROJECTS / name / f).read_text(encoding="utf-8")} for f in FILES]}


def run(body, _q) -> dict:
    name, threshold = body.get("name"), body.get("threshold", "medium")
    if name not in NAMES:
        raise labkit.web.ApiError(400, "Choose vulnerable or fixed.")
    if threshold not in mcpscan.SEVERITY:
        raise labkit.web.ApiError(400, "Choose high, medium or low.")
    findings = mcpscan.scan_project(PROJECTS / name)
    verdict = mcpscan.gate(findings, threshold)
    if name == "vulnerable":
        if len(findings) >= 8:
            progress.mark("scan", f"The scanner found {len(findings)} problems in the vulnerable server project.")
        if not verdict["passed"]:
            progress.mark("block", f"The gate stopped the build at threshold {threshold}: {verdict['blockers']} blocking findings.")
    elif verdict["passed"] and threshold == "low":
        progress.mark("ship", "The fixed project passed the gate at the strictest setting (low): nothing to report.")
    return {"name": name, "findings": findings, "verdict": verdict, "state": LAB.state({}, {})}


LAB = labkit.Lab(
    product="Acme MCP Pipeline Console", lab="Labs 7.1 and 7.2: Security gates for an MCP server",
    intro="", suggestions=[], views=["pipeline", "missions"],
    missions_lede="A server is about to ship. The pipeline decides. Each mission is detected when you run it.",
    missions=[
        {"id": "scan", "kind": "auto", "title": "Scan the vulnerable server project",
         "text": "On the Pipeline page, choose the vulnerable project and run the pipeline. Read what the scanner found, and the line it points at."},
        {"id": "block", "kind": "auto", "title": "Let the gate stop the build",
         "text": "Run the vulnerable project and read the verdict. The gate fails the build when a finding is at or above the threshold you choose."},
        {"id": "ship", "kind": "auto", "title": "Ship the fixed project through the strictest gate",
         "text": "Run the fixed project at the threshold low. Compare the two projects file by file to see what changed."},
    ],
    flag_next="Next: Lab 7.2 shows the pipeline step and what a scanner cannot catch.",
    progress=progress, servers={},
)

if __name__ == "__main__":
    LAB.run({("POST", "/api/project"): project, ("POST", "/api/pipeline"): run})
