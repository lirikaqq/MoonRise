#!/usr/bin/env python3
"""Удаление всех матчей и kill feed из БД."""
import asyncio
import sys

sys.path.insert(0, '/app')

from sqlalchemy import text
from app.database import get_db


async def clear_all():
    async for db in get_db():
        await db.execute(text("DELETE FROM match_kills"))
        await db.execute(text("DELETE FROM match_player_heroes"))
        await db.execute(text("DELETE FROM match_players"))
        await db.execute(text("DELETE FROM matches"))
        await db.commit()

        # Проверка
        for tbl in ["match_kills", "match_player_heroes", "match_players", "matches"]:
            r = await db.execute(text(f"SELECT COUNT(*) FROM {tbl}"))
            print(f"  {tbl}: {r.scalar()}")
        break


asyncio.run(clear_all())
print("✅ Все логи матчей удалены!")
