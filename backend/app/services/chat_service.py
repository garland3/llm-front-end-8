import logging
from typing import Dict, List, Any, AsyncGenerator
from datetime import datetime

from app.services.llm_service import LLMService
from app.services.mcp_service import MCPService
from app.services.tool_schema_service import ToolSchemaService
from app.core.logging import log_exception

logger = logging.getLogger(__name__)

class ChatService:
    def __init__(self):
        self.llm_service = LLMService()
        self.mcp_service = MCPService()
        self.tool_schema_service = ToolSchemaService(self.mcp_service)
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
            tool_schemas = []
            # add log information. for message, llm, tool, user. 
            logger.info(f"Processing message for user {user_email} with LLM provider {llm_provider} \n\tand tools {selected_tools} with message\n: {message}")

            # Validate and get tool schemas
            if selected_tools:
                validated_tools = await self.mcp_service.validate_tool_access(
                    selected_tools, user_email
                )
                authorized_tools = [
                    t['tool_id'] for t in validated_tools if t['has_access']
                ]
                tools_used = authorized_tools
                
                # Generate tool schemas for LLM
                if authorized_tools:
                    tool_schemas = await self.tool_schema_service.get_tool_schemas_for_user(
                        authorized_tools, user_email
                    )
            
            # Get LLM response with tool schemas
            response = await self.llm_service.generate_response(
                message, llm_provider, tools_used, user_email, tool_schemas
            )
            
            logger.info(f"Reponse from LLM for user {user_email}: {response}    ")
            # Handle tool calls if present
            final_response, executed_tools = await self._handle_tool_calls(
                response, user_email, message
            )
            
            self._store_chat_entry(user_email, message, final_response, llm_provider, executed_tools or tools_used)
            
            return {
                'content': final_response,
                'provider': llm_provider,
                'tools_used': executed_tools or tools_used,
                'tool_executions': executed_tools is not None
            }
            
        except Exception as e:
            log_exception(logger, e, f"processing message for {user_email}")
            raise
    
    async def _handle_tool_calls(self, response: Any, user_email: str, original_message: str) -> tuple[str, List[str]]:
        """Handle tool calls from LLM response and execute them."""
        try:
            # If response is just a string, no tool calls were made
            if isinstance(response, str):
                return response, None
            
            # If response is a dict with tool_calls, execute them
            if isinstance(response, dict) and 'tool_calls' in response:
                tool_calls = response['tool_calls']
                executed_tools = []
                tool_results = []
                
                logger.info(f"Processing {len(tool_calls)} tool calls for user {user_email}")
                
                for tool_call in tool_calls:
                    function_name = tool_call['function']['name']
                    arguments = tool_call['function']['arguments']
                    
                    # Parse arguments if they're a string
                    if isinstance(arguments, str):
                        import json
                        arguments = json.loads(arguments)
                    
                    # Execute the tool
                    result = await self.tool_schema_service.execute_tool_call(
                        function_name, arguments, user_email
                    )
                    
                    tool_results.append({
                        'function': function_name,
                        'arguments': arguments,
                        'result': result
                    })
                    
                    if result.get('success'):
                        executed_tools.append(result.get('tool_id', function_name))
                
                # Generate final response incorporating tool results
                final_response = self._format_response_with_tool_results(
                    response.get('content', ''), tool_results, original_message
                )
                
                return final_response, executed_tools
            
            # Fallback for unexpected response format
            return str(response), None
            
        except Exception as e:
            log_exception(logger, e, f"handling tool calls for {user_email}")
            # Return original response on error
            return str(response), None
    
    def _format_response_with_tool_results(
        self, 
        base_content: str, 
        tool_results: List[Dict[str, Any]], 
        original_message: str
    ) -> str:
        """Format the final response including tool execution results."""
        try:
            if not tool_results:
                return base_content
            
            response_parts = []
            
            if base_content:
                response_parts.append(base_content)
            
            # Add tool execution results
            response_parts.append("\n\nTool Execution Results:")
            
            for i, result in enumerate(tool_results, 1):
                function_name = result['function']
                success = result['result'].get('success', False)
                
                if success:
                    tool_output = result['result'].get('result', 'No output')
                    response_parts.append(
                        f"\n{i}. {function_name}: {tool_output}"
                    )
                else:
                    error = result['result'].get('error', 'Unknown error')
                    response_parts.append(
                        f"\n{i}. {function_name}: Error - {error}"
                    )
            
            return "".join(response_parts)
            
        except Exception as e:
            logger.error(f"Error formatting response with tool results: {str(e)}")
            return base_content or "Response generated with tool execution."

    async def process_message_stream(
        self,
        message: str,
        llm_provider: str,
        selected_tools: List[str],
        user_email: str
    ) -> AsyncGenerator[str, None]:
        """
        Called by the websocket manager to do a chat completion. This is the main chat completion method. 
        """
        try:
            tools_select_could_used = []
            
            if selected_tools:
                validated_tools = await self.mcp_service.validate_tool_access(
                    selected_tools, user_email
                )
                authorized_tools = [
                    t['tool_id'] for t in validated_tools if t['has_access']
                ]
                tools_select_could_used = authorized_tools
                # log the authorized selected tools.
                logger.info(f"Authorized tools for user {user_email}: {tools_select_could_used}")
            
            response_chunks = []
            tool_schemas = []
            if tools_select_could_used:
                tool_schemas = await self.tool_schema_service.get_tool_schemas_for_user(
                    tools_select_could_used, user_email
                )
            
            async for chunk in self.llm_service.generate_response_stream(
                message, llm_provider, tools_select_could_used, user_email, tool_schemas
            ):
                response_chunks.append(chunk)
                yield chunk
            
            if response_chunks is not None:
                # check if none or empty
                clean_chunks = [chunk for chunk in response_chunks if chunk]
                full_response = ''.join(clean_chunks)
            else:
                full_response = ""
            
            self._store_chat_entry(user_email, message, full_response, llm_provider, tools_select_could_used)
            
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