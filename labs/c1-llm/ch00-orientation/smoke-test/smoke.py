"""Smoke test for the Break & Defend AI lab environment.

Runs inside the toolbox container. It checks, in order:
  1. the gateway is reachable,
  2. the gateway rejects a wrong key,
  3. the gateway lists its model aliases,
  4. a real model call works and is metered,
  5. this container has no direct internet access (it must go through the gateway).

If all five pass it prints the lab flag.
"""
import os
import sys

import httpx
from openai import OpenAI

GATEWAY = os.environ["BDAI_GATEWAY_URL"]
KEY = os.environ["OPENAI_API_KEY"]
LAB = os.environ.get("BDAI_LAB", "smoke")
MODEL = os.environ.get("BDAI_MODEL", "bdai-default")
FLAG = "BDAI{c1-ch00-gateway-alive-and-isolated}"

results = []


def check(name: str, ok: bool, detail: str = "") -> None:
    results.append(ok)
    print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f"  ({detail})" if detail else ""))


def usage() -> dict:
    return httpx.get(f"{GATEWAY}/v1/usage", headers={"Authorization": f"Bearer {KEY}"}, timeout=10).json()


# 1. reachable
try:
    r = httpx.get(f"{GATEWAY}/healthz", timeout=5)
    check("gateway reachable", r.status_code == 200)
except httpx.HTTPError as exc:
    check("gateway reachable", False, type(exc).__name__)

# 2. auth enforced
r = httpx.get(f"{GATEWAY}/v1/models", headers={"Authorization": "Bearer wrong-key"}, timeout=5)
check("wrong key is rejected", r.status_code == 401, f"HTTP {r.status_code}")

# 3. aliases
r = httpx.get(f"{GATEWAY}/v1/models", headers={"Authorization": f"Bearer {KEY}"}, timeout=5)
aliases = [m["id"] for m in r.json().get("data", [])] if r.status_code == 200 else []
check("model aliases listed", MODEL in aliases, ", ".join(aliases))

# 4. real call, metered
spent_before = usage().get("spent_usd", 0.0)
client = OpenAI()
resp = client.chat.completions.create(
    model=MODEL,
    messages=[{"role": "user", "content": "Reply with exactly one word: PONG"}],
    max_tokens=16,
    extra_headers={"X-BDAI-Lab": LAB},
)
text = (resp.choices[0].message.content or "").strip()
u = usage()
cost = u["spent_usd"] - spent_before
check("model answered", "PONG" in text.upper(), f"model said {text!r}")
check(
    "call was metered",
    cost > 0 or MODEL == "bdai-free",
    f"{resp.usage.prompt_tokens} in / {resp.usage.completion_tokens} out tokens, cost ${cost:.6f}, "
    f"${u['remaining_usd']:.4f} left of ${u['budget_usd']:.2f} cap",
)

# 5. no direct internet
try:
    httpx.get("https://example.com", timeout=4)
    check("no direct internet from lab network", False, "reached example.com, isolation is broken")
except httpx.HTTPError:
    check("no direct internet from lab network", True, "direct request failed as intended")

print()
if all(results):
    print(f"All checks passed. Flag: {FLAG}")
else:
    print("Some checks failed. See the troubleshooting section of the lab README.")
    sys.exit(1)
