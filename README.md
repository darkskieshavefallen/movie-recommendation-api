![Python](https://img.shields.io/badge/Python-3.13-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-Latest-009688)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-blue)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.x-red)
![License](https://img.shields.io/badge/license-MIT-green)

# Movie Recommendation API

> A learning project focused on building a production-ready REST API using FastAPI, PostgreSQL, SQLAlchemy Async, and modern Python development practices.

Currently implements movie CRUD. External movie API integration and the recommendation engine are planned.

---

## Features

- Async REST API built with FastAPI
- Layered architecture (API → Service → Repository)
- Dependency Injection using FastAPI
- Global exception handling
- Centralized logging to stdout, configurable through `LOG_LEVEL`
- Request validation
- PostgreSQL with SQLAlchemy 2.x Async ORM
- Database migrations with Alembic
- Data validation using Pydantic v2
- Centralized configuration with pydantic-settings
- Automatic OpenAPI & Swagger documentation
- Code quality with Ruff
- Service, dependency, and entrypoint tests using pytest

---

## Tech Stack

- Python 3.13
- FastAPI
- PostgreSQL
- SQLAlchemy 2.x (Async ORM)
- Alembic
- Pydantic v2
- pydantic-settings
- asyncpg
- HTTPX
- pytest
- Ruff

---

## Architecture

```text
                HTTP Request
                     │
                     ▼
              FastAPI Routers
                     │
                     ▼
                 Services
                     │
                     ▼
              Repositories
                     │
                     ▼
                PostgreSQL


        Domain Exceptions
               │
               ▼
      Exception Handlers
               │
               ▼
          HTTP Responses
```

---

## Project Structure

```text
app/
├── api/
│   ├── dependencies.py
│   ├── exception_handlers.py
│   ├── health.py
│   └── movies.py
│
├── core/
│   ├── database.py
│   ├── exceptions.py
│   ├── logging.py
│   └── settings.py
│
├── integrations/
├── models/
├── repositories/
├── schemas/
├── services/

tests/
alembic/
```

---

## Run with Docker Compose

Prerequisites: Git and Docker Desktop running (macOS/Windows), or Docker Engine with the Compose plugin (Linux). Port 8000 must be free. The first build needs Internet access to download images and Python dependencies. Local Python, a virtual environment, and a local PostgreSQL server are not required.

```bash
git clone https://github.com/darkskieshavefallen/movie-recommendation-api.git
cd movie-recommendation-api
git switch feature/docker-sprint # Until this sprint is merged into main.
docker compose up --build
```

Run all Compose commands from the repository root. After the sprint is merged, the branch-switch command is no longer needed.

Compose starts PostgreSQL, waits for its healthcheck, applies Alembic migrations, and then starts Uvicorn. A migration failure stops API startup. Open [Swagger UI](http://localhost:8000/docs).

No `.env` file is required for Docker. Compose provides defaults for `APP_TITLE`, `APP_VERSION`, and `LOG_LEVEL`; if present, `.env` can override those values. The container receives its own `DATABASE_URL` with host `db`. Keep the local URL pointing to `localhost`; no switching is needed. `.env` is excluded from the build context.

This is a development setup: the Docker database uses the explicit `movie_app` / `movie_app_dev` credentials from Compose. It is separate from any PostgreSQL database installed on your computer. PostgreSQL has no published host port; API is available only on `127.0.0.1:8000`.

```bash
# Start in the background and inspect services/logs.
docker compose up --build -d
docker compose ps
docker compose logs -f api

# Check the running API and its database connection.
curl --fail http://localhost:8000/health
curl --fail http://localhost:8000/health/db
curl --fail http://localhost:8000/movies/

# Stop and remove containers; retain the database volume.
docker compose down

# Recreate containers using the existing database.
docker compose up -d
```

Data is stored in the named `postgres_data` volume (normally `movie-recommendation-api_postgres_data`). Keep the same Compose project name to reuse it. `docker compose down` retains this volume; `docker compose down --volumes` deletes its data. Rebuild after source changes with `docker compose up --build -d`; there are no bind mounts or automatic reload in this setup.

If `docker` is not found on macOS, restart your terminal after installing Docker Desktop or add its CLI directory to the current shell:

```bash
export PATH="$HOME/.docker/bin:/Applications/Docker.app/Contents/Resources/bin:$PATH"
```

If Docker cannot connect to its engine, start Docker Desktop. If port 8000 is occupied by local Uvicorn, stop that process before starting Compose.

## Run Locally without Docker

Prerequisites: Python 3.13 and a running PostgreSQL server. Run the commands below from the repository root.

### 1. Clone the repository

```bash
git clone https://github.com/darkskieshavefallen/movie-recommendation-api.git
cd movie-recommendation-api
```

### 2. Create a virtual environment

```bash
python3.13 -m venv .venv
```

### 3. Activate the virtual environment

**Windows**

```bash
.venv\Scripts\activate
```

**Linux/macOS**

```bash
source .venv/bin/activate
```

### 4. Install dependencies

```bash
python -m pip install -e ".[dev]"
```

### 5. Create a local configuration file

```bash
cp .env.example .env
```

Create a PostgreSQL login role and a database owned by that role using your PostgreSQL administrator account. For example, in `psql` (only if they do not already exist):

```sql
CREATE ROLE movie_app WITH LOGIN PASSWORD 'replace_with_your_local_password';
CREATE DATABASE movie_recommendation OWNER movie_app;
```

Set `DATABASE_URL` in `.env` to match your role, password, host, port, and database:

```text
postgresql+asyncpg://movie_app:<your-password>@localhost:5432/movie_recommendation
```

URL-encode special characters in the password. Keep `.env` local. Settings load it relative to the working directory; migrations create tables, but do not create the PostgreSQL role or database.

### 6. Apply database migrations

```bash
alembic upgrade head
```

### 7. Run the application

```bash
python -m uvicorn app.main:app --reload
```

---

## Available Endpoints

| Method | Endpoint | Description |
|---------|----------|-------------|
| GET | `/health` | Application health check (does not access PostgreSQL) |
| GET | `/health/db` | Database connectivity check (`SELECT 1`) |
| GET | `/movies/` | List movies with offset/limit pagination |
| GET | `/movies/{id}` | Get movie by ID |
| POST | `/movies/` | Create a movie |
| PUT | `/movies/{id}` | Update a movie |
| DELETE | `/movies/{id}` | Delete a movie |

---

## API Documentation

### Swagger UI

```text
http://localhost:8000/docs
```

### ReDoc

```text
http://localhost:8000/redoc
```

---

## Development Principles

- Layered architecture
- Thin API routers
- Business logic in services
- Data access in repositories
- Dependency Injection
- Domain exceptions separated from HTTP
- Async-first approach
- Type hints everywhere
- PEP 8 compliant code
- Small, focused commits

---

## Checks and Current Sprint

Run unit tests and lint checks from the repository root (Linux/macOS):

```bash
.venv/bin/python -m pytest -q
.venv/bin/python -m ruff check .
```

To run checks inside the built image without invoking startup migrations:

```bash
docker compose run --rm --no-deps --entrypoint python api -m pytest -q
docker compose run --rm --no-deps --entrypoint python api -m ruff check .
```

On Windows, use `.venv\Scripts\python.exe`. If cache writes are restricted, add `-p no:cacheprovider` to pytest and `--no-cache` to Ruff.

Verified on 2026-09-08: all 16 tests pass and Ruff checks pass. Update/delete explicitly roll back the lookup transaction before re-raising `MovieNotFoundError`; the API handler remains responsible for logging the 404. FastAPI dependencies use `Annotated`; a request-level test verifies the shared session and dependency cleanup. OpenAPI is unchanged after the dependency refactor. The unit tests do not require a live database. A separate Docker smoke check verified fresh startup, automatic migrations, health endpoints, Swagger, CRUD, and persistence after container recreation; see [verification results](docs/DOCKER_VERIFICATION.md).

The Docker sprint (ANT-5–ANT-11) is implemented in `feature/docker-sprint` and [PR #8](https://github.com/darkskieshavefallen/movie-recommendation-api/pull/8), pending review and acceptance. Each task has a separate commit.

See [project context](docs/PROJECT_CONTEXT.md) for the agreed sequence and Docker decisions, and [AGENTS.md](AGENTS.md) for contributor instructions.

---

## Roadmap

- [x] Project setup
- [x] Application configuration
- [x] PostgreSQL integration
- [x] SQLAlchemy Async ORM
- [x] Alembic migrations
- [x] ORM models
- [x] Pydantic schemas
- [x] Repository layer
- [x] Service layer
- [x] Dependency Injection
- [x] REST API endpoints
- [x] Validation and exception handling
- [x] Update movie endpoint
- [x] Delete movie endpoint
- [x] Initial service unit tests
- [x] Resolve transaction-contract test failures
- [ ] Integration tests
- [x] Logging
- [x] Docker
- [ ] CI/CD
- [ ] External movie API integration
- [ ] Recommendation engine
- [ ] React frontend

---

## License

This project is licensed under the MIT License.
