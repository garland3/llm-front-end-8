import logging
from typing import Dict, List, Any, AsyncGenerator
from datetime import datetime

from app.services.llm_service import LLMService
from app.services.mcp_service import MCPService
from app.core.logging import log_exception

logger = logging.getLogger(__name__)

class ChatService:
    def __init__(self):
        self.llm_service = LLMService()
        self.mcp_service = MCPService()
        self.chat_history = {}

    async def process_message(
        self,
        message: str,
        llm_provider: str,
        selected_tools: List[str],
        user_email: str
    ) -> Dict[str, Any]:
        try:
            tools_used = []
            
            if selected_tools:
                validated_tools = await self.mcp_service.validate_tool_access(
                    selected_tools, user_email
                )
                authorized_tools = [
                    t['tool_id'] for t in validated_tools if t['has_access']
                ]
                tools_used = authorized_tools
            
            response = await self.llm_service.generate_response(
                message, llm_provider, tools_used, user_email
            )
            
            self._store_chat_entry(user_email, message, response, llm_provider, tools_used)
            
            return {
                'content': response,
                'provider': llm_provider,
                'tools_used': tools_used
            }
            
        except Exception as e:
            log_exception(logger, e, f"processing message for {user_email}")
            raise

    async def process_message_stream(
        self,
        message: str,
        llm_provider: str,
        selected_tools: List[str],
        user_email: str
    ) -> AsyncGenerator[str, None]:
        try:
            tools_used = []
            
            if selected_tools:
                validated_tools = await self.mcp_service.validate_tool_access(
                    selected_tools, user_email
                )
                authorized_tools = [
                    t['tool_id'] for t in validated_tools if t['has_access']
                ]
                tools_used = authorized_tools
            
            response_chunks = []
            async for chunk in self.llm_service.generate_response_stream(
                message, llm_provider, tools_used, user_email
            ):
                response_chunks.append(chunk)
                yield chunk
            
            full_response = ''.join(response_chunks)
            self._store_chat_entry(user_email, message, full_response, llm_provider, tools_used)
            
        except Exception as e:
            log_exception(logger, e, f"processing streaming message for {user_email}")
            yield f"Error: {str(e)}"

    def _store_chat_entry(
        self,
        user_email: str,
        message: str,
        response: str,
        provider: str,
        tools_used: List[str]
    ):
        if user_email not in self.chat_history:
            self.chat_history[user_email] = []
        
        entry = {
            'timestamp': datetime.now().isoformat(),
            'user_message': message,
            'assistant_response': response,
            'provider': provider,
            'tools_used': tools_used
        }
        
        self.chat_history[user_email].append(entry)
        
        if len(self.chat_history[user_email]) > 100:
            self.chat_history[user_email] = self.chat_history[user_email][-100:]

    async def get_chat_history(self, user_email: str, limit: int = 50) -> List[Dict[str, Any]]:
        try:
            history = self.chat_history.get(user_email, [])
            return history[-limit:] if limit else history
        except Exception as e:
            log_exception(logger, e, f"retrieving chat history for {user_email}")
            return []