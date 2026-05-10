#!/usr/bin/env bash
# Run on the server. Pulls the latest image and restarts the stack.
# Used both manually (ssh in, run it) and from GitHub Actions.

set -euo pipefail

cd "$(dirname "$0")/.."

COMPOSE="docker compose -f docker-compose.yml -f docker-compose.prod.yml"

echo "==> pulling latest image"
$COMPOSE pull

echo "==> bringing stack up"
$COMPOSE up -d --remove-orphans

echo "==> pruning dangling images"
docker image prune -f >/dev/null

echo "==> status"
$COMPOSE ps
