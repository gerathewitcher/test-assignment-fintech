from collections.abc import Awaitable
from datetime import datetime
from typing import Protocol
from uuid import UUID

import asyncpg
import pytest


class InsertBuildingFixture(Protocol):
    def __call__(
        self,
        *,
        address: str,
        lon: float,
        lat: float,
        created_at: datetime,
    ) -> Awaitable[UUID]: ...


class InsertActivityFixture(Protocol):
    def __call__(
        self,
        *,
        name: str,
        parent_id: UUID | None = None,
    ) -> Awaitable[UUID]: ...


class InsertOrganizationFixture(Protocol):
    def __call__(
        self,
        *,
        name: str,
        building_id: UUID | None,
        created_at: datetime,
    ) -> Awaitable[UUID]: ...


class InsertOrganizationActivityFixture(Protocol):
    def __call__(
        self,
        *,
        organization_id: UUID,
        activity_id: UUID,
    ) -> Awaitable[None]: ...


class InsertOrganizationPhoneFixture(Protocol):
    def __call__(
        self,
        *,
        organization_id: UUID,
        phone_number: str,
    ) -> Awaitable[UUID]: ...


@pytest.fixture
def insert_building(
    db_conn: asyncpg.Connection,
) -> InsertBuildingFixture:
    """Insert a single building row and return its id."""

    async def _insert(
        *,
        address: str,
        lon: float,
        lat: float,
        created_at: datetime,
    ) -> UUID:
        row = await db_conn.fetchrow(
            """
            INSERT INTO building (id, address, location, created_at)
            VALUES (
                gen_random_uuid(),
                $1,
                ST_SetSRID(ST_MakePoint($2, $3), 4326)::geography,
                $4
            )
            RETURNING id
            """,
            address,
            lon,
            lat,
            created_at,
        )
        if row is None:
            raise RuntimeError("Insert building failed: no row returned")
        return row["id"]

    return _insert


@pytest.fixture
def insert_activity(
    db_conn: asyncpg.Connection,
) -> InsertActivityFixture:
    """Insert activity row and return its id."""

    async def _insert(
        *,
        name: str,
        parent_id: UUID | None = None,
    ) -> UUID:
        row = await db_conn.fetchrow(
            """
            INSERT INTO activity (id, name, parent_id)
            VALUES (gen_random_uuid(), $1, $2)
            RETURNING id
            """,
            name,
            parent_id,
        )
        if row is None:
            raise RuntimeError("Insert activity failed: no row returned")
        return row["id"]

    return _insert


@pytest.fixture
def insert_organization(
    db_conn: asyncpg.Connection,
) -> InsertOrganizationFixture:
    """Insert organization row and return its id."""

    async def _insert(
        *,
        name: str,
        building_id: UUID | None,
        created_at: datetime,
    ) -> UUID:
        row = await db_conn.fetchrow(
            """
            INSERT INTO organization (id, name, building_id, created_at)
            VALUES (gen_random_uuid(), $1, $2, $3)
            RETURNING id
            """,
            name,
            building_id,
            created_at,
        )
        if row is None:
            raise RuntimeError("Insert organization failed: no row returned")
        return row["id"]

    return _insert


@pytest.fixture
def insert_organization_activity(
    db_conn: asyncpg.Connection,
) -> InsertOrganizationActivityFixture:
    """Insert organization-activity link row."""

    async def _insert(
        *,
        organization_id: UUID,
        activity_id: UUID,
    ) -> None:
        await db_conn.execute(
            """
            INSERT INTO organization_activity (organization_id, activity_id)
            VALUES ($1, $2)
            """,
            organization_id,
            activity_id,
        )

    return _insert


@pytest.fixture
def insert_organization_phone(
    db_conn: asyncpg.Connection,
) -> InsertOrganizationPhoneFixture:
    """Insert organization phone row and return its id."""

    async def _insert(
        *,
        organization_id: UUID,
        phone_number: str,
    ) -> UUID:
        row = await db_conn.fetchrow(
            """
            INSERT INTO organization_phone_number (id, organization_id, phone_number)
            VALUES (gen_random_uuid(), $1, $2)
            RETURNING id
            """,
            organization_id,
            phone_number,
        )
        if row is None:
            raise RuntimeError("Insert organization phone failed: no row returned")
        return row["id"]

    return _insert
