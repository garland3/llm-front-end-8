import logging
import asyncio
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

from fastmcp import Client
from app.services.mcp_service import MCPService
from app.core.logging import log_exception

logger = logging.getLogger(__name__)

@dataclass
class ToolSchema:
    """Represents a tool schema for LLM consumption."""
    name: str
    description: str
    parameters: Dict[str, Any]
    tool_id: str  # MCP server tool ID
    server_tool_name: str  # Actual tool name in the MCP server

class ToolSchemaService:
    """Service to generate LLM-compatible tool schemas from FastMCP servers."""
    
    def __init__(self, mcp_service: MCPService):
        self.mcp_service = mcp_service
        self._schema_cache = {}  # Cache schemas to avoid repeated MCP calls
        self._cache_valid = False
    
    async def get_tool_schemas_for_user(self, tool_ids: List[str], user_email: str) -> List[Dict[str, Any]]:
        """
        Get LLM-compatible tool schemas for the specified tool IDs and user.
        
        Args:
            tool_ids: List of MCP tool IDs to get schemas for
            user_email: User email for access validation
            
        Returns:
            List of tool schemas compatible with LLM function calling
        """
        try:
            schemas = []
            
            for tool_id in tool_ids:
                # Validate user access
                validations = await self.mcp_service.validate_tool_access([tool_id], user_email)
                if not validations or not validations[0]['has_access']:
                    logger.warning(f"User {user_email} does not have access to tool {tool_id}")
                    continue
                
                # Get tool schemas from the MCP server
                tool_schemas = await self._get_schemas_for_tool(tool_id, user_email)
                schemas.extend(tool_schemas)
            
            logger.info(f"Generated {len(schemas)} tool schemas for user {user_email}")
            return schemas
            
        except Exception as e:
            log_exception(logger, e, f"getting tool schemas for {user_email}")
            return []
    
    async def _get_schemas_for_tool(self, tool_id: str, user_email: str) -> List[Dict[str, Any]]:
        """Get schemas for all tools in a specific MCP server."""
        try:
            tool_info = self.mcp_service.tools.get(tool_id)
            if not tool_info or tool_info['type'] != 'fastmcp':
                logger.warning(f"Tool {tool_id} is not a FastMCP tool")
                return []
            
            # Get MCP client for this tool
            client = await self.mcp_service._get_mcp_client(tool_info)
            
            # List all available tools from the MCP server
            mcp_tools = await client.list_tools()
            
            schemas = []
            for mcp_tool in mcp_tools:
                schema = self._convert_mcp_tool_to_llm_schema(mcp_tool, tool_id)
                if schema:
                    schemas.append(schema)
            
            return schemas
            
        except Exception as e:
            log_exception(logger, e, f"getting schemas for tool {tool_id}")
            return []
    
    def _convert_mcp_tool_to_llm_schema(self, mcp_tool: Any, tool_id: str) -> Optional[Dict[str, Any]]:
        """Convert an MCP tool to LLM-compatible schema."""
        try:
            # Extract tool information
            tool_name = mcp_tool.name
            description = getattr(mcp_tool, 'description', '') or f"Tool from {tool_id} MCP server"
            
            # Convert input schema to LLM format
            input_schema = getattr(mcp_tool, 'inputSchema', {})
            
            # Build LLM-compatible schema
            llm_schema = {
                "type": "function",
                "function": {
                    "name": f"{tool_id}_{tool_name}",  # Prefix with tool_id to avoid conflicts
                    "description": description,
                    "parameters": self._convert_parameters_schema(input_schema)
                },
                # Store metadata for execution
                "_mcp_metadata": {
                    "tool_id": tool_id,
                    "server_tool_name": tool_name
                }
            }
            
            return llm_schema
            
        except Exception as e:
            log_exception(logger, e, f"converting MCP tool {getattr(mcp_tool, 'name', 'unknown')} to LLM schema")
            return None
    
    def _convert_parameters_schema(self, input_schema: Dict[str, Any]) -> Dict[str, Any]:
        """Convert MCP input schema to LLM function parameters schema."""
        if not input_schema:
            return {
                "type": "object",
                "properties": {},
                "required": []
            }
        
        # MCP schemas are typically JSON Schema format already
        # Ensure they have the required structure for LLM function calling
        if "type" not in input_schema:
            input_schema["type"] = "object"
        
        if "properties" not in input_schema:
            input_schema["properties"] = {}
            
        if "required" not in input_schema:
            input_schema["required"] = []
        
        return input_schema
    
    async def execute_tool_call(self, function_name: str, arguments: Dict[str, Any], user_email: str) -> Dict[str, Any]:
        """
        Execute a tool call from an LLM response.
        
        Args:
            function_name: LLM function name (format: tool_id_server_tool_name)
            arguments: Function arguments from LLM
            user_email: User email for access validation
            
        Returns:
            Tool execution result
        """
        try:
            # Parse function name to extract tool_id and server_tool_name
            if '_' not in function_name:
                raise ValueError(f"Invalid function name format: {function_name}")
            
            parts = function_name.split('_', 1)
            tool_id = parts[0]
            server_tool_name = parts[1]
            
            # Validate access
            validations = await self.mcp_service.validate_tool_access([tool_id], user_email)
            if not validations or not validations[0]['has_access']:
                raise ValueError(f"Access denied to tool {tool_id}")
            
            # Get the MCP client and execute the tool
            tool_info = self.mcp_service.tools.get(tool_id)
            if not tool_info:
                raise ValueError(f"Tool {tool_id} not found")
            
            client = await self.mcp_service._get_mcp_client(tool_info)
            result = await client.call_tool(server_tool_name, arguments)
            
            return {
                "success": True,
                "result": result.data if hasattr(result, 'data') else str(result),
                "tool_id": tool_id,
                "tool_name": server_tool_name
            }
            
        except Exception as e:
            log_exception(logger, e, f"executing tool call {function_name}")
            return {
                "success": False,
                "error": str(e),
                "tool_id": tool_id if 'tool_id' in locals() else "unknown",
                "tool_name": function_name
            }
    
    async def get_all_available_schemas(self, user_email: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get all available tool schemas organized by MCP server for a user.
        
        Returns:
            Dictionary mapping tool_id to list of available schemas
        """
        try:
            available_tools = await self.mcp_service.get_available_tools(user_email)
            
            all_schemas = {}
            for tool in available_tools:
                if tool.get('type') == 'fastmcp' and 'access_reason' not in tool:
                    tool_id = tool['id']
                    schemas = await self._get_schemas_for_tool(tool_id, user_email)
                    if schemas:
                        all_schemas[tool_id] = schemas
            
            return all_schemas
            
        except Exception as e:
            log_exception(logger, e, f"getting all available schemas for {user_email}")
            return {}
    
    def invalidate_cache(self):
        """Invalidate the schema cache to force refresh on next request."""
        self._schema_cache.clear()
        self._cache_valid = False
        logger.debug("Tool schema cache invalidated")