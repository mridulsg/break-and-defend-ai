"""The two ways to load a model file.

  unsafe_load  pickle.load: the standard way, and the way that runs whatever the file says. Many tools still do this for .pkl,
               .bin and .pt files. Read it: it is one line, and it trusts the file completely.
  safe_load    refuses any file that wants to import anything, and reads the plain-data format (JSON) with a normal parser.

The console runs these inside a container with no network, a read-only filesystem and a temporary /tmp, and the sample
"dangerous" file only makes an empty folder in /tmp. That folder is the proof that code ran.
"""
import io
import json
import os
import pathlib
import pickle
import shutil

MODELS = pathlib.Path(os.environ.get("BDAI_LAB_DIR", "/lab")) / "models"
MARKER = pathlib.Path("/tmp/bdai-proof-of-code-execution")
NAMES = ("sentiment-v1.pkl", "sentiment-community.pkl", "sentiment-v1.json")


def path_for(name: str) -> pathlib.Path:
    if name not in NAMES:
        raise ValueError("Pick one of the sample model files.")
    return MODELS / name


def reset_marker() -> None:
    shutil.rmtree(MARKER, ignore_errors=True)
    if MARKER.is_dir() or MARKER.exists():
        MARKER.unlink(missing_ok=True)


def unsafe_load(data: bytes):
    """The risky way: whatever the file says to do, happens."""
    return pickle.loads(data)  # noqa: S301 (this is the point of the lab)


class _NoImports(pickle.Unpickler):
    def find_class(self, module, name):
        raise pickle.UnpicklingError(f"this file asks to import {module}.{name}, so it was not loaded")


def safe_load(data: bytes, name: str):
    """The safe way: plain data only."""
    if name.endswith(".json"):
        weights = json.loads(data.decode("utf-8"))
        if not isinstance(weights, dict) or "weights" not in weights:
            raise ValueError("That is not a model file.")
        return weights
    return _NoImports(io.BytesIO(data)).load()


def summary(weights) -> str:
    if isinstance(weights, dict) and "model" in weights:
        return f"{weights['model']} v{weights.get('version', '?')}, {len(weights.get('weights', {}))} weights"
    return "(loaded something that is not a model)"
