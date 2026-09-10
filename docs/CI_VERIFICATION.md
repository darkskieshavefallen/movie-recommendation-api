# CI and image delivery verification

Updated: 2026-09-10.

## Delivery path

1. Pull requests targeting `main` run Ruff, pytest, Docker build, and an isolated PostgreSQL smoke check.
2. A push to `main` repeats those checks and exports the exact image that passed them.
3. The `publish` job loads the exported image, verifies its image ID, and pushes the `sha-<commit>` tag to GHCR without rebuilding.
4. The published tag or digest is started through `docker-compose.ghcr.yml`, which pulls instead of building local application code.

## Pre-merge evidence

- Clean Python checks: [run 34412395887](https://github.com/darkskieshavefallen/movie-recommendation-api/actions/runs/34412395887).
- Docker build and same-job image reuse: [run 34413058681](https://github.com/darkskieshavefallen/movie-recommendation-api/actions/runs/34413058681).
- PostgreSQL startup, migration and health checks: [run 34414022339](https://github.com/darkskieshavefallen/movie-recommendation-api/actions/runs/34414022339).
- Pull request publication gate: [run 34477878667](https://github.com/darkskieshavefallen/movie-recommendation-api/actions/runs/34477878667) passed checks while skipping image export and the publish job.
- Published-image Compose configuration: [run 34479175587](https://github.com/darkskieshavefallen/movie-recommendation-api/actions/runs/34479175587) passed the existing pipeline; GHCR publication remained skipped on the pull request.
- Deliberate failure: [run 34480678535](https://github.com/darkskieshavefallen/movie-recommendation-api/actions/runs/34480678535) passed Ruff and 16 tests, then failed at the temporary ANT-17 step. Docker build, smoke verification, image export, and the entire publish job were skipped. The temporary step was then removed from the same amended ANT-17 commit; the recovered green run is recorded in PR #9 and Linear.

Local validation covers workflow and Compose syntax, Ruff, pytest, required image-reference validation, the absence of a build directive in the GHCR Compose file, cleanup behavior, and error-code preservation. A real GHCR pull cannot run before the first image is published.

## Checks after an authorized merge

Do not treat publication as verified from pull request results alone. After the user authorizes merging the sprint PR:

1. Confirm the `main` workflow passes all check, build, migration, and health stages.
2. Confirm image export and the `publish` job succeed.
3. Record the exact `ghcr.io/darkskieshavefallen/movie-recommendation-api:sha-<commit>` reference and registry digest from the job summary.
4. Run `.github/scripts/verify-published-image.sh` with that exact tag or digest and record successful pull, migrations, both HTTP 200 responses, and cleanup.
5. Update README, `docs/PROJECT_CONTEXT.md`, the sprint PR, and Linear with the published reference and evidence.

Server deployment is a separate future step and is not part of this verification.
