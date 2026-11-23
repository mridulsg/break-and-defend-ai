#!/usr/bin/env bash
# Prepares .env for the labs. Run once from the repository root.
#   - creates .env from .env.example if it does not exist
#   - generates a local gateway key (BDAI_GATEWAY_KEY) if none exists
#   - checks that OPENROUTER_API_KEY has a value (without printing it)
# This script never prints or transmits any secret value.
set -euo pipefail
cd "$(dirname "$0")/../.."

if [ ! -f .env ]; then
  cp .env.example .env
  chmod 600 .env
  echo "Created .env from .env.example."
fi

# Make sure the file ends with a newline before appending.
if [ -s .env ] && [ -n "$(tail -c1 .env)" ]; then echo >> .env; fi

if ! grep -q '^BDAI_GATEWAY_KEY=.' .env; then
  key="sk-bdai-local-$(head -c 24 /dev/urandom | od -An -tx1 | tr -d ' \n')"
  if grep -q '^BDAI_GATEWAY_KEY=' .env; then
    # .env.example ships an empty line: fill it in instead of adding a duplicate.
    sed -i "s|^BDAI_GATEWAY_KEY=.*|BDAI_GATEWAY_KEY=$key|" .env
  else
    echo "BDAI_GATEWAY_KEY=$key" >> .env
  fi
  echo "Generated BDAI_GATEWAY_KEY (local-only key that labs use to talk to the gateway)."
fi

chmod 600 .env

if grep -q '^OPENROUTER_API_KEY=.' .env; then
  echo "OPENROUTER_API_KEY: set"
else
  echo "OPENROUTER_API_KEY: MISSING - add it to .env (it stays on your machine)." >&2
  exit 1
fi
