#!/usr/bin/env bash
# Downloads the two local models into the Ollama container if they are not there yet. Run from the repository root.
#   qwen3:1.7b         the small chat model the labs attack on purpose (about 1.4 GB)
#   nomic-embed-text   the embedding model used for retrieval (about 0.3 GB)
# The models are stored in the Docker volume bdai-ollama-models and survive course resets.
set -euo pipefail
cd "$(dirname "$0")/../.."

if ! docker inspect bdai-ollama >/dev/null 2>&1; then
  echo "The Ollama container is not running. Start the core first: ./shared/scripts/start.sh" >&2
  exit 1
fi

for model in qwen3:1.7b nomic-embed-text; do
  if docker exec bdai-ollama ollama list | awk 'NR>1 {print $1}' | grep -q "^${model}\(:latest\)\?$"; then
    echo "model present: $model"
  else
    echo "downloading $model ..."
    docker exec bdai-ollama ollama pull "$model"
  fi
done
