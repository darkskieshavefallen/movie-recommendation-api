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
- Test-ready architecture using pytest

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

## Getting Started

Prerequisites: Python 3.13 and a running PostgreSQL server. Docker support is planned but is not yet implemented. Run the commands below from the repository root.

### 1. Clone the repository

```bash
git clone <repository-url>
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

On Windows, use `.venv\Scripts\python.exe`. If cache writes are restricted, add `-p no:cacheprovider` to pytest and `--no-cache` to Ruff.

Verified on 2026-09-07: all 14 tests pass and Ruff checks pass. Update/delete explicitly roll back the lookup transaction before re-raising `MovieNotFoundError`; the API handler remains responsible for logging the 404. FastAPI dependencies use `Annotated`; a request-level test verifies the shared session and dependency cleanup. OpenAPI is unchanged after the dependency refactor. These checks do not verify a live PostgreSQL connection or full API CRUD.

The current sprint starts with the transaction contract and lint fixes (ANT-5, ANT-6), followed by Dockerfile, `.dockerignore`, migration entrypoint, and Compose with PostgreSQL (ANT-7–ANT-10). The final step is a full startup/CRUD/persistence check and updated launch documentation (ANT-11). Work is grouped into one feature branch and one PR.

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
- [ ] Docker
- [ ] CI/CD
- [ ] External movie API integration
- [ ] Recommendation engine
- [ ] React frontend

---

## License

This project is licensed under the MIT License.
