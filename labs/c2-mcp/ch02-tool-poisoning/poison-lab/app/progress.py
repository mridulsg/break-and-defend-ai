"""Which of the three missions you have completed, and the evidence. The web console records a mission the moment the
behaviour proves it, so there is nothing to type in.

    python /lab/app/progress.py        # print your progress

Missions: "poison" (a tool's description made the assistant send internal ticket text to a server outside Acme), "shadow" (a tool the
engineer never used changed how a different server's tool was called), "rugpull" (a description that was clean when the engineer
approved the server turned hostile after an update).
"""
import progresskit

FLAG = "BDAI{c2-ch02-the-description-was-the-attack}"
MISSIONS = ("poison", "shadow", "rugpull")
_store = progresskit.Store(MISSIONS)
load, mark, is_complete = _store.load, _store.mark, _store.is_complete

if __name__ == "__main__":
    progresskit.cli(_store, FLAG)
