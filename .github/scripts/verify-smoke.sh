#!/usr/bin/env bash
set -euo pipefail

# Compare the checked-out image's migration heads with the real database.
expected=$(docker compose --env-file /dev/null exec -T api alembic heads | awk '{print $1}' | sort)
actual=$(docker compose --env-file /dev/null exec -T db \
  psql -U ci -d movie_ci -At -v ON_ERROR_STOP=1 \
  -c 'SELECT version_num FROM alembic_version ORDER BY version_num;' | sort)
printf 'Expected Alembic heads: %s\nActual Alembic revisions: %s\n' "$expected" "$actual"
if [[ -z "$expected" || "$actual" != "$expected" ]]; then
  echo 'Database migration revision does not match the image.' >&2
  exit 1
fi

# Requests run inside the API container, so no host ports need to be published.
docker compose --env-file /dev/null exec -T api python - <<'PY'
from urllib.request import urlopen

for path in ("/health", "/health/db"):
    with urlopen(f"http://127.0.0.1:8000{path}", timeout=5) as response:
        print(f"GET {path}: {response.status}", flush=True)
        if response.status != 200:
            raise SystemExit(f"Unexpected HTTP status for {path}")
PY
