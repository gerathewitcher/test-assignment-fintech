import asyncpg

from src.config import settings


def ensure_local_dev_db() -> None:
    if settings.POSTGRES_HOST not in {"localhost", "127.0.0.1"}:
        raise RuntimeError(
            "Refusing to access non-localhost database. "
            "Set POSTGRES_HOST to localhost or 127.0.0.1."
        )


async def create_connection() -> asyncpg.Connection:
    ensure_local_dev_db()
    return await asyncpg.connect(
        user=settings.POSTGRES_USER,
        password=settings.POSTGRES_PASSWORD,
        host=settings.POSTGRES_HOST,
        port=settings.POSTGRES_PORT,
        database=settings.POSTGRES_DB,
    )
