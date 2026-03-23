import httpx
from typing import Optional
from app.config import settings


DISCORD_API_URL = "https://discord.com/api/v10"
DISCORD_OAUTH_URL = "https://discord.com/api/oauth2"


def get_discord_login_url() -> str:
    """Получить URL для авторизации через Discord."""
    params = {
        "client_id": settings.DISCORD_CLIENT_ID,
        "redirect_uri": settings.DISCORD_REDIRECT_URI,
        "response_type": "code",
        "scope": "identify",  # Получаем только базовую информацию о пользователе
    }
    query = "&".join(f"{k}={v}" for k, v in params.items())
    return f"{DISCORD_OAUTH_URL}/authorize?{query}"


async def exchange_code_for_token(code: str) -> Optional[dict]:
    """Обменять код авторизации на access token."""
    data = {
        "client_id": settings.DISCORD_CLIENT_ID,
        "client_secret": settings.DISCORD_CLIENT_SECRET,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": settings.DISCORD_REDIRECT_URI,
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{DISCORD_OAUTH_URL}/token",
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Discord token error: {response.status_code} - {response.text}")
            return None


async def get_discord_user(access_token: str) -> Optional[dict]:
    """Получить информацию о пользователе Discord."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{DISCORD_API_URL}/users/@me",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Discord user error: {response.status_code} - {response.text}")
            return None