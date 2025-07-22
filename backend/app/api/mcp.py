import logging
from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel
from typing import List, Dict, Any

from app.services.mcp_service import MCPService
from app.services.tool_schema_service import ToolSchemaService
from app.core.logging import log_exception

logger = logging.getLogger(__name__)
router = APIRouter()

class MCPValidationRequest(BaseModel):
    tool_ids: List[str]

class ToolSchemaRequest(BaseModel):
    tool_ids: List[str]

class ToolExecutionRequest(BaseModel):
    function_name: str
    arguments: Dict[str, Any]

def get_mcp_service() -> MCPService:
    return MCPService()

def get_tool_schema_service() -> ToolSchemaService:
    mcp_service = MCPService()
    return ToolSchemaService(mcp_service)

def get_user_email(request: Request) -> str:
    return getattr(request.state, 'user_email', 'unknown')

@router.get("/tools")
async def get_tools(
    request: Request,
    mcp_service: MCPService = Depends(get_mcp_service),
    user_email: str = Depends(get_user_email)
) -> List[Dict[str, Any]]:
    try:
        tools = await mcp_service.get_available_tools(user_email)
        return tools
    except Exception as e:
        log_exception(logger, e, "retrieving MCP tools")
        raise HTTPException(status_code=500, detail="Failed to retrieve MCP tools")

@router.get("/tools/{tool_id}")
async def get_tool_details(
    tool_id: str,
    request: Request,
    mcp_service: MCPService = Depends(get_mcp_service),
    user_email: str = Depends(get_user_email)
) -> Dict[str, Any]:
    try:
        tool = await mcp_service.get_tool_details(tool_id, user_email)
        if not tool:
            raise HTTPException(status_code=404, detail="Tool not found")
        return tool
    except HTTPException:
        raise
    except Exception as e:
        log_exception(logger, e, f"retrieving tool details for {tool_id}")
        raise HTTPException(status_code=500, detail="Failed to retrieve tool details")

@router.get("/tools/{tool_id}/resources")
async def get_tool_resources(
    tool_id: str,
    request: Request,
    mcp_service: MCPService = Depends(get_mcp_service),
    user_email: str = Depends(get_user_email)
) -> Dict[str, Any]:
    try:
        resources = await mcp_service.get_tool_resources(tool_id, user_email)
        return {"resources": resources}
    except Exception as e:
        log_exception(logger, e, f"retrieving resources for tool {tool_id}")
        raise HTTPException(status_code=500, detail="Failed to retrieve tool resources")

@router.post("/validate")
async def validate_tool_access(
    validation_request: MCPValidationRequest,
    request: Request,
    mcp_service: MCPService = Depends(get_mcp_service),
    user_email: str = Depends(get_user_email)
) -> List[Dict[str, Any]]:
    try:
        validations = await mcp_service.validate_tool_access(
            validation_request.tool_ids, 
            user_email
        )
        return validations
    except Exception as e:
        log_exception(logger, e, "validating tool access")
        raise HTTPException(status_code=500, detail="Failed to validate tool access")

@router.post("/tools/{tool_id}/execute")
async def execute_tool(
    tool_id: str,
    request: Request,
    mcp_service: MCPService = Depends(get_mcp_service),
    user_email: str = Depends(get_user_email)
) -> Dict[str, Any]:
    try:
        body = await request.json()
        result = await mcp_service.execute_tool(tool_id, body, user_email)
        return result
    except HTTPException:
        raise
    except Exception as e:
        log_exception(logger, e, f"executing tool {tool_id}")
        raise HTTPException(status_code=500, detail="Failed to execute tool")

@router.post("/schemas")
async def get_tool_schemas(
    schema_request: ToolSchemaRequest,
    request: Request,
    tool_schema_service: ToolSchemaService = Depends(get_tool_schema_service),
    user_email: str = Depends(get_user_email)
) -> Dict[str, Any]:
    """Get LLM-compatible tool schemas for the specified tools."""
    try:
        schemas = await tool_schema_service.get_tool_schemas_for_user(
            schema_request.tool_ids, user_email
        )
        return {
            "schemas": schemas,
            "count": len(schemas),
            "tool_ids": schema_request.tool_ids
        }
    except Exception as e:
        log_exception(logger, e, "retrieving tool schemas")
        raise HTTPException(status_code=500, detail="Failed to retrieve tool schemas")

@router.get("/schemas/all")
async def get_all_tool_schemas(
    request: Request,
    tool_schema_service: ToolSchemaService = Depends(get_tool_schema_service),
    user_email: str = Depends(get_user_email)
) -> Dict[str, Any]:
    """Get all available tool schemas organized by MCP server."""
    try:
        all_schemas = await tool_schema_service.get_all_available_schemas(user_email)
        return {
            "schemas_by_tool": all_schemas,
            "total_servers": len(all_schemas),
            "total_schemas": sum(len(schemas) for schemas in all_schemas.values())
        }
    except Exception as e:
        log_exception(logger, e, "retrieving all tool schemas")
        raise HTTPException(status_code=500, detail="Failed to retrieve all tool schemas")

@router.post("/execute")
async def execute_tool_call(
    execution_request: ToolExecutionRequest,
    request: Request,
    tool_schema_service: ToolSchemaService = Depends(get_tool_schema_service),
    user_email: str = Depends(get_user_email)
) -> Dict[str, Any]:
    """Execute a tool call from an LLM response."""
    try:
        result = await tool_schema_service.execute_tool_call(
            execution_request.function_name,
            execution_request.arguments,
            user_email
        )
        return result
    except Exception as e:
        log_exception(logger, e, f"executing tool call {execution_request.function_name}")
        raise HTTPException(status_code=500, detail="Failed to execute tool call")