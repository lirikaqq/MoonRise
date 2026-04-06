from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, func
from sqlalchemy.orm import selectinload, joinedload
from typing import List, Optional
from datetime import datetime

from app.models.user import User
from app.models.tournament import Tournament, TournamentParticipant
from app.models.match import MatchPlayer, MatchPlayerHero  # <-- Импорты добавлены
from app.schemas.player import PlayerUpdate


class PlayerService:

    @staticmethod
    async def get_all_players(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[User]:
        result = await db.execute(
            select(User)
            .order_by(User.username)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    @staticmethod
    async def get_player_profile(db: AsyncSession, player_id: int) -> Optional[User]:
        result = await db.execute(
            select(User)
            .options(selectinload(User.battletags))
            .where(User.id == player_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_player_tournaments(db: AsyncSession, player_id: int) -> list:
        # Убедимся, что игрок существует
        player = await db.get(User, player_id)
        if not player:
            return []

        result = await db.execute(
            select(Tournament, TournamentParticipant)
            .join(TournamentParticipant, Tournament.id == TournamentParticipant.tournament_id)
            .where(TournamentParticipant.user_id == player_id)
            .order_by(Tournament.start_date.desc())
        )
        
        tournaments_data = []
        for tournament, participant in result.all():
            tournaments_data.append({
                "tournament_id": tournament.id,
                "title": tournament.title,
                "format": tournament.format,
                "status": tournament.status,
                "start_date": tournament.start_date.isoformat(),
                "cover_url": tournament.cover_url,
                "participant_status": participant.status,
                "is_allowed": participant.is_allowed,
                "checked_in": bool(participant.checkedin_at)
            })
        return tournaments_data
    
    @staticmethod
    async def update_player(db: AsyncSession, user_id: int, data: PlayerUpdate) -> User:
        user = await db.get(User, user_id)
        if not user:
            return None # Обработка в роутере
        
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(user, key, value)
        
        user.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(user)
        return user

    # 👇 НОВЫЙ МЕТОД 👇
    @staticmethod
    async def delete_player(db: AsyncSession, player_id: int) -> Optional[User]:
        """Полностью удаляет игрока и всю связанную с ним статистику."""
        player = await db.get(User, player_id)
        if not player:
            return None

        # Шаг 1: Удаляем статистику по героям игрока во всех матчах.
        # Это нужно делать вручную, т.к. прямой связи с User нет (через MatchPlayer).
        await db.execute(
            delete(MatchPlayerHero).where(
                MatchPlayerHero.match_player_id.in_(
                    select(MatchPlayer.id).where(MatchPlayer.user_id == player_id)
                )
            )
        )

        # Шаг 2: Удаляем статистику игрока во всех матчах.
        # Это нужно делать вручную, т.к. в модели User->MatchPlayer стоит ondelete="SET NULL".
        await db.execute(
            delete(MatchPlayer).where(MatchPlayer.user_id == player_id)
        )
        
        # Шаг 3: Удаляем самого игрока.
        # SQLAlchemy благодаря cascade='all, delete-orphan' и ondelete='CASCADE' 
        # в моделях User и Tournament позаботится об остальном 
        # (BattleTags, TournamentParticipant и т.д.).
        await db.delete(player)
        await db.commit()
        return player