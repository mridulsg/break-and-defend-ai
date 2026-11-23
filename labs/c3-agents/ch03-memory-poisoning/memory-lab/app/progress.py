"""Which of the three missions you have completed, and the evidence. The web console records a mission the moment the
behaviour proves it, so there is nothing to type in.

    python /lab/app/progress.py        # print your progress

Missions: "baseline" (a planted memory fired in a later session), "tradeoff" (you stopped every attack by also breaking useful
memory), "hardened" (every attack stopped, and useful memory still works).
"""
import progresskit

FLAG = "BDAI{c3-ch03-the-memory-was-the-attack}"
MISSIONS = ("baseline", "tradeoff", "hardened")
_store = progresskit.Store(MISSIONS)
load, mark, is_complete = _store.load, _store.mark, _store.is_complete

if __name__ == "__main__":
    progresskit.cli(_store, FLAG)
