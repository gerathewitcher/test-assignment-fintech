import argparse
import asyncio
import random
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID

import asyncpg

from scripts._dev_db import create_connection, ensure_local_dev_db


@dataclass(frozen=True)
class SeedProfile:
    buildings: int
    organizations: int


SEED_PROFILES: dict[str, SeedProfile] = {
    "small": SeedProfile(buildings=30, organizations=80),
    "medium": SeedProfile(buildings=120, organizations=350),
    "large": SeedProfile(buildings=300, organizations=900),
}


ROOT_ACTIVITIES: tuple[str, ...] = (
    "Food & Beverage",
    "Retail",
    "Information Technology",
    "Healthcare",
    "Consumer Services",
    "Financial Services",
)

CHILD_ACTIVITIES_BY_ROOT: dict[str, tuple[str, ...]] = {
    "Food & Beverage": ("Coffee Shops", "Restaurants", "Bakeries", "Fast Food"),
    "Retail": ("Grocery Stores", "Electronics", "Pharmacies", "Fashion"),
    "Information Technology": (
        "Software Development",
        "IT Consulting",
        "Cybersecurity",
    ),
    "Healthcare": ("Clinics", "Dentistry", "Diagnostics"),
    "Consumer Services": ("Beauty Salons", "Fitness Clubs", "Cleaning Services"),
    "Financial Services": ("Banks", "Insurance", "Payment Services"),
}

BRANDS_BY_ACTIVITY: dict[str, tuple[str, ...]] = {
    "Coffee Shops": ("Manhattan Brew", "Brooklyn Bean", "Queens Coffee Co"),
    "Restaurants": ("Tribeca Table", "SoHo Kitchen", "Midtown Bistro"),
    "Bakeries": ("Hudson Bakery", "City Bread Lab", "Daily Crust"),
    "Fast Food": ("NYC Bites", "Quick Slice", "Street Eats"),
    "Grocery Stores": ("Metro Market", "Neighborhood Fresh", "Urban Grocery"),
    "Electronics": ("Tech Borough", "Device Hub", "City Electronics"),
    "Pharmacies": ("Care Pharmacy", "Metro Drugs", "Health Corner"),
    "Fashion": ("Urban Threads", "SoHo Wear", "Borough Outfitters"),
    "Software Development": ("Skyline Software", "Empire Code", "Manhattan Labs"),
    "IT Consulting": ("City IT Advisors", "NY Digital Consulting", "Hudson IT Group"),
    "Cybersecurity": ("Secure Skyline", "NY Cyber Shield", "Hudson ZeroTrust"),
    "Clinics": ("Manhattan Clinic", "City Care Clinic", "Borough Medical"),
    "Dentistry": ("Smile NYC", "City Dental Care", "Borough Smiles"),
    "Diagnostics": ("Metro Diagnostics", "City Diagnostic Center", "Borough Lab"),
    "Beauty Salons": ("SoHo Beauty", "Metro Beauty Bar", "City Glow"),
    "Fitness Clubs": ("Empire Fitness", "City Fit Club", "Metro Fitness Hub"),
    "Cleaning Services": ("City Clean", "Metro Cleaning Co", "NY Spotless"),
    "Banks": ("Empire Bank", "City National Bank", "Borough Bank"),
    "Insurance": ("City Insure", "Metro Coverage", "Empire Insurance"),
    "Payment Services": ("NY Pay Systems", "Metro Payments", "City Billing"),
}

BOROUGHS: tuple[str, ...] = (
    "Manhattan",
    "Brooklyn",
    "Queens",
    "Bronx",
    "Staten Island",
)
STREETS: tuple[str, ...] = (
    "5th Ave",
    "Madison Ave",
    "Broadway",
    "Lexington Ave",
    "Park Ave",
    "Wall St",
    "Canal St",
    "Atlantic Ave",
    "Queens Blvd",
    "Flatbush Ave",
    "Columbus Ave",
)
ZIP_CODES: tuple[str, ...] = (
    "10001",
    "10002",
    "10003",
    "10010",
    "10011",
    "10012",
    "10013",
    "10014",
    "10016",
    "10017",
    "10018",
    "10019",
    "10022",
    "11201",
    "11211",
    "11101",
)
NYC_AREA_CODES: tuple[str, ...] = ("212", "332", "646", "718", "917", "929")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Seed local dev PostgreSQL database.")
    parser.add_argument(
        "--profile",
        choices=tuple(SEED_PROFILES.keys()),
        default="small",
        help="Seed profile size.",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Truncate existing data before seeding.",
    )
    parser.add_argument(
        "--random-seed",
        type=int,
        default=42,
        help="Random seed for deterministic generation.",
    )
    return parser.parse_args()


async def ensure_extensions(conn: asyncpg.Connection) -> None:
    await conn.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
    await conn.execute("CREATE EXTENSION IF NOT EXISTS postgis")
    await conn.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")


async def reset_data(conn: asyncpg.Connection) -> None:
    await conn.execute(
        """
        TRUNCATE TABLE
            organization_phone_number,
            organization,
            activity,
            building
        RESTART IDENTITY CASCADE
        """
    )


async def get_or_create_activity(
    conn: asyncpg.Connection,
    *,
    name: str,
    parent_id: UUID | None,
) -> UUID:
    row = await conn.fetchrow(
        """
        SELECT id
        FROM activity
        WHERE name = $1
          AND parent_id IS NOT DISTINCT FROM $2
        LIMIT 1
        """,
        name,
        parent_id,
    )
    if row is not None:
        return row["id"]

    inserted = await conn.fetchrow(
        """
        INSERT INTO activity (id, name, parent_id)
        VALUES (gen_random_uuid(), $1, $2)
        RETURNING id
        """,
        name,
        parent_id,
    )
    if inserted is None:
        raise RuntimeError(f"Failed to create activity: {name}")
    return inserted["id"]


async def seed_activities(conn: asyncpg.Connection) -> list[UUID]:
    activity_ids: list[UUID] = []
    root_ids: dict[str, UUID] = {}

    for root_name in ROOT_ACTIVITIES:
        root_id = await get_or_create_activity(conn, name=root_name, parent_id=None)
        root_ids[root_name] = root_id
        activity_ids.append(root_id)

    for root_name, children in CHILD_ACTIVITIES_BY_ROOT.items():
        for child_name in children:
            child_id = await get_or_create_activity(
                conn,
                name=child_name,
                parent_id=root_ids[root_name],
            )
            activity_ids.append(child_id)

    return activity_ids


async def insert_building(conn: asyncpg.Connection, *, idx: int) -> UUID:
    address = (
        f"{random.randint(1, 9999)} {random.choice(STREETS)}, "
        f"{random.choice(BOROUGHS)}, New York, NY {random.choice(ZIP_CODES)}"
    )
    lon = -74.05 + random.random() * 0.35
    lat = 40.55 + random.random() * 0.35
    created_at = datetime(2025, 1, 1, 8, 0, tzinfo=UTC) + timedelta(minutes=idx * 5)
    row = await conn.fetchrow(
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
        raise RuntimeError("Failed to insert building")
    return row["id"]


async def insert_organization(
    conn: asyncpg.Connection,
    *,
    idx: int,
    activity_id: UUID,
    activity_name: str,
    building_id: UUID | None,
) -> UUID:
    base_name = random.choice(BRANDS_BY_ACTIVITY.get(activity_name, ("NY Company",)))
    name = f"{base_name} #{idx:04d}"
    created_at = datetime(2025, 2, 1, 9, 0, tzinfo=UTC) + timedelta(minutes=idx * 3)
    row = await conn.fetchrow(
        """
        INSERT INTO organization (id, name, building_id, activity_id, created_at)
        VALUES (gen_random_uuid(), $1, $2, $3, $4)
        RETURNING id
        """,
        name,
        building_id,
        activity_id,
        created_at,
    )
    if row is None:
        raise RuntimeError("Failed to insert organization")
    return row["id"]


async def insert_organization_phone(
    conn: asyncpg.Connection,
    *,
    organization_id: UUID,
) -> None:
    phone = (
        f"+1 ({random.choice(NYC_AREA_CODES)}) "
        f"{random.randint(100, 999)}-{random.randint(1000, 9999)}"
    )
    await conn.execute(
        """
        INSERT INTO organization_phone_number (id, organization_id, phone_number)
        VALUES (gen_random_uuid(), $1, $2)
        """,
        organization_id,
        phone,
    )


async def seed(profile: SeedProfile, *, reset: bool, random_seed: int) -> None:
    ensure_local_dev_db()
    random.seed(random_seed)

    conn = await create_connection()
    try:
        await ensure_extensions(conn)
        if reset:
            await reset_data(conn)

        activity_ids = await seed_activities(conn)
        activity_name_by_id = {
            row["id"]: row["name"]
            for row in await conn.fetch("SELECT id, name FROM activity")
        }

        building_ids: list[UUID] = []
        for idx in range(1, profile.buildings + 1):
            building_ids.append(await insert_building(conn, idx=idx))

        org_count = 0
        phone_count = 0
        for idx in range(1, profile.organizations + 1):
            activity_id = random.choice(activity_ids)
            activity_name = activity_name_by_id.get(
                activity_id, "Information Technology"
            )
            building_id = random.choice(building_ids)

            org_id = await insert_organization(
                conn,
                idx=idx,
                activity_id=activity_id,
                activity_name=activity_name,
                building_id=building_id,
            )
            org_count += 1

            for _ in range(random.choices([1, 2, 3], weights=[58, 32, 10], k=1)[0]):
                await insert_organization_phone(conn, organization_id=org_id)
                phone_count += 1

        print(
            "Seed completed:\n"
            f"  profile={profile}\n"
            f"  buildings={len(building_ids)}\n"
            f"  organizations={org_count}\n"
            f"  phone_numbers={phone_count}"
        )
    finally:
        await conn.close()


def main() -> None:
    args = parse_args()
    profile = SEED_PROFILES[args.profile]
    asyncio.run(seed(profile, reset=args.reset, random_seed=args.random_seed))


if __name__ == "__main__":
    main()
