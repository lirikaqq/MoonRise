from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.models.user import User, BattleTag
from app.schemas.player import BattleTagCreate
from app.services.overfast import OverfastService
from fastapi import HTTPException
import logging

logger = logging.getLogger(__name__)


class PlayerService:
    """Сервис для работы с профилями игроков."""

    @staticmethod
    async def get_player_by_id(db: AsyncSession, player_id: int) -> User:
        """Получить игрока по ID с баттлтегами."""
        result = await db.execute(
            select(User)
            .options(selectinload(User.battletags))
            .where(User.id == player_id)
        )
        player = result.scalar_one_or_none()
        
        if not player:
            raise HTTPException(status_code=404, detail="Player not found")
        
        return player

    @staticmethod
    async def get_player_by_discord_id(db: AsyncSession, discord_id: str) -> User:
        """Получить игрока по Discord ID."""
        result = await db.execute(
            select(User)
            .options(selectinload(User.battletags))
            .where(User.discord_id == discord_id)
        )
        player = result.scalar_one_or_none()
        
        if not player:
            raise HTTPException(status_code=404, detail="Player not found")
        
        return player

    @staticmethod
    async def add_battletag(db: AsyncSession, player_id: int, tag_data: BattleTagCreate) -> dict:
        """Добавить баттлтег и подтянуть данные из Overfast API."""
        # Проверяем что игрок существует
        result = await db.execute(select(User).where(User.id == player_id))
        player = result.scalar_one_or_none()
        
        if not player:
            raise HTTPException(status_code=404, detail="Player not found")
        
        # Проверяем есть ли уже баттлтеги
        result = await db.execute(
            select(BattleTag).where(BattleTag.user_id == player_id).limit(1)
        )
        existing_tag = result.scalar_one_or_none()
        
        is_primary = tag_data.is_primary or not existing_tag
        
        # Если новый основной — сбрасываем старый
        if is_primary:
            result = await db.execute(
                select(BattleTag).where(
                    BattleTag.user_id == player_id,
                    BattleTag.is_primary == True
                )
            )
            old_primary = result.scalar_one_or_none()
            if old_primary:
                old_primary.is_primary = False
        
        # Создаём баттлтег
        new_tag = BattleTag(
            user_id=player_id,
            tag=tag_data.tag,
            is_primary=is_primary
        )
        db.add(new_tag)
        
        # Подтягиваем данные из Overfast API
        overfast_data = None
        try:
            summary = await OverfastService.get_player_summary(tag_data.tag)
            if summary:
                overfast_data = OverfastService.extract_rank_info(summary)
                logger.info(f"🎮 Overfast data for {tag_data.tag}: {overfast_data}")
        except Exception as e:
            logger.warning(f"⚠️ Could not fetch Overfast data: {e}")
        
        await db.commit()
        await db.refresh(new_tag)
        
        return {
            "battletag": new_tag,
            "overfast_data": overfast_data
        }

    @staticmethod
    async def delete_battletag(db: AsyncSession, player_id: int, tag_id: int) -> dict:
        """Удалить баттлтег."""
        result = await db.execute(
            select(BattleTag).where(
                BattleTag.id == tag_id,
                BattleTag.user_id == player_id
            )
        )
        tag = result.scalar_one_or_none()
        
        if not tag:
            raise HTTPException(status_code=404, detail="BattleTag not found")
        
        if tag.is_primary:
            result = await db.execute(
                select(BattleTag).where(
                    BattleTag.user_id == player_id,
                    BattleTag.id != tag_id
                ).limit(1)
            )
            next_tag = result.scalar_one_or_none()
            if next_tag:
                next_tag.is_primary = True
        
        await db.delete(tag)
        await db.commit()
        return {"message": "BattleTag deleted successfully"}

    @staticmethod
    async def set_primary_battletag(db: AsyncSession, player_id: int, tag_id: int) -> BattleTag:
        """Сделать баттлтег основным."""
        result = await db.execute(
            select(BattleTag).where(
                BattleTag.id == tag_id,
                BattleTag.user_id == player_id
            )
        )
        tag = result.scalar_one_or_none()
        
        if not tag:
            raise HTTPException(status_code=404, detail="BattleTag not found")
        
        result = await db.execute(
            select(BattleTag).where(
                BattleTag.user_id == player_id,
                BattleTag.is_primary == True
            )
        )
        old_primary = result.scalar_one_or_none()
        if old_primary:
            old_primary.is_primary = False
        
        tag.is_primary = True
        await db.commit()
        await db.refresh(tag)
        return tag