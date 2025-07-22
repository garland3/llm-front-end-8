import json
import logging
from typing import Dict, Any
from fastapi import WebSocket, WebSocketDisconnect
from fastapi.routing import APIRouter

from app.core.logging import log_exception
from app.services.chat_service import ChatService

logger = logging.getLogger(__name__)
router = APIRouter()

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.chat_service = ChatService()

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        logger.info(f"WebSocket connected: {client_id}")

    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            logger.info(f"WebSocket disconnected: {client_id}")

    async def send_message(self, client_id: str, message: dict):
        if client_id in self.active_connections:
            try:
                await self.active_connections[client_id].send_text(json.dumps(message))
            except Exception as e:
                log_exception(logger, e, f"sending message to {client_id}")
                self.disconnect(client_id)

    async def handle_message(self, client_id: str, data: dict):
        message_type = data.get('type')
        
        try:
            if message_type == 'chat_message':
                await self.handle_chat_message(client_id, data)
            else:
                logger.warning(f"Unknown message type: {message_type}")
                await self.send_message(client_id, {
                    'type': 'error',
                    'error': f'Unknown message type: {message_type}'
                })
        except Exception as e:
            log_exception(logger, e, f"handling message type {message_type}")
            await self.send_message(client_id, {
                'type': 'chat_error',
                'error': str(e)
            })

    async def handle_chat_message(self, client_id: str, data: dict):
        message = data.get('message', '')
        llm_provider = data.get('llm_provider', '')
        selected_tools = data.get('selected_tools', [])
        
        if not message.strip():
            await self.send_message(client_id, {
                'type': 'chat_error',
                'error': 'Message cannot be empty'
            })
            return
        
        if not llm_provider:
            await self.send_message(client_id, {
                'type': 'chat_error',
                'error': 'LLM provider must be specified'
            })
            return

        websocket = self.active_connections.get(client_id)
        if not websocket:
            return

        user_email = getattr(websocket, 'user_email', 'unknown')
        
        await self.send_message(client_id, {
            'type': 'chat_stream',
            'start': True
        })

        async for chunk in self.chat_service.process_message_stream(
            message, llm_provider, selected_tools, user_email
        ):
            await self.send_message(client_id, {
                'type': 'chat_stream',
                'content': chunk
            })

        await self.send_message(client_id, {
            'type': 'chat_stream',
            'end': True
        })

manager = ConnectionManager()

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    client_id = f"{websocket.client.host}_{id(websocket)}"
    
    await manager.connect(websocket, client_id)
    
    if hasattr(websocket, 'state') and hasattr(websocket.state, 'user_email'):
        websocket.user_email = websocket.state.user_email
    else:
        websocket.user_email = "test@test.com"
    
    try:
        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                await manager.handle_message(client_id, message)
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON received: {e}")
                await manager.send_message(client_id, {
                    'type': 'error',
                    'error': 'Invalid JSON format'
                })
    except WebSocketDisconnect:
        manager.disconnect(client_id)
    except Exception as e:
        log_exception(logger, e, f"WebSocket handler for {client_id}")
        manager.disconnect(client_id)