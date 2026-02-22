**Язык:** [English](../README.md) | Русский

## Задание

Полное описание задания:
- English: `test-assignment.en.md`
- Русский: `test-assignment.ru.md`

## Локальная разработка

Предварительные требования:

- `uv` (обязательно): https://docs.astral.sh/uv/getting-started/installation/
- `task` (опционально, для команд из Taskfile): https://taskfile.dev/installation/

1. Создайте `.env` на основе `.env.example`:

```bash
cp .env.example .env
```

2. Поднимите локальный PostgreSQL (PostGIS):

```bash
docker compose up -d db
```

3. Примените миграции:

```bash
uv run alembic upgrade head
```

4. (Опционально) Заполните БД тестовыми данными (организации/здания в Нью-Йорке):

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

5. Запустите интеграционные тесты:

```bash
task run-integration-tests
```

6. Запустите приложение:

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
