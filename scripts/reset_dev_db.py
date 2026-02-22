import asyncio

from scripts._dev_db import create_connection


async def reset() -> None:
    conn = await create_connection()
    try:
        await conn.execute(
            """
            TRUNCATE TABLE
                organization_phone_number,
                organization_activity,
                organization,
                activity,
                building
            RESTART IDENTITY CASCADE
            """
        )
        print("Reset completed.")
    finally:
        await conn.close()


def main() -> None:
    asyncio.run(reset())


if __name__ == "__main__":
    main()
