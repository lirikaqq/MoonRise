# backend/make_admin.py
import asyncio
from sqlalchemy import select
from app.database import async_session_maker
from app.models.user import User

async def main():
    username = input("Введите ваш точный никнейм (username) на сайте: ")
    
    async with async_session_maker() as db:
        user = await db.scalar(select(User).where(User.username == username))
        if user:
            user.role = "admin"
            await db.commit()
            print(f"✅ УРА! Пользователь '{username}' теперь АДМИН!")
        else:
            print(f"❌ ОШИБКА: Пользователь '{username}' не найден. Вы точно авторизовались на сайте?")

if __name__ == "__main__":
    asyncio.run(main())