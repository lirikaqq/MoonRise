# backend/app/ws/connection_manager.py
from fastapi import WebSocket
from typing import Dict, List

class ConnectionManager:
    def __init__(self):
        # Словарь для хранения подключений. Ключ - ID сессии драфта, значение - список сокетов.
        self.active_connections: Dict[int, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, session_id: int):
        await websocket.accept()
        if session_id not in self.active_connections:
            self.active_connections[session_id] = []
        self.active_connections[session_id].append(websocket)

    def disconnect(self, websocket: WebSocket, session_id: int):
        if session_id in self.active_connections:
            self.active_connections[session_id].remove(websocket)
            # Если в комнате не осталось никого, удаляем саму комнату
            if not self.active_connections[session_id]:
                del self.active_connections[session_id]

    async def broadcast(self, message: str, session_id: int):
        if session_id in self.active_connections:
            for connection in self.active_connections[session_id]:
                await connection.send_text(message)

# Создаем один глобальный экземпляр менеджера
manager = ConnectionManager()