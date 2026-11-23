"""Which of the four missions you have completed, and the evidence. The web console records a mission the moment the
behaviour proves it, so there is nothing to type in.

    python /lab/app/progress.py        # print your progress

Missions: "baseline" (a hijacked agent deleted a ticket, paid 5000 and looped), "friction" (you found the control that stops every
attack by making every payment wait for a person), "hardened" (every attack stopped and the real payment still goes through on its own).
"""
import progresskit

FLAG = "BDAI{c3-ch04-small-powers-small-damage}"
MISSIONS = ("baseline", "friction", "hardened")
_store = progresskit.Store(MISSIONS)
load, mark, is_complete = _store.load, _store.mark, _store.is_complete

if __name__ == "__main__":
    progresskit.cli(_store, FLAG)
