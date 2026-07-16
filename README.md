# Movie Recommendation API

> A learning project focused on building a production-style backend using FastAPI and modern Python technologies.

## Tech Stack

- Python 3.13
- FastAPI
- PostgreSQL
- SQLAlchemy 2.x
- Alembic
- Pydantic v2
- Pydantic Settings
- HTTPX
- AsyncPG
- Pytest
- Ruff

## Project Structure

```text
app/
├── api/             # FastAPI routers
├── core/            # Configuration and infrastructure
├── integrations/    # External APIs
├── models/          # SQLAlchemy models
├── repositories/    # Data access layer
├── schemas/         # Pydantic schemas
└── services/        # Business logic

tests/
alembic/
```

## Getting Started

Create a virtual environment:

```bash
python -m venv .venv
```

Install dependencies:

```bash
pip install -e ".[dev]"
```

Create a local configuration file:

```bash
cp .env.example .env
```

Run the application:

```bash
uvicorn app.main:app --reload
```

Swagger UI:

```
http://localhost:8000/docs
```

## Project Goals

- Learn modern backend development with FastAPI
- Build a clean layered architecture
- Integrate external movie APIs
- Work with PostgreSQL and Alembic
- Cover the application with tests
- Containerize the application with Docker
- Build a React frontend