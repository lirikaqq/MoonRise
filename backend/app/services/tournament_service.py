from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from app.models.tournament import Tournament
from app.schemas.tournament import TournamentCreate, TournamentUpdate
from fastapi import HTTPException
from typing import Optional
import logging

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

        # Фильтр по формату
        if format and format != "all":
            query = query.where(Tournament.format == format)

        # Поиск по названию
        if search:
            query = query.where(
                Tournament.title.ilike(f"%{search}%")
            )

        # Сортировка: сначала активные и featured, потом по дате
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

        # Обновляем только переданные поля
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(tournament, field, value)

        await db.commit()
        await db.refresh(tournament)
        return tournament

    @staticmethod
    async def delete(db: AsyncSession, tournament_id: int) -> dict:
        """Удалить турнир (soft delete)."""
        tournament = await TournamentService.get_by_id(db, tournament_id)
        tournament.is_active = False
        await db.commit()
        return {"message": f"Tournament {tournament.title} deleted"}

    @staticmethod
    async def update_status(
        db: AsyncSession,
        tournament_id: int,
        status: str
    ) -> Tournament:
        """Изменить статус турнира."""
        valid_statuses = ["upcoming", "registration", "checkin", "ongoing", "completed", "cancelled"]
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