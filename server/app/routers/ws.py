from typing import Dict
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()


class ConnectionManager:
    def __init__(self) -> None:
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, client_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections[client_id] = websocket

    def disconnect(self, client_id: str) -> None:
        self.active_connections.pop(client_id, None)

    async def send_to(self, client_id: str, message: dict) -> None:
        ws = self.active_connections.get(client_id)
        if ws:
            await ws.send_json(message)


manager = ConnectionManager()


@router.websocket("/gestures/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str) -> None:
    await manager.connect(client_id, websocket)
    try:
        while True:
            # Espera mensajes del cliente (por ejemplo, {type: "gesture", gesture: "next"})
            data = await websocket.receive_json()
            await manager.send_to(client_id, {"echo": data})
    except WebSocketDisconnect:
        manager.disconnect(client_id)
