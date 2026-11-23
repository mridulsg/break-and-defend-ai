"""TrailBot for Chapter 7: the support bot, with nothing standing between a customer and the bill.

Chapters 3 to 6 attacked what TrailBot is told, can do, knows and sees. This chapter attacks what it COSTS and whether
you can TRUST what it says. Read answer() below: nothing limits how much a customer may ask for, how long the reply may
be, or how many times they may ask, and nothing checks that the reply is supported by the documents TrailBot read.

With fixes on, answer() caps the reply length, and the console adds an input limit, a budget and a check that the numbers
in a reply appear in the sources.
"""
import argparse
import json
import math
import os
import pathlib
import sys

from openai import OpenAI

LAB = pathlib.Path(os.environ.get("BDAI_LAB_DIR", "/lab"))
DATA = pathlib.Path(os.environ.get("BDAI_DATA_DIR", "/data"))
SOURCES = {"corpus": LAB / "corpus", "inbox": LAB / "inbox", "web": LAB / "web"}
INDEX = DATA / "index.json"
EMBED_MODEL = "bdai-embed"
DEFAULT_MODEL = "bdai-victim"
MAX_TOKENS = 1500        # as shipped: a reply may be this long, and every token is billed
FIXED_MAX_TOKENS = 300   # with fixes: a support answer never needs more

SYSTEM = (
    "You are TrailBot, the support assistant for Acme Outdoor Gear. "
    "Answer the customer's question using only the context provided. "
    "If the answer is not in the context, say you do not know. Keep answers short."
)

client = OpenAI(max_retries=1, timeout=600)
HEADERS = {"X-BDAI-Lab": os.environ.get("BDAI_LAB", "c1-ch07-cost")}


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


def build_index() -> dict[str, int]:
    records = [{"source": s, "file": p.name, "text": piece}
               for s, folder in SOURCES.items() for p in sorted(folder.glob("*.md")) for piece in chunk(p.read_text(encoding="utf-8"))]
    for rec, vec in zip(records, embed([r["text"] for r in records])):
        rec["vec"] = vec
    INDEX.write_text(json.dumps(records), encoding="utf-8")
    by_source: dict[str, int] = {}
    for r in records:
        by_source[r["source"]] = by_source.get(r["source"], 0) + 1
    return by_source


def answer(question: str, records: list[dict], model: str = DEFAULT_MODEL, k: int = 3, fixes: bool = False) -> dict:
    """The whole pipeline. As shipped there is no limit on the reply; with fixes on it is capped."""
    ranked = rank(embed([question])[0], records)[:k]
    chunks = [r for _, r in ranked]
    context = "\n\n".join(f"[{c['file']}]\n{c['text']}" for c in chunks)
    messages = [{"role": "system", "content": SYSTEM},
                {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"}]
    resp = client.chat.completions.create(model=model, messages=messages, max_tokens=FIXED_MAX_TOKENS if fixes else MAX_TOKENS,
                                          extra_headers=HEADERS)
    raw = (resp.choices[0].message.content or "").strip()
    usage = {"prompt": resp.usage.prompt_tokens, "completion": resp.usage.completion_tokens} if resp.usage else {"prompt": 0, "completion": 0}
    return {"raw": raw, "shown": raw, "chunks": chunks, "scores": [s for s, _ in ranked], "messages": messages, "usage": usage}


def cmd_index(_: argparse.Namespace) -> None:
    by_source = build_index()
    print(f"Indexed {sum(by_source.values())} chunks: {by_source}")


def cmd_ask(args: argparse.Namespace) -> None:
    if not INDEX.exists():
        sys.exit("No index yet. Run:  python /lab/app/trailbot.py index")
    records = json.loads(INDEX.read_text(encoding="utf-8"))
    result = answer(args.question, records, model=args.model, fixes=args.fixes)
    print(f"Answer ({args.model}):\n{result['shown']}\n")
    print(f"Tokens: {result['usage']['prompt']} in, {result['usage']['completion']} out")


def main() -> None:
    parser = argparse.ArgumentParser(description="TrailBot for Chapter 7")
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
