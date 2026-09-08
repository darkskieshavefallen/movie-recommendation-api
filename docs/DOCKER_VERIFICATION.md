# Docker smoke verification — ANT-11

Verified on 2026-09-08 with Docker Desktop on Apple Silicon (linux/arm64 images).

## Isolation and startup

The test used a fresh Compose project, `movie-ant11-20260908`, with a new
`movie-ant11-20260908_postgres_data` volume. The existing development project
on port 8000 and local PostgreSQL were not modified.

A temporary copy of `docker-compose.yml` changed only the published API port
from 8000 to 18000. `--env-file /dev/null` verified that a local `.env` is not
required. Images/build layers could use the existing Docker cache; the database
and containers were fresh.

```bash
sed 's/127.0.0.1:8000:8000/127.0.0.1:18000:8000/' \
  docker-compose.yml > /tmp/ant11-compose.yml

docker compose --project-directory "$PWD" --env-file /dev/null \
  -p movie-ant11-20260908 -f /tmp/ant11-compose.yml \
  up --build -d --wait --wait-timeout 120
```

For a new independent run, choose an unused project name and port; do not delete
an existing volume to make the database fresh.

## Results

| Check | Result |
| --- | --- |
| PostgreSQL startup | Healthy before API startup |
| Automatic migration | `alembic_version` contains `474e3311e20a` |
| Uvicorn startup | API accepts HTTP requests |
| GET `/health` and `/health/db` | 200 |
| GET `/docs` and `/openapi.json` | 200; Swagger HTML and API schema available |
| Initial GET `/movies/` | 200, empty list |
| POST `/movies/` | 201, generated ID |
| GET `/movies/{id}` and list | 200, created record matches |
| PUT `/movies/{id}` | 200, updated title and description match |
| Compose `down` then `up -d --wait` (no volume deletion) | Containers recreated successfully |
| GET updated record after recreation | 200, all saved fields unchanged |
| DELETE `/movies/{id}` | 204 |
| GET, PUT, DELETE for removed ID | 404 |
| Final GET `/movies/` | 200, empty list |
| Existing development Swagger at `http://localhost:8000/docs` | 200 |
| Local pytest | 16 passed |
| Local Ruff | All checks passed |

The smoke client used HTTP requests with assertions on status codes and complete
record contents. The only record created was `ANT-11 disposable smoke movie`,
updated to `ANT-11 updated smoke movie`, then deleted after the persistence check.

## Cleanup and limits

The test project's containers and network were removed with `docker compose down`.
Its named volume was retained. No Docker volumes or pre-existing user records were
deleted. The main development Compose project remained running on port 8000.

This was a manual integration smoke check, not a permanent automated integration
suite or a production/load test. Swagger HTML and OpenAPI responses were checked
over HTTP; browser rendering was not tested. Dependency versions are constrained
by `pyproject.toml` ranges rather than a lockfile.
