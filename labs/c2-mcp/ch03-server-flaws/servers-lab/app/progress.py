"""Which of the three missions you have completed, and the evidence. The web console records a mission the moment the
behaviour proves it, so there is nothing to type in.

    python /lab/app/progress.py        # print your progress

Missions: "traversal" (read_file handed over a file outside the docs folder), "injection" (check_host ran a command you wrote),
"ssrf" (fetch_url fetched something from an internal service you cannot reach yourself).
"""
import progresskit

FLAG = "BDAI{c2-ch03-the-tool-trusted-its-arguments}"
MISSIONS = ("traversal", "injection", "ssrf")
_store = progresskit.Store(MISSIONS)
load, mark, is_complete = _store.load, _store.mark, _store.is_complete

if __name__ == "__main__":
    progresskit.cli(_store, FLAG)
