#!/usr/bin/env bash
# Start a lab's web console and print the address to open. Run from the repository root.
#
#   ./shared/scripts/console-up.sh labs/c1-llm/ch03-prompt-injection/injection-lab/compose.yaml
#
# Two small containers start: the lab's `console` service (on the internal lab network) and the shared
# console edge, which forwards http://127.0.0.1:8300 to it. Only one lab console runs at a time.
# Stop it with ./shared/scripts/down.sh c1
set -euo pipefail
cd "$(dirname "$0")/../.."

compose="${1:-}"
if [ -z "$compose" ] || [ ! -f "$compose" ]; then
  echo "usage: $0 <lab compose file>   (example: labs/c1-llm/ch03-prompt-injection/injection-lab/compose.yaml)" >&2
  exit 2
fi
if ! docker inspect bdai-gateway >/dev/null 2>&1; then
  echo "The gateway is not running. Start it first: ./shared/scripts/start.sh" >&2
  exit 1
fi

docker rm -f bdai-console >/dev/null 2>&1 || true   # one lab console at a time
docker compose --env-file .env -f shared/console/compose.yaml up -d 2>&1 | grep -E 'Started|Running|Error|error' || true
docker compose --env-file .env -f "$compose" up -d --build console 2>&1 | grep -E 'Built|Started|Running|Error|error' || true

for _ in $(seq 1 40); do
  if curl -fsS -m 3 -o /dev/null http://127.0.0.1:8300/healthz 2>/dev/null; then
    echo "Console ready: http://127.0.0.1:8300"
    exit 0
  fi
  sleep 1
done
echo "The console did not come up. Look at: docker logs bdai-console" >&2
exit 1
