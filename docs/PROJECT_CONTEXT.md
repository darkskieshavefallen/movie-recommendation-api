# Контекст проекта и текущий спринт

Обновлено: 2026-09-10. Факты ниже — снимок состояния, перед изменениями перепроверь их.

## Цель и состояние

Учебный backend рекомендаций фильмов. Сейчас реализован CRUD фильмов; интеграция с внешним кино-API и сам recommendation engine относятся к будущей работе.

Стек: Python 3.13, FastAPI, Pydantic v2, SQLAlchemy async, asyncpg, PostgreSQL, Alembic, pytest, Ruff. Есть DI, сервисы/репозитории, обработчики ошибок и централизованное логирование. Логирование влито в main через PR #7, локальный HEAD при проверке — `70f3fa9`.

Текущая точка: PR #8 (ANT-5–ANT-11) влит 8 сентября, `origin/main` — `feb0e1a`. Начат Sprint 16 — CI and Docker image publishing, общая ветка `feature/ci-sprint` от этого main, общий draft PR #9: https://github.com/darkskieshavefallen/movie-recommendation-api/pull/9. ANT-12–ANT-14 опубликованы отдельными коммитами и проверены на GitHub runner. Текущее поручение — ANT-15: публикация проверенного образа в GHCR. Пользователь просит двигаться строго по задачам Linear и объяснять новые понятия на примерах.

ANT-12: опубликован коммит `13352d5`, добавлен `.github/workflows/ci.yml` для PR в main и push в main: Ubuntu, Python 3.13, установка `.[dev]`, Ruff и pytest. Настройки заданы явно в env без секретов; PostgreSQL не запускается, доступ к БД подменён в существующих тестах. Локально, в копии без `.env` и на чистом GitHub runner проверки прошли: 16 тестов, Ruff. Удалённый запуск: https://github.com/darkskieshavefallen/movie-recommendation-api/actions/runs/34412395887. Ссылки на коммит, ветку и PR прикреплены к Linear. Задача не закрывалась.

ANT-13: после тестов в тот же job добавлены определение `CI_IMAGE=movie-recommendation-api:<git rev-parse HEAD>`, `docker build --tag "$CI_IMAGE" .` и проверка доступности образа через `docker image inspect`. Тег передаётся следующим шагам через `GITHUB_ENV`. Сборка использует существующие Dockerfile и .dockerignore; образ доступен следующему шагу в локальном Docker runner без пересборки. Для PR тег соответствует фактически проверяемому merge-коммиту GitHub. Ошибки сборки/inspect не игнорируются. README описывает этот контракт. Проверены синтаксис YAML (Psych), shell-команд (`bash -n`) и `git diff --check`; результат удалённой сборки после отправки коммита фиксируется в PR #9 и Linear. Запуск с PostgreSQL — ANT-14, публикация образа — последующие задачи, пока не реализованы.

Docker Desktop установлен и запущен при проверке ANT-7. В терминале агента команда доступна как `/Users/anton/.docker/bin/docker`; для сборки потребовалось добавить `/Applications/Docker.app/Contents/Resources/bin` в PATH команды. До появления .dockerignore использован временный tar-контекст только из Dockerfile и выбранных отслеживаемых файлов, без .env, .venv и IDE-артефактов. Запуск API с БД в контейнере ещё не проверялся. В ANT-7 прикреплены коммит, ветка и PR, оставлен русский отчёт; задача не закрывалась.

## Выявленные вопросы

- ANT-15: после успешного smoke на push в main checks job экспортирует ровно проверенный CI_IMAGE через docker save и upload-artifact (retention 1 day). Отдельный publish job с единственным `packages: write` скачивает artifact, делает docker load, сверяет image ID с output checks job, назначает `ghcr.io/darkskieshavefallen/movie-recommendation-api:sha-<checked_sha>` и отправляет через GITHUB_TOKEN без пересборки. Затем `docker buildx imagetools inspect` читает registry digest; image@digest пишется в job summary и outputs. В PR оба шага экспорта и весь publish job пропускаются, поэтому запись в GHCR возможна только после успешного push в main. Локально проверяем YAML/shell и PR skip; реальную аутентификацию, push, digest и создаваемый package можно подтвердить только после merge, который требует отдельного поручения пользователя.
- ANT-14 опубликована коммитом `a0534d8`; CI https://github.com/darkskieshavefallen/movie-recommendation-api/actions/runs/34414022339 прошёл за 52 секунды. PostgreSQL и API стали healthy, expected/actual Alembic revision — `474e3311e20a`, /health и /health/db вернули 200. Cleanup удалил оба контейнера, сеть и volume. Ссылки прикреплены к Linear, PR #9 остаётся draft.

- ANT-14: текущее поручение после ANT-13 — проверка запуска с PostgreSQL в CI. Добавлены `.github/compose.ci.yml` и `.github/scripts/verify-smoke.sh`; workflow запускает уже собранный CI_IMAGE без пересборки, с исходным entrypoint и отдельной PostgreSQL 16. Проект `movie-ci-<run-id>-<attempt>` изолирует сеть и disposable volume, порты не публикуются, .env не читается. `up --wait --wait-timeout 120` ожидает healthchecks; скрипт сравнивает реальные ревизии БД с Alembic heads образа и требует 200 от /health и /health/db. На сбое выводятся логи, always-cleanup удаляет только ресурсы CI-проекта. Локально прошли Compose config, YAML parsing, bash -n и пять проверок скрипта с подменённым Docker (успех, несовпадение ревизии, пустой head, ошибка БД, ошибка HTTP); ошибки сохраняют ненулевой код. Локальный Docker daemon выключен; реальные результаты GitHub runner записываются в PR #9 и Linear после отправки. CRUD и публикация образа не входят в ANT-14.
- ANT-13 опубликована коммитом `c7b4182`; CI https://github.com/darkskieshavefallen/movie-recommendation-api/actions/runs/34413058681 прошёл за 39 секунд: Ruff, 16 тестов, сборка и inspect. Тег совпал с SHA checkout `778a33b9c627eadce5e46d4f255c7167b687b972`, ID собранного образа совпал с результатом inspect. Ссылки прикреплены к Linear, общий PR #9 остаётся draft.

- 8 сентября, ANT-11: на свежем изолированном Compose-проекте movie-ant11-20260908 (порт 18000, без .env) проверены startup, healthcheck, автоматическая миграция 474e3311e20a, /health, /health/db, Swagger HTML/OpenAPI, полный CRUD и сохранность изменённой записи после down/up без удаления volume. После проверки тестовая запись удалена, тестовые контейнеры остановлены, volume сохранён. Основной проект на 8000 не затронут. Локальные pytest — 16 passed, Ruff проходит. README содержит Docker/local запуск, конфигурацию, остановку, volume и ограничения. Подробности — docs/DOCKER_VERIFICATION.md. Исторические ограничения предыдущих этапов ниже относятся к моменту их выполнения.

- 8 сентября, ANT-10: добавлен docker-compose.yml с сервисами api/db, PostgreSQL 16, healthcheck и depends_on: service_healthy, volume postgres_data. Docker-БД использует отдельные учебные реквизиты из Compose; DATABASE_URL в контейнере указывает на db, локальный .env не менялся. Порт API опубликован на 127.0.0.1:8000; порт БД на Mac не опубликован. Проверены compose config --quiet и up --build -d --wait: PostgreSQL healthy, автоматическая миграция 474e3311e20a применена, Uvicorn PID 1. /health, /health/db и /movies/ вернули 200 (список пуст). Контейнеры оставлены работающими; volume movie-recommendation-api_postgres_data создан. Полный CRUD и сохранность данных после перезапуска — ANT-11.

- 8 сентября, ANT-9: добавлен исполняемый docker-entrypoint.sh с `set -e`, `alembic upgrade head` и `exec "$@"`, подключён ENTRYPOINT в Dockerfile. Реальный запуск выявил ошибку регистрации editable-пакета до копирования исходников (ModuleNotFoundError: app); исправлено повторной регистрацией `pip install --no-deps -e .` после COPY исходников. Образ ant-9 собран, 16 тестов проходят локально и в контейнере, Ruff проходит. Тесты проверяют порядок, код ошибки, аргументы с пробелами и сохранение PID через exec. Реальный Alembic при недоступной тестовой БД завершает контейнер кодом 1, Uvicorn не запускается. Успешная миграция на живой БД в контейнере ещё не проверялась; Compose и отдельный контейнер миграций не добавлялись.

- 8 сентября, ANT-8: добавлен .dockerignore для .env и локальных вариантов (с сохранением .env.example), Git/IDE/assistant-файлов, venv, Python-кэшей, логов и результатов сборки. Обычная сборка из корня проекта успешна: `movie-recommendation-api:ant-8`. Временная диагностическая сборка проверила отсутствие локальных файлов в фактическом контексте и доступность исходников, тестов, миграций и метаданных. Следующий этап — ANT-9 (entrypoint и миграции); Dockerfile в ANT-8 не менялся.

- 7 сентября, ANT-5: сервис явно выполняет rollback при MovieNotFoundError в update/delete, завершая транзакцию поиска перед повторным выбросом исключения. Логирование 404 остаётся в HTTP-обработчике. Все 13 unit-тестов проходят; тесты отсутствующего фильма также проверяют отсутствие refresh и ошибочных логов. Следующий шаг — ANT-6. Задача ожидает приёмки пользователя.
- 7 сентября, ANT-6: Ruff 0.16.6 проходит. В pyproject.toml явно дополнены проверки E4/E7/E9/F/I/UP/B, Alembic обозначен сторонним пакетом. Depends переведён на Annotated во всех зависимостях и маршрутах, исправлены импорты и аннотации Python 3.13. Все 14 тестов проходят, включая проверку общей сессии сервиса/репозитория и её очистки. OpenAPI до/после совпадает; генерация SQL Alembic offline успешна. Следующий шаг — ANT-7; ANT-6 ожидает приёмки пользователя.
- 5 сентября PostgreSQL отвечал на localhost:5432, но роль `movie_app` отсутствовала. Это исторический результат, не доказательство текущего состояния. База по конфигурации называлась `movie_recommendation`.
- 7 сентября локальный запуск подтверждён: PostgreSQL 16 запущен через Homebrew; созданы отсутствовавшие роль `movie_app` и БД `movie_recommendation` с настройками из `.env`. Применена миграция `474e3311e20a` (`alembic upgrade head`). Uvicorn запущен через `.venv/bin/python -m uvicorn app.main:app --reload`; `/health`, `/health/db`, `/movies/` и `/docs` вернули 200, список фильмов пуст. Сценарии записи CRUD не проверялись. Следующий шаг — ANT-5, затем ANT-6 перед Docker.
- PyCharm сообщает системный SDK Python 3.13.15; команды проверок и запуска выполнялись через `.venv/bin/python` согласно AGENTS.md. Настройки IDE не менялись.
- `/health` возвращал 200 при проверке внутри процесса; интеграционных тестов БД/API в проверенном наборе нет.
- При последней проверке пользовательские изменения: `.idea/modules.xml`, `.idea/vcs.xml`.

## Linear

Проект: https://linear.app/dshf/project/movie-recommendation-api-1f35c4e4ad7e/issues

Все семь задач созданы с критериями готовности и зависимостями. Календарные cycles, сроки и исполнители не назначены. Номера 15.2–15.6 — учебные этапы; после последнего решения пользователя они не требуют отдельных PR.

| Задача | Работа | Зависимость |
| --- | --- | --- |
| ANT-5 | Согласовать rollback и исправить два тестовых падения | — |
| ANT-6 | Привести Ruff к зелёному состоянию | — |
| ANT-7 | 15.2: базовый Dockerfile | ANT-5, ANT-6 |
| ANT-8 | 15.3: .dockerignore | ANT-7 |
| ANT-9 | 15.4: entrypoint и миграции | ANT-8 |
| ANT-10 | 15.5: Compose с PostgreSQL | ANT-9 |
| ANT-11 | 15.6: полный запуск, smoke-проверка и README | ANT-10 |

## Организация CI-спринта

Общая ветка — `feature/ci-sprint`. По уточнению пользователя после каждой выполненной задачи обязательно создаём отдельный коммит с ANT-идентификатором, отправляем ветку и поддерживаем общий draft PR спринта, без повторного согласования. ANT-12 фиксируется отдельным коммитом; после публикации проверяем Actions на GitHub и прикрепляем ссылки в Linear. Merge и закрытие задач остаются отдельным поручением пользователя.

## Организация Docker-спринта (завершён, история)

Одна ветка `feature/docker-sprint` от `main` и один PR на весь текущий спринт подготовки и Docker. По решению пользователя на каждую задачу ANT-5–ANT-11 создаётся отдельный коммит. После реализации задачи в Linear добавляется комментарий по-русски с результатами проверок и ссылкой на коммит.

Сохраняем поэтапное объяснение каждого нового файла. Общий draft PR открыт в начале спринта: https://github.com/darkskieshavefallen/movie-recommendation-api/pull/8. Все дальнейшие коммиты отправляем в `feature/docker-sprint`, обновляя описание PR по мере выполнения задач. В PR перечислены все семь задач Linear. После завершения спринта передаём PR на ревью в отдельную задачу Codex, затем дорабатываем ту же ветку. Merge и закрытие задач — по поручению пользователя.

## Docker: согласованные решения

- Сначала простой development-образ `python:3.13-slim`, WORKDIR `/app`, `PYTHONUNBUFFERED=1`, порт 8000 и запуск `uvicorn app.main:app --host 0.0.0.0 --port 8000`.
- Изучить слои и кэширование. Файлы, нужные для установки зависимостей, копировать до остального исходного кода. План использует `pip install -e ".[dev]"`; проверь требования setuptools, README и обнаружения пакетов реальной сборкой. Не копируй непроверенный пример из старого чата буквально.
- Затем .dockerignore, исключающий .env, venv, Git/IDE-файлы, кэши и прочие локальные артефакты.
- Entrypoint применяет `alembic upgrade head`, прекращает запуск при ошибке и передаёт управление основному процессу через exec.
- Compose содержит только api и db. PostgreSQL использует именованный volume `postgres_data` и healthcheck; api ждёт готовности БД.
- Compose передаёт DATABASE_URL с хостом `db`. Для локального запуска остаётся `localhost`; вручную переключать .env между режимами не нужно.
- Пока без отдельного контейнера миграций, Redis, Nginx, Celery, production Compose, bind mounts, multi-stage и преждевременной оптимизации.
- Итоговая проверка: `docker compose up`, автоматические миграции, `/health`, `/health/db`, Swagger и CRUD. Данные сохраняются после перезапуска. Проверки изменения данных выполняй на отдельной тестовой БД/данных.
- README должен описывать воспроизводимый запуск и все реальные предпосылки, включая Docker и создание локальной конфигурации, если она требуется.
