# Решение тестового задания на позицию Python-разработчика

**Язык:** [English](../README.md) | Русский

## Задание

Полное описание задания:
- [English](test-assignment.en.md)
- [Русский](test-assignment.ru.md)

---

## Чеклист задания

- [x] Стек FastAPI + Pydantic + SQLAlchemy + Alembic
- [x] Статический API ключ для всех API-эндпоинтов
- [x] Справочник организаций с:
  - [x] названием
  - [x] несколькими номерами телефонов
  - [x] привязкой к зданию
  - [x] несколькими видами деятельности (many-to-many)
- [x] Справочник зданий с адресом и геокоординатами (PostGIS)
- [x] Дерево деятельностей с ограничением глубины до 3 уровней (триггер в БД)
- [x] API методы:
  - [x] список организаций
  - [x] фильтрация организаций по зданию
  - [x] фильтрация организаций по виду деятельности
  - [x] поиск по виду деятельности с дочерними видами
  - [x] поиск организаций по названию
  - [x] организации в радиусе от точки
  - [x] организации в прямоугольной области (bbox)
  - [x] информация об организации по id
  - [x] список зданий
- [x] OpenAPI + Swagger UI + ReDoc
- [x] Docker-упаковка приложения и БД
- [x] Интеграционные тесты для основных сценариев и фильтров

---

## Локальная разработка

Предварительные требования:

- `uv` (обязательно): https://docs.astral.sh/uv/getting-started/installation/
- `task` (опционально, для команд из Taskfile): https://taskfile.dev/installation/

1. Склонируйте репозиторий:

```bash
git clone https://github.com/gerathewitcher/test-assignment-fintech
cd test-assignment-fintech
```

2. Создайте `.env` на основе `.env.example`:

```bash
cp .env.example .env
```

3. Поднимите локальный PostgreSQL (PostGIS):

```bash
docker compose up -d db
```

4. Примените миграции:

```bash
uv run alembic upgrade head
```

5. (Опционально) Заполните БД тестовыми данными (организации/здания в Нью-Йорке):

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

6. Запустите интеграционные тесты:

```bash
task run-integration-tests
```

7. Запустите приложение:

```bash
uv run start-app
```

Базовый URL API:

```text
http://localhost:8000
```

---

## Полный запуск в Docker

Запуск полного стека (app + PostGIS):

```bash
docker compose up --build -d
```

---

## Документация API

После запуска приложения доступны:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- OpenAPI schema: `http://localhost:8000/openapi.json`

---

## Аутентификация

Все запросы к API должны содержать статический API ключ в заголовке `Authorization`.

Пример:

```bash
curl -H "Authorization: Bearer dev-static-api-key" \
  "http://localhost:8000/api/v1/directory/building"
```

API ключ задается через переменную окружения `API_KEY` в файле `.env`
