# Movie Recommendation API

## Goal

Build a production-ready REST API for movie recommendations using modern Python backend practices.

---

## Tech Stack

- Python 3.13
- FastAPI
- SQLAlchemy 2.x (Async ORM)
- Alembic
- PostgreSQL
- Pydantic v2
- pydantic-settings
- httpx
- pytest
- Ruff

---

## Project Structure

```
app/
│
├── api/              # FastAPI routers and dependencies
├── core/             # Configuration and database
├── integrations/     # External services
├── models/           # SQLAlchemy ORM models
├── repositories/     # Data access layer
├── schemas/          # Pydantic DTOs
├── services/         # Business logic
│
tests/
alembic/
README.md
AGENTS.md
pyproject.toml
.gitignore
```

---

## Architecture

The project follows a layered architecture.

```
HTTP Request
        │
        ▼
API (Controllers)
        │
        ▼
Services
        │
        ▼
Repositories
        │
        ▼
Database
```

### Layer responsibilities

#### API

- Receive HTTP requests.
- Validate input using Pydantic.
- Call services.
- Return HTTP responses.
- No business logic.

#### Services

- Implement business logic.
- Orchestrate repository calls.
- Manage transactions (`commit()` / `rollback()`).
- Convert ORM models into Pydantic schemas.

#### Repositories

- Execute database queries.
- Work only with SQLAlchemy ORM models.
- Never contain business logic.
- Never call `commit()` or `rollback()`.

---

## Database Rules

- Use SQLAlchemy 2.x async API.
- Use `AsyncSession`.
- Repositories use `flush()` but never `commit()`.
- Transactions are controlled by the service layer.
- Use Alembic for all schema changes.

---

## Configuration Rules

- Never use `os.getenv()` directly.
- Access configuration only through `app.core.settings`.
- Settings must be initialized only once using `lru_cache`.

---

## Code Style

- Follow PEP 8.
- Always use type hints.
- Use modern Python typing (`list`, `dict`, `| None`).
- Prefer descriptive names over abbreviations.
- Keep functions focused on a single responsibility.
- Prefer readability over cleverness.

---

## Documentation

- All docstrings must be written in English.
- Explain architectural decisions before making significant changes.

---

## General Rules

- Keep controllers thin.
- Keep repositories independent from Pydantic.
- Keep services independent from HTTP.
- Avoid unnecessary dependencies.
- Prefer composition over inheritance.