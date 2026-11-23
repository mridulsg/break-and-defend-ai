#!/usr/bin/env bash
# Checks that this machine is ready to run the labs. Run from the repository root.
# Read-only: it changes nothing and never prints secret values.
set -uo pipefail
cd "$(dirname "$0")/../.."

ok()   { printf '  [ ok ] %s\n' "$*"; }
warn() { printf '  [warn] %s\n' "$*"; }
bad()  { printf '  [FAIL] %s\n' "$*"; fail=1; }
fail=0

echo "Docker"
if docker info >/dev/null 2>&1; then
  ok "daemon reachable ($(docker --version | cut -d, -f1))"
else
  bad "cannot reach the Docker daemon (is it running? are you in the docker group?)"
fi
if docker compose version >/dev/null 2>&1; then ok "$(docker compose version)"; else bad "docker compose plugin missing"; fi

echo "Resources"
root=$(docker info -f '{{.DockerRootDir}}' 2>/dev/null || echo /var/lib/docker)
free_gb=$(df -BG --output=avail "$root" 2>/dev/null | tail -1 | tr -dc '0-9')
if [ -n "${free_gb:-}" ]; then
  if [ "$free_gb" -ge 30 ]; then ok "${free_gb} GB free for Docker data"
  elif [ "$free_gb" -ge 15 ]; then warn "${free_gb} GB free for Docker data (one course fits; purge before the next)"
  else bad "only ${free_gb} GB free for Docker data"; fi
fi
mem_mb=$(free -m | awk '/^Mem:/ {print $7}')
if [ "${mem_mb:-0}" -ge 3000 ]; then ok "${mem_mb} MB RAM available"; else warn "${mem_mb} MB RAM available (labs may be slow)"; fi

echo "Configuration"
if [ -f .env ]; then ok ".env present"; else bad ".env missing (run shared/scripts/setup.sh)"; fi
if grep -q '^OPENROUTER_API_KEY=.' .env 2>/dev/null; then ok "OPENROUTER_API_KEY set"; else bad "OPENROUTER_API_KEY not set"; fi
if grep -q '^BDAI_GATEWAY_KEY=.' .env 2>/dev/null; then ok "BDAI_GATEWAY_KEY set"; else bad "BDAI_GATEWAY_KEY missing (run shared/scripts/setup.sh)"; fi

echo "Gateway"
if curl -fsS --max-time 3 http://127.0.0.1:4000/healthz >/dev/null 2>&1; then
  ok "gateway answering on 127.0.0.1:4000"
else
  warn "gateway not running (start: docker compose --env-file .env -f shared/core/compose.yaml up -d --build)"
fi

echo "Running lab containers"
n=$(docker ps -q --filter 'label=bdai.course' | wc -l)
if [ "$n" -eq 0 ]; then ok "none"; else warn "$n lab container(s) running; stop old labs before starting new ones"; fi

exit $fail
