import logging
import os
import re
import subprocess
import sys
import uuid
from collections.abc import AsyncGenerator, Generator

import asyncpg
import pytest
from dishka import AsyncContainer, make_async_container
from dishka.integrations.fastapi import setup_dishka
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from testcontainers.postgres import PostgresContainer

from src.app import App
from src.config import settings
from src.dependencies import AppProvider, DatabaseProvider
from tests.integration.fixtures.db import (  # noqa: F401
    insert_activity,
    insert_building,
    insert_organization,
    insert_organization_phone,
)

logger = logging.getLogger(__name__)
DB_CLONE_LOCK_KEY = 74123091


def _safe_identifier(value: str) -> str:
    """Validate SQL identifier used for dynamic database names."""
    if not re.fullmatch(r"[a-z0-9_]+", value):
        raise ValueError(f"Unsafe database identifier: {value}")
    return value


def _build_sqlalchemy_async_dsn(pg: dict[str, str | int], db: str) -> str:
    """Build SQLAlchemy async DSN via existing Settings.POSTGRES_DSN logic."""
    cfg = settings.model_copy(
        update={
            "POSTGRES_USER": str(pg["user"]),
            "POSTGRES_PASSWORD": str(pg["password"]),
            "POSTGRES_HOST": str(pg["host"]),
            "POSTGRES_PORT": int(pg["port"]),
            "POSTGRES_DB": db,
        }
    )
    return str(cfg.POSTGRES_DSN)


async def _connect(pg: dict[str, str | int], database: str) -> asyncpg.Connection:
    """Create asyncpg connection to a specific database."""
    return await asyncpg.connect(
        user=str(pg["user"]),
        password=str(pg["password"]),
        host=str(pg["host"]),
        port=int(pg["port"]),
        database=database,
    )


def _run_migrations_for_db(pg: dict[str, str | int], database_name: str) -> None:
    """Run Alembic migrations against a specific database."""
    env = os.environ.copy()
    env["POSTGRES_USER"] = str(pg["user"])
    env["POSTGRES_PASSWORD"] = str(pg["password"])
    env["POSTGRES_HOST"] = str(pg["host"])
    env["POSTGRES_PORT"] = str(pg["port"])
    env["POSTGRES_DB"] = database_name

    subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        check=True,
        env=env,
    )


async def _drop_database_if_exists(
    pg: dict[str, str | int], database_name: str
) -> None:
    """Terminate active sessions and drop database if it exists."""
    db_name = _safe_identifier(database_name)
    admin_conn = await _connect(pg, "postgres")
    try:
        await admin_conn.execute(
            "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
            "WHERE datname = $1 AND pid <> pg_backend_pid()",
            db_name,
        )
        await admin_conn.execute(f'DROP DATABASE IF EXISTS "{db_name}"')
    finally:
        await admin_conn.close()


async def _acquire_db_clone_lock(conn: asyncpg.Connection) -> None:
    """Acquire advisory lock for template/clone DB operations."""
    await conn.execute("SELECT pg_advisory_lock($1)", DB_CLONE_LOCK_KEY)


async def _release_db_clone_lock(conn: asyncpg.Connection) -> None:
    """Release advisory lock for template/clone DB operations."""
    await conn.execute("SELECT pg_advisory_unlock($1)", DB_CLONE_LOCK_KEY)


@pytest.fixture(scope="session")
def postgres_container() -> Generator[dict[str, str | int], None, None]:
    """Start PostGIS container for integration tests session."""
    logger.info("Starting PostGIS test container")
    with PostgresContainer(
        image="postgis/postgis:17-master",
        username=settings.POSTGRES_USER,
        password=settings.POSTGRES_PASSWORD,
        dbname="postgres",
    ) as container:
        logger.info("PostGIS test container is ready")
        yield {
            "user": settings.POSTGRES_USER,
            "password": settings.POSTGRES_PASSWORD,
            "host": container.get_container_host_ip(),
            "port": int(container.get_exposed_port(5432)),
        }
    logger.info("PostGIS test container stopped")


@pytest.fixture(scope="session")
async def template_db(postgres_container: dict[str, str | int]) -> AsyncGenerator[str]:
    """Create migrated template database reused as source for per-test clones."""
    template_db_name = _safe_identifier(f"test_template_{uuid.uuid4().hex[:12]}")
    logger.info("Creating template DB: %s", template_db_name)
    await _drop_database_if_exists(postgres_container, template_db_name)

    admin_conn = await _connect(postgres_container, "postgres")
    try:
        await _acquire_db_clone_lock(admin_conn)
        try:
            await admin_conn.execute(f'CREATE DATABASE "{template_db_name}"')
        finally:
            await _release_db_clone_lock(admin_conn)
    finally:
        await admin_conn.close()

    _run_migrations_for_db(postgres_container, template_db_name)
    logger.info("Template DB is ready: %s", template_db_name)

    yield template_db_name

    logger.info("Dropping template DB: %s", template_db_name)
    await _drop_database_if_exists(postgres_container, template_db_name)


@pytest.fixture
async def test_db(
    postgres_container: dict[str, str | int], template_db: str
) -> AsyncGenerator[str]:
    """Create isolated database clone for a single test and remove it after."""
    test_db_name = _safe_identifier(f"test_case_{uuid.uuid4().hex[:12]}")
    logger.info("Creating test DB: %s from template %s", test_db_name, template_db)
    await _drop_database_if_exists(postgres_container, test_db_name)

    admin_conn = await _connect(postgres_container, "postgres")
    try:
        await _acquire_db_clone_lock(admin_conn)
        try:
            await admin_conn.execute(
                f'CREATE DATABASE "{test_db_name}" TEMPLATE "{template_db}"'
            )
        finally:
            await _release_db_clone_lock(admin_conn)
    finally:
        await admin_conn.close()

    yield test_db_name

    logger.info("Dropping test DB: %s", test_db_name)
    await _drop_database_if_exists(postgres_container, test_db_name)


@pytest.fixture
async def db_conn(
    postgres_container: dict[str, str | int], test_db: str
) -> AsyncGenerator[asyncpg.Connection]:
    """Provide direct asyncpg connection to current isolated test database."""
    conn = await _connect(postgres_container, test_db)
    try:
        yield conn
    finally:
        await conn.close()


@pytest.fixture
async def app(
    postgres_container: dict[str, str | int], test_db: str
) -> AsyncGenerator[FastAPI]:
    """Build FastAPI app wired to the test-specific database."""
    test_dsn = _build_sqlalchemy_async_dsn(postgres_container, test_db)
    fastapi_app: FastAPI = App.create_fastapi_app()
    container: AsyncContainer = make_async_container(
        AppProvider(),
        DatabaseProvider(dsn=test_dsn),
    )
    setup_dishka(container, fastapi_app)

    try:
        yield fastapi_app
    finally:
        await container.close()


@pytest.fixture
async def client(app: FastAPI) -> AsyncGenerator[AsyncClient]:
    """Provide HTTP client bound to in-process FastAPI app."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
        headers={"Authorization": f"Bearer {settings.API_KEY}"},
    ) as test_client:
        yield test_client
