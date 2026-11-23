"""Which of the five missions you have completed, and the evidence. The web console records a mission the moment the behaviour
proves it, so there is nothing to type in.

    python /lab/app/progress.py        # print your progress

Missions: "traversal" (read_file returned a secret), "scope" (a read-only token changed a ticket), "poison" (you read the
description of the third-party tool that gives orders to the model), "register" (you wrote the risk register), "retest" (with the
fixes on, the traversal was refused).
"""
import progresskit

FLAG = "BDAI{c2-ch09-found-reported-fixed-retested}"
MISSIONS = ("traversal", "scope", "poison", "register", "retest")
_store = progresskit.Store(MISSIONS)
load, mark, is_complete = _store.load, _store.mark, _store.is_complete

if __name__ == "__main__":
    progresskit.cli(_store, FLAG)
