# Контекст проекта

Обновлено: 2026-09-17. Это краткий снимок актуального состояния. История
изменений хранится в Git, GitHub PR и Linear.

## Назначение

Movie Recommendation API — учебный backend на FastAPI для локального каталога
фильмов и детерминированных рекомендаций. Основной продуктовый контур работает
без внешнего провайдера:

- CRUD фильмов в PostgreSQL;
- явно запускаемый fictional demo-каталог;
- рекомендации по общим жанрам и близости года выпуска;
- опциональный read-only поиск TMDB без импорта данных в локальную БД;
- OpenAPI, health/readiness endpoints, Docker и CI.

React frontend будет разрабатываться в отдельном репозитории. Этот репозиторий
остаётся backend-сервисом и источником HTTP-контракта.

## Архитектура и стек

Основная граница: `API -> Service -> Repository -> PostgreSQL`.

- Router отвечает за HTTP, зависимости и сериализацию.
- Service содержит бизнес-логику и границы транзакций.
- Repository выполняет доступ к данным и не делает `commit`.
- Доменные исключения преобразуются в HTTP-ответы централизованно.

Стек: Python 3.13, FastAPI, Pydantic v2, async SQLAlchemy, asyncpg,
PostgreSQL 16, Alembic, pytest, Ruff, Docker Compose и GitHub Actions.

## Текущее состояние

В рамках учебного проекта и MVP бэкенд готов.

## Конфигурация

Минимальная локальная конфигурация описана в `.env.example`. Важные настройки:

- `DATABASE_URL` — PostgreSQL connection URL;
- `CORS_ALLOWED_ORIGINS` — JSON-список явных frontend origins;
- `TMDB_ENABLED=false` — внешний каталог по умолчанию выключен;
- `TMDB_READ_ACCESS_TOKEN` обязателен только при включённом TMDB.

Настоящие credentials нельзя коммитить. `/health` подтверждает только жизнь
процесса; готовность PostgreSQL проверяет `/health/db`.

## Проверки

Быстрый набор:

```bash
.venv/bin/python -m ruff check .
.venv/bin/python -m pytest -q -m "not integration"
```

PostgreSQL integration suite требует отдельную disposable-базу и переменную
`INTEGRATION_DATABASE_URL`; подробный safety-контракт находится в
`docs/POSTGRESQL_INTEGRATION_TESTS.md`. CI запускает quality и integration jobs
независимо, а Docker build/smoke — только после их успеха.

Итоговые результаты конкретного изменения фиксируются в соответствующем PR и
Linear-задаче, чтобы этот документ не превращался в журнал запусков.

## Ограничения и следующие шаги

- Локальные рекомендации не используют TMDB или ML/AI.
- ML/AI поверх данных TMDB не добавляется без письменного разрешения
  провайдера, смены провайдера либо полного отделения интеграции; подробности —
  в `docs/EXTERNAL_MOVIE_API.md`.
- Автоматический demo seed намеренно не выполняется при startup или миграциях.
- Ближайший продуктовый этап после ANT-38 — React frontend в отдельном
  репозитории; server deployment остаётся более поздним этапом.

## Рабочие ссылки

- Linear project: https://linear.app/dshf/project/movie-recommendation-api-1f35c4e4ad7e/issues
- GitHub repository: https://github.com/darkskieshavefallen/movie-recommendation-api
- Внешний каталог: `docs/EXTERNAL_MOVIE_API.md`
- Локальные рекомендации: `docs/LOCAL_RECOMMENDATIONS.md`
- Integration tests: `docs/POSTGRESQL_INTEGRATION_TESTS.md`
- Docker/CI: `docs/DOCKER_VERIFICATION.md`, `docs/CI_VERIFICATION.md`
