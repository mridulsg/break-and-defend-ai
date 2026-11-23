"""Which of the three missions you have completed, and the evidence. The web console records a mission the moment the
behaviour proves it, so there is nothing to type in.

    python /lab/app/progress.py        # print your progress

Missions: "audience" (the tickets server accepted a token issued for a different server), "scope" (a read-only token wrote to a
ticket), "forged" (the server accepted a token nobody signed).
"""
import progresskit

FLAG = "BDAI{c2-ch04-the-token-said-yes-to-everything}"
MISSIONS = ("audience", "scope", "forged")
_store = progresskit.Store(MISSIONS)
load, mark, is_complete = _store.load, _store.mark, _store.is_complete

if __name__ == "__main__":
    progresskit.cli(_store, FLAG)
