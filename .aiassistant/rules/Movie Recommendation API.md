---
apply: always
---

# Project: movie-recommendation-api

## Tech Stack

- Python 3.13
- FastAPI
- SQLAlchemy 2.x Async ORM
- PostgreSQL
- Alembic
- Pydantic v2
- pydantic-settings
- pytest
- Ruff

---

## Architecture

```
API
 ↓
Service
 ↓
Repository
 ↓
Database
```

Project structure:

```
app/
├── api/
├── services/
├── repositories/
├── models/
├── schemas/
├── core/
```

Always preserve this architecture.

---

## Development Rules

- Analyze the existing implementation before making changes.
- Modify only the files required for the task.
- Keep routers thin.
- Business logic belongs only in services.
- Repositories should contain only database operations.
- Do not place business logic into repositories.
- Repository must never call commit() or rollback().
- Transaction management belongs only in services.
- Use dependency injection.
- Prefer async code.
- Preserve the existing project style and naming.
- Do not introduce new architecture without necessity.
- If the task is ambiguous, ask instead of guessing.

---

## Code Style

- Use type hints everywhere.
- Use Google-style English docstrings for every public class and method.
- Follow existing naming conventions.
- Prefer readability over clever code.
- Do not perform unrelated refactoring.

---

## Testing

- Use pytest.
- Use pytest-asyncio for async tests.
- Use AsyncMock for async dependencies.
- Unit tests must not use a real database.
- Follow the Arrange → Act → Assert pattern.

---

## Working Style

Before implementing:

- Briefly explain the implementation plan.

After implementing:

- Explain what changed.
- Explain why the solution matches the current architecture.
- Run:
  - `ruff check`
  - `pytest` (when applicable)

---

## Context Efficiency

- Do not analyze the entire project for small localized changes.
- Read only the files required for the current task.
- Reuse previously gathered context whenever possible.
- Avoid rereading README and AGENTS.md unless necessary.

---

## Educational Mode

This project is built for learning.

When implementing non-trivial code:

- Briefly explain architectural decisions.
- Explain important trade-offs.
- Do not write long tutorials.