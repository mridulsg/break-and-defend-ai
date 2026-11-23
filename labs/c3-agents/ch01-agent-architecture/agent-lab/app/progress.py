"""Missions: "run" (you ran the tasks), "obey" (you saw an agent follow an instruction it found in a web page), "stop" (you turned on a platform
control and the same page no longer worked).

    python /lab/app/progress.py        # print your progress
"""
import progresskit

FLAG = "BDAI{c3-ch01-the-agent-obeyed-the-page}"
MISSIONS = ('run', 'obey', 'stop')
_store = progresskit.Store(MISSIONS)
load, mark, is_complete = _store.load, _store.mark, _store.is_complete

if __name__ == "__main__":
    progresskit.cli(_store, FLAG)
