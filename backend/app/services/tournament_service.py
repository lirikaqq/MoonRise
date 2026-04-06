from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from app.models.tournament import Tournament
from app.schemas.tournament import TournamentCreate, TournamentUpdate
from fastapi import HTTPException
from typing import Optional
import logging
from sqlalchemy.orm import joinedload
from collections import defaultdict
from app.models.match import Encounter

logger = logging.getLogger(__name__)


class TournamentService:
    """Сервис для работы с турнирами."""

    @staticmethod
    async def get_all(
        db: AsyncSession,
        format: Optional[str] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 20
    ) -> list[Tournament]:
        """Получить список турниров с фильтрацией."""
        query = select(Tournament).where(Tournament.is_active == True)

        if format and format != "all":
            query = query.where(Tournament.format == format)

        if search:
            query = query.where(
                Tournament.title.ilike(f"%{search}%")
            )

        query = query.order_by(
            Tournament.is_featured.desc(),
            Tournament.start_date.desc()
        )

        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def get_by_id(db: AsyncSession, tournament_id: int) -> Tournament:
        """Получить турнир по ID."""
        result = await db.execute(
            select(Tournament).where(Tournament.id == tournament_id)
        )
        tournament = result.scalar_one_or_none()

        if not tournament:
            raise HTTPException(status_code=404, detail="Tournament not found")

        return tournament

    @staticmethod
    async def create(db: AsyncSession, data: TournamentCreate) -> Tournament:
        """Создать новый турнир."""
        tournament = Tournament(
            title=data.title,
            description=data.description,
            format=data.format,
            cover_url=data.cover_url,
            start_date=data.start_date,
            end_date=data.end_date,
            registration_open=data.registration_open,
            registration_close=data.registration_close,
            checkin_open=data.checkin_open,
            checkin_close=data.checkin_close,
            max_participants=data.max_participants,
            status="upcoming",
        )
        db.add(tournament)
        await db.commit()
        await db.refresh(tournament)
        logger.info(f"✅ Tournament created: {tournament.title}")
        return tournament

    @staticmethod
    async def update(
        db: AsyncSession,
        tournament_id: int,
        data: TournamentUpdate
    ) -> Tournament:
        """Обновить турнир."""
        tournament = await TournamentService.get_by_id(db, tournament_id)

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(tournament, field, value)

        await db.commit()
        await db.refresh(tournament)
        return tournament

    # 👇 ИЗМЕНЕНО: Заменили старый soft-delete на новый hard-delete.
    # Этот метод теперь выполняет полное удаление из БД.
    @staticmethod
    async def delete_tournament(db: AsyncSession, tournament_id: int) -> Optional[Tournament]:
        """Удаляет турнир и все связанные с ним данные (hard delete)."""
        tournament = await TournamentService.get_by_id(db, tournament_id)
        
        # Благодаря cascade="all, delete-orphan" в модели Tournament,
        # SQLAlchemy автоматически удалит все дочерние записи:
        # participants, teams, encounters, matches и т.д.
        await db.delete(tournament)
        await db.commit()
        
        # Возвращаем объект для формирования сообщения в роутере
        return tournament

    @staticmethod
    async def update_status(
        db: AsyncSession,
        tournament_id: int,
        status: str
    ) -> Tournament:
        """Изменить статус турнира."""
        valid_statuses = ["upcoming", "registration", "checkin", "draft", "ongoing", "completed", "cancelled"]
        if status not in valid_statuses:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status. Must be one of: {valid_statuses}"
            )

        tournament = await TournamentService.get_by_id(db, tournament_id)
        tournament.status = status
        await db.commit()
        await db.refresh(tournament)
        return tournament
    
    @staticmethod
    async def get_bracket(db: AsyncSession, tournament_id: int) -> dict:
        """Собирает все матчи турнира и возвращает JSON сетки."""
        
        await TournamentService.get_by_id(db, tournament_id)

        query = (
            select(Encounter)
            .options(
                joinedload(Encounter.team1),
                joinedload(Encounter.team2)
            )
            .where(Encounter.tournament_id == tournament_id)
            .order_by(Encounter.round_number.asc(), Encounter.id.asc())
        )
        
        result = await db.execute(query)
        encounters = result.scalars().all()

        if not encounters:
            return {"upper_bracket": []}

        rounds_map = defaultdict(list)
        for enc in encounters:
            r_num = enc.round_number or 1
            rounds_map[r_num].append(enc)

        upper_bracket = []
        sorted_rounds = sorted(rounds_map.keys())
        
        for r_num in sorted_rounds:
            matches = []
            for enc in rounds_map[r_num]:
                t1_is_winner = (enc.winner_team_id == enc.team1_id) if enc.winner_team_id else False
                t2_is_winner = (enc.winner_team_id == enc.team2_id) if enc.winner_team_id else False
                
                matches.append({
                    "id": enc.id,
                    "isEmpty": False,
                    "team1": {
                        "name": enc.team1.name if enc.team1 else "TBD",
                        "score": enc.team1_score,
                        "isWinner": t1_is_winner
                    },
                    "team2": {
                        "name": enc.team2.name if enc.team2 else "TBD",
                        "score": enc.team2_score,
                        "isWinner": t2_is_winner
                    }
                })
            
            upper_bracket.append({
                "round_name": f"ROUND {r_num}",
                "matches": matches
            })

        if len(upper_bracket) > 1:
            upper_bracket[-1]["round_name"] = "GRAND FINAL"
        if len(upper_bracket) > 2:
            upper_bracket[-2]["round_name"] = "SEMI-FINAL"

        return {"upper_bracket": upper_bracket}