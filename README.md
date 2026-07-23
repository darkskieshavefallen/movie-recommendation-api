![Python](https://img.shields.io/badge/Python-3.13-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-Latest-009688)
![License](https://img.shields.io/badge/license-MIT-green)

# Movie Recommendation API

> A learning project focused on building a production-ready REST API using FastAPI, PostgreSQL, and modern Python development practices.

---

## Features

- Async REST API built with FastAPI
- Layered architecture (API → Service → Repository)
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
API (Controllers)
      │
      ▼
Services
      │
      ▼
Repositories
      │
      ▼
PostgreSQL
```

### Project Structure

```text
app/
├── api/             # FastAPI routers and dependencies
├── core/            # Configuration and database
├── integrations/    # External services
├── models/          # SQLAlchemy ORM models
├── repositories/    # Database access layer
├── schemas/         # Pydantic DTOs
├── services/        # Business logic

tests/               # Unit and integration tests
alembic/             # Database migrations
```

---

## Getting Started

### 1. Clone the repository

```bash
git clone <repository-url>
cd movie-recommendation-api
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

### 3. Activate the virtual environment

Windows:

```bash
.venv\Scripts\activate
```

Linux/macOS:

```bash
source .venv/bin/activate
```

### 4. Install dependencies

```bash
pip install -e ".[dev]"
```

### 5. Create a local configuration file

```bash
cp .env.example .env
```

### 6. Apply database migrations

```bash
alembic upgrade head
```

### 7. Run the application

```bash
uvicorn app.main:app --reload
```

---

## API Documentation

Swagger UI

```text
http://localhost:8000/docs
```

ReDoc

```text
http://localhost:8000/redoc
```

---

## Development Principles

- Layered architecture
- Thin controllers
- Business logic in services
- Data access in repositories
- Async-first approach
- Type hints everywhere
- PEP 8 compliant code
- Small, focused commits

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
- [ ] Dependency Injection
- [ ] REST API endpoints
- [ ] Validation and exception handling
- [ ] Unit tests
- [ ] Integration tests
- [ ] Logging
- [ ] Docker
- [ ] CI/CD
- [ ] External movie API integration
- [ ] Recommendation engine
- [ ] React frontend