"""Which of the four missions you have completed, and the evidence. The web console records a mission the moment
the behaviour proves it, so there is nothing to type in.

    python /lab/app/progress.py        # print your progress

Missions: "list" (you sent tools/list yourself), "call" (you called a tool yourself), "origin" (a server refused a request
from a foreign Origin), "agent" (the assistant chose a tool and the host called it).
"""
import progresskit

FLAG = "BDAI{c2-ch01-i-have-read-the-protocol}"
MISSIONS = ("list", "call", "origin", "agent")
_store = progresskit.Store(MISSIONS)
load, mark, is_complete = _store.load, _store.mark, _store.is_complete

if __name__ == "__main__":
    progresskit.cli(_store, FLAG)
