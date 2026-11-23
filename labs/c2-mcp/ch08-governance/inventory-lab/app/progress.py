"""Which of the three missions you have completed, and the evidence. The web console records a mission the moment the
behaviour proves it, so there is nothing to type in.

    python /lab/app/progress.py        # print your progress

Missions: "inventory" (you scanned every developer's config), "decide" (every unapproved or drifted server has a decision with an
owner and a reason), "clean" (a rescan shows nothing undecided).
"""
import progresskit

FLAG = "BDAI{c2-ch08-nothing-runs-that-nobody-owns}"
MISSIONS = ("inventory", "decide", "clean")
_store = progresskit.Store(MISSIONS)
load, mark, is_complete = _store.load, _store.mark, _store.is_complete

if __name__ == "__main__":
    progresskit.cli(_store, FLAG)
