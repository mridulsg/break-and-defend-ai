"""Acme's two internal MCP servers, as the Course 2 labs share them.

  notes     a read-only knowledge base for engineers: list_notes, read_note
  tickets   Acme's issue tracker:                      list_tickets, get_ticket, add_comment (this one WRITES)

Everything here is made up. Each lab starts these as they are, or builds on them (a poisoned description, a missing check).
"""
import threading

import mcpmini

NOTES = {
    "onboarding": ("New engineer onboarding", "Welcome to Acme. Day one: get your laptop, join the #eng channel, read the release checklist. "
                   "Your buddy will pair with you on your first ticket. Ask questions early."),
    "oncall-runbook": ("On-call runbook", "If the orders service is slow: check the dashboard, then restart the worker pool. "
                       "If the database is full, page the data team. Always write what you did in the ticket."),
    "release-checklist": ("Release checklist", "1. All tests green. 2. Changelog updated. 3. A second engineer approved the change. "
                          "4. Deploy to staging and wait ten minutes. 5. Deploy to production on a weekday morning."),
    "vendor-contacts": ("Vendor contacts", "Cloud provider support: open a case in the portal. Payment provider: use the partner line on the vendor page."),
}

TICKETS = {
    "T-101": {"title": "Orders service slow after deploy", "status": "open", "owner": "sam", "body": "Latency doubled after Tuesday's release. Rollback not tried yet."},
    "T-102": {"title": "Update the returns page copy", "status": "open", "owner": "maria", "body": "Marketing wants the 30-day return window on the first line."},
    "T-103": {"title": "Rotate the warehouse API key", "status": "done", "owner": "jonas", "body": "Rotated on Monday. Old key revoked."},
}


class AcmeTickets:
    """The ticket data and the comments people (or assistants) have added. Comments are the lab's evidence of a write."""

    def __init__(self):
        self.lock = threading.Lock()
        self.reset()

    def reset(self):
        with self.lock:
            self.tickets = {k: dict(v) for k, v in TICKETS.items()}
            self.comments: list[dict] = []


def build_notes(name: str = "notes") -> mcpmini.McpServer:
    s = mcpmini.McpServer(name, instructions="Acme's engineering knowledge base. Read-only.")

    @s.tool("list_notes", "List the ids and titles of all notes.")
    def list_notes(args):
        return "\n".join(f"{k}: {v[0]}" for k, v in NOTES.items())

    @s.tool("read_note", "Read one note by its id.", {"type": "object", "properties": {"id": {"type": "string", "description": "The note id, e.g. onboarding"}}, "required": ["id"], "additionalProperties": False})
    def read_note(args):
        note = NOTES.get(args["id"])
        if note is None:
            raise KeyError(f"no note called {args['id']!r}")
        return f"# {note[0]}\n\n{note[1]}"

    return s


def build_tickets(data: AcmeTickets, name: str = "tickets") -> mcpmini.McpServer:
    s = mcpmini.McpServer(name, instructions="Acme's issue tracker.")

    @s.tool("list_tickets", "List all tickets with their status.")
    def list_tickets(args):
        return "\n".join(f"{k}: {t['title']} [{t['status']}]" for k, t in data.tickets.items())

    @s.tool("get_ticket", "Read one ticket by its id.", {"type": "object", "properties": {"id": {"type": "string", "description": "The ticket id, e.g. T-101"}}, "required": ["id"], "additionalProperties": False})
    def get_ticket(args):
        t = data.tickets.get(args["id"])
        if t is None:
            raise KeyError(f"no ticket {args['id']!r}")
        return f"{args['id']}: {t['title']}\nStatus: {t['status']}\nOwner: {t['owner']}\n\n{t['body']}"

    @s.tool("add_comment", "Add a comment to a ticket. This changes the ticket.",
            {"type": "object", "properties": {"id": {"type": "string"}, "text": {"type": "string"}}, "required": ["id", "text"], "additionalProperties": False})
    def add_comment(args):
        if args["id"] not in data.tickets:
            raise KeyError(f"no ticket {args['id']!r}")
        with data.lock:
            data.comments.append({"id": args["id"], "text": args["text"]})
        return f"Comment added to {args['id']}."

    return s
