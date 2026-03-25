from fastapi import APIRouter
from app.services.overfast import OverfastService

router = APIRouter(prefix="/overfast", tags=["overfast"])


@router.get("/player/{battletag}")
async def get_overfast_player(battletag: str):
    """
    Получить данные игрока из Overfast API.
    
    BattleTag формат: Player-1234 (с дефисом, не решёткой)
    """
    # Заменяем дефис обратно на решётку для API
    tag = battletag.replace("-", "#")
    
    summary = await OverfastService.get_player_summary(tag)
    
    if not summary:
        return {"error": "Player not found", "battletag": tag}
    
    rank_info = OverfastService.extract_rank_info(summary)
    
    return {
        "battletag": tag,
        "summary": summary,
        "ranks": rank_info
    }


@router.get("/player/{battletag}/stats")
async def get_overfast_player_stats(battletag: str):
    """Получить статистику игрока из Overfast API."""
    tag = battletag.replace("-", "#")
    
    stats = await OverfastService.get_player_stats(tag)
    
    if not stats:
        return {"error": "Stats not found", "battletag": tag}
    
    return {
        "battletag": tag,
        "stats": stats
    }