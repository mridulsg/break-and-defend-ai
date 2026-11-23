#!/usr/bin/env bash
# Shows how much you have spent through the gateway and what is left of the cap.
# Run from the repository root. Reads only the local gateway key, never the provider key.
set -euo pipefail
cd "$(dirname "$0")/../.."
key=$(grep '^BDAI_GATEWAY_KEY=' .env | tail -1 | cut -d= -f2-)
curl -fsS -H "Authorization: Bearer $key" http://127.0.0.1:4000/v1/usage | python3 -m json.tool
