from collections.abc import Awaitable, Callable
from typing import AsyncGenerator, Sequence, TypeVar

from sqlalchemy import (
    CursorResult,
    Insert,
    RowMapping,
    Select,
    Update,
    text,
)
from sqlalchemy.ext.asyncio import AsyncConnection, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from src.config import settings


class Base(DeclarativeBase):
    pass


T = TypeVar("T")


class Database:
    def __init__(self, dsn: str | None = None) -> None:
        self.engine = create_async_engine(
            dsn or str(settings.POSTGRES_DSN),
            pool_size=settings.DATABASE_POOL_SIZE,
            pool_recycle=settings.DATABASE_POOL_TTL,
            pool_pre_ping=settings.DATABASE_POOL_PRE_PING,
        )

    async def fetch_one(
        self,
        select_query: Select | Insert | Update,
        connection: AsyncConnection | None = None,
        commit_after: bool = False,
    ) -> RowMapping | None:
        return await self._with_connection(
            connection,
            lambda conn: self._fetch_one_with_connection(
                select_query, conn, commit_after
            ),
        )

    async def fetch_all(
        self,
        select_query: Select | Insert | Update,
        connection: AsyncConnection | None = None,
        commit_after: bool = False,
    ) -> Sequence[RowMapping]:
        return await self._with_connection(
            connection,
            lambda conn: self._fetch_all_with_connection(
                select_query, conn, commit_after
            ),
        )

    async def execute(
        self,
        query: Insert | Update,
        connection: AsyncConnection | None = None,
        commit_after: bool = False,
    ) -> None:
        await self._with_connection(
            connection,
            lambda conn: self._execute_with_connection(query, conn, commit_after),
        )

    async def _with_connection(
        self,
        connection: AsyncConnection | None,
        operation: Callable[[AsyncConnection], Awaitable[T]],
    ) -> T:
        if connection is not None:
            return await operation(connection)

        async with self.engine.connect() as new_connection:
            return await operation(new_connection)

    async def _fetch_one_with_connection(
        self,
        select_query: Select | Insert | Update,
        connection: AsyncConnection,
        commit_after: bool,
    ) -> RowMapping | None:
        cursor = await self._execute_query(select_query, connection, commit_after)
        return cursor.mappings().first()

    async def _fetch_all_with_connection(
        self,
        select_query: Select | Insert | Update,
        connection: AsyncConnection,
        commit_after: bool,
    ) -> Sequence[RowMapping]:
        cursor = await self._execute_query(select_query, connection, commit_after)
        return cursor.mappings().all()

    async def _execute_with_connection(
        self,
        query: Insert | Update,
        connection: AsyncConnection,
        commit_after: bool,
    ) -> None:
        await self._execute_query(query, connection, commit_after)

    async def _execute_query(
        self,
        query: Select | Insert | Update,
        connection: AsyncConnection,
        commit_after: bool = False,
    ) -> CursorResult:
        result = await connection.execute(query)

        if commit_after:
            await connection.commit()

        return result

    async def get_db_connection(self) -> AsyncGenerator:
        connection = await self.engine.connect()

        try:
            yield connection
        finally:
            await connection.close()

    async def check_connection(self) -> None:
        async with self.engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
