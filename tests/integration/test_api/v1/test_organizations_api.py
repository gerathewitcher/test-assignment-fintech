from datetime import datetime, timezone

import pytest
from httpx import AsyncClient

from src.api.v1.constants import API_V1_DIRECTORY_PREFIX
from tests.integration.factories.building_factory import (
    BuildingPayload,
    build_building_payload,
)
from tests.integration.fixtures.db import (
    InsertActivityFixture,
    InsertBuildingFixture,
    InsertOrganizationActivityFixture,
    InsertOrganizationFixture,
    InsertOrganizationPhoneFixture,
)


def _url(path: str) -> str:
    return f"{API_V1_DIRECTORY_PREFIX}{path}"


@pytest.mark.asyncio
async def test_get_organizations_empty_list(client: AsyncClient) -> None:
    """Returns empty organizations page when there is no data."""
    response = await client.get(_url("/organization"))

    assert response.status_code == 200
    payload = response.json()
    assert payload["items"] == []
    assert payload["next_cursor"] is None


@pytest.mark.asyncio
async def test_get_organizations_returns_items_with_relations(
    client: AsyncClient,
    insert_activity: InsertActivityFixture,
    insert_building: InsertBuildingFixture,
    insert_organization: InsertOrganizationFixture,
    insert_organization_activity: InsertOrganizationActivityFixture,
) -> None:
    """Returns organizations list with building relation"""
    activity_id = await insert_activity(name="Coffee Shops")
    building_payload: BuildingPayload = build_building_payload(
        index=10, address="Moscow, Arbat, 10"
    )
    building_id = await insert_building(**building_payload)

    org_id = await insert_organization(
        name="Brew Lab",
        building_id=building_id,
        created_at=datetime(2025, 1, 1, 10, 0, tzinfo=timezone.utc),
    )
    await insert_organization_activity(organization_id=org_id, activity_id=activity_id)

    response = await client.get(_url("/organization?limit=10"))

    assert response.status_code == 200
    payload = response.json()
    assert len(payload["items"]) == 1
    assert payload["next_cursor"] is None

    org = payload["items"][0]
    assert org["name"] == "Brew Lab"
    assert org["building"]["address"] == "Moscow, Arbat, 10"


@pytest.mark.asyncio
async def test_get_organizations_pagination_with_cursor(
    client: AsyncClient,
    insert_activity: InsertActivityFixture,
    insert_building: InsertBuildingFixture,
    insert_organization: InsertOrganizationFixture,
    insert_organization_activity: InsertOrganizationActivityFixture,
) -> None:
    """Paginates organizations with keyset cursor."""
    activity_id = await insert_activity(name="IT Consulting")
    building_id = await insert_building(**build_building_payload(index=20))

    alpha_id = await insert_organization(
        name="Alpha Systems",
        building_id=building_id,
        created_at=datetime(2025, 1, 1, 10, 0, tzinfo=timezone.utc),
    )
    await insert_organization_activity(
        organization_id=alpha_id, activity_id=activity_id
    )
    beta_id = await insert_organization(
        name="Beta Systems",
        building_id=building_id,
        created_at=datetime(2025, 1, 1, 11, 0, tzinfo=timezone.utc),
    )
    await insert_organization_activity(organization_id=beta_id, activity_id=activity_id)

    first_page = await client.get(_url("/organization?limit=1"))
    assert first_page.status_code == 200
    first_payload = first_page.json()
    assert len(first_payload["items"]) == 1
    assert first_payload["items"][0]["name"] == "Alpha Systems"
    assert first_payload["next_cursor"] is not None

    second_page = await client.get(
        _url("/organization"),
        params={"limit": 1, "cursor": first_payload["next_cursor"]},
    )
    assert second_page.status_code == 200
    second_payload = second_page.json()
    assert len(second_payload["items"]) == 1
    assert second_payload["items"][0]["name"] == "Beta Systems"
    assert second_payload["next_cursor"] is None


@pytest.mark.asyncio
async def test_get_organizations_invalid_cursor_returns_400(
    client: AsyncClient,
) -> None:
    """Returns 400 for malformed organization cursor."""
    response = await client.get(_url("/organization?cursor=not-a-valid-cursor"))

    assert response.status_code == 400
    payload = response.json()
    assert payload["detail"] == "Invalid pagination cursor"


@pytest.mark.asyncio
async def test_get_organization_by_uuid(
    client: AsyncClient,
    insert_activity: InsertActivityFixture,
    insert_building: InsertBuildingFixture,
    insert_organization: InsertOrganizationFixture,
    insert_organization_activity: InsertOrganizationActivityFixture,
    insert_organization_phone: InsertOrganizationPhoneFixture,
) -> None:
    """Returns organization detail with phone numbers and activities list."""
    clinics_activity_id = await insert_activity(name="Clinics")
    diagnostics_activity_id = await insert_activity(name="Diagnostics")
    building_id = await insert_building(**build_building_payload(index=30))
    org_id = await insert_organization(
        name="Med Point",
        building_id=building_id,
        created_at=datetime(2025, 1, 2, 10, 0, tzinfo=timezone.utc),
    )
    await insert_organization_activity(
        organization_id=org_id,
        activity_id=clinics_activity_id,
    )
    await insert_organization_activity(
        organization_id=org_id,
        activity_id=diagnostics_activity_id,
    )
    await insert_organization_phone(
        organization_id=org_id,
        phone_number="+7 (495) 111-11-11",
    )
    await insert_organization_phone(
        organization_id=org_id,
        phone_number="+7 (495) 222-22-22",
    )

    response = await client.get(_url(f"/organization/{org_id}"))

    assert response.status_code == 200
    payload = response.json()
    assert payload["name"] == "Med Point"
    numbers = {item["number"] for item in payload["phone_numbers"]}
    assert numbers == {"+7 (495) 111-11-11", "+7 (495) 222-22-22"}
    activity_names = {item["name"] for item in payload["activities"]}
    assert activity_names == {"Clinics", "Diagnostics"}
