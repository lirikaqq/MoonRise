import asyncio
import os
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db  # <--- ИСПОЛЬЗУЕМ GET_DB ВМЕСТО SessionLocal
from app.models.user import User
from app.models.tournament import Tournament, TournamentParticipant
from datetime import datetime

# ==========================================
# НАСТРОЙКИ
# ==========================================
TOURNAMENT_ID = 29  # ID турнира
LOG_FILE = "match.txt"

async def parse_and_import():
    if not os.path.exists(LOG_FILE):
        print(f"❌ Файл {LOG_FILE} не найден!")
        return

    print("🔍 Читаем лог...")
    players = set()
    
    # Парсим только события входа игроков (чтобы вытащить ники)
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if "player_joined" in line:
                parts = line.strip().split(",")
                if len(parts) >= 4:
                    nickname = parts[3]
                    players.add(nickname)
    
    if not players:
        print("❌ Игроки не найдены в логе!")
        return

    print(f"✅ Найдено {len(players)} игроков: {', '.join(players)}")
    print(f"🚀 Начинаем импорт в БД (Турнир ID: {TOURNAMENT_ID})...")

    # Используем твой генератор get_db()
    async for db in get_db():
        # 1. Проверяем, существует ли турнир
        result = await db.execute(select(Tournament).where(Tournament.id == TOURNAMENT_ID))
        tournament = result.scalar_one_or_none()
        
        if not tournament:
            print(f"❌ Турнир с ID {TOURNAMENT_ID} не найден в базе!")
            return

        added_users = 0
        registered_users = 0

        for nickname in players:
            # 2. Ищем или создаем пользователя (по фейковому Discord ID)
            fake_discord_id = f"fake_discord_{nickname.lower()}"
            
            result = await db.execute(select(User).where(User.discord_id == fake_discord_id))
            user = result.scalar_one_or_none()
            
            if not user:
                user = User(
                    discord_id=fake_discord_id,
                    username=nickname,
                    role="player"
                )
                db.add(user)
                await db.flush()  # Получаем user.id, не делая commit
                added_users += 1
                print(f"👤 Создан профиль: {nickname}")
            
            # 3. Регистрируем пользователя на турнир
            result = await db.execute(
                select(TournamentParticipant).where(
                    TournamentParticipant.tournament_id == TOURNAMENT_ID,
                    TournamentParticipant.user_id == user.id
                )
            )
            participant = result.scalar_one_or_none()
            
            if not participant:
                new_participant = TournamentParticipant(
                    tournament_id=TOURNAMENT_ID,
                    user_id=user.id,
                    status="registered",
                    registered_at=datetime.utcnow()
                )
                db.add(new_participant)
                tournament.participants_count += 1
                registered_users += 1
                print(f"✅ {nickname} зарегистрирован на турнир!")
            else:
                print(f"⚠️ {nickname} УЖЕ зарегистрирован.")

        # Сохраняем все изменения в базу
        await db.commit()
        
        print("\n🎉 ИМПОРТ ЗАВЕРШЕН!")
        print(f"Новых пользователей создано: {added_users}")
        print(f"Регистраций на турнир добавлено: {registered_users}")
        break  # Выходим из цикла get_db после одной сессии

if __name__ == "__main__":
    asyncio.run(parse_and_import())