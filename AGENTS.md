# Movie Recommendation API

## Goal

Build a production-style backend service using FastAPI.

## Tech Stack

- Python 3.13
- FastAPI
- SQLAlchemy 2
- Alembic
- PostgreSQL
- Pydantic v2
- httpx
- pytest

## Architecture_MVP

app/
│
├── api/
├── services/
├── repositories/
├── models/
├── schemas/
├── integrations/
├── core/
│
tests/
alembic/
README.md
AGENTS.md
.gitignore
pyproject.toml

## Rules

- Always use type hints.
- Follow PEP 8.
- Keep controllers thin.
- Put business logic into services.
- Use repositories for database access.
- Explain architectural decisions before making significant changes.
- Never introduce unnecessary dependencies.
- Prefer readability over cleverness.- Никогда не используйте os.getenv() напрямую.
- Доступ ко всем настройкам должен осуществляться через app.core.settings.
- Настройки должны загружаться только один раз с использованием фабрики lru_cache.
