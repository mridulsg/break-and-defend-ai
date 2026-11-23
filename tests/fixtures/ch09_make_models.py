"""Generates the Chapter 9 sample model files. The checked-in files must equal this output (a unit test checks).

    python tests/fixtures/ch09_make_models.py

sentiment-v1.pkl          a clean model: a pickled dictionary of numbers. It needs no imports to load.
sentiment-community.pkl   looks the same, but the pickle also tells the loader to import a function and call it first. The function
                          is posix.mkdir and it only makes an empty folder in /tmp, so this lab can show code running at load time
                          harmlessly. The bytes are written by hand so they are the same on every operating system.
sentiment-v1.json         the same weights in a plain data format that cannot contain code.

Nothing here is malware. A real attack uses the identical mechanism with a different function.
"""
import json
import pathlib
import pickle
import struct

MODELS = pathlib.Path(__file__).resolve().parents[2] / "labs" / "c1-llm" / "ch09-ai-supply-chain" / "supply-lab" / "models"
MARKER = "/tmp/bdai-proof-of-code-execution"

WEIGHTS = {"model": "acme-sentiment", "version": "1.0", "bias": -0.12,
           "weights": {"great": 1.4, "love": 1.1, "warm": 0.7, "sturdy": 0.9, "broken": -1.6, "leaks": -1.3, "late": -0.8, "refund": -0.6}}


def clean() -> bytes:
    return pickle.dumps(WEIGHTS, protocol=2)


def community() -> bytes:
    """The clean pickle with one extra step in front: GLOBAL posix.mkdir, the folder name, REDUCE (call it), POP (drop the result)."""
    path = MARKER.encode()
    call = b"cposix\nmkdir\n" + b"X" + struct.pack("<I", len(path)) + path + b"\x85" + b"R" + b"0"
    return b"\x80\x02" + call + clean()[2:]


def write() -> None:
    MODELS.mkdir(parents=True, exist_ok=True)
    (MODELS / "sentiment-v1.pkl").write_bytes(clean())
    (MODELS / "sentiment-community.pkl").write_bytes(community())
    (MODELS / "sentiment-v1.json").write_text(json.dumps(WEIGHTS, indent=1, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    write()
    print("written to", MODELS)
