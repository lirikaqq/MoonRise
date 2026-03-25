import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.models.tournament import Tournament
from app.config import settings
from datetime import datetime


async def seed_tournaments():
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with AsyncSessionLocal() as session:
        tournaments = [
            Tournament(
                title="MoonRise MIX #3",
                description="Турнир в котором команды формируются с помощью инструментов для баланса команд.",
                format="mix",
                cover_url=None,
                start_date=datetime(2026, 3, 7),
                end_date=datetime(2026, 3, 8),
                status="registration",
                max_participants=100,
                participants_count=45,
                is_featured=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            ),
            Tournament(
                title="2x2 Valentines Cup",
                description="Парный турнир ко Дню Валентина.",
                format="other",
                start_date=datetime(2026, 2, 14),
                end_date=datetime(2026, 2, 14),
                status="completed",
                max_participants=100,
                participants_count=100,
                is_featured=False,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            ),
            Tournament(
                title="MoonRise Draft",
                description="Драфт турнир.",
                format="draft",
                start_date=datetime(2025, 12, 13),
                end_date=datetime(2025, 12, 14),
                status="completed",
                max_participants=100,
                participants_count=80,
                is_featured=False,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            ),
            Tournament(
                title="Lucio Wave Clash",
                description="Специальный турнир.",
                format="other",
                start_date=datetime(2025, 11, 29),
                end_date=datetime(2025, 11, 29),
                status="completed",
                max_participants=100,
                participants_count=60,
                is_featured=False,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            ),
            Tournament(
                title="MoonRise MIX #2",
                description="Второй микс турнир.",
                format="mix",
                start_date=datetime(2025, 11, 1),
                end_date=datetime(2025, 11, 2),
                status="completed",
                max_participants=100,
                participants_count=100,
                is_featured=False,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            ),
            Tournament(
                title="NoMercy Tournament",
                description="Жёсткий турнир.",
                format="start",
                start_date=datetime(2025, 10, 17),
                end_date=datetime(2025, 10, 17),
                status="completed",
                max_participants=100,
                participants_count=100,
                is_featured=False,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            ),
            Tournament(
                title="MoonRise MIX #1",
                description="Первый микс турнир.",
                format="mix",
                start_date=datetime(2025, 10, 4),
                end_date=datetime(2025, 10, 5),
                status="completed",
                max_participants=100,
                participants_count=100,
                is_featured=False,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            ),
        ]

        for t in tournaments:
            session.add(t)

        await session.commit()
        print("✅ Tournaments seeded!")
        for t in tournaments:
            print(f"   {t.title} ({t.format}) - {t.status}")


if __name__ == "__main__":
    asyncio.run(seed_tournaments())