FROM python:3.13-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1

# Install dependencies before copying source code to reuse this build layer.
COPY pyproject.toml README.md ./
RUN pip install -e ".[dev]"

COPY app/ ./app/
COPY tests/ ./tests/
COPY alembic/ ./alembic/
COPY alembic.ini ./

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
