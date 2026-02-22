FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock README.md ./
COPY src ./src
COPY alembic ./alembic
COPY alembic.ini ./alembic.ini

RUN uv sync --frozen --no-dev

EXPOSE 8000

CMD ["sh", "-c", "uv run alembic upgrade head && uv run start-app"]
