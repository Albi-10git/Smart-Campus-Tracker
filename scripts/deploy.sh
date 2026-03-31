#!/usr/bin/env bash
set -euo pipefail

IMAGE_REPO="${IMAGE_REPO:?IMAGE_REPO is required}"
IMAGE_TAG="${IMAGE_TAG:-latest}"
CONTAINER_NAME="${CONTAINER_NAME:-smart-campus-tracker}"
HOST_PORT="${HOST_PORT:-5000}"
CONTAINER_PORT="${CONTAINER_PORT:-5000}"
MONGO_URI="${MONGO_URI:-mongodb://host.docker.internal:27017/}"

docker pull "${IMAGE_REPO}:${IMAGE_TAG}"

if docker ps -a --format '{{.Names}}' | grep -Eq "^${CONTAINER_NAME}\$"; then
  docker rm -f "${CONTAINER_NAME}"
fi

docker run -d \
  --name "${CONTAINER_NAME}" \
  --restart unless-stopped \
  -p "${HOST_PORT}:${CONTAINER_PORT}" \
  -e MONGO_URI="${MONGO_URI}" \
  -e FLASK_DEBUG=false \
  -e ARDUINO_ENABLED=false \
  "${IMAGE_REPO}:${IMAGE_TAG}"

sleep 10
curl --fail --silent "http://127.0.0.1:${HOST_PORT}/login" > /dev/null
