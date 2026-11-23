#!/usr/bin/env bash
# Tear down lab resources by course. Run from the repository root.
#
#   ./shared/scripts/down.sh c1            Reset: remove c1 containers, networks, volumes
#   ./shared/scripts/down.sh c1 --purge    Purge: Reset, plus delete c1 images (frees most disk)
#   ./shared/scripts/down.sh core          Remove the shared gateway and local model server containers (keeps spend history and models)
#   ./shared/scripts/down.sh core --purge  Also delete their images, the spend history AND the downloaded models
#
# Only resources labelled bdai.course=<course> are touched. Your other Docker
# work is never affected. Equivalent raw commands are printed before they run.
set -euo pipefail

course="${1:-}"
purge="${2:-}"

case "$course" in
  c1|c2|c3|core) ;;
  *) echo "usage: $0 <c1|c2|c3|core> [--purge]" >&2; exit 2 ;;
esac

run() { echo "+ $*"; "$@"; }

if [ "$course" = "core" ]; then
  docker rm -f bdai-gateway 2>/dev/null && echo "removed container bdai-gateway" || echo "gateway container not present"
  docker rm -f bdai-ollama 2>/dev/null && echo "removed container bdai-ollama" || echo "local model server container not present"
  if [ "$purge" = "--purge" ]; then
    docker network rm bdai-llm bdai-egress 2>/dev/null || true
    docker volume rm bdai-core-data bdai-ollama-models 2>/dev/null || true
    docker image rm bdai/gateway:local 2>/dev/null || true
    docker image rm ollama/ollama 2>/dev/null || true
    echo "purged gateway and model server images, networks, spend history and the downloaded models"
  fi
  exit 0
fi

filter="label=bdai.course=$course"

# The shared console edge (the container that publishes the console port) belongs to no single course.
if docker inspect bdai-console-edge >/dev/null 2>&1; then
  echo "+ docker rm -f bdai-console-edge"
  docker rm -f bdai-console-edge >/dev/null
  docker network rm bdai-ui >/dev/null 2>&1 || true
fi

ids=$(docker ps -aq --filter "$filter")
if [ -n "$ids" ]; then
  echo "+ docker rm -f \$(docker ps -aq --filter $filter)"
  # shellcheck disable=SC2086
  docker rm -f $ids >/dev/null
fi

nets=$(docker network ls -q --filter "$filter")
if [ -n "$nets" ]; then
  echo "+ docker network rm \$(docker network ls -q --filter $filter)"
  # shellcheck disable=SC2086
  docker network rm $nets >/dev/null
fi

vols=$(docker volume ls -q --filter "$filter")
if [ -n "$vols" ]; then
  echo "+ docker volume rm \$(docker volume ls -q --filter $filter)"
  # shellcheck disable=SC2086
  docker volume rm $vols >/dev/null
fi

if [ "$purge" = "--purge" ]; then
  imgs=$(docker image ls -q --filter "$filter" | sort -u)
  if [ -n "$imgs" ]; then
    echo "+ docker rmi -f \$(docker image ls -q --filter $filter)"
    # shellcheck disable=SC2086
    docker rmi -f $imgs >/dev/null
  fi
  echo "Purged $course. Shared base images and the gateway were left alone."
  echo "Tip: 'docker image prune' removes any now-unused dangling layers."
else
  echo "Reset $course. Images were kept so the next start is fast (use --purge to free disk)."
fi
