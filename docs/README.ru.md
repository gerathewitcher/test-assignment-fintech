**Язык:** [English](../README.md) | Русский

## Задание

Полное описание задания:
- English: `test-assignment.en.md`
- Русский: `test-assignment.ru.md`

## Локальная разработка

Предварительные требования:

- `uv` (обязательно): https://docs.astral.sh/uv/getting-started/installation/
- `task` (опционально, для команд из Taskfile): https://taskfile.dev/installation/

1. Поднимите локальный PostgreSQL (PostGIS):

```bash
docker compose up -d db
```

2. Примените миграции:

```bash
uv run alembic upgrade head
```

3. (Опционально) Заполните БД тестовыми данными (организации/здания в Нью-Йорке):

```bash
task db-seed
task db-seed-small
task db-seed-medium
task db-seed-large
task db-reset
```

Прямой запуск скриптов:

```bash
uv run python scripts/seed_dev_db.py --profile medium --reset
uv run python scripts/reset_dev_db.py
```

4. Запустите интеграционные тесты:

```bash
task run-integration-tests
```

5. Запустите приложение:

```bash
uv run start-app
```

Базовый URL API:

```text
http://localhost:8000
```

## Полный запуск в Docker

Запуск полного стека (app + PostGIS):

```bash
docker compose up --build -d
```

## Документация API

После запуска приложения доступны:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- OpenAPI schema: `http://localhost:8000/openapi.json`

## Аутентификация

Все запросы к API должны содержать статический API ключ в заголовке `Authorization`.

Пример:

```bash
curl -H "Authorization: Bearer dev-static-api-key" \
  "http://localhost:8000/api/v1/directory/building"
```

API ключ задается через переменную окружения `API_KEY` (см. `src/config.py`).
