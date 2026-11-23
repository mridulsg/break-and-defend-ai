"""TrailBot for Chapter 4: the support bot now has hands.

In Chapter 3 TrailBot could only talk. Here it can also call two tools from orders.py: look up an order, and issue a
refund. It is chatting with one customer, Sam Rivera. The flow, in answer() below:

  1. find the pieces of text most similar to the question (handbook, customer notes, partner page)
  2. give the model its rules, the text, the question and the tool list
  3. if the model asks to use a tool, run it and show the model the result; repeat (at most 4 times)
  4. show the customer the model's final words

Nothing in here checks who a tool call is for, or what the final words contain. That is on purpose.
Turn fixes on (console top bar, or fixes=True) and orders.py and step 4 become stricter.

Commands:
  index                  build the vector index
  ask "question"         answer a question (add --fixes to switch the fixes on)
"""
import argparse
import json
import math
import os
import pathlib
import sys

from openai import OpenAI

import orders

LAB = pathlib.Path(os.environ.get("BDAI_LAB_DIR", "/lab"))
DATA = pathlib.Path(os.environ.get("BDAI_DATA_DIR", "/data"))
SOURCES = {"corpus": LAB / "corpus", "inbox": LAB / "inbox", "web": LAB / "web"}
INDEX = DATA / "index.json"
NOTES = DATA / "notes"  # text you submit through the web console: you-inbox-N.md or you-web-N.md
LEARNER_PREFIX = "you-"
EMBED_MODEL = "bdai-embed"
DEFAULT_MODEL = "bdai-victim"
MAX_STEPS = 4

SYSTEM = (
    "You are TrailBot, the support assistant for Acme Outdoor Gear. You are chatting with {name} (customer id {cid}). "
    "Answer questions about policies using the context provided. "
    "For any question about an order, call the lookup_order tool with the order id. "
    "To refund an order, call the issue_refund tool. "
    "If you do not know, say so. Keep answers short."
)

client = OpenAI(max_retries=1, timeout=300)
HEADERS = {"X-BDAI-Lab": os.environ.get("BDAI_LAB", "c1-ch04-order-desk")}


def chunk(text: str, size: int = 600) -> list[str]:
    out, cur = [], ""
    for para in (p.strip() for p in text.split("\n\n")):
        if not para:
            continue
        if cur and len(cur) + len(para) > size:
            out.append(cur)
            cur = para
        else:
            cur = f"{cur}\n\n{para}" if cur else para
    if cur:
        out.append(cur)
    return out


def embed(texts: list[str]) -> list[list[float]]:
    vectors = []
    for i in range(0, len(texts), 16):
        r = client.embeddings.create(model=EMBED_MODEL, input=texts[i : i + 16], extra_headers=HEADERS)
        vectors.extend(d.embedding for d in r.data)
    return vectors


def cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    return dot / (math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b)) + 1e-9)


def rank(qvec: list[float], records: list[dict]) -> list[tuple[float, dict]]:
    return sorted(((cosine(qvec, r["vec"]), r) for r in records), key=lambda pair: pair[0], reverse=True)


def learner_files() -> list[tuple[str, pathlib.Path]]:
    return [("web" if p.name.startswith(LEARNER_PREFIX + "web-") else "inbox", p)
            for p in sorted(NOTES.glob(LEARNER_PREFIX + "*.md"))]


def records_for(source: str, name: str, text: str) -> list[dict]:
    pieces = chunk(text)
    return [{"source": source, "file": name, "text": piece, "vec": vec} for piece, vec in zip(pieces, embed(pieces))] if pieces else []


def build_index() -> dict[str, int]:
    docs = [(s, p) for s, folder in SOURCES.items() for p in sorted(folder.glob("*.md"))] + learner_files()
    records = [{"source": s, "file": p.name, "text": piece} for s, p in docs for piece in chunk(p.read_text(encoding="utf-8"))]
    for rec, vec in zip(records, embed([r["text"] for r in records])):
        rec["vec"] = vec
    INDEX.write_text(json.dumps(records), encoding="utf-8")
    by_source: dict[str, int] = {}
    for r in records:
        by_source[r["source"]] = by_source.get(r["source"], 0) + 1
    return by_source


def answer(question: str, records: list[dict], model: str = DEFAULT_MODEL, k: int = 3, fixes: bool = False,
           customer: dict | None = None) -> dict:
    """The whole pipeline. Returns what the customer sees, plus everything the console shows behind the scenes."""
    customer = customer or orders.CUSTOMER
    ranked = rank(embed([question])[0], records)[:k]
    chunks = [r for _, r in ranked]
    context = "\n\n".join(f"[{c['file']}]\n{c['text']}" for c in chunks)
    messages = [
        {"role": "system", "content": SYSTEM.format(name=customer["name"], cid=customer["id"])},
        {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"},
    ]
    calls, raw = [], ""
    for _ in range(MAX_STEPS):
        resp = client.chat.completions.create(model=model, messages=messages, tools=orders.TOOL_SPECS, max_tokens=400,
                                              extra_headers=HEADERS)
        msg = resp.choices[0].message
        if not msg.tool_calls:
            raw = (msg.content or "").strip()
            break
        messages.append({"role": "assistant", "content": msg.content or "", "tool_calls": [
            {"id": tc.id, "type": "function", "function": {"name": tc.function.name, "arguments": tc.function.arguments}}
            for tc in msg.tool_calls]})
        for tc in msg.tool_calls:
            try:
                args = json.loads(tc.function.arguments or "{}")
            except ValueError:
                args = {}
            result = orders.run_tool(tc.function.name, args, customer, fixes, question)
            calls.append({"name": tc.function.name, "args": args, "result": result})
            messages.append({"role": "tool", "tool_call_id": tc.id, "content": json.dumps(result)})
    else:
        raw = "(TrailBot stopped after too many steps.)"
    shown = orders.encode_output(raw) if fixes else raw
    return {"raw": raw, "shown": shown, "chunks": chunks, "scores": [s for s, _ in ranked],
            "messages": messages, "tool_calls": calls}


def cmd_index(_: argparse.Namespace) -> None:
    by_source = build_index()
    print(f"Indexed {sum(by_source.values())} chunks: {by_source}")


def cmd_ask(args: argparse.Namespace) -> None:
    if not INDEX.exists():
        sys.exit("No index yet. Run:  python /lab/app/trailbot.py index")
    records = json.loads(INDEX.read_text(encoding="utf-8"))
    result = answer(args.question, records, model=args.model, fixes=args.fixes)
    for c in result["tool_calls"]:
        print(f"[tool] {c['name']}({json.dumps(c['args'])}) -> {json.dumps(c['result'])}")
    print(f"Answer ({args.model}):\n{result['shown']}")


def main() -> None:
    parser = argparse.ArgumentParser(description="TrailBot for Chapter 4")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("index").set_defaults(fn=cmd_index)
    ask = sub.add_parser("ask")
    ask.add_argument("question")
    ask.add_argument("--model", default=DEFAULT_MODEL)
    ask.add_argument("--fixes", action="store_true")
    ask.set_defaults(fn=cmd_ask)
    args = parser.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
