import asyncio
from app.database import async_session
from app.models.user import User, BattleTag
from datetime import datetime

users_data = [
    # Команда Ocelot
    {"username": "Ocelot", "battletags": ["Ocelot#1234"]},
    {"username": "Darknight", "battletags": ["Darknight#5678"]},
    {"username": "NotNumb", "battletags": ["NotNumb#9101"]},
    {"username": "Cranbereis", "battletags": ["Cranbereis#1112"]},
    {"username": "Блеба", "battletags": ["Блеба#1314", "BJIe6a#1314"]},

    # Команда PŪPREMŠKIY
    {"username": "PŪPREMŠKIY", "battletags": ["PŪPREMŠKIY||2#1516"]},
    {"username": "thofyb", "battletags": ["thofyb#1718"]},
    {"username": "Kamikuje", "battletags": ["Kamikuje#1920"]},
    {"username": "Squirrel", "battletags": ["Squirrel#2122"]},
    {"username": "DEE", "battletags": ["DEE#2324"]},
]

async def seed_users_and_battletags():
    async with async_session() as db:
        print("🌱 Начинаем сидинг юзеров и BattleTag'ов...")
        
        for u_data in users_data:
            user = User(
                discord_id=f"fake_{u_data['username']}",
                username=u_data['username'],
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(user)
            await db.flush() # Получаем user.id

            print(f"  - Создан юзер: {user.username} (ID: {user.id})")
            
            for i, tag_str in enumerate(u_data['battletags']):
                btag = BattleTag(
                    user_id=user.id,
                    tag=tag_str,
                    is_primary=(i == 0) # Первый тег — основной
                )
                db.add(btag)
                print(f"    - Добавлен BattleTag: {btag.tag}")

        await db.commit()
        print("\n✅ Сидинг завершён!")

if __name__ == "__main__":
    asyncio.run(seed_users_and_battletags())