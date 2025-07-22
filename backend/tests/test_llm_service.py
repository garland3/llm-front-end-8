import pytest
import os
from unittest.mock import patch
from app.services.llm_service import LLMService

class TestLLMService:
    def setup_method(self):
        with patch.dict(os.environ, {'DEBUG': 'true'}):
            self.llm_service = LLMService()

    @pytest.mark.asyncio
    async def test_get_available_providers(self):
        providers = await self.llm_service.get_available_providers("test@test.com")
        assert len(providers) > 0
        assert all('id' in p and 'name' in p for p in providers)

    @pytest.mark.asyncio
    async def test_get_provider_details_valid(self):
        provider = await self.llm_service.get_provider_details("openai-gpt4", "test@test.com")
        assert provider is not None
        assert provider['id'] == "openai-gpt4"
        assert provider['available'] == True

    @pytest.mark.asyncio
    async def test_get_provider_details_invalid(self):
        provider = await self.llm_service.get_provider_details("nonexistent", "test@test.com")
        assert provider is None

    @pytest.mark.asyncio
    async def test_validate_provider_access_valid(self):
        validation = await self.llm_service.validate_provider_access("openai-gpt4", "test@test.com")
        assert validation['provider_id'] == "openai-gpt4"
        assert validation['has_access'] == True

    @pytest.mark.asyncio
    async def test_validate_provider_access_invalid(self):
        validation = await self.llm_service.validate_provider_access("nonexistent", "test@test.com")
        assert validation['provider_id'] == "nonexistent"
        assert validation['has_access'] == False

    @pytest.mark.asyncio
    async def test_generate_response(self):
        response = await self.llm_service.generate_response(
            "Hello", "openai-gpt4", [], "test@test.com"
        )
        assert isinstance(response, str)
        assert len(response) > 0

    @pytest.mark.asyncio
    async def test_generate_response_stream(self):
        chunks = []
        async for chunk in self.llm_service.generate_response_stream(
            "Hello", "openai-gpt4", [], "test@test.com"
        ):
            chunks.append(chunk)
        
        assert len(chunks) > 0
        assert all(isinstance(chunk, str) for chunk in chunks)