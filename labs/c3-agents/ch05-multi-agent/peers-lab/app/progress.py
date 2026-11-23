"""Which of the three missions you have completed, and the evidence. The web console records a mission the moment the
behaviour proves it, so there is nothing to type in.

    python /lab/app/progress.py        # print your progress

Missions: "baseline" (all three attacks on agent-to-agent trust worked), "overreach" (you stopped every attack by refusing all work),
"hardened" (every attack stopped and both real tasks work).
"""
import progresskit

FLAG = "BDAI{c3-ch05-trust-is-not-transitive}"
MISSIONS = ("baseline", "overreach", "hardened")
_store = progresskit.Store(MISSIONS)
load, mark, is_complete = _store.load, _store.mark, _store.is_complete

if __name__ == "__main__":
    progresskit.cli(_store, FLAG)
