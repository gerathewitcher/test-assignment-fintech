from datetime import datetime, timedelta, timezone
from typing import TypedDict


class BuildingPayload(TypedDict):
    address: str
    lon: float
    lat: float
    created_at: datetime


def build_building_payload(
    *,
    index: int = 1,
    address: str | None = None,
    lon: float | None = None,
    lat: float | None = None,
    created_at: datetime | None = None,
) -> BuildingPayload:
    """Build deterministic test payload for building insertion."""
    base_time = datetime(2025, 1, 1, 10, 0, tzinfo=timezone.utc)
    return {
        "address": address or f"Moscow, Test Street, {index}",
        "lon": lon if lon is not None else 37.60 + (index * 0.001),
        "lat": lat if lat is not None else 55.75 + (index * 0.001),
        "created_at": created_at or (base_time + timedelta(minutes=index)),
    }
