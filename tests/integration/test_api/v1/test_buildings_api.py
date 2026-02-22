import pytest
from httpx import AsyncClient

from src.api.v1.constants import API_V1_DIRECTORY_PREFIX
from tests.integration.factories.building_factory import (
    BuildingPayload,
    build_building_payload,
)
from tests.integration.fixtures.db import InsertBuildingFixture


def _url(path: str) -> str:
    return f"{API_V1_DIRECTORY_PREFIX}{path}"


@pytest.mark.asyncio
async def test_get_buildings_empty_list(client: AsyncClient) -> None:
    """Returns empty buildings page when there is no data."""
    response = await client.get(_url("/building"))

    assert response.status_code == 200
    payload: dict = response.json()
    assert payload["items"] == []
    assert payload["next_cursor"] is None


@pytest.mark.asyncio
async def test_get_buildings_from_factory_insert(
    client: AsyncClient,
    insert_building: InsertBuildingFixture,
) -> None:
    """Returns inserted buildings from the list endpoint."""
    first: BuildingPayload = build_building_payload(index=1)
    second: BuildingPayload = build_building_payload(index=2)
    await insert_building(**first)
    await insert_building(**second)

    response = await client.get(_url("/building?limit=10"))

    assert response.status_code == 200
    payload: dict = response.json()
    assert len(payload["items"]) == 2
    assert payload["next_cursor"] is None


@pytest.mark.asyncio
async def test_get_buildings_pagination_with_cursor(
    client: AsyncClient,
    insert_building: InsertBuildingFixture,
) -> None:
    """Paginates buildings with keyset cursor."""
    first: BuildingPayload = build_building_payload(
        index=1, address="Moscow, Cursor St, 1"
    )
    second: BuildingPayload = build_building_payload(
        index=2, address="Moscow, Cursor St, 2"
    )
    await insert_building(**first)
    await insert_building(**second)

    first_page = await client.get(_url("/building?limit=1"))
    assert first_page.status_code == 200
    first_payload: dict = first_page.json()
    assert len(first_payload["items"]) == 1
    assert first_payload["items"][0]["address"] == "Moscow, Cursor St, 1"
    assert first_payload["next_cursor"] is not None

    second_page = await client.get(
        _url("/building"),
        params={"limit": 1, "cursor": first_payload["next_cursor"]},
    )
    assert second_page.status_code == 200
    second_payload: dict = second_page.json()
    assert len(second_payload["items"]) == 1
    assert second_payload["items"][0]["address"] == "Moscow, Cursor St, 2"
    assert second_payload["next_cursor"] is None


@pytest.mark.asyncio
async def test_get_buildings_invalid_cursor_returns_400(client: AsyncClient) -> None:
    """Returns 400 for malformed buildings cursor."""
    response = await client.get(_url("/building?cursor=not-a-valid-cursor"))

    assert response.status_code == 400
    payload: dict = response.json()
    assert payload["detail"] == "Invalid pagination cursor"
