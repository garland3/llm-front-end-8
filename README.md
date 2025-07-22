# LLM Frontend

A modular LLM frontend with MCP integration built with FastAPI and vanilla JavaScript.

## Features

- **Multiple LLM Providers**: Support for OpenAI, Anthropic, and local models
- **MCP Integration**: Model Context Protocol servers for tool integration
- **WebSocket Support**: Real-time communication for dynamic loading
- **Authentication**: Middleware-based auth with reverse proxy support
- **Modular Architecture**: Clean separation of concerns with < 400 lines per file
- **Comprehensive Logging**: Structured logging with exception tracking
- **Tool Authorization**: Server-side validation of MCP tool access

## Quick Start

### Prerequisites

- Python 3.8+
- uv (Python package manager)

### Installation

1. Install uv:
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. Install dependencies:
   ```bash
   uv sync
   ```

3. Configure environment:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and configuration
   ```

### Running the Application

#### Development Mode
```bash
python start.py
```

#### Manual Start
```bash
cd backend
uv run python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### Production Mode with Docker
```bash
docker build -t llm-frontend .
docker run -p 8000:8000 llm-frontend
```

The application will be available at http://localhost:8000

## Configuration

### Environment Variables (.env file)

- `DEBUG`: Enable debug mode (bypasses auth, sets user to test@test.com)
- `HOST`: Server host (default: 0.0.0.0)
- `PORT`: Server port (default: 8000)
- `LOG_LEVEL`: Logging level (default: INFO)
- `OPENAI_API_KEY`: OpenAI API key
- `ANTHROPIC_API_KEY`: Anthropic API key
- `MODELS_CONFIG_PATH`: Path to models YAML configuration (default: models.yml)
- `MCP_CONFIG_PATH`: Path to MCP JSON configuration (default: mcp/config.json)

### Model Configuration (models.yml)

Configure LLM providers in the YAML file:

```yaml
models:
  - id: "openai-gpt4"
    name: "OpenAI GPT-4"
    model_name: "gpt-4"
    model_url: "https://api.openai.com/v1/chat/completions"
    api_key: "${OPENAI_API_KEY}"
    provider: "openai"
    required_group: "mcp_users"
    available: true
```

### Testing

Run unit tests:
```bash
uv run python -m pytest backend/tests/ -v
```