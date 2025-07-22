import pytest
import os
from unittest.mock import patch
from app.services.mcp_service import MCPService

class TestMCPService:
    def setup_method(self):
        with patch.dict(os.environ, {'DEBUG': 'true'}):
            self.mcp_service = MCPService()

    @pytest.mark.asyncio
    async def test_get_available_tools(self):
        tools = await self.mcp_service.get_available_tools("test@test.com")
        assert isinstance(tools, list)

    @pytest.mark.asyncio
    async def test_validate_tool_access_valid_tools(self):
        validations = await self.mcp_service.validate_tool_access(
            ["filesystem"], "test@test.com"
        )
        assert len(validations) == 1
        assert validations[0]['tool_id'] == "filesystem"
        assert isinstance(validations[0]['has_access'], bool)

    @pytest.mark.asyncio
    async def test_validate_tool_access_invalid_tools(self):
        validations = await self.mcp_service.validate_tool_access(
            ["nonexistent"], "test@test.com"
        )
        assert len(validations) == 1
        assert validations[0]['tool_id'] == "nonexistent"
        assert validations[0]['has_access'] == False
        assert "not found" in validations[0]['reason'].lower()

    @pytest.mark.asyncio
    async def test_get_tool_details_valid(self):
        if 'filesystem' in self.mcp_service.tools:
            tool = await self.mcp_service.get_tool_details("filesystem", "test@test.com")
            assert tool is not None
            assert tool['id'] == "filesystem"

    @pytest.mark.asyncio
    async def test_get_tool_details_invalid(self):
        tool = await self.mcp_service.get_tool_details("nonexistent", "test@test.com")
        assert tool is None

    @pytest.mark.asyncio
    async def test_get_tool_resources(self):
        if 'filesystem' in self.mcp_service.tools:
            resources = await self.mcp_service.get_tool_resources("filesystem", "test@test.com")
            assert isinstance(resources, list)