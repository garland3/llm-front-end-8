import os
import json
import logging
import asyncio
from typing import Dict, List, Any, Optional
from pathlib import Path

from fastmcp import Client
from app.auth.authorization import is_user_in_group
from app.core.logging import log_exception
from app.core.config import get_settings, get_project_root

logger = logging.getLogger(__name__)

class MCPService:
    def __init__(self):
        settings = get_settings()
        project_root = get_project_root()
        
        self.mcp_directory = project_root / "mcp"
        self.config_file = project_root / settings.mcp_config_path
        self.tools = {}
        self.external_mcps = {}
        self.mcp_clients = {}  # Store active MCP clients
        self._load_mcp_tools()
        
        # Register this instance for global cleanup
        try:
            from app.main import register_mcp_service
            register_mcp_service(self)
        except ImportError:
            # If we can't import register function, it's fine
            pass

    def _load_mcp_tools(self):
        try:
            self._load_builtin_tools()
            self._load_external_mcps()
            logger.info(f"Loaded {len(self.tools)} MCP tools")
        except Exception as e:
            log_exception(logger, e, "loading MCP tools")

    def _load_builtin_tools(self):
        if not self.mcp_directory.exists():
            logger.warning(f"MCP directory {self.mcp_directory} does not exist")
            return

        for tool_dir in self.mcp_directory.iterdir():
            if tool_dir.is_dir() and not tool_dir.name.startswith('.'):
                try:
                    self._load_tool_from_directory(tool_dir)
                except Exception as e:
                    log_exception(logger, e, f"loading tool from {tool_dir}")

    def _load_tool_from_directory(self, tool_dir: Path):
        config_path = tool_dir / "tool.json"
        if not config_path.exists():
            logger.warning(f"No tool.json found in {tool_dir}")
            return

        with open(config_path, 'r') as f:
            tool_config = json.load(f)

        tool_id = tool_config.get('id', tool_dir.name)
        
        # Check if there's a server.py file for fastmcp integration
        server_path = tool_dir / "server.py"
        
        self.tools[tool_id] = {
            'id': tool_id,
            'name': tool_config.get('name', tool_id),
            'description': tool_config.get('description', ''),
            'exclusive': tool_config.get('exclusive', False),
            'required_group': tool_config.get('required_group', 'default'),
            'type': 'fastmcp' if server_path.exists() else 'builtin',
            'path': str(tool_dir),
            'server_path': str(server_path) if server_path.exists() else None,
            'command': tool_config.get('command', []),
            'resources': tool_config.get('resources', []),
            'templates': tool_config.get('templates', [])
        }

    def _load_external_mcps(self):
        if not self.config_file.exists():
            logger.debug(f"No external MCP config file found at {self.config_file}")
            return

        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)

            external_mcps = config.get('external_mcps', [])
            for mcp_config in external_mcps:
                tool_id = mcp_config['id']
                self.tools[tool_id] = {
                    'id': tool_id,
                    'name': mcp_config.get('name', tool_id),
                    'description': mcp_config.get('description', ''),
                    'exclusive': mcp_config.get('exclusive', False),
                    'required_group': mcp_config.get('required_group', 'default'),
                    'type': 'external',
                    'endpoint': mcp_config.get('endpoint', ''),
                    'resources': mcp_config.get('resources', []),
                    'templates': mcp_config.get('templates', [])
                }

        except Exception as e:
            log_exception(logger, e, "loading external MCP config")

    async def get_available_tools(self, user_email: str) -> List[Dict[str, Any]]:
        try:
            available_tools = []
            
            for tool in self.tools.values():
                has_access = is_user_in_group(user_email, tool['required_group'])
                tool_info = tool.copy()
                
                if not has_access:
                    tool_info['access_reason'] = f"Requires group: {tool['required_group']}"
                
                # For FastMCP tools, try to get additional info from the server
                if tool['type'] == 'fastmcp' and has_access:
                    try:
                        client = await self._get_mcp_client(tool)
                        mcp_tools = await client.list_tools()
                        tool_info['mcp_tools'] = [
                            {
                                'name': t.name,
                                'description': getattr(t, 'description', ''),
                                'input_schema': getattr(t, 'inputSchema', {})
                            } for t in mcp_tools
                        ]
                        tool_info['mcp_tools_count'] = len(mcp_tools)
                    except Exception as e:
                        logger.warning(f"Could not get MCP tools for {tool['id']}: {str(e)}")
                        tool_info['mcp_error'] = str(e)
                
                available_tools.append(tool_info)
            
            logger.debug(f"Retrieved {len(available_tools)} tools for {user_email}")
            return available_tools
            
        except Exception as e:
            log_exception(logger, e, f"getting tools for {user_email}")
            return []

    async def get_tool_details(self, tool_id: str, user_email: str) -> Dict[str, Any]:
        try:
            tool = self.tools.get(tool_id)
            if not tool:
                return None
            
            has_access = is_user_in_group(user_email, tool['required_group'])
            tool_info = tool.copy()
            
            if not has_access:
                tool_info['access_reason'] = f"Requires group: {tool['required_group']}"
            
            return tool_info
            
        except Exception as e:
            log_exception(logger, e, f"getting tool details for {tool_id}")
            return None

    async def get_tool_resources(self, tool_id: str, user_email: str) -> List[Dict[str, Any]]:
        try:
            tool = self.tools.get(tool_id)
            if not tool:
                return []
            
            has_access = is_user_in_group(user_email, tool['required_group'])
            if not has_access:
                return []
            
            return tool.get('resources', [])
            
        except Exception as e:
            log_exception(logger, e, f"getting resources for tool {tool_id}")
            return []

    async def validate_tool_access(self, tool_ids: List[str], user_email: str) -> List[Dict[str, Any]]:
        try:
            validations = []
            
            for tool_id in tool_ids:
                tool = self.tools.get(tool_id)
                if not tool:
                    validations.append({
                        'tool_id': tool_id,
                        'has_access': False,
                        'reason': 'Tool not found'
                    })
                    continue
                
                has_access = is_user_in_group(user_email, tool['required_group'])
                validations.append({
                    'tool_id': tool_id,
                    'has_access': has_access,
                    'reason': 'Access granted' if has_access else f"Requires group: {tool['required_group']}"
                })
            
            return validations
            
        except Exception as e:
            log_exception(logger, e, f"validating tool access for {user_email}")
            return []

    async def execute_tool(self, tool_id: str, parameters: Dict[str, Any], user_email: str) -> Dict[str, Any]:
        try:
            tool = self.tools.get(tool_id)
            if not tool:
                raise ValueError(f"Tool {tool_id} not found")
            
            has_access = is_user_in_group(user_email, tool['required_group'])
            if not has_access:
                raise ValueError(f"Access denied to tool {tool_id}")
            
            if tool['type'] == 'fastmcp':
                return await self._execute_fastmcp_tool(tool, parameters, user_email)
            elif tool['type'] == 'builtin':
                return await self._execute_builtin_tool(tool, parameters, user_email)
            elif tool['type'] == 'external':
                return await self._execute_external_tool(tool, parameters, user_email)
            else:
                raise ValueError(f"Unknown tool type: {tool['type']}")
            
        except Exception as e:
            log_exception(logger, e, f"executing tool {tool_id}")
            raise

    async def _execute_builtin_tool(self, tool: Dict[str, Any], parameters: Dict[str, Any], user_email: str) -> Dict[str, Any]:
        logger.info(f"Executing builtin tool {tool['id']} for {user_email}")
        
        return {
            'tool_id': tool['id'],
            'result': f"Mock execution of builtin tool {tool['name']} with parameters: {parameters}",
            'success': True
        }

    async def _execute_fastmcp_tool(self, tool: Dict[str, Any], parameters: Dict[str, Any], user_email: str) -> Dict[str, Any]:
        """Execute a FastMCP tool by connecting to its server."""
        logger.info(f"Executing FastMCP tool {tool['id']} for {user_email}")
        
        try:
            # Get or create MCP client for this tool
            client = await self._get_mcp_client(tool)
            
            # List available tools from the server
            available_tools = await client.list_tools()
            
            if not available_tools:
                return {
                    'tool_id': tool['id'],
                    'success': False,
                    'error': 'No tools available from MCP server'
                }
            
            # For now, execute the first available tool
            # In a more sophisticated implementation, you'd map specific tool names
            tool_name = available_tools[0].name
            
            # Execute the tool
            result = await client.call_tool(tool_name, parameters)
            
            return {
                'tool_id': tool['id'],
                'tool_name': tool_name,
                'result': result.data if hasattr(result, 'data') else str(result),
                'success': True
            }
            
        except Exception as e:
            logger.error(f"FastMCP tool execution failed: {str(e)}")
            return {
                'tool_id': tool['id'],
                'success': False,
                'error': f"FastMCP execution failed: {str(e)}"
            }
    
    async def _get_mcp_client(self, tool: Dict[str, Any]) -> Client:
        """Get or create an MCP client for the given tool."""
        tool_id = tool['id']
        
        if tool_id not in self.mcp_clients:
            server_path = tool['server_path']
            if not server_path or not os.path.exists(server_path):
                raise ValueError(f"Server path not found for tool {tool_id}")
            
            # Create client pointing to the server script
            client = Client(server_path)
            
            # Connect to the server
            await client.__aenter__()
            
            self.mcp_clients[tool_id] = client
            logger.info(f"Created MCP client for tool {tool_id}")
        
        return self.mcp_clients[tool_id]
    
    async def close_mcp_clients(self):
        """Close all active MCP clients."""
        if not self.mcp_clients:
            return
            
        logger.info(f"Closing {len(self.mcp_clients)} MCP clients...")
        
        for tool_id, client in list(self.mcp_clients.items()):
            try:
                # Check if client has an active session
                if hasattr(client, '_session') and client._session:
                    await client.__aexit__(None, None, None)
                    logger.info(f"Closed MCP client for tool {tool_id}")
                else:
                    logger.info(f"MCP client for tool {tool_id} already closed")
            except Exception as e:
                logger.error(f"Error closing MCP client for {tool_id}: {str(e)}")
        
        self.mcp_clients.clear()
        logger.info("All MCP clients closed")

    async def _execute_external_tool(self, tool: Dict[str, Any], parameters: Dict[str, Any], user_email: str) -> Dict[str, Any]:
        logger.info(f"Executing external tool {tool['id']} for {user_email}")
        
        return {
            'tool_id': tool['id'],
            'result': f"Mock execution of external tool {tool['name']} at {tool['endpoint']} with parameters: {parameters}",
            'success': True
        }
    
    # function which can parse the tool_calls from the llm endpoint 
    # and then call the correct tool and return some message about the args, tool, and response. 
    # do for the N tools requested to call. 
    async def handle_tool_calls(self, tool_calls: List[Dict[str, Any]], user_email: str) -> List[Dict[str, Any]]:
        results = []
        
        for tool_call in tool_calls:
            tool_id = tool_call.get('tool_id')
            parameters = tool_call.get('parameters', {})
            
            try:
                result = await self.execute_tool(tool_id, parameters, user_email)
                results.append({
                    'tool_id': tool_id,
                    'result': result,
                    'success': True
                })
            except Exception as e:
                logger.error(f"Error executing tool {tool_id}: {str(e)}")
                results.append({
                    'tool_id': tool_id,
                    'error': str(e),
                    'success': False
                })
        
        return results