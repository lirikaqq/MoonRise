import asyncio
from app.database import AsyncSessionLocal
from sqlalchemy import text


async def make_admin():
    async with AsyncSessionLocal() as db:
        await db.execute(text("UPDATE users SET role = 'admin' WHERE id = 3"))
        await db.commit()
        print("User 3 is now admin!")


asyncio.run(make_admin())