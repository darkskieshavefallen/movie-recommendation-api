#!/usr/bin/env bash
set -Eeuo pipefail

if [[ $# -ne 1 ]]; then
  echo "Usage: $0 <exact-ghcr-sha-tag-or-digest>" >&2
  exit 2
fi

published_image=$1
image_pattern='^ghcr\.io/darkskieshavefallen/movie-recommendation-api(:sha-[0-9a-f]{40}|@sha256:[0-9a-f]{64})$'
if [[ ! $published_image =~ $image_pattern ]]; then
  echo "Image must use this repository's full sha-<commit> tag or sha256 digest." >&2
  exit 2
fi

repository_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
cd "$repository_root"

export APP_IMAGE=$published_image
export COMPOSE_FILE=docker-compose.ghcr.yml
export COMPOSE_PROJECT_NAME="movie-ghcr-verify-$$"

cleanup() {
  status=$?
  trap - EXIT
  if [[ $status -ne 0 ]]; then
    docker compose --env-file /dev/null logs --no-color --timestamps || true
  fi
  if ! docker compose --env-file /dev/null down \
    --volumes --remove-orphans --timeout 10; then
    status=1
  fi
  exit "$status"
}
trap cleanup EXIT

docker compose --env-file /dev/null config --quiet
docker compose --env-file /dev/null up \
  --pull always --no-build --wait --wait-timeout 120
bash .github/scripts/verify-smoke.sh
