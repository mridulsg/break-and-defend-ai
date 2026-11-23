"""Missions: "baseline" (all three attacks worked), "tagging" (you saw that marking text as untrusted changed nothing), "overblock" (a policy that stops
every attack and all work), "hardened" (every attack stopped, every task works).

    python /lab/app/progress.py        # print your progress
"""
import progresskit

FLAG = "BDAI{c3-ch02-goal-hijacked-and-held}"
MISSIONS = ('baseline', 'tagging', 'overblock', 'hardened')
_store = progresskit.Store(MISSIONS)
load, mark, is_complete = _store.load, _store.mark, _store.is_complete

if __name__ == "__main__":
    progresskit.cli(_store, FLAG)
