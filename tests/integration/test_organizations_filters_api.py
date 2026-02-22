from datetime import datetime, timezone
from typing import TypedDict
from uuid import UUID

import pytest
from httpx import AsyncClient

from tests.integration.factories.building_factory import (
    BuildingPayload,
    build_building_payload,
)
from tests.integration.fixtures.db import (
    InsertActivityFixture,
    InsertBuildingFixture,
    InsertOrganizationFixture,
)


class OrgFilterDataset(TypedDict):
    activity: dict[str, UUID]
    building: dict[str, UUID]
    org: dict[str, UUID]


@pytest.fixture
async def org_filter_dataset(
    insert_activity: InsertActivityFixture,
    insert_building: InsertBuildingFixture,
    insert_organization: InsertOrganizationFixture,
) -> OrgFilterDataset:
    food_id = await insert_activity(name="Food")
    coffee_id = await insert_activity(name="Coffee Shops", parent_id=food_id)
    it_id = await insert_activity(name="IT")

    b1_payload: BuildingPayload = build_building_payload(
        index=101,
        address="Moscow, Center, 1",
        lon=37.6176,
        lat=55.7558,
    )
    b1 = await insert_building(**b1_payload)
    b2_payload: BuildingPayload = build_building_payload(
        index=102,
        address="Moscow, Center, 2",
        lon=37.62,
        lat=55.757,
    )
    b2 = await insert_building(**b2_payload)
    b3_payload: BuildingPayload = build_building_payload(
        index=103,
        address="Saint Petersburg, Nevsky, 7",
        lon=30.3351,
        lat=59.9343,
    )
    b3 = await insert_building(**b3_payload)

    alpha = await insert_organization(
        name="Alpha Coffee",
        building_id=b1,
        activity_id=coffee_id,
        created_at=datetime(2025, 1, 10, 10, 0, tzinfo=timezone.utc),
    )
    bravo = await insert_organization(
        name="Bravo Coffee",
        building_id=b2,
        activity_id=coffee_id,
        created_at=datetime(2025, 1, 10, 10, 5, tzinfo=timezone.utc),
    )
    code = await insert_organization(
        name="Code Forge",
        building_id=b3,
        activity_id=it_id,
        created_at=datetime(2025, 1, 10, 10, 10, tzinfo=timezone.utc),
    )
    food_court = await insert_organization(
        name="Food Court",
        building_id=b1,
        activity_id=food_id,
        created_at=datetime(2025, 1, 10, 10, 15, tzinfo=timezone.utc),
    )

    return {
        "activity": {"food": food_id, "coffee": coffee_id, "it": it_id},
        "building": {"b1": b1, "b2": b2, "b3": b3},
        "org": {
            "alpha": alpha,
            "bravo": bravo,
            "code": code,
            "food_court": food_court,
        },
    }


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("params", "expected_org_keys"),
    [
        ({"name": "coffee"}, {"alpha", "bravo"}),
        ({"building_uuid": "b1"}, {"alpha", "food_court"}),
        ({"activity_uuid": "coffee", "include_children": "false"}, {"alpha", "bravo"}),
        ({"activity_uuid": "food", "include_children": "false"}, {"food_court"}),
        (
            {"activity_uuid": "food", "include_children": "true"},
            {"alpha", "bravo", "food_court"},
        ),
        (
            {
                "center_lat": "55.7558",
                "center_long": "37.6176",
                "radius": "3000",
            },
            {"alpha", "bravo", "food_court"},
        ),
        (
            {"name": "coffee", "building_uuid": "b1"},
            {"alpha"},
        ),
    ],
)
async def test_get_organizations_filters(
    client: AsyncClient,
    org_filter_dataset: OrgFilterDataset,
    params: dict[str, str],
    expected_org_keys: set[str],
) -> None:
    building_map: dict[str, UUID] = org_filter_dataset["building"]
    activity_map: dict[str, UUID] = org_filter_dataset["activity"]
    org_map: dict[str, UUID] = org_filter_dataset["org"]

    query_params: dict[str, str] = {}
    for key, value in params.items():
        if key == "building_uuid":
            query_params[key] = str(building_map[value])
            continue
        if key == "activity_uuid":
            query_params[key] = str(activity_map[value])
            continue
        query_params[key] = value

    response = await client.get("/organization", params=query_params)

    assert response.status_code == 200
    payload = response.json()
    got_ids: set[UUID] = {UUID(item["uuid"]) for item in payload["items"]}
    expected_ids: set[UUID] = {org_map[key] for key in expected_org_keys}
    assert got_ids == expected_ids


@pytest.mark.asyncio
async def test_get_organizations_invalid_radius_params_returns_422(
    client: AsyncClient,
) -> None:
    response = await client.get(
        "/organization",
        params={
            "center_lat": "55.75",
            "center_long": "37.61",
            "radius": "-1",
        },
    )

    assert response.status_code == 422
