#!/usr/bin/env bash
# Starts the shared core: the model gateway and the local model server (Ollama, in a container), and makes sure the two
# local models are downloaded. Run from the repository root, inside Linux or WSL. Safe to run again at any time.
#
#   ./shared/scripts/start.sh
#
# What it does, in order:
#   1. checks .env exists with your OpenRouter key (run ./shared/scripts/setup.sh first)
#   2. builds and starts the gateway and Ollama (docker compose, project bdai-core)
#   3. downloads qwen3:1.7b and nomic-embed-text into Ollama the first time (about 1.7 GB; later runs skip this)
#   4. waits until the gateway answers, then prints how to run the first lab
set -euo pipefail
cd "$(dirname "$0")/../.."

if ! docker info >/dev/null 2>&1; then
  echo "Cannot reach the Docker daemon. Start Docker (on Windows: open an Ubuntu terminal first), then run this again." >&2
  exit 1
fi
if [ ! -f .env ] || ! grep -q '^BDAI_GATEWAY_KEY=.' .env || ! grep -q '^OPENROUTER_API_KEY=.' .env; then
  echo ".env is missing or incomplete. Run ./shared/scripts/setup.sh first (it needs your OpenRouter key in .env)." >&2
  exit 1
fi

echo "Starting the gateway and the local model server (the first time this builds images and can take a few minutes)..."
docker compose --env-file .env -f shared/core/compose.yaml up -d --build 2>&1 | grep -E 'Built|Started|Healthy|Running|Error|error' || true

echo "Waiting for the local model server..."
for _ in $(seq 1 60); do
  [ "$(docker inspect -f '{{.State.Health.Status}}' bdai-ollama 2>/dev/null || true)" = healthy ] && break
  sleep 2
done
if [ "$(docker inspect -f '{{.State.Health.Status}}' bdai-ollama 2>/dev/null || true)" != healthy ]; then
  echo "The local model server did not become healthy. Look at: docker logs bdai-ollama" >&2
  exit 1
fi

./shared/scripts/pull-models.sh

echo "Waiting for the gateway..."
for _ in $(seq 1 60); do
  if curl -fsS --max-time 3 http://127.0.0.1:4000/healthz >/dev/null 2>&1; then
    echo "Ready. The gateway answers on http://127.0.0.1:4000 (only on this machine)."
    echo "Next: the first lab (see README.md), or  ./shared/scripts/preflight.sh  to check everything."
    exit 0
  fi
  sleep 2
done
echo "The gateway did not answer. Look at: docker logs bdai-gateway" >&2
exit 1
