"""Checks your trust classification for Lab 1.1 and prints the flag when it is right.

Edit answers.json, then run this. For every wrong or unanswered item it prints a hint,
not the answer.
"""
import json
import os
import pathlib
import sys

FLAG = "BDAI{c1-ch01-trust-boundaries-mapped}"
CHOICES = {"trusted", "semi_trusted", "untrusted"}

EXPECTED = {
    "system_prompt": "trusted",
    "handbook_docs": "semi_trusted",
    "inbox_notes": "untrusted",
    "web_pages": "untrusted",
    "user_question": "untrusted",
    "embedding_model": "semi_trusted",
    "model_output": "untrusted",
}

HINTS = {
    "system_prompt": "Who writes it, and can an outsider change it? Think about who controls the source file.",
    "handbook_docs": "Staff write these, but what could change them without a human noticing (a pipeline, a shared drive, a compromised account)?",
    "inbox_notes": "Look at the folder name and think about who produced the text.",
    "web_pages": "Where did this content originate, and does Acme control that origin?",
    "user_question": "The person typing is an arbitrary member of the public.",
    "embedding_model": "Acme did not train it and cannot inspect it. What does that make it?",
    "model_output": "The answer goes to a person or another system. Is it something you can assume is safe to act on?",
}

path = pathlib.Path(os.environ.get("BDAI_ANSWERS", "/lab/answers.json"))
try:
    answers = json.loads(path.read_text(encoding="utf-8"))
except (OSError, ValueError) as exc:
    sys.exit(f"Could not read answers.json: {exc}")
if not isinstance(answers, dict):
    sys.exit('answers.json must be a JSON object like {"system_prompt": "trusted", ...}')

wrong = 0
for key, expected in EXPECTED.items():
    given = answers.get(key, "?")
    if given not in CHOICES:
        print(f"[ -- ] {key}: not answered (use one of: {', '.join(sorted(CHOICES))})")
        print(f"         hint: {HINTS[key]}")
        wrong += 1
    elif given != expected:
        print(f"[FAIL] {key}: '{given}' is not right")
        print(f"         hint: {HINTS[key]}")
        wrong += 1
    else:
        print(f"[PASS] {key}: {given}")

print()
if wrong:
    print(f"{wrong} item(s) to fix. Edit answers.json and run the check again.")
    sys.exit(1)
print(f"All seven components classified correctly. Flag: {FLAG}")
