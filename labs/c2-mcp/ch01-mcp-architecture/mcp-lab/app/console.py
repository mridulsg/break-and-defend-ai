"""The Acme engineering assistant console for Lab 1.1: an AI assistant (the host) connected to two MCP servers.

You can talk to the assistant, read what each server offers, and send raw MCP requests yourself with the Tool tester.
Run by the `console` service (see compose.yaml); open http://127.0.0.1:8300.
"""
import os
import sys

sys.path.insert(0, os.environ.get("BDAI_MCP_DIR", "/mcp"))

import acme  # noqa: E402
import labkit  # noqa: E402
import progress  # noqa: E402

DATA = acme.AcmeTickets()
SERVERS = {"notes": ("Acme notes", acme.build_notes()), "tickets": ("Acme tickets", acme.build_tickets(DATA))}


def on_tester(result: dict, brk: str) -> None:
    if brk == "origin" and result["status"] == 403:
        progress.mark("origin", "A request with a foreign Origin header was refused with HTTP 403. That check is the defence against DNS rebinding.")
    elif not brk and result["status"] == 200 and result["method"] == "tools/list":
        progress.mark("list", f"You sent tools/list to the {result['server']} server and read its tools.")
    elif not brk and result["status"] == 200 and result["method"] == "tools/call" and not result["error"]:
        progress.mark("call", f"You called {result['tool']} on the {result['server']} server yourself.")


def watch(result: dict, question: str) -> dict:
    calls = result["tool_calls"]
    if calls:
        c = calls[0]
        progress.mark("agent", f"The assistant chose {c['server']}.{c['tool']} and the host called it: tools/call over MCP.")
    names = ", ".join(f"{c['server']}.{c['tool']}" for c in calls) or "None"
    return {"alerts": [], "rows": [{"label": "Tools the assistant called", "value": names, "bad": False},
                                   {"label": "Comments added to tickets", "value": str(len(DATA.comments)), "bad": False}]}


LAB = labkit.Lab(
    product="Acme Engineering Assistant", lab="Lab 1.1: Explore MCP and map its trust boundaries",
    intro="You are an Acme engineer. The assistant is connected to two MCP servers, the notes and the tickets. Ask it about a ticket or a note.",
    suggestions=["What is ticket T-101 about?", "What does the note release-checklist say?", "List the open tickets"],
    missions_lede="Four things to do with the protocol. Each is detected automatically.",
    missions=[
        {"id": "list", "kind": "auto", "title": "Ask a server what tools it has",
         "text": "On the Tool tester page, choose a server and the method tools/list, and press Send. Read the raw request and response."},
        {"id": "call", "kind": "auto", "title": "Call a tool yourself",
         "text": "On the Tool tester page choose tools/call, name a tool (read_note or get_ticket) and give its arguments as JSON. The MCP servers page lists the names and what each needs.",
         "hint": "The arguments for read_note are {\"id\": \"onboarding\"}. For get_ticket they are {\"id\": \"T-101\"}."},
        {"id": "origin", "kind": "auto", "title": "Get a request refused for its Origin",
         "text": "On the Tool tester page, choose Break it: Add a foreign Origin header, and send. The server must refuse it. Then try the other two ways to break a request and read the errors."},
        {"id": "agent", "kind": "auto", "title": "Make the assistant use a tool",
         "text": "On the chat page, ask something that needs a tool. Open Behind the scenes to see which tool it chose and what the host sent."},
    ],
    flag_next="Next: Chapter 2 looks at what happens when a server is not what it seems.",
    progress=progress, servers=SERVERS, watch=watch, on_tester=on_tester,
    extra_state=lambda: {"comments": list(DATA.comments)},
)

if __name__ == "__main__":
    LAB.run()
