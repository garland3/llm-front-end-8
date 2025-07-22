import os
import json
import logging
from typing import Dict, List, Any
from pathlib import Path

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
        self._load_mcp_tools()

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
        
        self.tools[tool_id] = {
            'id': tool_id,
            'name': tool_config.get('name', tool_id),
            'description': tool_config.get('description', ''),
            'exclusive': tool_config.get('exclusive', False),
            'required_group': tool_config.get('required_group', 'default'),
            'type': 'builtin',
            'path': str(tool_dir),
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
            
            if tool['type'] == 'builtin':
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

    async def _execute_external_tool(self, tool: Dict[str, Any], parameters: Dict[str, Any], user_email: str) -> Dict[str, Any]:
        logger.info(f"Executing external tool {tool['id']} for {user_email}")
        
        return {
            'tool_id': tool['id'],
            'result': f"Mock execution of external tool {tool['name']} at {tool['endpoint']} with parameters: {parameters}",
            'success': True
        }