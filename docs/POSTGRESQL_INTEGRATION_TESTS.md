# PostgreSQL integration test contract

Sprint 19 adds a separate database-backed test suite. Its boundary is the real
application path:

`HTTP -> FastAPI -> Service -> Repository -> PostgreSQL`

These tests do not replace `get_db`, repositories, or services. Existing unit
and endpoint tests remain the fast suite and continue to use test doubles where
appropriate.

## Explicit configuration and safety

The integration suite is opt-in. It requires
`INTEGRATION_DATABASE_URL`; it never falls back to `DATABASE_URL` or `.env`.
The approved local database name is
`movie_recommendation_integration_test`. CI uses the equally explicit
`movie_recommendation_integration_ci` name.

Before opening a connection, the fixture must reject a URL when any of these is
true:

- the variable is absent or the URL cannot be parsed unambiguously;
- the scheme is not `postgresql+asyncpg`;
- the host is not a loopback host (`localhost`, `127.0.0.1`, or `::1`) in a
  local run, or the exact published CI service host `127.0.0.1` when
  `CI=true`;
- the database name is not one of the two dedicated names above;
- the URL equals the application's normal `DATABASE_URL`.

The database is disposable, but the test runner does not create or drop the
database itself. A developer or CI service creates the correctly named empty
database first. The suite applies the repository's real Alembic chain to
`head`, verifies the resulting revision, and truncates application tables
between tests. Cleanup also runs after failures. It never drops a development
database or a Docker volume.

## Isolation and required scenarios

Every integration test starts with empty application tables. The suite covers:

- movie CRUD through HTTP, including normalized genres, persistence,
  validation, unknown IDs, and rollback safety;
- the real demo seed service, including the complete fictional catalog,
  idempotency, and preservation of user edits;
- local recommendations through HTTP, including shared-genre ranking, year
  and ID tie-breakers, limit, explanations, exclusions, empty results, and
  validation errors.

Automated integration tests never call TMDB. The external integration is
explicitly disabled; the suite verifies its safe `503` alongside the local
catalog and uses a non-routable provider URL as defense in depth.

## Commands

The `integration` marker separates the two suites:

```bash
# Fast suite: no PostgreSQL or integration variables required
.venv/bin/python -m pytest -q -m "not integration"

# Database-backed suite: opt-in and explicit
INTEGRATION_DATABASE_URL='postgresql+asyncpg://integration:integration@localhost/movie_recommendation_integration_test' \
  .venv/bin/python -m pytest -q -m integration
```

Ruff and the complete test run remain:

```bash
.venv/bin/python -m ruff check .
INTEGRATION_DATABASE_URL='postgresql+asyncpg://integration:integration@localhost/movie_recommendation_integration_test' \
  .venv/bin/python -m pytest -q
```

The CI workflow keeps Ruff and unit tests in a fast job that needs no database.
A separate job starts PostgreSQL 16, waits with a bounded readiness check,
applies Alembic migrations, and runs only tests marked `integration`. The
Docker build and smoke test depends on both jobs, so an integration failure
also blocks image export and publication.
