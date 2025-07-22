import logging
import os
import yaml
import json
from typing import Dict, List, Any, AsyncGenerator
import asyncio
from pathlib import Path
from string import Template
import httpx

from app.auth.authorization import is_user_in_group
from app.core.logging import log_exception
from app.core.config import get_settings, get_project_root
from app.services.mcp_service import MCPService
from app.services.tool_schema_service import ToolSchemaService

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self):
        self.providers = {}
        self.mcp_service = MCPService()
        self.tool_schema_service = ToolSchemaService(self.mcp_service)
        self._load_models_config()

    def _load_models_config(self):
        """Load model configurations from YAML file"""
        try:
            settings = get_settings()
            project_root = get_project_root()
            config_path = project_root / settings.models_config_path
            
            if not config_path.exists():
                logger.warning(f"Models config file not found at {config_path}")
                self._load_default_models()
                return

            with open(config_path, 'r', encoding='utf-8') as f:
                config_content = f.read()
                
            config_template = Template(config_content)
            config_content = config_template.safe_substitute(os.environ)
            
            config = yaml.safe_load(config_content)
            
            models = config.get('models', [])
            for model in models:
                model_id = model.get('id')
                if model_id:
                    self.providers[model_id] = {
                        'id': model_id,
                        'name': model.get('name', model_id),
                        'model': model.get('model_name', ''),
                        'model_name': model.get('model_name', ''),
                        'model_url': model.get('model_url', ''),
                        'api_key': model.get('api_key', ''),
                        'provider': model.get('provider', ''),
                        'description': model.get('description', ''),
                        'available': model.get('available', True),
                        'required_group': model.get('required_group', 'default'),
                        'max_tokens': model.get('max_tokens', 4096),
                        'supports_streaming': model.get('supports_streaming', True)
                    }
            
            logger.info(f"Loaded {len(self.providers)} model providers from {config_path}")
            
        except Exception as e:
            log_exception(logger, e, "loading models config")
            self._load_default_models()

    def _load_default_models(self):
        """Load default model configurations as fallback"""
        logger.info("Loading default model configurations")
        self.providers = {
            'openai-gpt4': {
                'id': 'openai-gpt4',
                'name': 'OpenAI GPT-4',
                'model': 'gpt-4',
                'model_name': 'gpt-4',
                'model_url': 'https://api.openai.com/v1/chat/completions',
                'api_key': '',
                'provider': 'openai',
                'description': 'OpenAI GPT-4 model',
                'available': False,
                'required_group': 'mcp_users',
                'max_tokens': 8192,
                'supports_streaming': True
            },
            'openai-gpt3': {
                'id': 'openai-gpt3',
                'name': 'OpenAI GPT-3.5 Turbo',
                'model': 'gpt-3.5-turbo',
                'model_name': 'gpt-3.5-turbo',
                'model_url': 'https://api.openai.com/v1/chat/completions',
                'api_key': '',
                'provider': 'openai',
                'description': 'OpenAI GPT-3.5 Turbo model',
                'available': False,
                'required_group': 'default',
                'max_tokens': 4096,
                'supports_streaming': True
            }
        }

    async def get_available_providers(self, user_email: str) -> List[Dict[str, Any]]:
        try:
            available_providers = []
            
            for provider in self.providers.values():
                has_access = is_user_in_group(user_email, provider['required_group'])
                provider_info = provider.copy()
                provider_info['available'] = provider_info['available'] and has_access
                
                if not has_access:
                    provider_info['access_reason'] = f"Requires group: {provider['required_group']}"
                
                available_providers.append(provider_info)
            
            logger.debug(f"Retrieved {len(available_providers)} providers for {user_email}")
            return available_providers
            
        except Exception as e:
            log_exception(logger, e, f"getting providers for {user_email}")
            return []

    async def get_provider_details(self, provider_id: str, user_email: str) -> Dict[str, Any]:
        try:
            provider = self.providers.get(provider_id)
            if not provider:
                return None
            
            has_access = is_user_in_group(user_email, provider['required_group'])
            provider_info = provider.copy()
            provider_info['available'] = provider_info['available'] and has_access
            
            if not has_access:
                provider_info['access_reason'] = f"Requires group: {provider['required_group']}"
            
            return provider_info
            
        except Exception as e:
            log_exception(logger, e, f"getting provider details for {provider_id}")
            return None

    async def validate_provider_access(self, provider_id: str, user_email: str) -> Dict[str, Any]:
        try:
            provider = self.providers.get(provider_id)
            if not provider:
                return {
                    'provider_id': provider_id,
                    'has_access': False,
                    'reason': 'Provider not found'
                }
            
            has_access = is_user_in_group(user_email, provider['required_group'])
            
            return {
                'provider_id': provider_id,
                'has_access': has_access and provider['available'],
                'reason': 'Access granted' if has_access else f"Requires group: {provider['required_group']}"
            }
            
        except Exception as e:
            log_exception(logger, e, f"validating provider access for {provider_id}")
            return {
                'provider_id': provider_id,
                'has_access': False,
                'reason': f'Validation error: {str(e)}'
            }

    async def generate_response(
        self,
        message: str,
        provider_id: str,
        tools_used: List[str],
        user_email: str,
        tool_schemas: List[Dict[str, Any]] = None
    ) -> str:
        """NOT used by the steraming. So, likely not used. """
        try:
            provider = self.providers.get(provider_id)
            if not provider:
                raise ValueError(f"Provider {provider_id} not found")
            
            has_access = is_user_in_group(user_email, provider['required_group'])
            if not has_access or not provider['available']:
                raise ValueError(f"Access denied to provider {provider_id}")
            
            if provider['provider'] == 'test':
                response = await self._mock_llm_call(message, provider, tools_used, tool_schemas)
            else:
                response = await self._real_llm_call(message, provider, tools_used, tool_schemas)
            
            logger.info(f"Generated response for {user_email} using {provider_id}")
            
            return response
            
        except Exception as e:
            log_exception(logger, e, f"generating response for {user_email}")
            raise

    async def generate_response_stream(
        self,
        message: str,
        provider_id: str,
        tools_could_use: List[str],
        user_email: str,
        tool_schemas: List[Dict[str, Any]] = None
    ) -> AsyncGenerator[str, None]:
        """
        MAIN STREAMING RESPONSE GENERATION METHOD for the LLM calling. 
        """
        try:
            provider = self.providers.get(provider_id)
            if not provider:
                raise ValueError(f"Provider {provider_id} not found")
            
            has_access = is_user_in_group(user_email, provider['required_group'])
            if not has_access or not provider['available']:
                raise ValueError(f"Access denied to provider {provider_id}")
            
            if provider['provider'] == 'test':
                async for chunk in self._mock_llm_stream(message, provider, tools_could_use, tool_schemas):
                    yield chunk
            else:
                async for chunk in self._real_llm_stream(message, provider, tools_could_use, tool_schemas, user_email):
                    yield chunk
            
            logger.info(f"Generated streaming response for {user_email} using {provider_id}")
            
            
        except Exception as e:
            log_exception(logger, e, f"generating streaming response for {user_email}")
            yield f"Error: {str(e)}"

    async def _mock_llm_call(self, message: str, provider: Dict, tools_used: List[str], tool_schemas: List[Dict[str, Any]] = None) -> str:
        await asyncio.sleep(1)
        
        tools_info = f" (using tools: {', '.join(tools_used)})" if tools_used else ""
        schemas_info = f" with {len(tool_schemas)} tool schemas" if tool_schemas else ""
        
        return (
            f"This is a mock response from {provider['name']} {provider['model']} "
            f"to your message: '{message}'{tools_info}{schemas_info}. "
            f"In a real implementation, this would connect to the actual LLM provider."
        )

    async def _mock_llm_stream(self, message: str, provider: Dict, tools_used: List[str], tool_schemas: List[Dict[str, Any]] = None) -> AsyncGenerator[str, None]:
        tools_info = f" (using tools: {', '.join(tools_used)})" if tools_used else ""
        
        response_parts = [
            f"This is a mock streaming response from {provider['name']} {provider['model']} ",
            f"to your message: '{message}'{tools_info}. ",
            "In a real implementation, this would connect to the actual LLM provider ",
            "and stream the response back in real-time."
        ]
        
        for part in response_parts:
            for word in part.split():
                yield word + " "
                await asyncio.sleep(0.1)

    async def _real_llm_call(self, message: str, provider: Dict, tools_used: List[str], tool_schemas: List[Dict[str, Any]] = None) -> str:
        """Make actual API call to LLM provider"""
        try:
            if provider['provider'] == 'openai':
                return await self._call_openai(message, provider, tools_used, tool_schemas)
            elif provider['provider'] == 'anthropic':
                return await self._call_anthropic(message, provider, tools_used, tool_schemas)
            elif provider['provider'] == 'azure-openai':
                return await self._call_azure_openai(message, provider, tools_used, tool_schemas)
            elif provider['provider'] == 'ollama':
                return await self._call_ollama(message, provider, tools_used, tool_schemas)
            else:
                raise ValueError(f"Unsupported provider: {provider['provider']}")
        except Exception as e:
            logger.error(f"Error calling {provider['provider']}: {str(e)}")
            raise

    async def _real_llm_stream(self, message: str, provider: Dict, tools_could_use: List[str], tool_schemas: List[Dict[str, Any]] = None, user_email: str = "system") -> AsyncGenerator[str, None]:
        """Make actual streaming API call to LLM provider"""
        try:
            if provider['provider'] == 'openai':
                async for chunk in self._stream_openai(message, provider, tools_could_use, tool_schemas, user_email):
                    yield chunk
            elif provider['provider'] == 'anthropic':
                async for chunk in self._stream_anthropic(message, provider, tools_could_use, tool_schemas):
                    yield chunk
            elif provider['provider'] == 'azure-openai':
                async for chunk in self._stream_azure_openai(message, provider, tools_could_use, tool_schemas):
                    yield chunk
            elif provider['provider'] == 'ollama':
                async for chunk in self._stream_ollama(message, provider, tools_could_use, tool_schemas):
                    yield chunk
            else:
                raise ValueError(f"Unsupported provider: {provider['provider']}")
        except Exception as e:
            logger.error(f"Error streaming from {provider['provider']}: {str(e)}")
            yield f"Error: {str(e)}"

    async def _call_openai(self, message: str, provider: Dict, tools_used: List[str], tool_schemas: List[Dict[str, Any]] = None) -> Any:
        """Call OpenAI API"""
        headers = {
            "Authorization": f"Bearer {provider['api_key']}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": provider['model_name'],
            "messages": [
                {"role": "user", "content": message}
            ],
            "max_tokens": provider['max_tokens'],
            "temperature": 0.7
        }
        
        # Add tools if provided
        if tool_schemas:
            payload["tools"] = tool_schemas
            payload["tool_choice"] = "auto"
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(provider['model_url'], headers=headers, json=payload)
            response.raise_for_status()
            
            data = response.json()
            message = data['choices'][0]['message']
            
            # Check if the model wants to call tools
            if 'tool_calls' in message and message['tool_calls']:
                # Return the message with tool calls for processing by the calling service
                return {
                    'content': message.get('content', ''),
                    'tool_calls': message['tool_calls']
                }
            
            return message['content']

    async def _stream_openai(self, message: str, provider: Dict, tools_could_use: List[str], tool_schemas: List[Dict[str, Any]] = None, user_email: str = "system") -> AsyncGenerator[str, None]:
        """Stream from OpenAI API"""
        headers = {
            "Authorization": f"Bearer {provider['api_key']}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": provider['model_name'],
            "messages": [
                {"role": "user", "content": message}
            ],
            "max_tokens": provider['max_tokens'],
            "temperature": 0.7,
            "stream": True
        }
        
        # Add tools if provided
        if tool_schemas:
            payload["tools"] = tool_schemas
            payload["tool_choice"] = "auto"
        
        tool_calls_buffer = {}  # Buffer to accumulate tool call data
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            async with client.stream("POST", provider['model_url'], headers=headers, json=payload) as response:
                response.raise_for_status()
                
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:]  # Remove "data: " prefix
                        if data_str.strip() == "[DONE]":
                            break
                        
                        try:
                            data = json.loads(data_str)
                            if 'choices' in data and len(data['choices']) > 0:
                                delta = data['choices'][0].get('delta', {})
                                
                                # Handle regular content streaming
                                if 'content' in delta:
                                    yield delta['content']
                                
                                # Handle tool calls
                                if 'tool_calls' in delta:
                                    for tool_call_delta in delta['tool_calls']:
                                        index = tool_call_delta.get('index', 0)
                                        if index not in tool_calls_buffer:
                                            tool_calls_buffer[index] = {
                                                'id': '',
                                                'type': 'function',
                                                'function': {'name': '', 'arguments': ''}
                                            }
                                        
                                        # Accumulate tool call data
                                        if 'id' in tool_call_delta:
                                            tool_calls_buffer[index]['id'] += tool_call_delta['id']
                                        
                                        if 'function' in tool_call_delta:
                                            func_delta = tool_call_delta['function']
                                            if 'name' in func_delta:
                                                tool_calls_buffer[index]['function']['name'] += func_delta['name']
                                            if 'arguments' in func_delta:
                                                tool_calls_buffer[index]['function']['arguments'] += func_delta['arguments']
                                
                                # Check if streaming is finished and we have tool calls to execute
                                finish_reason = data['choices'][0].get('finish_reason')
                                if finish_reason == 'tool_calls' and tool_calls_buffer:
                                    # Execute tool calls and stream results
                                    async for tool_result_chunk in self._execute_and_stream_tool_calls(tool_calls_buffer, user_email):
                                        yield tool_result_chunk
                                        
                        except json.JSONDecodeError:
                            continue

    async def _execute_and_stream_tool_calls(self, tool_calls_buffer: Dict[int, Dict[str, Any]], user_email: str = "system") -> AsyncGenerator[str, None]:
        """Execute tool calls and stream the results to the user"""
        
        # Convert OpenAI tool call format for execution
        tool_calls = []
        for tool_call in tool_calls_buffer.values():
            try:
                function_name = tool_call['function']['name']
                args = json.loads(tool_call['function']['arguments'])
                tool_calls.append({
                    'function_name': function_name,
                    'arguments': args
                })
            except json.JSONDecodeError:
                yield f"\n\n🚫 **Error**: Invalid tool arguments for {tool_call['function']['name']}\n\n"
                continue
        
        if not tool_calls:
            return
        
        # Stream tool execution information
        yield f"\n\n🔧 **Executing {len(tool_calls)} tool call(s):**\n"
        
        for i, tool_call in enumerate(tool_calls, 1):
            function_name = tool_call['function_name']
            arguments = tool_call['arguments']
            
            # Stream tool call info
            yield f"\n**{i}. Tool:** `{function_name}`\n"
            yield f"**Arguments:** `{json.dumps(arguments)}`\n"
            
            try:
                # Execute the tool using the proper tool schema service
                result = await self.tool_schema_service.execute_tool_call(function_name, arguments, user_email)
                
                if result.get('success', False):
                    yield f"**✅ Result:** {result.get('result', 'Success')}\n"
                else:
                    error = result.get('error', 'Unknown error')
                    yield f"**❌ Error:** {error}\n"
                    
            except Exception as e:
                yield f"**❌ Error:** {str(e)}\n"
        
        yield f"\n**Tool execution completed.**\n\n"

    async def _call_anthropic(self, message: str, provider: Dict, tools_used: List[str], tool_schemas: List[Dict[str, Any]] = None) -> str:
        """Call Anthropic API"""
        headers = {
            "x-api-key": provider['api_key'],
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }
        
        payload = {
            "model": provider['model_name'],
            "max_tokens": provider['max_tokens'],
            "messages": [
                {"role": "user", "content": message}
            ]
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(provider['model_url'], headers=headers, json=payload)
            response.raise_for_status()
            
            data = response.json()
            return data['content'][0]['text']

    async def _stream_anthropic(self, message: str, provider: Dict, tools_used: List[str], tool_schemas: List[Dict[str, Any]] = None) -> AsyncGenerator[str, None]:
        """Stream from Anthropic API"""
        headers = {
            "x-api-key": provider['api_key'],
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }
        
        payload = {
            "model": provider['model_name'],
            "max_tokens": provider['max_tokens'],
            "messages": [
                {"role": "user", "content": message}
            ],
            "stream": True
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            async with client.stream("POST", provider['model_url'], headers=headers, json=payload) as response:
                response.raise_for_status()
                
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:]
                        if data_str.strip() == "[DONE]":
                            break
                        
                        try:
                            data = json.loads(data_str)
                            if data.get('type') == 'content_block_delta':
                                yield data['delta']['text']
                        except json.JSONDecodeError:
                            continue

    async def _call_azure_openai(self, message: str, provider: Dict, tools_used: List[str], tool_schemas: List[Dict[str, Any]] = None) -> str:
        """Call Azure OpenAI API"""
        headers = {
            "api-key": provider['api_key'],
            "Content-Type": "application/json"
        }
        
        payload = {
            "messages": [
                {"role": "user", "content": message}
            ],
            "max_tokens": provider['max_tokens'],
            "temperature": 0.7
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(provider['model_url'], headers=headers, json=payload)
            response.raise_for_status()
            
            data = response.json()
            return data['choices'][0]['message']['content']

    async def _stream_azure_openai(self, message: str, provider: Dict, tools_used: List[str], tool_schemas: List[Dict[str, Any]] = None) -> AsyncGenerator[str, None]:
        """Stream from Azure OpenAI API"""
        headers = {
            "api-key": provider['api_key'],
            "Content-Type": "application/json"
        }
        
        payload = {
            "messages": [
                {"role": "user", "content": message}
            ],
            "max_tokens": provider['max_tokens'],
            "temperature": 0.7,
            "stream": True
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            async with client.stream("POST", provider['model_url'], headers=headers, json=payload) as response:
                response.raise_for_status()
                
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:]
                        if data_str.strip() == "[DONE]":
                            break
                        
                        try:
                            data = json.loads(data_str)
                            if 'choices' in data and len(data['choices']) > 0:
                                delta = data['choices'][0].get('delta', {})
                                if 'content' in delta:
                                    yield delta['content']
                        except json.JSONDecodeError:
                            continue

    async def _call_ollama(self, message: str, provider: Dict, tools_used: List[str], tool_schemas: List[Dict[str, Any]] = None) -> str:
        """Call Ollama API"""
        payload = {
            "model": provider['model_name'],
            "prompt": message,
            "stream": False
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(provider['model_url'], json=payload)
            response.raise_for_status()
            
            data = response.json()
            return data['response']

    async def _stream_ollama(self, message: str, provider: Dict, tools_used: List[str], tool_schemas: List[Dict[str, Any]] = None) -> AsyncGenerator[str, None]:
        """Stream from Ollama API"""
        payload = {
            "model": provider['model_name'],
            "prompt": message,
            "stream": True
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            async with client.stream("POST", provider['model_url'], json=payload) as response:
                response.raise_for_status()
                
                async for line in response.aiter_lines():
                    try:
                        data = json.loads(line)
                        if 'response' in data:
                            yield data['response']
                        if data.get('done', False):
                            break
                    except json.JSONDecodeError:
                        continue