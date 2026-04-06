# backend/app/ws/draft_ws.py
import asyncio
import json # Убедись, что json импортирован
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession

import redis.asyncio as redis
from app.redis_client import redis_pool # Импортируем сам пул, а не get_redis_client
from app.ws.connection_manager import manager
from app.core.security import decode_access_token

router = APIRouter()

@router.websocket("/ws/draft/{session_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    session_id: int,
    token: str,
):
    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        await websocket.close(code=1008, reason="Invalid token")
        return
    
    await manager.connect(websocket, session_id)
    
    # Создаем новое подключение к Redis специально для этого сокета
    redis_client = redis.Redis(connection_pool=redis_pool)
    pubsub = redis_client.pubsub()
    channel = f"draft:{session_id}"
    await pubsub.subscribe(channel)

    try:
        async def redis_listener(ws: WebSocket):
            # Используем while True для большей надежности
            while True:
                message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                if message and message["type"] == "message":
                    await ws.send_text(message["data"])
                # Небольшая задержка, чтобы не загружать процессор
                await asyncio.sleep(0.01)

        async def client_listener(ws: WebSocket):
            async for _ in ws.iter_text():
                pass

        await asyncio.gather(
            redis_listener(websocket),
            client_listener(websocket)
        )

    except WebSocketDisconnect:
        manager.disconnect(websocket, session_id)
        print(f"Client disconnected from draft {session_id}")
    finally:
        await pubsub.unsubscribe(channel)
        await redis_client.close() # Закрываем соединение с Redis