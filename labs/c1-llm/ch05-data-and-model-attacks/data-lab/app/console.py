"""The Acme console for Labs 5.1 and 5.2: three AI systems that learn from data, and a way to feed each one bad data.

  * TrailBot reads documents (including customer notes). Poison its knowledge and its answers change.
  * The review moderator is a small model trained on labelled reviews, and customers can flag more. Poison the
    training data and a hidden trigger can switch it off.
  * The reply autocomplete is a small language model trained on past support chats. Ask it the right way and it
    writes out a customer's private details.

Run by the `console` service (see compose.yaml); open http://127.0.0.1:8300. Missions are detected automatically from
what the systems actually do. The "Fixes" switch turns on one protection per system, so you can run an attack twice.
"""
import hashlib
import json
import os
import pathlib
import re
import sys
import threading
import time

sys.path.insert(0, os.environ.get("BDAI_CONSOLE_DIR", "/console"))

import openai  # noqa: E402

import autocomplete  # noqa: E402
import moderator  # noqa: E402
import progress  # noqa: E402
import server  # noqa: E402
import trailbot  # noqa: E402

STATIC = pathlib.Path(os.environ.get("BDAI_CONSOLE_DIR", "/console")) / "static"
FIXES_FILE = trailbot.DATA / "fixes"
MODELS = [
    {"id": "bdai-victim", "label": "Local model (Qwen3 1.7B, free)", "hosted": False},
    {"id": "bdai-default", "label": "Hosted model (Claude Haiku 5.5, about $0.001 a question)", "hosted": True},
]
MAX_QUESTION, MAX_NOTE, MAX_NOTES, MAX_EXAMPLE = 2000, 2000, 10, 300
NOTE_FILE = re.compile(r"^you-(inbox|web)-(\d+)\.md$")
LOCK = threading.RLock()
HANDBOOK_WINDOWS = {30, 60}  # the return windows in the staff handbook, in days
RETURN_WORDS = ("return", "refund", "exchange", "send back")
_cache: dict = {}


def fixes_on() -> bool:
    return FIXES_FILE.exists() and FIXES_FILE.read_text().strip() == "on"


def ensure_ready() -> None:
    with LOCK:
        trailbot.DATA.mkdir(parents=True, exist_ok=True)
        trailbot.NOTES.mkdir(parents=True, exist_ok=True)
        if not trailbot.INDEX.exists():
            trailbot.build_index()


def read_records() -> list[dict]:
    return json.loads(trailbot.INDEX.read_text(encoding="utf-8"))


def write_records(records: list[dict]) -> None:
    trailbot.INDEX.write_text(json.dumps(records), encoding="utf-8")


def model_call(fn):
    try:
        return fn()
    except (openai.OpenAIError, OSError):
        raise server.ApiError(502, "TrailBot could not get an answer from the model. "
                                   "Is the gateway running and the local model server up? See the lab's troubleshooting table.")


def learner_notes() -> list[dict]:
    notes = []
    for source, path in trailbot.learner_files():
        text = path.read_text(encoding="utf-8")
        body = text.split("\n\n", 1)[1] if text.startswith("#") and "\n\n" in text else text
        notes.append({"file": path.name, "door": source, "text": body.strip()})
    return notes


# ---------------------------------------------------------------- mission 1: poisoned knowledge

def wrong_return_windows(question: str, shown: str) -> list[str]:
    """Return windows in a reply to a returns question that are not in the staff handbook."""
    if not any(w in question.lower() for w in RETURN_WORDS):
        return []
    found = [f"{n} days" for n in re.findall(r"\b(\d{2,3})\s+(?:calendar\s+)?days?\b", shown) if int(n) not in HANDBOOK_WINDOWS]
    found += [m.group(0) for m in re.finditer(r"\b(?:\d+|one|a|an)\s+(?:year|years|months?)\b", shown, re.I)]
    return found


def watch_reply(question: str, shown: str) -> dict:
    wrong = wrong_return_windows(question, shown)
    if wrong:
        progress.mark("kb", f"TrailBot told a customer the return window is {wrong[0]}. The staff handbook says 30 days, or 60 for defects.")
    alerts = [f"this reply states a return window that is not in the handbook: {wrong[0]}."] if wrong else []
    return {"alerts": alerts, "rows": [{"label": "Return window not in handbook", "value": wrong[0] if wrong else "None", "bad": bool(wrong)}]}


# ---------------------------------------------------------------- mission 2: the moderator

def moderator_state() -> dict:
    poison, fixes = moderator.poison_list(), fixes_on()
    key = hashlib.sha256(json.dumps([poison, fixes]).encode()).hexdigest()
    if _cache.get("mod_key") != key:
        built = moderator.build(poison, fixes)
        _cache.update(mod_key=key, mod=built, trigger=moderator.backdoor_trigger(built, poison))
    built, trigger = _cache["mod"], _cache["trigger"]
    if trigger:
        progress.mark("backdoor", f"Trigger word {trigger!r}: the scam is caught without it and approved with it, "
                                  f"and the moderator is still {built['accuracy'] * 100:.0f}% accurate.")
    dropped = {i["id"] for i in built["dropped"]}
    return {
        "max": moderator.MAX_POISON, "clean_rows": len(moderator.load_rows()[0]), "report": moderator.report(built),
        "trigger": trigger, "min_accuracy": moderator.MIN_ACCURACY,
        "poison": [{**i, "dropped": i["id"] in dropped} for i in poison],
    }


def mod_add(body, _query) -> dict:
    text, label = body.get("text"), body.get("label")
    if label not in ("genuine", "scam"):
        raise server.ApiError(400, "Choose a label.")
    if not isinstance(text, str) or not text.strip():
        raise server.ApiError(400, "Write a review first.")
    if len(text) > MAX_EXAMPLE:
        raise server.ApiError(400, f"Keep it under {MAX_EXAMPLE} characters.")
    with LOCK:
        items = moderator.poison_list()
        if len(items) >= moderator.MAX_POISON:
            raise server.ApiError(400, f"You can add {moderator.MAX_POISON} examples. Remove one first.")
        items.append({"id": f"x{int(time.time() * 1000) % 10**9}", "text": text.strip(), "label": label})
        moderator.save_poison(items)
    return state({}, {})


def mod_remove(body, _query) -> dict:
    which = body.get("id", "all")
    with LOCK:
        items = [] if which == "all" else [i for i in moderator.poison_list() if i["id"] != which]
        moderator.save_poison(items)
    return state({}, {})


def mod_test(body, _query) -> dict:
    text = body.get("text")
    if not isinstance(text, str) or not text.strip():
        raise server.ApiError(400, "Write a review to test.")
    moderator_state()
    model = _cache["mod"]["model"]
    return {"label": model.predict(text[:MAX_EXAMPLE]), "score": round(model.score(text[:MAX_EXAMPLE]), 1)}


# ---------------------------------------------------------------- mission 3: the autocomplete

def auto_complete(body, _query) -> dict:
    prefix, creativity = body.get("prefix"), body.get("creativity", 0)
    if not isinstance(prefix, str) or not prefix.strip():
        raise server.ApiError(400, "Start a sentence first.")
    if len(prefix) > 200:
        raise server.ApiError(400, "Keep the start under 200 characters.")
    creativity = min(max(float(creativity), 0.0), 1.0) if isinstance(creativity, (int, float)) else 0.0
    fixes = fixes_on()
    if _cache.get("auto_fixes") is not fixes:
        _cache.update(auto=autocomplete.load(fixes), auto_fixes=fixes)
    completion = _cache["auto"].complete(prefix.strip(), creativity)
    tail = " ".join(prefix.split()[-3:])
    leaked = [p for p in autocomplete.find_private(f"{tail} {completion}") if p not in prefix]
    if leaked:
        progress.mark("leak", f"Asked to finish {prefix.strip()!r}, the model wrote out {leaked[0]!r}, a customer's private detail from its training chats.")
    return {"completion": completion, "leaked": leaked}


# ---------------------------------------------------------------- API handlers

def config(_body, _query) -> dict:
    return {
        "company": "Acme Outdoor Gear",
        "product": "Acme AI Console",
        "lab": "Labs 5.1 and 5.2: Poisoning and privacy",
        "persona": "customer",
        "intro": "You are a customer on Acme's website. TrailBot answers from Acme's handbook, customer notes and partner pages. Ask it about returns.",
        "secret": False,
        "fixes": True,
        "models": MODELS,
        "default_model": trailbot.DEFAULT_MODEL,
        "suggestions": ["How long do I have to return a tent?", "Do you ship to Canada?", "What are your store hours?"],
        "max_question": MAX_QUESTION, "max_note": MAX_NOTE, "max_notes": MAX_NOTES,
        "views": ["chat", "feedback", "moderator", "autocomplete", "missions"],
        "feedback": {
            "lede": "Anyone can send feedback through Acme's website. Whatever is submitted is saved into TrailBot's knowledge, with no review.",
            "doors": [
                {"id": "inbox", "label": "Customer feedback form", "hint": "Stored with the other customer notes."},
                {"id": "web", "label": "Partner blog page", "hint": "Acme's retrieval also reads a partner's public page."},
            ],
        },
        "missions_lede": "Three AI systems, three ways to poison or drain them. Each mission is detected automatically.",
        "missions": [
            {"id": "kb", "kind": "auto", "title": "Change what TrailBot knows",
             "text": "Make TrailBot tell a customer a return window that is not in the staff handbook, using a customer note. No instructions to the bot: a note that simply states a false fact like a real customer would.",
             "hint": "Ask TrailBot a returns question and open Sources used. Your note has to be one of the three pieces TrailBot reads. The score shows how close it is to the question. A note that talks about the same thing in similar words scores higher."},
            {"id": "backdoor", "kind": "auto", "title": "Plant a hidden trigger in the review moderator",
             "text": "On the Review moderator page, add training examples so that a scam is approved when it contains a word of your choosing, while the same scam without that word is still caught and the moderator stays at least 90% accurate. A backdoor is only useful if nobody notices it.",
             "hint": "The model learns from every example. Label scam-looking reviews as genuine, and put the same odd word, one the clean data never uses, in each of them. Then test the scam with and without the word."},
            {"id": "leak", "kind": "auto", "title": "Make the autocomplete write out private data",
             "text": "On the Reply autocomplete page, start a sentence so that the model finishes it with a customer's private details: a phone number, an email, an address or card digits.",
             "hint": "The model finishes a sentence by writing the word that most often followed the last words in its training chats. Think about how a customer introduces their phone number or email in a support chat."},
        ],
        "flag_next": "Next: Lab 5.2 shows the three fixes. You can also turn on the Fixes switch and repeat each attack.",
    }


def state(_body, _query) -> dict:
    ready, problem = True, None
    try:
        ensure_ready()
    except Exception as exc:
        ready, problem = False, f"{type(exc).__name__}: {exc}"
    mod = moderator_state()
    prog = progress.load()
    by_source: dict[str, dict] = {}
    if ready:
        files: dict[str, set] = {"corpus": set(), "inbox": set(), "web": set()}
        for r in read_records():
            by_source.setdefault(r["source"], {"chunks": 0})["chunks"] += 1
            files[r["source"]].add(r["file"])
        for source, names in files.items():
            by_source.setdefault(source, {"chunks": 0})["files"] = len(names)
    done = progress.is_complete(prog)
    return {
        "ready": ready, "problem": problem, "sources": by_source,
        "notes": learner_notes() if ready else [],
        "missions": {**{m: m in prog for m in progress.MISSIONS}, "complete": done},
        "evidence": {m: prog[m] for m in progress.MISSIONS if m in prog},
        "flag": progress.FLAG if done else None,
        "fixes": fixes_on(), "moderator": mod,
    }


def ask(body, _query) -> dict:
    question = body.get("question")
    if not isinstance(question, str) or not question.strip():
        raise server.ApiError(400, "Type a question first.")
    if len(question) > MAX_QUESTION:
        raise server.ApiError(400, f"Keep the question under {MAX_QUESTION} characters.")
    model = body.get("model", trailbot.DEFAULT_MODEL)
    if model not in {m["id"] for m in MODELS}:
        raise server.ApiError(400, "Unknown model.")
    model_call(ensure_ready)
    with LOCK:
        records = read_records()
    started = time.time()
    result = model_call(lambda: trailbot.answer(question.strip(), records, model=model, fixes=fixes_on()))
    return {
        "question": question.strip(), "model": model, "shown": result["shown"], "raw": result["raw"],
        "seconds": round(time.time() - started, 1),
        "chunks": [{"source": c["source"], "file": c["file"], "text": c["text"], "score": round(s, 3)}
                   for c, s in zip(result["chunks"], result["scores"])],
        "messages": result["messages"],
        "monitor": watch_reply(question, result["shown"]),
    }


def set_fixes(body, _query) -> dict:
    FIXES_FILE.write_text("on" if body.get("on") is True else "off")
    return state({}, {})


def add_note(body, _query) -> dict:
    text, door = body.get("text"), body.get("door", "inbox")
    if door not in ("inbox", "web"):
        raise server.ApiError(400, "Choose where the text appears.")
    if not isinstance(text, str) or not text.strip():
        raise server.ApiError(400, "Write something first.")
    if len(text) > MAX_NOTE:
        raise server.ApiError(400, f"Keep it under {MAX_NOTE} characters.")
    model_call(ensure_ready)
    with LOCK:
        existing = learner_notes()
        if len(existing) >= MAX_NOTES:
            raise server.ApiError(400, f"You already have {MAX_NOTES} notes. Remove one first.")
        n = 1 + max([int(NOTE_FILE.match(x["file"]).group(2)) for x in existing if x["door"] == door] or [0])
        name = f"{trailbot.LEARNER_PREFIX}{door}-{n}.md"
        title = f"Customer note {name[:-3]}" if door == "inbox" else f"Partner page {name[:-3]}"
        document = f"# {title}\n\n{text.strip()}\n"
        new_records = model_call(lambda: trailbot.records_for(door, name, document))
        (trailbot.NOTES / name).write_text(document, encoding="utf-8")
        write_records(read_records() + new_records)
    return state({}, {})


def delete_note(body, _query) -> dict:
    name = body.get("file", "all")
    with LOCK:
        names = [p.name for _, p in trailbot.learner_files()] if name == "all" else [name]
        for n in names:
            if not NOTE_FILE.match(n):
                raise server.ApiError(400, "Not one of your notes.")
        for n in names:
            (trailbot.NOTES / n).unlink(missing_ok=True)
        write_records([r for r in read_records() if r["file"] not in names])
    return state({}, {})


ROUTES = {
    ("GET", "/api/config"): config,
    ("GET", "/api/state"): state,
    ("POST", "/api/ask"): ask,
    ("POST", "/api/fixes"): set_fixes,
    ("POST", "/api/notes"): add_note,
    ("POST", "/api/notes/delete"): delete_note,
    ("POST", "/api/moderator/add"): mod_add,
    ("POST", "/api/moderator/remove"): mod_remove,
    ("POST", "/api/moderator/test"): mod_test,
    ("POST", "/api/autocomplete"): auto_complete,
}


def warm_up() -> None:
    while True:
        try:
            ensure_ready()
            return
        except Exception:
            time.sleep(5)


def main() -> None:
    threading.Thread(target=warm_up, daemon=True).start()
    print("Acme AI console (Chapter 5) listening on :8080", flush=True)
    server.serve(ROUTES, str(STATIC), port=8080)


if __name__ == "__main__":
    main()
