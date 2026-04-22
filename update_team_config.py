import asyncio
import os
import sys
import json
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings
from app.models.tournament import Tournament

DATABASE_URL = str(settings.DATABASE_URL).replace("postgresql://", "postgresql+asyncpg://")
engine = create_async_engine(DATABASE_URL, echo=True)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def update_to_5v5():
    async with AsyncSessionLocal() as session:
        try:
            result = await session.execute(
                select(Tournament).where(Tournament.id == 6)
            )
            tournament = result.scalar_one_or_none()

            if not tournament:
                print("❌ Турнир с ID 6 не найден")
                return

            new_config = {
                "team_size": 5,
                "role_limits": {
                    "tank": 1,
                    "dps": 2,
                    "sup": 2,
                    "flex": 0
                }
            }

            await session.execute(
                update(Tournament)
                .where(Tournament.id == 6)
                .values(team_config=new_config)
            )

            await session.commit()
            await session.refresh(tournament)

            print("✅ Успешно обновлено на 5 на 5!")
            print("Новый team_config:")
            print(json.dumps(tournament.team_config, ensure_ascii=False, indent=2))

        except Exception as e:
            await session.rollback()
            print(f"❌ Ошибка: {e}")
        finally:
            await engine.dispose()


if __name__ == "__main__":
    asyncio.run(update_to_5v5())