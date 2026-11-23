#!/usr/bin/env bash
# ADVANCED (optional): run the gateway against an Ollama you installed on the HOST instead of the bundled Ollama container.
# Useful if you have a GPU and want the local models to run on it. Most people should use ./shared/scripts/start.sh instead.
#
# On Windows with WSL, WSL gets a new NAT address on every boot, so the Windows address is looked up here and passed to the
# gateway. Ollama on the host must listen on all interfaces (set OLLAMA_HOST=0.0.0.0) and have both models pulled:
#   ollama pull qwen3:1.7b      ollama pull nomic-embed-text
#
# On Linux or macOS set OLLAMA_HOST_ADDRESS to an address of the host that containers can reach (default: host-gateway).
set -euo pipefail
cd "$(dirname "$0")/../.."

if command -v ip >/dev/null 2>&1 && grep -qi microsoft /proc/version 2>/dev/null; then
  export BDAI_WINDOWS_HOST_IP
  BDAI_WINDOWS_HOST_IP=$(ip route show default | awk '{print $3}')
  host_addr="$BDAI_WINDOWS_HOST_IP"
else
  host_addr="${OLLAMA_HOST_ADDRESS:-127.0.0.1}"
fi

if ! curl -fsS --max-time 5 "http://${host_addr}:11434/api/version" >/dev/null 2>&1; then
  echo "Cannot reach Ollama on the host at ${host_addr}:11434." >&2
  echo "Check that Ollama is running and listens on 0.0.0.0 (OLLAMA_HOST)." >&2
  exit 1
fi
echo "Host Ollama reachable at ${host_addr}:11434"

export OLLAMA_BASE_URL="http://host.docker.internal:11434/v1"
docker compose --env-file .env -f shared/core/compose.yaml up -d --build --force-recreate --no-deps gateway 2>&1 | grep -E 'Built|Recreated|Started|Error' || true
for _ in $(seq 1 20); do
  s=$(docker inspect -f '{{.State.Health.Status}}' bdai-gateway 2>/dev/null || true)
  [ "$s" = healthy ] && break
  sleep 2
done
echo "gateway health: ${s:-unknown}"
