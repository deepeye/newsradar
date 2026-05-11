"""One-shot script to create X KOL data source and trigger collection"""
import asyncio
import json
from uuid import uuid4

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy import text


async def main():
    engine = create_async_engine(
        "postgresql+asyncpg://postgres:postgres@localhost:5432/clue_collector"
    )
    async with AsyncSession(engine) as session:
        # Check if KOL group exists
        result = await session.execute(
            text("SELECT id, name FROM source_groups WHERE name = 'KOL监控'")
        )
        group = result.fetchone()

        if not group:
            group_id = uuid4()
            await session.execute(
                text(
                    "INSERT INTO source_groups "
                    "(id, name, collect_interval, is_active, created_at, updated_at) "
                    "VALUES (:id, 'KOL监控', 30, true, now(), now())"
                ),
                {"id": str(group_id)},
            )
            print(f"Created KOL group: {group_id}")
        else:
            group_id = group[0]
            print(f"KOL group exists: {group_id}")

        # Check if X KOL data source already exists
        result = await session.execute(
            text(
                "SELECT id FROM data_sources "
                "WHERE collector_type = 'kol' AND name = 'x:Elon Musk'"
            )
        )
        existing = result.fetchone()

        if existing:
            source_id = existing[0]
            print(f"X KOL data source exists: {source_id}")
        else:
            source_id = uuid4()
            config = json.dumps(
                {"platform": "x", "platform_id": "elonmusk", "screen_name": "Elon Musk"}
            )
            await session.execute(
                text(
                    "INSERT INTO data_sources "
                    "(id, group_id, name, type, collector_type, config, priority, is_active, status, consecutive_failures, created_at, updated_at) "
                    "VALUES (:id, :gid, 'x:Elon Musk', 'ACCOUNT', 'kol', :config, 1, true, 'ACTIVE', 0, now(), now())"
                ),
                {"id": str(source_id), "gid": str(group_id), "config": config},
            )
            print(f"Created X data source: {source_id}")

        # Check if KOL profile exists
        result = await session.execute(
            text("SELECT id FROM kol_profiles WHERE platform = 'x' AND platform_id = 'elonmusk'")
        )
        existing_profile = result.fetchone()

        if existing_profile:
            print(f"KOL profile exists: {existing_profile[0]}")
        else:
            kol_id = uuid4()
            await session.execute(
                text(
                    "INSERT INTO kol_profiles "
                    "(id, source_id, platform, platform_id, screen_name, is_active, created_at, updated_at) "
                    "VALUES (:id, :sid, 'x', 'elonmusk', 'Elon Musk', true, now(), now())"
                ),
                {"id": str(kol_id), "sid": str(source_id)},
            )
            print(f"Created KOL profile: {kol_id}")

        await session.commit()
    await engine.dispose()
    print("Done!")


asyncio.run(main())