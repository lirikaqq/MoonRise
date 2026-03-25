import httpx
import logging
from app.config import settings

logger = logging.getLogger(__name__)

# Базовый URL Overfast API
BASE_URL = settings.OVERFAST_API_URL


class OverfastService:
    """Сервис для работы с Overfast API (неофициальный API Overwatch)."""
    
    @staticmethod
    def _format_battletag(tag: str) -> str:
        """Преобразовать BattleTag из формата Player#1234 в Player-1234."""
        return tag.replace("#", "-")
    
    @staticmethod
    async def get_player_summary(battletag: str) -> dict | None:
        """
        Получить краткую информацию об игроке.
        
        Возвращает: ранг, уровень, аватар, endorsement и т.д.
        """
        player_id = OverfastService._format_battletag(battletag)
        url = f"{BASE_URL}/players/{player_id}/summary"
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)
                
                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"✅ Overfast: Got profile for {battletag}")
                    return data
                    
                elif response.status_code == 404:
                    logger.warning(f"⚠️ Overfast: Player {battletag} not found")
                    return None
                    
                else:
                    logger.error(f"❌ Overfast: Error {response.status_code} for {battletag}")
                    return None
                    
        except httpx.TimeoutException:
            logger.error(f"❌ Overfast: Timeout for {battletag}")
            return None
        except Exception as e:
            logger.error(f"❌ Overfast: Error for {battletag}: {e}")
            return None
    
    @staticmethod
    async def get_player_stats(battletag: str) -> dict | None:
        """
        Получить детальную статистику игрока.
        
        Возвращает: статистика по героям, время игры, винрейт и т.д.
        """
        player_id = OverfastService._format_battletag(battletag)
        url = f"{BASE_URL}/players/{player_id}/stats/summary"
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)
                
                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"✅ Overfast: Got stats for {battletag}")
                    return data
                    
                elif response.status_code == 404:
                    logger.warning(f"⚠️ Overfast: Stats not found for {battletag}")
                    return None
                    
                else:
                    logger.error(f"❌ Overfast: Error {response.status_code}")
                    return None
                    
        except httpx.TimeoutException:
            logger.error(f"❌ Overfast: Timeout for stats {battletag}")
            return None
        except Exception as e:
            logger.error(f"❌ Overfast: Error for stats {battletag}: {e}")
            return None
    
    @staticmethod
    def extract_rank_info(summary: dict) -> dict:
        """
        Извлечь информацию о ранге из summary.
        
        Возвращает:
        {
            "tank_rank": "Diamond 2",
            "damage_rank": "Master 4",
            "support_rank": "Diamond 1",
            "avatar_url": "https://...",
            "title": "...",
            "endorsement_level": 3
        }
        """
        result = {
            "tank_rank": None,
            "tank_tier": None,
            "damage_rank": None,
            "damage_tier": None,
            "support_rank": None,
            "support_tier": None,
            "ow_avatar_url": None,
            "title": None,
            "endorsement_level": None,
        }
        
        if not summary:
            return result
        
        # Аватар и endorsement
        result["ow_avatar_url"] = summary.get("avatar")
        result["title"] = summary.get("title")
        result["endorsement_level"] = (
            summary.get("endorsement", {}).get("level") if summary.get("endorsement") else None
        )
        
        # Ранги по ролям
        competitive = summary.get("competitive")
        if competitive and competitive.get("pc"):
            pc_ranks = competitive["pc"]
            
            for role in ["tank", "damage", "support"]:
                role_data = pc_ranks.get(role)
                if role_data:
                    result[f"{role}_rank"] = role_data.get("division")
                    result[f"{role}_tier"] = role_data.get("tier")
        
        return result