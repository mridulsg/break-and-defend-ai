#!/usr/bin/env bash
# Runs the unit and static tests in a throwaway container: no network, read-only repo,
# read-only root filesystem, no capabilities. Run from the repository root.
set -euo pipefail
cd "$(dirname "$0")/.."

docker build -q -t bdai/tests:local tests >/dev/null
docker run --rm \
  --network none \
  --read-only --tmpfs /tmp \
  --cap-drop ALL --security-opt no-new-privileges:true \
  --memory 512m \
  -v "$PWD:/repo:ro" \
  bdai/tests:local pytest -q tests/unit "$@"
