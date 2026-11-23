"""Which of the three missions you have completed, and the evidence. The web console records a mission the moment the
behaviour proves it, so there is nothing to type in.

    python /lab/app/progress.py        # print your progress

Missions: "scan" (you scanned the vulnerable server project), "block" (the pipeline gate stopped the build), "ship" (the fixed
project passed the gate at the strictest setting).
"""
import progresskit

FLAG = "BDAI{c2-ch07-the-pipeline-said-no-then-yes}"
MISSIONS = ("scan", "block", "ship")
_store = progresskit.Store(MISSIONS)
load, mark, is_complete = _store.load, _store.mark, _store.is_complete

if __name__ == "__main__":
    progresskit.cli(_store, FLAG)
