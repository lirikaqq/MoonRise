import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.models.user import User, BattleTag
from app.database import Base
from app.config import settings
from datetime import datetime

async def seed_database():
    """Добавить тестовых пользователей в БД."""
    
    # Создаём engine
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    
    # Создаём sessionmaker
    AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with AsyncSessionLocal() as session:
        # Создаём тестового пользователя
        user1 = User(
            discord_id="123456789",
            username="TestPlayer1",
            avatar_url="https://cdn.discordapp.com/avatars/123456789/default.png",
            role="player",
            division="Gold",
            is_banned=False,
            reputation_score=100,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        
        user2 = User(
            discord_id="987654321",
            username="TestPlayer2",
            avatar_url="https://cdn.discordapp.com/avatars/987654321/default.png",
            role="player",
            division="Silver",
            is_banned=False,
            reputation_score=50,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        
        session.add(user1)
        session.add(user2)
        await session.flush()  # Чтобы получить ID
        
        # Добавляем баттлтеги
        tag1 = BattleTag(
            user_id=user1.id,
            tag="TestPlayer1#1234",
            is_primary=True,
        )
        
        tag2 = BattleTag(
            user_id=user2.id,
            tag="TestPlayer2#5678",
            is_primary=True,
        )
        
        session.add(tag1)
        session.add(tag2)
        
        await session.commit()
        
        print("✅ Database seeded with test users!")
        print(f"   User 1: {user1.username} (ID: {user1.id})")
        print(f"   User 2: {user2.username} (ID: {user2.id})")

if __name__ == "__main__":
    asyncio.run(seed_database())