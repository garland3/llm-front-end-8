import pytest
import os
from unittest.mock import patch
from app.services.chat_service import ChatService

class TestChatService:
    def setup_method(self):
        with patch.dict(os.environ, {'DEBUG': 'true'}):
            self.chat_service = ChatService()

    @pytest.mark.asyncio
    async def test_process_message(self):
        response = await self.chat_service.process_message(
            "Hello", "openai-gpt4", [], "test@test.com"
        )
        assert 'content' in response
        assert 'provider' in response
        assert 'tools_used' in response
        assert isinstance(response['content'], str)
        assert len(response['content']) > 0

    @pytest.mark.asyncio
    async def test_process_message_with_tools(self):
        response = await self.chat_service.process_message(
            "Calculate 2+2", "openai-gpt4", ["calculator"], "test@test.com"
        )
        assert 'content' in response
        assert 'tools_used' in response
        assert isinstance(response['tools_used'], list)

    @pytest.mark.asyncio
    async def test_process_message_stream(self):
        chunks = []
        async for chunk in self.chat_service.process_message_stream(
            "Hello", "openai-gpt4", [], "test@test.com"
        ):
            chunks.append(chunk)
        
        assert len(chunks) > 0
        assert all(isinstance(chunk, str) for chunk in chunks)

    def test_get_chat_history_empty(self):
        history = self.chat_service.chat_history.get("newuser@test.com", [])
        assert history == []

    @pytest.mark.asyncio
    async def test_get_chat_history_after_message(self):
        await self.chat_service.process_message(
            "Hello", "openai-gpt4", [], "test@test.com"
        )
        
        history = await self.chat_service.get_chat_history("test@test.com")
        assert len(history) > 0
        assert 'user_message' in history[0]
        assert 'assistant_response' in history[0]