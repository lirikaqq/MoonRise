# backend/app/redis_client.py
import redis.asyncio as redis
from app.config import settings

# Создаем асинхронный пул соединений к Redis
# decode_responses=True автоматически декодирует ответы из байтов в строки UTF-8
redis_pool = redis.ConnectionPool.from_url(
    settings.REDIS_URL, decode_responses=True
)

def get_redis_client() -> redis.Redis:
    """
    Зависимость для получения клиента Redis из пула.
    Это эффективнее, чем создавать новое соединение на каждый запрос.
    """
    return redis.Redis(connection_pool=redis_pool)