"""Reference solution for Lab 3.2. NOT shipped to learners: tests use it to prove the lab can be passed.

Architectural defences: untrusted sources are never retrieved, and the secret never enters the prompt.
"""


def allowed_sources() -> set[str]:
    return {"corpus"}


def system_prompt(base: str, secret: str) -> str:
    return base


def wrap_context(chunks: list[dict]) -> str:
    return "\n\n".join(f"[{c['file']}]\n{c['text']}" for c in chunks)


def guard_output(answer: str, chunks: list[dict]) -> str:
    return answer
