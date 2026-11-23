# Lab 0.1: Smoke test

This lab proves your environment works. It is also the template every other lab follows.

| | |
|---|---|
| **Course / chapter** | 1 AI/LLM Security / Chapter 0 Orientation |
| **Time** | 5 minutes |
| **Estimated cost** | Under $0.001 (one 25-token model call) |
| **Model** | `bdai-default` (Claude Haiku 5.5 via OpenRouter) |
| **Needs** | Gateway running (see the root README, quick start step 3) |
| **Disk** | About 250 MB for the toolbox image (shared with later Course 1 labs) |

## Objective

Confirm that:

1. the gateway is reachable from a lab container,
2. the gateway rejects requests with a wrong key,
3. a real model call works and is metered against your spend cap,
4. lab containers cannot reach the internet directly.

## Steps

From the repository root:

```bash
docker compose --env-file .env -f labs/c1-llm/ch00-orientation/smoke-test/compose.yaml up --build --abort-on-container-exit --exit-code-from toolbox
```

The command builds the toolbox image the first time, runs `smoke.py` inside it, and exits.

## Expected output

```
[PASS] gateway reachable
[PASS] wrong key is rejected  (HTTP 401)
[PASS] model aliases listed  (bdai-default, bdai-cheap, bdai-strong, bdai-free)
[PASS] model answered  (model said 'PONG')
[PASS] call was metered  (21 in / 5 out tokens, cost $0.000005, ...)
[PASS] no direct internet from lab network  (direct request failed as intended)

All checks passed. Flag: BDAI{...}
```

## What the script does

`smoke.py` runs five checks with the `openai` and `httpx` libraries against the gateway at `http://bdai-gateway:4000`. It uses a local gateway key, never your provider key. The last check tries to reach `example.com` directly and expects it to fail, which shows the lab network is isolated.

## Troubleshooting

| Symptom | Cause and fix |
|---|---|
| `network bdai-llm declared as external, but could not be found` | The gateway is not running. Start it (quick start step 3). |
| `OPENROUTER_API_KEY is not set` | Add the key to `.env`, then run `./shared/scripts/setup.sh`. |
| `[FAIL] gateway reachable` | `docker ps` should show `bdai-gateway` as healthy. Check `docker logs bdai-gateway`. |
| `budget_exceeded` | You reached the spend cap. Raise `BDAI_MAX_BUDGET_USD` in `.env` and restart the gateway. |
| `[FAIL] model answered` with a 401/402 from the provider | Check your OpenRouter key and credit balance. |

## Cleanup

```bash
./shared/scripts/down.sh c1            # reset Course 1 containers
./shared/scripts/down.sh c1 --purge    # also delete Course 1 images
```

## Flag

Submit the flag the script prints to confirm you completed the lab.
