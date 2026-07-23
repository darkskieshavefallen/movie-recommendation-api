---
apply: always
---

Project: movie-recommendation-api

Architecture:

- FastAPI
- SQLAlchemy 2.x async
- Alembic
- PostgreSQL
- Pydantic v2

Project structure:

app/
    api/
    services/
    repositories/
    models/
    schemas/
    core/

Rules:

- Keep routers thin.
- Business logic belongs only in services.
- Repositories should contain only database operations.
- Do not place business logic into repositories.
- Use dependency injection.
- Prefer async code.
- Keep naming consistent with the existing project.
- Preserve project architecture.
- Every public class and method should have a Google-style English docstring.