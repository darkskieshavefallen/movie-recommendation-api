![Python](https://img.shields.io/badge/Python-3.13-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.x-009688)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-blue)
[![CI](https://github.com/darkskieshavefallen/movie-recommendation-api/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/darkskieshavefallen/movie-recommendation-api/actions/workflows/ci.yml)
![License](https://img.shields.io/badge/license-MIT-green)

# Movie Recommendation API

[English version](README.md)

Учебный backend на FastAPI, async SQLAlchemy, PostgreSQL, Alembic, Pydantic v2
и pytest. В нём есть CRUD локальных фильмов, явно запускаемый каталог
вымышленных demo-фильмов и детерминированные локальные рекомендации. Поиск в
TMDB — опциональная возможность: локальный API запускается и работает без
TMDB-токена.

React frontend планируется в отдельном репозитории. Этот репозиторий остаётся
backend-сервисом и источником HTTP-контракта.

## Архитектура

```mermaid
flowchart LR
    UI[React frontend<br/>отдельный репозиторий] -->|HTTP + настроенный CORS| API[FastAPI routers]
    API --> S[Services<br/>бизнес-логика и транзакции]
    S --> R[Repositories<br/>доступ к данным]
    R --> DB[(PostgreSQL)]
    API --> ES[External movie service]
    ES -. только при включении .-> TMDB[TMDB API]
```

```mermaid
flowchart TD
    Start[Запуск приложения] --> Enabled{TMDB_ENABLED?}
    Enabled -->|false| Local[Локальный каталог, рекомендации,<br/>health и документация доступны]
    Local --> Disabled[Внешний поиск возвращает безопасный 503]
    Enabled -->|true| Token{Токен настроен?}
    Token -->|нет| Refuse[Валидация конфигурации останавливает запуск]
    Token -->|да| Client[Управляемый async TMDB-клиент]
```

Сохраняется граница `API -> Service -> Repository -> PostgreSQL`. Router
отвечает за HTTP, service — за бизнес-логику и транзакции, repository — за
доступ к данным без `commit`.

## Быстрый запуск через Docker

Нужны Git и Docker Desktop либо Docker Engine с Compose plugin. Учётная запись
и токен TMDB для локального ядра не требуются.

```bash
git clone https://github.com/darkskieshavefallen/movie-recommendation-api.git
cd movie-recommendation-api
cp .env.example .env
docker compose up --build
```

Compose запускает PostgreSQL 16, ждёт его готовности, применяет все миграции
Alembic и поднимает API на `http://127.0.0.1:8000`.

- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc
- Liveness: http://127.0.0.1:8000/health
- Готовность БД: http://127.0.0.1:8000/health/db

Остановка с сохранением данных:

```bash
docker compose down
```

`docker compose down --volumes` также удаляет development-volume PostgreSQL.

## Локальный запуск Python

Нужны Python 3.13 и PostgreSQL 16.

```bash
python3.13 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
cp .env.example .env
# Настройте DATABASE_URL для локального PostgreSQL.
.venv/bin/alembic upgrade head
.venv/bin/python -m uvicorn app.main:app --reload
```

Настройки читаются из переменных окружения и локального `.env`. Настоящие
credentials нельзя коммитить. Полный шаблон находится в
[.env.example](.env.example).

## Опциональный поиск TMDB

По умолчанию TMDB отключён. Все локальные маршруты продолжают работать, а
`GET /external/movies/search` возвращает стабильный безопасный `503`.

Для read-only поиска задайте в `.env` оба значения:

```dotenv
TMDB_ENABLED=true
TMDB_READ_ACCESS_TOKEN=your_real_read_access_token
```

Токен отправляется только в заголовке Authorization провайдера. Внешние
результаты не импортируются в локальную БД. Условия провайдера, атрибуция,
ошибки и ограничение ML/AI описаны в
[docs/EXTERNAL_MOVIE_API.md](docs/EXTERNAL_MOVIE_API.md).

## CORS для отдельного frontend

По умолчанию разрешён стандартный локальный origin Vite; глобальный wildcard не
используется:

```dotenv
CORS_ALLOWED_ORIGINS=["http://localhost:5173"]
```

Несколько приложений задаются JSON-списком явных origin:

```dotenv
CORS_ALLOWED_ORIGINS=["http://localhost:5173","http://127.0.0.1:5173"]
```

Конфигурация отклоняет `*`, дубликаты и origin с credentials, path, query или
fragment.

## Основные маршруты

| Метод | Путь | Назначение |
| --- | --- | --- |
| `GET` | `/health` | Жив ли процесс |
| `GET` | `/health/db` | Доступен ли PostgreSQL |
| `GET` | `/movies/?offset=0&limit=100` | Стабильная страница по возрастанию ID |
| `POST` | `/movies/` | Создать локальный фильм |
| `GET` | `/movies/{movie_id}` | Получить локальный фильм |
| `PUT` | `/movies/{movie_id}` | Полностью обновить локальный фильм |
| `DELETE` | `/movies/{movie_id}` | Удалить локальный фильм |
| `GET` | `/movies/{movie_id}/recommendations?limit=5` | Локальные рекомендации |
| `GET` | `/external/movies/search?query=Alien` | Опциональный поиск TMDB |

Ограничения записи фильма согласованы в Pydantic и PostgreSQL:

- `title`: обрезаются внешние пробелы, длина 1–255 символов;
- `release_year`: 1888–2100;
- `genres`: не более 10 уникальных нормализованных значений, каждое до 50
  символов.

Некорректные данные возвращают `422` до обращения к repository. Список сохраняет
параметры `offset` и `limit` и явно сортируется по локальному ID, поэтому
пагинация детерминирована. Рекомендации используют только локальный PostgreSQL и
сортируются по числу общих жанров, разнице годов и локальному ID.

При обновлении со схемы до ANT-38 миграция удаляет только несовместимые
одноразовые demo/test-записи: фильмы с пустым названием или годом вне
1888–2100. Все валидные существующие строки сохраняются.

## Demo-каталог

Явная development-команда добавляет отсутствующие вымышленные фильмы и не
перезаписывает существующие пары title/year:

```bash
.venv/bin/python -m app.cli.seed_demo
```

Команда не подключена к startup или миграциям и отказывается работать с
нелокальной либо похожей на production базой.

## Проверки

Быстрые проверки не требуют PostgreSQL и TMDB-токена:

```bash
.venv/bin/python -m ruff check .
.venv/bin/python -m pytest -q -m "not integration"
```

Integration suite требует отдельную явно названную disposable-базу:

```bash
INTEGRATION_DATABASE_URL='postgresql+asyncpg://integration:integration@localhost/movie_recommendation_integration_test' \
  .venv/bin/python -m pytest -q -m integration
```

Integration-тесты применяют настоящие миграции и проверяют полный путь
`HTTP -> FastAPI -> Service -> Repository -> PostgreSQL`. Правила безопасности
и настройка описаны в
[docs/POSTGRESQL_INTEGRATION_TESTS.md](docs/POSTGRESQL_INTEGRATION_TESTS.md).

CI независимо запускает Ruff/unit и PostgreSQL integration tests. Docker
build/smoke начинается только после успеха обоих jobs. Публикация в GHCR
разрешена только после успешного push в `main`.

## Документация

- [Актуальный контекст проекта](docs/PROJECT_CONTEXT.md)
- [Контракт локальных рекомендаций](docs/LOCAL_RECOMMENDATIONS.md)
- [Решение по внешнему каталогу](docs/EXTERNAL_MOVIE_API.md)
- [Контракт PostgreSQL integration tests](docs/POSTGRESQL_INTEGRATION_TESTS.md)
- [Проверка Docker](docs/DOCKER_VERIFICATION.md)
- [Проверка CI и доставки образа](docs/CI_VERIFICATION.md)

## Roadmap

- [x] Async CRUD с PostgreSQL и Alembic
- [x] Docker, CI и проверенная доставка образа в GHCR
- [x] Опциональный внешний каталог
- [x] Локальные детерминированные рекомендации
- [x] PostgreSQL integration test suite
- [x] Стабилизация backend для отдельного frontend
- [ ] React frontend в отдельном репозитории
- [ ] Server deployment

## Лицензия

Проект распространяется по [MIT License](LICENSE).
