"""Which of the three missions you have completed, and the evidence. The web console records a mission the moment the
behaviour proves it, so there is nothing to type in.

    python /lab/app/progress.py        # print your progress

Missions: "found" (you ran the probes against the unprotected agent platform and all three problems showed), "register" (you wrote
the risk register), "retest" (with controls chosen, every probe was stopped and both real tasks still work).
"""
import progresskit

FLAG = "BDAI{c3-ch06-assessed-reported-fixed-retested}"
MISSIONS = ("found", "register", "retest")
_store = progresskit.Store(MISSIONS)
load, mark, is_complete = _store.load, _store.mark, _store.is_complete

if __name__ == "__main__":
    progresskit.cli(_store, FLAG)
