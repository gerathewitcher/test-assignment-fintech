# Test Assignment Solution for Python Developer Position

**Language:** English | [Русский](docs/README.ru.md)

## Assignment

Full assignment description:
- [English](docs/test-assignment.en.md)
- [Russian](docs/test-assignment.ru.md)

---

## Assignment Checklist

- [x] FastAPI + Pydantic + SQLAlchemy + Alembic stack
- [x] Static API key authorization for all API endpoints
- [x] Organizations directory with:
  - [x] name
  - [x] multiple phone numbers
  - [x] building relation
  - [x] multiple activity relations (many-to-many)
- [x] Buildings with address and geo coordinates (PostGIS)
- [x] Activity tree with max nesting depth = 3 (DB trigger)
- [x] API methods:
  - [x] list organizations
  - [x] filter organizations by building
  - [x] filter organizations by activity
  - [x] activity filter with child activities support
  - [x] organizations search by name
  - [x] organizations in radius from a point
  - [x] organizations in rectangular area (bbox)
  - [x] organization details by id
  - [x] buildings list
- [x] OpenAPI + Swagger UI + ReDoc
- [x] Dockerized app + database
- [x] Integration tests for main API flows and filters

---

## Local Development

Prerequisites:

- `uv` (required): https://docs.astral.sh/uv/getting-started/installation/
- `task` (optional, for Taskfile commands): https://taskfile.dev/installation/

1. Clone repository:

```bash
git clone https://github.com/gerathewitcher/test-assignment-fintech
cd test-assignment-fintech
```

2. Create `.env` from `.env.example`:

```bash
cp .env.example .env
```

3. Start local PostgreSQL (PostGIS):

```bash
docker compose up -d db
```

4. Apply migrations:

```bash
uv run alembic upgrade head
```

5. (Optional) Seed development data (New York organizations/buildings):

```bash
task db-seed
task db-seed-small
task db-seed-medium
task db-seed-large
task db-reset
```

Direct script usage:

```bash
uv run python scripts/seed_dev_db.py --profile medium --reset
uv run python scripts/reset_dev_db.py
```

6. Run integration tests:

```bash
task run-integration-tests
```

7. Run API server:

```bash
uv run start-app
```

API base URL:

```text
http://localhost:8000
```

---

## Full Run In Docker

Run full stack (app + PostGIS):

```bash
docker compose up --build -d
```

---

## API Documentation

Interactive API docs are available after app startup:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- OpenAPI schema: `http://localhost:8000/openapi.json`

---

## Authentication

All API requests must include a static API key in the `Authorization` header.

Example:

```bash
curl -H "Authorization: Bearer dev-static-api-key" \
  "http://localhost:8000/api/v1/directory/building"
```

API key is configured via environment variable `API_KEY` in `.env`
