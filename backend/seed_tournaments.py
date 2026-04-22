# -*- coding: utf-8 -*-
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import async_session_maker
from app.models.tournament import Tournament
from datetime import datetime, timezone

async def seed_tournaments():
    async with async_session_maker() as session:
        tournaments = [
            Tournament(
                title="2x2 Valentines Cup",
                description_general="Парный турнир ко Дню Валентина.",
                format="mix",
                start_date=datetime(2026, 2, 14, tzinfo=timezone.utc),
                end_date=datetime(2026, 2, 14, tzinfo=timezone.utc),
                status="completed",
                max_participants=100,
                participants_count=100,
                is_featured=False,
            ),
            Tournament(
                title="MoonRise Draft",
                description_general="Драфт турнир.",
                format="draft",
                start_date=datetime(2025, 12, 13, tzinfo=timezone.utc),
                end_date=datetime(2025, 12, 14, tzinfo=timezone.utc),
                status="completed",
                max_participants=100,
                participants_count=80,
                is_featured=False,
            ),
            Tournament(
                title="Lucio Wave Clash",
                description_general="Специальный турнир.",
                format="mix",
                start_date=datetime(2025, 11, 29, tzinfo=timezone.utc),
                end_date=datetime(2025, 11, 29, tzinfo=timezone.utc),
                status="completed",
                max_participants=100,
                participants_count=60,
                is_featured=False,
            ),
            Tournament(
                title="MoonRise MIX #2",
                description_general="Второй микс турнир.",
                format="mix",
                start_date=datetime(2025, 11, 1, tzinfo=timezone.utc),
                end_date=datetime(2025, 11, 2, tzinfo=timezone.utc),
                status="completed",
                max_participants=100,
                participants_count=100,
                is_featured=False,
            ),
            Tournament(
                title="NoMercy Tournament",
                description_general="Жёсткий турнир.",
                format="mix",
                start_date=datetime(2025, 10, 17, tzinfo=timezone.utc),
                end_date=datetime(2025, 10, 17, tzinfo=timezone.utc),
                status="completed",
                max_participants=100,
                participants_count=100,
                is_featured=False,
            ),
            Tournament(
                title="MoonRise MIX #1",
                description_general="Первый микс турнир.",
                format="mix",
                start_date=datetime(2025, 10, 4, tzinfo=timezone.utc),
                end_date=datetime(2025, 10, 5, tzinfo=timezone.utc),
                status="completed",
                max_participants=100,
                participants_count=100,
                is_featured=False,
            ),
        ]

        for t in tournaments:
            session.add(t)

        await session.commit()
        print("✅ Успешно! Старые турниры добавлены в базу.")
        for t in tournaments:
            print(f"   {t.title} ({t.format}) - {t.status}")


if __name__ == "__main__":
    asyncio.run(seed_tournaments())
