from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional

from app.database import get_db
from app.models.user import User, BattleTag
from app.core.security import decode_access_token
from app.models.tournament import TournamentParticipant

router = APIRouter(tags=["users"])


async def get_current_user_optional(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """Возвращает юзера если токен валидный, иначе None."""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    
    try:
        token = auth_header.split(" ", 1)[1]
        payload = decode_access_token(token)
        if not payload or not payload.get("sub"):
            return None
        
        result = await db.execute(
            select(User).where(User.id == int(payload["sub"]))
        )
        return result.scalar_one_or_none()
    except (ValueError, IndexError, AttributeError):
        return None


async def get_current_user_required(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> User:
    """Возвращает юзера или кидает 401."""
    auth_header = request.headers.get("Authorization")
    
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        token = auth_header.split(" ", 1)[1]
        payload = decode_access_token(token)
        if not payload or not payload.get("sub"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        result = await db.execute(
            select(User).where(User.id == int(payload["sub"]))
        )
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token format",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ============================
# GET /users/me/battletags
# ============================

@router.get("/me/battletags")
async def get_my_battletags(
    current_user: User = Depends(get_current_user_required),
    db: AsyncSession = Depends(get_db)
):
    """Получить все BattleTag'и текущего юзера."""
    
    result = await db.execute(
        select(BattleTag)
        .where(BattleTag.user_id == current_user.id)
        .order_by(BattleTag.is_primary.desc(), BattleTag.created_at.asc())
    )
    battletags = result.scalars().all()

    return {
        "battletags": [
            {
                "id": bt.id,
                "tag": bt.tag,
                "is_primary": bt.is_primary,
                "created_at": bt.created_at.isoformat() if bt.created_at else None,
            }
            for bt in battletags
        ]
    }


# ============================
# GET /users/me
# ============================

@router.get("/me")
async def get_my_profile(
    current_user: User = Depends(get_current_user_required),
    db: AsyncSession = Depends(get_db)
):
    """Получить профиль текущего юзера."""
    return {
        "id": current_user.id,
        "discord_id": current_user.discord_id,
        "username": current_user.username,
        "display_name": current_user.display_name,
        "avatar_url": current_user.avatar_url,
        "role": current_user.role,
        "primary_role": current_user.primary_role,
        "secondary_role": current_user.secondary_role,
        "bio": current_user.bio,
        "is_banned": current_user.is_banned,
        "reputation_score": current_user.reputation_score,
        "created_at": current_user.created_at.isoformat() if current_user.created_at else None,
        "updated_at": current_user.updated_at.isoformat() if current_user.updated_at else None,
    }

@router.get("/me/applications")
async def get_my_all_applications(
    current_user: User = Depends(get_current_user_required),
    db: AsyncSession = Depends(get_db)
):
    """Получить все заявки текущего юзера (чтобы закрасить кнопки на фронте)."""
    result = await db.execute(
        select(TournamentParticipant.tournament_id, TournamentParticipant.status, TournamentParticipant.is_allowed)
        .where(TournamentParticipant.user_id == current_user.id)
    )
    rows = result.all()
    
    return [
        {
            "tournament_id": r.tournament_id,
            "status": r.status,
            "is_allowed": r.is_allowed
        }
        for r in rows
    ]