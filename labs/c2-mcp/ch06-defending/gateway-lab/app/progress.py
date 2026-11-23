"""Which of the three missions you have completed, and the evidence. The web console records a mission the moment the
behaviour proves it, so there is nothing to type in.

    python /lab/app/progress.py        # print your progress

Missions: "baseline" (you ran the attack suite with no gateway controls and saw every attack work), "overblock" (you found a policy
that stopped every attack by also stopping real work), "hardened" (every attack stopped and every real task still works).
"""
import progresskit

FLAG = "BDAI{c2-ch06-stopped-the-attacks-kept-the-work}"
MISSIONS = ("baseline", "overblock", "hardened")
_store = progresskit.Store(MISSIONS)
load, mark, is_complete = _store.load, _store.mark, _store.is_complete

if __name__ == "__main__":
    progresskit.cli(_store, FLAG)
