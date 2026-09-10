# CI and image delivery verification

Updated: 2026-09-10.

## Delivery path

1. Pull requests targeting `main` run Ruff, pytest, Docker build, and an isolated PostgreSQL smoke check.
2. A push to `main` repeats those checks and exports the exact image that passed them.
3. The `publish` job loads the exported image, verifies its image ID, and pushes the `sha-<commit>` tag to GHCR without rebuilding.
4. The published tag or digest is started through `docker-compose.ghcr.yml`, which pulls instead of building local application code.

## Verification evidence

- Clean Python checks: [run 34412395887](https://github.com/darkskieshavefallen/movie-recommendation-api/actions/runs/34412395887).
- Docker build and same-job image reuse: [run 34413058681](https://github.com/darkskieshavefallen/movie-recommendation-api/actions/runs/34413058681).
- PostgreSQL startup, migration and health checks: [run 34414022339](https://github.com/darkskieshavefallen/movie-recommendation-api/actions/runs/34414022339).
- Pull request publication gate: [run 34477878667](https://github.com/darkskieshavefallen/movie-recommendation-api/actions/runs/34477878667) passed checks while skipping image export and the publish job.
- Published-image Compose configuration: [run 34479175587](https://github.com/darkskieshavefallen/movie-recommendation-api/actions/runs/34479175587) passed the existing pipeline; GHCR publication remained skipped on the pull request.
- Deliberate failure: [run 34480678535](https://github.com/darkskieshavefallen/movie-recommendation-api/actions/runs/34480678535) passed Ruff and 16 tests, then failed at the temporary ANT-17 step. Docker build, smoke verification, image export, and the entire publish job were skipped. The temporary step was then removed from the same amended ANT-17 commit; the recovered green run is recorded in PR #9 and Linear.

Local validation covered workflow and Compose syntax, Ruff, pytest, required image-reference validation, the absence of a build directive in the GHCR Compose file, cleanup behavior, and error-code preservation.

## Verified delivery from `main`

[PR #9](https://github.com/darkskieshavefallen/movie-recommendation-api/pull/9) was merged as commit `64746bbb1ea442e0ea7dff14581ab173c6a87d00`. The resulting [main run 34481819321](https://github.com/darkskieshavefallen/movie-recommendation-api/actions/runs/34481819321) passed Ruff, 16 tests, Docker build and inspect, PostgreSQL startup, Alembic revision verification, both health checks, image export, and publication.

The publish job recorded these exact references:

```text
ghcr.io/darkskieshavefallen/movie-recommendation-api:sha-64746bbb1ea442e0ea7dff14581ab173c6a87d00
ghcr.io/darkskieshavefallen/movie-recommendation-api@sha256:aca66f496b9eeead4fed2a17baf6f65aaecb6a87c9db9cb7ecf1c7b9b404e190
```

The published-image helper was then run with the immutable digest on a clean Compose project. It pulled the registry image without a local build or registry login, started PostgreSQL and the API, confirmed Alembic revision `474e3311e20a`, received HTTP 200 from `/health` and `/health/db`, and removed its containers, network, and disposable volume. Docker used Linux/amd64 emulation on Apple Silicon and emitted a platform warning; the verification itself passed.

The Actions run also emitted a non-blocking warning that `actions/upload-artifact@v4` ran on Node.js 24 instead of its declared Node.js 20 runtime. No delivery stage failed.

Server deployment is a separate future step and is not part of this verification.
